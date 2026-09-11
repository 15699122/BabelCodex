"""Resource and disk sanity checks run alongside output QA."""

from __future__ import annotations

import shutil
from pathlib import Path

from codex_babeldoc.qa.models import QaFinding, QaSeverity

MIN_FREE_BYTES = 500 * 1024 * 1024  # 500 MiB


def check_disk_space(path: Path | str, *, min_free_bytes: int = MIN_FREE_BYTES) -> list[QaFinding]:
    """Warn when the output filesystem has very little free space."""
    try:
        usage = shutil.disk_usage(Path(path).resolve().parent)
    except OSError as exc:
        return [
            QaFinding(
                code="DISK_USAGE_UNAVAILABLE",
                severity=QaSeverity.INFO,
                message="Disk usage could not be determined.",
                detail=type(exc).__name__,
            )
        ]
    if usage.free < min_free_bytes:
        return [
            QaFinding(
                code="LOW_DISK_SPACE",
                severity=QaSeverity.WARNING,
                message="Very little free disk space remains.",
                detail=f"free={usage.free}",
            )
        ]
    return []


def check_output_size(
    path: Path | str, *, max_bytes: int = 2 * 1024 * 1024 * 1024
) -> list[QaFinding]:
    """Warn when a single output file approaches the sanity size ceiling."""
    candidate = Path(path)
    if not candidate.is_file():
        return []
    size = candidate.stat().st_size
    if size >= max_bytes:
        return [
            QaFinding(
                code="OUTPUT_TOO_LARGE",
                severity=QaSeverity.ERROR,
                message="Output file exceeds the size sanity ceiling.",
                detail=f"size={size}",
            )
        ]
    return []
