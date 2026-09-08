"""Backward-compatible facade over the versioned BabelDOC backend.

All BabelDOC internals live in :mod:`codex_babeldoc.backends.babeldoc_v064`.
New code should depend on :mod:`codex_babeldoc.backends.base` types and the
:class:`~codex_babeldoc.backends.babeldoc_v064.BabelDocV064Backend` directly.
This facade keeps the pre-existing ``translate(...)`` keyword interface working
while the orchestrator migrates to the versioned backend contract.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from codex_babeldoc.backends.babeldoc_v064 import BabelDocV064Backend
from codex_babeldoc.backends.base import ProgressEvent


class BabelDocInternalBackend:
    """Legacy keyword-style entry point delegating to the 0.6.x backend."""

    def __init__(self) -> None:
        self._backend = BabelDocV064Backend()

    def translate(
        self,
        source: Path,
        output_dir: Path,
        *,
        lang_in: str,
        lang_out: str,
        translator_factory: Callable[[], object],
        no_mono: bool,
        no_dual: bool,
        qps: int,
        min_text_length: int,
        working_dir: Path,
        watermark_output_mode: str,
        auto_extract_glossary: bool,
        ocr_workaround: bool,
        auto_enable_ocr_workaround: bool,
        enhance_compatibility: bool,
        translate_table_text: bool,
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> object:
        from codex_babeldoc.backends.base import PdfTranslateRequest

        request = PdfTranslateRequest(
            protocol_version=1,
            job_id="legacy-facade",
            source_path=source,
            output_dir=output_dir,
            working_dir=working_dir,
            lang_in=lang_in,
            lang_out=lang_out,
            backend_name=self._backend.name,
            backend_version=self._backend.version,
            produce_mono=not no_mono,
            produce_dual=not no_dual,
            config_fingerprint="",
            qps=qps,
            min_text_length=min_text_length,
            watermark_output_mode=watermark_output_mode,
            auto_extract_glossary=auto_extract_glossary,
            ocr_workaround=ocr_workaround,
            auto_enable_ocr_workaround=auto_enable_ocr_workaround,
            enhance_compatibility=enhance_compatibility,
            translate_table_text=translate_table_text,
        )
        backend_kwargs = {}
        if on_progress is not None:
            backend_kwargs["on_progress"] = on_progress
        result = self._backend.translate(request, translator_factory, **backend_kwargs)
        return result.raw
