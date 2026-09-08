"""Bounded document context extraction."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DocumentContext:
    title: str = ""
    abstract: str = ""

    @property
    def version(self) -> str | None:
        if not self.title and not self.abstract:
            return None
        return hashlib.sha256(f"{self.title}\x00{self.abstract}".encode()).hexdigest()

    def prompt(self, *, max_chars: int = 4000) -> str:
        parts = []
        if self.title:
            parts.append(f"Document title: {self.title}")
        if self.abstract:
            parts.append(f"Document abstract/context: {self.abstract}")
        return "\n".join(parts)[:max_chars]


class ContextExtractor:
    def __init__(self, *, max_chars: int = 4000) -> None:
        self.max_chars = max(0, max_chars)

    def from_file(self, path: Path) -> DocumentContext:
        return self.from_text(path.read_text(encoding="utf-8"))

    def from_pdf(self, path: Path) -> DocumentContext:
        """Extract bounded metadata and opening-page text from a PDF."""
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PDF context extraction requires PyMuPDF") from exc

        with fitz.open(path) as document:
            metadata = document.metadata or {}
            metadata_title = str(metadata.get("title") or "").strip()
            opening_text = "\n".join(
                document.load_page(index).get_text() for index in range(min(3, document.page_count))
            )
        extracted = self.from_text(opening_text)
        return DocumentContext(title=metadata_title or extracted.title, abstract=extracted.abstract)

    def from_text(self, text: str) -> DocumentContext:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return DocumentContext()
        title = lines[0][:300]
        abstract = ""
        for index, line in enumerate(lines[1:], start=1):
            if re.fullmatch(r"(?i)(abstract|summary|摘要|概要)[:：]?", line):
                body = []
                for candidate in lines[index + 1 :]:
                    if re.fullmatch(
                        r"(?i)(introduction|background|方法|methods?|引言|背景)[:：]?", candidate
                    ):
                        break
                    body.append(candidate)
                abstract = " ".join(body)
                break
        if not abstract:
            abstract = " ".join(lines[1:4])
        return DocumentContext(title=title, abstract=abstract[: self.max_chars])
