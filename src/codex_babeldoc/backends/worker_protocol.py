"""Versioned JSON protocol between the orchestrator and the BabelDOC worker.

The worker process owns all BabelDOC internals. Communication is file-based:

- request:  a versioned JSON document on disk
- progress: JSONL lines on the worker's stderr
- result:   a single JSON document on the worker's stdout

Third-party ``print`` output must never reach stdout; the worker entry point
redirects plain stdout writes to stderr before anything else is imported.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROTOCOL_VERSION = 1

# Exit codes emitted by the worker entry point.
EXIT_COMPLETED = 0
EXIT_REQUEST_INVALID = 2
EXIT_TRANSLATION_FAILED = 3
EXIT_CRASHED = 4


@dataclass(slots=True, frozen=True)
class TranslatorSpec:
    """JSON-serializable description of the translator to build in-process."""

    name: str
    lang_in: str
    lang_out: str
    context_prompt: str | None = None
    model: str | None = None
    effort: str | None = None
    cache_path: str | None = None
    cache_enabled: bool = True
    cache_store_plaintext: bool = True
    cache_ttl_seconds: int | None = None
    glossary_prompt: str = ""
    glossary_version: str | None = None
    context_version: str | None = None
    thread_state_path: str | None = None
    document_id: str | None = None


@dataclass(slots=True, frozen=True)
class WorkerRequest:
    """Envelope sent to the worker process."""

    request: dict  # PdfTranslateRequest fields (paths as strings)
    translator: TranslatorSpec
    protocol_version: int = PROTOCOL_VERSION

    def to_json(self) -> str:
        return json.dumps(
            {
                "protocol_version": self.protocol_version,
                "request": self.request,
                "translator": asdict(self.translator),
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, raw: str) -> WorkerRequest:
        data = json.loads(raw)
        if int(data.get("protocol_version", 0)) != PROTOCOL_VERSION:
            raise ValueError(f"unsupported worker protocol version: {data.get('protocol_version')}")
        t = data["translator"]
        return cls(
            request=dict(data["request"]),
            translator=TranslatorSpec(
                name=str(t["name"]),
                lang_in=str(t["lang_in"]),
                lang_out=str(t["lang_out"]),
                context_prompt=t.get("context_prompt"),
                model=t.get("model"),
                effort=t.get("effort"),
                cache_path=t.get("cache_path"),
                cache_enabled=bool(t.get("cache_enabled", True)),
                cache_store_plaintext=bool(t.get("cache_store_plaintext", True)),
                cache_ttl_seconds=t.get("cache_ttl_seconds"),
                glossary_prompt=str(t.get("glossary_prompt", "")),
                glossary_version=t.get("glossary_version"),
                context_version=t.get("context_version"),
                thread_state_path=t.get("thread_state_path"),
                document_id=t.get("document_id"),
            ),
            protocol_version=PROTOCOL_VERSION,
        )


@dataclass(slots=True, frozen=True)
class WorkerArtifact:
    artifact_type: str
    path: str
    size: int


@dataclass(slots=True, frozen=True)
class WorkerProgress:
    stage: str
    stage_current: int | None = None
    stage_total: int | None = None
    overall_progress: float | None = None
    message: str | None = None


@dataclass(slots=True, frozen=True)
class WorkerResult:
    job_id: str
    artifacts: list[WorkerArtifact] = field(default_factory=list)
    total_seconds: float = 0.0
    backend_name: str = ""
    backend_version: str = ""

    def to_json(self) -> str:
        return json.dumps(
            {
                "protocol_version": PROTOCOL_VERSION,
                "status": "completed",
                "result": {
                    "job_id": self.job_id,
                    "artifacts": [asdict(a) for a in self.artifacts],
                    "total_seconds": self.total_seconds,
                    "backend_name": self.backend_name,
                    "backend_version": self.backend_version,
                },
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, raw: str) -> WorkerResult:
        data = json.loads(raw)
        if int(data.get("protocol_version", 0)) != PROTOCOL_VERSION:
            raise ValueError(f"unsupported worker protocol version: {data.get('protocol_version')}")
        if data.get("status") != "completed":
            raise ValueError(f"unexpected worker status: {data.get('status')}")
        r = data["result"]
        return cls(
            job_id=str(r["job_id"]),
            artifacts=[
                WorkerArtifact(
                    artifact_type=str(a["artifact_type"]),
                    path=str(a["path"]),
                    size=int(a["size"]),
                )
                for a in r.get("artifacts", [])
            ],
            total_seconds=float(r.get("total_seconds", 0.0)),
            backend_name=str(r.get("backend_name", "")),
            backend_version=str(r.get("backend_version", "")),
        )


@dataclass(slots=True, frozen=True)
class WorkerError:
    category: str
    code: str
    safe_message: str
    retryable: bool = False
    technical_message: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "protocol_version": PROTOCOL_VERSION,
                "status": "failed",
                "error": {
                    "category": self.category,
                    "code": self.code,
                    "safe_message": self.safe_message,
                    "retryable": self.retryable,
                    "technical_message": self.technical_message,
                },
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, raw: str) -> WorkerError:
        data = json.loads(raw)
        if int(data.get("protocol_version", 0)) != PROTOCOL_VERSION:
            raise ValueError(f"unsupported worker protocol version: {data.get('protocol_version')}")
        e = data["error"]
        return cls(
            category=str(e["category"]),
            code=str(e["code"]),
            safe_message=str(e["safe_message"]),
            retryable=bool(e.get("retryable", False)),
            technical_message=e.get("technical_message"),
        )


def encode_progress(event: WorkerProgress) -> str:
    payload = {"type": "progress", **asdict(event)}
    return json.dumps(payload, ensure_ascii=False)


def decode_progress(line: str) -> WorkerProgress | None:
    """Parse one stderr line; return None for non-protocol output."""
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if data.get("type") != "progress":
        return None
    return WorkerProgress(
        stage=str(data.get("stage", "unknown")),
        stage_current=data.get("stage_current"),
        stage_total=data.get("stage_total"),
        overall_progress=data.get("overall_progress"),
        message=data.get("message"),
    )


def request_file_path(working_dir: Path, job_id: str) -> Path:
    return working_dir / f"worker-request-{job_id}.json"
