# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ``babelcodex-service`` sidecar executable.

This spec is the controlled, reproducible way to build the packaged sidecar
for the Tauri GUI. It is intentionally platform-neutral: run PyInstaller on
each target platform and install the resulting binary under the Tauri
target-triple name in ``gui/src-tauri/binaries/``.

Required environment:
- Python 3.11-3.12 (the project ``.python-version``)
- project runtime dependencies installed via ``uv sync --extra runtime``
- ``pyinstaller`` available in the active environment

Build (from the repository root):

    uv run --extra runtime --with pyinstaller pyinstaller \
        --clean --noconfirm scripts/babelcodex-service.spec

The frozen executable dispatches BabelDOC worker subprocess requests through
the ``--worker-request`` flag, so a single binary serves both the JSONL
sidecar protocol and the in-frozen worker entry point.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# Resolve paths relative to this spec file so the build is reproducible
# from any working directory. PyInstaller exposes the spec directory as
# ``SPECPATH`` while executing the spec.
_REPO_ROOT = Path(SPECPATH).resolve().parent
_ENTRY = str(_REPO_ROOT / "scripts" / "sidecar_entry.py")
_SRC = str(_REPO_ROOT / "src")

# ``babelcodex`` modules are imported by absolute path from ``src``.
# BabelDOC and the Codex SDK are imported lazily at translation time, so
# PyInstaller cannot discover them through static analysis alone.
hiddenimports = [
    "codex_babeldoc.backends.babeldoc_v064",
    "codex_babeldoc.backends.babeldoc_worker",
    "codex_babeldoc.backends.worker_protocol",
    "codex_babeldoc.translators.codex_sdk",
    "codex_babeldoc.translation.gateway",
    "codex_babeldoc.translation.cache",
    "codex_babeldoc.translation.retry",
    "codex_babeldoc.translation.validation",
    "codex_babeldoc.translation.placeholders",
    "codex_babeldoc.translation.batching",
    "codex_babeldoc.translation.glossary",
    "codex_babeldoc.translation.context",
    "codex_babeldoc.translation.thread_state",
]
binaries = []
datas = []
for _package in ("babeldoc", "openai_codex"):
    try:
        _datas, _binaries, _hidden = collect_all(_package)
        datas += _datas
        binaries += _binaries
        hiddenimports += _hidden
    except Exception:  # pragma: no cover - build environment may lack the package
        pass

a = Analysis(
    [_ENTRY],
    pathex=[_SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="babelcodex-service",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)