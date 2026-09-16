# Compatibility Baseline

## Linux worker/retry follow-up fixes (2026-09-16)

- Orchestrator retry loop now clamps the total-attempt ceiling to at least 1,
  matching `resolve_retry_limits`: `max_retries=0` means one initial attempt
  with no automatic retry, and the final error reports the actual attempt
  count. Regressions in `tests/test_retry_policy.py`.
- The BabelDOC worker now routes its own `logging` diagnostics (gateway
  validation-retry warnings and similar) to `worker-diagnostics.log` inside
  the job working directory, keeping the stderr channel machine-readable
  (protocol progress JSONL plus tolerated third-party output only). Remaining
  stderr noise is upstream-only: BabelDOC per-paragraph fallback diagnostics
  and the PyMuPDF `fitz` deprecation notice. Regressions in
  `tests/test_worker.py::TestWorkerDiagnosticsLogging`.
- Both fixes require fresh native Windows evidence (rebuild the PyInstaller
  sidecar and rerun the frozen worker gate; rerun the persisted
  `cbpdf one --config config/e2e.toml` and `cbpdf qa` path) before the
  corresponding Windows `FAIL` items can be closed; they remain
  `WINDOWS_VERIFICATION_PENDING`. Details in
  [`docs/validation/windows.md`](validation/windows.md).
  **Superseded:** the 2026-09-16 Windows run rebuilt the current-source
  sidecar and closed both items — see “Windows revalidation of the Linux
  follow-up fixes (2026-09-16)” above. The historical Windows `FAIL` rows are
  preserved unchanged in the validation document.

## Linux output confirmation follow-up (2026-09-16)

- The current Windows portable/YAML validation identified a product-code defect:
  constructing the application service through `Orchestrator` created the configured
  output directory before the sidecar could honor `confirmed=false`.
- Linux fixed the lifecycle boundary by initializing `Orchestrator` with
  `ensure_dirs(include_output=False)`. The sidecar now leaves output absent before
  confirmation and creates it only after `confirmed=true`; translation rendering
  retains responsibility for creating output when a job actually writes artifacts.
- Regression coverage is
  `tests/test_sidecar.py::test_real_sidecar_startup_does_not_create_output_before_confirmation`.
-   Linux verification for the current tree is Python `257 passed, 5 deselected`, mock
  integration `5 passed`, GUI `28 passed` plus production build, Ruff/format,
  compileall, docs inventory and lock checks all passing.
- This is Linux evidence only. A fresh Windows sidecar build and native JSONL
  `prepare_output_directory` probe must be executed before the Windows item can move
  from `WINDOWS_VERIFICATION_PENDING` to `WINDOWS_PASS`.

## Linux PyMuPDF package-name hygiene follow-up (2026-09-16)

- Decision on the residual `fitz` deprecation notice recorded by Windows: the
  project does not add a `fitz` alias shim and does not suppress upstream
  stderr. The remaining notice comes from upstream BabelDOC importing the
  deprecated shim and belongs to a future dependency update.
- Action: `scripts/generate_fixture.py` now imports `pymupdf as fitz` — it was
  the last project file still importing the deprecated shim directly.
- Regressions: `tests/test_babeldoc_compat.py::TestPyMuPDFPackageNameHygiene`
  pins (a) no `import fitz` / `from fitz` anywhere under `src/`, `scripts/` or
  `tests/`, and (b) the fixture generator produces a non-empty PDF in a
  subprocess with no `deprecated` text on stdout/stderr (`pymupdf` unavailable
  skips).
- Windows MSI (`light.exe` LGHT0217), native WDIO (`uv_os_get_passwd ...
  ENOMEM`), MSI extraction/parity, native GUI/manual, clean-user/security and
  live Codex/PDF remain `FAIL`/`BLOCKED`/`NOT RUN` Windows-operator items; no
  Linux-side change is implied.

## Windows revalidation of the Linux follow-up fixes (2026-09-16)

- 本节是“Linux follow-up 完成后进行的 Windows 复验”的**计划参考**，
  准确的命令、证据、失败分类和手工修复步骤统一以
  `docs/validation/windows.md` 的“Windows validation of current portable/YAML working tree:
  2026-09-16”及其 Failure analysis and Linux follow-up / Current disposition 为准。
- 当前 portable/YAML 源树的 Windows 结果混合存在，产品整体仍处于
  `WINDOWS_VERIFICATION_PENDING`。已通过项目的证据（锁定 Python 环境、Python suite、
  Ruff/format/compileall/docs inventory、GUI build/test、PowerShell staging/audit、
  fresh sidecar build/protocol/allowlist、settings/staging/log retrieval、
  Tauri Rust/features/Debug/Release build、moved-root audit/layout/process smoke、
  embedded native WDIO 6 specs/20 tests、cleanup）参见 windows.md 对应行。
- 产品侧 FAIL 是 output confirmation contract：sidecar 启动时已经创建 output 目录，
  因此无法观察 `prepare_output_directory(confirmed=false)`。Linux 已完成生命周期修复，
  但该项在 Windows 复验成功前仍保持 `WINDOWS_VERIFICATION_PENDING`。
- BLOCKED/NOT RUN 项目（原生手动 GUI/视觉、安装器/MSI/NSIS、
  クリーンユーザー/セキュリティ/署名/SBOM、ライブ Codex/実PDF/長文書）も本 portable/YAML
  ラウンドで解決済みではなく、後の専用作業に委ねる。
- 文書内で「Windows 再検証により両 follow-up が閉じた」と記述している箇所がある場合は、
  それは過去の別源木に対する記録であり、現在の portable/YAML 木については
  windows.md の本輪結果が標準となる。歴史 FAIL 行は消さず、参照だけで整合させる。

## Linux dependency-shape recovery (2026-09-15)

- The local virtual environment was resynchronized with the declared lockfile using `uv sync --locked --extra runtime --extra dev`. `BabelDOC 0.6.4`, `openai-codex 0.147.0` and the bundled Codex CLI runtime are now installed and importable.
- The previous local failures caused by `babeldoc`/`openai_codex` absence are resolved: version detection returns `0.6.4`, bundled runtime discovery succeeds, targeted CLI/retry/BabelDOC tests pass (`34 passed`), and the full Python suite passes (`234 passed, 5 deselected`).
- `cbpdf doctor` still reports `codex_authenticated=false` / `Not logged in` on this machine. This is an expected unauthenticated local state, not a dependency-shape failure; no live Codex request was made.
- This Linux environment recovery does not alter Windows validation status. Windows Python/uv, frozen sidecar, native WDIO, MSI and desktop acceptance still require independent Windows evidence and remain governed by `docs/validation/windows.md`.

## Linux detailed validation run (2026-09-15)

- Level 1 passed: Python `234 passed, 5 deselected`, integration mock `5 passed`, GUI Vitest `28 passed`, GUI build, Ruff, compileall, docs inventory, Cargo default/mcp-dev/e2e and formatting checks. `cbpdf doctor` is `BLOCKED_ENV` only for the unauthenticated Codex state (`Not logged in`); runtime dependencies themselves are healthy.
- Linux Native E2E passed with 4 specs and 15 tests through the real Tauri WebView and embedded WebDriver. Native mock lifecycle, path rejection, sidecar handshake and smoke all passed; project process/port cleanup passed.
- Browser Mode is `BLOCKED_ENV`, not a product failure: no system Chrome/Chromium or chromedriver was available, and the managed Chrome download stalled before spec execution. The project-owned stale WDIO/Vite session was cleaned; no unrelated workspace process was touched.
- Windows-only behavior remains outside Linux evidence and must stay `WINDOWS_VERIFICATION_PENDING` until actual Windows execution. Linux `PASS` does not promote any Windows queue item.

## Latest Windows current-head reconciliation (2026-09-15)

- Windows validated documentation commit `268102b1a0c48ad359e54ccf1b6798e82448b4b8`; relative to `8f046ef`, it contains documentation only, so no new product-code fix is indicated on Linux.
- GUI unit/build, capability separation, Rust default/mcp-dev/e2e checks, Tauri debug builds, direct sidecar protocol/allowlist, narrow release/NSIS process checks, narrow MCP localhost observation and cleanup passed.
- Current Windows blockers/failures remain: `npm ci` file-lock recovery (`EBUSY`/`ENOTEMPTY`), Python/uv runtime/cache access, native WDIO pre-spec `uv_os_get_passwd ... ENOMEM`, frozen worker `unable to open database file`, and WiX `light.exe` MSI failure. Validation-only dependency repair does not convert clean installation into PASS.
- Native GUI/picker/DPI/accessibility, clean-user installation, MSI admin extraction/parity, external-provider diagnostics and authorized live Codex/PDF remain incomplete. Overall compatibility state remains `WINDOWS_VERIFICATION_PENDING`.
- The next Windows run must restore a writable local environment, rebuild the sidecar from the current source, diagnose WDIO before the full suite, repair the matching WiX toolchain, and record all results in `docs/validation/windows.md`; previous artifacts and Linux results do not substitute for current Windows evidence.

## Latest Windows current-head configuration result (2026-09-15)

- The latest Windows run targeted `dev` commit `8f046ef12ab9a9e8d82c260673a303892202ec21`. GUI unit/build, inline capability separation, Rust default/mcp-dev/e2e boundaries, Tauri debug builds, direct sidecar protocol/allowlist and narrow release process checks passed.
- The current-head native WDIO regression failed before spec loading with `uv_os_get_passwd ... ENOMEM`; the frozen worker failed with `unable to open database file`; and current MSI generation failed in WiX `light.exe`. These are current FAIL/BLOCKED evidence, not configuration passes.
- Windows recovery must first restore writable Python/uv, npm/uv cache, `TEMP`/`TMP`, E2E workspace and WiX toolchain paths, then rebuild the target-triple sidecar and rerun the affected gates. Previous artifacts and previous-commit `WVQ-017` PASS evidence do not close the current-head failures.
- Overall compatibility state remains `WINDOWS_VERIFICATION_PENDING`. Native GUI/picker/path/DPI/accessibility, clean-user installation, release security, MCP localhost observation and authorized live Codex/PDF remain separately pending.
- The executable Windows follow-up is intentionally centralized in `docs/validation/windows.md`: restore writable local caches and Python/uv, rebuild and probe a fresh sidecar, diagnose WDIO before the full suite, repair the WiX toolchain before MSI parity, then execute native GUI/clean-user/MCP/release/live checks in that order. No prior artifact or Linux result substitutes for current Windows evidence.

## Linux GUI notice/state lifecycle follow-up (2026-09-14)

- Linux routed App-level notices through a new shared `JobStore.setNotice()`
  so polling/reconnect updates cannot overwrite a locally shown selection or
  error notice; GUI regressions pin the behavior. The Windows Release
  selection-notice persistence `FAIL` remains `WINDOWS_VERIFICATION_PENDING`
  until native retest.
- `startTranslation` now uses a one-shot request that does not schedule a
  global reconnect on rejection; a rejected path keeps the healthy connection
  `ready`. This addresses the observed `正在重新连接` after path rejection;
  native Windows revalidation remains pending.
- These fixes do not diagnose the Debug-only healthy-handshake failure, which
  remains an open Windows follow-up.

## Latest Windows revalidation after Linux status/PID fixes (2026-09-14)

- The dirty WSL source at `dev` HEAD `7cd978e` was synchronized one-way to E:
  with the GUI failed-state tone fix and conservative Windows PID-query fix.
  Windows Python `226 passed, 5 deselected`, GUI `24 passed`, mock PDF
  integration `5 passed`, current frozen/target-triple sidecars, freshness
  audits, NSIS/MSI, extraction parity and process smokes passed.
- The frozen valid worker functionally completed but emitted
  `--multiprocessing-fork` argument/parser warnings; this remains a current
  `FAIL` for frozen subprocess stderr cleanliness. Linux added
  `multiprocessing.freeze_support()` before importing the frozen sidecar
  entrypoint and a regression test; a fresh native Windows frozen-worker run is
  still required before this item can be closed.
- The earlier automated native stale-GUI attempt was `BLOCKED` by Computer Use,
  but the subsequent human Windows retest passed: the stale sidecar showed
  `本地服务不可用` / `Sidecar unavailable` with the corrected red status light,
  while the fresh control showed `本地服务已连接`. The earlier historical
  green-indicator `FAIL` remains preserved in the validation history.
- The operator observed a green light during `正在连接本地服务`; a neutral
  gray connecting-state indicator is recommended as a UX improvement, but is
  not a current acceptance failure. The GUI picker/path/permission/
  cancellation/reconnection matrix remains `NOT RUN` with
  `SKIPPED_BY_USER_REQUEST`, per explicit user instruction. Details are in
  [`docs/validation/windows.md`](validation/windows.md).
- The follow-up manual GUI observations passed Chinese rendering, keyboard
  navigation, Settings, empty Jobs state, reduced-size layout and the narrow
  Unicode/space/allowlist/missing/permission/picker-cancel checks. NVDA is
  permanently skipped because it is not installed. Mock-job cancellation and
  sidecar reconnection were observed to fail; artifact tamper validation was
  blocked because the mock job failed before producing an artifact. Clean-user
  installation/recovery (`WIN-MANUAL-005`) is permanently skipped by explicit
  user request, so no clean-user conclusion is inferred. A current GUI `FAIL`
  was also recorded: clicking `x` on a top notice such as `Sidecar handshake
  ready` closes it only momentarily before it reappears. Linux now stores
  dismissal in the shared JobStore and has GUI regression coverage; native
  Windows notice dismissal remains pending. Details are in
  [`docs/validation/windows.md`](validation/windows.md).

## Latest current-source stale-GUI observation (2026-09-14)

- The fresh control GUI launched, displayed `本地服务已连接` with
  `Sidecar handshake ready`, and exited normally.
- The current GUI paired with the deliberately stale sidecar failed closed as
  intended at the text/banner level (`本地服务不可用` / `Sidecar unavailable`),
  but its status light remained green. The full stale-GUI observation is
  therefore `FAIL` for semantic status presentation, not a release pass.
- The likely cause and required Linux follow-up are recorded in
  [`docs/validation/windows.md`](validation/windows.md). This is a manual
  observation and does not establish general native GUI or release acceptance.
- The GUI picker, path, permission, cancellation and reconnection interaction
  matrix was explicitly skipped for this round and is recorded as `NOT RUN`
  with disposition `SKIPPED_BY_USER_REQUEST`; no PASS or BLOCKED conclusion is
  inferred from the narrower process-smoke evidence.

## Latest real Codex benchmark attempt (2026-09-14)

- An operator-initiated real `codex-sdk` run was started from the current
  Windows source. The six-page input reached `translating`, but its runner
  disappeared before persisting a terminal state or producing artifacts; this
  is `BLOCKED`, not a translation or QA pass.
- A follow-up `inspect` exposed a Windows-specific state-recovery error:
  `_process_is_alive()` propagated `OSError: [WinError 11]` from
  `os.kill(pid, 0)`. The formal live Codex/PDF compatibility conclusion
  remains pending. Linux now handles indeterminate PID-query `OSError`
  conservatively and has a regression test; the repaired source still requires
  native Windows revalidation before this item can be considered closed.

## Latest Windows validation reconciliation (2026-09-14, current source and package gates)

- The current `dev` source at `7cd978eaa3bd1b9e4d7226d626603a0bdc3b7a9a` was
  synchronized to the disposable Windows validation workspace with filtered
  one-way copying and selected-file SHA-256 parity. The current-source package
  and runtime checks passed: controlled-temp Python suite `225 passed, 5
  deselected`, GUI `23 passed`, mock PDF integration `5 passed`, frozen worker
  valid/invalid requests, protocol-v1 and target-triple handshakes, fresh/stale
  bundle audits, NSIS/MSI build and extraction parity, QA/tamper checks and
  release GUI process smoke.
- The earlier Linux follow-ups for documentation-inventory separator handling
  and frozen `bitstring` submodule collection are therefore both revalidated
  natively. Their Windows status is closed by direct evidence; the historical
  failed runs remain unchanged in `docs/validation/windows.md`.
- The current automated product validation summary is `PASS 31 / FAIL 0 /
  BLOCKED 4 / NOT RUN 6 / NOT APPLICABLE 1`; those blocked native desktop
  observations were not executable from the automated run because no trusted
  targetable desktop surface was available. A subsequent operator-run
  current-source stale-sidecar observation is recorded above and is `FAIL` for
  its green unavailable-state indicator. The unexecuted items include clean-
  user recovery, WVQ-007 lifecycle, release security, dependency remediation
  and live Codex/PDF. Overall status remains `WINDOWS_VERIFICATION_PENDING`.
- This result does not establish a Windows release. Unsigned development
  artifacts, native GUI/accessibility/path interaction, clean-user behavior,
  lifecycle semantics and authorized live service acceptance remain separate
  requirements. Linux results must not be promoted to `WINDOWS_PASS`.

## Linux follow-up after the 2026-09-14 operator observations

- Linux corrected the GUI connection-status CSS mapping so `failed` sidecar
  connections use the destructive status color. A GUI regression test now pins
  the failed/ready status-tone contract. The current Windows stale-GUI result
  remains a historical `FAIL` until the repaired package is observed natively;
  it is not promoted to `WINDOWS_PASS`.
- Linux hardened `_process_is_alive()` against indeterminate native `OSError`
  PID queries by conservatively treating the process as alive. A regression
  test covers the behavior. The Windows recovery path and the real Codex
  benchmark remain `WINDOWS_VERIFICATION_PENDING`/blocked until rerun with an
  approved isolated benchmark.
- Linux evidence after the fixes: Python `226 passed, 5 deselected`, mock PDF
  integration `5 passed` with 10 non-blocking fork deprecation warnings, GUI
  `24 passed`, GUI build, Ruff, format, compileall and docs inventory all pass.

## Latest Windows validation reconciliation (2026-09-12, MSI revalidation)

- The current WSL `dev` working tree at HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` was synchronized one-way to the disposable E: validation workspace. The dirty source included five documentation files and eleven code/test files; 68 files were copied, 0 failed, 17 Windows-local excluded/preserved entries remained, and all eleven changed/untracked code/test SHA-256 hashes matched.
- Windows automated validation passed: Python `201 passed, 5 deselected`, GUI Vitest `22 passed`, mock PDF integration `5 passed`, lock/sync, Ruff, compileall, doctor, Vite, Cargo, Tauri config/icon checks, QA positive/tamper/cleanup, PyInstaller, frozen/target-triple sidecar handshakes, worker error path, fresh/stale bundle audit, NSIS/MSI build, MSI administrative extraction with payload parity, extracted-sidecar handshake and release/extracted GUI process smoke.
- Fresh sidecar SHA-256 is `B892AD806BD7E579BBA153C373BFFC4F1A03CFCF04D184E576B00D06827D4EB5`; release GUI is `8B1450D6872EBC57133AA88C4BB8C62A30F78A49D8D6B074740A8A66252FA934`; NSIS is `EFE0FF2D3E93FA5BF93428E62BF22DDD9FD79A699FBF7007550506AD671A448A`; MSI is `28F5206CD54C559623863285BA6A1B2E576D0F10AA0FB225BA969DC78C4F3576`. These are unsigned development artifacts.
- No current `FAIL` was observed. Packaged stale-GUI error observation and the native GUI interaction/path/DPI/NVDA matrix are `BLOCKED` because `sky` trusted RPC is unavailable. Clean-user recovery, full WVQ-007 lifecycle semantics, release security, live Codex/PDF and dependency-advisory remediation remain `NOT RUN`; Linux-only AppImage/native-Linux acceptance is `NOT APPLICABLE`.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`. Linux follow-up is limited to provisioning native UI automation, completing the native WVQ-007 lifecycle matrix, and scheduling release-security/live-service checks. No business code, dependency, or configuration was changed by this validation run.

## Latest Windows validation reconciliation (2026-09-12, latest Linux CLI/QA change revalidation)

- The current WSL `dev` working tree at HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` was synchronized one-way to the disposable E: validation workspace. The source included the current dirty-tree CLI file-handle release change and its regression test, plus the existing GUI/QA changes; 68 files were copied, 0 failed, and 17 Windows-local excluded/preserved entries remained. SHA-256 parity was confirmed for 11 changed or untracked code/test files.
- Windows automated validation passed: Python `201 passed, 5 deselected`, GUI Vitest `22 passed`, mock PDF integration `5 passed`, lock/sync, Ruff, compileall, doctor, Vite, Cargo, Tauri config/icon checks, PyInstaller, frozen/target-triple sidecar handshakes, worker error path, fresh/stale bundle audit, NSIS/MSI build, release GUI process smoke, and the PDF QA positive/tamper/cleanup harness. The new CLI log-handler release regression passed; the prior QA cleanup `WinError 32` was not reproduced in this run.
- Fresh sidecar SHA-256 is `617E3B38440B3BAAF884844480AD3825B79C645CC35B9B261E0BEB38DE08FB53`; release GUI is `4801F1565974DA99368271EE5A298C89A40AD00695B7FADBF052004BE55A615F`; NSIS is `645CB227A80CD9A65656F3D68D761D4CE8DEAC37DC1720441F9E53BEC9358744`; MSI is `FEDCF16AE47F0F1599E8F12075F7FD6C7642C6363C23844B105548E99D9B31CB`. These are unsigned development artifacts.
- No current `FAIL` was observed. MSI administrator extraction/package parity is `BLOCKED` because the current MSI administrative extraction timed out without a log or payload. Packaged stale-GUI error observation and the native GUI interaction/path/DPI/NVDA matrix are also `BLOCKED` because the Windows computer-use trusted RPC service is unavailable. Clean-user recovery, full WVQ-007 lifecycle semantics, release security, live Codex/PDF, and dependency-advisory remediation remain `NOT RUN`; Linux-only AppImage/native-Linux acceptance is `NOT APPLICABLE`.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`. Linux follow-up is to recover MSI extraction evidence, run the native GUI and clean-user matrices when the Windows UI harness is available, complete WVQ-007 lifecycle coverage, and schedule release-security/live-service checks. No business code, dependency, or configuration was changed by this validation run.

Last verified: 2026-09-10

## Local development baseline

| Component | Verified version/status |
| --- | --- |
| Host | Ubuntu 26.04.1 LTS on WSL2, x86-64 |
| uv | 0.12.10 |
| Python | CPython 3.12.14 managed by uv |
| BabelDOC | 0.6.4 |
| openai-codex | 0.147.0 |
| openai-codex-cli-bin | 0.147.0 |
| pytest | 9.1.1 |
| Ruff | 0.16.6 |

The system Python is 3.14.4 and is intentionally not used because BabelCodex currently requires Python 3.11–3.12. `.python-version` pins local project commands to Python 3.12.

## Verified commands

```bash
uv sync --locked --extra runtime --extra dev
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run babeldoc --warmup
uv run babelcodex --config config/example.toml doctor
uv run --extra runtime --with pyinstaller pyinstaller \
    --clean --noconfirm scripts/babelcodex-service.spec
```

The last command builds the packaged `babelcodex-service` sidecar from
`scripts/babelcodex-service.spec` (entry: `scripts/sidecar_entry.py`). It is
the controlled replacement for the previously temporary, uncommitted PyInstaller
entry: the frozen binary dispatches the BabelDOC worker subprocess through
`--worker-request` (`codex_babeldoc.backends.worker_client.worker_command`)
instead of `python -m`, which cannot execute inside a PyInstaller bundle. The
spec is platform-neutral; the binary must be built and validated on each target
platform (e.g. Windows target-triple naming for the Tauri externalBin), and the
build plus frozen `--worker-request` behavior are `WINDOWS_VERIFICATION_PENDING`.

On 2026-09-08:

- dependency resolution completed successfully with 95 packages;
- BabelDOC warmup completed and downloaded the layout model/CMap assets;
- formatting and lint checks passed;
- the unit test suite reported 6 passing tests;
- the bundled Codex runtime reported `codex-cli 0.147.0`;
- Codex authentication was not active, so `doctor` correctly returned a non-zero status.

## Codex authentication requirement

The SDK runtime is installed, but live translation requires the user to authenticate Codex. Run the bundled or separately installed Codex CLI and choose ChatGPT sign-in, then verify:

```bash
uv run babelcodex --config config/example.toml doctor
```

`codex_authenticated` must be `true` before live Codex integration tests or PDF translation are attempted.

Authentication is intentionally not required by unit tests or GitHub Actions CI.

## CI baseline

GitHub Actions uses:

- Ubuntu hosted runner;
- Python 3.12;
- uv 0.12.10;
- `uv sync --locked --extra runtime --extra dev`;
- Ruff formatting/lint checks;
- pytest without live Codex usage or BabelDOC model warmup.

## Windows native validation

### Latest current-GUI working-tree run: 2026-09-10 (post-reconciliation confirmation)

The current Linux working tree (`dev`, `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca`, with uncommitted GUI and documentation changes) was synchronized one-way to `E:\Shiraishi\VSCode Workspace\Codex_Translator` and revalidated with the target Python 3.12.13 environment.

- PASS: dependency/lock checks, Ruff format/check, compileall, Python tests (`157 passed, 3 deselected`), runtime doctor, GUI Vitest (`19 passed`), GUI production build, Tauri `cargo check`, Tauri configuration/icon checks, current-source PyInstaller, frozen/target-triple/MSI-extracted sidecar smoke, bundle audit, NSIS/MSI generation, MSI extraction and package-level GUI launch.
- The previous GUI duplicate `mock-job-1` failure was fixed in Linux through idempotent `job_created` reconciliation and was not reproduced in the latest Windows revalidation. The reconciled GUI and subsequent Chinese UI regression coverage are `WINDOWS_PASS` for the validated working tree; the historical failure remains documented below.
- The previous PyInstaller environment block and `doctor()` installation-shape failure were resolved or not reproduced in the latest Windows revalidation. Their historical records remain unchanged and are not current blockers.
- Current status: `WINDOWS_VERIFICATION_PENDING` because packaged GUI interaction, clean-user/path-permission coverage, NVDA, DPI, Defender/SmartScreen, signing/SBOM, formal release audit and live Codex/PDF integration remain unexecuted.

Detailed commands, evidence, failure classification and follow-up actions are recorded in `docs/validation/windows.md` under the `2026-09-10` validation run.

Windows 原生验证已于 2026-09-08 在 E 盘 checkout 完成一轮。以下结果来自 Windows 11 x86-64（OS build 10.0.29648）：

- Python 3.12.13、uv 0.12.10；
- Node.js 24.19.0、npm 11.17.0；
- Rust 1.98.0、`stable-x86_64-pc-windows-msvc`；
- Visual Studio 2022 Build Tools 17.14.39，WebView2 runtime 已检测到；
- PyInstaller 6.22.2 用于本轮 sidecar 技术验证。

已完成：

1. `uv sync --locked --extra runtime --extra dev` 成功，解析并安装 95 个包；
2. uv lock --locked、Ruff format/check 通过；完整 uv run pytest -q 本次复核未全通过（1 failed，121 passed，3 deselected），失败项见下方 Windows 回归记录。
3. `npm ci` 成功（158 packages，0 vulnerabilities），GUI Vitest 14 tests 通过，`npm run build` 通过；
4. Windows 原生 `cargo check` 通过；
5. `babelcodex-service-x86_64-pc-windows-msvc.exe` 已构建并通过 JSONL `list_jobs` smoke test，sidecar 退出码为 0；
6. NSIS 与 MSI bundle 已生成。MSI 隔离解包后，包内 sidecar 与 target-triple sidecar 的 SHA-256 一致，并在工作目录为项目根、显式传入受控 `--config config/example.toml` 的条件下再次通过 JSONL smoke test；
7. 解包后的 `babelcodex-gui.exe` 已完成进程级启动检查，进程存活 8 秒后仅终止本次测试进程树；
8. `doctor` 通过，检测到 BabelDOC 0.6.4、openai-codex 0.147.0，当前 Codex 登录有效。

本轮产物哈希：

```text
76D8209E9558A47A06738A79E383233E10F23D692F055B247BDAB4599A76E38A  babelcodex-service-x86_64-pc-windows-msvc.exe  (188193952 bytes)
9C5C1D44C01C2F60560F829C7D5002DAD0FD4B4B816F64A49E72608AEB979E8F  BabelCodex_0.1.0_x64-setup.exe  (189692306 bytes)
00E555374A6D6C9A0457BFD16F2105D8BA5ACAE941E19783CFD11DA01CFC4F5A  BabelCodex_0.1.0_x64_en-US.msi  (189558784 bytes)
```

仍未完成：

- 文件选择器、输入/输出 allowlist、路径空格、反斜杠、非 ASCII 用户目录、窗口关闭和输出目录打开的完整 GUI 交互矩阵；
- 没有开发依赖、仓库目录或预置配置的干净 Windows 用户环境验收；本轮只完成 MSI 隔离解包、sidecar smoke 和 GUI 进程级启动；
- Defender/SmartScreen 行为、签名发布、SBOM，以及 Linux 目标机实际 smoke/发布验收；Linux `.deb`/AppImage 构建脚本和 bundle audit 已在 WSL/Linux 侧完成并通过 fixture/实际构建验证；
- 目标机运行矩阵和正式发布资源审计；`tauri.conf.json` 的 `bundle.icon` 已在 Linux 更新为 `["icons/icon.ico", "icons/icon.png"]`（新增已提交的 `gui/src-tauri/icons/icon.ico`，由 `scripts/generate_windows_icon.py` 生成），用于修复最新一轮 Windows 原生 MSI 构建中 `Couldn't find a .ico icon` 失败；Linux AppImage 构建已通过，但 MSI 重建、目标机图标显示和正式发布资源审计仍需 Windows 原生复验（`WINDOWS_VERIFICATION_PENDING`）。

原生 Windows 仍是必要条件，WSL/Linux 结果不能替代上述尚未完成的 GUI 交互验收：

WSL/Linux 的 `cargo check`、浏览器端 Vitest、Vite build、bundle audit 和 Linux `.deb`/AppImage 构建已通过，可作为先决检查，但不能替代原生 Windows packaged GUI smoke test 或目标 Linux 机器运行验证。Windows 桌面边界测试应继续使用 mock transport/fixture；真实 Codex 集成另行标记为付费或 ChatGPT-plan integration test。

## Non-Windows implementation boundary

在 Linux/WSL 可完成并已纳入当前代码门禁的内容包括：

- glossary CSV 导入/导出、全局与文档级合并、稳定版本 hash 和 bounded terminology prompt；
- UTF-8 文档 context sidecar 的标题/摘要提取、归一化、截断和稳定版本 hash；
- glossary/context 到 TranslationGateway cache key、worker `TranslatorSpec` 和 Codex thread prime 的接入；
- CLI glossary 管理、MCP/CLI 共用 Application Service、状态保存跨平台加固以及相关 contract/regression tests。
- 可配置的 Codex compact contract：官方 `Thread.compact()` 优先，失败时采用新 thread + prime + state rotation fallback；不依赖 Windows。
- GUI Glossary/Document Context 编辑页及其 scoped sidecar contract；不依赖 Windows，可在 Linux/WSL 通过 mock transport 和 JSONL contract tests 验证。

仍强制依赖 Windows 原生环境的内容包括：

- packaged GUI 文件选择、真实路径 allowlist、窗口关闭、取消、完成产物和输出目录交互矩阵；
- 干净 Windows 用户目录首次启动、WebView2/Defender/SmartScreen、非 ASCII 用户目录和路径空格/反斜杠验证；
- Windows 签名、SBOM、portable 发布验收、正式资源审计和目标用户环境 smoke；
- Windows 原生完整 pytest 已在最新重验证中通过（144 passed，3 deselected），其中 `tests/test_mcp.py::test_start_get_validate_and_cleanup_are_scoped` 与 `tests/test_cli.py::test_glossary_cli_import_and_list` 均通过；当前 source-level Python/GUI/Tauri/sidecar 检查为 `WINDOWS_PASS`，剩余 Windows 工作集中在 packaged/release 验收。

需要认证 Codex/目标集成环境、但不属于 Windows-only 的内容包括：

- Codex 客户端实际注册和 stdio MCP discovery；
- 真实 Codex thread resume/rotation、thread compact 和 ChatGPT-plan PDF 翻译；
- 长文档术语一致性与真实账户下的 throughput/usage benchmark。
- packaged sidecar 下的 GUI glossary/context 保存、干净用户目录和真实桌面编辑交互仍需目标平台验证。


## Windows native validation incidents and execution boundary

记录日期：2026-09-08。以下错误均已定位并处理，不代表当前通过项失败：

- 初次 WSL 到 E 盘同步使用相对路径排除参数，未可靠排除 node_modules 等生成目录；通过检查同步清单发现后，改用绝对排除路径重新同步，并保留 E 盘已有依赖、缓存、状态、日志和构建产物。
- 首次 Tauri bundle 构建因 icons/icon.ico 缺失而失败；随后补齐方形源图标并在 `tauri.conf.json` 声明 `icons/icon.png`，Linux AppImage 构建已验证，Windows 目标机图标显示和发布资源审计仍待完成。后续一轮 current-source NSIS/MSI 联合构建再次在 MSI 阶段因 `Couldn't find a .ico icon` 失败（旧 MSI 未作为证据）；Linux 已新增 `scripts/generate_windows_icon.py` 并提交按标准 Windows 尺寸生成的 `gui/src-tauri/icons/icon.ico`，`bundle.icon` 更新为 `["icons/icon.ico", "icons/icon.png"]`；该 MSI 修复为 `LINUX_VERIFIED` + `WINDOWS_VERIFICATION_PENDING`，需 Windows 原生重建复验，旧 MSI 不得作为当前证据。
- 首次 PyInstaller 直接以模块文件作为入口时出现 attempted relative import with no known parent package；改用临时的包级入口完成 sidecar 构建，临时入口未作为项目源文件保留。
- 首次使用的旧生成 bundle 包含过期或不匹配的 sidecar；删除范围仅限 gui/src-tauri/target/release/bundle 和 build/windows-msi-extract，随后重新构建并核对包内 sidecar 与 target-triple sidecar 哈希一致。
- 一次 sidecar smoke 从 binaries 或 MSI 解包目录启动且未提供配置，出现 FileNotFoundError，原因是相对路径寻找 config/example.toml；改在项目根工作目录启动，并显式传入受控 --config config/example.toml 后，目标 sidecar 和 MSI 解包 sidecar 的 list_jobs JSONL smoke 均退出码 0。
- 一次自动检查脚本错误使用 PowerShell 保留变量 args，导致 uv 只打印帮助；改为显式调用后，uv lock --locked、Ruff 和 doctor 均通过，但完整 pytest 后续发现 Windows 取消测试回归，详见下方复核记录。

本轮未执行及原因：

- 未执行完整 GUI 文件选择、allowlist、路径空格/反斜杠/非 ASCII 路径、进度、取消、完成产物、输出目录和窗口关闭交互；本轮只具备自动化前端测试、sidecar 协议 smoke 和解包 GUI 进程级启动证据，尚未运行真实桌面交互矩阵。
- 未执行无开发依赖、无仓库目录、无预置配置的干净 Windows 用户环境验收；现有 MSI 隔离解包仍借用了项目根配置，不能证明干净用户首次启动行为。
- 未执行 Defender/SmartScreen、签名、SBOM、正式 portable 发布和发布资源审计；本轮产物为 unsigned 开发验证包，且尚未进入正式发布附件流程。
- 未执行目标 Linux 机器 smoke；WSL/Linux 构建环境只能验证构建和静态先决条件，不能代替目标发行版运行验证。
- 文档和 Linux bundle 脚本同步后未重复构建 Windows NSIS/MSI；本次新增内容不改变 Windows GUI、Rust 或 sidecar 源代码，因此采用现有 bundle 哈希复核、包内 sidecar smoke 和 cargo check 复核作为边界明确的回归验证。
- 未执行真实 Codex PDF 翻译集成；项目测试约束禁止单元测试消耗付费或 ChatGPT-plan 用量，本轮仅验证 doctor 登录状态和 mock/协议路径。

证据文件：build/windows-tauri-final2.log、build/windows-artifacts.sha256，以及 compatibility.md 中列出的 sidecar、NSIS 和 MSI SHA-256。


## Windows validation rerun and regression status

追加复核日期：2026-09-08。以下结果来自本次 E 盘 Windows checkout 复核：

- 通过：uv lock --locked、Ruff format/check、doctor、GUI Vitest（14 tests）、Vite build、Windows cargo check。
- 通过：Windows target-triple sidecar 与 MSI 解包 sidecar 在项目根工作目录、显式传入受控 --config config/example.toml 后执行 list_jobs JSONL smoke，均退出码 0；解包 GUI 进程级启动 8 秒后已停止。
- 通过：现有 sidecar、NSIS 和 MSI 产物哈希保持与 windows-artifacts.sha256 一致，三项产物均为 NotSigned。
- 待复验：完整 uv run pytest -q 两次复核曾失败于 tests/test_mcp.py::test_cancel_uses_the_active_job_handle；一次在 2 秒等待后仍为 RUNNING，一次因 state.py 的 os.replace 返回 PermissionError: [WinError 5] 而变为 FAILED。
- 处置：已增加 StateStore 单实例保存锁、Windows 短暂 PermissionError 的有限退避重试，并将 MCP 取消回归测试改为最长 10 秒的 terminal 状态轮询；Windows 原生完整测试仍需重新执行确认。
- Linux 侧历史复验：上述修复后的完整 uv run pytest -q 已通过（123 passed，3 deselected），Ruff、compileall 和相关协议测试均通过；本轮新增 glossary/context/thread state 后的最终结果见下方 Current Linux/WSL implementation verification。
- 结论：Windows 原生构建、GUI、sidecar 和打包 smoke 仍通过；Windows 原生完整 pytest 仍需重新执行后，才能将跨平台 Python 质量门禁标记为稳定通过。

## Current Linux/WSL implementation verification

本轮非 Windows 开发完成后，在 2026-09-09 的 Linux/WSL 工作区复验：

- `uv run pytest -q`：150 passed，3 deselected；
- GUI `npm test -- --run`：17 passed；`npm run build`：通过；
- Ruff format/check、Python compileall：通过；
- `npm audit --omit=dev`：0 vulnerabilities；
- CLI/MCP/sidecar `doctor` smoke：在 Linux 本地未登录 Codex 状态下按预期返回未认证信息，不影响 Linux 门禁；
- StateStore 读路径加固已完成并经 Windows 原生复验确认为 `WINDOWS_PASS`：`load`/`load_by_job_id`/`list_jobs` 现通过 `_read_state_json()` 对瞬时 `PermissionError`（Windows 并发 `os.replace` 下的 sharing violation）执行与写侧对称的有界指数退避；回归测试覆盖瞬时恢复、持续失败抛出和有界重试预算；Windows 复验全量 pytest 为 `150 passed, 3 deselected`，此前记录的瞬时读失败未复现，间歇性 FAIL 观察已作为历史记录移除；
- glossary CLI `list` smoke、MCP stdio smoke、glossary/context contract tests 和 scoped sidecar editor API tests：通过；
- PDF metadata/opening-page context adapter、thread identity persistence、mocked Codex `thread_resume`/compact contract 和 GUI glossary/context editor behavior：通过；
- GUI glossary/context 编辑器已通过 sidecar scoped API 读写 global/document glossary、enabled/notes、文档 stem 校验和 UTF-8 context sidecar；
- Windows 复验后的 Linux follow-up 已完成：TOML Windows 路径 fixture 使用安全字符串序列化，MCP job cleanup 同时检查 active future、处理 Future 完成竞态并对瞬时文件锁执行有限退避重试；Linux 全量验证通过，且最新 Windows 重验证已确认 CLI Windows-path fixture、MCP cleanup 和完整 Python 门禁均为 `WINDOWS_PASS`；
- Windows current-source packaging 后的 MSI `.ico` Linux follow-up 已完成并经 Windows 原生复验确认为 `WINDOWS_PASS`：`scripts/generate_windows_icon.py`、已提交的 `gui/src-tauri/icons/icon.ico`（16/24/32/48/64/128/256 px）和 `tauri.conf.json` 的 `["icons/icon.ico", "icons/icon.png"]` 更新；Linux 复验为 `147 passed, 3 deselected`、Ruff/lint/format 通过、GUI 17 tests 和 Vite build 通过、`.ico` 七尺寸与配置解析有效；最新 Windows 复验中当前源码 NSIS（`D653629B7F40AAA30311107A17956E12976DF39B42BEF9F5391E859B489DB28D`）与 MSI（`4E885B1E35A3C566D9257A701608BA383B2E5577C40A30A6E93A1578B02F57A4`，195,715,072 bytes）构建均已通过（首次 MSI 失败仅为 E 盘副本同步状态问题，补同步核对哈希后通过；旧 MSI 未作为证据）；packaged GUI 交互与 release 验收仍为 `NOT RUN`，整体保持 `WINDOWS_VERIFICATION_PENDING`；
- 未生成或提交 glossary/context 用户文件；配置目录仅在本地运行时创建为空目录。

上述结果不能替代 Windows 原生 packaged GUI 交互、干净用户验收、Defender/SmartScreen、签名/SBOM/release 审计、npm 全量 advisories 处置、Codex 客户端实际注册、真实 Codex thread resume/rotation 行为、packaged/clean-profile GUI 编辑交互、目标 Linux 机器 smoke 或真实 Codex/PDF 集成。
## Bundle-audit URL false-positive follow-up (2026-09-09)

- Windows 在当前源码复验中把 `scripts/check_gui_bundle.py` 记为 `WINDOWS_FAIL`：生成的 JS/CSS 里的普通 `https://` 字符串被裸 `[A-Za-z]:[\\/]` 误判为开发机绝对路径；该项是验证脚本缺陷，不是产物路径泄漏证据。
- Linux 已修复并纳入门禁：`contains_development_machine_absolute_path()` 先剥离 `scheme://authority` 再匹配并加负向后顾；`file:///home/...` 与 `file:///C:/...` 仍可检出；`tests/test_check_gui_bundle.py` 7 个回归测试覆盖 URL 通过、真路径检出、缺 sidecar 与禁入文件行为；用真实 Vite 产物复跑 audit 通过。
- Linux 复验：`uv run pytest -q` 为 `157 passed, 3 deselected`，Ruff lint/format、compileall、GUI 17 tests 通过。
- 该修复为 `LINUX_VERIFIED` + `WINDOWS_VERIFICATION_PENDING`：audit 项仅可在 Windows 用修复后脚本重跑通过后才可从 `WINDOWS_FAIL` 转为 `WINDOWS_PASS`，不得提前标记。
## Latest Windows validation reconciliation (2026-09-09)

- Current WSL `dev` working tree HEAD `7ba4ddf` was synchronized one-way to E: and revalidated with the project-managed Python 3.12.13 environment. Dependency/lock checks, Ruff, compileall, `150 passed, 3 deselected`, doctor, GUI 17 tests/build, Windows Cargo, PyInstaller, frozen/target-triple sidecar smoke, NSIS/MSI generation, MSI extraction, extracted sidecar smoke and package-level GUI launch all passed.
- The current bundle audit is a real `FAIL`: `scripts/check_gui_bundle.py` flags normal `https://` strings in generated JS/CSS because its absolute-path regex matches the `s://` suffix. This is recorded as a validation-script defect, not as evidence of a product path leak; no code was changed during the Windows run.
- Current artifacts: NSIS `259D35315741EF3DA4D7318C1DEF36016031524133601108EBE580E55E608FD3` (195,746,309 bytes) and MSI `8307FD99E183E0B8074E1EC863B5CF3EEB12C69BAB9C839D647502624B8A3DE7` (195,715,072 bytes), both unsigned. MSI-contained sidecar hash matched the target-triple sidecar.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`; interactive/clean-user GUI, cancellation/reconnection/path-permission matrix, Defender/SmartScreen, signing/SBOM/release audit and live Codex/PDF integration remain `NOT RUN`.
- Linux follow-up: narrow/fix the bundle-audit regex with regression coverage for URL schemes, then rerun the audit. Do not treat the previous audit `PASS` entries as overriding this newer current-source result.

## Latest Windows validation reconciliation (2026-09-10)

- The latest WSL `dev` working tree (HEAD `8f6ee91`, including the uncommitted current GUI redesign and documentation changes) was synchronized one-way to E: and revalidated on Windows 11 with project Python 3.12.13, `uv 0.12.10`, Node.js 24.19.0, npm 11.17.0 and Rust/cargo 1.98.0.
- Dependency/lock checks, Ruff, compileall, Python tests (`157 passed, 3 deselected`), doctor, GUI production build, focused store tests, Cargo, Tauri config/icon checks, fresh PyInstaller sidecar, frozen/target-triple/MSI-extracted sidecar smoke, bundle audit, NSIS/MSI generation, MSI extraction and package-level GUI process launches passed.
- Full GUI Vitest is `WINDOWS_FAIL`: 15/17 passed; two App tests found duplicate `mock-job-1` rows after mock job/event reconciliation. This is a current GUI project-code issue and needs Linux-side correction and cross-platform rerun.
- Fresh frozen/target/package sidecar SHA-256 is `8E899E6833943E1BF201313E8F3EF25BEA0F8F95C69B4A9709AAF679F307B668`. NSIS is `CB6476F09664D5B6F8AD4E188FD48E733B069FA13D0D65A006768353AB600708` (195,748,979 bytes); MSI is `AF0F910308C1BC412484417FF6EFD929C1EBA49040FEC0DFDD76812C139552E8` (195,710,976 bytes). All are unsigned development artifacts.
- Packaged GUI interaction, clean-user/path-permission matrix, Defender/SmartScreen, signing/SBOM/release audit and live Codex/PDF integration remain `NOT RUN`; target Linux machine smoke is `NOT APPLICABLE`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Linux reconciliation after Windows validation (2026-09-10)

- The Windows duplicate `mock-job-1` failure was classified as a shared GUI state-reconciliation issue: `JobStore.applyEvent()` appended a `job_created` event even when `list_jobs` had already supplied the same `job_id`.
- Linux fixed the issue by making `job_created` application idempotent. Existing jobs are merged in place without losing richer state, while unseen jobs are inserted once. A regression test covers replay after `list_jobs` and verifies that only one job remains.
- Linux also corrected the App test/UI accessibility mismatch by exposing `Job details` as the actual heading and retaining the job ID as separate metadata.
- Linux verification after these fixes: GUI Vitest `3 files, 18 tests passed`; `npm run build` passed; `uv run pytest -q --tb=short` reported `157 passed, 3 deselected`; Ruff format/check, compileall and `git diff --check` passed.
- The GUI fix was first `LINUX_VERIFIED` and has since reached `WINDOWS_PASS` in the latest Windows revalidation. The historical Windows `doctor()` installation-shape failure and current-source PyInstaller block were resolved or not reproduced in subsequent runs; packaged desktop interaction, clean-user, NVDA, DPI, signing/SBOM and release checks remain `WINDOWS_VERIFICATION_PENDING` or `NOT RUN` exactly as recorded in `docs/validation/windows.md`.

## Latest Windows validation reconciliation (2026-09-10, GUI fix revalidation)

- The latest WSL `dev` working tree at HEAD `8f6ee91` (including uncommitted GUI reconciliation changes) was synchronized one-way to E: and revalidated on Windows 11 with project Python 3.12.13, `uv 0.12.10`, Node.js 24.19.0, npm 11.17.0 and Rust/cargo 1.98.0.
- Dependency/lock checks, Ruff, compileall, Python tests (`157 passed, 3 deselected`), doctor, GUI tests (`18 passed`), GUI build, Cargo, Tauri config/icon checks, fresh PyInstaller sidecar, frozen/target-triple/MSI-extracted sidecar smoke, bundle audit, NSIS/MSI generation and package-level GUI launches all passed.
- The prior GUI duplicate `mock-job-1` failure was not reproduced after the synchronized Linux working-tree reconciliation; the current GUI source and its 18-test suite pass on Windows.
- Fresh sidecar SHA-256 is `CDE9A9DBDD4F47671EBE576BB2DCBED5DAF19E88615E56AC344D8A6CC7F0956A`. NSIS is `14975F49B62A070D97B1649460BCD87955559541209BD259EFDD8F64C9A9AC27` (195,747,786 bytes); MSI is `C8CD3C61AF7E97890B97B7FD17C0D000B50BC34318B5D1E0B6D5BE315D905275` (195,710,976 bytes). All are unsigned development artifacts.
- Packaged GUI interaction, clean-user/path-permission matrix, Defender/SmartScreen, signing/SBOM/release audit and live Codex/PDF integration remain `NOT RUN`; target Linux machine smoke is `NOT APPLICABLE`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-10, post-reconciliation confirmation)

- The latest WSL `dev` working tree at HEAD `8f6ee91` (including uncommitted GUI, architecture and documentation changes) was synchronized one-way to E: and revalidated on Windows 11 with project Python 3.12.13, `uv 0.12.10`, Node.js 24.19.0, npm 11.17.0 and Rust/cargo 1.98.0.
- Dependency/lock checks, Ruff, compileall, Python tests (`157 passed, 3 deselected`), doctor, GUI tests (`18 passed`), GUI build, Cargo, Tauri config/icon checks, fresh PyInstaller sidecar, frozen/target-triple/MSI-extracted sidecar smoke, bundle audit, NSIS/MSI generation and package-level GUI launches all passed.
- The earlier GUI duplicate `mock-job-1` failure remains historical and was not reproduced after the synchronized Linux reconciliation changes.
- Fresh sidecar SHA-256 is `CDE9A9DBDD4F47671EBE576BB2DCBED5DAF19E88615E56AC344D8A6CC7F0956A`. NSIS is `14975F49B62A070D97B1649460BCD87955559541209BD259EFDD8F64C9A9AC27` (195,747,786 bytes); MSI is `C8CD3C61AF7E97890B97B7FD17C0D000B50BC34318B5D1E0B6D5BE315D905275` (195,710,976 bytes). All are unsigned development artifacts.
- Packaged GUI interaction, clean-user/path-permission matrix, Defender/SmartScreen, signing/SBOM/release audit and live Codex/PDF integration remain `NOT RUN`; target Linux machine smoke is `NOT APPLICABLE`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-10, current GUI confirmation)

- The latest WSL `dev` working tree at HEAD `8f6ee91` (including uncommitted GUI, architecture and documentation changes) was synchronized one-way to E: and revalidated on Windows 11 with project Python 3.12.13, `uv 0.12.10`, Node.js 24.19.0, npm 11.17.0 and Rust/cargo 1.98.0.
- Dependency/lock checks, Ruff, compileall, Python tests (`157 passed, 3 deselected`), doctor, GUI tests (`19 passed`), GUI build, Cargo, Tauri config/icon checks, fresh PyInstaller sidecar, frozen/target-triple/MSI-extracted sidecar smoke, bundle audit, NSIS/MSI generation and package-level GUI launches all passed.
- The earlier GUI duplicate `mock-job-1` issue remains historical and was not reproduced after the synchronized Linux reconciliation changes; the current GUI suite passes 19/19.
- Fresh sidecar SHA-256 is `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`. NSIS is `9C9332AD3FE09FAFFB71AAE35F157D1333DEAC6F57E369BA052B3511DA4B4F1B` (195,743,723 bytes); MSI is `D0C5D8B87EB9BA7D5F21F66445C46BD827F0A0558E28F1416573ECE848B7CC23` (195,715,072 bytes). All are unsigned development artifacts.
- Packaged GUI interaction, clean-user/path-permission matrix, Defender/SmartScreen, signing/SBOM/release audit and live Codex/PDF integration remain `NOT RUN`; target Linux machine smoke is `NOT APPLICABLE`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-10, current UI revalidation)

- The latest WSL `dev` working tree at HEAD `8f6ee91` (including uncommitted GUI, architecture and documentation changes) was synchronized one-way to E: and revalidated on Windows 11 with project Python 3.12.13, `uv 0.12.10`, Node.js 24.19.0, npm 11.17.0 and Rust/cargo 1.98.0.
- Dependency/lock checks, Ruff, compileall, Python tests (`157 passed, 3 deselected`), doctor, GUI tests (`19 passed`), GUI build, Cargo, Tauri config/icon checks, fresh PyInstaller sidecar, frozen/target-triple/MSI-extracted sidecar smoke, bundle audit, NSIS/MSI generation and package-level GUI launches all passed.
- The current UI change is verified at automated/build/process level only; packaged Chinese rendering, keyboard navigation, DPI and NVDA remain `NOT RUN`.
- Fresh sidecar SHA-256 is `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`. NSIS is `9C9332AD3FE09FAFFB71AAE35F157D1333DEAC6F57E369BA052B3511DA4B4F1B` (195,743,723 bytes); MSI is `D0C5D8B87EB9BA7D5F21F66445C46BD827F0A0558E28F1416573ECE848B7CC23` (195,715,072 bytes). All are unsigned development artifacts.
- Packaged GUI interaction, clean-user/path-permission/accessibility matrix, Defender/SmartScreen, signing/SBOM/release audit and live Codex/PDF integration remain `NOT RUN`; target Linux machine smoke is `NOT APPLICABLE`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Upgrade policy

Changing Python, BabelDOC, openai-codex or uv requires:

1. regenerating `uv.lock`;
2. running all local quality gates;
3. checking `doctor` output;
4. re-running BabelDOC warmup on a clean cache when practical;
5. updating this compatibility document;
6. validating at least one mock PDF fixture before enabling the new baseline.

## Latest Windows validation reconciliation (2026-09-11, current PDF QA/release tree)

- WSL `dev` HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` was synchronized one-way to E: after correcting an initially incomplete filtered copy; the current PDF-QA/release files matched by hash. The only pre-existing Linux source change was a mode-only change to `scripts/build_linux_gui_bundle.sh`.
- Windows validation passed with Python `196 passed, 5 deselected`, mock PDF integration `5 passed`, GUI `19 passed`, Ruff/compileall, doctor, Cargo, fresh PyInstaller, direct/target-triple sidecar JSONL, corrected GUI bundle audit, Tauri NSIS/MSI generation and MSI extraction. The fresh sidecar SHA-256 is `DD99EFC90C3960A27025CC5913BE0835CAA521D8DF332678D7A57D2DEE1496E6` (194,430,767 bytes); GUI is `B0071FA5...` (4,597,248 bytes); NSIS is `07BA3593...` (195,775,955 bytes); MSI is `096BC48D...` (195,743,744 bytes).
- The first bundle audit and first MSI-extracted sidecar attempt are recorded as validation-input `FAIL` results in `docs/validation/windows.md`; corrected reruns passed. Packaged interaction, clean-user, accessibility/DPI, signing/SBOM/release security and live Codex/PDF remain `NOT RUN`; overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-12, latest Linux state revalidation)

- WSL Ubuntu `dev` HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` was synchronized one-way to the E: disposable workspace after comparing and preserving E: local dependencies, caches, state, logs and user data; 68 files copied, 0 failed, 17 extras preserved, and 9 changed/untracked code/test hashes matched.
- Current automated validation passed: `200 passed, 5 deselected`; GUI `22 passed`; mock PDF integration `5 passed`; QA CLI positive/tamper assertions; current PyInstaller sidecar; protocol-v1 and target-triple handshakes; corrected fresh/stale `--source-tree` audit; NSIS/MSI build; and release GUI 8-second process smoke. Sidecar SHA-256 is `CBAD9089F3E952A62CE5E1A666340A8B0CBF1FD40354A789A5C56A1FBEEA7841` (194,439,871 bytes); GUI is `452E86E9EC1EC7CB0F384854C03ABDDFE32899AEFCF29FF4A934E972B8B0274F`; NSIS is `AE89EB2F737D755C9634AA182C1CBDBB2B488CF967E56EB30325F6B6E85477E1`; MSI is `DA6380426405FF7F07E22EB22BE8C1C689CC41FB1A7D5EF320B23A8C1D442AD3`.
- One `FAIL` remains: QA assertions passed, but the temporary harness could not immediately remove `logs\cbpdf.log` because of `WinError 32`. MSI administrative extraction is `BLOCKED` after a 90-second no-output timeout with no payload; native GUI and stale-GUI error observation are also `BLOCKED` because the trusted `sky` service is unavailable. Clean-user, full WVQ-007 semantics, release security, dependency remediation and live Codex/PDF remain `NOT RUN`; overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-12, current dirty-tree rerun)

- WSL `dev` HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` was re-synchronized one-way to E: with generated `gui/dist` and other dependency/cache/state directories excluded; 68 files copied, 0 failed, and 10 changed/untracked code/test hashes matched.
- Windows automation passed `200 passed, 5 deselected`, GUI `22 passed`, mock PDF integration `5 passed`, QA CLI/tamper assertions, current PyInstaller sidecar, protocol-v1/target-triple handshake, fresh/stale `--source-tree` audit, NSIS/MSI build and release GUI process smoke. Fresh sidecar SHA-256 is `232198B0EF1A65C0D633F7423D6CE0C66DE7794C65389767EF6E6C4D441983F4` (194,438,039 bytes); GUI is `78DA33D072FC911CE86946E021B563BC8AF02481696477F4ADF2CC992D644B8E`; NSIS is `8662431EF3FB8FD73876EF3AE3461C17909BDE2044C4F7406965FC135A40FB5A`; MSI is `56B0100F2A515B4CB4E55343FB8B224917F6587C3EB3C7D55BA2761B33677C19`.
- Temporary QA fixture cleanup again failed with Windows `WinError 32`. Current MSI administrative extraction is `BLOCKED` because one invocation hung without target/log output and a direct retry returned 0 without extracted payload evidence. Native GUI interaction and stale-GUI error presentation remain `BLOCKED` because the trusted `sky` service is unavailable. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-11, current dirty tree and ADR-029)

- WSL `dev` HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` plus its uncommitted sidecar-handshake, GUI protocol, freshness-audit and mock-test resource-scope changes was synchronized one-way to E: with 71 files copied and zero failures; changed-file hashes matched.
- Windows passed Python `200 passed, 5 deselected`, GUI `22 passed`, mock PDF integration `5 passed`, QA CLI fixture/tamper detection, fresh PyInstaller, `get_server_info` handshake, target-triple sidecar, `--source-tree` fresh/stale audit, NSIS/MSI build and MSI extraction. Fresh sidecar SHA-256 is `701D83EF04689C87BFAFE93FB6A22D44A15903CA46843C5E9C431E40384BD97C` (194,438,558 bytes); NSIS is `6BBBDAE445BB514A1A2DBE244B26F96F9F0D5936A7BA4B53AFAE1C242AF4A77F`; MSI is `6EBEC6E108667A3D8EC7D43DC1F0C4B17E5EB2F74BDC8966B5E315B054E436F1`.
- A Windows `WinError 32` occurred while cleaning the temporary fixture after QA assertions; native GUI interaction and packaged stale-GUI error observation were blocked because the computer-use trusted RPC service was unavailable. These remain explicit `FAIL`/`BLOCKED` findings; overall status remains `WINDOWS_VERIFICATION_PENDING`.
## Latest Linux reconciliation after the 2026-09-11 dirty-tree result

- The validation input already included the `tests/test_e2e_mock.py` resource-scope change (PyMuPDF context managers). The QA fixture/tamper assertions passed, but the harness-level temporary fixture cleanup still failed with `PermissionError: [WinError 32]`. Linux therefore corrected the earlier attribution: the test-scope change is test hygiene only and is neither the cause nor the fix of the Windows cleanup failure.
- Linux static review of the QA boundary found no production-code handle leak: `pdf_sanity.py`, `text_checks.py` and `layout_checks.py` close every PyMuPDF document via `try/finally` or `with`. The remaining `WinError 32` candidates live in the Windows validation harness lifecycle (not-yet-exited subprocess, Defender/antivirus scan, or a `uv run` wrapper holding the fixture handle at deletion time).
- The `WinError 32` remains a historical `FAIL` tracked under `WVQ-007` for a native Windows re-run with the current source; it must not be converted to `PASS` by Linux-only changes, and no cleanup assertion was weakened. Native GUI interaction and the packaged stale-GUI observation remain `BLOCKED` (computer-use trusted RPC unavailable), and overall status stays `WINDOWS_VERIFICATION_PENDING`.

## Latest Linux follow-up after the 2026-09-12 log-handle observation

- The 2026-09-12 rerun shifted the locked artifact from the fixture PDF to the QA CLI's own `logs\cbpdf.log` while keeping the identical failure class; Linux attributed both to the short-lived CLI command's file-handle lifecycle and implemented a hardening: `main()` now closes and detaches every root-logger `FileHandler` in a `finally` at command completion, with a regression test (`test_cli_releases_log_file_handlers_at_exit`) pinning detachment and stream closure. Linux gates after the change: `201 passed, 5 deselected`, Ruff/format, GUI Vitest and `tsc --noEmit` all clean.
- The hardening is a handle-exposure mitigation, not a claimed Windows fix. The `WinError 32` stays a historical `FAIL` under `WVQ-007` for native re-run; native GUI and stale-GUI observation remain `BLOCKED`, and overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-12, CLI/QA-change native revalidation)

- The revalidation input included the CLI log-handler release hardening; Windows natively retested the previously failing QA harness temporary cleanup and it **passed without the previous `WinError 32`** (`201 passed, 5 deselected`, GUI `22 passed`, mock PDF `5 passed`, tamper detection, fresh PyInstaller, protocol-v1/target-triple handshakes, fresh bundle audit, NSIS/MSI build, release GUI smoke — no `FAIL` this round).
- Windows scoped the result explicitly: only the QA-harness cleanup path is cleared; the full `WVQ-007` work-dir/lock/retry/cancel/reconnect matrix remains `NOT RUN` and `WINDOWS_VERIFICATION_PENDING`. The `WVQ-009` stale bundle negative audit obtained native PASS evidence (older sidecar rejected with `sidecar predates newer Python sources`), but `WVQ-009` stays `WINDOWS_VERIFICATION_PENDING` because the packaged stale-GUI error observation and native GUI interaction remain `BLOCKED` (trusted RPC `sky` unavailable); MSI administrative extraction is still `BLOCKED` (90-second timeout without log/payload); clean-user, `WVQ-005` release security and live Codex/PDF remain `NOT RUN`.
- No further Linux code change was made this round: the remaining failure owners are Windows-environment observations, and speculative Linux-only changes would not be evidence for them. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-12, MSI revalidation)

- The previously `BLOCKED` MSI administrative extraction is now closed with full native evidence: extraction with the documented quoted `/a`, `TARGETDIR`, `/L*v` arguments returned exit 0, the extracted sidecar SHA-256 exactly matched the fresh build (`B892AD80...E4EB5`), the extracted sidecar v1 handshake/shutdown exited 0, and the extracted GUI stayed alive for 8 seconds. This run had **no `FAIL`** (`PASS 21 / FAIL 0 / BLOCKED 2 / NOT RUN 5 / NOT APPLICABLE 1`).
- The QA fixture temporary cleanup passed for a second consecutive round with the CLI handler-release hardening, and the stale bundle negative audit again rejected the preserved older sidecar.
- Remaining gaps are unchanged in ownership: native GUI automation (`WVQ-001`–`WVQ-004`, stale-GUI part of `WVQ-009`) and the full `WVQ-007` lifecycle matrix, clean-user session, `WVQ-005` release security and live Codex/PDF stay `NOT RUN`/`BLOCKED` pending the Windows-native environment. All `WVQ-*` items remain `WINDOWS_VERIFICATION_PENDING`; no Linux code change was made this round because none of the remaining gaps can be advanced by Linux-only edits. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-12, current dirty tree fresh package rerun)

- WSL `dev` HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` was synchronized one-way to E: with 67 files copied, zero failures, 17 local extras preserved, and 24 selected control/changed-file SHA-256 matches. Python `201 passed, 5 deselected`, GUI `22 passed`, mock PDF integration `5 passed`, current PyInstaller, protocol-v1/target-triple handshakes, fresh/stale bundle audit, NSIS/MSI, MSI administrative extraction, extracted sidecar and extracted GUI process smoke all passed.
- QA/tamper detection passed and the temporary QA directory cleaned successfully after the current CLI handler-release path; this clears only that harness path, not the full `WVQ-007` Windows lifecycle matrix. Fresh sidecar SHA-256 is `29D0A257C35835440831EAF13AD4A4F788C490A52CBB8521FD3FC76B0BD02AC4`; NSIS and MSI are unsigned development artifacts.
- Native GUI and packaged stale-GUI observation remain `BLOCKED` because the trusted desktop automation surface failed with `helper_unknown_error: setup refresh had errors`. Clean-user, WVQ-007 full lifecycle, WVQ-005 release security and live Codex/PDF remain `NOT RUN`; overall status remains `WINDOWS_VERIFICATION_PENDING`.

## Latest Windows validation reconciliation (2026-09-12, manual GUI handoff)

The automated native GUI and stale-GUI observations remain `BLOCKED` because the trusted desktop surface was unavailable. A human-validation pack is now prepared under `E:\Shiraishi\VSCode Workspace\Codex_Translator\build\manual-gui-validation-20260912-152358`, with a current fresh pair and a current-GUI/older-sidecar stale pair. The manual checks are `NOT RUN` pending screenshots and exact observations; this handoff is not Windows acceptance evidence. No business-code change was made.

## Latest Windows validation reconciliation (2026-09-12, manual GUI results)

The human operator completed the GUI handoff. Fresh/stale launch and basic window operations passed; page navigation exposed a Settings/layout jump, native PDF picker selection/load passed, native PDF drag-and-drop failed, and stale-GUI error presentation failed because the stale pair opened without a reported actionable compatibility error. Keyboard, NVDA and DPI/scaling were explicitly skipped and remain `NOT RUN`. Overall status remains `WINDOWS_VERIFICATION_PENDING`; no business-code change was made.

## Latest Windows validation reconciliation (2026-09-12, screenshot evidence update)

Three operator screenshots from the stale-GUI pair were preserved in the E: validation pack. They show generic `Starting sidecar`/`Sidecar unavailable` notices, incomplete lower-left notice visibility on New Translation, shifted right-side status placement and complete lower-left notice visibility on Settings, plus unchanged drop-zone appearance before/after PDF drag. This confirms the previously reported layout and drag/drop failures; stale-GUI error visibility is present but remains a `FAIL` for actionable compatibility guidance. No business-code change was made.

## Latest Windows validation reconciliation (2026-09-13, current worker/package tree)

- WSL `dev` HEAD `14b4856bf37cf06674b6319da8f0ab6451728348` was synchronized one-way to E: with 87 controlled files copied and zero failures; 40 selected source/control hashes matched, while E: dependencies, caches, state, logs, user content and generated assets were preserved. The Linux working tree retained only the pre-existing mode-only `scripts/build_linux_gui_bundle.sh` change.
- Windows passed locked dependency setup, Ruff/compileall, documentation-inventory CLI, GUI tests (`22`), focused job-store tests (`9`), GUI/Tauri build checks, mock PDF integration (`5`), QA/tamper cleanup, current sidecar protocol-v1 and target-triple handshakes, fresh/stale source-tree audit, NSIS/MSI build and extraction parity, and current/extracted GUI process smoke. Fresh sidecar SHA-256 is `2416E557906C9DB4218D80CFB535D57762553C0C5B66A7B71ABE5F080C3C4ABF` (194,468,829 bytes); NSIS is `896EBFD1660A44DA672A92233DFCA06A61E1879343464D2F93AAA5D89B97765E` (195,799,129 bytes); MSI is `42B5CFAB2ED7A0E58108A1D9A900477950DF55098D8E3683A6360A9DF7F7E9F6` (195,768,320 bytes). All packages remain unsigned development artifacts.
- Two current failures require Linux follow-up: the Windows documentation-inventory test expects POSIX separators (`220 passed, 1 failed, 5 deselected` overall), and a valid frozen worker request fails with `BABELDOC_RUNTIME_ERROR`/exit 3 because `bitstring.bitstore_bitarray` is absent from the frozen runtime although normal Python imports it. No Linux/spec change was made during this validation.
- Native GUI/stale-GUI remain `BLOCKED` by unavailable computer-use desktop initialization; clean-user, full WVQ-007, WVQ-005 release security, dependency remediation and live Codex/PDF remain `NOT RUN`; target Linux smoke is `NOT APPLICABLE`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.
- Required next steps are to make the inventory assertion platform-independent, investigate and regression-test PyInstaller collection for `bitstring.bitstore_bitarray`, then rerun the frozen worker/package gates on Windows. Native GUI/accessibility/path, lifecycle, clean-user, release-security and authorized live-integration acceptance remain separate Windows tasks.

## Linux follow-up after the 2026-09-13 Windows validation

- The documentation-inventory portability issue is fixed by explicit `/` normalization of managed relative paths; a regression simulates Windows-style separators, and the Linux documentation gate now passes.
- The frozen sidecar spec now collects all `bitstring` submodules, the `tiktoken` package and its `tiktoken_ext` plugin, and no longer excludes standard-library modules needed by BabelDOC's dynamic runtime path. Linux rebuilt the sidecar successfully and a frozen mock worker request completed with exit 0 and mono/dual PDF artifacts.
- This is Linux evidence only. The original Windows frozen-worker failure remains a historical `FAIL` until the repaired source is rebuilt and rerun natively. Windows frozen-worker/package, target-triple, bundle, GUI, lifecycle, release-security and live-integration items remain `WINDOWS_VERIFICATION_PENDING`.
