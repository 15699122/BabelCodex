import json
from pathlib import Path

from codex_babeldoc.cli import collect_doctor_checks, doctor
from codex_babeldoc.core.config import load_config


def test_collect_doctor_checks_detects_installed_runtime():
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")

    checks = collect_doctor_checks(cfg)

    assert checks["python_supported"] is True
    assert checks["babeldoc_python"] == "0.6.4"
    assert checks["openai_codex"]
    assert checks["codex_cli"] or checks["codex_bundled_runtime"]


def test_doctor_succeeds_when_all_critical_checks_pass(monkeypatch, capsys):
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    checks = collect_doctor_checks(cfg)
    checks["codex_authenticated"] = True
    checks["codex_auth_message"] = "Logged in"
    monkeypatch.setattr("codex_babeldoc.cli.collect_doctor_checks", lambda config: checks)

    assert doctor(cfg) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["codex_authenticated"] is True


def test_doctor_fails_when_codex_is_not_authenticated(monkeypatch, capsys):
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "example.toml")
    checks = collect_doctor_checks(cfg)
    checks["codex_authenticated"] = False
    checks["codex_auth_message"] = "Not logged in"
    monkeypatch.setattr("codex_babeldoc.cli.collect_doctor_checks", lambda config: checks)

    assert doctor(cfg) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["codex_authenticated"] is False


def test_glossary_cli_import_and_list(tmp_path, monkeypatch, capsys):
    from codex_babeldoc.cli import main

    source = tmp_path / "terms.csv"
    source.write_text("source,target\nmodel,模型\n", encoding="utf-8")
    isolated = tmp_path / "config.toml"
    isolated.write_text(
        "[project]\n"
        f'input_dir = "{tmp_path / "incoming"}"\n'
        f'output_dir = "{tmp_path / "translated"}"\n'
        f'state_dir = "{tmp_path / "state"}"\n'
        f'log_dir = "{tmp_path / "logs"}"\n'
        f'glossary_dir = "{tmp_path / "glossary"}"\n'
        f'context_dir = "{tmp_path / "context"}"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert main(["--config", str(isolated), "glossary", "import", str(source)]) == 0
    capsys.readouterr()
    assert main(["--config", str(isolated), "glossary", "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["entries"][0]["target"] == "模型"
