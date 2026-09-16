# Sidecar binaries

Release builds place platform-specific binaries here using Tauri's target
triple naming convention. Generated binaries are intentionally not committed.

```text
babelcodex-service-x86_64-unknown-linux-gnu
babelcodex-service-x86_64-pc-windows-msvc.exe
```

## Building the sidecar

Build the sidecar from the repository root with the controlled PyInstaller
spec (`scripts/babelcodex-service.spec`, entry `scripts/sidecar_entry.py`):

```bash
uv run --extra runtime --with pyinstaller pyinstaller \
    --clean --noconfirm scripts/babelcodex-service.spec
```

The frozen binary serves both the JSONL sidecar protocol and the BabelDOC
worker subprocess (dispatched via `--worker-request` inside a frozen bundle).
Install the built executable under the Tauri target-triple name above for the
target platform. The packaged binary and its frozen worker dispatch must be
validated on the target platform; see `docs/validation/windows.md`.