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

## Tauri MCP development bridge

The Rust project includes `tauri-plugin-mcp-bridge` as a committed dependency.
The bridge is registered only in Debug builds and binds to `127.0.0.1`; Release
builds do not start it. The capability file includes `mcp-bridge:default` and
Tauri global APIs are enabled for the development bridge.

The MCP server itself is an external Agent tool, not a GUI project dependency.
Do not add `@hypothesi/tauri-mcp-server` to this package. A desktop-capable
Windows/Codex environment may run the server externally, for example with
`npx.cmd -y @hypothesi/tauri-mcp-server`, while Linux Cline should normally not
start it when no targetable desktop is available.

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

## WebdriverIO E2E

The GUI uses `@wdio/tauri-service` as its desktop E2E infrastructure. Three
modes are provided:

| Mode | Command | Needs | Coverage |
|---|---|---|---|
| Vitest | `npm test -- --run` | Node | components, state, protocol, error handling |
| WDIO Browser | `npm run e2e:browser` | Chrome/Chromium + Vite dev server | renderer user flows, mock sidecar |
| WDIO Native | `npm run e2e:native` | desktop session + real sidecar binary | Tauri WebView, plugin-shell, sidecar lifecycle |
| WDIO External | `npm run e2e:external` | WebKitWebDriver (Linux) / Edge WebDriver (Windows) | driver diagnostic fallback |

```bash
npm run e2e:prepare   # prepare capabilities + build/e2e workspace
npm run e2e:build     # build Tauri binary with e2e feature
npm run e2e:browser   # run browser mode (needs Chrome/Chromium)
npm run e2e:native    # run native embedded mode (needs real sidecar)
npm run e2e:external  # run external provider diagnostic (needs WebKitWebDriver)
npm run e2e           # browser + native
```

The E2E build uses a dedicated Cargo feature `e2e` that includes
`tauri-plugin-wdio` and `tauri-plugin-wdio-webdriver`. The MCP Debug Bridge
uses a separate feature `mcp-dev`; the two are mutually exclusive (enforced
at compile time). E2E capabilities are inlined as `CapabilityEntry::Inlined` objects directly in
`tauri.e2e.conf.json` (merged via `--config`); no capability file is ever
written into `src-tauri/capabilities/`, so default/mcp-dev Cargo checks are
never exposed to `wdio:default`. They never enter production builds. The E2E
sidecar runs against
`config/e2e.toml` (`translator = "mock"`) and never touches real Codex.

The frontend loads `@wdio/tauri-plugin` only when `VITE_E2E=1` is set at build
time, so normal builds never include the WDIO frontend plugin.

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