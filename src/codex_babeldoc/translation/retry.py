"""Validation wrapper with exact-output repair retries.

Wraps any :class:`TranslatorAdapter` so invalid translations (placeholder
mismatch, markdown fences, explanatory commentary) never reach BabelDOC.
Failed outputs trigger a repair turn that names the specific validation
errors; after the configured repair attempts are exhausted the failure is
raised as a structured :class:`BabelCodexError`.
"""

from __future__ import annotations

import logging

from codex_babeldoc.core.errors import BabelCodexError, ErrorCategory, ErrorCode
from codex_babeldoc.translators.base import TranslatorAdapter

from .validation import validate_translation

log = logging.getLogger(__name__)

_DEFAULT_MAX_REPAIRS = 2


class ValidatingTranslator(TranslatorAdapter):
    """Decorator that validates every translation and retries invalid output."""

    def __init__(
        self,
        inner: TranslatorAdapter,
        *,
        lang_in: str = "en",
        lang_out: str = "zh",
        max_repair_attempts: int = _DEFAULT_MAX_REPAIRS,
    ) -> None:
        self.inner = inner
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.max_repair_attempts = max_repair_attempts
        self.repair_count = 0

    def translate(self, text: str) -> str:
        output = self.inner.translate(text)
        result = validate_translation(text, output)
        if result.valid:
            return output

        last_errors: tuple[str, ...] = result.errors
        for attempt in range(1, self.max_repair_attempts + 1):
            log.warning(
                "Translation validation failed (attempt %s/%s): %s",
                attempt,
                self.max_repair_attempts,
                ", ".join(result.errors),
            )
            output = self.inner.translate(self._repair_prompt(text, output, result.errors))
            self.repair_count += 1
            result = validate_translation(text, output)
            if result.valid:
                return output
            last_errors = result.errors

        raise BabelCodexError(
            category=ErrorCategory.VALIDATION,
            code=self._error_code(last_errors),
            safe_message=(
                "Translation output failed validation after "
                f"{self.max_repair_attempts} repair attempts."
            ),
            retryable=False,
            technical_message="; ".join(last_errors),
        )

    def _repair_prompt(self, source: str, bad_output: str, errors: tuple[str, ...]) -> str:
        error_list = "\n".join(f"- {error}" for error in errors)
        return (
            f"Your previous translation was rejected for these exact problems:\n"
            f"{error_list}\n\n"
            f"Translate the following text from {self.lang_in} to {self.lang_out}. "
            "Return ONLY the corrected translation, with no commentary, no markdown "
            "fences, and no quotation marks. Preserve every placeholder, URL and "
            "citation exactly as in the source.\n\n"
            f"Previous (rejected) output:\n{bad_output}\n\n"
            f"Source text:\n{source}"
        )

    @staticmethod
    def _error_code(errors: tuple[str, ...]) -> ErrorCode:
        if any(
            error.startswith(("missing_placeholder", "unexpected_placeholder")) for error in errors
        ):
            return ErrorCode.PLACEHOLDER_MISMATCH
        return ErrorCode.CODEX_INVALID_OUTPUT

    def close(self) -> None:
        self.inner.close()
