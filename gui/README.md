# BabelCodex GUI

This directory contains the Tauri 2 + React/TypeScript desktop host spike.

## Local development

```bash
npm ci
npm test
npm run build
npm run tauri dev
```

The browser/Vite development shell uses an in-memory mock transport. The
packaged Tauri application uses the fixed `binaries/babelcodex-service`
sidecar and passes only the configured TOML path.

The GUI does not import BabelDOC, initialize the Codex SDK, execute system
Python, or expose arbitrary shell commands. Long-running work remains in the
Python Application Service and its worker process.

The New translation view uses the fixed Tauri dialog plugin for packaged file
selection and restricts the picker to PDF files. Browser/Vite development uses
the native browser file input and drag-and-drop fallback; selected browser
files remain mock paths and are not uploaded or read by the GUI.

Release packaging must place a platform-specific sidecar binary in
`src-tauri/binaries/` using Tauri's target-triple naming convention. Generated
sidecar binaries are intentionally excluded from version control.

## Cross-platform bundle audit

After copying a built GUI and its target-triple sidecar into a staging
directory, run the dependency-free audit from the repository root:

```bash
python scripts/check_gui_bundle.py ./staging/linux \
  --target x86_64-unknown-linux-gnu \
  --manifest ./staging/linux/SHA256SUMS
```

Use `x86_64-pc-windows-msvc` for a Windows staging directory. The audit checks
the expected sidecar, rejects user state, credentials, caches, development
directories and likely machine-specific absolute paths, and emits an uppercase
SHA-256 manifest. It does not replace native Windows packaged smoke tests or
code-signing verification.

For a Linux bundle build, provide the already-built sidecar explicitly or use
the project virtualenv entry point:

```bash
bash scripts/build_linux_gui_bundle.sh .venv/bin/babelcodex-service
```

The script installs the sidecar under the Linux target triple only for the
duration of `tauri build`, runs the GUI tests and production build first, and
removes the copied binary on exit. It does not replace a Linux host smoke test
and must not be used with an untrusted executable path. Linux `.deb` and
AppImage bundle creation is supported here; target-machine smoke and
distribution approval remain separate release steps.