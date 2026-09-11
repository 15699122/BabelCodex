from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorCategory(StrEnum):
    CONFIG = "config"
    INPUT = "input"
    AUTH = "auth"
    TRANSLATION = "translation"
    VALIDATION = "validation"
    BABELDOC = "babeldoc"
    WORKER = "worker"
    OUTPUT = "output"
    RESOURCE = "resource"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ErrorCode(StrEnum):
    CONFIG_INVALID = "CONFIG_INVALID"
    INPUT_NOT_FOUND = "INPUT_NOT_FOUND"
    INPUT_PDF_INVALID = "INPUT_PDF_INVALID"
    PDF_NO_EXTRACTABLE_TEXT = "PDF_NO_EXTRACTABLE_TEXT"
    PDF_SCANNED_DOCUMENT = "PDF_SCANNED_DOCUMENT"
    BABELDOC_NOT_INSTALLED = "BABELDOC_NOT_INSTALLED"
    BABELDOC_VERSION_UNSUPPORTED = "BABELDOC_VERSION_UNSUPPORTED"
    BABELDOC_ASSET_MISSING = "BABELDOC_ASSET_MISSING"
    BABELDOC_RUNTIME_ERROR = "BABELDOC_RUNTIME_ERROR"
    BABELDOC_NO_FINISH_RESULT = "BABELDOC_NO_FINISH_RESULT"
    CODEX_NOT_INSTALLED = "CODEX_NOT_INSTALLED"
    CODEX_NOT_LOGGED_IN = "CODEX_NOT_LOGGED_IN"
    CODEX_AUTH_EXPIRED = "CODEX_AUTH_EXPIRED"
    CODEX_MODEL_UNAVAILABLE = "CODEX_MODEL_UNAVAILABLE"
    CODEX_TIMEOUT = "CODEX_TIMEOUT"
    CODEX_OVERLOADED = "CODEX_OVERLOADED"
    CODEX_EMPTY_OUTPUT = "CODEX_EMPTY_OUTPUT"
    CODEX_INVALID_OUTPUT = "CODEX_INVALID_OUTPUT"
    PLACEHOLDER_MISMATCH = "PLACEHOLDER_MISMATCH"
    BATCH_RESPONSE_MISMATCH = "BATCH_RESPONSE_MISMATCH"
    WORKER_TIMEOUT = "WORKER_TIMEOUT"
    WORKER_CRASHED = "WORKER_CRASHED"
    OUTPUT_PDF_MISSING = "OUTPUT_PDF_MISSING"
    OUTPUT_PDF_INVALID = "OUTPUT_PDF_INVALID"
    DISK_FULL = "DISK_FULL"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class BabelCodexError(Exception):
    category: ErrorCategory
    code: ErrorCode
    safe_message: str
    retryable: bool = False
    technical_message: str | None = None

    def __str__(self) -> str:
        return self.safe_message


def classify_exception(exc: Exception) -> BabelCodexError:
    if isinstance(exc, BabelCodexError):
        return exc
    if isinstance(exc, FileNotFoundError):
        return BabelCodexError(
            category=ErrorCategory.INPUT,
            code=ErrorCode.INPUT_NOT_FOUND,
            safe_message="Input file was not found.",
            technical_message=str(exc),
        )
    if isinstance(exc, TimeoutError):
        return BabelCodexError(
            category=ErrorCategory.TRANSLATION,
            code=ErrorCode.CODEX_TIMEOUT,
            safe_message="Translation timed out.",
            retryable=True,
            technical_message=str(exc),
        )
    return BabelCodexError(
        category=ErrorCategory.UNKNOWN,
        code=ErrorCode.UNKNOWN,
        safe_message="The translation job failed.",
        technical_message=str(exc),
    )


# Per-category maximum total attempts. Connections, credentials and user input
# are never retried automatically; transient translation/resource failures are.
DEFAULT_RETRY_LIMITS: dict[ErrorCategory, int] = {
    ErrorCategory.CONFIG: 1,
    ErrorCategory.INPUT: 1,
    ErrorCategory.AUTH: 1,
    ErrorCategory.TRANSLATION: 3,
    ErrorCategory.VALIDATION: 1,
    ErrorCategory.BABELDOC: 2,
    ErrorCategory.WORKER: 2,
    ErrorCategory.OUTPUT: 1,
    ErrorCategory.RESOURCE: 3,
    ErrorCategory.CANCELLED: 1,
    ErrorCategory.UNKNOWN: 1,
}


def resolve_retry_limits(
    policy: dict[str, int] | None, default_max: int
) -> dict[ErrorCategory, int]:
    """Merge an operator retry policy over the per-category defaults.

    ``default_max`` is the configured global ``max_retries`` and acts as the
    ceiling for total attempts per job; a category policy can only lower it, it
    can never raise it. Unknown category keys are ignored.
    """
    limits = dict(DEFAULT_RETRY_LIMITS)
    for key, value in (policy or {}).items():
        try:
            category = ErrorCategory(str(key))
        except ValueError:
            continue
        try:
            limit = max(1, int(value))
        except (TypeError, ValueError):
            continue
        limits[category] = limit
    ceiling = max(1, int(default_max))
    return {category: min(limit, ceiling) for category, limit in limits.items()}


def retry_limit_for(
    category: ErrorCategory,
    policy: dict[str, int] | None,
    default_max: int,
) -> int:
    """Return the effective total-attempt ceiling for a failure category."""
    return resolve_retry_limits(policy, default_max).get(category, max(1, int(default_max)))
