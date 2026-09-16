"""Deterministic scripted translator for tests and mock pipelines."""

from __future__ import annotations

from collections.abc import Callable

from .base import TranslatorAdapter


class ScriptedTranslator(TranslatorAdapter):
    """Return canned responses keyed by source text.

    ``responses`` maps exact source text to the output that should be
    returned. Matching is exact on purpose: repair prompts embed the
    original source text, so substring matching would wrongly re-trigger
    the mapping for the rejected output. ``default`` handles anything not
    listed. Calls are recorded in ``calls`` so tests can assert retry
    behavior.
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        *,
        default: Callable[[str], str] | None = None,
    ) -> None:
        self.responses = dict(responses or {})
        self.default = default
        self.calls: list[str] = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        if text in self.responses:
            return self.responses[text]
        if self.default is not None:
            return self.default(text)
        raise KeyError(f"No scripted response for: {text[:60]!r}")

    def close(self) -> None:
        pass
