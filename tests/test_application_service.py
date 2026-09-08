from pathlib import Path

from codex_babeldoc.application.service import (
    BabelCodexService,
    InvocationSource,
    StartTranslationCommand,
)
from codex_babeldoc.core.config import load_config
from codex_babeldoc.core.state import JobStage, JobStatus


def test_start_translation_records_invocation_source(tmp_path, monkeypatch):
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    cfg.project.state_dir = tmp_path / "state"
    cfg.ensure_dirs()

    source = tmp_path / "doc.pdf"
    source.write_bytes(b"%PDF-test")

    class _FakeOrchestrator:
        def __init__(self) -> None:
            from codex_babeldoc.core.state import StateStore

            self.state = StateStore(cfg.project.state_dir)
            self.calls: list[tuple] = []

        def run_one(self, path, *, force=False, invocation_source="cli"):
            self.calls.append((path, force, invocation_source))
            job = self.state.load(path, config_fingerprint=cfg.fingerprint())
            job.status = JobStatus.COMPLETED
            job.stage = JobStage.COMPLETED
            self.state.save(job)
            return "completed"

    fake = _FakeOrchestrator()
    service = BabelCodexService(cfg, orchestrator=fake)
    state = service.start_translation(
        StartTranslationCommand(
            source_path=source,
            invocation_source=InvocationSource.MCP,
        )
    )
    assert state.status is JobStatus.COMPLETED
    assert fake.calls[0][2] == "mcp"


def test_get_and_list_jobs(tmp_path):
    from codex_babeldoc.core.state import StateStore

    store = StateStore(tmp_path / "state")
    service = BabelCodexService.__new__(BabelCodexService)
    service.orchestrator = type("O", (), {"state": store})()

    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    job = store.load(pdf, config_fingerprint="f")
    store.save(job)

    assert service.list_jobs()[0].job_id == job.job_id
    assert service.get_job(job.job_id) is not None
    assert service.get_job("missing") is None
