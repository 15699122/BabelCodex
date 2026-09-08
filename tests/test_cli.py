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
