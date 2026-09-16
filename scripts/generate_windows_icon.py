#!/usr/bin/env python3
"""Generate the Windows ``.ico`` application icon from the PNG source icon.

Tauri's MSI bundling requires a ``.ico`` resource in ``bundle.icon``; the
Linux ``.deb``/AppImage bundles use the PNG source. This script converts
``gui/src-tauri/icons/icon.png`` into ``gui/src-tauri/icons/icon.ico`` with the
standard Windows size list so the packaged MSI/NSIS export has a valid icon.

Usage (from the repository root):

    uv run python scripts/generate_windows_icon.py

The generated ``icon.ico`` is a committed asset; re-run this script only when
the source PNG icon changes. Pillow is transitively available in the locked
development environment (via BabelDOC dependency ``scikit-image``); no new
project dependency is declared for this maintenance script.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOURCE = _REPO_ROOT / "gui" / "src-tauri" / "icons" / "icon.png"
_TARGET = _REPO_ROOT / "gui" / "src-tauri" / "icons" / "icon.ico"

# Standard Windows icon sizes used by installers and file associations.
_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> int:
    if not _SOURCE.is_file():
        print(f"source icon not found: {_SOURCE}", file=sys.stderr)
        return 2
    image = Image.open(_SOURCE)
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    image.save(_TARGET, format="ICO", sizes=_SIZES)
    with Image.open(_TARGET) as check:
        print(f"wrote {_TARGET} (size={check.size}, frames={getattr(check, 'n_frames', 1)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
