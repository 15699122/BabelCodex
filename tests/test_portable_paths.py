from pathlib import Path

from codex_babeldoc.core.portable_paths import portable_layout, resolve_portable_root


def test_portable_layout_is_relative_to_config_parent(tmp_path: Path):
    config = tmp_path / "config" / "config.yaml"
    config.parent.mkdir()
    config.write_text("schema_version: 1\n", encoding="utf-8")
    assert resolve_portable_root(config) == tmp_path
    layout = portable_layout(config)
    assert layout.incoming == tmp_path / "cache" / "incoming"
    assert layout.babeldoc_cache == tmp_path / "cache" / "babeldoc"
    assert layout.relative_paths()["resource"] == "resource"


def test_portable_layout_does_not_depend_on_current_working_directory(tmp_path: Path, monkeypatch):
    root = tmp_path / "portable"
    config = root / "config" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("schema_version: 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert portable_layout(config).output == root / "output"
