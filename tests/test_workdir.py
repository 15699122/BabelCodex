"""Working-directory retention sweep and path-safe removal helpers."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from codex_babeldoc.core.state import JobState, JobStatus
from codex_babeldoc.core.workdir import (
    WorkdirError,
    remove_work_dir,
    resolve_work_dir,
    sweep_work_dirs,
)


def _terminal_job(work_root: Path, stem: str = "doc") -> JobState:
    source = work_root.parent / f"{stem}.pdf"
    source.write_bytes(b"%PDF-test")
    return JobState(
        job_id=f"job-{stem}",
        source_path=str(source.resolve()),
        source_fingerprint="f",
        config_fingerprint="c",
        status=JobStatus.FAILED,
    )


def _make_workdir(work_root: Path, name: str) -> Path:
    work_dir = work_root / name
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "worker-request.json").write_text("{}", encoding="utf-8")
    return work_dir


def test_sweep_removes_old_terminal_workdir(tmp_path):
    work_root = tmp_path / "work"
    work_dir = _make_workdir(work_root, "job-doc")
    old = time.time() - 30 * 86400
    os.utime(work_dir, (old, old))
    job = _terminal_job(work_root)
    result = sweep_work_dirs(work_root, [job], retention_days=1)
    assert result["removed"] == [str(work_dir.resolve())]
    assert not work_dir.exists()


def test_sweep_keeps_fresh_terminal_workdir_within_retention(tmp_path):
    work_root = tmp_path / "work"
    work_dir = _make_workdir(work_root, "job-doc")
    job = _terminal_job(work_root)
    result = sweep_work_dirs(work_root, [job], retention_days=7)
    assert work_dir.exists()
    assert any("within retention" in item for item in result["retained"])


def test_sweep_keeps_active_job_workdir(tmp_path):
    work_root = tmp_path / "work"
    work_dir = _make_workdir(work_root, "job-doc")
    job = _terminal_job(work_root)
    job.status = JobStatus.RUNNING
    result = sweep_work_dirs(work_root, [job], retention_days=0)
    assert work_dir.exists()
    assert any("active" in item for item in result["retained"])


def test_sweep_dry_run_removes_nothing(tmp_path):
    work_root = tmp_path / "work"
    work_dir = _make_workdir(work_root, "job-doc")
    old = time.time() - 30 * 86400
    os.utime(work_dir, (old, old))
    job = _terminal_job(work_root)
    result = sweep_work_dirs(work_root, [job], retention_days=1, dry_run=True)
    assert work_dir.exists()
    assert result["removed"] == []
    assert any("candidate" in item for item in result["retained"])


def test_sweep_refuses_symlinked_job_directory(tmp_path):
    work_root = tmp_path / "work"
    work_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = work_root / "job-evil"
    link.symlink_to(outside, target_is_directory=True)
    result = sweep_work_dirs(work_root, [], retention_days=0)
    assert link.is_symlink()
    assert outside.exists()
    assert any("outside" in item or "symlink" in item for item in result["retained"])


def test_resolve_work_dir_rejects_outside_root_and_root_itself(tmp_path):
    work_root = tmp_path / "work"
    work_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(WorkdirError, match="outside"):
        resolve_work_dir(work_root, outside)
    with pytest.raises(WorkdirError, match="itself"):
        resolve_work_dir(work_root, work_root)


def test_remove_work_dir_retries_transient_lock(tmp_path, monkeypatch):
    from codex_babeldoc.core import workdir as workdir_module

    target = tmp_path / "dir"
    target.mkdir()
    real_rmtree = workdir_module.shutil.rmtree
    calls = 0

    def flaky_rmtree(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise PermissionError("transient lock")
        return real_rmtree(*args, **kwargs)

    monkeypatch.setattr(workdir_module.shutil, "rmtree", flaky_rmtree)
    monkeypatch.setattr(workdir_module.time, "sleep", lambda _seconds: None)
    remove_work_dir(target)
    assert calls == 3
    assert not target.exists()
