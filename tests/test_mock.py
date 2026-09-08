from codex_babeldoc.translators.mock import MockTranslator


def test_mock():
    assert MockTranslator().translate("hello") == "[MOCK]hello"
