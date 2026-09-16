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
# Strip ``scheme://authority`` (but not the path) before matching, so ordinary
# ``https://...`` strings are not mistaken for Windows drive paths (the previous
# bare ``[A-Za-z]:[\\/]`` pattern matched the ``s://`` inside ``https://`` and
# produced false positives on generated JS/CSS; see docs/validation/windows.md).
# Stripping only scheme+authority keeps ``file:///home/...`` detectable because
# the Unix path remains after the URL prefix is removed.
URL_AUTHORITY_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://[^/\s\"'<>)]*")
ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|/home/|/Users/|/tmp/|/private/tmp/)")


def contains_development_machine_absolute_path(text: str) -> bool:
    """Detect Windows-drive or known Unix development-machine paths in ``text``.

    ``scheme://authority`` prefixes are removed first so bundled ``https://``
    strings do not trip the Windows drive-letter pattern; the path part of a
    URL is kept, so ``file:///home/...`` and ``file:///C:/...`` still match.
    """
    return bool(ABSOLUTE_PATH.search(URL_AUTHORITY_PATTERN.sub("", text)))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def newest_source_mtime(source_tree: Path) -> float | None:
    """Return the newest mtime among inputs embedded in the frozen sidecar.

    The sidecar binary embeds the ``codex_babeldoc`` package and its declared
    metadata, so any Python source, the PyInstaller spec, or ``pyproject.toml``
    newer than the binary means the bundle shipped a stale sidecar (observed as
    a protocol/config drift in the 2026-09-11 Windows validation).
    """
    candidates: list[Path] = [
        source_tree / "pyproject.toml",
        source_tree / "scripts" / "babelcodex-service.spec",
        *sorted((source_tree / "src").rglob("*.py")),
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.is_file()]
    return max(mtimes) if mtimes else None


def audit(
    bundle_dir: Path, target: str, manifest_path: Path | None, source_tree: Path | None = None
) -> int:
    if not bundle_dir.is_dir():
        print(f"bundle directory does not exist: {bundle_dir}", file=sys.stderr)
        return 2
    if source_tree is not None and not (source_tree / "src").is_dir():
        print(f"source tree has no src directory: {source_tree}", file=sys.stderr)
        return 2

    sidecar = bundle_dir / SIDECAR_NAMES[target]
    if not sidecar.is_file():
        print(f"missing target-triple sidecar: {sidecar.name}", file=sys.stderr)
        return 2

    violations: list[str] = []
    if source_tree is not None:
        newest = newest_source_mtime(source_tree)
        if newest is not None and sidecar.stat().st_mtime < newest:
            violations.append(
                f"sidecar predates newer Python sources (sidecar={sidecar.stat().st_mtime:.0f}, "
                "newest source input, %.0f); rebuild the frozen sidecar before packaging" % newest
            )
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
            if contains_development_machine_absolute_path(text):
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
    parser.add_argument(
        "--source-tree",
        type=Path,
        help=(
            "repository checkout the sidecar was built from; when given, the audit "
            "fails if the sidecar binary is older than any embedded Python source"
        ),
    )
    args = parser.parse_args()
    source_tree = args.source_tree.resolve() if args.source_tree is not None else None
    return audit(args.bundle_dir.resolve(), args.target, args.manifest, source_tree)


if __name__ == "__main__":
    raise SystemExit(main())
