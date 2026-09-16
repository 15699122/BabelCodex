"""Contract tests for the fixed GUI-sidecar JSONL boundary."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from time import sleep
from typing import cast

from codex_babeldoc.application.service import BabelCodexService
from codex_babeldoc.application.sidecar import PROTOCOL_VERSION, JsonlSidecar, run_jsonl
from codex_babeldoc.backends.base import ProgressEvent
from codex_babeldoc.core.config import load_config
from codex_babeldoc.core.state import JobStage, JobStatus, StateStore


def _service(tmp_path: Path) -> BabelCodexService:
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "config.yaml")
    cfg.config_path = tmp_path / "config.yaml"
    cfg.project.input_dir = tmp_path / "incoming"
    cfg.project.state_dir = tmp_path / "state"
    cfg.project.output_dir = tmp_path / "translated"
    cfg.project.log_dir = tmp_path / "logs"
    cfg.project.glossary_dir = tmp_path / "glossary"
    cfg.project.context_dir = tmp_path / "context"
    cfg.babeldoc.working_dir = tmp_path / "work"
    cfg.ensure_dirs()
    return BabelCodexService(cfg)


def test_sidecar_rejects_path_outside_allowlist(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "r1",
            "method": "start_translation",
            "source_path": str(tmp_path / "outside.pdf"),
        }
    )[0]
    assert response["ok"] is False
    error = response["error"]
    assert isinstance(error, dict)
    assert error["category"] == "config"
    sidecar.close()


def test_sidecar_lists_jobs_without_exposing_shell(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "r2",
            "method": "list_jobs",
        }
    )[0]
    assert response["ok"] is True
    assert response["result"] == {"jobs": []}
    sidecar.close()


def test_get_server_info_reports_protocol_version_and_capabilities(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "info",
            "method": "get_server_info",
        }
    )[0]
    assert response["ok"] is True
    info = response["result"]
    assert isinstance(info, dict)
    assert info["protocol_version"] == PROTOCOL_VERSION
    assert isinstance(info["package_version"], str) and info["package_version"]
    assert "start_translation" in info["capabilities"]
    assert "retry_job" in info["capabilities"]
    assert "validate_output" in info["capabilities"]
    assert "run_qa" in info["capabilities"]
    assert "shutdown" in info["capabilities"]
    sidecar.close()


def test_sidecar_reads_and_writes_scoped_glossary_and_context(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)

    saved_glossary = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "glossary-save",
            "method": "save_glossary",
            "scope": "document",
            "document_id": "paper",
            "entries": [
                {"source": "model", "target": "模型", "notes": "preferred", "enabled": True},
                {"source": "disabled", "target": "忽略", "enabled": False},
            ],
        }
    )[0]
    assert saved_glossary["ok"] is True
    assert any(
        entry["source"] == "disabled" and entry["enabled"] is False
        for entry in saved_glossary["result"]["entries"]
    )

    listed = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "glossary-list",
            "method": "list_glossary",
            "scope": "document",
            "document_id": "paper",
        }
    )[0]
    assert listed["result"]["version"]
    assert (tmp_path / "glossary" / "documents" / "paper.csv").is_file()

    context = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "context-save",
            "method": "save_context",
            "document_id": "paper",
            "text": "A Paper\nAbstract\nA useful context.",
        }
    )[0]
    assert context["result"]["title"] == "A Paper"
    assert context["result"]["abstract"] == "A useful context."

    loaded = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "context-get",
            "method": "get_context",
            "document_id": "paper",
        }
    )[0]
    assert loaded["result"]["text"] == "A Paper\nAbstract\nA useful context."
    sidecar.close()


def test_sidecar_exposes_portable_layout_and_settings(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    layout = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "layout",
            "method": "get_runtime_layout",
        }
    )[0]
    assert layout["ok"] is True
    assert layout["result"]["paths"]["output"] == "<external>"
    assert layout["result"]["paths"]["resource"] == "resource"

    settings = sidecar.handle(
        {"protocol_version": PROTOCOL_VERSION, "request_id": "settings", "method": "get_settings"}
    )[0]
    assert settings["result"]["logging"] == {"level": "info", "max_files": 5}
    saved = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "settings-save",
            "method": "save_settings",
            "settings": {"logging": {"level": "debug", "max_files": 3}},
        }
    )[0]
    assert saved["ok"] is True
    assert saved["result"]["requires_restart"] is True
    assert service.config.logging.level == "debug"
    sidecar.close()


def test_sidecar_stages_pdf_and_requires_output_confirmation(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    source = tmp_path / "selected.pdf"
    source.write_bytes(b"%PDF-staged")
    staged = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "stage",
            "method": "stage_input",
            "source_path": str(source),
        }
    )[0]
    assert staged["ok"] is True
    staged_path = Path(staged["result"]["source_path"])
    assert staged_path.parent == service.config.project.input_dir
    assert staged_path.read_bytes() == source.read_bytes()

    service.config.project.output_dir.rmdir()
    pending = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "output",
            "method": "prepare_output_directory",
            "confirmed": False,
        }
    )[0]
    assert pending["result"]["requires_confirmation"] is True
    ready = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "output-confirm",
            "method": "prepare_output_directory",
            "confirmed": True,
        }
    )[0]
    assert ready["result"]["exists"] is True
    sidecar.close()


def test_real_sidecar_startup_does_not_create_output_before_confirmation(tmp_path):
    from codex_babeldoc.application.service import BabelCodexService
    from codex_babeldoc.core.config import AppConfig

    config = AppConfig(root=tmp_path)
    config.project.output_dir = tmp_path / "output"
    config.config_path = tmp_path / "config.yaml"
    config.resolve_paths()
    service = BabelCodexService(config)
    assert not config.project.output_dir.exists()
    sidecar = JsonlSidecar(service)
    pending = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "output-real",
            "method": "prepare_output_directory",
            "confirmed": False,
        }
    )[0]
    assert pending["ok"] is True
    assert pending["result"]["requires_confirmation"] is True
    assert not config.project.output_dir.exists()
    sidecar.close()


def test_sidecar_latest_log_redacts_credential_like_values(tmp_path):
    service = _service(tmp_path)
    log = service.config.project.log_dir / "babelcodex-test.log"
    log.write_text("authorization=Bearer top-secret ordinary=ok\n", encoding="utf-8")
    sidecar = JsonlSidecar(service)
    result = sidecar.handle(
        {"protocol_version": PROTOCOL_VERSION, "request_id": "log", "method": "get_latest_log"}
    )[0]
    assert result["ok"] is True
    assert "top-secret" not in result["result"]["text"]
    assert "ordinary=ok" in result["result"]["text"]
    sidecar.close()


def test_sidecar_rejects_document_path_traversal(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "bad-document",
            "method": "get_context",
            "document_id": "../outside",
        }
    )[0]
    assert response["ok"] is False
    assert "single document stem" in response["error"]["safe_message"]
    sidecar.close()


def test_sidecar_rejects_windows_style_document_path_traversal(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "bad-windows-document",
            "method": "get_context",
            "document_id": "..\\outside",
        }
    )[0]
    assert response["ok"] is False
    assert "single document stem" in response["error"]["safe_message"]
    sidecar.close()


def test_run_jsonl_round_trip_and_shutdown(tmp_path):
    service = _service(tmp_path)
    stdin = io.StringIO(
        json.dumps(
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": "r3",
                "method": "list_jobs",
            }
        )
        + "\n"
        + json.dumps(
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": "r4",
                "method": "shutdown",
            }
        )
        + "\n"
    )
    stdout = io.StringIO()
    run_jsonl(service, stdin, stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert messages[0]["request_id"] == "r3"
    assert messages[1]["request_id"] == "r4"
    assert messages[1]["result"] == {"closing": True}


def test_sidecar_returns_structured_error_for_invalid_protocol(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {"protocol_version": 999, "request_id": "bad", "method": "list_jobs"}
    )[0]
    assert response["ok"] is False
    assert response["request_id"] == "bad"
    error = response["error"]
    assert isinstance(error, dict)
    assert error["safe_message"] == "unsupported sidecar protocol version"
    sidecar.close()


def test_sidecar_returns_structured_error_for_non_convertible_protocol(tmp_path):
    service = _service(tmp_path)
    sidecar = JsonlSidecar(service)
    response = sidecar.handle(
        {"protocol_version": [], "request_id": "bad-type", "method": "list_jobs"}
    )[0]
    assert response["ok"] is False
    assert response["request_id"] == "bad-type"
    error = response["error"]
    assert isinstance(error, dict)
    assert error["safe_message"] == "unsupported sidecar protocol version"
    sidecar.close()


def test_run_jsonl_returns_structured_error_for_malformed_input(tmp_path):
    service = _service(tmp_path)
    stdout = io.StringIO()
    run_jsonl(service, io.StringIO("not-json\n"), stdout)
    message = json.loads(stdout.getvalue())
    assert message["ok"] is False
    assert message["request_id"] == ""
    assert "error" in message


@dataclass
class _FakeConfig:
    project: object

    def fingerprint(self):
        return "fake-config"


class _FakeService:
    def __init__(
        self, tmp_path: Path, *, started: Event | None = None, release: Event | None = None
    ):
        self.config = _FakeConfig(type("Project", (), {"input_dir": tmp_path / "incoming"})())
        self.state = StateStore(tmp_path / "state")
        self.orchestrator = type("Orchestrator", (), {"state": self.state})()
        self.started = started
        self.release = release

    def start_translation(self, command):
        if self.started is not None:
            self.started.set()
        if command.on_progress is not None:
            command.on_progress(
                ProgressEvent(
                    stage="render",
                    stage_current=2,
                    stage_total=4,
                    overall_progress=0.5,
                    message="halfway",
                )
            )
        if self.release is not None:
            self.release.wait(timeout=2)
        job = self.state.load(command.source_path, config_fingerprint=self.config.fingerprint())
        job.status = JobStatus.COMPLETED
        job.stage = JobStage.COMPLETED
        self.state.save(job)
        return job

    def get_job(self, job_id):
        return self.state.load_by_job_id(job_id)

    def list_jobs(self):
        return self.state.list_jobs()

    @staticmethod
    def job_view(job):
        if job is None:
            return None
        return {
            "job_id": job.job_id,
            "source_name": Path(job.source_path).name,
            "status": job.status.value,
            "stage": job.stage.value,
            "attempts": job.attempts,
            "safe_error_message": job.safe_error_message,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at,
            "artifacts": [],
            "qa_status": job.qa_status,
        }


class _FailingService(_FakeService):
    def start_translation(self, command):
        if self.started is not None:
            self.started.set()
        raise RuntimeError("expected fake failure")


class _CancellableService(_FakeService):
    def start_translation(self, command):
        if self.started is not None:
            self.started.set()
        assert command.cancel_event is not None
        command.cancel_event.wait(timeout=2)
        job = self.state.load(command.source_path, config_fingerprint=self.config.fingerprint())
        job.status = JobStatus.CANCELLED
        self.state.save(job)
        return job


def _sidecar(service: _FakeService) -> JsonlSidecar:
    """Construct a sidecar with the deliberately lightweight test service."""
    return JsonlSidecar(cast(BabelCodexService, service))


def test_sidecar_event_polling_supports_incremental_cursor(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "event.pdf"
    source.write_bytes(b"%PDF-test")
    started = Event()
    release = Event()
    service = _FakeService(tmp_path, started=started, release=release)
    sidecar = _sidecar(service)
    response = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "start",
            "method": "start_translation",
            "source_path": str(source),
        }
    )[0]
    job_id = response["result"]["job_id"]
    assert started.wait(timeout=1)
    first = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "poll-1",
            "method": "poll_events",
            "after_sequence": 0,
            "job_id": job_id,
        }
    )[0]["result"]
    assert [event["event_type"] for event in first["events"]][:2] == [
        "job_created",
        "status_changed",
    ]
    initial_progress = [event for event in first["events"] if event["event_type"] == "progress"]
    cursor = first["next_sequence"]
    release.set()
    deadline = 1.0
    while deadline > 0:
        second = sidecar.handle(
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": "poll-2",
                "method": "poll_events",
                "after_sequence": cursor,
                "job_id": job_id,
            }
        )[0]["result"]
        if any(event["event_type"] == "job_completed" for event in second["events"]):
            break
        sleep(0.01)
        deadline -= 0.01
    assert second["events"][-1]["event_type"] == "job_completed"
    progress = initial_progress + [
        event for event in second["events"] if event["event_type"] == "progress"
    ]
    assert progress[0]["payload"]["overall_progress"] == 0.5
    sidecar.close()


def test_sidecar_emits_cancel_request_event(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "cancel.pdf"
    source.write_bytes(b"%PDF-test")
    started = Event()
    release = Event()
    service = _FakeService(tmp_path, started=started, release=release)
    sidecar = _sidecar(service)
    start = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "start",
            "method": "start_translation",
            "source_path": str(source),
        }
    )[0]
    job_id = start["result"]["job_id"]
    assert started.wait(timeout=1)
    cancel = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "cancel",
            "method": "cancel_job",
            "job_id": job_id,
        }
    )[0]
    assert cancel["result"]["status"] == "cancel_requested"
    events = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "poll",
            "method": "poll_events",
            "job_id": job_id,
        }
    )[0]["result"]["events"]
    assert any(
        event["event_type"] == "status_changed" and event["payload"]["status"] == "cancel_requested"
        for event in events
    )
    release.set()
    sidecar.close()


def test_sidecar_emits_failure_event_for_background_exception(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "failure.pdf"
    source.write_bytes(b"%PDF-test")
    started = Event()
    service = _FailingService(tmp_path, started=started)
    sidecar = _sidecar(service)
    start = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "start",
            "method": "start_translation",
            "source_path": str(source),
        }
    )[0]
    job_id = start["result"]["job_id"]
    assert started.wait(timeout=1)
    for _ in range(100):
        events = sidecar.handle(
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": "poll",
                "method": "poll_events",
                "job_id": job_id,
            }
        )[0]["result"]["events"]
        if any(event["event_type"] == "job_failed" for event in events):
            break
        sleep(0.01)
    assert events[-1]["event_type"] == "job_failed"
    assert events[-1]["payload"]["error"]["category"] == "unknown"
    sidecar.close()


def test_sidecar_restart_reconciles_persisted_job_state(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "persisted.pdf"
    source.write_bytes(b"%PDF-test")
    service = _FakeService(tmp_path)
    sidecar = _sidecar(service)
    start = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "start",
            "method": "start_translation",
            "source_path": str(source),
        }
    )[0]
    job_id = start["result"]["job_id"]
    sidecar._executor.shutdown(wait=True)
    sidecar.close()

    restarted = _sidecar(_FakeService(tmp_path))
    response = restarted.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "reconnect",
            "method": "get_job",
            "job_id": job_id,
        }
    )[0]
    assert response["ok"] is True
    assert response["result"]["job"]["job_id"] == job_id
    assert response["result"]["job"]["status"] == "completed"
    restarted.close()


def test_sidecar_cancels_running_job_and_persists_terminal_state(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "cancel-running.pdf"
    source.write_bytes(b"%PDF-test")
    started = Event()
    service = _CancellableService(tmp_path, started=started)
    sidecar = _sidecar(service)
    start = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "start",
            "method": "start_translation",
            "source_path": str(source),
        }
    )[0]
    job_id = start["result"]["job_id"]
    assert started.wait(timeout=1)

    cancel = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "cancel",
            "method": "cancel_job",
            "job_id": job_id,
        }
    )[0]
    assert cancel["result"] == {
        "job_id": job_id,
        "cancelled": True,
        "status": "cancel_requested",
    }

    terminal_events = []
    for _ in range(100):
        events = sidecar.handle(
            {
                "protocol_version": PROTOCOL_VERSION,
                "request_id": "poll-terminal",
                "method": "poll_events",
                "job_id": job_id,
            }
        )[0]["result"]["events"]
        terminal_events.extend(events)
        if any(
            event["event_type"] == "status_changed" and event["payload"]["status"] == "cancelled"
            for event in terminal_events
        ):
            break
        sleep(0.01)
    assert any(
        event["event_type"] == "status_changed" and event["payload"]["status"] == "cancelled"
        for event in terminal_events
    )
    assert not any(event["event_type"] == "job_failed" for event in terminal_events)
    assert not any(event["event_type"] == "job_completed" for event in terminal_events)
    job = sidecar.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "get-cancelled",
            "method": "get_job",
            "job_id": job_id,
        }
    )[0]["result"]["job"]
    assert job["status"] == "cancelled"
    sidecar.close()
