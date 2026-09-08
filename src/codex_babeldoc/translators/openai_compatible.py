from __future__ import annotations

from .base import TranslatorAdapter


class OpenAICompatibleTranslator(TranslatorAdapter):
    """Placeholder adapter for later API-based fallback.

    It is intentionally not implemented in the MVP because the primary purpose of
    this scaffold is to exercise Codex/ChatGPT authentication rather than silently
    falling back to separately billed OpenAI API usage.
    """

    def translate(self, text: str) -> str:
        raise NotImplementedError(
            "OpenAI-compatible fallback is a planned adapter. Use codex-sdk or mock."
        )
