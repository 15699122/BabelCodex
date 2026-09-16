# Linux 测试矩阵

本文档描述在 Linux 开发机上应当运行的验证命令、测试标记与付费测试边界。默认验证范围由「增量验证策略」决定：验证范围应与改动风险匹配，而不是与项目总规模匹配。Windows 验证流程与结果见 `docs/validation/windows.md`；逐文件职责见 `docs/development/codebase-map.md`。

## Latest Windows validation after Linux follow-up fixes (2026-09-16)

- 当前 WSL `dev` 工作树（HEAD `268102b1`）已按单向流程同步到 E:\ 验证工作区，
  本节是 Linux follow-up 完成后的 Windows 结果**最新计划参考**。
  准确的命令、证据、失败分类和手工修复步骤统一以
  `docs/validation/windows.md` 的“Windows validation of current portable/YAML working tree:
  2026-09-16”及其 Failure analysis and Linux follow-up / Current disposition 为准。
- 当前 Linux 主套件为 Python `257 passed, 5 deselected`；mock integration 为 `5 passed`。
- 当前最新 Windows 结果混合存在，产品整体仍处于 `WINDOWS_VERIFICATION_PENDING`。
  已通过项目的证据（锁定 Python 环境、Python suite、Ruff/format/compileall/docs inventory、
  GUI build/test、PowerShell staging/audit、fresh sidecar build/protocol/allowlist、
  settings/staging/log retrieval、Tauri Rust/features/Debug/Release build、
  moved-root audit/layout/process smoke、embedded native WDIO 6 specs/20 tests、cleanup）
  参见 windows.md 对应行。产品侧 FAIL 是 output confirmation contract（启动时已创建 output
  目录，无法观察 `confirmed=false`），Linux 已完成代码修复，Windows 复验仍待执行。
  BLOCKED/NOT RUN 项目（原生手动 GUI/视觉、安装器/MSI/NSIS、
  清洁用户/安全/签名/SBOM、实时 Codex/真实 PDF/长文档）也未在本轮解决。
- 历史上保留的“Linux follow-up 两项已由 Windows 复验关闭”表述，如与当前 windows.md 结果不一致，
  **不再作为当前结论**。历史 FAIL 行不删除，当前标准来源统一为 windows.md。
  歴史 FAIL 行は削除せず、現在の標準出典を windows.md に一元化する。
- 結論：Linux フォローアップ完了後にも総体状態は `WINDOWS_VERIFICATION_PENDING`。
  詳細は `docs/development-plan.md` の該当節と `docs/validation/windows.md` を参照。

## Linux follow-up after the 2026-09-16 Windows revalidation

- 唯一新增的 Linux 回归位于默认（非 integration）套件：
  `tests/test_babeldoc_compat.py::TestPyMuPDFPackageNameHygiene`。
  它静态禁止 `src/`、`scripts/`、`tests/` 中出现 `import fitz` / `from fitz`，
  并在子进程运行 `scripts/generate_fixture.py` 断言产物非空且 stdout/stderr 无
  `deprecated`（`pymupdf` 缺失时 `importorskip` 跳过）。
- 常规命令即可覆盖：`uv run pytest -q`、`uv run ruff check .`、
  `uv run ruff format --check .`、`uv run python -m compileall -q src tests scripts`、
  `uv run python scripts/check_docs_inventory.py`、`git diff --check`。
- 本轮 Windows `FAIL`/`BLOCKED`/`NOT RUN`（WiX LGHT0217 MSI、Node `ENOMEM` native
  WDIO、MSI extraction/parity、native GUI/manual、clean-user/security、live
  Codex/PDF）全部是 Windows 运营方事项，Linux 侧没有可执行动作，不得用 Linux
  结果替代；逐用例证据与手动修复步骤见 `docs/validation/windows.md`。

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

本地 batching 性能证据使用 `uv run python scripts/benchmark_batching.py`；该命令只运行
deterministic mock，不访问网络、不初始化 Codex、不消耗付费/计划用量。输出 JSON 中的
`turns`、`average_batch_size`、`turn_reduction_ratio` 和 `results_match_baseline` 可用于 Linux
基线；真实 Codex throughput/latency 仍必须显式授权并单独记录。

改动合入前至少运行：pytest、ruff、GUI 测试与构建，以及文档防漂移检查（若改动涉及文档或模块增删）。

## 增量验证策略（Incremental Validation Strategy）

本节决定「一次改动需要运行多少测试」。失败分类、执行顺序和证据格式见下节
「验证 Agent 执行规范」；Windows 侧的最小化与复验规则见
`docs/development/cross-platform-validation.md`。

### 目标与核心规则

默认采用最小必要测试范围，目标是在保持足够置信度的前提下减少重复测试、无关模块
构建、Windows 环境切换、GUI 自动化、全量回归和不必要的资源消耗。不要因为仓库存在
完整测试套件，就在每次修改后执行全部测试。

核心原则：**验证范围与改动风险匹配，而不是与项目总规模匹配**，默认
`small change -> small targeted validation`。

### 变更分类与默认范围

先根据 `git diff`、changed files、受影响模块、调用/依赖关系、公共 API、平台相关
行为、上一轮失败和测试归属对改动分类，再决定范围：

| 类别 | 典型改动 | 默认验证 |
|---|---|---|
| A 文档 | `README.md`、`docs/**`、注释 | 只跑文档静态检查：`uv run python scripts/check_docs_inventory.py`、`uv run pytest -q tests/test_docs_inventory.py`；不跑功能测试 |
| B 局部实现 | 单模块内部函数/boundary 修复 | 直接相关 unit + regression：`uv run pytest -q tests/<file>::<Class>`；必要时 `ruff` 与 `compileall` |
| C 公共 API/共享库 | `application/service.py`、`translation/gateway.py`、`core/state.py` 等对外契约 | B + 直接消费者与相关 integration：`uv run pytest -q tests/<consumer>.py`，必要时叠加 `-m integration` |
| D 跨模块行为 | orchestrator、worker、sidecar、GUI store 的协作改动 | 涉及模块 + 集成边界 + 受影响 workflow + regression；范围不确定时直接升级 |
| E 安全敏感 | 鉴权、凭据、文件权限、命令执行、路径/网络信任边界（如 `core/private_data.py`、`backends/worker_client.py` 的 allowlist、`translators/codex_sdk.py` 的 deny-all） | 直接测试 + 对应 suite 的安全回归（如 `tests/test_worker.py`、`tests/test_mcp.py`） |
| F 平台相关 | Windows 路径、进程派生、GUI、打包、sidecar | Linux 执行全部可执行部分，Windows-only 项加入 WVQ；Windows 只跑与本改动相关的平台项 |
| G 依赖/构建系统 | `pyproject.toml`、`uv.lock`、`gui/package.json`、`Cargo.toml`、CI/构建脚本 | 依赖解析 + 相关构建 + 受影响测试；必要时升级到 broader/full |

### 默认不做的事

对局部改动，不默认执行：全仓库测试、所有平台测试、完整 installer/package 验证、
所有 GUI 测试，以及与当前 diff 无关的模块测试。

### 测试选择

优先寻找同目录测试、引用被改模块的测试、针对被改函数/类/服务的测试、已有
regression test，以及与改动 API 直接关联的 integration test。项目已支持过滤，优先使用：

```bash
uv run pytest -q tests/test_worker.py::TestWorkerDiagnosticsLogging   # class/name 过滤
uv run pytest -q tests/test_retry_policy.py                           # 单文件
uv run pytest -q -m integration tests/test_e2e_mock.py                # 显式慢测试（默认 deselect）
npm --prefix gui test -- --run src/jobStore.test.ts                   # Vitest 指定文件
cd gui && npm run e2e:native:smoke                                    # WDIO 指定 spec
```

Rust 侧当前没有单元测试，以 `cargo check --manifest-path gui/src-tauri/Cargo.toml
--locked`（必要时叠加 `--features mcp-dev` 或 `--features e2e`）作为编译门禁。优先使用
仓库已有脚本与命令，不自行发明新的验证流程。

### 升级阶梯

出现以下情况时扩大范围：直接测试失败、意外构建错误、公共 API 受影响、依赖关系不
明确、多模块受影响、结果与预期不一致、修改了公共基础设施、出现新运行时行为、可能
影响多平台、属于 regression，或上一轮失败暗示影响面更大。

升级顺序为 `Targeted -> Module -> Subsystem -> Full`，不要从 Targeted 直接跳到 Full。

### 何时运行完整套件

仅当出现以下条件才默认全量：release/pre-release、重大重构、架构变更、依赖大改、
共享核心库变更、数据库 schema/迁移变更、跨模块大 diff、安全关键改动、影响面难以
判断、targeted 测试反复暴露无关失败，或用户明确要求全量回归。

### 验证记录

每轮至少记录：changed scope、selected tests、skipped tests、为什么该范围足够、测试
结果、是否需要扩大范围。未运行全量时必须显式写明
`Full test suite not run because ...`，不得暗示已完成全量验证。

### 结论格式

验证结束按五段输出：

- `Validated`：本轮实际完成的验证；
- `Not required`：因当前改动不影响而未执行的测试；
- `Deferred`：计划在 Windows / release / 全量回归阶段执行；
- `Blocked`：当前无法执行的验证；
- `Escalation required`：若结果要求扩大范围，写明下一层验证范围。

## 验证 Agent 执行规范

本节是 BabelCodex 面向 Tauri、Python sidecar 和 WebdriverIO 的统一测试
Agent 规范。它约束 Linux/Cline 与 Windows/Codex 的执行顺序、失败分类、
证据记录和自动修复边界；一次具体验证的事实结果仍只写入
`docs/validation/windows.md` 或对应历史记录。

### 角色与核心原则

| 环境 | 主要职责 |
|---|---|
| Linux + Cline | 功能开发、重构、测试维护、Python/GUI/Rust 验证、WDIO Browser Mode 和 Linux Native E2E；完成当前阶段全部 Linux 可执行工作后再整理 Windows 队列 |
| Windows + Codex | Windows 真实环境验证；优先共享 `@wdio/tauri-service`，然后 Windows-only WDIO，最后才使用 Computer Use；诊断、低风险修复、相关重跑和结果回写 |

核心原则：确定性自动化优先于视觉 GUI 自动化，自动诊断优先于人工判断，
局部失败不得无条件阻塞无关测试。不得为了让结果变绿而删除断言、降低
验收标准、扩大生产 capability、重复重建无关环境或修改用户数据格式。

### 执行前预检

只执行与当前测试范围有关的轻量预检：

1. `git status --short --branch`；
2. Node/npm、Rust/Cargo/Tauri 和现有依赖是否可用；
3. 项目能否构建；
4. WDIO 配置是否存在；
5. E2E binary 是否能够生成；
6. 当前层级所需的 WebView2、WebDriver、embedded driver 或桌面会话是否满足。

预检失败时先判断影响范围：只暂停依赖该组件的测试，继续执行静态检查、
单元测试、独立集成测试和其他不依赖该环境的测试。不要在预检阶段执行与
当前范围无关的大规模诊断。

### 测试层级与优先级

必须按以下顺序推进，并在低层级已有明确证据时避免无价值的高层级重复：

1. **Level 1 — 静态与快速测试**：lint、type check、Rust compile/check、unit、
   frontend unit、integration；先修复明确的代码、类型或测试问题。
2. **Level 2 — WDIO Browser Mode**：页面渲染、表单、路由、UI 状态、常规交互和
   可 mock 的 Tauri invoke。已被 Browser Mode 充分覆盖的 renderer 行为不再用
   Computer Use 重复确认。
3. **Level 3 — Tauri Native E2E**：默认使用 `@wdio/tauri-service` 的
   `driverProvider: embedded`，覆盖真实 Tauri WebView、IPC/invoke、command
   返回值、窗口行为、前端日志、Rust/backend 日志和完整流程；只有怀疑 driver
   层问题且仓库已有 fallback 时，才尝试 external provider。
4. **Level 4 — Windows-only tests**：仅在 Windows 执行路径、WebView2、文件系统、
   平台 IPC、托盘、通知、注册表、安装卸载、权限和平台快捷键等 Windows 专项。
   Linux 对不适用项目使用 `SKIPPED_PLATFORM`，不记为失败。
5. **Level 5 — Computer Use**：只用于原生 picker、系统通知、托盘、安装器、原生
   窗口、DPI/多显示器、拖放、WDIO 无法稳定访问的系统组件和视觉布局验收。
   Computer Use 不替代能由 WDIO 稳定完成的测试。

### 失败诊断顺序与分类

每次失败先依次检查：测试步骤/断言 → WDIO 输出 → frontend console → Tauri
IPC/invoke → Rust/backend 日志 → Windows system error → 测试代码 → 产品代码
→ 环境/自动化基础设施。没有证据不得直接修改生产代码。

每个用例必须使用以下细粒度状态之一：

| 状态 | 含义与处理 |
|---|---|
| `PASS` | 首次通过，行为符合预期且无关键 console/backend 异常 |
| `PASS_FLAKY` | 满足安全重试条件，最多总执行 3 次，后续重试成功；记录初次错误、retry_count、成功次数和疑似原因 |
| `PASS_AFTER_FIX` | 明确局部产品/配置修复后通过；记录修复范围和相关回归结果 |
| `PASS_AFTER_TEST_FIX` | 明确测试缺陷修复后通过；不得删除有效断言或放宽正确预期 |
| `FAIL_PRODUCT` | 相同输入稳定复现且业务、IPC、状态机、数据读写或平台实现不符合需求 |
| `FAIL_PRODUCT_NEEDS_DEVELOPMENT` | 产品问题需要架构、需求、安全模型、数据模型或大范围重构，禁止当前 Agent 擅自扩大范围 |
| `FAIL_TEST` | selector、fixture、mock、初始化、配置、隔离或 expectation 与正式需求不一致 |
| `BLOCKED_ENV` | 缺依赖、WebView2、toolchain、权限、网络、外部服务或鉴权环境导致无法执行 |
| `BLOCKED_AUTOMATION` | Computer Use、embedded/external driver、WDIO session 或 Agent GUI 控制层不可用，且没有产品缺陷证据 |
| `SKIPPED_PLATFORM` | 当前平台不适用，或项目明确规定由另一平台执行 |
| `NEEDS_REVIEW` | 行为与测试/文档冲突，需求没有说明哪个结论正确 |
| `NEEDS_DEVELOPMENT_REVIEW` | 需要重大架构、安全、数据格式、capability 或 breaking API 决策 |

不要使用没有附加分类的单独 `FAIL` 或 `BLOCKED` 作为最终用例状态。历史
Windows 文档中的旧状态必须保留；新增记录使用上述细粒度状态，并在汇总
层映射到跨平台工作流状态（见 `cross-platform-validation.md`）。

### 分类后的动作

#### Flaky / transient

只有日志、失败位置和多次结果共同支持时才能判断 flaky。安全重试必须：

- 只清理该测试自己的状态；
- 不重建整个项目环境；
- 使用短退避，建议约 1 秒、3 秒；
- 最多重试 2 次，即总执行次数最多 3 次；
- compiler error、确定性断言、panic、schema mismatch、明确业务错误、稳定权限
  错误不得自动重试。

连续失败且表现稳定后立即重新分类为 `FAIL_PRODUCT`、`FAIL_TEST`、
`BLOCKED_ENV` 或 `BLOCKED_AUTOMATION`。

#### Product / test / environment

- `FAIL_PRODUCT` 必须记录最小复现、输入、Expected/Actual、frontend/backend 日志、
  stack trace、源码位置、root cause、跨平台范围和是否 Windows-only。修复后运行
  失败用例、相关回归集和适当范围综合回归。
- `FAIL_TEST` 可以修复测试，但不得删除有效断言、修改 Expected 迎合错误行为、
  用超长 sleep 掩盖 race，或临时重写整个测试架构。通过后记为 `PASS_AFTER_TEST_FIX`。
- `BLOCKED_ENV` 只暂停依赖该环境的测试，记录 affected_component、affected_tests、
  root_cause_guess、key_log、recovery_action，并继续独立测试。
- `BLOCKED_AUTOMATION` 先尝试一次低成本恢复：重启 session、清理残留进程、已配置的
  embedded→external fallback 或重新启动应用。仍失败则输出人工步骤，并明确“尚未
  验证，不代表产品失败”。
- 行为与需求无法判断时使用 `NEEDS_REVIEW`；需要大范围变更时使用
  `NEEDS_DEVELOPMENT_REVIEW`，不得擅自扩大修改范围。

### 自动修复边界

允许优先修复：明确的测试脚本错误、局部实现错误、类型/编译错误和明确配置错误。
不得自动进行架构调整、重大数据模型变更、安全模型变化、生产 capability 扩权、
删除安全检查、用户数据格式变更或 breaking API。Windows 纯环境问题不得通过修改
Linux 业务代码“绕过”。

### 测试独立性与重试粒度

每个 E2E 用例应独立创建数据、不依赖执行顺序、结束时清理自身状态，并避免共享
可变全局状态。发生污染时只恢复受影响的测试环境。重试优先按 failed test，
其次 failed spec，只有最终回归需要时才运行完整矩阵。

Linux 工作流固定为：

```text
开发 → Unit → Integration → Browser Mode → Linux Native WDIO
→ 修复 → 相关回归 → 继续 Linux 开发 → 阶段性 Linux 完成
→ 整理 Windows 队列 → 集中 Windows 验证
```

Windows 工作流固定为：

```text
读取文档 → 检查 Linux 结果 → 构建 E2E → 共享 WDIO
→ Windows-only WDIO → 自动诊断/低风险修复/相关重跑
→ Computer Use 剩余系统级测试 → 汇总并回写验证文档
```

除非 Windows 结果是后续开发的硬依赖，不得每完成一个小功能就中断 Linux
开发等待 Windows 手工验证。

### 证据与结构化输出

每个失败用例至少收集：`case_id`、test name、platform、command、timestamp、
expected、actual、相关 WDIO 输出、frontend console、backend/Rust log 和 stack trace。
GUI 问题按需增加 screenshot、window information、route/UI state；避免收集无关大日志。

推荐的单用例结果结构如下：

```json
{
  "case_id": "TC_001",
  "name": "Settings can be saved",
  "platform": "windows",
  "layer": "native_e2e",
  "status": "PASS",
  "category": null,
  "retry_count": 0,
  "action_taken": "Executed native Tauri E2E through @wdio/tauri-service.",
  "details": {
    "summary": "Settings were saved successfully.",
    "expected": "Settings persist after Save.",
    "actual": "Settings persisted correctly.",
    "reproduction": null,
    "relevant_log": null,
    "root_cause": null,
    "affected_component": null
  },
  "evidence": {
    "frontend_log": null,
    "backend_log": null,
    "screenshot": null
  }
}
```

`layer` 只能使用：`static`、`unit`、`integration`、`browser_e2e`、
`native_e2e`、`windows_native`、`computer_use`。

完成当前可执行测试后输出最终汇总，至少包含各状态计数、
`regression_status`、remaining Windows validation、manual tests required、
development followups、environment issues 和 flaky tests。汇总不得把
`BLOCKED_ENV`、`BLOCKED_AUTOMATION` 或 `SKIPPED_PLATFORM` 计入 PASS。

### Computer Use 人工 fallback

每个 `BLOCKED_AUTOMATION` 用例必须给出：

1. 前置条件；
2. 启动应用方式；
3. 点击/输入步骤；
4. 测试数据；
5. 预期结果；
6. 失败时应收集的日志；
7. PASS 判定标准；
8. FAIL 判定标准。

不能只写“需要人工测试”。如果 Computer Use 不可用，必须继续执行独立的
CLI、filesystem、protocol、process、静态和打包检查，并以
`BLOCKED_AUTOMATION` 记录桌面用例。

### E2E 安全边界

测试可以启用 `tauri-plugin-wdio`、`tauri-plugin-wdio-webdriver` 和测试专用
capability，但这些能力必须只存在于 E2E/Test build。不得把 WebDriver 暴露到生产
构建、永久扩大 production capability、禁用安全机制或提交真实 token、密码、API key、
用户 PDF、状态和日志。真实 Codex/ChatGPT-plan 测试必须显式授权、专门标记并默认跳过。

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
| `config/e2e.yaml` | ✅ | `translation.translator: mock`，无付费；所有运行数据进入 `gui/build/e2e/` |
| Capability flavor 注入 | ✅ | flavor capability 内联于 `tauri.*.conf.json`（`CapabilityEntry::Inlined`），不再生成文件；回归 Guard `tests/test_gui_flavor_capabilities.py` |
| WDIO Browser mode | ❌ BLOCKED | 缺少 Chrome/Chromium |
| WDIO Native smoke | ✅ | `npm run e2e:native:smoke`：4 tests passed；真实 Tauri WebView + embedded WebDriver 已在当前 Linux 桌面执行 |
| WDIO Native mock lifecycle | ✅ | `npm run e2e:native:mock`：4 tests passed；mock job/cancel/restart 流程通过 |
| WDIO Native full suite | ✅ | `npm run e2e:native`：4 spec files、15 tests 全部通过；包含 smoke、handshake、path rejection 和 mock lifecycle |

### Linux detailed validation run (2026-09-15)

本轮按验证 Agent 规范执行：先完成 Level 1，再执行 Browser Mode 和 Linux
Native WDIO；失败按单用例细粒度状态分类，未把平台不适用项目计入失败。

#### Environment preflight

| Check | Layer | Status | Evidence |
|---|---|---|---|
| `Git workspace/config presence` | `static` | `PASS` | Expected repository state; WDIO configs, `config/e2e.yaml` and Linux sidecar candidate present. |
| Python/uv/runtime imports | `static` | `PASS` | Python 3.12.14, uv 0.12.10; `babeldoc`, `openai_codex`, `pymupdf` importable. |
| Node/npm | `static` | `PASS` | Node 26.7.0, npm 11.19.0. |
| Rust/Cargo | `static` | `PASS` | rustc/cargo 1.98.0. |
| Linux desktop session | `native_e2e` | `PASS` | `DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`. |
| Chrome/Chromium executable | `browser_e2e` | `BLOCKED_ENV` | No system Chrome/Chromium or chromedriver was available; WDIO attempted managed Chrome 153.0.8010.36 download but stalled at 99.57% before spec execution. |

#### Level 1 — static, unit and integration

| Case / command | Layer | Status | Retry | Result |
|---|---|---|---:|---|
| `uv run pytest -q --tb=short` | `unit` | `PASS` | 0 | 250 passed, 5 deselected. |
| `uv run pytest -q -m integration tests/test_e2e_mock.py` | `integration` | `PASS` | 0 | 5 passed; 10 known multiprocessing fork `DeprecationWarning`s, non-blocking. |
| `uv run ruff check .` | `static` | `PASS` | 0 | All checks passed. |
| `uv run ruff format --check .` | `static` | `PASS` | 0 | 96 files already formatted. |
| `uv run python -m compileall -q src tests scripts` | `static` | `PASS` | 0 | Compilation completed. |
| `uv run python scripts/check_docs_inventory.py` | `static` | `PASS` | 0 | Documentation inventory passed. |
| `uv run pytest -q tests/test_docs_inventory.py tests/test_gui_flavor_capabilities.py` | `unit` | `PASS` | 0 | 24 passed. |
| `npm --prefix gui test -- --run` | `unit` | `PASS` | 0 | 4 files, 28 tests passed. |
| `npm --prefix gui run build` | `static` | `PASS` | 0 | TypeScript/Vite production build passed. |
| Cargo fmt/default/mcp-dev/e2e checks | `static` | `PASS` | 0 | All checks passed; default build retained the existing `unused_mut` warning only. |
| `uv run cbpdf --config config/config.yaml doctor` | `integration` | `BLOCKED_ENV` | 0 | Runtime dependencies and bundled Codex CLI detected, but this Linux machine reports `codex_authenticated=false` / `Not logged in`; no live request was made. Only authentication-dependent checks are blocked. |

#### Level 2 — WDIO Browser Mode

| Case | Layer | Status | Retry | Evidence and action |
|---|---|---|---:|---|
| `npm run e2e:browser -- --logLevel info` | `browser_e2e` | `BLOCKED_ENV` | 0 | Vite started and WDIO attempted to provision Chrome/Chromedriver, but managed Chrome download stalled at 99.57% and no spec ran. One existing BabelCodex browser/Vite session was identified and cleaned by exact project-path process matching. No product conclusion is inferred. |

恢复 Browser Mode 前置条件：安装可执行的 Chrome/Chromium 与匹配 driver，或
提供稳定可写的 WDIO managed-browser cache；随后只重跑 Browser Mode，不必重跑
已经通过的 Level 1 或 Native spec，最后再执行一次适当范围的综合回归。

#### Level 3 — Linux Native E2E

| Case | Layer | Status | Retry | Evidence |
|---|---|---|---:|---|
| `npm run e2e:native` | `native_e2e` | `PASS` | 0 | 4 spec files / 15 tests passed: mock lifecycle 4, path rejection 4, sidecar handshake 3, native smoke 4. Real Tauri WebView and embedded WebDriver were used; no native spec failed. |
| Native cleanup | `native_e2e` | `PASS` | 0 | Tauri app, embedded driver and checked ports 4444/4445/5173/9223 left no project-process or listener residue. |

#### Level 4 — Windows-only and Level 5 — Computer Use

| Scope | Layer | Status | Category / reason |
|---|---|---|---|
| Windows path, WebView2, Windows IPC, installer/uninstaller, registry, notifications, tray, Windows permissions and platform shortcuts | `windows_native` | `SKIPPED_PLATFORM` | Must execute on Windows; Linux evidence cannot substitute. |
| Windows native picker, DPI/NVDA, clean-user, MSI admin extraction, Defender/SmartScreen, signing/SBOM and release acceptance | `computer_use` / `windows_native` | `SKIPPED_PLATFORM` | Windows-only or target-desktop scope; no Linux PASS inferred. |

#### Structured final summary

```json
{
  "summary": {
    "total": 20,
    "pass": 16,
    "pass_flaky": 0,
    "pass_after_fix": 0,
    "pass_after_test_fix": 0,
    "fail_product": 0,
    "fail_test": 0,
    "blocked_env": 2,
    "blocked_automation": 0,
    "skipped_platform": 1,
    "needs_review": 0
  },
  "regression_status": "PASS_WITH_ISSUES",
  "remaining_windows_validation": [
    "WVQ-001 through WVQ-018 as applicable, including current-head native revalidation",
    "Windows packaging, clean-user, DPI/accessibility, release security and live Codex/PDF"
  ],
  "manual_tests_required": [],
  "development_followups": [
    "Install/provision Chrome or Chromium and a stable matching driver/cache before rerunning Browser Mode"
  ],
  "environment_issues": [
    "Browser WDIO managed Chrome download stalled before spec execution",
    "Codex authentication is not configured for this local environment"
  ],
  "flaky_tests": []
}
```

本汇总中的 `PASS` 只覆盖 Linux 实际执行的层级；`BLOCKED_ENV` 不代表产品
失败，`SKIPPED_PLATFORM` 不计入失败，也不改变 Windows 验证队列状态。

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
| Windows 原生 GUI/DPI/picker/Codex/PDF | WINDOWS_VERIFICATION_PENDING | WVQ-001～016，Linux 仅验证契约/夹具/回归 |

Windows WVQ-018 inline capability 与 WVQ-017 automated native scope 已通过；Windows 原生 GUI、完整 work-dir recovery、打包/clean-user、DPI/picker、发布安全、MCP localhost 和真实 Codex/PDF 等仍按 WVQ-001～016 保持 WINDOWS_VERIFICATION_PENDING。Linux 原生 WDIO 结果保持 LINUX_VERIFIED，浏览器模式仍为 BLOCKED。

## Linux dependency-shape recovery (2026-09-15)

`uv sync --locked --extra runtime --extra dev` 已恢复与 `uv.lock` 一致的本地 runtime/dev 环境。当前 `BabelDOC==0.6.4`、`openai-codex==0.147.0` 和 bundled Codex CLI runtime 均可导入/探测；Python 全量测试为 `234 passed, 5 deselected`。`cbpdf doctor` 若返回非零，仅表示当前机器尚未完成 Codex 登录（`codex_authenticated=false`），不表示依赖缺失。Windows 端仍必须在其独立环境中重新执行对应检查。

## Windows 后续执行边界（当前基线：`268102b`）

## 当前阻塞恢复复核（2026-09-15）

本轮针对细粒度状态执行了一次低成本恢复，不改写此前的历史记录：

| 项目 | 状态 | 当前结论 |
|---|---|---|
| Linux Browser Mode | `BLOCKED_ENV` | `npm ci` 已恢复 617 个 GUI 包，残缺 Chrome/Chromedriver 缓存已隔离，Chromedriver 已重新取得；Chrome for Testing 长时下载/续传仍以 TLS EOF 中止，未进入 spec。 |
| Linux `cbpdf doctor` | `BLOCKED_ENV` | 依赖和 bundled runtime 正常；`codex login status` 为 `Not logged in`，需用户完成交互式登录后复验。 |
| Windows native GUI/manual acceptance | `BLOCKED_AUTOMATION` | Computer Use 一次重试后仍为 `apps=[]`，无可控原生 app；已有 CLI/协议/进程 PASS 不替代 GUI-only 结论。 |

Browser Mode 的可修复项仅限本地依赖、完整浏览器/driver 缓存和项目残留进程；本轮没有修改 manifest、lockfile、业务代码或 Tauri 配置。Codex 鉴权和 Windows 原生桌面控制分别需要用户授权/宿主能力，保留阻塞状态。完整手动操作、证据要求和 Linux 后续清单见 [`docs/validation/windows.md`](../validation/windows.md) 的 “Blocker recovery analysis (2026-09-15)”。

Windows 验证应从 `docs/validation/windows.md` 的下一轮 handoff 开始，按
`Source/workspace → Toolchain regression → native GUI/recovery → stale package/QA →
filesystem/runtime → clean-user/package → MCP/live/release` 顺序集中执行。`WVQ-018`
与自动化 `WVQ-017` 已有 Windows PASS，不需要重复作为未完成项目登记，但仍可作为每轮构建的回归门禁。Windows 端至少需要运行：

```powershell
npm.cmd --prefix gui ci
npm.cmd --prefix gui test -- --run
npm.cmd --prefix gui run build
npm.cmd --prefix gui run e2e:prepare
npm.cmd --prefix gui run e2e:build
npm.cmd --prefix gui run e2e:native
npm.cmd --prefix gui run mcp:build
```

其中 `e2e:prepare`/`e2e:build` 后必须确认 `gui/src-tauri/capabilities/` 仍只有
`default.json`；`e2e.json` 和 `mcp-debug.json` 不得重新出现。`e2e:native` 必须在
Windows 真实桌面会话中覆盖 path rejection 和 Windows paths specs，不能用 Linux
native 结果或冻结 sidecar 的直接 JSONL probe 替代 GUI→sidecar 原生链路。

Windows-only 的 picker、drive-letter/Unicode/space/traversal、权限、取消/重连、
work-dir/file-lock、DPI/NVDA、clean-user、NSIS/MSI/portable、stale-GUI、MCP localhost、
Defender/SmartScreen、签名/SBOM、真实 Codex/PDF 均不能由 Linux 测试关闭。缺少桌面自动化能力时，按
`COMPUTER_USE_UNAVAILABLE` 记录为 `BLOCKED`，继续执行独立的命令、文件系统、协议、
进程和打包检查；每个 `FAIL`/`BLOCKED`/`NOT RUN` 必须写明原因和后续动作。
