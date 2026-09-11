import json
from pathlib import Path

from codex_babeldoc.cli import collect_doctor_checks, doctor
from codex_babeldoc.core.config import load_config


def _toml_string(value: Path) -> str:
    """Serialize a filesystem path as a TOML basic string."""
    return json.dumps(str(value), ensure_ascii=False)


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
        f"input_dir = {_toml_string(tmp_path / 'incoming')}\n"
        f"output_dir = {_toml_string(tmp_path / 'translated')}\n"
        f"state_dir = {_toml_string(tmp_path / 'state')}\n"
        f"log_dir = {_toml_string(tmp_path / 'logs')}\n"
        f"glossary_dir = {_toml_string(tmp_path / 'glossary')}\n"
        f"context_dir = {_toml_string(tmp_path / 'context')}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert main(["--config", str(isolated), "glossary", "import", str(source)]) == 0
    capsys.readouterr()
    assert main(["--config", str(isolated), "glossary", "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["entries"][0]["target"] == "模型"


def test_toml_string_escapes_windows_path() -> None:
    isolated = _toml_string(Path(r"C:\Users\Tester\BabelCodex\incoming"))
    assert isolated == '"C:\\\\Users\\\\Tester\\\\BabelCodex\\\\incoming"'


def test_inspect_and_validate_cli_for_missing_job(tmp_path, capsys):
    from codex_babeldoc.cli import main

    config = tmp_path / "config.toml"
    config.write_text(
        "[project]\n"
        f"input_dir = {_toml_string(tmp_path / 'incoming')}\n"
        f"output_dir = {_toml_string(tmp_path / 'translated')}\n"
        f"state_dir = {_toml_string(tmp_path / 'state')}\n"
        f"log_dir = {_toml_string(tmp_path / 'logs')}\n",
        encoding="utf-8",
    )
    assert main(["--config", str(config), "inspect", "missing"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "job was not found"
    assert main(["--config", str(config), "validate", "missing"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "job was not found"


def test_cleanup_cli_dry_run_reports_without_deleting(tmp_path, capsys):
    from codex_babeldoc.cli import main

    config = tmp_path / "config.toml"
    config.write_text(
        "[project]\n"
        f"input_dir = {_toml_string(tmp_path / 'incoming')}\n"
        f"output_dir = {_toml_string(tmp_path / 'translated')}\n"
        f"state_dir = {_toml_string(tmp_path / 'state')}\n"
        f"log_dir = {_toml_string(tmp_path / 'logs')}\n",
        encoding="utf-8",
    )
    work_dir = tmp_path / "state" / "babeldoc-work" / "job-doc"
    work_dir.mkdir(parents=True)
    (work_dir / "worker-request.json").write_text("{}", encoding="utf-8")

    assert main(["--config", str(config), "cleanup", "--dry-run"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["dry_run"] is True
    assert work_dir.is_dir()


def test_qa_cli_reports_passing_output(tmp_path, capsys):
    import fitz

    from codex_babeldoc.cli import main
    from codex_babeldoc.core.artifacts import Artifact, ArtifactType
    from codex_babeldoc.core.state import JobStatus, StateStore

    config = tmp_path / "config.toml"
    config.write_text(
        "[project]\n"
        f"input_dir = {_toml_string(tmp_path / 'incoming')}\n"
        f"output_dir = {_toml_string(tmp_path / 'translated')}\n"
        f"state_dir = {_toml_string(tmp_path / 'state')}\n"
        f"log_dir = {_toml_string(tmp_path / 'logs')}\n",
        encoding="utf-8",
    )
    for name in ("incoming", "translated"):
        (tmp_path / name).mkdir()
    source = tmp_path / "incoming" / "doc.pdf"
    source.write_bytes(b"%PDF-test")
    output = tmp_path / "translated" / "doc.mono.pdf"
    document = fitz.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "Hello translated output text.")
        document.save(output)
    finally:
        document.close()

    store = StateStore(tmp_path / "state")
    job = store.load(source, config_fingerprint="f")
    job.status = JobStatus.COMPLETED
    job.artifacts = [Artifact(ArtifactType.MONO_PDF, str(output))]
    store.save(job)

    assert main(["--config", str(config), "qa", job.job_id]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert result["qa_status"] == "passed"
    assert result["reports"][0]["report"].endswith(".qa.json")
