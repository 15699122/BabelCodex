"""Output cleanliness validation tests."""

import pytest

from codex_babeldoc.translation.validation import validate_translation


@pytest.mark.parametrize(
    ("source", "translated", "expected_valid"),
    [
        ("Hello world", "你好，世界", True),
        ("The <b1>result</b1> is good", "这个 <b1>结果</b1> 很好", True),
        ("", "译文", False),
        ("Hello", "", False),
        ("Hello", "```text\n你好\n```", False),
        ("Hello", "Translation: 你好", False),
        ("Hello", "以下是翻译：你好", False),
        ("Hello", '"你好"', False),
        ("Hello", "READY", False),
        ("A fairly long source sentence", "短", False),
        ("Visit https://example.com now", "现在访问", False),
        ("Visit https://example.com now", "现在访问 https://example.com", True),
        ("The <b1>x</b1> y", "<b1>结果", False),
        ("A <b1> B", "结果 <b1>", False),
    ],
)
def test_validate_translation(source: str, translated: str, expected_valid: bool) -> None:
    result = validate_translation(source, translated)
    assert result.valid is expected_valid, result.errors


def test_error_codes_are_specific() -> None:
    result = validate_translation("keep <b1>here</b1>", "丢失了标记")
    assert "missing_placeholder:<b1>" in result.errors

    result = validate_translation("text", "结果 <b1> 多余")
    assert "unexpected_placeholder:<b1>" in result.errors

    result = validate_translation("text", "")
    assert result.errors == ("empty_output",)


def test_clean_output_has_no_errors() -> None:
    source = "The model uses {1} attention with <b1>transformers</b1> (see https://arxiv.org/abs/1234.5678)."
    translated = (
        "该模型使用 {1} 注意力机制与 <b1>Transformer</b1>（参见 https://arxiv.org/abs/1234.5678）。"
    )
    result = validate_translation(source, translated)
    assert result.valid, result.errors
