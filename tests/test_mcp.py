"""Contract and security tests for the local stdio MCP adapter."""

from __future__ import annotations

import io
import json
import time
from pathlib import Path

from codex_babeldoc.application.mcp import MCP_PROTOCOL_VERSION, McpServer, run_stdio
from codex_babeldoc.application.service import BabelCodexService
from codex_babeldoc.core.artifacts import Artifact, ArtifactType
from codex_babeldoc.core.config import load_config
from codex_babeldoc.core.state import JobStatus


def _service(tmp_path: Path) -> BabelCodexService:
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    cfg.project.input_dir = tmp_path / "incoming"
    cfg.project.output_dir = tmp_path / "translated"
    cfg.project.state_dir = tmp_path / "state"
    cfg.project.log_dir = tmp_path / "logs"
    cfg.babeldoc.working_dir = tmp_path / "work"
    cfg.ensure_dirs()
    return BabelCodexService(cfg)


def _request(server: McpServer, request_id: str, method: str, params: dict | None = None) -> dict:
    response = server.handle(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    )
    assert response is not None
    return response


def _call(server: McpServer, request_id: str, name: str, arguments: dict | None = None) -> dict:
    response = _request(
        server, request_id, "tools/call", {"name": name, "arguments": arguments or {}}
    )
    assert "result" in response, response
    return response["result"]["structuredContent"]


def test_initialize_lists_scoped_tools_and_notifications_are_silent(tmp_path):
    server = McpServer(_service(tmp_path))
    response = _request(server, "1", "initialize", {"protocolVersion": MCP_PROTOCOL_VERSION})
    assert response["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    names = {tool["name"] for tool in _request(server, "2", "tools/list")["result"]["tools"]}
    assert names == {
        "babelcodex_doctor",
        "babelcodex_start_translation",
        "babelcodex_get_job",
        "babelcodex_list_jobs",
        "babelcodex_cancel_job",
        "babelcodex_validate_output",
        "babelcodex_cleanup_job",
    }
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    server.close()


def test_stdio_round_trip_and_parse_error(tmp_path):
    service = _service(tmp_path)
    stdin = io.StringIO(
        '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n'
        "not-json\n"
        '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
    )
    stdout = io.StringIO()
    run_stdio(McpServer(service), stdin, stdout)
    messages = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert messages[0]["id"] == 1
    assert messages[1]["error"]["code"] == -32700


def test_start_get_validate_and_cleanup_are_scoped(tmp_path):
    service = _service(tmp_path)
    source = service.config.project.input_dir / "paper.pdf"
    source.write_bytes(b"%PDF-test")
    server = McpServer(service)
    started = _call(server, "start", "babelcodex_start_translation", {"source_path": str(source)})
    job_id = started["job_id"]
    job = service.get_job(job_id)
    assert job is not None
    deadline = time.monotonic() + 2
    while (
        job.status in {JobStatus.DISCOVERED, JobStatus.RUNNING, JobStatus.RETRY_PENDING}
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
        job = service.get_job(job_id)
    assert job is not None
    output = service.config.project.output_dir / "paper.mono.pdf"
    output.write_bytes(b"%PDF-output")
    job.status = JobStatus.COMPLETED
    job.artifacts = [Artifact(ArtifactType.MONO_PDF, str(output))]
    service.orchestrator.state.save(job)

    validated = _call(server, "validate", "babelcodex_validate_output", {"job_id": job_id})
    assert validated["validated"] is True
    assert validated["artifacts"][0]["sha256"]

    work_dir = service.config.babeldoc.working_dir / "job-paper"
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "request.json").write_text("{}", encoding="utf-8")
    cleaned = _call(server, "cleanup", "babelcodex_cleanup_job", {"job_id": job_id})
    assert cleaned["removed"] is True
    assert not work_dir.exists()
    assert output.exists()
    server.close()


def test_validate_rejects_artifact_outside_output_allowlist(tmp_path):
    service = _service(tmp_path)
    source = service.config.project.input_dir / "paper.pdf"
    source.write_bytes(b"%PDF-test")
    server = McpServer(service)
    job_id = _call(server, "start", "babelcodex_start_translation", {"source_path": str(source)})[
        "job_id"
    ]
    job = service.get_job(job_id)
    assert job is not None
    deadline = time.monotonic() + 2
    while (
        job.status in {JobStatus.DISCOVERED, JobStatus.RUNNING, JobStatus.RETRY_PENDING}
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
        job = service.get_job(job_id)
    assert job is not None
    job.status = JobStatus.COMPLETED
    job.artifacts = [Artifact(ArtifactType.MONO_PDF, str(source))]
    service.orchestrator.state.save(job)
    response = _request(
        server,
        "validate",
        "tools/call",
        {"name": "babelcodex_validate_output", "arguments": {"job_id": job_id}},
    )
    assert response["error"]["code"] == -32003
    server.close()


def test_unknown_tool_and_arbitrary_shell_are_rejected(tmp_path):
    server = McpServer(_service(tmp_path))
    unknown = _request(
        server, "1", "tools/call", {"name": "shell", "arguments": {"command": "whoami"}}
    )
    assert unknown["error"]["code"] == -32602
    arbitrary = _request(server, "2", "exec", {"command": "whoami"})
    assert arbitrary["error"]["code"] == -32601
    server.close()


def test_tool_arguments_are_strictly_scoped(tmp_path):
    server = McpServer(_service(tmp_path))
    response = _request(
        server,
        "1",
        "tools/call",
        {"name": "babelcodex_list_jobs", "arguments": {"path": "/tmp"}},
    )
    assert response["error"]["code"] == -32602
    server.close()


def test_non_object_request_returns_jsonrpc_error(tmp_path):
    server = McpServer(_service(tmp_path))
    response = server.handle(["not", "an", "object"])
    assert response is not None
    assert response["error"]["code"] == -32600
    server.close()


def test_completed_job_is_not_started_again(tmp_path):
    service = _service(tmp_path)
    source = service.config.project.input_dir / "completed.pdf"
    source.write_bytes(b"%PDF-test")
    server = McpServer(service)
    first = _call(server, "start", "babelcodex_start_translation", {"source_path": str(source)})
    deadline = time.monotonic() + 2
    while server.context.active and time.monotonic() < deadline:
        time.sleep(0.01)
    job = service.get_job(first["job_id"])
    assert job is not None
    job.status = JobStatus.COMPLETED
    service.orchestrator.state.save(job)
    second = _call(server, "again", "babelcodex_start_translation", {"source_path": str(source)})
    assert second["skipped"] is True
    assert second["status"] == "completed"
    server.close()


def test_cancel_uses_the_active_job_handle(tmp_path):
    service = _service(tmp_path)
    source = service.config.project.input_dir / "cancel.pdf"
    source.write_bytes(b"%PDF-test")
    server = McpServer(service)
    job_id = _call(server, "start", "babelcodex_start_translation", {"source_path": str(source)})[
        "job_id"
    ]
    response = _request(
        server,
        "cancel",
        "tools/call",
        {"name": "babelcodex_cancel_job", "arguments": {"job_id": job_id}},
    )
    assert response["result"]["structuredContent"]["cancelled"] is True
    deadline = time.monotonic() + 2
    job = service.get_job(job_id)
    while (
        job is not None
        and job.status in {JobStatus.DISCOVERED, JobStatus.RUNNING, JobStatus.RETRY_PENDING}
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
        job = service.get_job(job_id)
    assert job is not None
    assert job.status is JobStatus.CANCELLED
    server.close()


def test_relative_source_path_is_resolved_inside_input_directory(tmp_path):
    service = _service(tmp_path)
    source = service.config.project.input_dir / "nested" / "relative.pdf"
    source.parent.mkdir()
    source.write_bytes(b"%PDF-test")
    server = McpServer(service)
    result = _call(
        server,
        "relative",
        "babelcodex_start_translation",
        {"source_path": "nested/relative.pdf"},
    )
    assert result["job_id"]
    server.close()
