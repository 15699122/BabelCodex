# BabelCodex Development Plan

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

1. [已完成，未签名] 在 Windows 原生环境构建 GUI 与 `babelcodex-service.exe`；
2. [已完成] 使用 Tauri target-triple sidecar 执行 NSIS/MSI `tauri build`（2026-09-09 最新轮：NSIS `D653629B...`、MSI `4E885B1E...` 均已生成并记录；旧 MSI 未作为证据）；
3. [部分完成] MSI 已隔离解包并运行 sidecar；干净用户环境安装/解压运行仍待完成；
4. [部分完成] 已验证 JSONL handshake、sidecar 退出和 GUI 进程级启动；文件选择、allowlist、进度、取消、完成产物和诊断 UI 仍待完成；
5. [部分完成] MSI 解包仅含 GUI 与 sidecar 可执行文件，未完成完整绝对路径/敏感内容审计；
6. [部分完成] 已生成 bundle/sidecar SHA-256 和构建日志；SBOM、签名和正式发布附件仍待完成。

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
- 尚未完成完整 GUI packaged 交互 E2E、干净用户环境验收、输入/输出 allowlist 与 Windows 路径矩阵、sidecar 自身重启编排、Linux 目标机 smoke、签名/SBOM 和正式发布验收；GUI 的重试、输出目录打开、cleanup 和 `validate_output` 仍需扩展 sidecar/Application Service contract，MCP 侧 scoped cleanup/validate 已完成。
- Linux/WSL 可完成的 glossary/context 基础接入与编辑页面已完成；剩余 packaged 交互、目标机运行、签名/SBOM 和正式发布验收继续保留在 Windows/目标平台清单中。

#### Phase 9B：白色 Vercel 风格 GUI 设计重构（PLANNED，2026 年 9 月 10 日）

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

**优先级：P3 | 复杂度：L | 预计：5–8 个开发日**

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

### Phase 13：PDF QA 与发布硬化

**优先级：P3 | 复杂度：L/XL | 预计：7–12 个开发日**

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
