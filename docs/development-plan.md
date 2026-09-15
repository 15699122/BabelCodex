# BabelCodex Development Plan

## Current handoff baseline (2026-09-15)

- 当前最新 Windows 验证源为 `dev` / commit `8f046ef12ab9a9e8d82c260673a303892202ec21`；该提交已推送并与 `origin/dev` 同步。最新 Windows 记录追加到 `docs/validation/windows.md`，当前工作树中的验证文档变更尚未作为新的源代码基线提交。
- Tauri WDIO 基础设施、确定性 mock contract、E2E-only allowlist、flavor capability 内联化和 7 项 capability regression Guard 已在 Linux 完成验证；GUI Vitest、Vite build、Ruff、docs inventory、Cargo default/mcp-dev/e2e checks 均通过。
- `WVQ-018` 的 inline capability 配置和上一轮 `WVQ-017` 自动化 native scope 曾有 Windows PASS，但对当前 `8f046ef` 的回归运行在 WDIO 加载阶段因 `uv_os_get_passwd ... ENOMEM` 失败；因此当前提交不得沿用上一轮 native PASS，必须在修复 Windows 运行环境后重新执行。
- Windows 结果必须写入 `docs/validation/windows.md`；不得把 Linux native 15/15 或直接 sidecar JSONL probe 记录为 Windows GUI 原生 PASS。当前源状态、失败恢复配置和命令见该文档的 “Next Windows handoff after current-head validation (baseline `8f046ef`)”。

## Next Windows validation scope after WVQ-018/WVQ-017 (2026-09-15)

本轮 Windows 已完成 flavor capability 与自动化 native E2E 验收；下一轮只处理尚未取得充分 Windows 证据的项目。总体状态继续为 `WINDOWS_VERIFICATION_PENDING`，不得因为 `WVQ-017`/`WVQ-018` 通过而提前宣称 GUI、安装器或发布验收完成。

### Windows 执行顺序

1. **同步与工具链快照**：从 WSL 的 `8f046ef` 单向同步到 disposable Windows workspace；记录 branch、commit、工作树状态、同步日期、Windows build、WebView2、Node/npm、Python/uv、Rust/MSVC 版本。保留 Windows 本地依赖、缓存和 sidecar，禁止把它们反向同步回 WSL。
2. **回归构建门禁**：执行 `npm.cmd --prefix gui ci`、GUI Vitest、`npm.cmd --prefix gui run build`、默认/mcp-dev/e2e Cargo check，并再次确认 capability 目录仅有 `default.json`。这一步是后续 packaged/native 检查的前置条件。
3. **P0 原生 GUI 与恢复**：在干净 fixture 下完成 WVQ-001、WVQ-003、WVQ-004；先验证中文布局/键盘和 picker/path allowlist，再执行 mock job 取消、sidecar 重启、worker crash、显式 retry、artifact tamper 和 active PID 不误回收。
4. **P0 stale package 与 QA**：完成 WVQ-009 的 fresh package handshake、source freshness audit 和 stale-GUI 错误展示；执行 WVQ-015 的 clean Windows CLI/sidecar JSON stdout 检查，确认 PyMuPDF/dependency notice 不污染机器可读输出。
5. **P1 运行时与文件系统**：完成 WVQ-007 全部 work-dir retention、锁文件、长路径/ junction、retry category、cancel/reconnect 矩阵；完成 WVQ-010～014 的 Windows worker、路径、环境变量、超时和恢复证据。
6. **P1 打包与桌面可用性**：完成 WVQ-002 的 125%/150%/200% DPI、NVDA、resize/close/focus 检查；完成 WVQ-004 clean-user 首次启动、卸载/重装/升级、MSI admin extraction 与 payload parity。
7. **P1/P2 安全与授权集成**：完成 WVQ-005 Defender/SmartScreen、签名、SBOM、checksum、依赖 advisory；完成 WVQ-016 Debug-only localhost MCP bridge 的 Windows 原生观察；只有获得明确授权后才执行 WVQ-006 live Codex/PDF。

### Current-head Windows recovery configuration

本轮 `8f046ef` 的配置门禁大部分通过，但 Windows 环境在 WDIO、Python/uv、冻结 worker 和 WiX MSI 阶段出现独立阻塞。下一轮必须先按以下配置恢复环境，再重跑依赖检查；不得把旧产物当作当前结果：

1. 为 Windows workspace、npm cache、uv cache、`TEMP`/`TMP` 和 E2E workspace 使用当前用户可写的本地路径，优先使用 E: 盘验证目录；记录实际路径和 ACL 检查结果。
2. 安装或修复可执行的 Windows Python/uv 环境，确认 `python --version`、`.venv\\Scripts\\python.exe --version`、`uv run python --version` 和 `uv sync --locked --extra runtime --extra dev` 均可运行；若默认 cache 失败，使用显式 E: cache 并记录错误，不得复用不可执行的旧 `.venv` trampoline。
3. 在可用 Python 环境中重新构建 target-triple sidecar：`uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec`。构建后使用新 sidecar、全新的 E2E state/work/artifact 目录执行 worker request，并保留 JSONL、stderr、数据库路径和目录 ACL 证据。
4. 对 `uv_os_get_passwd ... ENOMEM` 先执行最小 WDIO/tsx 启动诊断，再执行 `npm.cmd --prefix gui run e2e:native:debug`；不要把“未进入 spec”记为产品 E2E PASS。若仍失败，保留 Node/tsx/WDIO 版本、环境变量摘要和最小错误日志。
5. 修复或重装与 Tauri MSI 构建匹配的 WiX toolset，确认 `candle.exe` 和 `light.exe` 来自同一工具链版本，再重跑 MSI 生成、admin extraction 和 payload parity。旧 MSI 只能作为历史产物，不能作为当前证据。
6. 以上环境恢复仅是 Windows 验证前置配置；native WDIO、冻结 worker、MSI、原生 GUI、clean-user 和发布安全在取得新的 Windows 结果前均保持 `WINDOWS_VERIFICATION_PENDING`、`FAIL` 或 `BLOCKED`，不得由 Linux 结果升级。

Windows 后续步骤的详细命令、证据要求、失败分类和 write-back 格式统一见
[`docs/validation/windows.md`](validation/windows.md) 的 “Current-head
environment recovery before rerun” 至 “Required Windows write-back” 小节。

### 失败与阻塞处理

- 独立的 CLI、协议、文件系统、构建和 bundle audit 检查必须在 GUI automation 或 Computer Use 阻塞后继续执行。
- MSI extraction、native GUI trusted RPC、NVDA 或外部 MCP 不可用时，分别标记 `BLOCKED` 或 `NOT RUN`，记录具体原因、重试情况和替代证据，不得标记为 PASS。
- `WVQ-007` 的完整 Windows 句柄生命周期仍需独立证据；一次 QA harness cleanup PASS 不能替代 work-dir/lock/retry/cancel/reconnect 全矩阵。
- `WVQ-009` 的 stale bundle negative audit PASS 不能替代 stale-GUI 原生错误展示；freshness、runtime handshake 和 GUI 错误呈现需要分别记录。

## Latest Windows validation after Linux inline capability configuration (2026-09-15)

Linux source HEAD 4d26621c1d60431db0f3f9d4e88f8df554aaaa59 is the documentation commit on top of the capability configuration commit 6ae5258. It was synchronized one-way to the E drive with dependencies, caches, state, logs, build artifacts, user data and the existing Windows sidecar excluded. The synchronization copied 15 source files with zero failures; three confirmed-obsolete E2E helper files were removed only from the E drive gui/scripts subtree.

Windows configuration and automation results:

- npm ci, production dependency audit, GUI Vitest 28/28 and the production build passed. The development dependency tree still reports 18 vulnerabilities; no automatic audit fix was run.
- The inline flavor boundary passed: gui/src-tauri/capabilities contains only default.json before and after E2E preparation/build; the obsolete prepare-e2e-rust.mjs and scripts/capabilities templates are absent from the Windows copy.
- Default Cargo, mcp-dev Cargo and e2e Cargo checks passed. The combined mcp-dev,e2e check produced the expected compile-time mutual-exclusion error.
- The standard embedded npm run e2e:native passed 6 spec files and 20 tests, including native path rejection and Windows path rejection. WebView2/Edge 152 and the tauri-service embedded provider started successfully.
- The independent frozen sidecar JSONL probe passed with protocol_version 1: get_server_info succeeded, an outside input path returned CONFIG_INVALID with the safe allowlist message, shutdown returned closing=true, and the process exited 0.
- MCP Debug Tauri build passed. The only recorded build warning was the known linker stdout message; WDIO service warnings about mock-store cleanup, null u32 diagnostics and disk-space detection remain non-blocking diagnostics.

WVQ-018 and the automated WVQ-017 native scope are now WINDOWS_PASS. Native picker, DPI/accessibility, clean-user, installer/release security, MCP localhost observation and authorized live Codex/PDF acceptance remain WINDOWS_VERIFICATION_PENDING. Full commands and evidence are in docs/validation/windows.md.

### Windows-only completion order

1. **Source/workspace preparation**：只从 WSL 同步源代码、配置、测试和指定文档；记录 branch/commit/dirty state；排除 `.git`、依赖、target、build、sidecar、state、日志、缓存、凭据和用户 PDF。
2. **Toolchain/build baseline**：Windows 上重新安装 npm 依赖，运行 GUI Vitest、production build，并记录 Node/npm/Python/uv/Rust/MSVC/WebView2 版本。
3. **WVQ-018 capability lifecycle**：确认 `gui/src-tauri/capabilities/` 只有 `default.json`，`e2e.json`/`mcp-debug.json` 永不生成；分别确认 default、mcp-dev、e2e flavor 的权限边界和互斥 feature。
4. **WVQ-017 native WDIO**：运行 `npm.cmd --prefix gui run e2e:native`，必须包含 smoke、handshake、mock lifecycle、path rejection 和 Windows path specs；失败时保留 spec、sidecar 日志和最小错误片段。
5. **Native desktop behavior**：验证 Windows picker、盘符/Unicode/空格/traversal/权限、取消、重连、artifact tamper、关闭重开和进程清理。
6. **Packaged/clean-user**：验证 target-triple sidecar、NSIS/MSI/portable、隔离用户首次启动、卸载/重装/升级、bundle audit 和 manifest；unsigned 限制单独记录。
7. **MCP/live/release**：验证 Debug-only localhost MCP Bridge；经授权后再执行真实 Codex/PDF；最后处理 Defender/SmartScreen、签名、SBOM、依赖 advisory 和发布审批。

上述顺序中，前一阶段失败时仍应继续执行不依赖它的独立检查；依赖失败的项目必须标记 `BLOCKED`，不得静默跳过。

## Windows WDIO configuration revalidation before Linux allowlist follow-up (2026-09-15)

- Linux/WSL remains the source of truth: branch dev, HEAD f6d3fd02322052b34ad92bb0dbd6aa8885f9b2c3, with the existing GUI/WDIO development tree dirty. Phase 15 infrastructure is present; the Windows run used a one-way WSL-to-E: sync and did not write business code back.
- Windows-side configuration is now aligned with the current plan: cross-env propagates VITE_E2E into the Tauri build and worker; e2e preparation selects the target-triple sidecar and fixture workspace; GUI and sidecar config paths resolve from the Tauri working directory as ../config/e2e.toml; E2E input helpers trigger the real React input/change path without enabling the branch in production builds; and the WDIO type surface matches @wdio/tauri-service 1.4.0.
- Windows evidence: npm ci, GUI Vitest 27/27, production build, E2E preparation/build, mock lifecycle 4/4, embedded handshake 3/3, embedded smoke 4/4 and Windows lifecycle 2/2 passed. The standard native command still fails in two path-allowlist specs because the deterministic E2E mock transport accepts an outside path; the frozen sidecar independently returned the required structured rejection for the same path.
- Current state remains WINDOWS_VERIFICATION_PENDING. The detailed matrix, exact commands, hashes, warnings and follow-up are recorded in docs/validation/windows.md. Live Codex, clean-user packaging, native picker, DPI/accessibility and release acceptance remain separate work.

## Linux follow-up after Windows WDIO revalidation (2026-09-15)

本节记录 Windows 配置复核回传后，Linux 端需要继续执行的工作；Windows 逐项命令、产物哈希和状态矩阵仍以 [docs/validation/windows.md](validation/windows.md) 为准。

### 当前配置结果

- Phase 15 的 Linux 实现已按当前计划同步到 Windows 验证副本：cross-env 负责将 VITE_E2E=1 传入 Tauri 构建与 worker；E2E 准备脚本按 target triple 选择 sidecar，并创建隔离的 gui/build/e2e/ 工作区。
- GUI/sidecar 的 E2E 配置路径统一按 Tauri 工作目录解析为 ../config/e2e.toml；输入 helper 通过真实 React input/change 路径注入 E2E fixture，生产构建不会启用该分支；WDIO 类型面与 @wdio/tauri-service@1.4.0 的 API 对齐。
- config/e2e.toml 继续使用 translator = mock，本轮没有真实 Codex、用户配置、用户 PDF 或付费模型调用。

### 当前验证结果

 - Windows 已通过：npm ci、GUI Vitest 27/27、生产构建、E2E prepare/build、mock lifecycle 4/4、embedded handshake 3/3、embedded smoke 4/4、Windows lifecycle 2/2；文档 inventory 17 passed。
 - Linux 已实际通过 native smoke 4/4、mock lifecycle 4/4、path rejection 4/4、sidecar handshake 3/3；完整 `npm run e2e:native` 共 4 个 spec 文件、15 个测试全部通过。E2E-only persistent mock 的 input-directory allowlist 修复和 Vitest regression 已验证。
 - 标准 npm run e2e:native 的 Windows 路径安全结论仍需在 Windows 同步修复后复跑，不得把 Linux mock contract 或旧 Windows 失败记录写成 Windows PASS。
- 同一 Windows 工作区对冻结 sidecar 的直接 JSONL probe 已返回 CONFIG_INVALID 及安全的 source_path is outside the configured input directory；这证明真实 sidecar allowlist 生效，但不等同于 GUI→真实 sidecar 的完整原生验收。
- 因此当前总体状态仍为 WINDOWS_VERIFICATION_PENDING；外部 driver 诊断、live Codex、clean-user、native picker、DPI/accessibility、release security 与完整生命周期矩阵仍未完成。

### Linux 端下一步

1. **Linux WDIO native 已完成**：allowlist contract、测试隔离和 localStorage 防护已修复；`npm run e2e:native` 15/15 通过。
2. **Browser mode 继续 BLOCKED**：当前 Linux 未提供 Chrome/Chromedriver；安装并确认浏览器与 Vite dev server 后再执行 `npm run e2e:browser`，不得用 native 结果替代 browser 覆盖。
3. **回传下一轮 Windows 验证**：Linux regression 通过后再次单向 WSL→E 同步，仅同步源代码/配置/测试和指定文档，不反向带回 node_modules、sidecar、日志、缓存或 build/e2e 产物；重跑标准 native、路径负向用例和冻结 sidecar protocol probe。
4. 保留 WVQ-017 及 live Codex/PDF、clean-user、原生 picker、DPI/NVDA、安装器与发布安全队列为 WINDOWS_VERIFICATION_PENDING，直到对应平台证据实际取得。

## Linux follow-up completion after Windows WDIO revalidation (2026-09-15)

Windows WVQ-017 复核外化了 `npm run e2e:prepare`/`e2e:build` 生成的 `gui/src-tauri/capabilities/e2e.json` 可能残留，从而污染默认与 mcp-dev 的 `cargo check`（`Permission wdio:default not found`）。Linux 端已通过**内联 capability**彻底修复；Windows 复验见 WVQ-018。完整 Linux 验证结果见 `docs/development/testing.md`（Linux follow-up completion）；Windows 运行明细与历史记录仍以 `docs/validation/windows.md` 为准。

根因：Tauri build script 用 `parse_capabilities("./capabilities/**/*")` + `validate_capabilities` 校验目录中**所有** capability 文件。

修复：
- 把 `e2e`/`mcp-dev` capability 作为 `CapabilityEntry::Inlined` 直接嵌入 `tauri.e2e.conf.json`/`tauri.mcp.conf.json`（通过 `--config` 合并）；
- 删除 `gui/scripts/prepare-e2e-rust.mjs` 与 `gui/scripts/capabilities/{e2e,mcp-debug}.json` 模板；
- 从 `package.json` 移除 `tauri:prepare`/`mcp:prepare` 及 `e2e:prepare`/`e2e:build` 中的能力注入步骤；
- 删除 `.gitignore` 中 flavor capability 条目；
- 新增回归 Guard `tests/test_gui_flavor_capabilities.py`（7 tests）断言共享 `capabilities/` 仅含 `default.json` 且 `mcp-dev`/`e2e` 互斥约束保留。

| 项目 | 状态 | 证据 |
|---|---|---|
| E2E capability 生成/清理生命周期 | ✅ RESOLVED | flavor capability 内联于 tauri.*.conf.json；`gui/src-tauri/capabilities/` 仅含 `default.json`，无生成痕迹。 |
| 默认 / mcp-dev / e2e Cargo checks | ✅ PASS | `cd gui/src-tauri && cargo check --locked` / `--features mcp-dev` / `--features e2e` 均 `Finished`，无 `wdio:default not found`。 |
| E2E prepare/build/native WDIO | ✅ PASS | `npm run e2e:prepare && npm run e2e:build && npm run e2e:native` — 4 spec files、15 tests 全部通过；结束后 `capabilities/` 仅 `default.json`，无 tauri/wdio/WebDriver 进程与监听端口。 |
| Linux 全量回归 | ✅ PASS（env-scoped） | `uv run pytest` 231 passed, 5 deselected；`ruff check`/`ruff format --check` clean；GUI `npm test` 28 passed、`tsc --noEmit`/`vite build` clean；docs inventory passed。（3 个预存 `pymupdf`/doctor-runtime 环境失败，`git stash` 后仍 fail，与改动无关。） |
| frozen sidecar/protocol probe | NOT RUN (not required) | 变更未触及 sidecar 协议/工作目录/allowlist/错误分类。 |
| Linux browser WDIO | BLOCKED | 未安装 Chrome/Chromium + 匹配 driver。 |
| Windows 原生 GUI/DPI/picker/Codex/PDF | WINDOWS_VERIFICATION_PENDING | WVQ-001～016 + WVQ-018 不变，Linux 仅验证契约/夹具/回归。 |

## Latest Windows WDIO revalidation after Linux allowlist contract (2026-09-15)

- The clean Linux dev HEAD 8763193b19bb1ddedd332c423087896236ce92b9 was synchronized one-way to E:/Shiraishi/VSCode Workspace/Codex_Translator. Robocopy copied 123 files with 0 failures and preserved the Windows dependency, cache, state, log, build and sidecar extras.
- Windows configuration gates passed: npm ci, production dependency audit, GUI Vitest 28/28, production build, E2E prepare/build, default and mcp-dev Cargo checks after generated-capability cleanup, E2E feature compilation and the mutual-exclusion compile guard.
- The standard embedded npm run e2e:native now passes 6 spec files and 20 tests, including the Linux-added E2E mock allowlist contract, native path rejection and Windows path rejection. The frozen target-triple sidecar independently returned the required structured CONFIG_INVALID rejection for an outside input path.
- A transient validation configuration failure was recorded: the generated E2E capability remained visible to default/mcp-dev Cargo checks after preparation. Removing the exact target-local generated file restored both checks; Linux should make this cleanup boundary idempotent or explicit.
- Automated WVQ-017 native scope is WINDOWS_PASS. Overall project state remains WINDOWS_VERIFICATION_PENDING for native picker, DPI/accessibility, clean-user, installer/release security and authorized live Codex/PDF acceptance. Full evidence is in [docs/validation/windows.md](validation/windows.md).

## Windows manual GUI basic-interaction result (2026-09-14)

- Operator evidence confirms PASS for Debug Bridge startup, fail-closed
  unavailable presentation, notice dismissal in the unavailable state, mouse
  and keyboard navigation, no-PDF protection, native picker cancellation,
  Unicode/space-containing path display and reduced-window layout.
- Release GUI starts the sidecar and reaches the connected state. Release
  valid-PDF selection also passes, but the selected-file notice disappears
  immediately and remains a GUI notification-lifecycle FAIL.
- Debug GUI remained in the unavailable state despite a successful Tauri/Vite
  launch and no captured sidecar error. Debug healthy-handshake diagnosis is
  still open; Release handshake passing does not clear the Debug path.
- Detailed evidence and the operator transcript are recorded in
  docs/validation/windows.md under the 2026-09-14 manual GUI basic-interaction
  section. No business code was changed.

## Windows manual file-selection/path result (2026-09-14)

- Operator screenshots confirm PASS for the PDF picker filter, picker
  cancellation, valid PDF selection, space-containing paths, Unicode paths,
  uppercase PDF extensions, configured-input path rejection, missing-file
  rejection and non-PDF invisibility under the PDF filter.
- A new GUI lifecycle FAIL remains: after the outside-directory and
  missing-file errors, the error notice is briefly visible and is then
  replaced or obscured by Starting sidecar / 正在重新连接. The path-safety
  checks pass; the error feedback does not remain stable enough to read.
- The screenshots also show 正在重新连接 during the rejected-path cases.
  This requires separating a real transport/reconnect transition from a
  notice/status overwrite. No business code was changed.

## Linux notice/state lifecycle follow-up (2026-09-14)

- Linux implemented shared notice updates in `JobStore.setNotice()` and routed
  App-level notices through it. This prevents polling/reconnect state updates
  from recreating a locally overwritten selection or error notice, addressing
  the Release selection-notice persistence `FAIL` at its shared-state root.
- `startTranslation` now uses a one-shot transport request that does not
  schedule global reconnect on rejection. A rejected path surfaces its error
  to the notice while the previously healthy connection stays `ready`,
  addressing the observed `正在重新连接` after path rejection.
- New GUI regressions pin both behaviors: a shared notice survives polling,
  and a rejected `start_translation` keeps the connection `ready`. Linux
  GUI tests/build pass; native Windows retest remains
  `WINDOWS_VERIFICATION_PENDING`.
- The Debug-only healthy-handshake diagnosis is not resolved by these
  lifecycle fixes and remains a Windows follow-up.

## Windows validation rerun for current Linux HEAD (2026-09-14)

- Current WSL HEAD 7cd978eaa3bd1b9e4d7226d626603a0bdc3b7a9a was synced
  one-way to E: with 24/24 source-state hashes matching and no business-code
  changes made in the validation workspace.
- Controlled Windows evidence passed: Python 227 passed, 5 deselected, GUI
  26 passed, mock integration 5 passed, source-scoped Ruff and
  compile/docs/lock/doctor gates, fresh PyInstaller sidecar and
  protocol/invalid/valid worker checks, target-sidecar and bundle audits,
  NSIS/MSI build/extraction, and release/extracted GUI process smoke. Tauri
  MCP Debug also passed narrow bridge, DOM, screenshot and navigation checks.
- Remaining status: default pytest is BLOCKED by Windows Temp WinError 5;
  unscoped Ruff is a FAIL caused by preserved build/uv-cache-current
  artifacts; the valid frozen worker is functionally PASS but stderr
  cleanliness remains FAIL for retry/fallback and PyMuPDF deprecation
  warnings. Broad GUI lifecycle, clean-user, release security and live
  Codex/PDF checks remain deferred.
- Overall Windows state remains WINDOWS_VERIFICATION_PENDING. Detailed
  evidence and Linux follow-up are in
  [docs/validation/windows.md](validation/windows.md).

## Latest Windows revalidation after Linux status/PID fixes (2026-09-14)

- Current WSL source `7cd978e` was revalidated on E: after the Linux
  failed-state color and conservative PID-query changes. Python `226 passed,
  5 deselected`, GUI `24 passed`, mock PDF integration `5 passed`, frozen
  worker functional output, protocol/freshness/package gates and MSI
  extraction/process smokes passed.
- The frozen worker also emitted `--multiprocessing-fork` parser/save warnings;
  record this as a current frozen-runtime `FAIL`. Linux has added
  `multiprocessing.freeze_support()` before the frozen sidecar imports its
  argparse entrypoint, plus a regression test. The repaired source still needs
  a fresh Windows frozen-worker/package revalidation. The earlier Computer Use blocker for
  native stale-GUI visual confirmation was resolved by a human Windows retest:
  the stale-sidecar state now shows the corrected red indicator and the fresh
  control shows the connected state. A neutral gray indicator while connecting
  is recorded as a UX recommendation, not a current acceptance failure.
- The GUI picker/path/permission/cancellation/reconnection matrix remains
  `NOT RUN` with `SKIPPED_BY_USER_REQUEST`, as explicitly requested. It is not
  a Linux development blocker. Full details and remaining follow-up are in
  [`docs/validation/windows.md`](validation/windows.md).
- Subsequent operator checks passed Chinese rendering, keyboard navigation,
  Settings, empty Jobs state, reduced-size layout and narrow path-rejection/
  picker-cancel cases. NVDA is permanently skipped because it is not installed.
  Mock-job cancellation and sidecar reconnection failed; artifact-tamper
  validation was blocked by the failed mock translation. `WIN-MANUAL-005`
- clean-user installation/recovery is permanently skipped by explicit user
  request, with no clean-user conclusion inferred. The GUI notice banner also
  has a current `FAIL`: clicking `x` on `Sidecar handshake ready` causes the
  unchanged notice immediately; Linux now stores notice dismissal in the shared
  `JobStore` and has regression coverage. Native Windows notice dismissal still
  needs revalidation. These findings need focused Windows follow-up after the
  frozen-worker issue is resolved.

## Current-source stale-GUI manual result (2026-09-14)

- The fresh control passed the observed launch/normal-exit check. The
  current-source GUI paired with the stale sidecar showed the correct
  fail-closed text and banner, but the `本地服务不可用` status light was
  green; the full stale-GUI observation remains a historical `FAIL` until
  native Windows revalidation.
- Linux follow-up completed: failed sidecar status now uses the destructive
  color selector and a GUI regression test fixes the `failed` status mapping.
  Native Windows stale-GUI revalidation remains
  `WINDOWS_VERIFICATION_PENDING` and must not be promoted by Linux evidence.
- The GUI picker/path/permission/cancellation/reconnection interaction matrix
  is `NOT RUN` for this round because it was explicitly skipped by the user;
  retain it in the Windows queue for a separately authorized native run.
- No business-code change is part of the validation task.

## Real Codex and long-document benchmark follow-up (2026-09-14)

- The first operator-initiated real Codex benchmark attempt is `BLOCKED`: the
  six-page input reached `translating`, then the runner disappeared without a
  terminal state or artifacts. The subsequent CLI inspection also exposed a
  Windows PID-recovery error in `_process_is_alive()`.
- Linux follow-up completed: `_process_is_alive()` now treats indeterminate
  native `OSError` PID queries conservatively as alive, with a regression test.
  The next step is to rerun with a fresh isolated state directory and an approved,
  substantially longer de-identified PDF. The detailed run evidence remains
  in [`docs/validation/windows.md`](validation/windows.md); no benchmark pass
  or long-document stability conclusion is claimed yet.

## Current plan reconciliation (2026-09-14)

- The latest Windows validation result is now a new fact input. The current
  source tree at `7cd978e` passed the frozen worker mock request, sidecar
  protocol-v1 handshake, target-triple sidecar, fresh/stale `WVQ-009` audit,
  NSIS/MSI build and extraction parity, QA/tamper checks, GUI tests/build and
  mock PDF integration. The recorded product summary is `PASS 31 / FAIL 0 /
  BLOCKED 4 / NOT RUN 6 / NOT APPLICABLE 1`; the overall state remains
  `WINDOWS_VERIFICATION_PENDING`.
- The previous Windows failures for documentation-inventory path separators and
  frozen `bitstring.bitstore_bitarray` collection are closed as Linux
  implementation work and have now been revalidated natively. They must not be
  carried forward as open Linux tasks or reimplemented.
- No new Linux product-code fix is required by the latest Windows result. The
  remaining Linux-applicable work is regression maintenance plus the planned
  non-Windows evidence work: authorized live Codex/thread behavior,
  long-document and batching/cache benchmarks, and QA/font/visual calibration.
  These must remain separate from Windows-only acceptance and must not consume
  live model usage by default.
- Native GUI interaction remains `BLOCKED` because the automated run lacked a
  trusted targetable desktop surface. The subsequent operator-run
  current-source stale-GUI observation is `FAIL` for the green unavailable-
  state indicator; its text/banner behavior passed narrowly and the fix/retest
  is recorded at the top of this document and in the validation record.
  The GUI picker/path/permission/cancellation/reconnection matrix is separately
  `NOT RUN` by explicit user request, not `BLOCKED`.
  DPI/NVDA is `NOT RUN` by explicit request; clean-user, WVQ-007, WVQ-005,
  live Codex/PDF and dependency-remediation checks remain unexecuted. All of
  these stay in the Windows validation queue with
  `WINDOWS_VERIFICATION_PENDING` or their documented `NOT RUN`/`BLOCKED` state.

## Tauri MCP bridge configuration (2026-09-14)

- Added the committed Rust dependency `tauri-plugin-mcp-bridge` to the Tauri
  host. The Bridge is registered only under `debug_assertions` and binds to
  `127.0.0.1`; Release builds do not start it.
- Added `mcp-bridge:default` capability permission and enabled Tauri global APIs
  required by the development Bridge. The external
  `@hypothesi/tauri-mcp-server` package is intentionally not added to
  `gui/package.json`; it remains an Agent-environment tool.
- Linux/WSL validation does not start Tauri MCP or claim desktop GUI validation
  without a targetable desktop. Native Windows/Codex Bridge and packaged GUI
  checks remain `WINDOWS_VERIFICATION_PENDING` until directly executed.

## Linux follow-up after the current-source Windows observations (2026-09-14)

- **Stale-GUI status mapping:** the Windows operator observed a green status
  light beside the unavailable-sidecar message. Linux changed the CSS rule to
  style the actual `failed` connection state as destructive and added a GUI
  regression for the state-to-tone mapping. The historical Windows observation
  remains `FAIL`; native retest remains `WINDOWS_VERIFICATION_PENDING`.
- **PID recovery safety:** the live benchmark follow-up exposed
  `OSError: [WinError 11]` from `_process_is_alive()`. Linux now treats an
  indeterminate native PID query conservatively as alive, avoiding unsafe
  terminalization of a possibly running job, and added a regression test.
  Native Windows recovery and the authorized live Codex benchmark remain
  pending; no benchmark pass or long-document acceptance is claimed.
- **Linux verification after these fixes:** Python `226 passed, 5
  deselected`; mock PDF integration `5 passed` with 10 fork deprecation
  warnings; GUI Vitest `24 passed`; GUI build, Ruff, format, compileall and
  documentation inventory passed.

### Linux 后续修复（2026-09-12，worker 环境与 QA CLI stdout）

- 针对上一轮增量验证的两个 `FAIL` 项完成了 Linux 侧修复并闭环，Windows 原生重验证保留为 `WINDOWS_VERIFICATION_PENDING`（`WVQ-014`/`WVQ-015`）。
- **worker 子进程环境 allowlist**：`src/codex_babeldoc/backends/worker_client.py` 将环境构建抽为 `worker_environment(env_extra=None)`，allowlist 同时保留 POSIX 键（`PATH/HOME/USER/TMPDIR/LANG/LC_ALL`）与 Windows 运行时/配置文件键（`SYSTEMROOT/USERPROFILE/TEMP/TMP/APPDATA/LOCALAPPDATA/PROGRAMDATA`），缺失键跳过、`env_extra` 优先。新增 `tests/test_worker.py::TestWorkerEnvironment`（Windows 键保留、POSIX 键保留、`env_extra` 覆盖、`Popen` 只收到 allowlist 键、不继承无关父变量）。
- **QA CLI stdout 污染**：根因是 PyMuPDF 的 `fitz` 兼容 shim 直接用 print 向 stdout 输出 deprecation 提示，`-W` 无法抑制。源码与测试统一改用官方 `pymupdf` 包名（`src/codex_babeldoc/qa/*`、`core/pipeline_meta.py`、`translation/context.py` 及相关测试）。新增 `tests/test_cli.py::test_qa_cli_stdout_is_machine_readable_in_clean_subprocess`：子进程以干净 `PYTHONPATH` 启动 `python -m codex_babeldoc.cli qa`，断言整个 stdout 可解析为单个 JSON 文档且 `ok == true`。
- Linux 验证：compileall PASS；ruff check/format PASS；Python 单元套件 `206 passed, 5 deselected`；GUI Vitest `22 passed`；Vite build PASS；mock PDF integration `5 passed`。未修改依赖、配置或架构。

### Windows 验证复核（2026-09-12，MSI 重验证）

- 当前 WSL `dev` HEAD 为 `4e709d922849516c8162f5b17d387b32b5f42ceb`，本轮 dirty tree 包含 5 个文档文件和 11 个代码/测试文件；已按规则单向同步到 E:，68 个文件更新、0 个失败、17 个 Windows 本地排除/保留项，11 个变更代码/测试文件 SHA-256 一致。
- Windows 自动化与包级验证均为 `PASS`：Python `201 passed、5 deselected`，GUI `22 passed`，mock PDF integration `5 passed`，QA CLI 正向/篡改/清理通过；lock/sync、Ruff、compileall、doctor、Vite、Cargo、Tauri 配置/icon、PyInstaller、sidecar handshake/worker 错误路径、target-triple、fresh/stale bundle audit、NSIS/MSI 构建、MSI 管理员提取与 payload parity、解包 sidecar handshake、release/解包 GUI 进程 smoke 均通过。之前的 `WinError 32` 清理问题本轮未复现。
- 当前 fresh sidecar SHA-256 为 `B892AD80...D4EB5`，release GUI 为 `8B1450D6...A934`，NSIS 为 `EFE0FF2D...448A`，MSI 为 `28F5206C...3576`；均为 unsigned 开发产物。packaged stale-GUI 错误展示和原生 GUI 交互/路径/DPI/NVDA 矩阵因 Windows UI trusted RPC 不可用为 `BLOCKED`。
- 本轮计数：`PASS 21 / FAIL 0 / BLOCKED 2 / NOT RUN 5 / NOT APPLICABLE 1`。clean-user、完整 WVQ-007 生命周期、Defender/SmartScreen/签名/SBOM/release 安全、live Codex/PDF 和依赖 advisory 处理为 `NOT RUN`；Linux-only AppImage/native-Linux acceptance 为 `NOT APPLICABLE`。整体仍为 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：Provision 可用的原生 Windows UI 自动化环境，完成 WVQ-001～004/009 原生桌面验证和 WVQ-007 全生命周期矩阵，再安排发布安全与 live service 验收；保留 sidecar handshake 与 source-freshness 双层门禁。本轮未修改业务代码、依赖或配置。

### Windows 验证复核（2026-09-12，CLI/QA 变更重跑）

- 当前 WSL `dev` HEAD 为 `4e709d922849516c8162f5b17d387b32b5f42ceb`，本轮包含 5 个既有文档变更和 11 个当前代码/测试变更；已按规则单向同步到 E:，68 个文件更新、0 个失败、17 个 Windows 本地排除/保留项，11 个变更代码/测试文件 SHA-256 一致。
- Windows 自动化与包级验证均为 `PASS`：Python `201 passed、5 deselected`，GUI `22 passed`，mock PDF integration `5 passed`，QA CLI 正向/篡改/清理路径通过；lock/sync、Ruff、compileall、doctor、Vite、Cargo、Tauri 配置/icon、PyInstaller、sidecar handshake/worker 错误路径、target-triple、fresh/stale bundle audit、NSIS/MSI 构建和 release GUI 进程 smoke 通过。新增 CLI 日志文件句柄释放回归测试通过，之前的 QA fixture `WinError 32` 清理问题本轮未复现。
- 当前 fresh sidecar SHA-256 为 `617E3B38...8FB53`，release GUI 为 `4801F156...A615F`，NSIS 为 `645CB227...8744`，MSI 为 `FEDCF16A...31CB`；均为 unsigned 开发产物。MSI 管理员提取/包内 parity 因超时且无 payload 为 `BLOCKED`；packaged stale-GUI 错误展示和原生 GUI 交互/路径/DPI/NVDA 矩阵因 Windows UI trusted RPC 不可用为 `BLOCKED`。
- 本轮计数：`PASS 21 / FAIL 0 / BLOCKED 3 / NOT RUN 5 / NOT APPLICABLE 1`。clean-user、完整 WVQ-007 生命周期、Defender/SmartScreen/签名/SBOM/release 安全、live Codex/PDF 和依赖 advisory 处理为 `NOT RUN`；Linux-only AppImage/native-Linux acceptance 为 `NOT APPLICABLE`。整体仍为 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：恢复并重跑 MSI 管理员提取，完成 WVQ-007 workdir/lock/retry/cancel/reconnect 全矩阵，安排 WVQ-001～004/009 原生桌面与 clean-user、路径权限、DPI/NVDA 和发布安全验证；保留 sidecar handshake 与 source-freshness 双层门禁。本轮未修改业务代码、依赖或配置。

本文档基于当前项目现状、AiNiee、PDFMathTranslate v1、PDFMathTranslate-next 与 BabelDOC 的实现分析，汇总成统一的开发框架与实施计划。

相关文档：

- 架构总览：`docs/architecture.md`
- 关键决策：`docs/decisions.md`
- 项目说明：`README.md`
- 架构约束：`AGENTS.md`

## 1. 总体结论

项目名称：**BabelCodex**

公开仓库：`15699122/BabelCodex`

产品定位：主要面向个人、本地 PDF 翻译，不以多租户 SaaS、公共翻译 API 或商业级 SLA 为目标。MIT License 允许修改、再分发和商业使用；“个人使用”是产品定位，不是额外的许可证限制。

默认生产模式采用：

```text
BabelDOC 0.6.x Python 高层 API
+ 单次 PDF 流水线
+ BabelDOC Worker Process
+ BaseTranslator Bridge
+ Translation Gateway
+ 每文档一个 Codex Thread
+ 短窗口批处理
+ 严格占位符验证
+ 结构化状态和错误管理
```

不把以下方式作为默认生产路径：

- BabelDOC CLI 黑盒调用
- 自行复制 PDFMathTranslate v1 的 PDF content stream 重写
- 主进程修改 BabelDOC 全局对象
- 默认执行两遍 BabelDOC 的 Extract/Render
- 抓取 ChatGPT Cookie
- 调用未公开 ChatGPT HTTP API
- 将 ChatGPT 登录伪装成 OpenAI-compatible endpoint
- Codex 失败后静默切换到付费 API Key
- 在同一个 Codex thread 上并发执行多个 turn

## 2. 功能范围

### MVP

- `cbpdf doctor`
- 单个 PDF 翻译
- 目录批量翻译
- BabelDOC 0.6.4 兼容适配
- Codex SDK 翻译
- mock 翻译
- 每文档一个 Codex thread
- 串行 Codex turn
- 占位符提取与验证
- Markdown/解释性输出检测
- 精确输出重试
- 文档级任务状态
- 完成任务跳过
- 强制重跑
- 单语 PDF
- 双语 PDF
- 结构化错误类别
- 基础 PDF 输出检查
- 不调用真实 Codex 的默认单元测试
- 显式标记的真实集成测试

### Beta

- Translation Gateway
- 短窗口批处理
- SQLite 段落缓存
- 文档 glossary
- Codex thread 恢复
- worker 结构化进度
- worker 超时和取消
- 输出 artifact manifest
- PDF fixture 回归测试
- 未翻译文本检测
- token 与耗时统计

### 稳定版

- 文档上下文提取
- 自动术语候选
- thread 压缩和轮换
- BabelDOC part 级恢复评估
- PDF 布局 QA
- 字体和缺字检测
- 视觉回归测试
- `inspect/retry/validate/list/cleanup` 等运维命令
- 可选的实验性两阶段 Extract/Render

### 首期不包含

- Web SaaS / 多租户
- 浏览器 Cookie 提取
- 未公开 ChatGPT API
- 默认 API Key 回退
- 多模型自动故障转移
- PDF 可视化编辑器
- 自研完整 OCR
- 自研 PDF 排版引擎
- 默认同时翻译多个大型 PDF
- 同一 Codex thread 并发调用
- 对所有扫描 PDF 承诺高精度

## 3. 开发阶段

### Phase 0A：公开 GitHub 仓库与项目基线

**优先级：P0 | 复杂度：M | 预计：0.5–1 个开发日**

**状态：已完成（2026 年 9 月 8 日）**

任务：

1. 确定产品名为 BabelCodex
2. 创建公开仓库 `15699122/BabelCodex`
3. 审查公开上传内容、许可证和测试 fixture
4. 扩展 `.gitignore`，排除 PDF、日志、状态、缓存、凭证和本地配置
5. 初始化本地 Git 仓库
6. 首次提交源码、测试、配置和规划文档
7. 推送 `main` 到 GitHub
8. 验证本地 `main` 与远程 `origin/main` 的 HEAD 一致
9. 建立后续 feature branch 和 Pull Request 规则

验收：

- GitHub 仓库为 public
- 本地 `main` 跟踪 `origin/main`
- 本地与远程 HEAD 相同
- 工作树干净
- secret scan 通过
- 不上传用户 PDF、译文、日志、状态、缓存、token 或私有 glossary

完成记录：

- 公开仓库已创建；
- 初始提交：`a2ee931d09b0911080fc40f7079f50f89963dd66`；
- 本地 `main` 已跟踪 `origin/main`；
- 首次推送后本地与远程 SHA 一致；
- staged credential scan 和禁止路径检查通过。

### Phase 0B：开发环境与依赖基线

**优先级：P0 | 复杂度：M | 预计：2–4 个开发日**

**状态：工程基线已完成；Codex 用户登录待完成（2026 年 9 月 8 日）**

任务：

1. 安装 Python 3.12
2. 安装 `uv`
3. 生成 `.venv`
4. 锁定 BabelDOC 0.6.4
5. 锁定 `openai-codex` 版本
6. 生成 `uv.lock`
7. 配置 pytest marker
8. 配置 Ruff
9. 完善 `doctor`
10. 验证 BabelDOC warmup
11. 验证 Codex 登录
12. 增加兼容矩阵文档

验收：

```bash
uv sync --extra runtime --extra dev
uv run pytest
uv run ruff check .
uv run cbpdf --config config/example.toml doctor
```

全部可执行，且 `doctor` 对缺失依赖返回非零退出码。

当前完成记录：

- 已安装 uv 0.12.10；
- 已由 uv 安装并固定 CPython 3.12.14；
- 已生成 `uv.lock`，解析 95 个包；
- 已安装 BabelDOC 0.6.4、openai-codex 0.147.0 和 bundled Codex runtime 0.147.0；
- BabelDOC warmup 已完成；
- Ruff format、Ruff check 和 6 个单元测试通过；
- GitHub Actions CI 已建立；
- `doctor` 已区分系统 Codex CLI、SDK bundled runtime 和认证状态。

当前阻塞项：Codex runtime 返回 `Not logged in`。用户完成 ChatGPT 登录并使 `doctor` 返回 0 后，Phase 0B 才完全关闭。

### Phase 1：稳定领域模型和错误框架

**优先级：P0 | 复杂度：M | 预计：3–4 个开发日**

任务：

1. 定义 PDF Request/Result
2. 定义 Translation Request/Result
3. 定义 Artifact
4. 定义事件
5. 定义错误类别
6. 升级 JobState
7. 增加 schema version
8. 状态原子写入
9. 配置 fingerprint
10. JobState 向后兼容测试

验收：

- 状态写入中断不会留下半个 JSON
- 旧状态可迁移或给出明确错误
- 错误可区分认证、翻译、BabelDOC 与 QA
- 所有模型有类型标注

### Phase 2：占位符与输出正确性

**优先级：P0 | 复杂度：L | 预计：4–7 个开发日**

任务：

1. 实现 placeholder extractor
2. 实现 multiset comparison
3. 实现标签配对
4. 实现 Markdown fence 检测
5. 实现解释性前缀检测
6. 实现空输出检测
7. 实现 exact-output retry
8. 引入 scripted translator
9. 编写表驱动测试
10. 把验证接入当前单段 Codex adapter

验收：

- 不合格译文无法返回 BabelDOC
- 占位符缺失、新增、重复、错序均可检测
- 修复重试次数有上限
- 默认测试不调用真实 Codex

### Phase 3：BabelDOC 兼容层重构

**优先级：P0 | 复杂度：L | 预计：4–6 个开发日**

任务：

1. 定义 `PdfBackend`
2. 新建 BabelDOC 0.6.4 mapper
3. 移动所有 BabelDOC internal import
4. 标准化 progress
5. 标准化 finish result
6. 标准化 exception
7. 保留现有 single-pass 行为
8. 测试 `WatermarkOutputMode`
9. 测试 mono/dual
10. 确认 table model 行为
11. 增加 mock backend contract tests

验收：

- `core/` 和 `translation/` 不导入 BabelDOC
- BabelDOC 版本不匹配时快速失败
- 单语和双语路径被转换成统一结果
- 可用 mock translator 完成小 PDF 翻译

### Phase 4：BabelDOC Worker Process

**优先级：P0 | 复杂度：L | 预计：5–8 个开发日**

任务：

1. 定义 protocol v1
2. 实现 worker request
3. 实现 JSONL progress
4. 实现最终 JSON result
5. stdout/stderr 分离
6. 主进程 worker client
7. 超时
8. 取消
9. 强制终止
10. worker 日志
11. 退出码映射
12. 非法协议测试
13. worker 崩溃测试

验收：

- 主进程不加载 BabelDOC
- worker 崩溃不导致 CLI 崩溃
- stdout 不受第三方输出污染
- 进度事件可实时显示
- 超时后 worker 可被终止
- 失败状态写入 JobState

### Phase 5：集成 Fixture 与 Codex 垂直切片

**优先级：P0 | 复杂度：L | 预计：4–7 个开发日**

Fixture 内容：

- 双栏、标题、多级字体
- 行内公式、独立公式
- URL、DOI、引用
- 脚注、表格、图片和图注
- 跨页段落、中英文混排

测试层次：

1. mock translator
2. scripted valid translator
3. scripted invalid translator
4. 真实 Codex integration
5. 单语输出
6. 双语输出
7. 基础 PDF QA

验收：

- mock E2E 稳定
- 占位符无损
- 真实 Codex 测试需显式开启
- 输出 PDF 可以打开
- PDF 页数合理
- 不设置 API Key

完成这一阶段即达到 **MVP**。

### Phase 6：Translation Gateway 和批处理

**优先级：P1 | 复杂度：XL | 预计：7–12 个开发日**

任务：

1. 引入 gateway
2. 把 validation 从 translator 移入 gateway
3. 实现 request queue
4. 实现 batch window
5. 实现 stable request IDs
6. 定义批量结构化响应
7. 实现 fan-out
8. 单项重试
9. batch 拆分
10. timeout
11. shutdown
12. worker exception propagation
13. 性能 benchmark
14. 与单段模式结果对比

验收：

- turn 数下降至少 60%
- segment 错配为 0
- 占位符准确率不下降
- 同一 thread 无并发 turn
- shutdown 无死锁
- 任一等待调用均有确定结果或异常

### Phase 7：SQLite 翻译缓存

**优先级：P1 | 复杂度：M | 预计：3–5 个开发日**

任务：建立 SQLite/WAL/busy timeout、版本化 cache key、cache hit 指标、清理命令、隐私配置、并发测试和迁移策略。

验收：重跑相同 PDF 能减少 Codex turn；glossary/context/prompt 变化会使旧缓存失效；无效输出不会进入缓存。

### Phase 8：GUI 技术验证

**优先级：P1 | 复杂度：L | 预计：4–7 个开发日**

**状态：Python sidecar、事件/取消协议、Tauri 2 host spike、一轮 Windows 原生 sidecar/package 验证，以及 Linux/WSL 侧 GUI 自动重连、构建准备和 glossary/context 编辑器已完成；目标平台 GUI 交互矩阵和干净用户环境桌面 E2E 待完成（2026 年 9 月 9 日）**

任务：

1. 采用 CopyPolish 已验证的 Tauri 2 + React + TypeScript 方向
2. 验证 Tauri 2 启动固定 BabelCodex Python sidecar
3. 验证 Windows/Linux target triple sidecar 打包
4. 验证 JSONL 请求、响应、进度事件和错误事件
5. 验证 Worker 子进程控制、重启、取消和终止
6. 验证实时进度、取消和错误显示
7. 验证 PDF 选择、输出目录和 QA 报告展示
8. 验证打包体积、动态库、模型和字体资源
9. 验证 Tauri capability 与 shell 权限最小化
10. 完成 GUI 框架和 sidecar 许可证审查

当前完成记录：

- 新增固定 `babelcodex-service` JSONL 入口；
- sidecar 复用 `BabelCodexService`，不复制 PDF 编排逻辑；
- 支持受控的启动、查询、列表、取消请求和关闭请求；
- 输入 PDF 强制限制在配置的 input allowlist 内；
- 支持带单调递增游标的 `poll_events`，并通过 `get_job` 支持断线后的状态校准；
- worker 的标准化 `ProgressEvent` 已沿 Application Service 转发到 sidecar 事件队列；
- worker 支持通过受控 `cancel_event` 终止 subprocess，取消任务持久化为 `cancelled` 且不进入 retry；
- sidecar 重启后可通过共享 state store 查询已持久化任务状态；
- 已覆盖协议往返、非法 JSON、协议错误、路径越界、shutdown、进度事件、后台失败、取消和无 shell 暴露测试；
- 已新增 Tauri 2 + React/TypeScript host spike、固定 `babelcodex-service` externalBin、最小 capability allowlist 和 mock transport；
- 已验证 GUI 的 Vitest/Vite 构建与 Tauri Rust host 的 `cargo check`；
- 已在 Windows 原生环境用 target triple sidecar 完成 `cargo check`、NSIS/MSI bundle 构建、MSI 隔离解包和 sidecar JSONL `list_jobs` smoke；
- 已完成解包 GUI 的进程级启动检查；
- 尚未完成 sidecar 自身重启编排、GUI 文件选择/allowlist/取消/输出目录等 packaged 交互 E2E、干净用户目录验收、Defender/SmartScreen 矩阵、签名/SBOM 和 Linux 目标机实际 smoke/发布验收；sidecar 指数退避、Linux bundle 构建和 glossary/context 编辑器已完成。
- 源配置已声明 `icons/icon.png`；Linux `.deb`/AppImage 构建已通过，目标机图标显示和正式发布资源审计仍待完成。

Phase 8 的以下步骤已完成：

- Windows Rust/MSVC、WebView2、Node.js/npm 和 Python sidecar 构建工具链；
- Windows target triple sidecar、Tauri externalBin 资源命名、`cargo check`；
- NSIS/MSI bundle、MSI 隔离解包、sidecar 受控 `--config` 启动和 JSONL smoke；
- bundle 与 sidecar SHA-256 记录，以及解包 GUI 的进程级启动检查。

仍需在原生 Windows 环境完成，不能由 WSL 或 Linux `cargo check` 替代：

- 干净 Windows 用户目录中的真实 GUI 启动与 sidecar handshake；
- 文件选择器、输入目录 allowlist、输出目录打开、窗口关闭、取消和完成产物；
- Defender/SmartScreen、路径空格、反斜杠、非 ASCII 用户目录和无 Codex 登录错误显示；
- 签名/SBOM、Linux 目标机实际 smoke、Windows/Linux 正式 portable 发布验收和跨平台资源审计。

- Linux/WSL 已完成 React/Vitest、Vite build、Python contract tests、协议测试、Rust 静态检查、bundle audit、Linux `.deb`/AppImage 构建和 sidecar 清理验证；这些结果不能标记 Windows 验收为完成，也不能替代目标 Linux 机器 smoke test。


验收：GUI 不直接导入 BabelDOC；前端不执行系统 Python 或任意 shell；翻译期间界面不冻结；Windows 和 Linux 最小 GUI 可运行；sidecar 只允许固定二进制和受控参数。

### Phase 9：GUI Alpha 与 Windows/Linux 打包

**优先级：P1 | 复杂度：XL | 预计：8–15 个开发日**

**状态：Windows unsigned NSIS/MSI bundle、Linux `.deb`/AppImage bundle、包内 sidecar smoke 和 Linux/WSL GUI Alpha 编辑能力已完成；正式 portable/clean-user GUI 验收、签名/SBOM、目标机 smoke 和发布审计待完成（2026 年 9 月 9 日）**

**执行节奏：** 本计划默认在 Linux 连续完成所有不依赖 Windows 结果的同范围开发项，并执行 Linux 验证；每个 Windows-only 事项累计登记到 `docs/validation/windows.md` 的 Windows Validation Queue。只有 `WINDOWS_VERIFICATION_BLOCKING`、无法从代码/文档可靠判断的关键 Windows 假设，或用户明确要求时，才在开发中提前进入 Windows 验证。当前批次结束后，以最终 diff 合并生成一次集中 Windows 验证计划，而不是按每个 feature 单独切换平台。

任务：

- AppShell、左侧导航和页面路由
- 新建翻译页：文件拖放、语言选择、单语/双语选项
- 任务中心、任务详情、完成结果和产物卡片
- Codex/BabelDOC/sidecar 环境检查
- 任务列表、阶段时间线、进度、取消、错误、输出目录
- glossary 选择、global/document 术语编辑和文档 context 分区设置页面
- 暖纸张/墨水蓝视觉主题已调整为白色主色调的 Vercel 风格设计方向（PLANNED，2026 年 9 月 10 日）：白底、黑白灰层级、黑色主按钮、语义色仅用于状态表达；移除远程 Google Fonts，改用本地/系统字体栈；重构 New Translation、Jobs、Job Details、Glossary/Context、Diagnostics/Settings 页面；并与交互真实性修复（真实语言控件、真实 stage 进度、glossary 稳定 key、Queue 防重、connection/feedback 分离）放在同一实施切片，见下方 Phase 9B。
- Windows portable bundle
- Linux portable bundle 或 AppImage
- sidecar target triple 和资源清单
- GitHub Release workflow、SBOM 和 SHA-256 checksums

Windows 专属执行清单：

1. [已完成，未签名] 在 Windows 原生环境构建当前源 GUI 与 `babelcodex-service.exe`；
2. [已完成] 使用当前源 Tauri target-triple sidecar 执行 NSIS/MSI `tauri build`，并记录最新 bundle/sidecar SHA-256；
3. [已完成，交互待验] MSI 已隔离解包并完成包内 sidecar smoke 与 GUI 进程级启动；干净用户环境安装/解压运行仍待完成；
4. [部分完成] 已验证 JSONL handshake、sidecar 退出、GUI 进程级启动和源级 GUI 测试；文件选择、allowlist、进度、取消、完成产物、重连和诊断 UI 的真实 packaged 交互仍待完成；
5. [已完成，交互待验] 当前源 bundle audit、MSI 解包内容和包内 sidecar 哈希一致性已通过；完整 clean-user、路径/权限和敏感内容验收仍待完成；
6. [部分完成，未签名] 已生成最新 bundle/sidecar SHA-256 和构建记录；SBOM、签名和正式发布附件仍待完成。

Windows 验收依赖原生 Windows GUI 运行结果；Linux 或 WSL 上的同名构建、Rust `cargo check` 和浏览器端测试只能作为先决检查。
Windows 本轮执行记录与边界（2026 年 9 月 8 日）：

- 本次 E 盘复核中，完整 uv run pytest -q 两次均在 test_cancel_uses_the_active_job_handle 失败：一次超时后仍为 RUNNING，一次因 Windows os.replace 返回 PermissionError: [WinError 5] 而为 FAILED；单独重跑一次通过，故 Python 全套质量门禁暂记为部分通过，需修复取消/状态持久化时序后复验。
- 已针对该 Windows 回归增加 StateStore 保存锁、短暂 `PermissionError` 退避重试和 10 秒 terminal 状态轮询测试；Windows 原生完整 pytest 仍需重新复验。
- Linux 侧修复后完整 pytest 已通过（123 passed，3 deselected）；该结果验证跨平台代码路径，但不能替代 Windows 原生复验。新增 glossary/context/thread state、Codex compact、GUI glossary/context editor 和本轮 Windows follow-up 修复后的最终 Linux/WSL 结果为 144 passed，3 deselected。

- 已处理的验证错误：相对路径排除参数导致首次同步未完整排除生成目录；Tauri 首次 bundle 缺少 icons/icon.ico；PyInstaller 直接模块入口触发相对导入错误；旧 bundle 中 sidecar 过期；sidecar 从解包目录启动时未显式传入配置导致 FileNotFoundError；以及一次 PowerShell args 参数转发错误导致 uv 只显示帮助。上述问题均已通过绝对排除路径、生成构建图标、临时包级入口、限定范围清理/重建、项目根目录加受控 --config 和显式命令调用处理。
- 未执行完整桌面 GUI 交互、干净用户目录、Defender/SmartScreen、签名/SBOM、正式 portable 发布审计和目标 Linux 机器 smoke；原因分别是本轮只覆盖自动化测试/协议 smoke/进程级启动、仍依赖项目根配置、使用 unsigned 开发包、尚未进入发布审计流程，以及 WSL/Linux 不能代表目标 Linux 机器。
- 文档与 Linux bundle 脚本同步后未重复 Windows NSIS/MSI 构建，因为本轮没有 Windows GUI/Rust/sidecar 源代码变化；已复核现有 bundle 哈希、包内 sidecar JSONL smoke 和 cargo check。
- 2026-09-09 针对最新 Linux commit 的 Windows 复验：uv sync、uv lock、Ruff、doctor、GUI Vitest（17 tests）、Vite build、cargo check 和当前源码 sidecar JSONL smoke 通过；完整 pytest 为 2 failed、138 passed、3 deselected（Windows TOML 路径 fixture 与 cleanup 的 WinError 32），最新 packaged sidecar 重建因 PyInstaller 环境阻塞，故当前状态为 WINDOWS_VERIFICATION_PENDING。
- 2026-09-09 重新同步同一最新 Linux commit 后复验：uv sync/lock、Ruff、doctor、GUI Vitest（17 tests）、Vite build、cargo check 和当前源码 sidecar JSONL smoke 通过；CLI 测试 5 passed，MCP 测试 10 passed、1 failed（cleanup 的 WinError 32），全量测试观察到 1 个失败且本次运行未返回最终摘要；此前 TOML Windows 路径失败未再现。当前源码 packaged sidecar 重建仍 BLOCKED，整体继续为 WINDOWS_VERIFICATION_PENDING。
- Linux follow-up after that Windows run：MCP cleanup 现在在删除 job-owned worker 目录前检查当前 MCP future 是否仍未完成；若仍 active 则返回 active-job 错误，避免持久化 terminal 状态与实际 worker 文件句柄释放竞态。另已处理 Future 完成回调与映射登记之间的竞态，并新增确定性回归测试。Linux 全量 pytest 为 144 passed，3 deselected。
- 2026-09-09 针对上述最新 Linux MCP 生命周期修复重新同步并执行 Windows 复验：CLI/MCP 重点回归 18 passed，Python 全量 144 passed、3 deselected，GUI 17 tests、Vite build、cargo check、doctor 和当前源码 sidecar JSONL smoke 均通过；MCP lifecycle/cleanup 与完整 Python 门禁为 `WINDOWS_PASS`。当前源码 sidecar/package 重建仍因缺少可用 Python 3.11 打包入口而 `WINDOWS_BLOCKED`，打包 GUI、干净用户和发布审计继续待执行。


- 2026-09-09 再次针对同一最新 Linux 工作树执行 Windows 复验：uv sync/lock、Ruff、doctor、Python 全量 144 passed、3 deselected、CLI/MCP 18 passed、GUI 17 tests、Vite build、cargo check 和当前源码 sidecar smoke 均通过；首次并行 GUI 调用因 npm ci 重装 node_modules 产生的临时错误已通过顺序重跑排除。当前源码打包仍 BLOCKED，整体保持 WINDOWS_VERIFICATION_PENDING。
- Linux 侧针对 Windows 打包阻塞补充的受控构建路径（2026-09-09）：新增 `scripts/babelcodex-service.spec`（平台无关 PyInstaller spec，含 BabelDOC/openai-codex hidden imports 与数据收集）、正式顶层入口 `scripts/sidecar_entry.py`（替代此前未保留的临时包级入口），并在 `worker_client.py` 新增 `worker_command()`：冻结（PyInstaller）exe 通过 `--worker-request` 分派 BabelDOC worker 子进程，避免打包二进制内执行 `python -m`；`sidecar.main()` 同步识别该参数。对应回归测试在 `tests/test_worker.py::TestWorkerCommand`。Linux 全量 pytest 为 147 passed、3 deselected，Ruff/format/compileall/spec 语法检查通过；上述内容为 `WINDOWS_VERIFICATION_PENDING`，需在 Windows 用真实 PyInstaller 产物复验后才可标记打包相关项为 PASS。
- Linux 端的受控 sidecar 打包验证（2026-09-09）：使用与 Windows 验证一致的 PyInstaller 6.22.2 从 `scripts/babelcodex-service.spec` 成功构建 Linux sidecar（约 218 MB），打包产物通过 JSONL `list_jobs`/`list_glossary`/`shutdown` smoke 与冻结环境 `--worker-request` 分派验证（缺失请求文件时返回协议化 WORKER_REQUEST_INVALID、exit 2，未出现 argparse/分派错误）。此项验证 spec 结构、hidden imports 和数据收集在 Linux 可复现构建中有效，属于 `LINUX_VERIFIED`；Windows target-triple exe、打包 GUI 与 installer 仍需 Windows 原生执行，保持 `WINDOWS_VERIFICATION_PENDING`。

- 2026-09-09 Windows current-source packaging 复验：PyInstaller spec/冻结 sidecar 构建、JSONL list_jobs、--worker-request 结构化错误路径、target-triple sidecar smoke、bundle audit 和 NSIS bundle 均通过；完整 Python 147 passed、3 deselected，GUI 17 tests、Vite、Tauri、doctor 均通过。NSIS/MSI 联合构建在 MSI 阶段因缺少 `.ico` 图标失败，旧 MSI 未作为证据，打包 GUI/干净用户/发布审计仍待完成，当前为 WINDOWS_VERIFICATION_PENDING。

- 2026-09-09 针对最新 Linux 工作树（含 icon.ico 配置修复）的 Windows 复验：当前源码 NSIS（`D653629B...`）与 MSI（`4E885B1E...`，195,715,072 bytes）构建均已通过；首次 MSI 失败仅因 E 盘副本 `tauri.conf.json` 未同步到含 `icon.ico` 的版本，补齐单向同步并核对哈希后通过，旧 MSI 未作为证据。Python 全量 147 passed、GUI 17 tests、Vite、Tauri、doctor、冻结 sidecar/target-triple smoke、bundle audit 均为 WINDOWS_PASS；MSI 图标修复在 Linux 为 LINUX_VERIFIED、在 Windows 为 WINDOWS_PASS；packaged GUI 交互/干净用户/发布审计仍为 NOT RUN，整体保持 WINDOWS_VERIFICATION_PENDING。

- 2026-09-09 Linux 本轮和解（reconciliation）：上述 Windows 复验结果已作为新事实输入；Linux 侧无新的失败或 BLOCKED 需要修复，因此本轮不新增或修改业务代码。Linux 复验：`uv run pytest -q` 为 `147 passed, 3 deselected`，Ruff lint/format 通过，Python compileall 通过，GUI `17 passed`、`npm run build` 通过、`npm audit --omit=dev` 为 0 vulnerabilities，`doctor` 在未登录 Codex 状态下按预期返回未认证信息；`.ico` 七尺寸与 tauri 配置解析仍有效。仍需 Windows 原生执行的项目继续标记为 `WINDOWS_VERIFICATION_PENDING` 或 `NOT RUN`，不得提前标记为 `WINDOWS_PASS`：当前 NSIS/MSI packaged sidecar smoke、packaged GUI 交互、干净用户、取消/重连、Windows 路径/权限矩阵、Defender/SmartScreen、签名/SBOM/release 审计，以及需授权的真实 Codex/PDF 集成。

- 2026-09-09 本轮和解（latest state-read hardening）：Windows 复验在包含读加固的同步工作树上执行完整 pytest（150 passed、3 deselected），瞬时 `PermissionError` 未复现；state 读加固与其回归测试升级为 `WINDOWS_PASS`，此前的间歇性 FAIL 观察作为历史记录移除（历史条目保留、不改写）。同轮 NSIS（`8D022FEE...`，195,746,324 bytes）与 MSI（`D1F56078...`，195,715,072 bytes）基于重建后的 sidecar（`FF3555AE...`）重新生成并记录哈希，解包 GUI 进程级启动 smoke 通过。Linux 侧无新失败或 BLOCKED，未修改业务代码。剩余待办为已安装 NSIS/MSI 的 packaged sidecar smoke、packaged GUI 交互、干净用户、取消/重连、Windows 路径/权限矩阵、Defender/SmartScreen、签名/SBOM/release 审计（`NOT RUN`），以及 npm advisories 独立评审和需授权的真实 Codex/PDF 集成。

- 2026-09-09 本轮和解（repeat confirmation, no source delta）：Windows 侧对同一工作树（HEAD `7ba4ddf` + 未提交改动，`state.py`/`test_state.py`/spec/Tauri 配置/图标哈希匹配）执行重复确认，所有已执行检查再次 `WINDOWS_PASS`（Python 150 passed、GUI 17 tests、Vite、Tauri、PyInstaller/冻结 sidecar/target-triple smoke、bundle audit、NSIS `8D022FEE...`、MSI `D1F56078...`、解包 GUI 启动 smoke），结果与上一轮一致，无新失败或 BLOCKED。Linux 侧无需任何代码或配置修改：Plan 关键路径已收敛为纯 Windows/发布流程执行项——已安装 NSIS/MSI 的 packaged sidecar smoke、packaged GUI 交互、干净用户、取消/重连、Windows 路径/权限矩阵、Defender/SmartScreen、签名/SBOM/release 审计（均 `NOT RUN`），npm advisories 独立评审，以及需授权的真实 Codex/PDF 集成；Phase 12/13 等后续功能阶段在验证结果中仍无提前启动依据。整体保持 `WINDOWS_VERIFICATION_PENDING`。

- 2026-09-09 本轮和解（bundle-audit URL false positive）：Windows 当前源码复验中 `scripts/check_gui_bundle.py` 把生成的 JS/CSS 里的普通 `https://` 字符串误判为开发机绝对路径（`s://` 命中裸 `[A-Za-z]:[\\/]`），该 audit 项记为 `WINDOWS_FAIL`（验证脚本缺陷，非产物路径泄漏证据）。Linux 侧已修复：新增 `contains_development_machine_absolute_path()`（先剥离 `scheme://authority` 再匹配 + 负向后顾防御），`file:///home/...` 与 `file:///C:/...` 仍可检出；新增 `tests/test_check_gui_bundle.py` 7 个回归测试；用真实 Vite 产物（含此前触发 FAIL 的 `index-BRF5O_XD.js`/`index-Ciks3U42.css`）在 Linux 复跑 audit 通过。Linux 复验：`uv run pytest -q` 为 `157 passed, 3 deselected`，Ruff lint/format、compileall、GUI 17 tests 通过。该修复为 `LINUX_VERIFIED` + `WINDOWS_VERIFICATION_PENDING`：audit 项仅可在 Windows 用修复后脚本重跑通过后才可从 `WINDOWS_FAIL` 转为 `WINDOWS_PASS`；packaged GUI 交互/干净用户、取消/重连、路径权限矩阵、Defender/SmartScreen、签名/SBOM/release 审计仍为 `NOT RUN`。整体保持 `WINDOWS_VERIFICATION_PENDING`。

首期不承诺所有 Linux 发行版原生安装包，也不优先采用单文件 executable。

GUI 页面信息架构：

```text
新建翻译
任务
术语表
诊断
设置
```

GUI 必须通过 Application Service 访问任务；Tauri Rust 层只负责窗口、文件对话框、受控 sidecar、协议转发和权限，不实现 PDF 翻译。

当前 GUI Alpha 切片记录（2026 年 9 月 9 日）：

- 已新增集中式 `JobStore`，统一管理 sidecar 启动、关闭、任务列表同步、事件游标和轮询；
- 已实现 `start_translation`、`list_jobs`、`poll_events`、`get_job`、`cancel_job` 的前端 contract；
- 新建翻译页已接入受控 PDF 文件选择：Tauri 使用 dialog plugin，浏览器使用原生 file input/drag-and-drop fallback，并在 GUI 边界拒绝非 PDF；
- Jobs 页面已支持通过 `get_job` 打开详情，展示状态、阶段、尝试次数、时间、QA 状态和 sidecar 返回的 artifact 元数据；
- 任务详情页已增加阶段时间线，并通过可清理的 `JobStore.watchJob` 周期刷新选中任务；
- sidecar 断线后进入 reconnect 状态，重连时重置事件游标，并使用 `list_jobs` 与活动任务 `get_job` 做状态校准；
- 已覆盖 GUI 初始连接、任务创建、事件应用、取消、重连校准和 cleanup 测试；
- 已完成一轮 Windows 原生 packaged 验证：Windows target-triple sidecar、NSIS/MSI bundle、MSI 隔离解包后的 sidecar JSONL smoke 和解包 GUI 进程级启动检查均通过；Tauri 文件选择、任务详情、阶段时间线和详情自动刷新已接入；
- GUI 已采用本地 shadcn/ui 风格组件层：`Button`、`Card`、`Badge` 和 `Progress`，使用语义化 variants、CSS variables、focus ring 和可访问 progressbar；未新增 Radix/Tailwind 依赖，也未改变 sidecar/Tauri 权限边界；
- 已完成 GUI 任务详情结果摘要、artifact SHA-256 展示、手动刷新和 sidecar 指数退避重连；
- 已增加跨平台 GUI bundle 审计脚本：校验 target-triple sidecar、拒绝用户状态/凭据/缓存/开发目录和疑似机器绝对路径，并生成 SHA-256 manifest；GitHub Actions 已加入 Linux GUI test/build job；
- 已增加跨平台 GUI bundle 审计脚本、Linux bundle 构建脚本、512×512 方形 Tauri 图标和 Linux CI GUI test/build job；
- 已完成 Linux `.deb`/AppImage bundle、512×512 方形图标、bundle audit、Linux bundle 构建脚本和 Linux CI GUI test/build job；
- 已完成 GUI Glossary 页面：通过 `JobStore` 调用 scoped sidecar API，支持 global/document glossary、enabled/notes、增删保存、版本显示和 document stem 校验；
- 已完成 document context 编辑：通过同一 sidecar API 加载/保存 UTF-8 context sidecar，并显示服务端返回的 bounded parser/version 结果；
- Linux/WSL 侧已通过 sidecar/Application Service contract 补齐 GUI 任务详情、显式 retry、artifact validation 和 PDF QA；GUI 只接收脱敏后的 artifact 文件名，不暴露本地绝对路径，也不提供任意路径打开或 shell 操作。尚未完成完整 GUI packaged 交互 E2E、干净用户环境验收、输入/输出 allowlist 与 Windows 路径矩阵、sidecar 自身重启编排、Linux 目标机 smoke、签名/SBOM 和正式发布验收；这些继续保留在 Windows/目标平台验证清单。
- Linux/WSL 可完成的 glossary/context 基础接入与编辑页面已完成；剩余 packaged 交互、目标机运行、签名/SBOM 和正式发布验收继续保留在 Windows/目标平台清单中。

#### Phase 9B：白色 Vercel 风格 GUI 设计与中文排版重构（LINUX_VERIFIED，2026 年 9 月 10 日；Windows 原生交互仍为 WINDOWS_VERIFICATION_PENDING）

**设计原则：**

- 主背景为白色/近白色，主文字接近黑色；卡片白底、细灰边框；主操作为黑色实心按钮，次操作为白底细边框按钮；
- 参考 Vercel 产品界面原则（高信息密度、黑白灰层级、细边框、克制圆角、低阴影、清晰主操作优先级），不照搬其品牌；
- 状态色仅表达语义（成功/警告/错误/信息），且不只依赖颜色区分状态，同时保留文本、图标或 badge；
- 深色模式不在本轮强制实施，但 token 必须使用语义命名，为未来 dark theme 保留扩展能力。

**Token 与主题基础：**

建立语义化 token（`--background`、`--foreground`、`--muted`、`--muted-foreground`、`--border`、`--surface`、`--surface-hover`、`--primary`、`--primary-foreground`、`--secondary`、`--secondary-foreground`、`--success`、`--warning`、`--destructive`、`--focus-ring`），正文与背景至少满足 WCAG AA 4.5:1。

**字体与跨平台策略：**

移除远程 Google Fonts 导入（当前 packaged Tauri CSP 不允许该远程字体路径，且与本地优先/离线目标冲突），改用系统字体栈，等宽字体仅用于 Job ID、文件 hash、文件路径和 protocol/version 字段。

**页面重构范围：**

- App Shell/导航：保留固定左 rail，转为白底 + 右侧细边框 + 浅灰活动背景；不得继续依赖 `body { min-width: 1080px; }` 防止布局压缩；支持窄桌面/高 DPI 紧凑布局；
- New Translation：去除大 hero 和伪数据指标，改为任务优先界面；From/To 必须为真实控件或明确只读摘要；Queue 按钮请求中必须 disabled 并显示 `Queuing…`；表单错误在字段附近显示；
- Jobs：目标为高信息密度任务列表；移除固定 68%/22% 确定型进度（无真实 percentage 时用 indeterminate progress 或 stage label）；空状态提供可执行 CTA；
- Job Details：改为任务排查导向的双栏信息工作台，突出输出文件和下一步操作，错误态展示安全错误消息、错误类别和可恢复操作；
- Glossary/Context：使用真实 segmented control/radio/tabs 语义并增加 `aria-pressed`/`aria-selected`；输入字体不低于 14px；保存状态明确区分 Saved/Saving/Unsaved/Failed；
- Diagnostics：避免硬编码结论，改用 sidecar/Application Service 返回的实际检查结果（含重新检查动作）；
- Settings：当前只读内容如不实现真实设置，应改名为 `Configuration`/`Runtime` 并明确由 `config.toml` 管理。

**同一实施切片必须包含的交互真实性修复：**

真实语言控件、真实 stage 进度、glossary 稳定 client ID、Queue 防重、connection state 与 operation feedback 解耦、字段错误关联、`role="status"`/`role="alert"` live region、焦点管理、reduced-motion 支持。

**验证要求：**

Linux 侧执行 Vitest、Vite build、axe/keyboard/overflow/reduced-motion 探针和截图矩阵；Windows packaged 侧（NSIS/MSI、DPI 125/150/200%、NVDA/键盘、文件选择、路径、取消、重连、干净用户）继续标记为 `WINDOWS_VERIFICATION_PENDING`，仅在实际通过后改为 `WINDOWS_PASS`。

- 2026-09-10 计划和解：

- Windows 最新验证中暴露的重复 `mock-job-1` 行属于共享 GUI 状态同步问题。Linux 已让 `JobStore.applyEvent()` 对重复/重放的 `job_created` 事件幂等：已存在的 `job_id` 原位合并并保留更丰富状态，未知任务才插入；新增回归测试覆盖 `list_jobs` 后重放事件的单任务不变量。
- 详情页已将 `Job details` 设为实际可访问 heading，job ID 作为独立元数据显示，修复了 Linux 测试与 UI 语义不一致的问题。
- Linux 验证：GUI Vitest `3 files, 19 tests passed`；Vite/TypeScript build 通过；Python `157 passed, 3 deselected`；Ruff format/check、compileall、`git diff --check` 通过。
- 该修复先在 Linux 标记为 `LINUX_VERIFIED`，随后已在最新 Windows working-tree revalidation 中通过 GUI 19-test suite，因此当前该修复为 `WINDOWS_PASS`；后续 Linux 修复仍必须遵守“先 Linux 验证、再 Windows re-validation”的状态流转，不得仅凭 Linux 结果标记 Windows PASS。
- Windows `doctor()` 的 `babeldoc_cli = null` 与 PyInstaller 环境缺失属于此前验证轮次的历史问题；最新 Windows revalidation 已通过 doctor 和当前源 PyInstaller。当前仍未完成的 packaged GUI 交互、clean-user、NVDA、DPI、签名/SBOM 和 release 检查继续保持 `WINDOWS_VERIFICATION_PENDING` 或 `NOT RUN`。
- 中文重排后的 Linux 验证：GUI Vitest `3 files, 19 tests passed`；Vite/TypeScript build 通过；Python `157 passed, 3 deselected`；Ruff format/check、compileall 和 Linux bundle audit 通过。最新 Windows current UI revalidation 已通过 GUI 19-test suite、当前源构建和包级 smoke，因此这些已执行项目为 `WINDOWS_PASS`；真实 packaged 中文显示、键盘/DPI/NVDA、文件选择、取消/重连、clean-user、路径权限、签名/SBOM 和 release audit 仍保持 `WINDOWS_VERIFICATION_PENDING` 或 `NOT RUN`。

**建议实施顺序：**

Phase 9A（交互真实性与状态模型）→ Phase 9B（白色设计系统与页面重排）→ Phase 9C（无障碍与适配）→ Phase 9D（Linux/Windows 验证）。

### Phase 10：Codex MCP Server Alpha

**优先级：P1 | 复杂度：L | 预计：5–10 个开发日**

**状态：已完成标准库 stdio MCP contract、scoped tools、严格参数校验、安全路径校验、MCP 取消 wiring 和 contract tests；Codex 客户端注册、目标环境 smoke、真实 Codex 翻译和发布审计仍待完成（2026 年 9 月 8 日）**

任务：

1. 实现本地 stdio MCP Server
2. 增加 `babelcodex_doctor`
3. 增加 `babelcodex_start_translation`
4. 增加 `babelcodex_get_job`
5. 增加 `babelcodex_list_jobs`
6. 增加 `babelcodex_cancel_job`
7. 增加 `babelcodex_validate_output`
8. 增加 `babelcodex_cleanup_job`
9. 实施输入/输出路径 allowlist
10. 禁止任意 shell、任意文件读取和任意路径删除
11. 防止内层 Codex thread 递归调用 BabelCodex MCP
12. 编写 MCP contract tests 和 Codex 注册文档

长任务必须采用异步 job 模式：启动工具返回 `job_id`，后续查询进度和产物。

验收：

- Codex 可以发现 BabelCodex MCP tools
- 可以启动、查询、取消和校验 PDF 翻译任务
- 输出路径受 allowlist 约束
- 不存在 MCP 递归调用
- 不提供任意 shell 执行

MCP 与 GUI 共用 Python Application Service、JobState、事件和错误码；GUI 的 Tauri sidecar 不得成为 MCP 的第二套编排实现。

当前实现记录：

- `babelcodex mcp serve` 通过 newline-delimited JSON-RPC 提供 MCP initialize、tools/list、tools/call 和 initialized notification；
- `babelcodex_doctor`、`babelcodex_start_translation`、`babelcodex_get_job`、`babelcodex_list_jobs`、`babelcodex_cancel_job`、`babelcodex_validate_output`、`babelcodex_cleanup_job` 已定义为受限 tools；
- MCP start 使用异步 executor 并立即返回持久化 `job_id`；状态和 artifact 仍由 Application Service/StateStore 提供；
- validate 只允许配置 output directory 下的 job artifacts，重新计算大小和 SHA-256，并进行 PDF magic-header 检查；cleanup 只允许删除配置 worker directory 下的 terminal job-owned 工作目录；
- 任意 shell、任意文件读取、任意路径删除和 Codex MCP 递归调用均未暴露；MCP cancel 使用进程内 `cancel_event`，服务关闭时主动通知活动 job 并清理句柄。
- `docs/mcp.md` 已记录 stdio 启动、客户端注册、工具边界和限制。
- MCP contract tests 当前覆盖 initialize/tools discovery、stdio parse error、异步 start、completed skip、取消、输出 allowlist、cleanup、严格参数和非对象请求。

### Phase 11：Glossary 与文档上下文

**优先级：P2 | 复杂度：L | 预计：5–8 个开发日**

**状态：已完成 Linux/WSL 可验证的 glossary/context、thread identity、compact contract 和 GUI 编辑页面；真实 Codex 账户行为、长文档 benchmark、packaged GUI 交互及 Windows-only 验收仍待完成（2026 年 9 月 9 日）**

任务：

1. CSV 导入导出
2. 文档级 glossary
3. glossary version
4. 标题/摘要提取
5. 初始上下文 prime
6. 术语一致性检查
7. Codex thread ID 持久化
8. thread 恢复
9. thread 轮换
10. 上下文压缩

验收：

- glossary 中强制术语稳定出现
- thread 重启后术语保持
- glossary 变化不会错误命中缓存
- 上下文不会无限增长

当前非 Windows 完成记录：

- 配置新增 `project.glossary_dir`、`project.context_dir`、`codex.context_max_chars` 和 `codex.max_turns_before_compact`；
- glossary 支持 `global.csv` 与 `documents/<document-stem>.csv`，文档级条目覆盖全局同名条目；
- glossary 支持 CSV 导入/导出、稳定版本 hash、enabled 标志、notes 和有上限的 terminology prompt；
- context 支持 UTF-8 文本 sidecar 的标题/摘要提取、空白归一化、边界截断和稳定版本 hash；
- `babelcodex glossary list|import|export` 已提供本地 CLI 管理入口；
- glossary/context prompt 与版本已接入 in-process/subprocess 共用的 `TranslatorSpec`、TranslationGateway cache key 和 Codex thread prime；
- PDF metadata/opening-page context adapter、provider-neutral `ThreadStateStore`、官方 SDK `thread_resume` 接入和成功 prime 后持久化已完成；
- compact 策略已接入：配置开启后优先调用官方 SDK `Thread.compact()`，不支持或失败时回退到新 thread + prime + state rotation；默认仍关闭；
- GUI Glossary 页面已通过 scoped sidecar API 支持 global/document glossary、enabled/notes、增删保存，以及 document context sidecar 编辑和保存；
- contract tests 已覆盖覆盖规则、导入导出、禁用术语、长度边界、文本/PDF context 提取、版本隔离、thread state rotation、mocked thread resume/compact、失败回滚、worker protocol round-trip 和 GUI sidecar editor API。

仍需后续完成：真实 Codex 账户下的 thread resume/rotation/compact 行为验收、长文档稳定性 benchmark、真实 Codex-plan integration，以及 packaged/clean-profile GUI 编辑交互验收；这些不应通过单元测试伪造或消耗默认测试额度。

### Phase 12：恢复、Part 与任务运维

**优先级：P3 | 复杂度：L | 预计：5–8 个开发日；artifact manifest、CLI 运维入口、安全完成跳过、保守 worker crash recovery、错误分类 retry policy、pipeline 元数据/part-resume 评估及 cleanup/保留策略均已完成 Linux 验证（2026 年 9 月 10 日）**

任务：

1. 扩展 `inspect`
2. 扩展 `retry`
3. 错误分类重试
4. worker crash 恢复
5. artifact manifest
6. BabelDOC part 信息记录
7. 评估 part-level resume
8. cleanup policy
9. 保留失败工作目录
10. 完成任务安全跳过

验收：

- 认证错误不会自动循环
- worker 崩溃可以明确恢复或终止
- 已完成任务可验证后跳过
- 输出丢失时不会仅依赖 `status=completed` 跳过
- 所有产物有哈希

当前 Linux/WSL 完成记录：

- 新增共享 artifact manifest 校验：仅接受已持久化且位于配置 output directory 内的 artifact，流式重算大小和 SHA-256，并对 PDF 执行 magic-header 检查；已持久化 hash 不匹配会被识别为篡改，不能静默覆盖；
- in-process legacy compatibility facade 现保留标准 `PdfTranslateResult`，使其 artifact 列表与 subprocess worker 结果在 Orchestrator 中使用同一 manifest 路径；worker protocol 中未携带 hash 的 artifact 由主进程首次验证后持久化；
- `status=completed` 只会在 manifest 完整验证通过时返回 `skipped`。输出缺失、路径越界、PDF header 异常或 hash 不匹配时，任务会恢复为新的可执行尝试（重置 attempts），而不是仅依赖旧状态跳过；
- Application Service 新增 `inspect_job`、`validate_output`、`retry_job`；CLI 已提供 `babelcodex inspect <job-id>`、`babelcodex validate <job-id>`、`babelcodex retry <job-id>`，MCP `babelcodex_validate_output` 复用同一验证规则；
- 每次执行在 persisted job state 中写入 `runner_pid`；新建 Orchestrator 时扫描遗留 `RUNNING` / `RETRY_PENDING` job。runner PID 缺失或已死亡时，状态会被保守地终止为 `FAILED`、`ErrorCategory.WORKER` / `WORKER_CRASHED`，并要求用户使用显式 `retry` 开始新尝试；不会自动重跑或消耗 Codex 用量。PID 仍存活的任务保持不变，避免 CLI、GUI sidecar 和 MCP 进程互相误判活动任务；
- 错误分类 retry policy：`core.errors.DEFAULT_RETRY_LIMITS` 定义每类别默认尝试上限，`[translation] retry_policy` 可操作员覆盖；全局 `max_retries` 仍是总尝试次数的上限，类别策略只能降低它。认证/配置/输入/验证/输出类默认 1 次、不自动循环（验收项），翻译/资源类有界重试；失败日志与持久化状态记录 category、code 与 `retry_limit/max_retries`；
- BabelDOC part 元数据与 resume 可行性：每次执行把 `pipeline_meta`（backend、babeldoc_version、source_page_count、`part_resume_supported=False`、note）持久化到 JobState，`babelcodex inspect` 直接可见；结论：0.6.x 高层单遍流水线 `SplitManager` 仅用于可选的复杂度估算、无稳定 part 级产物，part-level resume 不采用（ADR-026），恢复语义由显式 retry + 类别重试提供；
- cleanup/保留策略：`[babeldoc] work_retention_days`（默认 7 天）控制终态 job 工作目录保留期，0 表示终态立即清理；`babelcodex cleanup [--dry-run]` 走 Application Service 共享逻辑，活动 job 永不清理；路径安全规则与 Windows 瞬时锁重试共享于 `core.workdir`，MCP `babelcodex_cleanup_job` 一并复用（ADR-027）；
- Linux 验证：`uv run pytest -q` 为 179 passed、4 deselected；`uv run pytest -q -m integration tests/test_e2e_mock.py` 为 4 passed；`uv run ruff check .`、`uv run ruff format --check .`、`python -m compileall -q src` 和 `git diff --check` 均通过。

仍需后续完成：真实 Codex 账户下的 retry/compact/thread resume 行为验收、长文档稳定性 benchmark 和 packaged/clean-user Windows sidecar 回归。Windows 侧新增工作目录清理/锁定行为与类别重试观察并入 `WVQ-007`/`WVQ-003`/`WVQ-004`，保持 `WINDOWS_VERIFICATION_PENDING`，不阻塞 Linux 开发。

#### 2026 年 9 月 11 日追加：Windows 验证后续硬化（Linux 完成）

2026-09-11 Windows 全量验证（`4e709d9`，记录见 `docs/validation/windows.md`）完成后，基于验证事实在 Linux 侧追加以下工作：

- 依赖通告评估：`npm audit` 两条 moderate 通告均来自 `@vitest/mocker`（GHSA-82fw-gwwq-j7x9，redirect mock 路径遍历），仅影响 dev 工具链 vitest（2.1.0–4.1.10），不进入打包产物；修复需升级 vitest 5（破坏性大版本）。决策：暂缓大版本升级并在此记录，GUI 打包产物不受通告影响；esbuild 0.28.2 无已知通告；
- 陈旧 sidecar 防线（ADR-029）：Windows 验证中“陈旧 sidecar 打进安装包”的输入漂移暴露了结构性风险，追加两层防线——① `scripts/check_gui_bundle.py --source-tree` 静态新鲜度审计（校验打包内 sidecar 的 mtime 不早于其嵌入的 Python 源、`pyproject.toml` 与 PyInstaller spec）；② sidecar 新增 `get_server_info` 运行时握手（协议版本 + 包版本 + 能力列表），GUI 启动时执行握手，失败转为明确的连接错误而非任务中途协议失配；
- Linux 验证：`uv run pytest -q` 为 200 passed、5 deselected；GUI `npx vitest run` 为 22 passed；`npx tsc --noEmit`、`uv run ruff check .`、`uv run ruff format --check .` 均通过。新增打包侧/握手 Windows 观察并入 `WVQ-009`，保持 `WINDOWS_VERIFICATION_PENDING`。

- 归因修正（2026-09-11 dirty-tree 验证后）：该验证输入已包含 `tests/test_e2e_mock.py` resource-scope 修改，但 Windows harness 清理仍复现 `WinError 32`，因此该测试句柄修改仅是测试卫生改进，不是该清理失败的根因或修复。Linux 静态审查确认 QA 边界（`pdf_sanity`/`text_checks`/`layout_checks`）无生产句柄泄漏；`WinError 32` 候选根因位于 Windows 验证 harness 生命周期（未退出子进程、Defender/杀毒扫描或 `uv run` 包装进程在删除时仍持有 fixture 句柄），保持历史 `FAIL` 并归入 `WVQ-007` 原生重跑，不得由 Linux-only 改动转 PASS。
- 句柄生命周期硬化（2026-09-12 日志句柄观察后）：2026-09-12 重跑中失败的锁定对象从 fixture PDF 变为 QA CLI 自写的 `logs/cbpdf.log`——两轮不同 artifact、同一失败类，指向短命 CLI 退出后的句柄生命周期。据此在 CLI `main()` 增加 `finally` 释放路径：命令完成时显式摘除并关闭 root logger 的全部 `FileHandler`（`_release_log_file_handlers`），不再仅依赖 `logging.shutdown()` atexit 钩子；新增回归测试 `test_cli_releases_log_file_handlers_at_exit` 固定摘除与流关闭行为。Linux 门禁：pytest `201 passed, 5 deselected`、Ruff/format、GUI Vitest 与 `tsc --noEmit` 均通过。定性为句柄暴露窗口的缓解措施，不声明为 Windows 清理失败的修复；`WVQ-007` 保持 `WINDOWS_VERIFICATION_PENDING`，需 Windows 原生重跑确认。
- Windows 原生复验（2026-09-12 CLI/QA 改动重验）：包含上述硬化的源码已同步并在 Windows 原生重跑——此前失败的 QA harness 临时目录清理 `PASS`，`WinError 32` 未复现，本轮无 `FAIL`。Windows 侧明确限定：仅清除 QA harness 清理路径，不证明完整 `WVQ-007` work-dir/lock/retry/cancel/reconnect 矩阵；`WVQ-007` 保持 `WINDOWS_VERIFICATION_PENDING`。同轮 `WVQ-009` 的 stale bundle **负向审计**获得原生 PASS 证据（陈旧 sidecar 被以 `sidecar predates newer Python sources` 拒绝），但 stale-GUI 原生错误展示与原生 GUI 交互仍 `BLOCKED`（trusted RPC `sky` 不可用），MSI admin extraction 仍 `BLOCKED`（90 秒无输出无 payload），clean-user、`WVQ-005` 发布安全与 live Codex/PDF 仍 `NOT RUN`，整体保持 `WINDOWS_VERIFICATION_PENDING`。本轮 Linux 未做新代码改动：余下失败归属 Windows 环境观察项，投机性 Linux-only 改动不构成证据。


### Phase 13：PDF QA 与发布硬化

**优先级：P3 | 复杂度：L/XL | 预计：7–12 个开发日；L0/L1/L2、缺字与空白启发、越界、未翻译比例、QA JSON/人类报告、资源检查与发布操作文档已完成 Linux 验证（2026 年 9 月 10 日）**

任务：

1. L0 文件检查
2. L1 PDF 结构检查
3. L2 文本检查
4. 缺字检查
5. 越界启发式
6. 页面空白异常
7. 未翻译比例
8. 视觉回归
9. QA JSON
10. QA 人类可读报告
11. 资源和磁盘检查
12. 发布操作文档

验收：

- 输出异常不会被标记为完全成功
- fixture 有稳定 QA 基线
- 发布前可自动生成质量报告
- 失败报告不包含敏感全文

当前 Linux/WSL 完成记录：

- 新 `qa/` 模块：L0 文件（存在/大小/PDF header）与 L1 结构（可打开/加密/页数/逐页文本）在 `pdf_sanity.py`；L2 空白页、CJK 目标未翻译比例启发、源 PDF verbatim 相似度在 `text_checks.py`；文本 span 越界启发与采样页渲染空白（缺字）检查在 `layout_checks.py`；磁盘剩余空间/单文件大小上限在 `resource_checks.py`；报告组合、人类可读摘要（不渲染段落全文）与原子 QA JSON 写在 `report.py`；
- `babelcodex qa <job-id>`（服务 `run_qa`、MCP `babelcodex_run_qa`）对终态 job 的 mono/dual 产物执行全程检查，报告写入 `output_dir/qa/<stem>.<type>.qa.json` 并更新 `qa_status`；任何 `error` 级 finding 使 `qa_status=failed`，输出异常永不标记为完全成功；
- QA 报告不加入 `job.artifacts` manifest（避免污染内容完整性校验）；报告为摘要，finding 只含代码/严重度/页码/短 detail，不含段落原文（验收：失败报告不含敏感全文）；
- fixture 稳定基线：`test_mock_output_has_a_stable_qa_baseline` 锁定两栏夹具的 mock 输出必为 PASS 且可复现（`MAYBE_UNTRANSLATED` 为预期 warning 不阻断）；
- 发布操作文档：`docs/release.md`（门禁、doctor、QA 报告、sidecar/Tauri 构建、发布安全与收尾清单）；
- 视觉回归以渲染空白/非空白像素启发代替全量像素级黄金基线对比（ADR-028），全量视觉对比与缺字字体级检测留待后续；
- Linux 验证：`uv run pytest -q` 为 196 passed、4 deselected；`uv run pytest -q -m integration tests/test_e2e_mock.py` 为 5 passed；`uv run ruff check .`、`uv run ruff format --check .`、`python -m compileall -q src`、`git diff --check` 均通过。

仍需后续完成：全量像素级视觉回归与字体级缺字检测、打包产物上的 `babelcodex qa` 冒烟、真实 Codex 长文档输出 QA 阈值校准。Windows 渲染/字体行为并入 `WVQ-008`，保持 `WINDOWS_VERIFICATION_PENDING`。

### Phase 15：WDIO GUI E2E 基础设施（Linux 完成）

**优先级：P0 | 复杂度：M | 预计：3–5 个开发日（Linux 基础设施层）**

任务：

1. 安装 `@wdio/cli`、`@wdio/local-runner`、`@wdio/mocha-framework`、`@wdio/spec-reporter`、`@wdio/globals`、`@wdio/tauri-service`、`@wdio/tauri-plugin`、`cross-env`
2. 新增 `tauri-plugin-wdio` 和 `tauri-plugin-wdio-webdriver` 作为 optional Cargo 依赖
3. 新增 `e2e` 和 `mcp-dev` 两个独立 Cargo feature，互斥（编译期检查）
4. 拆分 capability：`main-capability`（生产）、`mcp-debug-capability`（MCP 开发）、`e2e-capability`（WDIO E2E）
5. 新增 `tauri.e2e.conf.json` 和 `tauri.mcp.conf.json` flavor 配置
6. 新增 `config/e2e.toml`（`translator = "mock"`），所有运行数据进入 `gui/build/e2e/`
7. 新增 `scripts/prepare-e2e.mjs`（workspace 准备）；capability flavor 注入改为内联于 `tauri.*.conf.json`，不再使用 `prepare-e2e-rust.mjs`
8. ~~新增 `scripts/capabilities/e2e.json` 和 `scripts/capabilities/mcp-debug.json` 模板~~ 未采用：flavor capability 直接内联于 `tauri.*.conf.json`（`CapabilityEntry::Inlined`）
9. 新增 `wdio.shared.conf.ts`、`wdio.browser.conf.ts`、`wdio.native.conf.ts`、`wdio.external.conf.ts`
10. 新增 `tests/e2e/browser/smoke.spec.ts`、`tests/e2e/browser/navigation.spec.ts`
11. 新增 `tests/e2e/native/smoke.spec.ts`
12. 新增 `tests/e2e/windows/paths.spec.ts`（Windows-only，Linux 自动 skip）
13. 前端条件加载 `@wdio/tauri-plugin`（仅 `VITE_E2E=1`）
14. 更新 `vitest.config.ts` 排除 `tests/e2e/`

验收：

- `npm ci` 可重建依赖
- `npm run e2e:browser` 是标准 renderer E2E 入口
- `npm run e2e:native` 是标准 native E2E 入口
- 测试不访问真实 Codex
- 测试不依赖用户配置、状态或 PDF
- 普通 Release 不包含 WDIO 插件
- 普通 Release 不包含 MCP Bridge listener
- MCP Debug 与 WDIO E2E 不能同时启用
- E2E capability 不进入普通构建
- sidecar 参数仍为固定 allowlist
- 测试结束后无 GUI/sidecar/worker 残留
- 失败时能保存足够日志和截图
- `data-testid` 只用于无法稳定语义定位的节点
- 文档 inventory 通过

当前 Linux/WSL 完成记录：

- 依赖安装：`@wdio/cli@9.31.9`、`@wdio/tauri-service@1.4.0`、`@wdio/tauri-plugin@1.4.0`、`cross-env@10.1.0` 等
- Cargo features：`default`、`mcp-dev`、`e2e` 三档，互斥检查生效
- Capability 拆分：`main-capability`（生产）、`mcp-debug-capability`（MCP）、`e2e-capability`（WDIO）
- Flavor configs：`tauri.conf.json`、`tauri.mcp.conf.json`、`tauri.e2e.conf.json`
- E2E config：`config/e2e.toml`（`translator = "mock"`）
- 前端条件加载：`import.meta.env.VITE_E2E === "1"` 时动态 import `@wdio/tauri-plugin`
- WDIO configs：`wdio.shared.conf.ts`、`wdio.browser.conf.ts`、`wdio.native.conf.ts`、`wdio.external.conf.ts`
- E2E specs：`tests/e2e/browser/smoke.spec.ts`、`tests/e2e/browser/navigation.spec.ts`、`tests/e2e/native/smoke.spec.ts`、`tests/e2e/windows/paths.spec.ts`
- npm 脚本：`e2e:prepare`、`e2e:build`、`e2e:browser`、`e2e:native`、`e2e:external`、`e2e`、`mcp:build`（移除 `tauri:prepare`/`mcp:prepare`，flavor capability 已内联）
- Linux 验证：
  - ✅ Vitest 28 tests 通过
  - ✅ TypeScript 编译通过
  - ✅ Cargo check (default / mcp-dev / e2e) 通过
  - ✅ MCP-dev + E2E 互斥检查生效
  - ✅ WDIO 配置文件与 E2E specs 已创建
  - ✅ 前端条件加载 `@wdio/tauri-plugin` 已实现
  - ✅ `config/e2e.toml` 无付费 mock 配置已创建
    - ✅ Capability flavor 注入机制已验证（`CapabilityEntry::Inlined` 直接嵌入 `tauri.*.conf.json`，不生成文件）
  - ❌ WDIO Browser mode BLOCKED：缺少 Chrome/Chromium
  - ✅ WDIO Native mode：4 spec files、15 tests 通过（embedded WebDriver + Linux desktop）

仍需后续完成：Linux Browser mode（当前 BLOCKED，缺少 Chrome/Chromedriver）；Windows 在同步 allowlist contract 修复后重新执行 `npm run e2e:native` 与 `tests/e2e/windows/*`；Computer Use 补充系统文件选择器、DPI、NVDA、安装器等场景。Windows 验证并入 `WVQ-017`，保持 `WINDOWS_VERIFICATION_PENDING`。

### Phase 14：实验性 Two-phase

**优先级：P4 | 复杂度：XL | 不纳入首个稳定版关键路径**

候选命令：

```bash
cbpdf extract document.pdf
cbpdf translate-manifest <job-id>
cbpdf render <job-id>
```

适用场景：

- 人工编辑译文
- 全文预扫描
- 离线翻译
- 外部 CAT 工具
- 研究型段落导出
- 需要完全独立的翻译生命周期

启用条件：

- BabelDOC 提供稳定 IL 或 hook contract
- extraction/render 顺序回归测试完善
- 有严格 segment alignment
- 性能收益或业务价值明确

## 4. 工作包依赖关系

```text
W-1 GitHub 公开仓库与本地同步
  → W0B 环境和依赖基线
  → W1 领域模型、错误和 Application Service
  → W2 占位符验证
  → W3 BabelDOC 兼容层
  → W4 Worker Process
  → W5 CLI MVP 与 Fixture/Codex E2E
  → W6 Translation Gateway 和批处理
  → W7 SQLite Cache
  → W8 GUI 技术验证
  → W9 GUI Alpha 与 Windows/Linux 打包
  → W10 Codex MCP Server Alpha
  → W11 Glossary 和 Context
  → W12 恢复和运维
  → W13 PDF QA 和发布硬化
  → W14 Two-phase 实验
```

可并行工作：

- W0B 完成后：占位符验证、状态模型、BabelDOC compatibility contract 可并行
- Worker 稳定后：fixture、PDF QA 基础、Codex smoke test 可并行
- Gateway 完成后：cache、GUI 技术验证、benchmark 可并行
- GUI Application Service 稳定后：GUI Alpha 和 MCP Server 可并行
- GUI sidecar protocol 稳定后：GUI Alpha、MCP Server 和 GUI E2E 可并行

## 5. 里程碑

### M-1：Public Repository Baseline

**状态：已完成（2026 年 9 月 8 日）**

- 产品名确定为 BabelCodex
- 创建公开仓库 `15699122/BabelCodex`
- 首次上传源码、测试、配置和规划文档
- secret scan 通过
- 本地 `main` 与远程 `origin/main` 同步
- README 明确个人、本地使用定位

### M0：Development Baseline

- 可复现环境
- `uv.lock`
- 单元测试
- `doctor`
- 版本矩阵

### M1：Correctness Core

- placeholder validator
- clean-output validator
- exact-output retry
- structured errors
- 状态 schema

### M2：CLI MVP Vertical Slice

- BabelDOC worker
- mock PDF E2E
- live Codex E2E
- 单语 PDF
- 双语 PDF
- fixture
- 基础 QA

### M3：Desktop Alpha

- Windows/Linux GUI 技术验证
- 共用 Application Service
- 任务列表、进度、取消、错误和输出目录
- GUI 不直接加载 BabelDOC
- Tauri 2 + React/TypeScript 前端外壳
- 固定 Python sidecar 和 JSONL 协议

### M4：Codex Tooling Alpha

- 本地 stdio MCP Server
- Codex 可发现并调用 BabelCodex tools
- 异步 job 查询协议
- 路径 allowlist 和递归调用保护
- Translation Gateway batching/cache

### M5：GUI Release Preview

- Windows portable bundle
- Linux portable bundle 或 AppImage
- sidecar 资源清单
- GUI E2E 与视觉 artifact
- 干净环境启动验收

### M6：Performance Beta

- Translation Gateway
- batching
- SQLite cache
- benchmark
- structured progress

### M7：Consistency Beta

- glossary
- document context
- thread resume/rotation
- terminology QA

### M8：Personal Release Candidate

- worker recovery
- artifact manifest
- PDF QA
- CLI inspect/retry/validate
- 操作文档
- 发布回归矩阵
- Windows portable bundle
- Linux portable bundle 或 AppImage
- MCP 注册与使用文档
- 个人使用、隐私和数据处理文档

## 6. 开发周期建议

按一名主要开发者估算：

| 阶段 | 建议周期 |
|---|---:|
| M-1 公开仓库基线 | 0.5–1 天 |
| M0 环境基线 | 0.5 周 |
| M1 正确性核心 | 1–1.5 周 |
| M2 CLI MVP 垂直切片 | 1.5–2 周 |
| M3 Desktop Alpha | 1–1.5 周 |
| M4 Codex Tooling Alpha | 1–1.5 周 |
| M5 GUI Release Preview | 1–2 周 |
| M6 性能 Beta | 1.5–2.5 周 |
| M7 一致性 Beta | 1–2 周 |
| M8 个人使用稳定候选 | 2–3 周 |

总体：

- 可演示 CLI MVP：约 3–4 周
- GUI/MCP Alpha：约 5–7 周
- GUI Release Preview：约 7–9 周
- 个人使用稳定候选：约 9–14 周

## 7. 质量门禁

### 代码门禁

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

### 架构门禁

- BabelDOC import 未泄漏出 `backends/`
- PDF 编排未进入 translator
- translator 未直接管理 JobState
- CLI、GUI 和 MCP 共用 Application Service
- MCP 不提供任意 shell、任意文件读取或任意路径删除
- 内层 Codex thread 不注册 BabelCodex MCP
- 公开仓库不包含用户文档、日志、状态、缓存或凭证
- GUI 不直接导入 BabelDOC、Codex SDK 或大模型资源
- GUI 只能通过固定 Python sidecar 调用 Application Service
- Tauri shell capability 只允许固定 sidecar 和受控参数
- GUI、CLI 和 MCP 使用同一任务状态和错误模型
- 无静默认证回退
- 无真实 Codex 默认测试
- 无 token 或全文敏感日志

### 正确性门禁

- placeholder regression 全绿
- 无效 Codex 输出被阻断
- fixture PDF 可打开
- 单语和双语产物存在
- worker 失败有结构化状态

### 性能门禁

批处理上线前后需对比：

```text
总段落数
总 Codex turn
总时间
平均 batch size
P50/P95 延迟
cache hit
validation retry
peak memory
```

## 8. 主要风险及控制措施

| 风险 | 严重度 | 控制措施 |
|---|---:|---|
| BabelDOC 内部 API 变化 | 高 | 版本锁定、兼容模块、契约测试 |
| Codex SDK 行为变化 | 高 | 锁版本、smoke test、错误转换 |
| 占位符被模型破坏 | 高 | 强验证、修复重试、阻断输出 |
| 批次返回错配 | 高 | stable ID、集合验证、单项回退 |
| PDF worker 卡死 | 高 | subprocess、timeout、kill |
| 登录过期 | 高 | 独立错误类别、禁止普通重试 |
| 长 thread 漂移 | 中高 | glossary 外部化、thread 轮换 |
| PDF 敏感内容进入日志 | 高 | 默认不记录全文、日志脱敏 |
| OCR 质量不稳定 | 中高 | OCR 状态显式化、首期不承诺 |
| 缓存污染 | 高 | 完整参数版本化、仅缓存验证结果 |
| BabelDOC 资产下载失败 | 中高 | warmup、doctor、离线资产检查 |
| 输出 PDF 看似成功但损坏 | 高 | artifact hash、PDF QA |
| 运行多个大 PDF 资源耗尽 | 中 | 首期文档级并发限制 |
| Two-phase 段落错配 | 高 | 非默认、严格对齐、后续研究 |
| GUI 打包资源缺失 | 中高 | Windows/Linux 干净环境测试、portable bundle、资源清单 |
| MCP 路径越权 | 高 | allowlist、绝对路径、符号链接解析、删除范围限制 |
| 外层 Codex 与内层 Codex 递归 | 高 | 禁用内层 MCP、嵌套深度限制、invocation source |
| 公开仓库误提交个人数据 | 高 | secret scan、严格 `.gitignore`、fixture 许可证审查 |
| Tauri sidecar 被滥用 | 高 | 固定二进制、capability allowlist、参数验证、禁止任意 shell |
| GUI 与 CLI/MCP 逻辑分叉 | 中高 | Application Service 单一入口、contract tests |
| WebView/系统缩放兼容问题 | 中 | Windows/Linux DPI、窄窗口和干净环境 E2E |
| GUI 退出造成翻译任务丢失 | 高 | Python Application Service 持久化 JobState、GUI 重连查询 |

## 9. 实施建议

```text
1. 创建公开 GitHub 仓库并同步本地基线
2. 环境和依赖锁定
3. 领域模型、错误分类和 Application Service
4. 占位符和输出验证
5. BabelDOC 0.6.4 兼容层
6. BabelDOC Worker Process
7. Mock Fixture PDF 端到端
8. 真实 Codex 垂直切片
9. Translation Gateway 批处理与缓存
10. GUI 技术验证和 Windows/Linux 打包
11. GUI Alpha 和 E2E
12. Codex MCP Server
13. Glossary 和文档上下文
14. 恢复和任务运维
15. PDF QA 和发布硬化
16. 最后评估 Two-phase
```

首个开发迭代不应立即实现批处理。先完成环境、验证器、重试、兼容 mapper 和 mock regression tests；第二个迭代完成 worker、fixture、mock/live E2E 与单语/双语检查，之后再进入 batching 和 glossary。

### Windows 验证更新（2026-09-09）

- 当前 Linux 工作树已同步到 E 盘验证副本；依赖锁定、Ruff、Python 全量测试（147 passed、3 deselected）、doctor、GUI 17 项测试、Vite、Tauri、PyInstaller 冻结 sidecar、JSONL/worker smoke、目标架构 sidecar、bundle 审计、NSIS 打包及 MSI 打包（`4E885B1E...`，195,715,072 bytes；首次失败仅为 E 盘 `tauri.conf.json` 同步状态问题，补同步核对哈希后通过）均为 `WINDOWS_PASS`。
- GUI 安装后交互、clean-user、签名/Defender/SmartScreen、SBOM、发布审计及 live Codex/PDF 未执行（`NOT RUN`）；整体状态仍为 `WINDOWS_VERIFICATION_PENDING`，后续进入安装包运行与发布安全验证。

### Windows 验证复核（2026-09-09）

- 当前同步副本再次完成依赖、Ruff、doctor、GUI 17 项测试、Vite、Cargo、PyInstaller、冻结/目标架构 sidecar、bundle 审计、GUI 启动 smoke、NSIS 和 MSI 验证；NSIS SHA-256 为 `4138276E...`，MSI SHA-256 为 `1AA47BD6...`。
- Python 全量测试首次运行出现 1 个 Windows 临时文件 `PermissionError`，focused test 和顺序复跑均通过（147 passed、3 deselected）；该间歇性文件锁/测试基础设施问题已记录，未修改业务代码。
- 交互式 GUI、clean-user、签名/Defender/SmartScreen、SBOM、发布审计及 live Codex/PDF 仍为 `NOT RUN`；整体状态保持 `WINDOWS_VERIFICATION_PENDING`。

### Windows 验证复核（2026-09-09，状态读取修复后）

- 状态文件读取重试修复已在 Windows 副本验证：Python 全量测试 `150 passed, 3 deselected`；Ruff、doctor、GUI 17 项、Vite、Cargo、PyInstaller、冻结/目标架构 sidecar、bundle 审计、GUI 启动 smoke、NSIS 和 MSI 均为 `PASS`。
- 最新 NSIS SHA-256 为 `8D022FEE...`，MSI SHA-256 为 `D1F56078...`；交互式 GUI、clean-user、签名/Defender/SmartScreen、SBOM、发布审计及 live Codex/PDF 仍为 `NOT RUN`。
- 上一轮记录的间歇性 Windows `PermissionError` 在包含修复的工作树上未复现；整体状态仍为 `WINDOWS_VERIFICATION_PENDING`，等待安装包交互与发布安全验证。

### Windows 验证复核（2026-09-09，重复确认）

- 在无新增源代码变化的当前 WSL 状态上再次完成同步、依赖、Ruff、doctor、Python 全量测试（150 passed、3 deselected）、GUI 17 项、Vite、Cargo、PyInstaller、sidecar、bundle 审计、GUI 启动 smoke、NSIS 和 MSI 验证，均为 `PASS`。
- 上一轮状态读取修复后的 Windows `PermissionError` 未复现；交互式 GUI、clean-user、签名/Defender/SmartScreen、SBOM、发布审计和 live Codex/PDF 仍为 `NOT RUN`，整体保持 `WINDOWS_VERIFICATION_PENDING`。

### Windows 验证复核（2026-09-09，当前源重跑）

- 针对当前 WSL `dev` 工作树（HEAD `7ba4ddf`，含未提交改动）重新同步并执行：uv sync/lock、Ruff、compileall、Python 全量测试 `150 passed, 3 deselected`、doctor、GUI 17 tests、Vite、Cargo、PyInstaller、冻结/target-triple sidecar smoke、NSIS/MSI 构建、MSI 隔离解包后的 sidecar smoke 和包内 GUI 8 秒启动，均通过。
- 本轮 `scripts/check_gui_bundle.py` 实际返回 `FAIL`：其 `[A-Za-z]:[\\/]` 规则把生成资产中的正常 `https://` 误识别为 `s://` 绝对路径；未发现真实开发机绝对路径。该问题属于验证脚本缺陷，未在 Windows 验证中修改。
- 新 NSIS SHA-256 为 `259D3531...`（195,746,309 bytes），MSI SHA-256 为 `8307FD99...`（195,715,072 bytes），均 `NotSigned`；包级启动/sidecar 通过，但不能替代交互式 GUI 和 clean-user 验收。
- 当前状态仍为 `WINDOWS_VERIFICATION_PENDING`；bundle audit 子项为 `WINDOWS_FAIL`，交互式 GUI、clean-user、取消/重连/路径权限矩阵、Defender/SmartScreen、签名/SBOM/release 审计和 live Codex/PDF 仍为 `NOT RUN`。
- Linux 后续只需在开发阶段修正/测试 audit 正则并重新验证；本轮未修改业务代码、配置或依赖。

### Windows 验证复核（2026-09-10，最新 Linux 工作树）

- WSL `dev` HEAD `8f6ee91`（含未提交 GUI 工作树）已通过受控单向同步在 Windows E: 副本复验；依赖/lock、Ruff、compileall、Python 全量 `157 passed、3 deselected`、doctor、GUI 构建、focused store tests、Cargo、Tauri 配置/icon、PyInstaller、冻结/target-triple/MSI 解包 sidecar smoke、bundle audit、NSIS/MSI 构建和包级 GUI 启动均通过。
- 当前 GUI 全量 Vitest 为 `FAIL`：17 项中 15 项通过，取消和详情两个 App 测试因 mock 事件与 `list_jobs` 状态合并后出现重复 `mock-job-1` 行而失败；这是 Linux GUI 代码/测试需处理的问题，不在 Windows 验证中修复。
- 当前 fresh sidecar SHA-256 为 `8E899E68...`；NSIS `CB6476F0...`（195,748,979 bytes），MSI `AF0F9103...`（195,710,976 bytes），MSI 管理员解包及解包 sidecar smoke 通过；均为 unsigned 开发产物。
- 安装/portable GUI 真实交互、clean-user、路径/权限矩阵、取消/重连、Defender/SmartScreen、签名/SBOM/release 审计、live Codex/PDF 仍为 `NOT RUN`；目标 Linux machine smoke 为 `NOT APPLICABLE`；整体保持 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：修正 mock job/event reconciliation 并在 Linux、Windows 重跑 GUI 全套；之后再安排干净用户/真实桌面交互和发布安全验收。本轮未修改业务代码、配置或依赖。

### Windows 验证复核（2026-09-10，GUI 修复后的最新工作树）

- WSL `dev` HEAD `8f6ee91`（含未提交 GUI reconciliation 变化）已完成受控单向同步并在 Windows E: 验证；依赖/lock、Ruff、compileall、Python 全量 `157 passed、3 deselected`、doctor、GUI 全量 `18 passed`、Vite、Cargo、Tauri 配置/icon、PyInstaller、冻结/target-triple/MSI 解包 sidecar smoke、bundle audit、NSIS/MSI 构建和包级 GUI 启动均为 `PASS`。
- 上轮 GUI 重复 `mock-job-1` 失败在当前同步工作树中未复现；`jobStore` 相关 focused tests 为 8 项通过。npm 仍报告 2 个 moderate advisories 和 esbuild pending-script warning，未执行自动修复。
- 当前 fresh sidecar SHA-256 为 `CDE9A9DB...`；NSIS `14975F49...`（195,747,786 bytes），MSI `C8CD3C61...`（195,710,976 bytes）；MSI 管理员解包、包内 sidecar smoke 和解包 GUI 进程启动均通过，产物均为 unsigned 开发包。
- 安装/portable GUI 真实交互、clean-user、路径/权限矩阵、取消/重连、Defender/SmartScreen、签名/SBOM/release 审计、live Codex/PDF 仍为 `NOT RUN`；目标 Linux machine smoke 为 `NOT APPLICABLE`；本轮无 `FAIL` 或 `BLOCKED`，整体仍为 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：保持 GUI reconciliation 回归测试，在后续 GUI 改动后重跑 Linux/Windows GUI 套件；再安排真实桌面/clean-user 与发布安全验收。本轮未修改业务代码、配置或依赖。

### Windows 验证复核（2026-09-10，最新工作树确认）

- 当前 WSL `dev` HEAD `8f6ee91`（含未提交 GUI、架构和文档变化）已完成受控单向同步并在 Windows E: 验证；依赖/lock、Ruff、compileall、Python 全量 `157 passed、3 deselected`、doctor、GUI 全量 `18 passed`、Vite、Cargo、Tauri 配置/icon、PyInstaller、冻结/target-triple/MSI 解包 sidecar smoke、bundle audit、NSIS/MSI 构建和包级 GUI 启动均为 `PASS`。
- 上轮 GUI 重复 `mock-job-1` 问题在当前同步工作树中未复现；相关 reconciliation 回归覆盖保留。npm 仍报告 2 个 moderate advisories 和 esbuild pending-script warning，未执行自动修复。
- 当前 fresh sidecar SHA-256 为 `CDE9A9DB...`；NSIS `14975F49...`（195,747,786 bytes），MSI `C8CD3C61...`（195,710,976 bytes）；MSI 管理员解包、包内 sidecar smoke 和解包 GUI 启动均通过，产物为 unsigned 开发包。
- 安装/portable GUI 真实交互、clean-user、路径/权限矩阵、取消/重连、Defender/SmartScreen、签名/SBOM/release 审计、live Codex/PDF 仍为 `NOT RUN`；目标 Linux machine smoke 为 `NOT APPLICABLE`；本轮无 `FAIL` 或 `BLOCKED`，整体仍为 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：后续 GUI 改动后继续重跑 Linux/Windows GUI 套件，再安排真实桌面/clean-user 与发布安全验收。本轮未修改业务代码、配置或依赖。

### Windows 验证复核（2026-09-12，最新 Linux 状态重跑）

- 当前 WSL Ubuntu `dev` HEAD `4e709d9`（dirty tree，5 个文档文件与 9 个代码/测试文件为既有变更）已在保留 E: 本地依赖、缓存、状态和用户数据的前提下受控单向同步；68 个文件同步、0 个失败，9 个代码/测试文件哈希一致。
- 本轮自动化与包级验证：Python `200 passed、5 deselected`，GUI `22 passed`，mock PDF integration `5 passed`；QA CLI 初始通过且删除 artifact 后正确失败；PyInstaller、protocol-v1/target-triple handshake、真实 assets 布局下的 fresh/stale bundle audit、NSIS/MSI 构建和 release GUI 8 秒进程 smoke 均通过。QA 断言之后的临时日志清理再次暴露 Windows `WinError 32`；MSI admin extraction 90 秒无输出、无 payload 为 `BLOCKED`；原生 GUI 与 stale-GUI 错误展示因 trusted RPC `sky` 不可用为 `BLOCKED`。
- 产物哈希：sidecar `CBAD9089...A7841`、GUI `452E86E9...0274F`、NSIS `AE89EB2F...477E1`、MSI `DA638042...42AD3`。状态计数为 `PASS 20 / FAIL 1 / BLOCKED 3 / NOT RUN 5 / NOT APPLICABLE 1`。
- Linux 后续：优先调查 QA 日志/临时目录句柄生命周期并重跑 `WVQ-007`；恢复可验证的当前 MSI 解包 parity；安排 `WVQ-001`～`WVQ-004` 与 `WVQ-009` 的原生桌面验证；保留 freshness + runtime handshake 双层门禁，并另行安排发布安全与 live Codex/PDF 验收。本轮未修改业务代码、依赖或配置，整体保持 `WINDOWS_VERIFICATION_PENDING`。

### Windows 验证复核（2026-09-12，当前 dirty tree 重跑）

- 当前 WSL `dev` HEAD `4e709d9` 已再次受控同步到 E:；排除了 `gui/dist`、依赖、缓存、状态和用户数据目录，68 个文件同步、0 个失败，10 个代码/测试文件哈希一致。
- 自动化验证：Python `200 passed、5 deselected`，GUI `22 passed`，mock PDF integration `5 passed`；QA CLI/tamper、PyInstaller、protocol-v1/target-triple handshake、fresh/stale bundle audit、NSIS/MSI 构建和 release GUI 8 秒进程 smoke 均通过。QA 断言通过后，临时 fixture 清理再次暴露 Windows `WinError 32`；MSI admin extraction 因无有效解包输出为 `BLOCKED`，原生 GUI 与 stale-GUI 错误展示因 trusted RPC `sky` 不可用为 `BLOCKED`。
- Linux 后续：优先调查 fixture/harness 文件句柄生命周期并重跑 `WVQ-007`；恢复有效 MSI 解包证据；安排 WVQ-001～004/009 原生桌面验证，保留 handshake 与 source freshness 双层门禁。本轮未修改业务代码、依赖或配置，整体保持 `WINDOWS_VERIFICATION_PENDING`。

### Windows 验证复核（2026-09-11，当前 dirty tree、WVQ-008/WVQ-009）

- WSL `dev` HEAD `4e709d9` 及未提交的 sidecar `get_server_info` 握手、GUI 协议回归、mock-test 资源范围变更和 `check_gui_bundle --source-tree` 新鲜度审计已同步到 E:；71 个源文件更新，0 个同步失败，变更文件哈希一致。
- Windows 自动化与包级验证：Python `200 passed、5 deselected`，GUI `22 passed`，mock PDF integration `5 passed`；QA CLI 对真实 fixture mock job 返回 PASS，删除 artifact 后返回 `qa_status=failed`；PyInstaller、握手、worker 错误路径、target-triple、fresh/stale bundle audit、NSIS/MSI、MSI 解包 sidecar/GUI 启动均完成。
- 本轮暴露一项未解决 Windows `WinError 32` 临时 fixture 清理失败，归入 `WVQ-007` 后续调查；原生 GUI 交互与 packaged stale-GUI 错误展示因 computer-use trusted RPC 未配置而为 `BLOCKED`。因此不能把本轮提升为完整 Windows release/desktop acceptance，整体保持 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：保留 `WVQ-009` 双层防线并在 sidecar/协议/打包变化后重跑；优先调查 Windows 文件句柄清理，再安排 `WVQ-001` 至 `WVQ-005` 的原生桌面、clean-user、路径/权限、DPI/NVDA 和发布安全验收。本轮未修改业务代码、依赖或配置。

### Windows 验证复核（2026-09-11，PDF QA 与发布路径）

- 当前 WSL `dev` HEAD `4e709d9` 已在 E: Windows 验证副本完成受控同步；修正初次过滤同步遗漏后，PDF QA、workdir、artifact manifest、release 文档和测试文件均已核对一致。Linux 工作树原有的 `scripts/build_linux_gui_bundle.sh` mode-only 改动保持不变。
- 当前 Python 全量 `196 passed、5 deselected`，mock PDF integration `5 passed`；Ruff、compileall、doctor、GUI `19 passed`、Vite、Cargo、PyInstaller、sidecar JSONL/worker、target-triple、bundle audit、NSIS/MSI、MSI 解包 sidecar 和 GUI 启动均完成。新增 PDF QA 的命令、报告和 service/MCP/CLI 覆盖因此达到 Windows 自动化与包级验证通过。
- 首次临时 bundle audit 因 staging 缺少 target-triple 文件名而 `FAIL`；首次 MSI 解包 sidecar 因 Tauri 输入仍是陈旧二进制而以 `retry_policy` 配置不兼容 `FAIL`。两者均已在不改业务代码的前提下修正验证输入并重跑 `PASS`，详见 `docs/validation/windows.md`。
- 中文真实渲染、键盘/DPI/NVDA、安装/portable 交互、clean-user、路径权限、取消/重连、Defender/SmartScreen、签名/SBOM/release 审计及 live Codex/PDF 仍为 `NOT RUN`；整体保持 `WINDOWS_VERIFICATION_PENDING`。后续 Linux 需保留 PDF QA 回归门禁，并安排上述 Windows 原生验收。

### Windows 验证复核（2026-09-10，当前 UI 工作树）

- 当前 WSL `dev` HEAD `8f6ee91`（含未提交 GUI、架构和文档变化）已完成受控单向同步并在 Windows E: 验证；依赖/lock、Ruff、compileall、Python 全量 `157 passed、3 deselected`、doctor、GUI 全量 `19 passed`、Vite、Cargo、Tauri 配置/icon、PyInstaller、冻结/target-triple/MSI 解包 sidecar smoke、bundle audit、NSIS/MSI 构建和包级 GUI 启动均为 `PASS`。
- 本轮最新 UI 变更已通过自动化测试和构建/进程级 smoke；中文界面真实渲染、键盘导航、DPI 125/150/200%、NVDA、clean-user 和真实桌面交互仍未执行。npm 仍报告 2 个 moderate advisories 和 esbuild pending-script warning，未执行自动修复。
- 当前 fresh sidecar SHA-256 为 `4577E0D4...`；NSIS `9C9332AD...`（195,743,723 bytes），MSI `D0C5D8B8...`（195,715,072 bytes）；MSI 管理员解包、包内 sidecar smoke 和解包 GUI 启动均通过，产物为 unsigned 开发包。
- 本轮无 `FAIL` 或 `BLOCKED`；安装/portable GUI 真实交互、中文 UI/accessibility、clean-user、路径/权限矩阵、取消/重连、Defender/SmartScreen、签名/SBOM/release 审计、live Codex/PDF 为 `NOT RUN`；目标 Linux machine smoke 为 `NOT APPLICABLE`；整体仍为 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：安排上述真实桌面与发布安全验证；后续 GUI 改动后继续重跑 Linux/Windows GUI 套件。本轮未修改业务代码、配置或依赖。

### Windows 验证复核（2026-09-10，当前工作树确认）

- 当前 WSL `dev` HEAD `8f6ee91`（含未提交 GUI、架构和文档变化）已完成受控单向同步并在 Windows E: 验证；依赖/lock、Ruff、compileall、Python 全量 `157 passed、3 deselected`、doctor、GUI 全量 `19 passed`、Vite、Cargo、Tauri 配置/icon、PyInstaller、冻结/target-triple/MSI 解包 sidecar smoke、bundle audit、NSIS/MSI 构建和包级 GUI 启动均为 `PASS`。
- 上轮 GUI 重复 `mock-job-1` 问题在当前同步工作树中未复现；reconciliation 回归覆盖继续通过。npm 仍报告 2 个 moderate advisories 和 esbuild pending-script warning，未执行自动修复。
- 当前 fresh sidecar SHA-256 为 `4577E0D4...`；NSIS `9C9332AD...`（195,743,723 bytes），MSI `D0C5D8B8...`（195,715,072 bytes）；MSI 管理员解包、包内 sidecar smoke 和解包 GUI 启动均通过，产物为 unsigned 开发包。
- 安装/portable GUI 真实交互、clean-user、路径/权限矩阵、取消/重连、Defender/SmartScreen、签名/SBOM/release 审计、live Codex/PDF 仍为 `NOT RUN`；目标 Linux machine smoke 为 `NOT APPLICABLE`；本轮无 `FAIL` 或 `BLOCKED`，整体仍为 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：后续 GUI 改动后继续重跑 Linux/Windows GUI 套件，再安排真实桌面/clean-user 与发布安全验收。本轮未修改业务代码、配置或依赖。

### Windows 验证复核（2026-09-12，当前 dirty tree fresh sidecar/package 重跑）

- 当前 WSL `dev` HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb`（dirty working tree）已按流程单向同步到 E:；Robocopy dry-run/实际均为 67 个文件、0 个失败、17 个 E: extras 保留，24 个选定控制/变更文件 SHA-256 一致。依赖、缓存、状态、日志、用户内容和生成 GUI 资产均未反向同步。
- Windows 自动化与包级验证：`uv sync --locked`/lock、Ruff、compileall、Python `201 passed、5 deselected`、doctor、GUI `22 passed`、Vite、Cargo/Tauri 配置图标、mock PDF integration `5 passed`、QA/tamper、PyInstaller、protocol-v1/target-triple handshake、fresh/stale bundle audit、NSIS/MSI、MSI admin extraction、解包 sidecar handshake 和解包 GUI 8 秒 smoke 均 `PASS`。
- 本轮 QA 临时目录清理通过，之前的 `WinError 32` 未在当前 CLI handler-release 路径复现；这只清除了 QA harness 路径，不等于完整 `WVQ-007` 生命周期矩阵已验证。fresh sidecar SHA-256 为 `29D0A257...BD02AC4`，NSIS 为 `D7AD204A...24BD2B2`，MSI 为 `114EE0EC...551F30BB`，均为 unsigned development artifacts。
- Native GUI/stale-GUI 观察因 trusted desktop automation 两次 `helper_unknown_error: setup refresh had errors` 为 `BLOCKED`；clean-user、完整 WVQ-007、WVQ-005 release security、live Codex/PDF 为 `NOT RUN`。状态计数为 `PASS 23 / FAIL 0 / BLOCKED 2 / NOT RUN 5 / NOT APPLICABLE 1`，整体保持 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：配置可用的原生 Windows desktop automation，执行 WVQ-001～004 与 WVQ-009 stale-GUI 展示；执行完整 WVQ-007 生命周期矩阵；另行安排 WVQ-005 发布安全和经授权的 live Codex/PDF。验证期间未修改业务代码、依赖、架构或配置。

### Windows GUI 手动验证移交（2026-09-12）

自动化桌面控制面两次不可用后，已在 E: 验证副本准备隔离人工验证包：`build\manual-gui-validation-20260912-152358`。`fresh` 使用当前 GUI + 当前 sidecar；`stale` 使用相同当前 GUI + 2026-09-10 旧 sidecar。详细步骤、PASS/FAIL/BLOCKED/NOT RUN 判定和证据模板见该目录的 `MANUAL-VALIDATION.md`。

当前自动化记录中的 GUI/stale-GUI 仍保留 `BLOCKED`，人工移交项在收到实际观察前记为 `NOT RUN`，不得据此提升为 Windows GUI 验收通过。Linux 后续只需回收人工结果并更新 `docs/validation/windows.md`；本次未修改业务代码、依赖、架构或配置。

### Windows GUI 手动验证结果（2026-09-12）

人工验证已完成并回填：fresh/stale GUI 的启动及窗口基本操作为 `PASS`；页面切换基本可用但设置页出现元素位置跳动，记为 `FAIL`；文件选择器打开/取消及 PDF 选择加载为 `PASS`；原生 PDF 拖入拖放框无法加载，记为 `FAIL`；stale GUI 可正常打开但未报告可理解的旧 sidecar/兼容性错误，stale-GUI 展示记为 `FAIL`。键盘、NVDA、DPI/缩放均按用户报告记为 `NOT RUN`，未作负面推断。

初步 Linux 后续：排查视图内容高度变化导致的滚动条/布局宽度变化；核对 Tauri 原生拖放事件中的真实 Windows 路径；让 sidecar 启动/握手失败的安全错误进入 GUI 可见区域。上述仅为问题记录，本轮未修改业务代码。

### Windows GUI 截图证据补充（2026-09-12）

已保存用户提供的三张 stale-GUI 截图：图 1 为 `Starting sidecar`，图 2 为 `Sidecar unavailable`，图 3 为设置页。截图确认 sidecar 通用错误可见，但左下角本地优先提示在新建翻译页显示不完整，设置页可完整显示且右上角服务状态位置发生变化；PDF 拖放前后拖放框无变化。布局稳定性、原生 PDF 拖放和 stale-GUI 可操作错误提示继续分别记为 `FAIL`；键盘、NVDA、DPI 继续为 `NOT RUN`。

### Windows 验证复核（2026-09-13，当前 HEAD 14b4856，worker/打包重验）

- 当前 Linux `dev` HEAD `14b4856bf37cf06674b6319da8f0ab6451728348`（工作树仍只有 `scripts/build_linux_gui_bundle.sh` mode-only dirty diff）已按受控排除规则单向同步到 E:；87 个受控文件复制、0 failed，17 个文件和 3 个目录 extras 保留，40 个选定源/测试/配置/验证文件 SHA-256 一致。
- Windows 验证：锁定依赖、Ruff、compileall、文档清单 CLI、GUI `22 passed`、jobStore `9 passed`、Vite/TypeScript、Cargo/Tauri、mock PDF `5 passed`、QA 正向/篡改和清理、当前源 PyInstaller、sidecar protocol-v1、invalid-worker、target-triple、fresh/stale bundle audit、NSIS/MSI、MSI parity/解包 sidecar handshake 和两个 GUI 8 秒 smoke 均通过。
- 两项当前失败需要 Linux 处理：`tests/test_docs_inventory.py` 在 Windows 路径分隔符断言失败，导致 Python `220 passed、1 failed、5 deselected`；有效 frozen worker mock 请求在冻结产物中报 `No module named 'bitstring.bitstore_bitarray'`、exit 3，而普通 `.venv` import 正常，疑似 PyInstaller 动态依赖/hidden-import 漏收集。本轮未修改业务代码或 spec。
- 当前轮状态计数为 `PASS 29 / FAIL 3 / BLOCKED 2 / NOT RUN 5 / NOT APPLICABLE 1`。native GUI/stale-GUI 因 computer-use helper `helper_unknown_error: setup refresh had errors` 为 `BLOCKED`；clean-user、完整 WVQ-007、WVQ-005 release security、live Codex/PDF 和 dependency remediation 仍为 `NOT RUN`，目标 Linux smoke 为 `NOT APPLICABLE`。整体保持 `WINDOWS_VERIFICATION_PENDING`。
- Linux 后续：先修复文档清单测试的跨平台路径断言并调查 frozen worker 的 `bitstring.bitstore_bitarray` 打包缺失，完成 Linux regression 后重跑 Windows frozen-worker、fresh/stale freshness、target-triple、NSIS/MSI 和解包 sidecar；另行安排原生桌面、WVQ-007、clean-user、发布安全和经授权 live Codex/PDF 验收。

### Linux follow-up（2026-09-13，Windows FAIL reconciliation）

- 文档库存路径问题已在 Linux 修复：`scripts/check_docs_inventory.py` 现在显式将相对路径规范化为 `/`，并新增 Windows 风格分隔符回归测试；相关文档库存测试通过。
- frozen worker 打包问题已在 Linux 修复：`scripts/babelcodex-service.spec` 使用 `collect_submodules("bitstring")`，收集 `tiktoken`/`tiktoken_ext` 动态插件，并移除会错误排除 `unittest`/`pydoc` 的标准库排除项；新增 spec 回归测试。
- Linux 证据：Python 默认套件 `223 passed, 5 deselected`；针对性文档库存/worker 测试 `39 passed`；Ruff check/format、compileall、文档库存 CLI、GUI Vitest `22 passed`、Vite/TypeScript build 均通过；Linux PyInstaller sidecar 构建成功；冻结 worker mock PDF 请求 exit 0，生成 mono/dual PDF artifact。
- 以上仅证明 Linux 源码和 Linux 冻结产物已修复，不能替代 Windows 原生重验证。Windows frozen worker、fresh/stale bundle、target-triple、NSIS/MSI、解包 sidecar 和 GUI/package acceptance 继续标记为 `WINDOWS_VERIFICATION_PENDING`，不得提前提升为 `WINDOWS_PASS`。
- 当前下一步：将本轮修复后的 Linux 工作树单向同步到 Windows，重跑原 frozen worker/package gates；保留 `WIN-MANUAL-002 / WVQ-001` 的有限范围 PASS，`WVQ-002` 的 `NOT RUN`、`WVQ-003`/stale-GUI 的 `BLOCKED` 以及 clean-user、WVQ-007、WVQ-005、live Codex/PDF 的未执行状态。

### Windows 验证复核（2026-09-13，当前 HEAD `62f23d9`）

本轮已完成修复后 frozen worker、sidecar handshake、fresh/stale bundle audit、target-triple、NSIS/MSI、MSI 解包 parity、QA/tamper、GUI 自动化测试和 mock PDF 的 Windows 重验；逐项状态与证据以 [`docs/validation/windows.md`](validation/windows.md) 的本轮记录为准。当前仍为 `WINDOWS_VERIFICATION_PENDING`：Windows 文档清单测试仍有路径分隔符 `FAIL`，原生桌面自动化因 trusted RPC 未配置而 `BLOCKED`，clean-user、WVQ-007 完整生命周期、WVQ-005 发布安全和 live Codex/PDF 尚未执行。Linux 后续只处理文档清单跨平台断言并安排上述 Windows 队列，不在本验证任务中扩大为业务开发。

### Windows 操作员处置（2026-09-13）

- 按用户要求，本轮 packaged GUI interaction/path/DPI/NVDA 矩阵记为 `NOT RUN`（`SKIPPED_BY_USER_REQUEST`）；未执行原生桌面操作，不据此宣称 Windows GUI 验收通过。
- packaged stale-sidecar GUI 错误展示仍保持 `BLOCKED`，因为 sidecar 在握手前因 `config/example.toml` 不在包工作目录而退出，尚未观察到目标的 stale/incompatible-handshake 可理解错误。分步骤操作、判定标准和证据要求见 [`docs/validation/windows.md`](validation/windows.md)。

### GUI WebdriverIO E2E 基础设施（2026-09-14，Batch 1-2 完成）

按 `docs/decisions.md` ADR-030，在 Linux 端一次性完成 `@wdio/tauri-service` 基础设施搭建，后续 Windows 只需执行标准 npm 命令。

**已完成：**

1. **Cargo features 与互斥控制面**
   - 新增 `mcp-dev` 和 `e2e` 两个 optional feature，编译期拒绝同时启用（`compile_error!`）
   - `mcp-dev` 注册 `tauri-plugin-mcp-bridge`，`e2e` 注册 `tauri-plugin-wdio` + `tauri-plugin-wdio-webdriver`
   - 默认 production build 不包含任一开发控制面

2. **Capability 模板化管理**
   - 正常运行 capability：`src-tauri/capabilities/default.json`（`main-capability`）
   - MCP/E2E capability 模板：`scripts/capabilities/mcp-debug.json` / `e2e.json`
   - `scripts/prepare-e2e-rust.mjs` 按 flavor 注入 capability，普通构建不获得测试权限
   - Tauri flavor configs：`tauri.mcp.conf.json`、`tauri.e2e.conf.json`

3. **确定性 E2E workspace 与无付费边界**
   - 新增 `config/e2e.toml`（`translator = "mock"`，所有运行数据进入 `gui/build/e2e/`）
   - `scripts/prepare-e2e.mjs` 严格限定 `build/e2e` 路径内操作，拒绝符号链接和越界访问
   - 所有 native E2E 使用 mock translator，不访问真实 Codex，符合架构不变量 8

4. **前端 WDIO plugin 条件加载**
   - `src/main.tsx` 改为 async bootstrap，`import.meta.env.VITE_E2E === "1"` 时动态 import `@wdio/tauri-plugin`
   - 生产构建不包含 WDIO frontend plugin（已验证 dist 中无 `wdio` 字符串）
   - `src/vite-env.d.ts` 添加 `@wdio/tauri-plugin` 模块声明

5. **WDIO 三层测试配置**
   - `wdio.shared.conf.ts`：共享 framework/reporter/timeout
   - `wdio.browser.conf.ts`：renderer 用户旅程（Chrome + Vite dev server，不需要 Tauri binary）
   - `wdio.native.conf.ts`：真实 Tauri WebView + embedded WebDriver server
   - `wdio.external.conf.ts`：诊断 fallback（external provider）

6. **标准 npm 命令**
   - `npm run e2e:prepare` / `npm run e2e:build` / `npm run e2e:browser` / `npm run e2e:native` / `npm run e2e`
   - `npm run e2e:native:debug` / `npm run e2e:external`：诊断模式
    - `npm run mcp:build`：MCP debug flavor（`mcp:prepare` 已移除，capability 已内联）

7. **测试 specs**
   - `tests/e2e/browser/smoke.spec.ts`：renderer 启动 + mock sidecar 连接
   - `tests/e2e/browser/navigation.spec.ts`：视图切换 + 空状态
   - `tests/e2e/native/smoke.spec.ts`：真实 WebView 启动 + WDIO Tauri API 可用
   - `tests/e2e/windows/paths.spec.ts`：Windows-only specs（Linux 自动 skip）
   - `tests/e2e/wdio.d.ts`：`browser.tauri.*` 类型声明

8. **验证通过**
   - `npx tsc --noEmit`：TypeScript 编译通过
   - `npx vitest run`：27/27 通过（e2e 目录已排除）
   - `npm run build`：生产构建成功，不包含 WDIO 产物
   - `cargo check`（default / mcp-dev / e2e / mcp-dev+e2e 互斥失败）：全部按预期
