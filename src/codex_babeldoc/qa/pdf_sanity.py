"""L0 file-level and L1 structure-level sanity checks for output PDFs.

These checks never parse or translate document content; they only establish
that a produced artifact is a real, readable, non-empty PDF with extractable
text. Deeper text/visual checks live in ``text_checks`` and ``layout_checks``.
"""

from __future__ import annotations

from pathlib import Path

from codex_babeldoc.qa.models import QaFinding, QaSeverity

PDF_MAGIC = b"%PDF-"
MAX_PDF_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB hard sanity ceiling
MIN_PDF_BYTES = 4  # long enough to include a PDF header


def check_file_level(path: Path | str) -> list[QaFinding]:
    """L0: existence, size and header sanity of an output file."""
    findings: list[QaFinding] = []
    candidate = Path(path)

    if not candidate.is_file():
        findings.append(
            QaFinding(
                code="FILE_MISSING",
                severity=QaSeverity.ERROR,
                message="Output file does not exist.",
                detail=str(candidate),
            )
        )
        return findings

    size = candidate.stat().st_size
    if size < MIN_PDF_BYTES:
        findings.append(
            QaFinding(
                code="FILE_TOO_SMALL",
                severity=QaSeverity.ERROR,
                message="Output file is too small to be a PDF.",
                detail=f"size={size}",
            )
        )
    if size > MAX_PDF_BYTES:
        findings.append(
            QaFinding(
                code="FILE_TOO_LARGE",
                severity=QaSeverity.ERROR,
                message="Output file exceeds the sanity size ceiling.",
                detail=f"size={size}",
            )
        )

    with candidate.open("rb") as handle:
        magic = handle.read(len(PDF_MAGIC))
    if magic != PDF_MAGIC:
        findings.append(
            QaFinding(
                code="PDF_HEADER_INVALID",
                severity=QaSeverity.ERROR,
                message="File does not start with a PDF header.",
            )
        )
    return findings


def check_pdf_structure(path: Path | str) -> list[QaFinding]:
    """L1: the document opens, is decryptable and has extractable pages."""
    findings: list[QaFinding] = []
    candidate = Path(path)
    try:
        import fitz  # pymupdf; lazy like the rest of the BabelDOC-bound code
    except ImportError as exc:
        findings.append(
            QaFinding(
                code="PDF_LIBRARY_UNAVAILABLE",
                severity=QaSeverity.ERROR,
                message="PyMuPDF is required for QA structure checks.",
                detail=type(exc).__name__,
            )
        )
        return findings

    try:
        document = fitz.open(candidate)
    except Exception as exc:  # noqa: BLE001 - any open failure is structural
        findings.append(
            QaFinding(
                code="PDF_OPEN_FAILED",
                severity=QaSeverity.ERROR,
                message="The document cannot be opened as a PDF.",
                detail=type(exc).__name__,
            )
        )
        return findings

    try:
        if document.needs_pass:
            findings.append(
                QaFinding(
                    code="PDF_ENCRYPTED",
                    severity=QaSeverity.WARNING,
                    message="The document is password protected.",
                    detail="needs_pass=True",
                )
            )
        elif document.is_encrypted:
            findings.append(
                QaFinding(
                    code="PDF_ENCRYPTED",
                    severity=QaSeverity.WARNING,
                    message="The document uses document-level encryption.",
                )
            )

        page_count = document.page_count
        if page_count <= 0:
            findings.append(
                QaFinding(
                    code="PDF_NO_PAGES",
                    severity=QaSeverity.ERROR,
                    message="The document has no pages.",
                )
            )
            return findings

        if page_count > 10_000:
            findings.append(
                QaFinding(
                    code="PDF_PAGE_COUNT_UNUSUAL",
                    severity=QaSeverity.WARNING,
                    message="Page count is unusually high.",
                    detail=f"pages={page_count}",
                )
            )

        # Every page must expose a text dictionary without raising.
        empty_pages = 0
        for index, page in enumerate(document):
            try:
                blocks = page.get_text("dict")
            except Exception as exc:  # noqa: BLE001 - per-page extraction failures
                findings.append(
                    QaFinding(
                        code="PDF_PAGE_TEXT_FAILED",
                        severity=QaSeverity.ERROR,
                        message="Text extraction failed for a page.",
                        page=index,
                        detail=type(exc).__name__,
                    )
                )
                continue
            if not blocks.get("blocks"):
                empty_pages += 1
        if empty_pages == page_count:
            findings.append(
                QaFinding(
                    code="PDF_ALL_PAGES_EMPTY",
                    severity=QaSeverity.ERROR,
                    message="Text extraction returned no blocks on any page.",
                )
            )
    finally:
        document.close()
    return findings


def check_pdf(path: Path | str) -> list[QaFinding]:
    """Run L0 + L1 checks and return the combined findings."""
    return check_file_level(path) + check_pdf_structure(path)
