"""Shared bounded logging configuration for CLI, sidecar and workers."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from codex_babeldoc.core.config import LoggingConfig

_LEVELS = {
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "silent": logging.CRITICAL + 1,
}
LOG_FILENAME_PREFIX = "babelcodex-"
_OWNED_HANDLER_ATTR = "_babelcodex_owned"
_SENSITIVE_LINE = re.compile(
    r"(?i)(authorization|api[-_]?key|access[-_]?token|refresh[-_]?token|password|secret)\s*[:=]\s*(?:bearer\s+)?\S+"
)


def _is_owned(handler: logging.Handler) -> bool:
    return bool(getattr(handler, _OWNED_HANDLER_ATTR, False))


def _prune_log_files(log_dir: Path, max_files: int) -> None:
    files = sorted(log_dir.glob("*.log"), key=lambda path: path.stat().st_mtime)
    for path in files[: max(0, len(files) - max_files + 1)]:
        try:
            path.unlink()
        except OSError:
            # A locked historical log must not prevent the application from
            # starting; the next startup can try the bounded cleanup again.
            continue


def configure_logging(
    log_dir: Path,
    settings: LoggingConfig | None = None,
    *,
    verbose: bool = False,
    stream: bool = True,
) -> Path | None:
    """Configure root logging and return the new log path, if enabled."""
    settings = settings or LoggingConfig()
    if verbose:
        settings = LoggingConfig(level="debug", max_files=settings.max_files)
    settings.validate()
    root = logging.getLogger()
    for handler in list(root.handlers):
        if _is_owned(handler):
            root.removeHandler(handler)
            handler.close()
    root.setLevel(_LEVELS[settings.level])
    if settings.level == "silent":
        return None

    log_dir.mkdir(parents=True, exist_ok=True)
    _prune_log_files(log_dir, settings.max_files)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    target = log_dir / f"{LOG_FILENAME_PREFIX}{stamp}.log"
    handlers: list[logging.Handler] = [logging.FileHandler(target, encoding="utf-8")]
    if stream:
        handlers.append(logging.StreamHandler())
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for handler in handlers:
        setattr(handler, _OWNED_HANDLER_ATTR, True)
        handler.setFormatter(formatter)
        root.addHandler(handler)
    return target


def release_file_handlers() -> None:
    """Detach and close all root handlers created by BabelCodex."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if _is_owned(handler):
            root.removeHandler(handler)
            handler.close()


def redact_log_text(text: str) -> str:
    """Redact common credential-like key/value fragments from diagnostics."""
    return _SENSITIVE_LINE.sub(lambda match: f"{match.group(1)}=<redacted>", text)
