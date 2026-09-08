from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from codex_babeldoc.core.config import load_config
from codex_babeldoc.core.orchestrator import Orchestrator


def _configure_logging(log_dir: Path, verbose: bool) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "cbpdf.log", encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def _bundled_codex_runtime() -> str | None:
    try:
        import codex_cli_bin
    except ImportError:
        return None

    executable = "codex.exe" if os.name == "nt" else "codex"
    path = Path(codex_cli_bin.__file__).resolve().parent / "bin" / executable
    return str(path) if path.is_file() else None


def _codex_auth_status(runtime: str | None) -> tuple[bool | None, str]:
    if runtime is None:
        return None, "runtime unavailable"
    try:
        result = subprocess.run(
            [runtime, "login", "status"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, "status check failed"

    message = (result.stdout or result.stderr).strip()
    return result.returncode == 0, message or "unknown"


def collect_doctor_checks(cfg) -> dict[str, str | bool | None]:
    bundled_runtime = _bundled_codex_runtime()
    codex_cli = shutil.which("codex")
    codex_runtime = codex_cli or bundled_runtime
    codex_authenticated, codex_auth_message = _codex_auth_status(codex_runtime)
    checks = {
        "python": sys.version.split()[0],
        "python_supported": (3, 11) <= sys.version_info[:2] < (3, 13),
        "babeldoc_cli": shutil.which("babeldoc"),
        "codex_cli": codex_cli,
        "codex_bundled_runtime": bundled_runtime,
        "codex_authenticated": codex_authenticated,
        "codex_auth_message": codex_auth_message,
    }
    try:
        import babeldoc

        checks["babeldoc_python"] = getattr(babeldoc, "__version__", "installed")
    except Exception as exc:  # noqa: BLE001 - diagnostics must report broken imports
        checks["babeldoc_python"] = f"missing: {exc}"
    try:
        import openai_codex

        checks["openai_codex"] = getattr(openai_codex, "__version__", "installed")
    except Exception as exc:  # noqa: BLE001 - diagnostics must report broken imports
        checks["openai_codex"] = f"missing: {exc}"
    checks["input_dir"] = str(cfg.project.input_dir)
    checks["output_dir"] = str(cfg.project.output_dir)
    return checks


def doctor(cfg) -> int:
    checks = collect_doctor_checks(cfg)
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    critical_values = (
        checks["python_supported"],
        checks["babeldoc_cli"],
        checks["babeldoc_python"],
        checks["openai_codex"],
        checks["codex_cli"] or checks["codex_bundled_runtime"],
        checks["codex_authenticated"],
    )
    return 0 if all(critical_values) else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="babelcodex")
    parser.add_argument("--config", default="config/example.toml")
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    run = sub.add_parser("run")
    run.add_argument("--force", action="store_true")
    one = sub.add_parser("one")
    one.add_argument("pdf")
    one.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    _configure_logging(cfg.project.log_dir, args.verbose)
    if args.command == "doctor":
        return doctor(cfg)

    orch = Orchestrator(cfg)
    if args.command == "run":
        print(json.dumps(orch.run_all(force=args.force), ensure_ascii=False, indent=2))
        return 0
    source = Path(args.pdf).resolve()
    print(orch.run_one(source, force=args.force))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
