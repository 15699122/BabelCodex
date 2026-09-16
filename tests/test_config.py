from pathlib import Path

import pytest

from codex_babeldoc.core.config import load_config


def test_load_example_config():
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "config.yaml")
    assert cfg.translation.translator == "codex-sdk"
    assert cfg.translation.lang_out == "zh"
    assert cfg.project.input_dir == root / "cache" / "incoming"
    assert cfg.codex.max_turns_before_compact == 0


def test_yaml_config_uses_portable_layout(tmp_path):
    cfg = load_config(Path(__file__).parents[1] / "config" / "config.yaml")
    assert cfg.project.output_dir == cfg.root / "output"
    assert cfg.project.state_dir == cfg.root / "cache" / "state"
    assert cfg.project.log_dir == cfg.root / "logs"
    assert cfg.logging.level == "info"
    assert cfg.logging.max_files == 5


def test_toml_configuration_is_rejected(tmp_path):
    toml_path = tmp_path / "legacy.toml"
    toml_path.write_text("[project]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be YAML"):
        load_config(toml_path)


def test_config_round_trip_is_atomic_and_keeps_backup(tmp_path):
    from codex_babeldoc.core.config import AppConfig, save_config

    path = tmp_path / "config" / "config.yaml"
    config = AppConfig(root=tmp_path)
    config.resolve_paths()
    save_config(config, path)
    config.logging.level = "debug"
    save_config(config, path)
    assert load_config(path).logging.level == "debug"
    assert path.with_suffix(".yaml.bak").is_file()


def test_invalid_logging_settings_are_rejected(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("schema_version: 1\nlogging:\n  level: trace\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported log level"):
        load_config(path)


def test_config_round_trip_does_not_persist_internal_root(tmp_path):
    from codex_babeldoc.core.config import AppConfig, save_config

    path = tmp_path / "config.yaml"
    config = AppConfig(root=tmp_path)
    config.resolve_paths()
    save_config(config, path)
    text = path.read_text(encoding="utf-8")
    assert "root:" not in text
    assert "schema_version: 1" in text
