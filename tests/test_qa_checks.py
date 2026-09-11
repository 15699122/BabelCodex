"""Unit tests for the QA check layers (L0/L1 sanity, text, layout, resources)."""

from __future__ import annotations

from pathlib import Path

import fitz

from codex_babeldoc.qa.layout_checks import check_overflow, check_visual_blank
from codex_babeldoc.qa.models import QaFinding, QaReport, QaSeverity, report_for
from codex_babeldoc.qa.pdf_sanity import (
    check_file_level,
    check_pdf,
    check_pdf_structure,
)
from codex_babeldoc.qa.report import run_qa, save_report, to_text
from codex_babeldoc.qa.resource_checks import check_disk_space, check_output_size
from codex_babeldoc.qa.text_checks import (
    check_blank_pages,
    check_text_quality,
    check_translation_density,
    cjk_ratio,
)


def _make_pdf(path: Path, *, texts: list[str] | None = None) -> Path:
    document = fitz.open()
    try:
        for index, text in enumerate(texts or ["Imported English sentence here."]):
            page = document.new_page()
            page.insert_text((72, 72 + index * 20), text)
        document.save(path)
    finally:
        document.close()
    return path


def test_cjk_ratio_counts_unified_ideographs():
    assert cjk_ratio("中文测试") == 1.0
    assert cjk_ratio("Hello world") == 0.0
    assert cjk_ratio("") == 0.0


def test_file_level_checks_detect_missing_and_bad_header(tmp_path):
    missing = tmp_path / "nope.pdf"
    findings = check_file_level(missing)
    assert [f.code for f in findings] == ["FILE_MISSING"]

    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf header")
    codes = [f.code for f in check_file_level(bad)]
    assert "PDF_HEADER_INVALID" in codes


def test_structure_check_detects_corrupt_pdf(tmp_path):
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF-1.7\n%%%% broken trailer")
    findings = check_pdf(corrupt)
    assert any(f.code == "PDF_OPEN_FAILED" for f in findings)


def test_pdf_structure_accepts_generated_document(tmp_path):
    target = _make_pdf(tmp_path / "ok.pdf")
    findings = check_pdf_structure(target)
    assert findings == []


def test_blank_pages_and_translation_density():
    blank = check_blank_pages(["some text", "", "   ", "more words"])
    assert any(f.code == "BLANK_PAGE" for f in blank)
    assert any(f.code == "MANY_BLANK_PAGES" for f in blank)

    density = check_translation_density(
        ["This is a purely English paragraph that was never translated into Chinese."] * 4,
        lang_out="zh",
    )
    assert any(f.code == "MAYBE_UNTRANSLATED" for f in density)

    chinese = check_translation_density(["这是完全中文的译文段落内容，质量良好。"], lang_out="zh")
    assert chinese == []


def test_text_quality_accepts_short_outputs_without_judging(tmp_path):
    short = _make_pdf(tmp_path / "short.pdf", texts=["ok"])
    findings = check_text_quality(short, lang_out="zh")
    assert not any(f.code == "MAYBE_UNTRANSLATED" for f in findings)


def test_overflow_detects_span_past_media_box(tmp_path):
    document = fitz.open()
    try:
        page = document.new_page()
        media = page.rect
        page.insert_text((media.x1 - 4, 100), "overflow")
        path = tmp_path / "overflow.pdf"
        document.save(path)
    finally:
        document.close()
    findings = check_overflow(path)
    assert any(f.code == "TEXT_OVERFLOW" for f in findings)


def test_visual_blank_detects_blank_rendered_page(tmp_path):
    document = fitz.open()
    try:
        document.new_page()  # no content at all
        path = tmp_path / "blank.pdf"
        document.save(path)
    finally:
        document.close()
    findings = check_visual_blank(path)
    assert any(f.code == "RENDER_BLANK_PAGE" for f in findings)


def test_resource_checks(tmp_path):
    assert check_disk_space(tmp_path) == []
    small = tmp_path / "small.txt"
    small.write_bytes(b"x")
    assert check_output_size(small) == []
    assert check_output_size(tmp_path / "missing") == []


def test_report_ok_flag_tracks_errors():
    ok = report_for("a.pdf", [QaFinding("X", QaSeverity.INFO, "i")])
    assert ok.ok is True
    bad = report_for(
        "a.pdf",
        [QaFinding("E", QaSeverity.ERROR, "e"), QaFinding("W", QaSeverity.WARNING, "w")],
    )
    assert bad.ok is False
    assert [f.code for f in bad.errors] == ["E"]
    assert [f.code for f in bad.warnings] == ["W"]
    payload = bad.to_dict()
    assert payload["finding_counts"] == {"info": 0, "warning": 1, "error": 1}


def test_to_text_never_contains_document_text():
    report = QaReport(source="x.pdf", ok=True)
    report.findings = [
        QaFinding("MAYBE_UNTRANSLATED", QaSeverity.WARNING, "output may be untranslated")
    ]
    text = to_text(report, verbosity=2)
    assert "MAYBE_UNTRANSLATED" in text
    assert text.count("\n") >= 1


def test_save_report_writes_atomically(tmp_path):
    report = report_for("x.pdf", [QaFinding("OK", QaSeverity.INFO, "fine")])
    target = save_report(report, tmp_path / "qa", "doc.mono_pdf")
    assert target.is_file()
    assert "qa_status" not in target.read_text(encoding="utf-8")  # no doc text leaked
    assert target.name == "doc.mono_pdf.qa.json"


def test_run_qa_end_to_end_on_generated_pdf(tmp_path):
    target = _make_pdf(tmp_path / "gen.pdf")
    report = run_qa(target, lang_out="zh", deep=False)
    assert report.ok is True
    codes = {f.code for f in report.findings}
    assert "PDF_OPEN_FAILED" not in codes


def test_excerpt_bounds_length():
    excerpt = QaFinding.excerpt("x" * 500)
    assert len(excerpt) <= 100
    assert excerpt.endswith("…")
