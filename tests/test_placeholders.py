"""Placeholder extraction and multiset comparison tests."""

import pytest

from codex_babeldoc.translation.models import PlaceholderInventory
from codex_babeldoc.translation.placeholders import (
    compare_inventories,
    extract_placeholder_counts,
    inventory_from_text,
    missing_preserved_substrings,
    tag_balance_errors,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", {}),
        ("plain text only", {}),
        ("result is <b1>good</b1>", {"<b1>": 1, "</b1>": 1}),
        ("value {1} and {v12}", {"{1}": 1, "{v12}": 1}),
        ("a <b1> b <b1> c", {"<b1>": 2}),
        ("see https://example.com/x", {}),
        ("10.1234/abc-def", {}),
    ],
)
def test_extract_placeholder_counts(text: str, expected: dict[str, int]) -> None:
    assert extract_placeholder_counts(text) == expected


@pytest.mark.parametrize(
    ("expected_counts", "actual_counts", "expected_errors"),
    [
        ({}, {}, ()),
        ({"<b1>": 1}, {"<b1>": 1}, ()),
        ({"<b1>": 1}, {}, ("missing_placeholder:<b1>",)),
        ({}, {"<b1>": 1}, ("unexpected_placeholder:<b1>",)),
        ({"<b1>": 2}, {"<b1>": 1}, ("placeholder_count_mismatch:<b1>:expected=2:actual=1",)),
        ({"{1}": 1, "</b1>": 1}, {"{1}": 1}, ("missing_placeholder:</b1>",)),
    ],
)
def test_compare_inventories(
    expected_counts: dict[str, int],
    actual_counts: dict[str, int],
    expected_errors: tuple[str, ...],
) -> None:
    errors = compare_inventories(
        PlaceholderInventory.from_counts(expected_counts),
        PlaceholderInventory.from_counts(actual_counts),
    )
    for item in expected_errors:
        assert item in errors
    assert len(errors) == len(expected_errors)


def test_inventory_round_trip_sorted() -> None:
    inventory = inventory_from_text("x {2} y {1} z <b1>")
    assert inventory.counts == (("<b1>", 1), ("{1}", 1), ("{2}", 1))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("<b1>ok</b1>", ()),
        ("<b1>unclosed", ("unbalanced_tag:b1:1",)),
        ("</b1>orphan", ("unbalanced_tag:b1:-1",)),
        ("<b1>a<b1>b</b1>", ("unbalanced_tag:b1:1",)),
        ("no tags", ()),
    ],
)
def test_tag_balance(text: str, expected: tuple[str, ...]) -> None:
    assert tag_balance_errors(text) == expected


def test_missing_preserved_substrings() -> None:
    source = "See https://example.com/doc and doi 10.1234/xyz-abc."
    assert missing_preserved_substrings(source, "URL and DOI dropped") == (
        "https://example.com/doc",
        "10.1234/xyz-abc",
    )
    assert (
        missing_preserved_substrings(
            source,
            "参见 https://example.com/doc 与 10.1234/xyz-abc。",
        )
        == ()
    )
