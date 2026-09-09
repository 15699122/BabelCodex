"""Build translator instances from a JSON-serializable specification.

Shared by the orchestrator (in-process mode) and the BabelDOC worker
subprocess, so both entry points construct identical translator stacks.
"""

from __future__ import annotations

from pathlib import Path

from codex_babeldoc.backends.worker_protocol import TranslatorSpec
from codex_babeldoc.translation.cache import TranslationCache
from codex_babeldoc.translation.gateway import TranslationGateway
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
            thread_state_path=spec.thread_state_path,
            document_id=spec.document_id,
            max_turns_before_compact=spec.max_turns_before_compact,
        )
    raise ValueError(f"Unknown translator: {spec.name}")


def build_validating_translator(spec: TranslatorSpec) -> ValidatingTranslator:
    """Build the translator wrapped with placeholder/output validation."""
    inner = build_translator(spec)
    return ValidatingTranslator(inner, lang_in=spec.lang_in, lang_out=spec.lang_out)


def build_gateway_translator(spec: TranslatorSpec) -> TranslationGateway:
    """Build the shared gateway used by production PDF translation paths."""
    inner = build_translator(spec)
    cache = None
    if spec.cache_enabled and spec.cache_path:
        cache = TranslationCache(
            Path(spec.cache_path),
            store_plaintext=spec.cache_store_plaintext,
            ttl_seconds=spec.cache_ttl_seconds,
        )
    return TranslationGateway(
        inner,
        cache=cache,
        lang_in=spec.lang_in,
        lang_out=spec.lang_out,
        translator_name=spec.name,
        model=spec.model or "",
        effort=spec.effort or "",
        prompt_version=spec.context_prompt or "",
        glossary_version=spec.glossary_version,
        context_version=spec.context_version,
    )
