from pathlib import Path

import pytest

from codex_babeldoc.core.state import (
    STATE_TRANSIENT_RETRIES,
    JobStatus,
    StateStore,
)


def test_state_roundtrip(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-test")
    store = StateStore(tmp_path / "state")
    job = store.load(pdf)
    job.status = JobStatus.COMPLETED
    store.save(job)
    again = store.load(pdf)
    assert again.status is JobStatus.COMPLETED
    assert again.fingerprint == job.fingerprint


def _make_store_with_saved_job(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-test")
    store = StateStore(tmp_path / "state")
    job = store.load(pdf)
    store.save(job)
    return store, job


def test_load_by_job_id_retries_transient_permission_error(tmp_path, monkeypatch):
    """Windows transient sharing violations during a concurrent save are retried."""
    store, job = _make_store_with_saved_job(tmp_path)

    real_read_text = Path.read_text
    attempts = {"count": 0}

    def flaky_read_text(self, *args, **kwargs):
        if self.parent == store.root and attempts["count"] < 2:
            attempts["count"] += 1
            raise PermissionError(13, "transient Windows sharing violation")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", flaky_read_text)
    try:
        loaded = store.load_by_job_id(job.job_id)
    finally:
        monkeypatch.undo()

    assert attempts["count"] == 2
    assert loaded is not None
    assert loaded.job_id == job.job_id


def test_load_by_job_id_raises_after_persistent_permission_error(tmp_path, monkeypatch):
    """A persistent PermissionError is still raised after bounded retries."""
    store, job = _make_store_with_saved_job(tmp_path)

    real_read_text = Path.read_text

    def denied_read_text(self, *args, **kwargs):
        if self.parent == store.root:
            raise PermissionError(13, "persistent denial")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", denied_read_text)
    try:
        with pytest.raises(PermissionError):
            store.load_by_job_id(job.job_id)
    finally:
        monkeypatch.undo()


def test_transient_retry_budget_is_bounded(tmp_path, monkeypatch):
    """The retry loop stops after the documented bounded attempt count."""
    store, job = _make_store_with_saved_job(tmp_path)

    real_read_text = Path.read_text
    attempts = {"count": 0}

    def denied_read_text(self, *args, **kwargs):
        if self.parent == store.root:
            attempts["count"] += 1
            raise PermissionError(13, "persistent denial")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", denied_read_text)
    try:
        with pytest.raises(PermissionError):
            store.load_by_job_id(job.job_id)
    finally:
        monkeypatch.undo()

    assert attempts["count"] == STATE_TRANSIENT_RETRIES
