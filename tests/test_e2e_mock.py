"""End-to-end tests: real BabelDOC pipeline driven through the orchestrator
with the deterministic MockTranslator.

These tests exercise the full PDF parse/translate/render path without any
network or Codex usage, but they do load the real BabelDOC engine and its
layout models, so they are marked ``integration`` and excluded from the
default pytest run (see ``addopts`` in pyproject.toml).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import fitz
import pytest

from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.orchestrator import Orchestrator
from codex_babeldoc.core.state import JobStatus

FIXTURE = Path(__file__).parent / "fixtures" / "fixture_two_column.pdf"

pytestmark = pytest.mark.integration


def _make_config(tmp_path: Path, worker_mode: str) -> AppConfig:
    cfg = AppConfig(root=tmp_path)
    cfg.translation.translator = "mock"
    cfg.translation.max_retries = 1
    cfg.babeldoc.worker_mode = worker_mode
    cfg.babeldoc.working_dir = tmp_path / "babeldoc-work"
    cfg.resolve_paths()
    cfg.ensure_dirs()
    shutil.copy(FIXTURE, cfg.project.input_dir / FIXTURE.name)
    return cfg


def _assert_completed(cfg: AppConfig, source: Path) -> None:
    orch = Orchestrator(cfg)
    result = orch.run_one(source)
    assert result == "completed"

    job = orch.state.load(source, config_fingerprint=cfg.fingerprint())
    assert job.status is JobStatus.COMPLETED
    assert job.backend_name == "python-internal"
    assert job.translator_name == "mock"

    source_pages = fitz.open(source).page_count
    for name in (
        f"{source.stem}.mono.pdf",
        f"{source.stem}.dual.pdf",
    ):
        output = cfg.project.output_dir / name
        if output.exists():
            doc = fitz.open(output)
            assert doc.page_count >= 1
            text = "".join(page.get_text() for page in doc)
            assert text.strip(), f"{name} contains no extractable text"

    # The dual PDF should have roughly twice the pages (or alternating pairs).
    dual = cfg.project.output_dir / f"{source.stem}.dual.pdf"
    if dual.exists():
        assert fitz.open(dual).page_count >= source_pages


class TestMockEndToEnd:
    def test_inprocess_mock_translation(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path, "inprocess")
        source = cfg.project.input_dir / FIXTURE.name
        _assert_completed(cfg, source)

    def test_subprocess_mock_translation(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path, "subprocess")
        source = cfg.project.input_dir / FIXTURE.name
        _assert_completed(cfg, source)

    def test_completed_job_is_skipped_without_force(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path, "inprocess")
        source = cfg.project.input_dir / FIXTURE.name
        orch = Orchestrator(cfg)
        assert orch.run_one(source) == "completed"
        assert orch.run_one(source) == "skipped"
        assert orch.run_one(source, force=True) == "completed"

    def test_missing_completed_artifact_is_not_skipped(self, tmp_path: Path) -> None:
        from codex_babeldoc.backends.base import PdfTranslateResult
        from codex_babeldoc.core.artifacts import Artifact, ArtifactType

        cfg = _make_config(tmp_path, "inprocess")
        source = cfg.project.input_dir / FIXTURE.name
        orch = Orchestrator(cfg)
        assert orch.run_one(source) == "completed"
        job = orch.state.load(source, config_fingerprint=cfg.fingerprint())
        assert job.artifacts
        output = Path(job.artifacts[0].path)
        output.unlink()
        calls = 0

        class _ReplacementBackend:
            def translate(self, *_args, **_kwargs):
                nonlocal calls
                calls += 1
                output.write_bytes(b"%PDF-recreated")
                return PdfTranslateResult(
                    job_id="replacement",
                    artifacts=[Artifact(ArtifactType.MONO_PDF, str(output))],
                )

        orch.backend = _ReplacementBackend()
        assert orch.run_one(source) == "completed"
        assert calls == 1

    def test_mock_output_has_a_stable_qa_baseline(self, tmp_path: Path) -> None:
        """The fixture PDF must produce a *passing* QA baseline every run.

        The mock translator keeps the source (English) text, so the Chinese
        density heuristic emits a ``MAYBE_UNTRANSLATED`` warning for long
        outputs. Warnings are expected and must not flip the report to failed;
        this test pins that stable baseline.
        """
        from codex_babeldoc.application.service import BabelCodexService

        cfg = _make_config(tmp_path, "inprocess")
        source = cfg.project.input_dir / FIXTURE.name
        _assert_completed(cfg, source)

        service = BabelCodexService(cfg)
        job = service.orchestrator.state.load(source, config_fingerprint=cfg.fingerprint())
        result = service.run_qa(job.job_id)
        assert result["ok"] is True
        assert result["qa_status"] == "passed"

        report_dir = cfg.project.output_dir / "qa"
        report_names = {path.name for path in report_dir.glob("*.qa.json")}
        assert report_names, "no QA report was written"
        for stem in ("mono_pdf", "dual_pdf"):
            assert any(name.startswith(f"{source.stem}.{stem}.") for name in report_names)
