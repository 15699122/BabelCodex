"""Output cleanliness and placeholder validation for translations."""

from __future__ import annotations

import re

from .models import ValidationResult
from .placeholders import (
    compare_inventories,
    inventory_from_text,
    missing_preserved_substrings,
    tag_balance_errors,
)

_MARKDOWN_FENCE = re.compile(r"```")

# Common explanatory prefixes models add despite instructions.
_PREFIXES = (
    "translation:",
    "translated text:",
    "here is the translation",
    "here's the translation",
    "以下是翻译",
    "翻译如下",
    "译文：",
    "译文:",
)


def _strip_wrapping_quotes(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in {'"', "'", "“", "”", "『", "』"}
    ):
        return stripped[1:-1].strip(), True
    return stripped, False


def validate_translation(source: str, translated: str) -> ValidationResult:
    """Validate one translated segment against its source.

    Returns a :class:`ValidationResult`; an invalid result must never reach
    BabelDOC's typesetting stage.
    """
    errors: list[str] = []
    output = (translated or "").strip()

    if not output:
        return ValidationResult(valid=False, errors=("empty_output",))

    if not source.strip():
        return ValidationResult(
            valid=False,
            errors=("unexpected_output_for_empty_source",),
        )

    if _MARKDOWN_FENCE.search(output):
        errors.append("markdown_fence")

    lowered = output.lower()
    for prefix in _PREFIXES:
        if lowered.startswith(prefix):
            errors.append(f"explanatory_prefix:{prefix}")
            break

    unwrapped, was_wrapped = _strip_wrapping_quotes(output)
    if was_wrapped:
        errors.append("wrapped_in_quotes")

    if unwrapped.upper() == "READY":
        errors.append("ready_only_output")

    if source.strip() and len(unwrapped) < max(1, len(source.strip()) // 10):
        errors.append("output_suspiciously_short")

    inventory_errors = compare_inventories(
        inventory_from_text(source),
        inventory_from_text(output),
    )
    errors.extend(inventory_errors)
    errors.extend(tag_balance_errors(output))
    errors.extend(
        f"missing_preserved:{item}" for item in missing_preserved_substrings(source, output)
    )

    # Deduplicate while keeping order.
    seen: set[str] = set()
    unique = tuple(e for e in errors if not (e in seen or seen.add(e)))
    return ValidationResult(valid=not unique, errors=unique)
