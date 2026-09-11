"""Layout and visual heuristics for translated PDFs.

Two families of checks live here:

- **overflow**: text spans whose bounding box crosses the media box, which the
  translated text rarely should do when typesetting stayed in bounds.
- **visual blankness**: rasterizing pages to catch glyph/font failures that a
  text layer alone cannot reveal (missing glyphs often render as blank ink).

Rasterization is bounded to a few sample pages so QA stays fast on long books,
and findings only reference page numbers and ratios, never document text.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # pymupdf; QA boundary keeps the import lazy via callers

from codex_babeldoc.qa.models import QaFinding, QaSeverity

OVERFLOW_TOLERANCE_PT = 1.0
OVERFLOW_BAD_MARGIN_PT = 10.0
OVERFLOW_WARNING_RATIO = 0.05
MAX_RENDER_PAGES = 5
VISUAL_BLANK_PIXEL_RATIO = 0.01
RENDER_ZOOM = 1.0  # ~72 DPI is enough for blank-ink detection


def _page_spans(page) -> list[tuple[float, float, fitz.Rect]]:
    """Yield (left, top, rect) for every text span on a page."""
    spans: list[tuple[float, float, fitz.Rect]] = []
    try:
        blocks = page.get_text("dict")
    except Exception:  # noqa: BLE001 - extraction failure is not a layout signal
        return spans
    for block in blocks.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                rect = span.get("bbox")
                if rect is None:
                    continue
                spans.append(
                    (
                        float(span.get("origin", (0, 0))[0]),
                        float(span.get("origin", (0, 0))[1]),
                        fitz.Rect(rect),
                    )
                )
    return spans


def check_overflow(path: Path | str) -> list[QaFinding]:
    """Flag text spans that cross the media box by more than a small tolerance."""
    findings: list[QaFinding] = []
    document = fitz.open(path)
    try:
        affected_pages: list[int] = []
        badly_overflowing = 0
        for page_number, page in enumerate(document):
            media = page.rect
            overflowed = 0
            for _left, _top, rect in _page_spans(page):
                if (
                    rect.x0 < media.x0 - OVERFLOW_TOLERANCE_PT
                    or rect.y0 < media.y0 - OVERFLOW_TOLERANCE_PT
                    or rect.x1 > media.x1 + OVERFLOW_TOLERANCE_PT
                    or rect.y1 > media.y1 + OVERFLOW_TOLERANCE_PT
                ):
                    overflowed += 1
                    if (
                        rect.x1 > media.x1 + OVERFLOW_BAD_MARGIN_PT
                        or rect.y1 > media.y1 + OVERFLOW_BAD_MARGIN_PT
                        or rect.x0 < media.x0 - OVERFLOW_BAD_MARGIN_PT
                        or rect.y0 < media.y0 - OVERFLOW_BAD_MARGIN_PT
                    ):
                        badly_overflowing += 1
            if overflowed:
                affected_pages.append(page_number)
        if affected_pages:
            severity = QaSeverity.WARNING if badly_overflowing else QaSeverity.INFO
            findings.append(
                QaFinding(
                    code="TEXT_OVERFLOW",
                    severity=severity,
                    message="Some text spans exceed the page media box.",
                    detail=f"affected_pages={len(affected_pages)} severe_spans={badly_overflowing}",
                )
            )
    finally:
        document.close()
    return findings


def _non_blank_pixel_ratio(page) -> float | None:
    """Return the share of non-white pixels, or None when rendering fails."""
    try:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(RENDER_ZOOM, RENDER_ZOOM))
    except Exception:  # noqa: BLE001 - rendering failure must not fail QA
        return None
    samples = pixmap.samples
    if not samples:
        return 0.0
    # RGBA vs RGB determined by pixmap.n; treat near-white as blank.
    channel_count = pixmap.n
    non_blank = 0
    total = 0
    white = 255 * channel_count
    step = channel_count
    for index in range(0, len(samples) - channel_count + 1, step):
        total += 1
        if sum(samples[index : index + channel_count]) < white - 6 * channel_count:
            non_blank += 1
    return non_blank / total if total else 0.0


def check_visual_blank(path: Path | str) -> list[QaFinding]:
    """Rasterize up to ``MAX_RENDER_PAGES`` pages and flag blank-looking ink."""
    findings: list[QaFinding] = []
    document = fitz.open(path)
    try:
        rendered = 0
        for page_number, page in enumerate(document):
            if rendered >= MAX_RENDER_PAGES:
                break
            ratio = _non_blank_pixel_ratio(page)
            if ratio is None:
                continue
            rendered += 1
            if ratio < VISUAL_BLANK_PIXEL_RATIO:
                findings.append(
                    QaFinding(
                        code="RENDER_BLANK_PAGE",
                        severity=QaSeverity.WARNING,
                        message="Rendered page is visually blank (possible missing glyph).",
                        page=page_number,
                        detail=f"non_blank_ratio={ratio:.4f}",
                    )
                )
    finally:
        document.close()
    return findings
