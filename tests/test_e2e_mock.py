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
