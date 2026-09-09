from pathlib import Path

from codex_babeldoc.core.config import load_config


def test_load_example_config():
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    assert cfg.translation.translator == "codex-sdk"
    assert cfg.translation.lang_out == "zh"
    assert cfg.project.input_dir == root / "incoming"
    assert cfg.codex.max_turns_before_compact == 0
