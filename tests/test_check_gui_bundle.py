"""Regression tests for scripts/check_gui_bundle.py."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_gui_bundle.py"

_WINDOW_TARGET = "x86_64-pc-windows-msvc"


@pytest.fixture(scope="module")
def audit_module():
    spec = importlib.util.spec_from_file_location("check_gui_bundle_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    (bundle / "assets").mkdir(parents=True)
    sidecar = bundle / "babelcodex-service-x86_64-pc-windows-msvc.exe"
    sidecar.write_bytes(b"babelcodex-fake-sidecar-payload-16-bytes")
    return bundle


def test_https_urls_are_not_flagged_as_absolute_paths(audit_module, tmp_path):
    """Generated JS/CSS with ordinary https/http URLs must pass the audit."""
    bundle = _make_bundle(tmp_path)
    (bundle / "assets" / "index.js").write_text(
        'const endpoint="https://tauri.app/v1/api";'
        'fetch("http://localhost:5173/@vite/client").then(r=>r.json());'
        'const wss="wss://event.example.com/stream";',
        encoding="utf-8",
    )
    (bundle / "assets" / "index.css").write_text(
        '@import url("https://fonts.example.com/ink.css");'
        ".body{background:url('https://img.example.com/paper.png')}",
        encoding="utf-8",
    )
    assert audit_module.audit(bundle, _WINDOW_TARGET, None) == 0


def test_windows_drive_path_is_flagged(audit_module, tmp_path):
    bundle = _make_bundle(tmp_path)
    (bundle / "assets" / "index.js").write_text(
        'const cfg="C:\\\\Users\\\\dev\\\\secrets\\\\config.toml";', encoding="utf-8"
    )
    assert audit_module.audit(bundle, _WINDOW_TARGET, None) == 1


def test_unix_development_paths_are_flagged(audit_module, tmp_path):
    bundle = _make_bundle(tmp_path)
    (bundle / "assets" / "index.js").write_text(
        'const a="/home/dev/project/state";const b="/tmp/build/cache";',
        encoding="utf-8",
    )
    assert audit_module.audit(bundle, _WINDOW_TARGET, None) == 1


def test_file_scheme_url_path_is_still_flagged(audit_module, tmp_path):
    """Stripping the URL scheme must not hide a real Unix path inside file://."""
    detector = audit_module.contains_development_machine_absolute_path
    assert detector('load("file:///home/dev/translated/out.pdf")') is True
    assert detector("file:///C:/Users/dev/out.pdf") is True


def test_url_strings_are_not_absolute_paths(audit_module):
    detector = audit_module.contains_development_machine_absolute_path
    assert detector("https://tauri.app/v1/api") is False
    assert detector("http://localhost:5173/@vite/client") is False
    assert detector('import.meta.url==="https://cdn.example.com/x.js"') is False
    assert detector("C:\\Users\\dev\\secrets") is True
    assert detector("/home/dev/project") is True


def test_missing_sidecar_returns_two(audit_module, tmp_path):
    bundle = tmp_path / "empty-bundle"
    bundle.mkdir()
    assert audit_module.audit(bundle, _WINDOW_TARGET, None) == 2


def test_forbidden_file_is_flagged(audit_module, tmp_path):
    bundle = _make_bundle(tmp_path)
    (bundle / ".env").write_text("SECRET=1", encoding="utf-8")
    assert audit_module.audit(bundle, _WINDOW_TARGET, None) == 1
