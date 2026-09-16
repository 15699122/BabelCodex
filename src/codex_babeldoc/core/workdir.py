"""Safe, bounded removal of per-job BabelDOC working directories.

The helpers mirror the path-safety rules used by the MCP cleanup tool: a
candidate must resolve inside the configured work root, must not be the root
itself, must not be a symlink, and must belong to a terminal job before the
retention sweep removes it. Removal tolerates transient Windows file locks
with a bounded retry/backoff loop.
"""

from __future__ import annotations

import shutil
import time
from collections.abc import Iterable
from pathlib import Path

from codex_babeldoc.core.state import JobState, JobStatus

_REMOVAL_RETRIES = 5
_REMOVAL_BACKOFF_SECONDS = 0.05

SECONDS_PER_DAY = 86_400


class WorkdirError(ValueError):
    """Raised when a candidate working directory is not safe to remove."""


def remove_work_dir(work_dir: Path) -> None:
    """Remove a directory tree, tolerating transient Windows file locks."""
    for attempt in range(_REMOVAL_RETRIES):
        try:
            shutil.rmtree(work_dir)
            return
        except PermissionError:
            if attempt == _REMOVAL_RETRIES - 1:
                raise
            time.sleep(_REMOVAL_BACKOFF_SECONDS * (attempt + 1))


def resolve_work_dir(work_root: Path, candidate: Path) -> Path:
    """Resolve and verify that ``candidate`` is a removable job directory."""
    work_root = work_root.resolve()
    resolved = candidate.resolve()
    try:
        resolved.relative_to(work_root)
    except ValueError as exc:
        raise WorkdirError("working directory is outside the configured worker directory") from exc
    if resolved == work_root:
        raise WorkdirError("refusing to remove the worker directory itself")
    if candidate.is_symlink() or resolved.is_symlink():
        raise WorkdirError("refusing to remove a symlinked job directory")
    return resolved


def sweep_work_dirs(
    work_root: Path,
    jobs: Iterable[JobState],
    *,
    retention_days: int,
    dry_run: bool = False,
) -> dict[str, object]:
    """Remove terminal job working directories older than ``retention_days``.

    Active jobs (``RUNNING`` / ``RETRY_PENDING``) are always kept, as are
    directories younger than the retention window so failed-job diagnostics
    survive for operator review. ``retention_days`` of 0 removes every terminal
    directory immediately. Returns a summary used by the shared service.
    """
    active_by_stem = {
        Path(job.source_path).stem
        for job in jobs
        if job.status in {JobStatus.RUNNING, JobStatus.RETRY_PENDING}
    }
    removal_seconds = max(0, int(retention_days)) * SECONDS_PER_DAY
    now = time.time()
    removed: list[str] = []
    retained: list[str] = []
    if not work_root.is_dir():
        return {"removed": removed, "retained": retained, "dry_run": dry_run}

    for candidate in sorted(work_root.glob("job-*")):
        if not candidate.is_dir():
            continue
        stem = candidate.name[len("job-") :]
        try:
            work_dir = resolve_work_dir(work_root, candidate)
        except WorkdirError as exc:
            retained.append(f"{candidate.name}: {exc}")
            continue
        if stem in active_by_stem:
            retained.append(f"{candidate.name}: active")
            continue
        if removal_seconds and now - work_dir.stat().st_mtime < removal_seconds:
            retained.append(f"{candidate.name}: within retention")
            continue
        if dry_run:
            retained.append(f"{candidate.name}: candidate")
            continue
        try:
            remove_work_dir(work_dir)
        except OSError as exc:
            retained.append(f"{candidate.name}: {exc}")
            continue
        removed.append(str(work_dir))
    return {"removed": removed, "retained": retained, "dry_run": dry_run}
