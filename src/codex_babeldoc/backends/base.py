from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from codex_babeldoc.core.artifacts import Artifact
from codex_babeldoc.core.events import JobEvent


@dataclass(slots=True, frozen=True)
class PdfTranslateRequest:
    protocol_version: int
    job_id: str
    source_path: Path
    output_dir: Path
    working_dir: Path
    lang_in: str
    lang_out: str
    backend_name: str
    backend_version: str
    produce_mono: bool
    produce_dual: bool
    config_fingerprint: str


@dataclass(slots=True)
class PdfTranslateResult:
    job_id: str
    artifacts: list[Artifact] = field(default_factory=list)
    total_seconds: float = 0.0
    backend_name: str = ""
    backend_version: str = ""


class PdfBackend(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def is_available(self) -> bool: ...

    def translate(self, request: PdfTranslateRequest) -> PdfTranslateResult: ...


class EventSink(Protocol):
    def __call__(self, event: JobEvent) -> None: ...
