from __future__ import annotations

import io
import logging
import os
import warnings
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Event

logger = logging.getLogger(__name__)

from codex_babeldoc.backends.base import ProgressEvent
from codex_babeldoc.core.artifact_manifest import validate_artifacts
from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.orchestrator import Orchestrator
from codex_babeldoc.core.private_data import ensure_private_dir, restrict_file
from codex_babeldoc.core.state import JOB_ID_PATTERN, JobState, JobStatus
from codex_babeldoc.translation.context import ContextExtractor
from codex_babeldoc.translation.glossary import (
    GlossaryEntry,
    read_csv,
    version_for,
    write_csv,
)


def _format_warnings(recorded: list[Warning]) -> str:
    """Return a compact, non-sensitive summary of recorded warnings."""

    def _mesg(w: Warning) -> str:
        base = str(w.message)
        cat = type(w.category).__name__
        loc = ""
        try:
            fn = w.filename  # type: ignore[attr-defined]
            _ln = w.lineno  # type: ignore[attr-defined]
        except AttributeError:
            fn = None
        if fn:
            loc = f" at {Path(fn).name}:{w.lineno}"  # type: ignore[attr-defined]
        return f"[{cat}] {base}{loc}"

    return " | ".join(_mesg(w) for w in recorded)


class InvocationSource(StrEnum):
    CLI = "cli"
    GUI = "gui"
    MCP = "mcp"


@dataclass(slots=True, frozen=True)
class StartTranslationCommand:
    source_path: Path
    force: bool = False
    invocation_source: InvocationSource = InvocationSource.CLI
    on_progress: Callable[[ProgressEvent], None] | None = None
    cancel_event: Event | None = None


class BabelCodexService:
    """Shared application boundary for CLI, GUI and MCP callers."""

    def __init__(self, config: AppConfig, orchestrator: Orchestrator | None = None) -> None:
        self.config = config
        self.orchestrator = orchestrator or Orchestrator(config)

    def start_translation(self, command: StartTranslationCommand) -> JobState:
        resolved = command.source_path.resolve()
        kwargs = {
            "force": command.force,
            "invocation_source": command.invocation_source.value,
        }
        if command.on_progress is not None:
            kwargs["on_progress"] = command.on_progress
        if command.cancel_event is not None:
            kwargs["cancel_event"] = command.cancel_event
        self.orchestrator.run_one(resolved, **kwargs)
        return self.orchestrator.state.load(
            resolved,
            config_fingerprint=self.config.fingerprint(),
        )

    def get_job(self, job_id: str) -> JobState | None:
        self._validate_job_id(job_id)
        return self.orchestrator.state.load_by_job_id(job_id)

    def list_jobs(self) -> list[JobState]:
        return self.orchestrator.state.list_jobs()

    def inspect_job(self, job_id: str) -> dict[str, object] | None:
        job = self.get_job(job_id)
        return self.job_view(job) if job is not None else None

    @staticmethod
    def job_view(job: JobState | None) -> dict[str, object] | None:
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
            "artifacts": [
                {
                    "artifact_type": artifact.artifact_type.value,
                    # External DTOs must not expose local absolute paths. The
                    # service and manifest retain the full path internally.
                    "path": Path(artifact.path).name,
                    "size": artifact.size,
                    "sha256": artifact.sha256,
                    "created_at": artifact.created_at,
                    "validated": artifact.validated,
                }
                for artifact in job.artifacts
            ],
            "qa_status": job.qa_status,
        }

    @staticmethod
    def _validate_job_id(job_id: str) -> None:
        if not isinstance(job_id, str) or JOB_ID_PATTERN.fullmatch(job_id) is None:
            raise ValueError("job_id is invalid")

    def validate_output(self, job_id: str) -> dict[str, object]:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError("job was not found")
        if job.status in {JobStatus.RUNNING, JobStatus.RETRY_PENDING}:
            raise ValueError("cannot validate an active job")
        validated, artifacts = validate_artifacts(
            job.artifacts, self.config.project.output_dir, update=True
        )
        job.qa_status = "passed" if validated else "failed"
        self.orchestrator.state.save(job)
        return {
            "job_id": job.job_id,
            "validated": validated,
            "qa_status": job.qa_status,
            "artifacts": artifacts,
        }

    def run_qa(self, job_id: str, *, deep: bool = True, verbose: bool = False) -> dict[str, object]:
        """Run the PDF QA battery over a terminal job's output artifacts.

        QA reports are diagnostic summaries written to ``output_dir/qa/`` and
        deliberately do not join ``job.artifacts``: regenerated reports must
        not disturb artifact manifest integrity checks. Any ERROR-level
        finding sets ``qa_status`` to ``failed`` so abnormal output is never
        marked as fully successful.

        Warnings and stderr emitted during QA are captured and routed to the
        process log so that CLI stdout remains clean JSON through the QA path.
        """
        from codex_babeldoc.core.artifacts import ArtifactType
        from codex_babeldoc.qa.report import (
            run_qa as run_report,
        )
        from codex_babeldoc.qa.report import (
            save_report,
            to_text,
        )

        _captured_warnings = io.StringIO()
        with warnings.catch_warnings(record=True) as _recorded:
            warnings.simplefilter("always")
            try:
                job = self.get_job(job_id)
                if job is None:
                    raise ValueError("job was not found")
                if job.status in {JobStatus.RUNNING, JobStatus.RETRY_PENDING}:
                    raise ValueError("cannot run QA on an active job")

                pdf_artifacts = [
                    artifact
                    for artifact in job.artifacts
                    if artifact.artifact_type in {ArtifactType.MONO_PDF, ArtifactType.DUAL_PDF}
                ]
                source_path = Path(job.source_path)
                if not source_path.is_file():
                    source_path = None

                qa_dir = self.config.project.output_dir / "qa"
                results: list[dict[str, object]] = []
                all_ok = True
                for artifact in pdf_artifacts:
                    target = Path(artifact.path)
                    if not target.is_file():
                        all_ok = False
                        results.append(
                            {
                                "artifact": artifact.artifact_type.value,
                                "ok": False,
                                "path": str(target),
                                "summary": "output file is missing",
                            }
                        )
                        continue
                    stem = f"{Path(job.source_path).stem}.{artifact.artifact_type.value}"
                    report = run_report(
                        target,
                        lang_out=self.config.translation.lang_out,
                        source_path=source_path,
                        deep=deep,
                    )
                    report_path = save_report(report, qa_dir, stem)
                    results.append(
                        {
                            "artifact": artifact.artifact_type.value,
                            "ok": report.ok,
                            "path": str(target),
                            "report": str(report_path),
                            "summary": to_text(report, verbosity=2 if verbose else 0),
                        }
                    )
                    if not report.ok:
                        all_ok = False

                job.qa_status = "passed" if all_ok else "failed"
                self.orchestrator.state.save(job)
                return {
                    "job_id": job.job_id,
                    "qa_status": job.qa_status,
                    "ok": all_ok,
                    "reports": results,
                }
            except Exception:
                _captured_warnings.write(_format_warnings(_recorded))
                raise
            finally:
                _captured_warnings.write(_format_warnings(_recorded))
                if _captured_warnings.getvalue():
                    logger.warning("QA warnings captured: %s", _captured_warnings.getvalue())

    def cleanup_work_dirs(self, *, dry_run: bool = False) -> dict[str, object]:
        """Sweep terminal job working directories older than the retention window."""
        from codex_babeldoc.core.workdir import sweep_work_dirs

        return sweep_work_dirs(
            self.config.babeldoc.working_dir,
            self.list_jobs(),
            retention_days=self.config.babeldoc.work_retention_days,
            dry_run=dry_run,
        )

    def retry_job(
        self, job_id: str, *, invocation_source: InvocationSource = InvocationSource.CLI
    ) -> JobState:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError("job was not found")
        if job.status in {JobStatus.RUNNING, JobStatus.RETRY_PENDING}:
            raise ValueError("cannot retry an active job")
        return self.start_translation(
            StartTranslationCommand(
                source_path=Path(job.source_path),
                force=True,
                invocation_source=invocation_source,
            )
        )

    def list_glossary(
        self, *, scope: str = "global", document_id: str | None = None
    ) -> dict[str, object]:
        path = self._glossary_path(scope=scope, document_id=document_id)
        entries = read_csv(path) if path.is_file() else ()
        return {
            "scope": scope,
            "document_id": document_id,
            "entries": [asdict(entry) for entry in entries],
            "version": version_for(entries) if entries else None,
        }

    def save_glossary(
        self,
        entries: list[dict[str, object]],
        *,
        scope: str = "global",
        document_id: str | None = None,
    ) -> dict[str, object]:
        normalized = tuple(
            GlossaryEntry(
                source=str(item.get("source", "")).strip(),
                target=str(item.get("target", "")).strip(),
                notes=str(item.get("notes", "")).strip(),
                enabled=self._as_bool(item.get("enabled", True)),
            )
            for item in entries
        )
        if any(not entry.source for entry in normalized):
            raise ValueError("glossary entries require a source term")
        path = self._glossary_path(scope=scope, document_id=document_id)
        write_csv(path, normalized)
        return self.list_glossary(scope=scope, document_id=document_id)

    def get_context(self, document_id: str) -> dict[str, object]:
        path = self._context_path(document_id)
        raw = path.read_text(encoding="utf-8") if path.is_file() else ""
        context = ContextExtractor(max_chars=self.config.codex.context_max_chars).from_text(raw)
        return {
            "document_id": document_id,
            "text": raw,
            "title": context.title,
            "abstract": context.abstract,
            "version": context.version,
        }

    def save_context(self, document_id: str, text: str) -> dict[str, object]:
        path = self._context_path(document_id)
        ensure_private_dir(path.parent)
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        restrict_file(temporary)
        try:
            os.replace(temporary, path)
            restrict_file(path)
        finally:
            temporary.unlink(missing_ok=True)
        return self.get_context(document_id)

    def _glossary_path(self, *, scope: str, document_id: str | None) -> Path:
        if scope == "global" and document_id is None:
            return self.config.project.glossary_dir / "global.csv"
        if scope == "document" and document_id:
            return (
                self.config.project.glossary_dir
                / "documents"
                / f"{self._safe_document_id(document_id)}.csv"
            )
        raise ValueError("scope must be global or document with a document_id")

    def _context_path(self, document_id: str) -> Path:
        return self.config.project.context_dir / f"{self._safe_document_id(document_id)}.txt"

    @staticmethod
    def _safe_document_id(document_id: str) -> str:
        candidate = document_id.strip()
        if (
            not candidate
            or Path(candidate).name != candidate
            or "/" in candidate
            or "\\" in candidate
            or candidate in {".", ".."}
        ):
            raise ValueError("document_id must be a single document stem")
        return candidate

    @staticmethod
    def _as_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "no", "off"}
        return bool(value)

    def close(self) -> None:
        """Release resources owned by the shared application service."""
        close = getattr(self.orchestrator, "close", None)
        if callable(close):
            close()
