# Linux 测试矩阵

本文档描述在 Linux 开发机上应当运行的验证命令、测试标记与付费测试边界。Windows 验证流程与结果见 `docs/validation/windows.md`；逐文件职责见 `docs/development/codebase-map.md`。

## 常规验证命令

| 命令 | 作用 | 预期结果 |
|---|---|---|
| `uv run pytest -q` | 全部单元测试（默认排除 `integration` 标记） | 全部通过 |
| `uv run pytest -q -m integration tests/test_e2e_mock.py` | worker 子进程端到端 mock 流水线 | 通过（较慢，涉及真实子进程） |
| `uv run ruff check .` | Python 静态检查 | 无告警 |
| `uv run ruff format --check .` | Python 格式门禁 | 无差异 |
| `uv run pytest -q tests/test_docs_inventory.py` | 文档防漂移检查（测试形式） | 通过 |
| `uv run python scripts/check_docs_inventory.py` | 文档防漂移检查（命令行形式） | 退出码 0 |
| `cd gui && npm test -- --run` | GUI Vitest 单元测试 | 全部通过 |
| `cd gui && npm run build` | GUI 生产构建 | 构建成功 |

改动合入前至少运行：pytest、ruff、GUI 测试与构建，以及文档防漂移检查（若改动涉及文档或模块增删）。

## 测试标记（markers）

- **无标记**：默认单元测试。不得访问网络、不得消耗 Codex/ChatGPT 计划用量、不得调用真实翻译服务。
- **`integration`**：真实子进程的端到端测试（仍使用 scripted/mock translator，不产生付费用量）。默认被 deselect，需显式 `-m integration` 运行。
- **付费/真实 Codex 测试**：当前不存在。未来引入时必须额外标记（如 `live`）、默认跳过，并在本文件登记其边界与运行条件（架构不变量 8）。

## 付费测试边界

1. 单元测试只允许使用 `scripted` / `mock` translator；
2. 任何会建立真实 Codex 连接的测试必须显式标记且默认跳过；
3. `tests/test_e2e_mock.py` 属于 `integration`：真实子进程 + BabelDOC 管线 + scripted translator，不付费。

## GUI 自动化测试矩阵（WebdriverIO）

| 模式 | 命令 | 需要 | 覆盖范围 |
|---|---|---|---|
| Vitest | `cd gui && npm test -- --run` | Node | 组件、状态、协议、错误处理 |
| WDIO Browser | `cd gui && npm run e2e:browser` | Chrome/Chromium + Vite dev server | renderer 用户流程、mock sidecar |
| WDIO Native | `cd gui && npm run e2e:native` | 桌面会话 + 真实 sidecar binary | Tauri WebView、plugin-shell、sidecar 生命周期 |
| WDIO External | `cd gui && npm run e2e:external` | WebKitWebDriver (Linux) / Edge WebDriver (Windows) | driver 诊断 fallback |

### Linux Phase 15 基线记录（基础设施实现阶段）

| 检查项 | 状态 | 说明 |
|---|---:|---|
| Vitest 28 tests | ✅ | `npm test -- --run` 通过 |
| TypeScript 编译 | ✅ | `npx tsc --noEmit` 无错误 |
| Cargo check (default) | ✅ | 正常 GUI 构建 |
| Cargo check (mcp-dev) | ✅ | MCP Debug Bridge feature |
| Cargo check (e2e) | ✅ | WDIO plugin feature |
| MCP-dev + E2E 互斥 | ✅ | 编译期 `compile_error!` 生效 |
| WDIO 配置文件 | ✅ | shared/browser/native/external 四配置 |
| WDIO E2E specs | ✅ | browser smoke/navigation + native smoke + windows paths |
| 前端条件加载 `@wdio/tauri-plugin` | ✅ | `VITE_E2E=1` 控制 |
| `config/e2e.toml` | ✅ | `translator = "mock"`，无付费 |
| Capability flavor 注入 | ✅ | flavor capability 内联于 `tauri.*.conf.json`（`CapabilityEntry::Inlined`），不再生成文件；回归 Guard `tests/test_gui_flavor_capabilities.py` |
| WDIO Browser mode | ❌ BLOCKED | 缺少 Chrome/Chromium |
| WDIO Native smoke | ✅ | `npm run e2e:native:smoke`：4 tests passed；真实 Tauri WebView + embedded WebDriver 已在当前 Linux 桌面执行 |
| WDIO Native mock lifecycle | ✅ | `npm run e2e:native:mock`：4 tests passed；mock job/cancel/restart 流程通过 |
| WDIO Native full suite | ✅ | `npm run e2e:native`：4 spec files、15 tests 全部通过；包含 smoke、handshake、path rejection 和 mock lifecycle |

## Windows WDIO 回传与 Linux 后续（2026-09-15）

Windows 配置复核确认 Phase 15 的 Linux 实现可以完成原生构建和 @wdio/tauri-service 启动链路：cross-env、target-triple sidecar 选择、隔离 build/e2e 工作区、../config/e2e.toml 路径、真实 React 输入事件 helper 与 TauriServiceAPI 类型均已对齐。详细 Windows 命令、哈希、日志和逐项状态不在本文件重复，见 [docs/validation/windows.md](../validation/windows.md)。

Windows 本轮通过了 npm 重建、GUI Vitest 27/27、生产构建、E2E prepare/build、mock lifecycle、embedded handshake/smoke 和 Windows lifecycle。标准 native 的路径负向断言曾暴露确定性 mock transport 缺少 allowlist 校验；Linux 端已补上 E2E-only contract 并在 Linux 全套 native 中验证通过，Windows 需要重新同步后复跑相关 specs。冻结 sidecar 的直接 JSONL probe 已正确返回 CONFIG_INVALID。所以：

- Linux Native mode 已在当前桌面会话实际执行并通过；该结果只证明 Linux E2E flavor、embedded WebDriver 和确定性 mock contract，不替代 Windows 原生验证。
- 这也不是 GUI→真实 sidecar 的 Windows 路径安全通过证据；需要 Windows 同步本次测试 contract 修复后重跑相关 specs，并保留冻结 sidecar JSONL probe 作为独立证据。
- 所有 GUI WDIO 运行继续使用 mock translator，禁止接入真实 Codex；外部 provider 仅用于 driver 诊断，不替代 embedded @wdio/tauri-service 主路径。

### Linux 端后续执行清单

| 操作 | 状态 | 完成条件 |
|---|---:|---|
| 为 E2E mock/contract 增加 outside-path 拒绝断言 | DONE | E2E-only persistent mock transport 校验 `build/e2e/incoming`; Vitest regression added |
| Linux 桌面 preflight + npm run e2e:native:mock | PASS | 当前 Linux display/embedded driver 可用，4 tests passed |
| Linux npm run e2e:native | PASS | allowlist 修复后 4 spec files、15 tests 全部通过；无 native spec 失败 |
| Linux browser mode | BLOCKED（若仍无 Chrome/Chromium） | 安装并确认 Chrome/Chromium 与 Vite dev server 后再执行 |
| Linux regression/document inventory | PASS | npm test 28/28、npm run build、Ruff、docs inventory 17/17 和 git diff --check 均通过 |
| Windows revalidation after Linux allowlist fix | PASS | 6 native spec files、20 tests passed；详细结果见 docs/validation/windows.md |

该清单只描述 Linux 端后续动作；总体 Windows 状态继续按 WINDOWS_VERIFICATION_PENDING 管理。

### E2E 构建与运行

```bash
cd gui
npm run e2e:prepare   # 准备 build/e2e workspace（flavor capability 已内联，无文件生成）
npm run e2e:build     # 构建带 e2e feature 的 Tauri binary
npm run e2e:browser   # 运行 browser mode（需要 Chrome/Chromium）
npm run e2e:native    # 运行 native embedded mode（需要真实 sidecar）
npm run e2e:external  # 运行 external provider 诊断（需要 WebKitWebDriver）
npm run e2e           # browser + native
```

### E2E 安全边界

- E2E 构建使用独立 Cargo feature `e2e`，包含 `tauri-plugin-wdio` 和 `tauri-plugin-wdio-webdriver`
- MCP Debug Bridge 使用独立 feature `mcp-dev`，两者互斥（编译期检查）
- E2E capability 作为 `CapabilityEntry::Inlined` 内联于 `tauri.e2e.conf.json`，通过 `--config` 合并进入 `--features e2e` 构建；不进入生产构建，且 `gui/src-tauri/capabilities/` 仅含 `default.json`，不会污染默认 / mcp-dev 的 `cargo check`（详见 `tests/test_gui_flavor_capabilities.py`）
- E2E 运行使用 `config/e2e.toml`（`translator = "mock"`），不访问真实 Codex
- 前端通过 `import.meta.env.VITE_E2E` 在 build time 选择配置文件

## 打包与 GUI 附加检查

- 打包 sidecar：`uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec`
- 打包产物校验：`uv run python scripts/check_gui_bundle.py <bundle-dir>`
- GUI E2E（WebdriverIO）、Windows 打包与人工验证见 `gui/README.md` 与 `docs/validation/windows.md`。

## Linux follow-up completion after Windows WDIO revalidation (2026-09-15)

Windows WVQ-017 复核外化了 `npm run e2e:prepare` 生成的 `gui/src-tauri/capabilities/e2e.json` 残留污染默认 / mcp-dev `cargo check`（`Permission wdio:default not found`）。Linux 端通过**内联 capability**彻底修复（flavor capability 直接嵌入 `tauri.*.conf.json`，不再向共享 `capabilities/` 写入任何文件）。本节为结果表；动因与清单参见 `docs/development-plan.md`（Linux follow-up completion）；Windows 复验仍排队于 `docs/validation/windows.md` WVQ-018。

| 项目 | 状态 | 证据 |
|---|---|---|
| E2E capability 生成/清理生命周期 | ✅ RESOLVED | `gui/src-tauri/capabilities/` 仅含 `default.json`；回归 Guard `tests/test_gui_flavor_capabilities.py`（7 tests） |
| 默认 / mcp-dev / e2e Cargo checks | ✅ PASS | `cargo check --locked` / `--features mcp-dev` / `--features e2e` 均 `Finished`，无 `wdio:default not found` |
| E2E prepare/build/native WDIO | ✅ PASS | `npm run e2e:native` — 4 spec files、15 tests 全部通过；结束后无残留 capability/driver/WebDriver 进程或监听端口 |
| Python / Rust / frontend / docs 门禁 | ✅ PASS (env-scoped) | `uv run pytest` 231 passed, 5 deselected；`ruff` clean；GUI `npm test` 28 passed、`tsc --noEmit`/`vite build` clean；docs inventory passed |
| frozen sidecar/protocol probe | NOT RUN (not required) | 变更未触及 sidecar 协议/工作目录/allowlist/错误分类 |
| Linux browser WDIO | BLOCKED | 缺少 Chrome/Chromium + 匹配 driver |
| Windows 原生 GUI/DPI/picker/Codex/PDF | WINDOWS_VERIFICATION_PENDING | WVQ-001～016 + WVQ-018，Linux 仅验证契约/夹具/回归 |

Windows 原生 GUI 与打包需复验 WVQ-018；Linux 原生 WDIO 结果保持 LINUX_VERIFIED，浏览器模式仍为 BLOCKED。

## Windows 后续执行边界（当前基线：`6ae5258`）

Windows 验证应从 `docs/validation/windows.md` 的 Current Windows handoff 开始，按
`Source/workspace → Toolchain → WVQ-018 → WVQ-017 native → native filesystem/UI →
packaged clean-user → MCP/live/release` 顺序集中执行。Windows 端至少需要运行：

```powershell
npm.cmd --prefix gui ci
npm.cmd --prefix gui test -- --run
npm.cmd --prefix gui run build
npm.cmd --prefix gui run e2e:prepare
npm.cmd --prefix gui run e2e:build
npm.cmd --prefix gui run e2e:native
```

其中 `e2e:prepare`/`e2e:build` 后必须确认 `gui/src-tauri/capabilities/` 仍只有
`default.json`；`e2e.json` 和 `mcp-debug.json` 不得重新出现。`e2e:native` 必须在
Windows 真实桌面会话中覆盖 path rejection 和 Windows paths specs，不能用 Linux
native 结果或冻结 sidecar 的直接 JSONL probe 替代 GUI→sidecar 原生链路。

Windows-only 的 picker、drive-letter/Unicode/space/traversal、权限、取消/重连、
DPI/NVDA、clean-user、NSIS/MSI/portable、MCP localhost、Defender/SmartScreen、
签名/SBOM、真实 Codex/PDF 均不能由 Linux 测试关闭。缺少桌面自动化能力时，按
`COMPUTER_USE_UNAVAILABLE` 记录为 `BLOCKED`，继续执行独立的命令、文件系统、协议、
进程和打包检查；每个 `FAIL`/`BLOCKED`/`NOT RUN` 必须写明原因和后续动作。
