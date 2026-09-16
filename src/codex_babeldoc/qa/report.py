"""Assemble QA findings into a report and render human-safe views.

The human-readable rendering is deliberately terse: it lists check codes,
severities, page numbers and short details, never the translated text.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from codex_babeldoc.qa.layout_checks import check_overflow, check_visual_blank
from codex_babeldoc.qa.models import QaFinding, QaReport, QaSeverity, report_for
from codex_babeldoc.qa.pdf_sanity import check_pdf
from codex_babeldoc.qa.resource_checks import check_disk_space
from codex_babeldoc.qa.text_checks import check_text_quality

_SEVERITY_LABEL = {
    QaSeverity.INFO: "info",
    QaSeverity.WARNING: "warning",
    QaSeverity.ERROR: "error",
}


def run_qa(
    path: Path | str,
    *,
    lang_out: str,
    source_path: Path | str | None = None,
    deep: bool = True,
) -> QaReport:
    """Run the full QA battery against one output PDF and return a report."""
    target = Path(path)
    findings: list[QaFinding] = []
    findings.extend(check_pdf(target))
    findings.extend(check_text_quality(target, lang_out=lang_out, source_path=source_path))
    if deep:
        findings.extend(check_overflow(target))
        findings.extend(check_visual_blank(target))
    findings.extend(check_disk_space(target.parent))
    return report_for(target, findings)


def to_text(report: QaReport, *, verbosity: int = 0) -> str:
    """Render a terse summary that never includes document content."""
    lines = [
        f"QA {report.source} -> {'PASS' if report.ok else 'FAIL'}",
        (
            f"findings: info={len(report.infos)} warning={len(report.warnings)} "
            f"error={len(report.errors)}"
        ),
    ]
    for finding in report.findings:
        if verbosity <= 0 and finding.severity is QaSeverity.INFO:
            continue
        location = f"p{finding.page}" if finding.page is not None else "-"
        line = f"[{_SEVERITY_LABEL[finding.severity]:>7}] {finding.code:<20} {location} {finding.message}"
        if finding.detail:
            line += f" ({finding.detail})"
        lines.append(line)
    return "\n".join(lines)


def save_report(report: QaReport, directory: Path | str, stem: str) -> Path:
    """Atomically write the QA report JSON and return its path."""
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{stem}.qa.json"
    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target_dir,
        prefix=f".{stem}.qa.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target
