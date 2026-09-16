"""QA data model for output PDF quality reports.

A :class:`QaReport` is deliberately a *summary* of findings, not a dump of the
translated document. Findings carry a short code, a severity and a location;
message text never embeds full paragraphs or sensitive document content.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path

QA_MODEL_VERSION = 1

_REPORT_EXCERPT_CHARS = 80


class QaSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class QaFinding:
    code: str
    severity: QaSeverity
    message: str
    page: int | None = None
    detail: str | None = None

    @classmethod
    def excerpt(cls, text: str, limit: int = _REPORT_EXCERPT_CHARS) -> str:
        """Return a short, safe excerpt for diagnostics without full text."""
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[:limit]}…"


@dataclass(slots=True)
class QaReport:
    source: str
    ok: bool
    findings: list[QaFinding] = field(default_factory=list)
    created_at: str = ""
    version: int = QA_MODEL_VERSION

    @property
    def errors(self) -> list[QaFinding]:
        return [f for f in self.findings if f.severity is QaSeverity.ERROR]

    @property
    def warnings(self) -> list[QaFinding]:
        return [f for f in self.findings if f.severity is QaSeverity.WARNING]

    @property
    def infos(self) -> list[QaFinding]:
        return [f for f in self.findings if f.severity is QaSeverity.INFO]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "source": self.source,
            "ok": self.ok,
            "created_at": self.created_at,
            "finding_counts": {
                "info": len(self.infos),
                "warning": len(self.warnings),
                "error": len(self.errors),
            },
            "findings": [asdict(finding) for finding in self.findings],
        }


def report_for(path: Path | str, findings: list[QaFinding]) -> QaReport:
    """Build a report from findings; ``ok`` is False when any ERROR exists."""
    from datetime import UTC, datetime

    return QaReport(
        source=str(path),
        ok=not any(f.severity is QaSeverity.ERROR for f in findings),
        findings=findings,
        created_at=datetime.now(UTC).isoformat(),
    )
