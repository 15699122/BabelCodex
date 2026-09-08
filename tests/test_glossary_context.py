from pathlib import Path

from codex_babeldoc.translation.context import ContextExtractor
from codex_babeldoc.translation.glossary import (
    GlossaryEntry,
    GlossaryStore,
    glossary_prompt,
    write_csv,
)


def test_glossary_import_export_override_and_version(tmp_path: Path):
    root = tmp_path / "glossary"
    write_csv(root / "global.csv", [GlossaryEntry("model", "模型"), GlossaryEntry("API", "接口")])
    write_csv(root / "documents" / "paper.csv", [GlossaryEntry("model", "模型架构")])
    store = GlossaryStore(root)
    entries = store.load("paper")
    assert [(entry.source, entry.target) for entry in entries] == [
        ("API", "接口"),
        ("model", "模型架构"),
    ]
    assert store.version("paper") != store.version()
    exported = tmp_path / "export.csv"
    assert store.export_csv(exported, document_stem="paper") == 2
    assert exported.is_file()


def test_glossary_prompt_is_bounded_and_skips_disabled():
    prompt = glossary_prompt(
        [GlossaryEntry("a", "b"), GlossaryEntry("disabled", "x", enabled=False)],
        max_chars=100,
    )
    assert "a → b" in prompt
    assert "disabled" not in prompt
    assert len(prompt) <= 100


def test_context_extractor_is_bounded_and_stable():
    context = ContextExtractor(max_chars=30).from_text(
        "A Paper Title\nAbstract\nThis is the abstract.\nIntroduction\nLong body."
    )
    assert context.title == "A Paper Title"
    assert context.abstract == "This is the abstract."
    assert len(context.prompt(max_chars=40)) <= 40
    assert context.version


def test_context_extractor_reads_pdf_metadata_and_opening_pages(tmp_path):
    import fitz

    path = tmp_path / "paper.pdf"
    document = fitz.open()
    document.set_metadata({"title": "PDF Metadata Title"})
    page = document.new_page()
    page.insert_text((72, 72), "Abstract\nA PDF abstract extracted from the opening page.")
    document.save(path)
    document.close()

    context = ContextExtractor(max_chars=200).from_pdf(path)
    assert context.title == "PDF Metadata Title"
    assert "PDF abstract extracted" in context.abstract
