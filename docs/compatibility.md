# Compatibility Baseline

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
