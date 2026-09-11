"""Minimal local stdio MCP server for scoped BabelCodex job operations.

The implementation intentionally uses only the Python standard library. It is
an adapter over :class:`BabelCodexService`; it does not implement PDF
translation, shell execution, arbitrary file reads, or unrestricted deletion.
"""

from __future__ import annotations

import json
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock
from typing import TextIO

from codex_babeldoc.application.service import (
    BabelCodexService,
    InvocationSource,
    StartTranslationCommand,
)
from codex_babeldoc.cli import collect_doctor_checks
from codex_babeldoc.core.errors import BabelCodexError
from codex_babeldoc.core.state import JobState, JobStatus
from codex_babeldoc.core.workdir import WorkdirError, remove_work_dir, resolve_work_dir

MCP_PROTOCOL_VERSION = "2024-11-05"
JSONRPC_VERSION = "2.0"


class McpError(ValueError):
    """An MCP request error that can safely be returned to the caller."""

    def __init__(self, code: int, message: str, data: object | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


@dataclass(slots=True)
class _JobContext:
    service: BabelCodexService
    executor: ThreadPoolExecutor
    active: dict[str, Event]
    futures: dict[str, Future[object]]
    lock: Lock


def _json_result(value: object) -> dict[str, object]:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return {"content": [{"type": "text", "text": text}], "structuredContent": value}


def _tool(
    name: str, description: str, properties: dict[str, object], required: list[str]
) -> dict[str, object]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


TOOLS = [
    _tool("babelcodex_doctor", "Check the local BabelCodex, BabelDOC and Codex runtime.", {}, []),
    _tool(
        "babelcodex_start_translation",
        "Start an asynchronous PDF translation inside the configured input allowlist.",
        {
            "source_path": {
                "type": "string",
                "description": "Absolute or configured-relative PDF path.",
            }
        },
        ["source_path"],
    ),
    _tool(
        "babelcodex_get_job",
        "Read one persisted translation job by its job ID.",
        {"job_id": {"type": "string"}},
        ["job_id"],
    ),
    _tool("babelcodex_list_jobs", "List persisted translation jobs.", {}, []),
    _tool(
        "babelcodex_cancel_job",
        "Request cancellation of a running translation job.",
        {"job_id": {"type": "string"}},
        ["job_id"],
    ),
    _tool(
        "babelcodex_validate_output",
        "Validate the persisted artifacts of a translation job without reading arbitrary paths.",
        {"job_id": {"type": "string"}},
        ["job_id"],
    ),
    _tool(
        "babelcodex_run_qa",
        "Run the PDF QA battery over a terminal job's output artifacts and return a terse summary.",
        {"job_id": {"type": "string"}},
        ["job_id"],
    ),
    _tool(
        "babelcodex_cleanup_job",
        "Remove only the job-owned temporary working directory for a terminal job.",
        {"job_id": {"type": "string"}},
        ["job_id"],
    ),
]

TOOL_ARGUMENTS = {
    "babelcodex_doctor": set(),
    "babelcodex_start_translation": {"source_path"},
    "babelcodex_get_job": {"job_id"},
    "babelcodex_list_jobs": set(),
    "babelcodex_cancel_job": {"job_id"},
    "babelcodex_validate_output": {"job_id"},
    "babelcodex_run_qa": {"job_id"},
    "babelcodex_cleanup_job": {"job_id"},
}


class McpServer:
    """Serve MCP JSON-RPC requests over stdin/stdout."""

    def __init__(
        self, service: BabelCodexService, *, executor: ThreadPoolExecutor | None = None
    ) -> None:
        self.context = _JobContext(
            service,
            executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="babelcodex-mcp"),
            {},
            {},
            Lock(),
        )
        self._owns_executor = executor is None
        self._initialized = False
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        with self.context.lock:
            for cancel_event in self.context.active.values():
                cancel_event.set()
            self.context.active.clear()
            self.context.futures.clear()
        if self._owns_executor:
            self.context.executor.shutdown(wait=False, cancel_futures=True)

    def handle(self, request: object) -> dict[str, object] | None:
        if not isinstance(request, dict):
            return self._error(None, -32600, "request must be a JSON object")
        request_id = request.get("id")
        if request.get("jsonrpc") != JSONRPC_VERSION:
            return self._error(request_id, -32600, "jsonrpc must be 2.0")
        method = request.get("method")
        if not isinstance(method, str):
            return self._error(request_id, -32600, "method is required")
        params = request.get("params", {})
        if not isinstance(params, dict):
            return self._error(request_id, -32602, "params must be an object")
        try:
            if method == "initialize":
                result = self._initialize(params)
            elif method == "notifications/initialized":
                self._initialized = True
                return None
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                result = self._call_tool(params)
            else:
                return self._error(request_id, -32601, f"method not found: {method}")
            if request_id is None:
                return None
            return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}
        except McpError as exc:
            return self._error(request_id, exc.code, str(exc), exc.data)
        except Exception as exc:  # noqa: BLE001 - protocol boundary must remain alive
            return self._error(
                request_id, -32603, "internal MCP server error", {"detail": str(exc)}
            )

    def _initialize(self, params: dict[str, object]) -> dict[str, object]:
        client_version = params.get("protocolVersion")
        if client_version is not None and not isinstance(client_version, str):
            raise McpError(-32602, "protocolVersion must be a string")
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "babelcodex", "version": "0.1.0"},
            "instructions": "Use only the scoped BabelCodex translation and job tools.",
        }

    def _call_tool(self, params: dict[str, object]) -> dict[str, object]:
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or not name:
            raise McpError(-32602, "tool name is required")
        if not isinstance(arguments, dict):
            raise McpError(-32602, "tool arguments must be an object")
        allowed_arguments = TOOL_ARGUMENTS.get(name)
        if allowed_arguments is None:
            raise McpError(-32602, f"unknown tool: {name}")
        unexpected = sorted(set(arguments) - allowed_arguments)
        if unexpected:
            raise McpError(-32602, f"unexpected tool arguments: {', '.join(unexpected)}")
        handlers = {
            "babelcodex_doctor": self._doctor,
            "babelcodex_start_translation": self._start_translation,
            "babelcodex_get_job": self._get_job,
            "babelcodex_list_jobs": self._list_jobs,
            "babelcodex_cancel_job": self._cancel_job,
            "babelcodex_validate_output": self._validate_output,
            "babelcodex_run_qa": self._run_qa,
            "babelcodex_cleanup_job": self._cleanup_job,
        }
        handler = handlers.get(name)
        assert handler is not None
        try:
            return _json_result(handler(arguments))
        except BabelCodexError as exc:
            raise McpError(
                -32001, exc.safe_message, {"category": exc.category.value, "code": exc.code.value}
            ) from exc

    def _doctor(self, arguments: dict[str, object]) -> dict[str, object]:
        if arguments:
            raise McpError(-32602, "babelcodex_doctor takes no arguments")
        return collect_doctor_checks(self.context.service.config)

    def _start_translation(self, arguments: dict[str, object]) -> dict[str, object]:
        source = self._source_path(arguments)
        job = self.context.service.orchestrator.state.load(
            source,
            config_fingerprint=self.context.service.config.fingerprint(),
        )
        if job.status is JobStatus.COMPLETED:
            return {"job_id": job.job_id, "status": job.status.value, "skipped": True}
        with self.context.lock:
            if job.job_id in self.context.active:
                raise McpError(-32002, "job is already active in this MCP process")
        self.context.service.orchestrator.state.save(job)
        cancel_event = Event()
        with self.context.lock:
            self.context.active[job.job_id] = cancel_event
        future = self.context.executor.submit(
            self.context.service.start_translation,
            StartTranslationCommand(
                source_path=source,
                invocation_source=InvocationSource.MCP,
                cancel_event=cancel_event,
            ),
        )
        with self.context.lock:
            self.context.futures[job.job_id] = future

        def finish(_completed: object) -> None:
            with self.context.lock:
                self.context.active.pop(job.job_id, None)
                self.context.futures.pop(job.job_id, None)

        future.add_done_callback(finish)
        if future.done():
            finish(future)
        return {"job_id": job.job_id, "status": job.status.value}

    def _get_job(self, arguments: dict[str, object]) -> dict[str, object]:
        job = self._job(arguments)
        return {"job": job.to_dict()}

    def _list_jobs(self, arguments: dict[str, object]) -> dict[str, object]:
        if arguments:
            raise McpError(-32602, "babelcodex_list_jobs takes no arguments")
        return {"jobs": [job.to_dict() for job in self.context.service.list_jobs()]}

    def _cancel_job(self, arguments: dict[str, object]) -> dict[str, object]:
        job = self._job(arguments)
        with self.context.lock:
            cancel_event = self.context.active.get(job.job_id)
        if cancel_event is None:
            if job.status is JobStatus.RUNNING or job.status is JobStatus.RETRY_PENDING:
                raise McpError(-32002, "job cancellation handle is no longer available")
            return {"job_id": job.job_id, "cancelled": False, "status": job.status.value}
        cancel_event.set()
        return {"job_id": job.job_id, "cancelled": True, "status": "cancel_requested"}

    def _validate_output(self, arguments: dict[str, object]) -> dict[str, object]:
        job = self._job(arguments)
        try:
            result = self.context.service.validate_output(job.job_id)
        except ValueError as exc:
            raise McpError(-32004, str(exc)) from exc
        if any(
            artifact.get("reason") == "outside_output_directory" for artifact in result["artifacts"]
        ):
            raise McpError(-32003, "artifact path is outside the configured output directory")
        return result

    def _run_qa(self, arguments: dict[str, object]) -> dict[str, object]:
        job = self._job(arguments)
        try:
            return self.context.service.run_qa(job.job_id)
        except ValueError as exc:
            raise McpError(-32004, str(exc)) from exc

    def _cleanup_job(self, arguments: dict[str, object]) -> dict[str, object]:
        job = self._job(arguments)
        with self.context.lock:
            active_future = self.context.futures.get(job.job_id)
        if active_future is not None and not active_future.done():
            raise McpError(-32004, "cannot clean up an active job")
        if job.status in {JobStatus.RUNNING, JobStatus.RETRY_PENDING}:
            raise McpError(-32004, "cannot clean up an active job")
        work_root = self.context.service.config.babeldoc.working_dir.resolve()
        work_dir = work_root / f"job-{Path(job.source_path).stem}"
        try:
            work_dir = resolve_work_dir(work_root, work_dir)
        except WorkdirError as exc:
            raise McpError(-32005, str(exc)) from exc
        if not work_dir.exists():
            return {"job_id": job.job_id, "removed": False, "path": str(work_dir)}
        remove_work_dir(work_dir)
        return {"job_id": job.job_id, "removed": True, "path": str(work_dir)}

    def _source_path(self, arguments: dict[str, object]) -> Path:
        raw = arguments.get("source_path")
        if not isinstance(raw, str) or not raw:
            raise McpError(-32602, "source_path is required")
        input_root = self.context.service.config.project.input_dir.resolve()
        candidate = Path(raw).expanduser()
        source = (candidate if candidate.is_absolute() else input_root / candidate).resolve()
        try:
            source.relative_to(input_root)
        except ValueError as exc:
            raise McpError(-32003, "source_path is outside the configured input directory") from exc
        if source.suffix.lower() != ".pdf" or not source.is_file():
            raise McpError(
                -32003, "source_path must be an existing PDF in the configured input directory"
            )
        return source

    def _job(self, arguments: dict[str, object]) -> JobState:
        job_id = arguments.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            raise McpError(-32602, "job_id is required")
        job = self.context.service.get_job(job_id)
        if job is None:
            raise McpError(-32004, "job was not found")
        return job

    @staticmethod
    def _error(
        request_id: object, code: int, message: str, data: object | None = None
    ) -> dict[str, object]:
        error: dict[str, object] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def run_stdio(server: McpServer, stdin: TextIO, stdout: TextIO) -> None:
    """Process newline-delimited JSON-RPC messages until EOF."""
    try:
        for line in stdin:
            if not line.strip():
                continue
            try:
                response = server.handle(json.loads(line))
            except json.JSONDecodeError:
                response = server._error(None, -32700, "parse error")
            except McpError as exc:
                response = server._error(None, exc.code, str(exc), exc.data)
            if response is not None:
                stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                stdout.flush()
    finally:
        server.close()


def serve(service: BabelCodexService, stdin: TextIO, stdout: TextIO) -> None:
    run_stdio(McpServer(service), stdin, stdout)
