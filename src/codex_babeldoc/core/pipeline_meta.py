"""BabelDOC pipeline metadata recorded per job for operator inspection.

BabelDOC 0.6.x exposes no stable part-level artifacts through its high-level
single-pass ``async_translate`` entrypoint. The internal ``SplitManager`` is
only consulted when an optional page-based ``split_strategy`` is enabled, and
even then parts are transient in-memory passes inside one opaque call. A crashed
job therefore must be retried as a whole; ``part_resume_supported`` is recorded
as ``False`` per job so ``inspect`` shows the assessment alongside the data.
"""

from __future__ import annotations

from pathlib import Path

PART_RESUME_UNSUPPORTED_NOTE = (
    "BabelDOC 0.6.x high-level single-pass pipeline does not expose stable "
    "part-level artifacts; a crashed job must be retried as a whole."
)


def record_pipeline_meta(source: Path, *, backend_name: str) -> dict[str, object]:
    """Record pipeline metadata without ever blocking the translation run."""
    return {
        "backend": backend_name,
        "babeldoc_version": _babeldoc_version(),
        "source_page_count": _source_page_count(source),
        "part_resume_supported": False,
        "note": PART_RESUME_UNSUPPORTED_NOTE,
    }


def _babeldoc_version() -> str:
    try:
        from codex_babeldoc.backends.babeldoc_v064 import detect_version

        return detect_version() or ""
    except Exception:  # noqa: BLE001 - metadata must never block translation
        return ""


def _source_page_count(source: Path) -> int | None:
    try:
        import fitz  # pymupdf, already a BabelDOC dependency; kept lazy

        with fitz.open(source) as document:
            return document.page_count
    except Exception:  # noqa: BLE001 - metadata must never block translation
        return None
