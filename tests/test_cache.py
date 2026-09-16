"""Tests for the SQLite translation cache."""

from __future__ import annotations

import time

from codex_babeldoc.translation.cache import TranslationCache


def test_cache_round_trip(tmp_path):
    cache = TranslationCache(tmp_path / "cache.db")
    key = TranslationCache.make_key("hello", "en", "zh", "mock", "", "low", "v1", None, None)

    assert cache.get(key) is None

    cache.put(
        key,
        "hello",
        "你好",
        lang_in="en",
        lang_out="zh",
        translator="mock",
        model="",
        effort="low",
        prompt_version="v1",
        glossary_version=None,
        context_version=None,
    )

    assert cache.get(key) == "你好"
    cache.close()


def test_cache_disabled_when_path_is_none():
    cache = TranslationCache(None)
    assert cache.get("any") is None
    cache.put(
        "any",
        "a",
        "b",
        lang_in="en",
        lang_out="zh",
        translator="mock",
        model="",
        effort="low",
        prompt_version="v1",
        glossary_version=None,
        context_version=None,
    )
    assert cache.stats()["enabled"] is False
    cache.close()


def test_cache_key_includes_every_input():
    k1 = TranslationCache.make_key("t", "en", "zh", "m", "gpt", "low", "v1", None, None)
    k2 = TranslationCache.make_key("t", "en", "zh", "m", "gpt", "low", "v1", "g1", None)
    k3 = TranslationCache.make_key("t", "en", "zh", "m", "gpt", "high", "v1", None, None)
    assert k1 != k2
    assert k1 != k3
    assert len(k1) == 64


def test_cache_ttl_expires(tmp_path):
    cache = TranslationCache(tmp_path / "cache.db", ttl_seconds=0)
    key = TranslationCache.make_key("x", "en", "zh", "m", "", "low", "v1", None, None)
    cache.put(
        key,
        "x",
        "y",
        lang_in="en",
        lang_out="zh",
        translator="m",
        model="",
        effort="low",
        prompt_version="v1",
        glossary_version=None,
        context_version=None,
    )
    time.sleep(0.01)
    assert cache.get(key) is None
    cache.close()


def test_cache_stats_and_clear(tmp_path):
    cache = TranslationCache(tmp_path / "cache.db")
    for i in range(3):
        key = TranslationCache.make_key(f"k{i}", "en", "zh", "m", "", "low", "v1", None, None)
        cache.put(
            key,
            f"k{i}",
            f"v{i}",
            lang_in="en",
            lang_out="zh",
            translator="m",
            model="",
            effort="low",
            prompt_version="v1",
            glossary_version=None,
            context_version=None,
        )

    assert cache.stats()["entries"] == 3
    assert cache.clear() == 3
    assert cache.stats()["entries"] == 0
    cache.close()
