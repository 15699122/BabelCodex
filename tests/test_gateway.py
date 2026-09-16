"""Tests for the Translation Gateway pipeline."""

from __future__ import annotations

from codex_babeldoc.translation.cache import TranslationCache
from codex_babeldoc.translation.gateway import TranslationGateway
from codex_babeldoc.translation.models import TranslationRequest
from codex_babeldoc.translators.base import TranslatorAdapter


class _FakeTranslator(TranslatorAdapter):
    def __init__(self, output: str = "译文") -> None:
        self.output = output
        self.calls: list[str] = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        return self.output


class _PlaceholderBreakingTranslator(TranslatorAdapter):
    """Returns output that drops a placeholder on the first call, then repairs."""

    def __init__(self) -> None:
        self.calls = 0

    def translate(self, text: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "译文"  # missing <b1> placeholder
        return "译文 <b1>保留</b1>"


def test_gateway_passthrough_without_cache_or_batch():
    t = _FakeTranslator("ok")
    gw = TranslationGateway(t)
    assert gw.translate("hello") == "ok"
    assert t.calls == ["hello"]
    gw.close()


def test_gateway_uses_cache_hit(tmp_path):
    class CountingTranslator(TranslatorAdapter):
        def __init__(self) -> None:
            self.n = 0

        def translate(self, text: str) -> str:
            self.n += 1
            return "cached"

    t = CountingTranslator()
    gw = TranslationGateway(t, cache=TranslationCache(tmp_path / "cache.db"))
    gw.translate("repeat")
    gw.translate("repeat")
    assert t.n == 1
    gw.close()


def test_gateway_cache_isolated_by_translator_metadata(tmp_path):
    first = _FakeTranslator("first")
    second = _FakeTranslator("second")
    cache_path = tmp_path / "cache.db"
    first_gateway = TranslationGateway(
        first,
        cache=TranslationCache(cache_path),
        translator_name="model-a",
    )
    assert first_gateway.translate("same") == "first"
    first_gateway.close()

    second_gateway = TranslationGateway(
        second,
        cache=TranslationCache(cache_path),
        translator_name="model-b",
    )
    assert second_gateway.translate("same") == "second"
    assert second.calls == ["same"]
    second_gateway.close()


def test_gateway_repairs_invalid_output():
    t = _PlaceholderBreakingTranslator()
    gw = TranslationGateway(t, max_repair_attempts=3)
    out = gw.translate("hello <b1>world</b1>")
    assert "<b1>" in out
    assert t.calls == 2
    gw.close()


def test_gateway_invalid_source_returns_untranslated():
    t = _FakeTranslator()
    gw = TranslationGateway(t)
    assert gw.translate("   ") == "   "
    assert t.calls == []
    gw.close()


def test_gateway_translate_request_model():
    t = _FakeTranslator("结果")
    gw = TranslationGateway(t)
    req = TranslationRequest(
        request_id="r1",
        document_id="d",
        sequence=0,
        source_text="abc",
        source_hash="",
        lang_in="en",
        lang_out="zh",
    )
    result = gw.translate_request(req)
    assert result.translated_text == "结果"
    assert result.validation_status == "valid"
    gw.close()


def test_gateway_cache_isolated_by_glossary_and_context_versions(tmp_path):
    cache_path = tmp_path / "cache.db"
    first = _FakeTranslator("first")
    first_gateway = TranslationGateway(
        first,
        cache=TranslationCache(cache_path),
        glossary_version="g1",
        context_version="c1",
    )
    first_gateway.translate("same")
    first_gateway.close()

    second = _FakeTranslator("second")
    second_gateway = TranslationGateway(
        second,
        cache=TranslationCache(cache_path),
        glossary_version="g2",
        context_version="c1",
    )
    assert second_gateway.translate("same") == "second"
    assert second.calls == ["same"]
    second_gateway.close()
