"""Best-effort permissions for local user document data."""

from __future__ import annotations

import os
from pathlib import Path


def ensure_private_dir(path: Path) -> Path:
    """Create a local-data directory and restrict it on POSIX systems."""
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)
    return path


def restrict_file(path: Path) -> None:
    """Restrict an existing local-data file on POSIX systems."""
    if os.name != "nt" and path.exists():
        path.chmod(0o600)
