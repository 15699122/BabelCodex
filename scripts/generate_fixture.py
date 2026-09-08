"""Generate the self-made integration fixture PDF for BabelCodex.

The fixture contains only fictional text written for this project, so it is
safe to commit to the public repository. It covers the layouts that stress
the translation pipeline: two-column body text, inline formulas, a display
formula line, URLs, DOI, citation markers, a footnote, a table, a caption
and CJK characters.

Usage: uv run python scripts/generate_fixture.py [output.pdf]
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz  # type: ignore[import-untyped]

WIDTH, HEIGHT = 595, 842  # A4 points
MARGIN = 50
COLUMN_GAP = 20
COLUMN_WIDTH = (WIDTH - 2 * MARGIN - COLUMN_GAP) / 2

LEFT_COLUMN_TEXT = (
    "BabelCodex Fixture Document\n"
    "\n"
    "This is a fictional test document generated for the BabelCodex "
    "integration test suite. It exercises two-column layout, inline "
    "formulas such as E = mc^2 and a = b + c, citation markers [1] and "
    "[2], hyperlinks, and a footnote.\n"
    "\n"
    "The attention mechanism introduced in [1] computes a weighted sum "
    "over input representations. Given a query q and keys k_i, the "
    "output is softmax(qK^T / sqrt(d)) V, where d is the hidden "
    "dimension. Empirical results are summarized in Table 1.\n"
    "\n"
    "Further reading is available at https://example.com/babelcodex and "
    "the companion dataset carries DOI 10.1234/babelcodex.fixture.\n"
    "\n"
    "For a longer paragraph test, this sentence repeats structure with "
    "slightly different wording so that the layout engine must wrap "
    "lines naturally across several lines without splitting inline "
    "formulas or dropping citation markers like [2].\n"
)

RIGHT_COLUMN_TEXT = (
    "Table 1: Fictional results\n"
    "\n"
    "Model | Score\n"
    "Baseline | 71.2\n"
    "Ours | 84.6\n"
    "\n"
    "The display formula below must remain untouched:\n"
    "\n"
    "L = sum_i (y_i - f(x_i))^2 + lambda ||w||^2\n"
    "\n"
    "Mixed-language text: 本文档是用于测试的双栏排版样例，包含中英文混排内容。 "
    "翻译管线必须正确处理 CJK 字符与拉丁字符之间的间距。\n"
    "\n"
    "A final sentence closes the column so both columns end near the "
    "bottom of the page.\n"
)


def _draw_column(page: fitz.Page, rect: fitz.Rect, text: str) -> None:
    blocks = [b for b in text.split("\n\n") if b.strip()]
    y = rect.y0
    for block in blocks:
        lines = block.split("\n")
        first = lines[0].strip()
        # Headings slightly larger; formula-ish lines monospaced.
        if first.startswith(("Table", "BabelCodex")):
            size = 11.5
            font = "helv"
        elif first.startswith("L ="):
            size = 10
            font = "cour"
        elif any("一" <= c <= "鿿" for c in block):
            size = 9.5
            font = "china-s"
        else:
            size = 9.5
            font = "helv"
        body = "\n".join(lines[1:]) if first.startswith(("Table", "BabelCodex")) else block
        target = fitz.Rect(rect.x0, y, rect.x1, rect.y1)
        page.insert_textbox(target, body, fontsize=size, fontname=font, align=0)
        # Approximate consumed height so blocks do not overlap.
        approx_lines = max(1, len(body) // 38) + body.count("\n")
        y += approx_lines * size * 1.45 + size


def build(output: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=WIDTH, height=HEIGHT)
    top = MARGIN + 18
    left = fitz.Rect(MARGIN, top, MARGIN + COLUMN_WIDTH, HEIGHT - MARGIN)
    right = fitz.Rect(
        MARGIN + COLUMN_WIDTH + COLUMN_GAP,
        top,
        WIDTH - MARGIN,
        HEIGHT - MARGIN,
    )
    _draw_column(page, left, LEFT_COLUMN_TEXT)
    _draw_column(page, right, RIGHT_COLUMN_TEXT)

    # Hyperlink on the URL text.
    for hit in page.search_for("https://example.com/babelcodex"):
        page.insert_link(
            {"kind": fitz.LINK_URI, "from": hit, "uri": "https://example.com/babelcodex"}
        )

    # Footnote.
    page.insert_text(
        (MARGIN, HEIGHT - 34),
        "1. Fictional citation generated for layout testing only.",
        fontsize=7.5,
        fontname="helv",
    )

    # Small inline image so picture regions exist in layout detection.
    pix = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, 60, 40), False)
    page.insert_image(fitz.Rect(right.x0, HEIGHT - 90, right.x0 + 60, HEIGHT - 50), pixmap=pix)

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    doc.close()
    print(f"fixture written: {output}")


if __name__ == "__main__":
    target = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/fixtures/fixture_two_column.pdf")
    )
    build(target)
