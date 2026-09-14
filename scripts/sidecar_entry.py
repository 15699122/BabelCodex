"""Controlled top-level entry point for the PyInstaller-packaged sidecar.

This file is the single frozen entry point referenced by
``scripts/babelcodex-service.spec``. It must stay import-safe outside the
``codex_babeldoc`` package, so it only forwards to
:func:`codex_babeldoc.application.sidecar.main`.
"""

from __future__ import annotations

import multiprocessing

if __name__ == "__main__":
    # PyInstaller worker children re-enter the frozen executable with
    # multiprocessing's private command-line arguments. Handle those before
    # BabelCodex's sidecar argparse sees them.
    multiprocessing.freeze_support()
    from codex_babeldoc.application.sidecar import main

    raise SystemExit(main())
