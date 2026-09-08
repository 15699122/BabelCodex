from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class PlaceholderInventory:
    counts: tuple[tuple[str, int], ...] = ()

    @classmethod
    def from_counts(cls, counts: dict[str, int]) -> PlaceholderInventory:
        return cls(tuple(sorted(counts.items())))


@dataclass(slots=True, frozen=True)
class TranslationRequest:
    request_id: str
    document_id: str
    sequence: int
    source_text: str
    source_hash: str
    lang_in: str
    lang_out: str
    placeholders: PlaceholderInventory = field(default_factory=PlaceholderInventory)
    glossary_version: str | None = None
    context_version: str | None = None


@dataclass(slots=True, frozen=True)
class TranslationResult:
    request_id: str
    translated_text: str
    validation_status: str = "pending"
    validation_errors: tuple[str, ...] = ()
    attempts: int = 1
    cache_hit: bool = False
    latency_ms: int = 0


@dataclass(slots=True, frozen=True)
class TranslationBatch:
    batch_id: str
    requests: tuple[TranslationRequest, ...]


@dataclass(slots=True, frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
