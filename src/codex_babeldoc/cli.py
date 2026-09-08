from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import shutil
import sys

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


def doctor(cfg) -> int:
    checks = {
        "python": sys.version.split()[0],
        "babeldoc_cli": shutil.which("babeldoc"),
        "codex_cli": shutil.which("codex"),
    }
    try:
        import babeldoc
        checks["babeldoc_python"] = getattr(babeldoc, "__version__", "installed")
    except Exception as exc:
        checks["babeldoc_python"] = f"missing: {exc}"
    try:
        import openai_codex
        checks["openai_codex"] = getattr(openai_codex, "__version__", "installed")
    except Exception as exc:
        checks["openai_codex"] = f"missing: {exc}"
    checks["input_dir"] = str(cfg.project.input_dir)
    checks["output_dir"] = str(cfg.project.output_dir)
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cbpdf")
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
