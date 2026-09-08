# Compatibility Baseline

Last verified: 2026-09-08

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
```

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
- 目标机运行矩阵和正式发布资源审计；源配置已声明 `icons/icon.png`，Linux AppImage 构建已通过，目标机图标显示和正式发布资源审计仍待完成。

原生 Windows 仍是必要条件，WSL/Linux 结果不能替代上述尚未完成的 GUI 交互验收：

WSL/Linux 的 `cargo check`、浏览器端 Vitest、Vite build、bundle audit 和 Linux `.deb`/AppImage 构建已通过，可作为先决检查，但不能替代原生 Windows packaged GUI smoke test 或目标 Linux 机器运行验证。Windows 桌面边界测试应继续使用 mock transport/fixture；真实 Codex 集成另行标记为付费或 ChatGPT-plan integration test。

## Non-Windows implementation boundary

在 Linux/WSL 可完成并已纳入当前代码门禁的内容包括：

- glossary CSV 导入/导出、全局与文档级合并、稳定版本 hash 和 bounded terminology prompt；
- UTF-8 文档 context sidecar 的标题/摘要提取、归一化、截断和稳定版本 hash；
- glossary/context 到 TranslationGateway cache key、worker `TranslatorSpec` 和 Codex thread prime 的接入；
- CLI glossary 管理、MCP/CLI 共用 Application Service、状态保存跨平台加固以及相关 contract/regression tests。

仍强制依赖 Windows 原生环境的内容包括：

- packaged GUI 文件选择、真实路径 allowlist、窗口关闭、取消、完成产物和输出目录交互矩阵；
- 干净 Windows 用户目录首次启动、WebView2/Defender/SmartScreen、非 ASCII 用户目录和路径空格/反斜杠验证；
- Windows 签名、SBOM、portable 发布验收、正式资源审计和目标用户环境 smoke；
- Windows 原生完整 pytest 复验，特别是 `tests/test_mcp.py::test_cancel_uses_the_active_job_handle`；

需要认证 Codex/目标集成环境、但不属于 Windows-only 的内容包括：

- Codex 客户端实际注册和 stdio MCP discovery；
- 真实 Codex thread resume/rotation、thread compact 和 ChatGPT-plan PDF 翻译；
- 长文档术语一致性与真实账户下的 throughput/usage benchmark。


## Windows native validation incidents and execution boundary

记录日期：2026-09-08。以下错误均已定位并处理，不代表当前通过项失败：

- 初次 WSL 到 E 盘同步使用相对路径排除参数，未可靠排除 node_modules 等生成目录；通过检查同步清单发现后，改用绝对排除路径重新同步，并保留 E 盘已有依赖、缓存、状态、日志和构建产物。
- 首次 Tauri bundle 构建因 icons/icon.ico 缺失而失败；随后补齐方形源图标并在 `tauri.conf.json` 声明 `icons/icon.png`，Linux AppImage 构建已验证，Windows 目标机图标显示和发布资源审计仍待完成。
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

本轮非 Windows 开发完成后，在 2026-09-08 的 Linux/WSL 工作区复验：

- `uv run pytest -q`：135 passed，3 deselected；
- GUI `npm test -- --run`：14 passed；`npm run build`：通过；
- Ruff format/check、Python compileall、JSON/YAML/Markdown checks：通过；
- glossary CLI `list` smoke、MCP stdio smoke 和 glossary/context contract tests：通过；
- PDF metadata/opening-page context adapter、thread identity persistence 和 mocked Codex `thread_resume` contract：通过；
- 未生成或提交 glossary/context 用户文件；配置目录仅在本地运行时创建为空目录。

上述结果不能替代 Windows 原生 packaged GUI、Windows 完整 pytest、Codex 客户端实际注册、真实 Codex thread resume/rotation 行为、目标 Linux 机器 smoke 或正式签名/发布验收。
## Upgrade policy

Changing Python, BabelDOC, openai-codex or uv requires:

1. regenerating `uv.lock`;
2. running all local quality gates;
3. checking `doctor` output;
4. re-running BabelDOC warmup on a clean cache when practical;
5. updating this compatibility document;
6. validating at least one mock PDF fixture before enabling the new baseline.
