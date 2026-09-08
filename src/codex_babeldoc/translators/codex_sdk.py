from __future__ import annotations

import threading

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
        context_prompt: str,
        model: str = "",
        effort: str = "low",
    ) -> None:
        try:
            from openai_codex import Codex, Sandbox
        except ImportError as exc:
            raise RuntimeError(
                "Codex SDK is not installed. Install with: pip install openai-codex"
            ) from exc

        self.lang_in = lang_in
        self.lang_out = lang_out
        self.context_prompt = context_prompt
        self.model = model or None
        self.effort = effort or None
        self._lock = threading.Lock()
        self._codex = Codex()
        self._thread = self._codex.thread_start(sandbox=Sandbox.read_only)
        self._prime_thread()

    def _prime_thread(self) -> None:
        prompt = (
            "You are acting only as a machine-translation component inside a PDF "
            "typesetting pipeline. "
            f"Source language: {self.lang_in}. Target language: {self.lang_out}. "
            f"{self.context_prompt} "
            "For all subsequent translation turns, output ONLY the translated text. "
            "Preserve placeholders such as <b1>, </b1>, {1}, formula tokens, URLs, "
            "citation labels, and intentional line structure exactly when they are not "
            "natural-language content. Never add markdown fences, commentary, notes, "
            "or quotation marks around the answer. Reply exactly: READY"
        )
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
