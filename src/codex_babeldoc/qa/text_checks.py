"""L2 text-quality checks for translated PDFs.

These checks operate on extracted text only and never embed full document
content in findings: messages carry counts, ratios and at most a short
excerpt. Glyph/rendering checks that require rasterization live in
``layout_checks``.
"""

from __future__ import annotations

from pathlib import Path
from re import findall, sub

from codex_babeldoc.qa.models import QaFinding, QaSeverity

_CJK_UNIFIED = r"[\u4e00-\u9fff]"
_ASCII_PATTERN = r"[A-Za-z]"
_BLANK_PAGE_MAX_CHARS = 20
_TRANSLATION_DENSITY_FLOOR = 0.05
_MIN_TEXT_CHARS_FOR_DENSITY = 200
_BLANK_PAGE_WARNING_RATIO = 0.3
_MATCH_LENGTH = 5  # 5 consecutive words = one translated sentence shape


def page_texts(path: Path | str) -> list[str]:
    """Extract one plain-text string per page; errors yield empty strings."""
    import fitz  # pymupdf; lazy import kept inside the QA boundary

    texts: list[str] = []
    document = fitz.open(path)
    try:
        for page in document:
            try:
                texts.append(page.get_text())
            except Exception:  # noqa: BLE001 - one bad page must not fail QA
                texts.append("")
    finally:
        document.close()
    return texts


def cjk_ratio(text: str) -> float:
    """Ratio of CJK Unified Ideograph characters to non-whitespace characters."""
    non_blank = sub(r"\s+", "", text)
    if not non_blank:
        return 0.0
    return len(findall(_CJK_UNIFIED, non_blank)) / len(non_blank)


def ascii_letter_ratio(text: str) -> float:
    non_blank = sub(r"\s+", "", text)
    if not non_blank:
        return 0.0
    return len(findall(_ASCII_PATTERN, non_blank)) / len(non_blank)


def _blank_pages(texts: list[str]) -> list[int]:
    return [
        i for i, text in enumerate(texts) if len(" ".join(text.split())) <= _BLANK_PAGE_MAX_CHARS
    ]


def _source_text(path: Path | str | None) -> str:
    if path is None:
        return ""
    try:
        return "\n".join(page_texts(path))
    except Exception:  # noqa: BLE001 - optional reference text must not fail QA
        return ""


def _similarity_to_source(output: str, source: str) -> float:
    """Share of output word 5-grams found verbatim in the source text."""
    output_words = output.split()
    if len(output_words) < _MATCH_LENGTH:
        return 0.0
    source_chunk = f" {' '.join(source.split())} "
    matched = 0
    total = 0
    for index in range(len(output_words) - _MATCH_LENGTH + 1):
        phrase = " ".join(output_words[index : index + _MATCH_LENGTH])
        total += 1
        if f" {phrase} " in source_chunk:
            matched += 1
    return matched / total if total else 0.0


def check_blank_pages(texts: list[str]) -> list[QaFinding]:
    """Flag blank/empty pages and suspicious blank-page ratios."""
    findings: list[QaFinding] = []
    blank = _blank_pages(texts)
    if not texts:
        return findings
    for page_number in blank:
        findings.append(
            QaFinding(
                code="BLANK_PAGE",
                severity=QaSeverity.INFO,
                message="Page contains almost no extractable text.",
                page=page_number,
            )
        )
    ratio = len(blank) / len(texts)
    if ratio >= _BLANK_PAGE_WARNING_RATIO and len(blank) >= 2:
        findings.append(
            QaFinding(
                code="MANY_BLANK_PAGES",
                severity=QaSeverity.WARNING,
                message="A large share of pages contain almost no text.",
                detail=f"blank={len(blank)}/{len(texts)}",
            )
        )
    return findings


def check_translation_density(
    texts: list[str], *, lang_out: str, source_text: str = ""
) -> list[QaFinding]:
    """Heuristically flag outputs that appear to be untranslated.

    The primary signal is target-language character density (CJK for Chinese
    targets). When the output is long enough to judge, a low density is a
    ``WARNING``: mock fixtures intentionally trigger it, giving a stable QA
    baseline. A secondary signal compares output word 5-grams against the
    source PDF to catch near-verbatim copies into other target languages.
    """
    findings: list[QaFinding] = []
    output = "\n".join(texts)
    non_blank_chars = len(sub(r"\s+", "", output))
    if non_blank_chars < _MIN_TEXT_CHARS_FOR_DENSITY:
        return findings

    is_chinese = str(lang_out).lower() in {"zh", "zh-cn", "zh-hans", "zh-hant", "zh-tw"}
    if is_chinese and cjk_ratio(output) < _TRANSLATION_DENSITY_FLOOR:
        findings.append(
            QaFinding(
                code="MAYBE_UNTRANSLATED",
                severity=QaSeverity.WARNING,
                message="Chinese target output has very low CJK character density.",
                detail=f"cjk_ratio={cjk_ratio(output):.3f}",
            )
        )
    elif source_text and _similarity_to_source(output, source_text) >= 0.5:
        findings.append(
            QaFinding(
                code="MAYBE_UNTRANSLATED",
                severity=QaSeverity.WARNING,
                message="Output shares long verbatim runs with the source PDF.",
                detail="5-gram similarity >= 0.5",
            )
        )
    return findings


def check_text_quality(
    path: Path | str,
    *,
    lang_out: str,
    source_path: Path | str | None = None,
    texts: list[str] | None = None,
) -> list[QaFinding]:
    """Run all L2 text checks against one output PDF."""
    extracted = texts if texts is not None else page_texts(path)
    return check_blank_pages(extracted) + check_translation_density(
        extracted,
        lang_out=lang_out,
        source_text=_source_text(source_path),
    )
