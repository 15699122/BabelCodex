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

Release packaging must place a platform-specific sidecar binary in
`src-tauri/binaries/` using Tauri's target-triple naming convention. Generated
sidecar binaries are intentionally excluded from version control.