"""Translation Gateway: the translator-independent core.

Normalises requests, checks the segment cache, dispatches cache misses
through the batch worker, validates every result, performs exact-output
repair retries, and writes validated results back to the cache.
"""

from __future__ import annotations

import logging
import uuid

from codex_babeldoc.core.errors import BabelCodexError, ErrorCategory, ErrorCode
from codex_babeldoc.translators.base import TranslatorAdapter

from .batching import BatchWorker
from .cache import TranslationCache
from .models import TranslationRequest, TranslationResult
from .placeholders import inventory_from_text
from .validation import validate_translation

log = logging.getLogger(__name__)

_PROMPT_VERSION = "v1"


class TranslationGateway:
    """Cache → batch → translate → validate → retry → cache pipeline."""

    def __init__(
        self,
        translator: TranslatorAdapter,
        *,
        cache: TranslationCache | None = None,
        batch_worker: BatchWorker | None = None,
        lang_in: str = "en",
        lang_out: str = "zh",
        max_repair_attempts: int = 2,
        translator_name: str = "translator",
        model: str = "",
        effort: str = "",
        prompt_version: str = _PROMPT_VERSION,
    ) -> None:
        self._translator = translator
        self._cache = cache
        self._batch = batch_worker
        self._lang_in = lang_in
        self._lang_out = lang_out
        self._max_repair_attempts = max_repair_attempts
        self._translator_name = translator_name
        self._model = model
        self._effort = effort
        self._prompt_version = prompt_version or _PROMPT_VERSION

    # ------------------------------------------------------------------
    def translate(self, source_text: str) -> str:
        """Synchronous entry point used by the BabelDOC bridge."""
        request = TranslationRequest(
            request_id=str(uuid.uuid4()),
            document_id="document",
            sequence=0,
            source_text=source_text,
            source_hash="",
            lang_in=self._lang_in,
            lang_out=self._lang_out,
            placeholders=inventory_from_text(source_text),
        )
        result = self.translate_request(request)
        return result.translated_text

    def translate_request(self, request: TranslationRequest) -> TranslationResult:
        if not request.source_text.strip():
            return TranslationResult(
                request_id=request.request_id,
                translated_text=request.source_text,
                validation_status="valid",
            )

        cached = self._lookup_cache(request)
        if cached is not None:
            return cached

        if self._batch is not None:
            result = self._batch.submit(request)
        else:
            result = self._translate_single(request)

        validated = self._validate_and_repair(request, result)
        self._store_cache(request, validated)
        return validated

    def _lookup_cache(self, request: TranslationRequest) -> TranslationResult | None:
        if self._cache is None:
            return None
        key = TranslationCache.make_key(
            request.source_text,
            request.lang_in,
            request.lang_out,
            self._translator_name,
            self._model,
            self._effort,
            self._prompt_version,
            request.glossary_version,
            request.context_version,
        )
        hit = self._cache.get(key)
        if hit is None:
            return None
        return TranslationResult(
            request_id=request.request_id,
            translated_text=hit,
            validation_status="valid",
            cache_hit=True,
        )

    def _translate_single(self, request: TranslationRequest) -> TranslationResult:
        output = self._translator.translate(request.source_text)
        return TranslationResult(
            request_id=request.request_id,
            translated_text=output,
            validation_status="pending",
        )

    def _validate_and_repair(
        self,
        request: TranslationRequest,
        result: TranslationResult,
    ) -> TranslationResult:
        output = result.translated_text
        validation = validate_translation(request.source_text, output)
        if validation.valid:
            return TranslationResult(
                request_id=request.request_id,
                translated_text=output,
                validation_status="valid",
                cache_hit=result.cache_hit,
            )

        for attempt in range(1, self._max_repair_attempts + 1):
            log.warning(
                "Validation failed (attempt %s/%s): %s",
                attempt,
                self._max_repair_attempts,
                ", ".join(validation.errors),
            )
            output = self._translator.translate(
                self._repair_prompt(request.source_text, output, validation.errors)
            )
            validation = validate_translation(request.source_text, output)
            if validation.valid:
                return TranslationResult(
                    request_id=request.request_id,
                    translated_text=output,
                    validation_status="valid",
                    attempts=attempt + 1,
                    cache_hit=result.cache_hit,
                )

        raise BabelCodexError(
            category=ErrorCategory.VALIDATION,
            code=ErrorCode.CODEX_INVALID_OUTPUT,
            safe_message="Translation output failed validation.",
            retryable=False,
            technical_message="; ".join(validation.errors),
        )

    def _store_cache(self, request: TranslationRequest, result: TranslationResult) -> None:
        if self._cache is None or result.validation_status != "valid":
            return
        key = TranslationCache.make_key(
            request.source_text,
            request.lang_in,
            request.lang_out,
            self._translator_name,
            self._model,
            self._effort,
            self._prompt_version,
            request.glossary_version,
            request.context_version,
        )
        self._cache.put(
            key,
            request.source_text,
            result.translated_text,
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            translator=self._translator_name,
            model=self._model,
            effort=self._effort,
            prompt_version=self._prompt_version,
            glossary_version=request.glossary_version,
            context_version=request.context_version,
        )

    @staticmethod
    def _repair_prompt(source: str, bad_output: str, errors: tuple[str, ...]) -> str:
        error_list = "\n".join(f"- {e}" for e in errors)
        return (
            "Your previous translation was rejected for these exact problems:\n"
            f"{error_list}\n\n"
            "Return ONLY the corrected translation, with no commentary, no "
            "markdown fences, and no quotation marks. Preserve every "
            "placeholder, URL and citation exactly.\n\n"
            f"Previous (rejected) output:\n{bad_output}\n\n"
            f"Source text:\n{source}"
        )

    def close(self) -> None:
        if self._batch is not None:
            self._batch.shutdown()
        self._translator.close()
        if self._cache is not None:
            self._cache.close()
