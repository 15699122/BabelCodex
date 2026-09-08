from __future__ import annotations

import threading
from pathlib import Path

from codex_babeldoc.translation.thread_state import ThreadStateStore

from .base import TranslatorAdapter


class CodexSdkTranslator(TranslatorAdapter):
    """Translate text through the official Codex Python SDK.

    The SDK reuses the user's existing Codex authentication, including ChatGPT
    sign-in. A single thread is retained for a document so terminology/context can
    remain more stable than one-process-per-segment execution.

    This adapter deliberately serializes calls. BabelDOC may invoke translators
    from workers; sharing one Codex thread concurrently is not assumed safe.
    """

    def __init__(
        self,
        lang_in: str,
        lang_out: str,
        *,
        context_prompt: str | None = None,
        model: str = "",
        effort: str = "low",
        thread_state_path: str | None = None,
        document_id: str | None = None,
    ) -> None:
        try:
            from openai_codex import Codex, Sandbox
        except ImportError as exc:
            raise RuntimeError(
                "Codex SDK is not installed. Install with: pip install openai-codex"
            ) from exc

        self.lang_in = lang_in
        self.lang_out = lang_out
        self.context_prompt = context_prompt or ""
        self.model = model or None
        self.effort = effort or None
        self._lock = threading.Lock()
        self._codex = Codex()
        self._thread_store = (
            ThreadStateStore(Path(thread_state_path)) if thread_state_path else None
        )
        self._document_id = document_id
        saved = self._thread_store.load(document_id) if self._thread_store and document_id else None
        if saved is not None:
            self._thread = self._codex.thread_resume(saved.thread_id, sandbox=Sandbox.read_only)
        else:
            self._thread = self._codex.thread_start(sandbox=Sandbox.read_only)
        self._prime_thread()
        if self._thread_store is not None and self._document_id:
            self._thread_store.rotate(self._document_id, self._thread.id)

    def _prime_thread(self) -> None:
        prompt = build_prime_prompt(self.lang_in, self.lang_out, self.context_prompt)
        result = self._thread.run(
            prompt,
            model=self.model,
            effort=self.effort,
            sandbox=None,
        )
        if not result.final_response or "READY" not in result.final_response.upper():
            raise RuntimeError("Codex translation thread failed to initialize cleanly")

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        prompt = (
            f"Translate the following text from {self.lang_in} to {self.lang_out}. "
            "Return translation only. Preserve all placeholders exactly.\n\n"
            f"{text}"
        )
        with self._lock:
            result = self._thread.run(
                prompt,
                model=self.model,
                effort=self.effort,
            )
        output = (result.final_response or "").strip()
        if not output:
            raise RuntimeError("Codex returned an empty translation")
        return output

    def close(self) -> None:
        close = getattr(self._codex, "close", None)
        if callable(close):
            close()


def build_prime_prompt(lang_in: str, lang_out: str, context_prompt: str = "") -> str:
    """Build the exact-output prompt used to prime a Codex translation thread."""
    return (
        "You are acting only as a machine-translation component inside a PDF "
        "typesetting pipeline. "
        f"Source language: {lang_in}. Target language: {lang_out}. "
        f"{context_prompt} "
        "For all subsequent translation turns, output ONLY the translated text. "
        "Preserve placeholders such as <b1>, </b1>, {1}, formula tokens, URLs, "
        "citation labels, and intentional line structure exactly when they are not "
        "natural-language content. Never add markdown fences, commentary, notes, "
        "or quotation marks around the answer. Reply exactly: READY"
    )
