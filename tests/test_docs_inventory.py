"""Tests for scripts/check_docs_inventory.py.

The first group runs the checks against the real repository and acts as the
CI documentation gate described in ``docs/README.md``. The second group uses
a tiny synthetic repository to verify that each check reports the intended
class of drift.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = REPO_ROOT / "scripts" / "check_docs_inventory.py"

_spec = importlib.util.spec_from_file_location("check_docs_inventory", _SCRIPT)
assert _spec is not None and _spec.loader is not None
inventory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inventory)


# ---------------------------------------------------------------------------
# Repository-level gate
# ---------------------------------------------------------------------------


def test_repo_inventory_complete() -> None:
    assert inventory.missing_inventory(REPO_ROOT) == []


def test_repo_map_paths_exist() -> None:
    assert inventory.map_paths_exist(REPO_ROOT) == []


def test_repo_readme_commands_registered() -> None:
    assert inventory.readme_commands_registered(REPO_ROOT) == []


def test_repo_doc_links_exist() -> None:
    assert inventory.doc_links_exist(REPO_ROOT) == []


def test_repo_check_passes() -> None:
    assert inventory.check(REPO_ROOT) == []


def test_repo_readme_has_cli_commands() -> None:
    """Sanity: the gate is meaningful, README must actually contain commands."""
    commands = [token for token, _ in inventory.readme_cli_commands(REPO_ROOT)]
    assert commands, "README no longer documents any cbpdf command"


# ---------------------------------------------------------------------------
# Synthetic-repository unit tests
# ---------------------------------------------------------------------------


def _make_repo(root: Path) -> None:
    (root / "src" / "codex_babeldoc").mkdir(parents=True)
    (root / "docs" / "development").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "src" / "codex_babeldoc" / "cli.py").write_text(
        'sub.add_parser("doctor")\nsub.add_parser("run")\n', encoding="utf-8"
    )
    (root / "README.md").write_text(
        "```bash\nuv run cbpdf --config config/example.toml doctor\n```\n", encoding="utf-8"
    )
    (root / "docs" / "development" / "codebase-map.md").write_text(
        "# Codebase map\n\n| `src/codex_babeldoc/cli.py` | CLI entry |\n",
        encoding="utf-8",
    )


def test_synthetic_repo_passes(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    assert inventory.check(tmp_path) == []


def test_missing_inventory_reports_unregistered_file(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    (tmp_path / "src" / "codex_babeldoc" / "new_module.py").write_text("", encoding="utf-8")
    problems = inventory.missing_inventory(tmp_path)
    assert problems == ["codebase map does not list managed file: src/codex_babeldoc/new_module.py"]


def test_missing_inventory_skips_pycache(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    (tmp_path / "scripts" / "__pycache__").mkdir()
    (tmp_path / "scripts" / "__pycache__" / "x.pyc").write_bytes(b"")
    (tmp_path / "scripts" / "helper.py").write_text("", encoding="utf-8")
    problems = inventory.missing_inventory(tmp_path)
    assert "codebase map does not list managed file: scripts/helper.py" in problems
    assert not any("__pycache__" in p for p in problems)


def test_map_paths_exist_reports_missing_path(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    map_path = tmp_path / "docs" / "development" / "codebase-map.md"
    map_path.write_text(
        "# Codebase map\n\nsee `src/codex_babeldoc/cli.py` and `tests/test_gone.py`\n",
        encoding="utf-8",
    )
    assert inventory.map_paths_exist(tmp_path) == [
        "codebase map references missing path: tests/test_gone.py"
    ]


def test_readme_command_must_be_registered(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        "```bash\nuv run cbpdf doctor\nuv run cbpdf --config config/example.toml bogus\n```\n",
        encoding="utf-8",
    )
    problems = inventory.readme_commands_registered(tmp_path)
    assert problems == ["README.md:3: 'cbpdf bogus' is not a registered subcommand"]


def test_flag_with_value_is_skipped(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("```bash\ncbpdf --config config/example.toml run\n```\n", encoding="utf-8")
    assert inventory.readme_commands_registered(tmp_path) == []


def test_doc_links_exist_reports_broken_link(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    index = tmp_path / "docs" / "README.md"
    index.write_text(
        "[map](development/codebase-map.md)\n[broken](development/gone.md)\n"
        "[anchor](#section)\n[external](https://example.com)\n",
        encoding="utf-8",
    )
    assert inventory.doc_links_exist(tmp_path) == [
        "docs/README.md: broken link -> development/gone.md"
    ]


def test_check_without_map_reports_missing_file(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    assert inventory.check(tmp_path) == ["missing required file: docs/development/codebase-map.md"]


def test_main_returns_nonzero_on_problems(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "docs" / "development").mkdir(parents=True)
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    problems = inventory.check(tmp_path)
    assert problems
    assert problems
    assert inventory.main([str(tmp_path)]) != 0
