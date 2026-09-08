from __future__ import annotations

from collections.abc import Callable
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
    qps: int = 1
    min_text_length: int = 5
    watermark_output_mode: str = "no_watermark"
    auto_extract_glossary: bool = False
    ocr_workaround: bool = False
    auto_enable_ocr_workaround: bool = True
    enhance_compatibility: bool = True
    translate_table_text: bool = False


@dataclass(slots=True)
class PdfTranslateResult:
    job_id: str
    artifacts: list[Artifact] = field(default_factory=list)
    total_seconds: float = 0.0
    backend_name: str = ""
    backend_version: str = ""
    glossary: object | None = None
    raw: object | None = None  # opaque backend payload for diagnostics


class PdfBackend(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def is_available(self) -> bool: ...

    def translate(
        self,
        request: PdfTranslateRequest,
        translator_factory: Callable[[], object],
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> PdfTranslateResult: ...


@dataclass(slots=True, frozen=True)
class ProgressEvent:
    stage: str
    stage_current: int | None = None
    stage_total: int | None = None
    overall_progress: float | None = None
    message: str | None = None


class EventSink(Protocol):
    def __call__(self, event: JobEvent) -> None: ...
