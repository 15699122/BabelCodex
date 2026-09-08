from codex_babeldoc.core.state import JobStatus, StateStore


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
