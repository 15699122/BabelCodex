"""Versioned glossary storage and bounded terminology guidance."""

from __future__ import annotations

import csv
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True, slots=True)
class GlossaryEntry:
    source: str
    target: str
    notes: str = ""
    enabled: bool = True


def read_csv(path: Path) -> tuple[GlossaryEntry, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        if not {"source", "target"}.issubset(fields):
            raise ValueError("glossary CSV must contain source and target columns")
        return tuple(
            GlossaryEntry(
                source=str(row.get("source", "")).strip(),
                target=str(row.get("target", "")).strip(),
                notes=str(row.get("notes", "")).strip(),
                enabled=str(row.get("enabled", "true")).strip().lower()
                not in {"0", "false", "no", "off"},
            )
            for row in reader
        )


def write_csv(path: Path, entries: tuple[GlossaryEntry, ...] | list[GlossaryEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=("source", "target", "notes", "enabled"))
        writer.writeheader()
        for entry in sorted(entries, key=lambda item: item.source.casefold()):
            writer.writerow(
                {
                    "source": entry.source,
                    "target": entry.target,
                    "notes": entry.notes,
                    "enabled": "true" if entry.enabled else "false",
                }
            )
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def version_for(entries: tuple[GlossaryEntry, ...] | list[GlossaryEntry]) -> str:
    payload = "\n".join(
        "\x00".join((entry.source, entry.target, entry.notes, str(entry.enabled)))
        for entry in sorted(entries, key=lambda item: item.source.casefold())
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def glossary_prompt(
    entries: tuple[GlossaryEntry, ...] | list[GlossaryEntry], *, max_chars: int = 4000
) -> str:
    if max_chars <= 0:
        return ""
    lines = ["Terminology requirements (apply consistently when context permits):"]
    used = len(lines[0])
    for entry in sorted(entries, key=lambda item: item.source.casefold()):
        if not entry.enabled or not entry.source or not entry.target:
            continue
        line = f"- {entry.source} → {entry.target}"
        if entry.notes:
            line += f" ({entry.notes})"
        if used + len(line) + 1 > max_chars:
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines) if len(lines) > 1 else ""


class GlossaryStore:
    """Load global and document-specific CSV files with document override semantics."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def load(self, document_stem: str | None = None) -> tuple[GlossaryEntry, ...]:
        merged: dict[str, GlossaryEntry] = {}
        paths = [self.root / "global.csv"]
        if document_stem:
            paths.append(self.root / "documents" / f"{document_stem}.csv")
        for path in paths:
            if not path.is_file():
                continue
            for entry in read_csv(path):
                if entry.source:
                    merged[entry.source] = entry
        return tuple(merged[key] for key in sorted(merged, key=str.casefold))

    def version(self, document_stem: str | None = None) -> str | None:
        entries = self.load(document_stem)
        return version_for(entries) if entries else None

    def guidance(self, document_stem: str | None = None, *, max_chars: int = 4000) -> str:
        return glossary_prompt(self.load(document_stem), max_chars=max_chars)

    def import_csv(self, source: Path, *, document_stem: str | None = None) -> int:
        entries = read_csv(source)
        target = (
            self.root / "documents" / f"{document_stem}.csv"
            if document_stem
            else self.root / "global.csv"
        )
        write_csv(target, entries)
        return len(entries)

    def export_csv(self, destination: Path, *, document_stem: str | None = None) -> int:
        entries = self.load(document_stem)
        write_csv(destination, entries)
        return len(entries)
