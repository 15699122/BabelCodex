"""Contract tests for the fixed GUI-sidecar JSONL boundary."""

from __future__ import annotations

import io
import json
from pathlib import Path

from codex_babeldoc.application.service import BabelCodexService
from codex_babeldoc.application.sidecar import PROTOCOL_VERSION, JsonlSidecar, run_jsonl
from codex_babeldoc.core.config import load_config


def _service(tmp_path: Path) -> BabelCodexService:
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    cfg.project.input_dir = tmp_path / "incoming"
    cfg.project.state_dir = tmp_path / "state"
    cfg.project.output_dir = tmp_path / "translated"
    cfg.project.log_dir = tmp_path / "logs"
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
    assert response["error"]["category"] == "config"
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
    assert response["error"]["safe_message"] == "unsupported sidecar protocol version"
    sidecar.close()


def test_run_jsonl_returns_structured_error_for_malformed_input(tmp_path):
    service = _service(tmp_path)
    stdout = io.StringIO()
    run_jsonl(service, io.StringIO("not-json\n"), stdout)
    message = json.loads(stdout.getvalue())
    assert message["ok"] is False
    assert message["request_id"] == ""
    assert "error" in message
