from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


class ArtifactType(StrEnum):
    SOURCE_PDF = "source_pdf"
    MONO_PDF = "mono_pdf"
    DUAL_PDF = "dual_pdf"
    QA_REPORT = "qa_report"
    WORKER_LOG = "worker_log"
    GLOSSARY = "glossary"


@dataclass(slots=True)
class Artifact:
    artifact_type: ArtifactType
    path: str
    size: int = 0
    sha256: str = ""
    created_at: str = ""
    validated: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> Artifact:
        return cls(
            artifact_type=ArtifactType(str(values["artifact_type"])),
            path=str(values["path"]),
            size=int(values.get("size", 0)),
            sha256=str(values.get("sha256", "")),
            created_at=str(values.get("created_at", "")),
            validated=bool(values.get("validated", False)),
        )
