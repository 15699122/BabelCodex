"""Controlled top-level entry point for the PyInstaller-packaged sidecar.

This file is the single frozen entry point referenced by
``scripts/babelcodex-service.spec``. It must stay import-safe outside the
``codex_babeldoc`` package, so it only forwards to
:func:`codex_babeldoc.application.sidecar.main`.
"""

from __future__ import annotations

from codex_babeldoc.application.sidecar import main

if __name__ == "__main__":
    raise SystemExit(main())
