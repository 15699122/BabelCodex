"""Build translator instances from a JSON-serializable specification.

Shared by the orchestrator (in-process mode) and the BabelDOC worker
subprocess, so both entry points construct identical translator stacks.
"""

from __future__ import annotations

from codex_babeldoc.backends.worker_protocol import TranslatorSpec
from codex_babeldoc.translation.retry import ValidatingTranslator


def build_translator(spec: TranslatorSpec) -> object:
    """Instantiate the raw translator named by ``spec``."""
    if spec.name == "mock":
        from codex_babeldoc.translators.mock import MockTranslator

        return MockTranslator()
    if spec.name == "codex-sdk":
        from codex_babeldoc.translators.codex_sdk import CodexSdkTranslator

        return CodexSdkTranslator(
            spec.lang_in,
            spec.lang_out,
            context_prompt=spec.context_prompt,
            model=spec.model,
            effort=spec.effort,
        )
    raise ValueError(f"Unknown translator: {spec.name}")


def build_validating_translator(spec: TranslatorSpec) -> ValidatingTranslator:
    """Build the translator wrapped with placeholder/output validation."""
    inner = build_translator(spec)
    return ValidatingTranslator(inner, lang_in=spec.lang_in, lang_out=spec.lang_out)
