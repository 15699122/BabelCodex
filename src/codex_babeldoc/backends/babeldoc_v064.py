"""BabelDOC 0.6.x compatibility implementation.

Every BabelDOC-internal import and every version-sensitive mapping lives in
this module. Other layers must use :mod:`codex_babeldoc.backends.base` types
only.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from codex_babeldoc.backends.base import PdfTranslateRequest, PdfTranslateResult, ProgressEvent
from codex_babeldoc.core.artifacts import Artifact, ArtifactType
from codex_babeldoc.core.errors import BabelCodexError, ErrorCategory, ErrorCode

SUPPORTED_MAJOR_MINOR = (0, 6)

_WATERMARK_MODES: dict[str, str] = {
    "watermarked": "Watermarked",
    "no_watermark": "NoWatermark",
    "both": "Both",
}


def detect_version() -> str | None:
    """Return the installed BabelDOC version, or ``None`` when unavailable."""
    try:
        import babeldoc

        version = getattr(babeldoc, "__version__", None)
        if version:
            return str(version)
    except ImportError:
        pass
    try:
        from importlib.metadata import version as pkg_version

        return pkg_version("BabelDOC")
    except Exception:  # noqa: BLE001 - any failure means "not available"
        return None


def is_supported_version(version: str | None) -> bool:
    """Check a version string against the supported 0.6.x range."""
    if not version:
        return False
    try:
        parts = tuple(int(p) for p in version.split(".")[:2])
    except ValueError:
        return False
    return len(parts) == 2 and parts == SUPPORTED_MAJOR_MINOR


def assert_supported(version: str | None) -> str:
    """Return the version or raise a structured compatibility error."""
    if version is None:
        raise BabelCodexError(
            category=ErrorCategory.BABELDOC,
            code=ErrorCode.BABELDOC_NOT_INSTALLED,
            safe_message="BabelDOC runtime is not installed.",
            technical_message="import of babeldoc failed",
        )
    if not is_supported_version(version):
        raise BabelCodexError(
            category=ErrorCategory.BABELDOC,
            code=ErrorCode.BABELDOC_VERSION_UNSUPPORTED,
            safe_message=f"Unsupported BabelDOC version {version}; expected 0.6.x.",
            technical_message=f"detected={version} supported={SUPPORTED_MAJOR_MINOR}",
        )
    return version


def normalize_watermark_mode(mode: str) -> str:
    """Map a project watermark mode to the BabelDOC enum member name."""
    try:
        return _WATERMARK_MODES[mode]
    except KeyError as exc:
        raise BabelCodexError(
            category=ErrorCategory.CONFIG,
            code=ErrorCode.CONFIG_INVALID,
            safe_message=f"Unknown watermark output mode: {mode}",
            technical_message=str(exc),
        ) from exc


def artifacts_from_result(raw: Any) -> list[Artifact]:
    """Extract mono/dual PDF artifacts from a BabelDOC TranslateResult."""
    artifacts: list[Artifact] = []
    for artifact_type, attr in (
        (ArtifactType.MONO_PDF, "mono_pdf_path"),
        (ArtifactType.DUAL_PDF, "dual_pdf_path"),
    ):
        value = getattr(raw, attr, None)
        if not value:
            continue
        path = Path(value)
        size = path.stat().st_size if path.is_file() else 0
        artifacts.append(Artifact(artifact_type=artifact_type, path=str(path), size=size))
    return artifacts


def convert_progress(event: dict[str, Any]) -> ProgressEvent | None:
    """Convert a raw BabelDOC event dict into a normalized progress event."""
    etype = str(event.get("type", ""))
    if etype in {"finish", "error"}:
        return None
    stage = str(event.get("stage") or etype or "unknown")
    return ProgressEvent(
        stage=stage,
        stage_current=_as_int(event.get("stage_current")),
        stage_total=_as_int(event.get("stage_total")),
        overall_progress=_as_float(event.get("overall_progress")),
        message=str(event.get("message")) if event.get("message") is not None else None,
    )


def _as_int(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def _as_float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _babeldoc_error(exc: Exception) -> BabelCodexError:
    return BabelCodexError(
        category=ErrorCategory.BABELDOC,
        code=ErrorCode.BABELDOC_RUNTIME_ERROR,
        safe_message="The BabelDOC PDF pipeline failed.",
        retryable=True,
        technical_message=str(exc),
    )


class BabelDocV064Backend:
    """PdfBackend implementation pinned to BabelDOC 0.6.x.

    This is the only class allowed to import BabelDOC internals. All
    version-sensitive behaviour (config construction, watermark mode mapping,
    event normalization, result extraction) is owned here.
    """

    name = "babeldoc"

    @property
    def version(self) -> str:
        version = detect_version()
        return "unavailable" if version is None else version

    def is_available(self) -> bool:
        return is_supported_version(detect_version())

    def ensure_ready(self) -> str:
        """Validate the runtime version before starting expensive work."""
        return assert_supported(detect_version())

    def translate(
        self,
        request: PdfTranslateRequest,
        translator_factory: Callable[[], object],
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> PdfTranslateResult:
        version = self.ensure_ready()
        started = time.monotonic()
        try:
            raw = asyncio.run(self._translate_async(request, translator_factory, on_progress))
        except BabelCodexError:
            raise
        except Exception as exc:
            raise _babeldoc_error(exc) from exc

        return PdfTranslateResult(
            job_id=request.job_id,
            artifacts=artifacts_from_result(raw),
            total_seconds=time.monotonic() - started,
            backend_name=self.name,
            backend_version=version,
            glossary=getattr(raw, "glossary", None),
            raw=raw,
        )

    async def _translate_async(
        self,
        request: PdfTranslateRequest,
        translator_factory: Callable[[], object],
        on_progress: Callable[[ProgressEvent], None] | None,
    ) -> object:
        from babeldoc.docvision.doclayout import DocLayoutModel
        from babeldoc.format.pdf.high_level import async_translate
        from babeldoc.format.pdf.translation_config import (
            TranslationConfig,
            WatermarkOutputMode,
        )

        adapter = translator_factory()
        babel_translator = _build_babeldoc_translator(adapter, request.lang_in, request.lang_out)
        layout_model = DocLayoutModel.load_onnx()
        table_model = None
        if request.translate_table_text:
            from babeldoc.docvision.table_detection.rapidocr import RapidOCRModel

            table_model = RapidOCRModel()

        config = TranslationConfig(
            input_file=str(request.source_path),
            font=None,
            pages=None,
            output_dir=str(request.output_dir),
            translator=babel_translator,
            term_extraction_translator=babel_translator,
            debug=False,
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            no_dual=not request.produce_dual,
            no_mono=not request.produce_mono,
            qps=request.qps,
            min_text_length=request.min_text_length,
            doc_layout_model=layout_model,
            working_dir=request.working_dir,
            watermark_output_mode=getattr(
                WatermarkOutputMode,
                normalize_watermark_mode(request.watermark_output_mode),
            ),
            auto_extract_glossary=request.auto_extract_glossary,
            ocr_workaround=request.ocr_workaround,
            auto_enable_ocr_workaround=request.auto_enable_ocr_workaround,
            enhance_compatibility=request.enhance_compatibility,
            table_model=table_model,
        )
        init_font_mapper = getattr(layout_model, "init_font_mapper", None)
        if callable(init_font_mapper):
            init_font_mapper(config)

        result = None
        try:
            async for event in async_translate(config):
                etype = event.get("type")
                if etype == "error":
                    raise _babeldoc_error(RuntimeError(str(event.get("error"))))
                if etype == "finish":
                    result = event.get("translate_result")
                    break
                if on_progress is not None:
                    progress = convert_progress(event)
                    if progress is not None:
                        on_progress(progress)
            if result is None:
                raise BabelCodexError(
                    category=ErrorCategory.BABELDOC,
                    code=ErrorCode.BABELDOC_NO_FINISH_RESULT,
                    safe_message="BabelDOC ended without producing a result.",
                    technical_message="async_translate finished without finish event",
                )
            return result
        finally:
            close = getattr(adapter, "close", None)
            if callable(close):
                close()


def _build_babeldoc_translator(adapter: object, lang_in: str, lang_out: str) -> object:
    """Dynamically derive from BabelDOC BaseTranslator at runtime."""
    from babeldoc.translator.translator import BaseTranslator

    class AdapterTranslator(BaseTranslator):
        name = "codex_bridge"
        model = "codex-sdk"

        def __init__(self) -> None:
            super().__init__(lang_in=lang_in, lang_out=lang_out, ignore_cache=False)

        def do_translate(self, text: str, rate_limit_params: dict | None = None) -> str:
            if text is None:
                # BabelDOC probes the engine with do_translate/do_llm_translate(None)
                # to detect capabilities; respond with a benign sentinel.
                return ""
            return adapter.translate(text)  # type: ignore[attr-defined]

        def do_llm_translate(self, text: str, rate_limit_params: dict | None = None) -> str:
            if text is None:
                return ""
            return adapter.translate(text)  # type: ignore[attr-defined]

    return AdapterTranslator()
