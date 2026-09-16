"""Structural token extraction and comparison.

BabelDOC embeds rich-text and formula placeholders inside translatable text.
A translation that drops, adds, or duplicates these tokens would corrupt the
rendered PDF, so the gateway must compare the placeholder multiset of the
source and the translated text before the result can be accepted.
"""

from __future__ import annotations

import re

from .models import PlaceholderInventory

# BabelDOC rich-text tags such as <b1> / </b1>, plus generic paired tags.
_RICH_TEXT_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9_]*>")

# Numbered and formula tokens such as {1} or {v12}.
_NUMBERED_TOKEN = re.compile(r"\{v?\d+\}")

# URLs and DOIs must survive translation verbatim.
_URL = re.compile(r"https?://[^\s<>\"']+")
_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")

# Trailing punctuation that sentence context may have glued onto a match.
_TRAILING_PUNCT = ".,;:!?)\\]}”’\"'，。；：）】"


def _strip_trailing_punct(token: str) -> str:
    return token.rstrip(_TRAILING_PUNCT)


def extract_placeholder_counts(text: str) -> dict[str, int]:
    """Return a multiset of structural tokens found in ``text``."""
    counts: dict[str, int] = {}
    for pattern in (_RICH_TEXT_TAG, _NUMBERED_TOKEN):
        for match in pattern.findall(text):
            counts[match] = counts.get(match, 0) + 1
    return counts


def inventory_from_text(text: str) -> PlaceholderInventory:
    return PlaceholderInventory.from_counts(extract_placeholder_counts(text))


def compare_inventories(
    expected: PlaceholderInventory,
    actual: PlaceholderInventory,
) -> tuple[str, ...]:
    """Compare two placeholder multisets and describe every difference.

    A plain set comparison would hide duplicates; this reports missing
    tokens, unexpected tokens, and wrong repetition counts separately.
    """
    errors: list[str] = []
    expected_counts = dict(expected.counts)
    actual_counts = dict(actual.counts)

    for token, count in expected_counts.items():
        found = actual_counts.get(token, 0)
        if found == 0:
            errors.append(f"missing_placeholder:{token}")
        elif found != count:
            errors.append(f"placeholder_count_mismatch:{token}:expected={count}:actual={found}")

    for token, count in actual_counts.items():
        if token not in expected_counts:
            errors.append(f"unexpected_placeholder:{token}")
        elif count != expected_counts[token] and f"placeholder_count_mismatch:{token}" not in str(
            errors
        ):
            # Only the first mismatch direction is reported above; skip repeats.
            continue

    return tuple(errors)


def tag_balance_errors(text: str) -> tuple[str, ...]:
    """Check that rich-text open/close tags are paired in the output."""
    opens = _RICH_TEXT_TAG.findall(text)
    balance: dict[str, int] = {}
    for tag in opens:
        name = tag[1:-1]
        if name.startswith("/"):
            balance[name[1:]] = balance.get(name[1:], 0) - 1
        else:
            balance[name] = balance.get(name, 0) + 1
    return tuple(
        f"unbalanced_tag:{name}:{count}" for name, count in sorted(balance.items()) if count != 0
    )


def preserved_substrings(text: str) -> tuple[str, ...]:
    """Return URLs and DOIs that must appear unchanged in the translation."""
    found = (
        *(_strip_trailing_punct(m) for m in _URL.findall(text)),
        *(_strip_trailing_punct(m) for m in _DOI.findall(text)),
    )
    return tuple(dict.fromkeys(found))


def missing_preserved_substrings(
    source: str,
    translated: str,
) -> tuple[str, ...]:
    return tuple(
        substring for substring in preserved_substrings(source) if substring not in translated
    )
