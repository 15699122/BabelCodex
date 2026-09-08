from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable


class BabelDocInternalBackend:
    """Thin compatibility layer around BabelDOC's current internal Python API.

    BabelDOC explicitly does not guarantee direct API compatibility. All imports
    therefore live inside this method so a future version can be supported in one
    file without contaminating the rest of the application.
    """

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
    ) -> object:
        return asyncio.run(
            self._translate_async(
                source,
                output_dir,
                lang_in=lang_in,
                lang_out=lang_out,
                translator_factory=translator_factory,
                no_mono=no_mono,
                no_dual=no_dual,
                qps=qps,
                min_text_length=min_text_length,
                working_dir=working_dir,
                watermark_output_mode=watermark_output_mode,
                auto_extract_glossary=auto_extract_glossary,
                ocr_workaround=ocr_workaround,
                auto_enable_ocr_workaround=auto_enable_ocr_workaround,
                enhance_compatibility=enhance_compatibility,
                translate_table_text=translate_table_text,
            )
        )

    async def _translate_async(self, source: Path, output_dir: Path, **kw) -> object:
        try:
            from babeldoc.docvision.doclayout import DocLayoutModel
            from babeldoc.format.pdf.high_level import async_translate
            from babeldoc.format.pdf.translation_config import (
                TranslationConfig,
                WatermarkOutputMode,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Compatible BabelDOC runtime not found. Install optional runtime dependencies."
            ) from exc

        adapter = kw.pop("translator_factory")()
        babel_translator = _build_babeldoc_translator(adapter, kw["lang_in"], kw["lang_out"])
        layout_model = DocLayoutModel.load_onnx()
        table_model = None
        if kw.pop("translate_table_text"):
            from babeldoc.docvision.table_detection.rapidocr import RapidOCRModel
            table_model = RapidOCRModel()

        mode_map = {
            "watermarked": WatermarkOutputMode.Watermarked,
            "no_watermark": WatermarkOutputMode.NoWatermark,
            "both": WatermarkOutputMode.Both,
        }
        config = TranslationConfig(
            input_file=str(source),
            font=None,
            pages=None,
            output_dir=str(output_dir),
            translator=babel_translator,
            term_extraction_translator=babel_translator,
            debug=False,
            lang_in=kw["lang_in"],
            lang_out=kw["lang_out"],
            no_dual=kw["no_dual"],
            no_mono=kw["no_mono"],
            qps=kw["qps"],
            min_text_length=kw["min_text_length"],
            doc_layout_model=layout_model,
            working_dir=kw["working_dir"],
            watermark_output_mode=mode_map[kw["watermark_output_mode"]],
            auto_extract_glossary=kw["auto_extract_glossary"],
            ocr_workaround=kw["ocr_workaround"],
            auto_enable_ocr_workaround=kw["auto_enable_ocr_workaround"],
            enhance_compatibility=kw["enhance_compatibility"],
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
                    raise RuntimeError(str(event.get("error")))
                if etype == "finish":
                    result = event.get("translate_result")
                    break
            if result is None:
                raise RuntimeError("BabelDOC ended without a finish result")
            return result
        finally:
            adapter.close()


def _build_babeldoc_translator(adapter, lang_in: str, lang_out: str):
    """Dynamically derive from BabelDOC BaseTranslator at runtime."""
    from babeldoc.translator.translator import BaseTranslator

    class AdapterTranslator(BaseTranslator):
        name = "codex_bridge"
        model = "codex-sdk"

        def __init__(self):
            super().__init__(lang_in=lang_in, lang_out=lang_out, ignore_cache=False)

        def do_translate(self, text, rate_limit_params=None):
            return adapter.translate(text)

        def do_llm_translate(self, text, rate_limit_params=None):
            return adapter.translate(text)

    return AdapterTranslator()
