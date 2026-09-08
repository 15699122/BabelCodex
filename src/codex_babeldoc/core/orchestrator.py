from __future__ import annotations

import logging
import time
from pathlib import Path

from codex_babeldoc.backends.babeldoc_internal import BabelDocInternalBackend
from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.state import StateStore
from codex_babeldoc.translators.codex_sdk import CodexSdkTranslator
from codex_babeldoc.translators.mock import MockTranslator

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
        if t.translator == "mock":
            return MockTranslator()
        if t.translator == "codex-sdk":
            return CodexSdkTranslator(
                t.lang_in,
                t.lang_out,
                context_prompt=c.context_prompt,
                model=t.model,
                effort=t.effort,
            )
        raise ValueError(f"Unknown translator: {t.translator}")

    def run_one(self, source: Path, *, force: bool = False) -> str:
        job = self.state.load(source)
        if job.status == "completed" and not force:
            return "skipped"

        t = self.cfg.translation
        b = self.cfg.babeldoc
        last_error = None
        for attempt in range(job.attempts + 1, t.max_retries + 1):
            job.attempts = attempt
            job.status = "running"
            self.state.save(job)
            try:
                self.backend.translate(
                    source,
                    self.cfg.project.output_dir,
                    lang_in=t.lang_in,
                    lang_out=t.lang_out,
                    translator_factory=self.translator_factory,
                    no_mono=t.no_mono,
                    no_dual=t.no_dual,
                    qps=t.qps,
                    min_text_length=t.min_text_length,
                    working_dir=b.working_dir,
                    watermark_output_mode=t.watermark_output_mode,
                    auto_extract_glossary=t.auto_extract_glossary,
                    ocr_workaround=b.ocr_workaround,
                    auto_enable_ocr_workaround=b.auto_enable_ocr_workaround,
                    enhance_compatibility=b.enhance_compatibility,
                    translate_table_text=b.translate_table_text,
                )
                job.status = "completed"
                job.last_error = None
                self.state.save(job)
                return "completed"
            except Exception as exc:
                last_error = str(exc)
                job.status = "failed"
                job.last_error = last_error
                self.state.save(job)
                log.exception("Translation attempt %s failed for %s", attempt, source)
                if attempt < t.max_retries:
                    time.sleep(min(2 ** (attempt - 1), 8))
        raise RuntimeError(f"Translation failed after {t.max_retries} attempts: {last_error}")

    def run_all(self, *, force: bool = False) -> dict[str, str]:
        results = {}
        for source in self.discover():
            try:
                results[source.name] = self.run_one(source, force=force)
            except Exception as exc:  # noqa: BLE001 - batch boundary isolates documents
                results[source.name] = f"failed: {exc}"
        return results
