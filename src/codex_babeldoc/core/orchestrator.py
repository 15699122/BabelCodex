from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path
from threading import Event

from codex_babeldoc.backends.babeldoc_internal import BabelDocInternalBackend
from codex_babeldoc.backends.base import ProgressEvent
from codex_babeldoc.backends.worker_client import build_worker_request, run_worker
from codex_babeldoc.backends.worker_protocol import TranslatorSpec
from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.errors import classify_exception
from codex_babeldoc.core.state import JobStage, JobStatus, StateStore
from codex_babeldoc.translators.factory import build_gateway_translator

log = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.cfg.ensure_dirs()
        self.state = StateStore(cfg.project.state_dir)
        self.backend = BabelDocInternalBackend()

    def discover(self) -> list[Path]:
        return sorted(self.cfg.project.input_dir.glob("*.pdf"))

    def translator_factory(self):
        t = self.cfg.translation
        c = self.cfg.codex
        if t.translator not in {"mock", "codex-sdk"}:
            raise ValueError(f"Unknown translator: {t.translator}")
        return build_gateway_translator(
            TranslatorSpec(
                name=t.translator,
                lang_in=t.lang_in,
                lang_out=t.lang_out,
                context_prompt=c.context_prompt or None,
                model=t.model or None,
                effort=t.effort or None,
                cache_path=str(self.cfg.project.state_dir / "translation-cache.db")
                if t.cache_enabled
                else None,
                cache_enabled=t.cache_enabled,
                cache_store_plaintext=t.cache_store_plaintext,
                cache_ttl_seconds=t.cache_ttl_seconds,
            )
        )

    def _translator_spec(self) -> TranslatorSpec:
        t = self.cfg.translation
        c = self.cfg.codex
        return TranslatorSpec(
            name=t.translator,
            lang_in=t.lang_in,
            lang_out=t.lang_out,
            context_prompt=c.context_prompt or None,
            model=t.model or None,
            effort=t.effort or None,
            cache_path=str(self.cfg.project.state_dir / "translation-cache.db")
            if t.cache_enabled
            else None,
            cache_enabled=t.cache_enabled,
            cache_store_plaintext=t.cache_store_plaintext,
            cache_ttl_seconds=t.cache_ttl_seconds,
        )

    def _translate_via_worker(
        self,
        source: Path,
        *,
        on_progress: Callable[[ProgressEvent], None] | None = None,
        cancel_event: Event | None = None,
    ) -> None:
        b = self.cfg.babeldoc
        t = self.cfg.translation
        request = {
            "job_id": f"job-{source.stem}",
            "source_path": str(source),
            "output_dir": str(self.cfg.project.output_dir),
            "working_dir": str(b.working_dir / f"job-{source.stem}"),
            "lang_in": t.lang_in,
            "lang_out": t.lang_out,
            "backend_name": b.backend,
            "produce_mono": not t.no_mono,
            "produce_dual": not t.no_dual,
            "qps": t.qps,
            "min_text_length": t.min_text_length,
            "watermark_output_mode": t.watermark_output_mode,
            "auto_extract_glossary": t.auto_extract_glossary,
            "ocr_workaround": b.ocr_workaround,
            "auto_enable_ocr_workaround": b.auto_enable_ocr_workaround,
            "enhance_compatibility": b.enhance_compatibility,
            "translate_table_text": b.translate_table_text,
        }
        spec = self._translator_spec()
        worker_request = build_worker_request(
            request,
            {
                "name": spec.name,
                "lang_in": spec.lang_in,
                "lang_out": spec.lang_out,
                "context_prompt": spec.context_prompt,
                "model": spec.model,
                "effort": spec.effort,
                "cache_path": spec.cache_path,
                "cache_enabled": spec.cache_enabled,
                "cache_store_plaintext": spec.cache_store_plaintext,
                "cache_ttl_seconds": spec.cache_ttl_seconds,
            },
        )
        run_worker(
            worker_request,
            working_dir=b.working_dir / f"job-{source.stem}",
            job_id=f"job-{source.stem}",
            on_progress=lambda event: self._forward_progress(event, on_progress),
            cancel_event=cancel_event,
        )

    @staticmethod
    def _forward_progress(
        event,
        on_progress: Callable[[ProgressEvent], None] | None,
    ) -> None:
        log.info("worker %s: %s", event.stage, event.message or "")
        if on_progress is not None:
            on_progress(
                ProgressEvent(
                    stage=event.stage,
                    stage_current=event.stage_current,
                    stage_total=event.stage_total,
                    overall_progress=event.overall_progress,
                    message=event.message,
                )
            )

    def run_one(
        self,
        source: Path,
        *,
        force: bool = False,
        invocation_source: str = "cli",
        on_progress: Callable[[ProgressEvent], None] | None = None,
        cancel_event: Event | None = None,
    ) -> str:
        job = self.state.load(source, config_fingerprint=self.cfg.fingerprint())
        job.invocation_source = invocation_source
        job.backend_name = self.cfg.babeldoc.backend
        job.translator_name = self.cfg.translation.translator
        job.model = self.cfg.translation.model
        if job.status is JobStatus.COMPLETED and not force:
            return "skipped"

        # A forced re-run of an already-completed job must reset the attempt
        # counter, otherwise the retry loop range is empty and we never run.
        if force:
            job.attempts = 0

        t = self.cfg.translation
        b = self.cfg.babeldoc
        last_error = None
        for attempt in range(job.attempts + 1, t.max_retries + 1):
            job.attempts = attempt
            job.status = JobStatus.RUNNING
            job.stage = JobStage.PREPARING_RUNTIME
            job.error_category = None
            job.error_code = None
            job.safe_error_message = None
            if not job.started_at:
                job.started_at = job.updated_at
            self.state.save(job)
            try:
                job.stage = JobStage.TRANSLATING
                self.state.save(job)
                if b.worker_mode == "subprocess":
                    self._translate_via_worker(
                        source,
                        on_progress=on_progress,
                        cancel_event=cancel_event,
                    )
                else:
                    backend_kwargs = {
                        "lang_in": t.lang_in,
                        "lang_out": t.lang_out,
                        "translator_factory": self.translator_factory,
                        "no_mono": t.no_mono,
                        "no_dual": t.no_dual,
                        "qps": t.qps,
                        "min_text_length": t.min_text_length,
                        "working_dir": b.working_dir,
                        "watermark_output_mode": t.watermark_output_mode,
                        "auto_extract_glossary": t.auto_extract_glossary,
                        "ocr_workaround": b.ocr_workaround,
                        "auto_enable_ocr_workaround": b.auto_enable_ocr_workaround,
                        "enhance_compatibility": b.enhance_compatibility,
                        "translate_table_text": b.translate_table_text,
                    }
                    if on_progress is not None:
                        backend_kwargs["on_progress"] = on_progress
                    self.backend.translate(
                        source,
                        self.cfg.project.output_dir,
                        **backend_kwargs,
                    )
                job.status = JobStatus.COMPLETED
                job.stage = JobStage.COMPLETED
                job.completed_at = job.updated_at
                job.safe_error_message = None
                self.state.save(job)
                return "completed"
            except Exception as exc:
                worker_error = getattr(exc, "error", None)
                if getattr(worker_error, "code", None) == "CANCELLED":
                    job.status = JobStatus.CANCELLED
                    job.error_category = None
                    job.error_code = None
                    job.safe_error_message = None
                    self.state.save(job)
                    return "cancelled"
                error = classify_exception(exc)
                last_error = error.safe_message
                job.status = JobStatus.FAILED
                job.error_category = error.category
                job.error_code = error.code
                job.safe_error_message = error.safe_message
                self.state.save(job)
                log.exception("Translation attempt %s failed for %s", attempt, source)
                if attempt < t.max_retries and error.retryable:
                    job.status = JobStatus.RETRY_PENDING
                    self.state.save(job)
                    time.sleep(min(2 ** (attempt - 1), 8))
                else:
                    break
        raise RuntimeError(f"Translation failed after {t.max_retries} attempts: {last_error}")

    def run_all(self, *, force: bool = False) -> dict[str, str]:
        results = {}
        for source in self.discover():
            try:
                results[source.name] = self.run_one(source, force=force)
            except Exception as exc:  # noqa: BLE001 - batch boundary isolates documents
                results[source.name] = f"failed: {exc}"
        return results
