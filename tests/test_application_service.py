from pathlib import Path

from codex_babeldoc.application.service import (
    BabelCodexService,
    InvocationSource,
    StartTranslationCommand,
)
from codex_babeldoc.core.artifacts import Artifact, ArtifactType
from codex_babeldoc.core.config import load_config
from codex_babeldoc.core.state import JobStage, JobStatus


def test_start_translation_records_invocation_source(tmp_path, monkeypatch):
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    cfg.project.state_dir = tmp_path / "state"
    cfg.ensure_dirs()

    source = tmp_path / "doc.pdf"
    source.write_bytes(b"%PDF-test")

    class _FakeOrchestrator:
        def __init__(self) -> None:
            from codex_babeldoc.core.state import StateStore

            self.state = StateStore(cfg.project.state_dir)
            self.calls: list[tuple] = []

        def run_one(self, path, *, force=False, invocation_source="cli"):
            self.calls.append((path, force, invocation_source))
            job = self.state.load(path, config_fingerprint=cfg.fingerprint())
            job.status = JobStatus.COMPLETED
            job.stage = JobStage.COMPLETED
            self.state.save(job)
            return "completed"

    fake = _FakeOrchestrator()
    service = BabelCodexService(cfg, orchestrator=fake)
    state = service.start_translation(
        StartTranslationCommand(
            source_path=source,
            invocation_source=InvocationSource.MCP,
        )
    )
    assert state.status is JobStatus.COMPLETED
    assert fake.calls[0][2] == "mcp"


def test_get_and_list_jobs(tmp_path):
    from codex_babeldoc.core.state import StateStore

    store = StateStore(tmp_path / "state")
    service = BabelCodexService.__new__(BabelCodexService)
    service.orchestrator = type("O", (), {"state": store})()

    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    job = store.load(pdf, config_fingerprint="f")
    store.save(job)

    assert service.list_jobs()[0].job_id == job.job_id
    assert service.get_job(job.job_id) is not None
    assert service.get_job("missing") is None


def test_validate_output_refreshes_manifest_and_detects_tampering(tmp_path):
    from codex_babeldoc.core.state import StateStore

    output_dir = tmp_path / "translated"
    output_dir.mkdir()
    store = StateStore(tmp_path / "state")
    service = BabelCodexService.__new__(BabelCodexService)
    service.config = type(
        "Config", (), {"project": type("Project", (), {"output_dir": output_dir})()}
    )()
    service.orchestrator = type("O", (), {"state": store})()
    source = tmp_path / "a.pdf"
    source.write_bytes(b"%PDF-source")
    output = output_dir / "a.mono.pdf"
    output.write_bytes(b"%PDF-output")
    job = store.load(source, config_fingerprint="f")
    job.status = JobStatus.COMPLETED
    job.artifacts = [Artifact(ArtifactType.MONO_PDF, str(output))]
    store.save(job)

    first = service.validate_output(job.job_id)
    assert first["validated"] is True
    output.write_bytes(b"%PDF-changed")
    second = service.validate_output(job.job_id)
    assert second["validated"] is False
    assert second["artifacts"][0]["reason"] == "hash_mismatch"


def test_service_startup_recovers_legacy_active_job_without_runner_pid(tmp_path):
    from codex_babeldoc.core.errors import ErrorCode
    from codex_babeldoc.core.state import StateStore

    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    cfg.project.state_dir = tmp_path / "state"
    cfg.project.input_dir = tmp_path / "incoming"
    cfg.project.output_dir = tmp_path / "translated"
    cfg.ensure_dirs()
    source = cfg.project.input_dir / "interrupted.pdf"
    source.write_bytes(b"%PDF")
    store = StateStore(cfg.project.state_dir)
    job = store.load(source, config_fingerprint=cfg.fingerprint())
    job.status = JobStatus.RUNNING
    job.stage = JobStage.TRANSLATING
    store.save(job)

    service = BabelCodexService(cfg)

    recovered = service.get_job(job.job_id)
    assert recovered is not None
    assert recovered.status is JobStatus.FAILED
    assert recovered.error_code is ErrorCode.WORKER_CRASHED
