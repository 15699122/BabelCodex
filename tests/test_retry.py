"""ValidatingTranslator retry behavior tests."""

import pytest

from codex_babeldoc.core.errors import BabelCodexError, ErrorCode
from codex_babeldoc.translation.retry import ValidatingTranslator
from codex_babeldoc.translators.scripted import ScriptedTranslator


def test_valid_output_passes_through_without_repair() -> None:
    inner = ScriptedTranslator({"Hello": "你好"})
    wrapper = ValidatingTranslator(inner)
    assert wrapper.translate("Hello") == "你好"
    assert inner.calls == ["Hello"]
    assert wrapper.repair_count == 0


def test_placeholder_mismatch_triggers_repair_then_succeeds() -> None:
    inner = ScriptedTranslator(
        {
            "keep <b1>mark</b1>": "第一次输出丢标记",
        },
        default=lambda text: "修复后的 <b1>标记</b1> 输出",
    )
    wrapper = ValidatingTranslator(inner)
    result = wrapper.translate("keep <b1>mark</b1>")
    assert "<b1>" in result
    assert wrapper.repair_count == 1
    # Repair prompt must name the specific validation error.
    assert "missing_placeholder" in inner.calls[1]
    assert "Previous (rejected) output" in inner.calls[1]


def test_repair_attempts_exhausted_raises_structured_error() -> None:
    inner = ScriptedTranslator(
        {},
        default=lambda text: "始终无效 <b1>多余标记",
    )
    wrapper = ValidatingTranslator(inner, max_repair_attempts=2)
    with pytest.raises(BabelCodexError) as excinfo:
        wrapper.translate("普通句子")
    assert excinfo.value.code is ErrorCode.PLACEHOLDER_MISMATCH
    assert excinfo.value.category.value == "validation"
    assert wrapper.repair_count == 2


def test_markdown_fence_output_uses_invalid_output_code() -> None:
    inner = ScriptedTranslator({}, default=lambda text: "``` fenced ```")
    wrapper = ValidatingTranslator(inner, max_repair_attempts=0)
    with pytest.raises(BabelCodexError) as excinfo:
        wrapper.translate("普通句子")
    assert excinfo.value.code is ErrorCode.CODEX_INVALID_OUTPUT


def test_max_repair_attempts_zero_fails_immediately() -> None:
    inner = ScriptedTranslator({}, default=lambda text: "```\nbad\n```")
    wrapper = ValidatingTranslator(inner, max_repair_attempts=0)
    with pytest.raises(BabelCodexError):
        wrapper.translate("text")
    assert wrapper.repair_count == 0
    assert len(inner.calls) == 1
