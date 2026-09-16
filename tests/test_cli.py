import json
import logging
from pathlib import Path

from codex_babeldoc.cli import (
    _configure_logging,
    _release_log_file_handlers,
    collect_doctor_checks,
    doctor,
)
from codex_babeldoc.core.config import load_config


def _write_config(path: Path, **paths: Path) -> None:
    """Write the smallest valid YAML config used by CLI tests."""
    import yaml

    root = path.parent
    values = {
        "schema_version": 1,
        "project": {
            "input_dir": str(paths.get("input_dir", root / "incoming")),
            "output_dir": str(paths.get("output_dir", root / "translated")),
            "state_dir": str(paths.get("state_dir", root / "state")),
            "log_dir": str(paths.get("log_dir", root / "logs")),
            "glossary_dir": str(paths.get("glossary_dir", root / "glossary")),
            "context_dir": str(paths.get("context_dir", root / "context")),
        },
    }
    path.write_text(yaml.safe_dump(values, sort_keys=False), encoding="utf-8")


def test_collect_doctor_checks_detects_installed_runtime():
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "config.yaml")

    checks = collect_doctor_checks(cfg)

    assert checks["python_supported"] is True
    assert checks["babeldoc_python"] == "0.6.4"
    assert checks["openai_codex"]
    assert checks["codex_cli"] or checks["codex_bundled_runtime"]


def test_doctor_succeeds_when_all_critical_checks_pass(monkeypatch, capsys):
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "config.yaml")
    checks = collect_doctor_checks(cfg)
    checks["codex_authenticated"] = True
    checks["codex_auth_message"] = "Logged in"
    monkeypatch.setattr("codex_babeldoc.cli.collect_doctor_checks", lambda config: checks)

    assert doctor(cfg) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["codex_authenticated"] is True


def test_doctor_fails_when_codex_is_not_authenticated(monkeypatch, capsys):
    root = Path(__file__).parents[1]
    cfg = load_config(root / "config" / "config.yaml")
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
    isolated = tmp_path / "config.yaml"
    _write_config(
        isolated,
        input_dir=tmp_path / "incoming",
        output_dir=tmp_path / "translated",
        state_dir=tmp_path / "state",
        log_dir=tmp_path / "logs",
        glossary_dir=tmp_path / "glossary",
        context_dir=tmp_path / "context",
    )
    monkeypatch.chdir(tmp_path)
    assert main(["--config", str(isolated), "glossary", "import", str(source)]) == 0
    capsys.readouterr()
    assert main(["--config", str(isolated), "glossary", "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["entries"][0]["target"] == "模型"


def test_yaml_config_preserves_windows_path() -> None:
    import yaml

    isolated = Path(r"C:\Users\Tester\BabelCodex\incoming")
    payload = yaml.safe_dump({"input_dir": str(isolated)}, sort_keys=False)
    assert str(isolated) in payload


def test_inspect_and_validate_cli_for_missing_job(tmp_path, capsys):
    from codex_babeldoc.cli import main

    config = tmp_path / "config.yaml"
    _write_config(config)
    assert main(["--config", str(config), "inspect", "0" * 64]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "job was not found"
    assert main(["--config", str(config), "validate", "0" * 64]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "job was not found"


def test_cleanup_cli_dry_run_reports_without_deleting(tmp_path, capsys):
    from codex_babeldoc.cli import main

    config = tmp_path / "config.yaml"
    _write_config(config)
    work_dir = tmp_path / "state" / "babeldoc-work" / "job-doc"
    work_dir.mkdir(parents=True)
    (work_dir / "worker-request.json").write_text("{}", encoding="utf-8")

    assert main(["--config", str(config), "cleanup", "--dry-run"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["dry_run"] is True
    assert work_dir.is_dir()


def test_qa_cli_reports_passing_output(tmp_path, capsys):
    import pymupdf as fitz

    from codex_babeldoc.cli import main
    from codex_babeldoc.core.artifacts import Artifact, ArtifactType
    from codex_babeldoc.core.state import JobStatus, StateStore

    config = tmp_path / "config.yaml"
    _write_config(config)
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


def test_qa_cli_stdout_is_machine_readable_in_clean_subprocess(tmp_path):
    """The QA command must emit only JSON on stdout in a fresh subprocess.

    Windows validation reproduced ``JSONDecodeError`` because the PyMuPDF
    ``fitz`` compatibility shim printed a deprecation notice to stdout before
    the JSON document. The production modules now import the official
    ``pymupdf`` name instead; this regression launches the CLI from a clean
    interpreter (where nothing imported fitz/pymupdf first) and asserts the
    whole stdout payload parses as JSON.
    """
    import os
    import subprocess
    import sys

    import pymupdf

    config = tmp_path / "config.yaml"
    _write_config(config)
    for name in ("incoming", "translated"):
        (tmp_path / name).mkdir()
    source = tmp_path / "incoming" / "doc.pdf"
    source.write_bytes(b"%PDF-test")
    output = tmp_path / "translated" / "doc.mono.pdf"
    document = pymupdf.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "Hello translated output text.")
        document.save(output)
    finally:
        document.close()

    from codex_babeldoc.core.artifacts import Artifact, ArtifactType
    from codex_babeldoc.core.state import JobStatus, StateStore

    store = StateStore(tmp_path / "state")
    job = store.load(source, config_fingerprint="f")
    job.status = JobStatus.COMPLETED
    job.artifacts = [Artifact(ArtifactType.MONO_PDF, str(output))]
    store.save(job)

    repo_root = Path(__file__).parents[1]
    env = {
        **os.environ,
        # pytest only adds src/ through its own pythonpath plugin; the child
        # interpreter needs the same path to import codex_babeldoc.cli.
        "PYTHONPATH": str(repo_root / "src"),
    }
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "codex_babeldoc.cli",
            "--config",
            str(config),
            "qa",
            job.job_id,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, f"exit {proc.returncode}: {proc.stderr[-800:]}"
    # A machine consumer must be able to parse stdout as one JSON document.
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["qa_status"] == "passed"


def test_cli_releases_log_file_handlers_at_exit(tmp_path):
    """Root-logger file handlers are closed and detached at CLI exit.

    Windows validation observed ``PermissionError: [WinError 32]`` while a
    temporary directory containing a freshly written ``logs/cbpdf.log`` was
    removed right after a QA command returned. This regression test pins the
    hardening: ``main()`` must release every root ``FileHandler`` in a
    ``finally`` so the log file is not held open during cleanup.
    """
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    root.handlers[:] = []
    try:
        log_dir = tmp_path / "logs"
        _configure_logging(log_dir, verbose=False)

        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        handler = file_handlers[0]
        log_files = list(log_dir.glob("babelcodex-*.log"))
        assert len(log_files) == 1
        log_file = log_files[0]
        assert not handler.stream.closed

        _release_log_file_handlers()

        remaining = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert remaining == []
        # FileHandler.close() flushes, closes the stream and resets it to None;
        # the OS handle is therefore released at this point.
        assert handler.stream is None
        # The handle is gone at the Python level; removal succeeds immediately
        # on platforms where open handles would otherwise block deletion.
        log_file.unlink()
        assert not log_file.exists()
    finally:
        root.handlers[:] = saved_handlers
