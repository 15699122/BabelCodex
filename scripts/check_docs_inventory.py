"""Documentation inventory checks.

The CI documentation gate. Verifies that:
- CLI subcommands documented in README match the registered CLI parsers.
- Every managed source file has an entry in docs/development/codebase-map.md.
- Every path referenced by the codebase map exists on disk.
- Markdown links inside docs/ point to files that exist.

All public helpers accept the repository root so the same checks can run
against the real repository and against synthetic fixtures in tests.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAP_REL = Path("docs/development/codebase-map.md")

# Flags that consume a separate value token (skipped together with the value).
_VALUE_FLAGS = {"--config"}
# Managed source scopes: (directory relative to repo root, glob pattern).
_TRACKED_SCOPES: tuple[tuple[str, str], ...] = (
    ("src", "*.py"),
    ("tests", "*.py"),
    ("scripts", "*.py"),
    (str(Path("gui") / "src"), "*.ts"),
)

_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_ADD_PARSER_PATTERN = re.compile(r"""add_parser\(\s*["']([a-z0-9-]+)["']""")


def readme_cli_commands(root: Path) -> list[tuple[str, int]]:
    """Return (subcommand, line_number) for cbpdf usages in README code blocks."""
    commands: list[tuple[str, int]] = []
    for lineno, line in enumerate(
        (root / "README.md").read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.strip()
        if stripped.startswith(("#", ">", "|")):
            continue
        tokens = stripped.split()
        while "cbpdf" in tokens:
            idx = tokens.index("cbpdf")
            subcommand = _first_positional(tokens[idx + 1 :])
            if subcommand is not None:
                commands.append((subcommand, lineno))
            tokens = tokens[idx + 1 :]
    return commands


def _first_positional(tokens: list[str]) -> str | None:
    """Return the first non-flag token, skipping value-taking flags."""
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token in _VALUE_FLAGS:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        return token
    return None


def registered_cli_commands(root: Path) -> set[str]:
    """Return subcommands registered via argparse add_parser in cli.py."""
    cli = root / "src" / "codex_babeldoc" / "cli.py"
    if not cli.is_file():
        return set()
    return set(_ADD_PARSER_PATTERN.findall(cli.read_text(encoding="utf-8")))


def _map_text(root: Path) -> str | None:
    map_path = root / MAP_REL
    if not map_path.is_file():
        return None
    return map_path.read_text(encoding="utf-8")


def _map_listed_paths(map_text: str) -> set[str]:
    """Backticked tokens in the map that look like managed repo-relative paths."""
    listed: set[str] = set()
    for token in re.findall(r"`([^`\n]+)`", map_text):
        candidate = token.strip().strip("/")
        if "*" in candidate:
            continue
        if candidate.endswith((".py", ".ts")) and "/" in candidate:
            listed.add(candidate)
    return listed


def _managed_files(root: Path) -> list[str]:
    files: list[str] = []
    for scope, pattern in _TRACKED_SCOPES:
        scope_dir = root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob(pattern)):
            rel = path.relative_to(root).as_posix()
            if "__pycache__" in rel or path.suffix == ".pyc":
                continue
            files.append(rel)
    return files


def missing_inventory(root: Path) -> list[str]:
    """Managed files that the codebase map does not list."""
    map_text = _map_text(root)
    if map_text is None:
        return []
    listed = _map_listed_paths(map_text)
    problems: list[str] = []
    for rel in _managed_files(root):
        if rel not in listed:
            problems.append(f"codebase map does not list managed file: {rel}")
    return problems


def map_paths_exist(root: Path) -> list[str]:
    """Backticked paths in the codebase map that do not exist on disk."""
    map_text = _map_text(root)
    if map_text is None:
        return []
    problems: list[str] = []
    for rel in sorted(_map_listed_paths(map_text)):
        if not (root / rel).is_file():
            problems.append(f"codebase map references missing path: {rel}")
    return problems


def readme_commands_registered(root: Path) -> list[str]:
    """README cbpdf usages whose subcommand is not registered in cli.py."""
    registered = registered_cli_commands(root)
    problems: list[str] = []
    for subcommand, lineno in readme_cli_commands(root):
        if subcommand not in registered:
            problems.append(
                f"README.md:{lineno}: 'cbpdf {subcommand}' is not a registered subcommand"
            )
    return problems


def doc_links_exist(root: Path) -> list[str]:
    """Relative markdown links inside docs/ that do not resolve to files."""
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return []
    problems: list[str] = []
    for doc in sorted(docs_dir.rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        for match in _LINK_PATTERN.finditer(text):
            target = match.group(1)
            if target.startswith(("#", "http://", "https://")):
                continue
            resolved = (doc.parent / target.split("#")[0]).resolve()
            if not resolved.is_file():
                problems.append(f"{doc.relative_to(root).as_posix()}: broken link -> {target}")
    return problems


def check(root: Path) -> list[str]:
    """Run every documentation gate check and return aggregated problems."""
    problems: list[str] = []
    if _map_text(root) is None:
        problems.append(f"missing required file: {MAP_REL}")
    else:
        problems.extend(missing_inventory(root))
        problems.extend(map_paths_exist(root))
    problems.extend(readme_commands_registered(root))
    problems.extend(doc_links_exist(root))
    return problems


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; exits non-zero when any documentation problem exists."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="repository root to check (default: current directory)",
    )
    args = parser.parse_args(argv)
    problems = check(Path(args.root).resolve())
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"docs inventory check failed with {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("docs inventory check passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
