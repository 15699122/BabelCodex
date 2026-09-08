from pathlib import Path

from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.orchestrator import Orchestrator
from codex_babeldoc.translation.glossary import GlossaryEntry, write_csv


def test_orchestrator_builds_document_scoped_guidance(tmp_path: Path):
    cfg = AppConfig(root=tmp_path)
    cfg.translation.translator = "mock"
    cfg.resolve_paths()
    cfg.ensure_dirs()
    source = cfg.project.input_dir / "paper.pdf"
    source.write_bytes(b"%PDF-test")
    write_csv(cfg.project.glossary_dir / "global.csv", [GlossaryEntry("model", "模型")])
    write_csv(
        cfg.project.glossary_dir / "documents" / "paper.csv",
        [GlossaryEntry("model", "模型架构")],
    )
    (cfg.project.context_dir / "paper.txt").write_text(
        "A Paper\nAbstract\nA bounded abstract.\nIntroduction\nBody.", encoding="utf-8"
    )

    spec = Orchestrator(cfg)._translator_spec(source)
    assert spec.glossary_version
    assert spec.context_version
    assert "模型架构" in spec.context_prompt
    assert "A bounded abstract." in spec.context_prompt
    cfg.codex.context_max_chars = 30
    bounded = Orchestrator(cfg)._translator_spec(source)
    assert len(bounded.context_prompt or "") <= 30


def test_orchestrator_uses_pdf_context_when_no_sidecar_exists(tmp_path: Path):
    import fitz

    cfg = AppConfig(root=tmp_path)
    cfg.translation.translator = "mock"
    cfg.resolve_paths()
    cfg.ensure_dirs()
    source = cfg.project.input_dir / "paper.pdf"
    document = fitz.open()
    document.set_metadata({"title": "PDF Title"})
    page = document.new_page()
    page.insert_text((72, 72), "Abstract\nExtracted abstract from PDF.")
    document.save(source)
    document.close()

    spec = Orchestrator(cfg)._translator_spec(source)
    assert "PDF Title" in (spec.context_prompt or "")
    assert "Extracted abstract" in (spec.context_prompt or "")
