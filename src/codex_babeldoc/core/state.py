from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock

from codex_babeldoc.core.artifacts import Artifact
from codex_babeldoc.core.errors import ErrorCategory, ErrorCode

SCHEMA_VERSION = 2
STATE_TRANSIENT_RETRIES = 5
STATE_TRANSIENT_BACKOFF_SECONDS = 0.02


class JobStatus(StrEnum):
    DISCOVERED = "discovered"
    RUNNING = "running"
    RETRY_PENDING = "retry_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStage(StrEnum):
    DISCOVERED = "discovered"
    VALIDATING_INPUT = "validating_input"
    PREPARING_RUNTIME = "preparing_runtime"
    TRANSLATING = "translating"
    RENDERING = "rendering"
    VALIDATING_OUTPUT = "validating_output"
    COMPLETED = "completed"


@dataclass(slots=True)
class JobState:
    job_id: str
    source_path: str
    source_fingerprint: str
    config_fingerprint: str
    schema_version: int = SCHEMA_VERSION
    status: JobStatus = JobStatus.DISCOVERED
    stage: JobStage = JobStage.DISCOVERED
    attempts: int = 0
    error_category: ErrorCategory | None = None
    error_code: ErrorCode | None = None
    safe_error_message: str | None = None
    backend_name: str = ""
    backend_version: str = ""
    translator_name: str = ""
    model: str = ""
    codex_thread_id: str | None = None
    invocation_source: str = "cli"
    started_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    artifacts: list[Artifact] = field(default_factory=list)
    qa_status: str = "pending"

    @property
    def source(self) -> str:
        return self.source_path

    @property
    def fingerprint(self) -> str:
        return self.source_fingerprint

    @property
    def last_error(self) -> str | None:
        return self.safe_error_message

    @last_error.setter
    def last_error(self, value: str | None) -> None:
        self.safe_error_message = value

    def touch(self) -> None:
        self.updated_at = _now()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "source_path": self.source_path,
            "source_fingerprint": self.source_fingerprint,
            "config_fingerprint": self.config_fingerprint,
            "status": self.status.value if isinstance(self.status, JobStatus) else str(self.status),
            "stage": self.stage.value if isinstance(self.stage, JobStage) else str(self.stage),
            "attempts": self.attempts,
            "error_category": self.error_category.value if self.error_category else None,
            "error_code": self.error_code.value if self.error_code else None,
            "safe_error_message": self.safe_error_message,
            "backend_name": self.backend_name,
            "backend_version": self.backend_version,
            "translator_name": self.translator_name,
            "model": self.model,
            "codex_thread_id": self.codex_thread_id,
            "invocation_source": self.invocation_source,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "qa_status": self.qa_status,
        }

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> JobState:
        if "schema_version" not in values:
            return cls.from_legacy_dict(values)
        return cls(
            schema_version=int(values.get("schema_version", SCHEMA_VERSION)),
            job_id=str(values["job_id"]),
            source_path=str(values["source_path"]),
            source_fingerprint=str(values["source_fingerprint"]),
            config_fingerprint=str(values.get("config_fingerprint", "")),
            status=JobStatus(str(values.get("status", JobStatus.DISCOVERED.value))),
            stage=JobStage(str(values.get("stage", JobStage.DISCOVERED.value))),
            attempts=int(values.get("attempts", 0)),
            error_category=(
                ErrorCategory(str(values["error_category"]))
                if values.get("error_category")
                else None
            ),
            error_code=ErrorCode(str(values["error_code"])) if values.get("error_code") else None,
            safe_error_message=(
                str(values["safe_error_message"])
                if values.get("safe_error_message") is not None
                else None
            ),
            backend_name=str(values.get("backend_name", "")),
            backend_version=str(values.get("backend_version", "")),
            translator_name=str(values.get("translator_name", "")),
            model=str(values.get("model", "")),
            codex_thread_id=(
                str(values["codex_thread_id"]) if values.get("codex_thread_id") else None
            ),
            invocation_source=str(values.get("invocation_source", "cli")),
            started_at=str(values.get("started_at", "")),
            updated_at=str(values.get("updated_at", "")),
            completed_at=str(values.get("completed_at", "")),
            artifacts=[
                Artifact.from_dict(item)
                for item in values.get("artifacts", [])
                if isinstance(item, dict)
            ],
            qa_status=str(values.get("qa_status", "pending")),
        )

    @classmethod
    def from_legacy_dict(cls, values: dict[str, object]) -> JobState:
        source_fingerprint = str(values["fingerprint"])
        status_value = str(values.get("status", "pending"))
        status_map = {
            "pending": JobStatus.DISCOVERED,
            "running": JobStatus.RUNNING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
        }
        status = status_map.get(status_value, JobStatus.DISCOVERED)
        stage = JobStage.COMPLETED if status is JobStatus.COMPLETED else JobStage.DISCOVERED
        return cls(
            job_id=job_id_for(source_fingerprint, ""),
            source_path=str(values["source"]),
            source_fingerprint=source_fingerprint,
            config_fingerprint="",
            status=status,
            stage=stage,
            attempts=int(values.get("attempts", 0)),
            safe_error_message=(
                str(values["last_error"]) if values.get("last_error") is not None else None
            ),
            updated_at=str(values.get("updated_at", "")),
            completed_at=str(values.get("updated_at", "")) if status is JobStatus.COMPLETED else "",
        )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def file_fingerprint(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def job_id_for(source_fingerprint: str, config_fingerprint: str) -> str:
    payload = f"{source_fingerprint}:{config_fingerprint}".encode()
    return sha256(payload).hexdigest()


def _read_state_json(path: Path) -> dict:
    """Read a state JSON file, tolerating transient Windows file-lock errors.

    :meth:`StateStore.save` swaps the state file atomically via ``os.replace``.
    On Windows, an overlapping read (for example a job-status poll while the
    async executor persists a terminal status) can fail transiently with
    ``PermissionError`` even though the state file itself is readable. Retry
    with the same bounded exponential backoff used by the write path.
    """
    last_error: PermissionError | None = None
    for attempt in range(STATE_TRANSIENT_RETRIES):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except PermissionError as error:
            last_error = error
            if attempt == STATE_TRANSIENT_RETRIES - 1:
                raise
            time.sleep(STATE_TRANSIENT_BACKOFF_SECONDS * (2**attempt))
    raise last_error  # pragma: no cover - the loop always returns or raises


class StateStore:
    def __init__(self, root: Path):
        self.root = root
        self._save_lock = RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.root / f"{job_id}.json"

    def load(self, source: Path, *, config_fingerprint: str = "") -> JobState:
        source = source.resolve()
        source_fp = file_fingerprint(source)
        job_id = job_id_for(source_fp, config_fingerprint)
        path = self._path(job_id)
        if path.exists():
            return JobState.from_dict(_read_state_json(path))
        legacy_path = self.root / f"{source_fp}.json"
        if legacy_path.exists():
            legacy = JobState.from_dict(_read_state_json(legacy_path))
            legacy.job_id = job_id
            legacy.config_fingerprint = config_fingerprint
            return legacy
        job = JobState(
            job_id=job_id,
            source_path=str(source),
            source_fingerprint=source_fp,
            config_fingerprint=config_fingerprint,
        )
        job.touch()
        return job

    def load_by_job_id(self, job_id: str) -> JobState | None:
        path = self._path(job_id)
        if not path.exists():
            return None
        return JobState.from_dict(_read_state_json(path))

    def list_jobs(self) -> list[JobState]:
        jobs: list[JobState] = []
        for path in sorted(self.root.glob("*.json")):
            try:
                jobs.append(JobState.from_dict(_read_state_json(path)))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return sorted(jobs, key=lambda job: job.updated_at, reverse=True)

    def save(self, job: JobState) -> None:
        with self._save_lock:
            job.touch()
            target = self._path(job.job_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{job.job_id}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                json.dump(job.to_dict(), temporary, ensure_ascii=False, indent=2)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            try:
                for attempt in range(STATE_TRANSIENT_RETRIES):
                    try:
                        os.replace(temporary_path, target)
                        break
                    except PermissionError:
                        if attempt == STATE_TRANSIENT_RETRIES - 1:
                            raise
                        time.sleep(STATE_TRANSIENT_BACKOFF_SECONDS * (2**attempt))
            finally:
                temporary_path.unlink(missing_ok=True)
