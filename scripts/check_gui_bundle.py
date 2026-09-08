#!/usr/bin/env python3
"""Audit a staged BabelCodex GUI bundle without executing platform binaries."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

SIDECAR_NAMES = {
    "x86_64-unknown-linux-gnu": "babelcodex-service-x86_64-unknown-linux-gnu",
    "x86_64-pc-windows-msvc": "babelcodex-service-x86_64-pc-windows-msvc.exe",
}
FORBIDDEN_NAMES = {".env", ".env.local", "job.json", "artifacts.json", "qa-report.json"}
FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "__pycache__", "state", "logs", "incoming"}
ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/home/|/Users/|/tmp/|/private/tmp/)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def audit(bundle_dir: Path, target: str, manifest_path: Path | None) -> int:
    if not bundle_dir.is_dir():
        print(f"bundle directory does not exist: {bundle_dir}", file=sys.stderr)
        return 2

    sidecar = bundle_dir / SIDECAR_NAMES[target]
    if not sidecar.is_file():
        print(f"missing target-triple sidecar: {sidecar.name}", file=sys.stderr)
        return 2

    violations: list[str] = []
    for path in bundle_dir.rglob("*"):
        relative = path.relative_to(bundle_dir)
        if set(relative.parts) & FORBIDDEN_PARTS:
            violations.append(f"forbidden path: {relative}")
        if path.name in FORBIDDEN_NAMES:
            violations.append(f"forbidden file: {relative}")
        if path.is_file() and path == sidecar and path.stat().st_size < 16:
            violations.append(f"sidecar is unexpectedly small: {relative}")
        if path.is_file() and path.suffix.lower() in {
            ".toml",
            ".json",
            ".txt",
            ".js",
            ".css",
            ".html",
        }:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if ABSOLUTE_PATH.search(text):
                violations.append(f"possible development-machine absolute path: {relative}")

    if violations:
        print("GUI bundle audit failed:", file=sys.stderr)
        print("\n".join(f"- {item}" for item in violations), file=sys.stderr)
        return 1

    lines = [
        f"{sha256(path)}  {path.relative_to(bundle_dir)}"
        for path in sorted(bundle_dir.rglob("*"))
        if path.is_file()
    ]
    output = "\n".join(lines) + "\n"
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(output, encoding="utf-8")
    print(f"GUI bundle audit passed: {bundle_dir}")
    print(output, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--target", choices=sorted(SIDECAR_NAMES), required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    return audit(args.bundle_dir.resolve(), args.target, args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
