# BabelCodex Architecture

**BabelCodex** 是一款面向个人用户的、本地优先的高保真 PDF 翻译工具。

产品计划提供三个入口：

- `babelcodex` CLI；
- Windows/Linux GUI 可执行文件；
- 可由 Codex 调用的本地 MCP Server。

三种入口必须共用 Application Service，不得各自复制任务编排逻辑。

- **BabelDOC** 负责 PDF 解析、版面分析、公式/富文本保护、字体映射和 PDF 重建。
- **官方 `openai-codex` SDK** 负责在 Codex ChatGPT 登录下提供语言翻译。
- **本项目** 负责任务编排、翻译网关、结果验证、缓存、恢复与质量检查。

## 1. 设计原则

1. **BabelDOC 独占 PDF fidelity。**
2. **Codex 独占语言生成。**
3. **认证与文档处理分离。**
4. **BabelDOC 不稳定性被隔离在 `backends/`。**
5. **PDF 核心运行在独立 Worker Process。**
6. **Translation Gateway 负责正确性与吞吐。**
7. **Desktop / ChatGPT 中的 Codex 仅作为开发与监督控制面。**
8. **不抓取 Cookie、不模拟未公开 ChatGPT 接口、不静默回退到 API Key。**

## 2. 顶层架构

```text
┌──────────────────────────────────────────────────────────┐
│             ChatGPT Desktop / Codex Workspace            │
│ 开发、命令执行、失败诊断、日志分析、质量报告人工审查       │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                 User Interfaces                          │
│ babelcodex CLI / Windows+Linux GUI / MCP Server          │
└──────────────────────────┬───────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────┐
│                 Application Service                      │
│ start / status / cancel / validate / cleanup              │
└──────────────────────────┬───────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────┐
│                     Orchestrator                          │
│ 发现、任务状态、配置快照、重试、恢复、产物登记、日志        │
└──────────────┬───────────────────────────────┬───────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐  ┌────────────────────────┐
│ BabelDOC Worker Process      │  │ State / Artifact Store │
│                              │  │                        │
│ BabelDOC 0.6.x               │  │ job.json               │
│ async_translate              │  │ artifacts.json         │
│ BaseTranslator Bridge        │  │ qa-report.json         │
│ PDF Parse / Render           │  │ translation-cache.db   │
└──────────────┬───────────────┘  └────────────────────────┘
               │ 同步 translate 调用
               ▼
┌──────────────────────────────────────────────────────────┐
│                  Translation Gateway                     │
│ 请求标准化、缓存、短窗口批处理、验证、重试、结果分发        │
└──────────────┬──────────────┬──────────────┬─────────────┘
               │              │              │
               ▼              ▼              ▼
       Placeholder       Translation       Glossary /
       Validator         Cache             Context
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│                  CodexSdkTranslator                      │
│ 官方 openai-codex SDK、每文档 thread、串行 turn、恢复      │
└──────────────────────────────────────────────────────────┘
```

## 3. 进程模型

### 主进程 / Application Service

Application Service 负责配置、文档发现、状态、worker 生命周期、重试决策、产物登记和事件分发。CLI、GUI 和 MCP 都通过该服务执行。

主进程和 GUI 不直接加载 BabelDOC、DocLayout ONNX、RapidOCR 或大型字体资源。

### Codex Desktop / Codex CLI

Codex Desktop/CLI 是开发、监督和自动化控制面，不是 BabelCodex 的生产 PDF 引擎。Codex 可以通过 MCP 调用 BabelCodex，但内层文档翻译 thread 不得递归调用 MCP Server。

### BabelDOC Worker

每个文档使用独立 worker：

```text
start worker
→ load BabelDOC
→ load layout model
→ initialize translator bridge
→ run async_translate
→ emit progress
→ return artifacts
→ close translator
→ exit worker
```

建议使用 `multiprocessing.get_context("spawn")` 或独立 Python subprocess。

### Codex 进程位置

- **MVP**：Codex adapter 与 BabelDOC 在同一 worker。
- **Beta 后候选**：把 Codex 移至独立 translation service，通过本地 IPC 通信。

## 4.1 公开仓库与个人使用边界

公开仓库为：

```text
15699122/BabelCodex
```

仓库已于 2026 年 9 月 8 日创建并完成本地 `main` 与 `origin/main` 的首次同步。

BabelCodex 主要面向个人、本地 PDF 翻译，不以多租户 SaaS、公共翻译 API 或商业级 SLA 为目标。MIT License 仍允许修改、再分发和商业使用；“个人使用”是产品定位，不是额外的许可证限制。

公开仓库不得包含：

- 用户 PDF、译文 PDF；
- 任务状态、日志和缓存；
- Codex 登录状态、token、Cookie 或 API Key；
- 含敏感内容的 glossary；
- 没有再分发许可的测试文档。

## 4. 模块划分

```text
src/codex_babeldoc/
├── cli.py
├── application/
│   ├── service.py
│   ├── commands.py
│   └── queries.py
├── interfaces/
│   ├── cli/
│   ├── gui/
│   └── mcp/
├── backends/
│   ├── base.py
│   ├── babeldoc_internal.py
│   ├── babeldoc_v064.py
│   ├── babeldoc_worker.py
│   ├── worker_client.py
│   └── worker_protocol.py
├── core/
│   ├── config.py
│   ├── orchestrator.py
│   ├── lifecycle.py
│   ├── state.py
│   ├── errors.py
│   ├── events.py
│   └── artifacts.py
├── translation/
│   ├── models.py
│   ├── gateway.py
│   ├── batching.py
│   ├── placeholders.py
│   ├── validation.py
│   ├── retry.py
│   ├── cache.py
│   ├── glossary.py
│   └── context.py
├── translators/
│   ├── base.py
│   ├── codex_sdk.py
│   ├── mock.py
│   └── scripted.py
└── qa/
    ├── models.py
    ├── pdf_sanity.py
    ├── text_checks.py
    ├── layout_checks.py
    └── report.py
```

## 5. 模块职责

### `application/`

CLI、GUI 和 MCP 共用的应用服务层。提供任务启动、查询、取消、校验和清理等操作，屏蔽底层 Orchestrator、Worker 和状态存储。

### `interfaces/`

- `cli/`：命令行入口，兼容保留 `cbpdf`。
- `gui/`：Windows/Linux 桌面 UI，不直接导入 BabelDOC。
- `mcp/`：本地 stdio MCP Server，仅暴露受限的翻译和任务管理工具。

GUI host 技术验证位于仓库根目录的 `gui/`：Tauri 2 只启动固定的
`babelcodex-service` sidecar，React/TypeScript 前端通过版本化 JSONL 协议
调用 Application Service。Vite 浏览器开发模式使用 mock transport，不连接
系统 Python；打包后的 Tauri capability 只允许固定 sidecar、受控 TOML 配置
参数、stdin 写入和 sidecar kill。

### `backends/`

唯一允许接触 BabelDOC 内部 API 的区域。

- `base.py`：定义稳定 PDF backend contract。
- `babeldoc_v064.py`：只处理 BabelDOC 0.6.4 的 lazy import、配置映射、事件转换、异常转换。
- `worker_protocol.py`：定义版本化 JSON 协议。
- `babeldoc_worker.py`：独立进程入口。
- `worker_client.py`：主进程中的启动、事件读取、超时、终止和结果解析。

### `core/`

不依赖 BabelDOC 或 Codex 具体实现。

- `orchestrator.py`：discover / run one / run all / 任务状态迁移 / backend 选择 / retry 决策 / 产物保存；完成任务只在 artifact manifest 仍完整有效时安全跳过，缺失或被篡改的输出会重置为可执行恢复尝试。真实执行会写入 owning runner PID；初始化时仅将 dead/unknown PID 的遗留 active state 终止为 `WORKER_CRASHED`，不会自动重试。
- `state.py`：原子状态写入 / schema version / job fingerprint / config fingerprint / 错误类别 / artifact 索引 / runner PID。PID 仍存活的 active state 不会被另一入口回收，避免 CLI、GUI 和 MCP 之间互相误判。
- `artifact_manifest.py`：对持久化 job artifact 执行 output-root allowlist、存在性、大小、流式 SHA-256 和 PDF magic-header 校验；已记录 digest 不匹配时报告完整性失败，而不是更新旧 digest。
- `errors.py`：稳定错误分类。
- `events.py`：统一事件模型。

### `translation/`

翻译业务规则，不依赖 PDF 编排。

- `models.py`：`TranslationRequest`、`TranslationResult`、`TranslationBatch`、`ValidationResult`、`PlaceholderInventory`。
- `gateway.py`：normalize → cache lookup → batching → translator → validate → repair retry → cache save → return。
- `batching.py`：在 BabelDOC 同步 translator contract 之上实现短窗口批处理。
- `placeholders.py`：提取结构 token。
- `validation.py`：检查输出格式和占位符完整性。
- `retry.py`：根据错误类型决定重试方式。
- `cache.py`：SQLite 段落缓存。
- `glossary.py`：读取 `glossary/global.csv` 与 `glossary/documents/<pdf-stem>.csv`，执行文档级覆盖、CSV 管理、稳定版本 hash 和有界 terminology prompt。
- `context.py`：从 `context/<pdf-stem>.txt` 提取标题/摘要，归一化并限制上下文长度，生成稳定版本 hash。

glossary、context 和 thread state 均属于用户本地数据，不得提交到公开仓库。Orchestrator 按 PDF stem 构造合并 guidance，将 glossary/context 版本写入 `TranslationRequest` 和 cache key，并通过统一 `TranslatorSpec` 传给 in-process 与 subprocess translator。Codex thread prime 只接收已经截断的合并 prompt；thread state 只保存 provider、document ID、thread ID 和 generation，成功 prime 后才落盘。`max_turns_before_compact` 默认为 0；启用后在下一次翻译 turn 前优先调用官方 `Thread.compact()`，若 SDK 不支持或调用失败，则新建 thread、重新 prime 并在成功后原子轮换 state。
- GUI 的 Glossary 页面不直接读写用户文件，而是通过 sidecar 的 `list_glossary`、`save_glossary`、`get_context` 和 `save_context` scoped methods 调用同一个 Application Service。服务端只接受 global/document scope 和单个 document stem，并负责 CSV、UTF-8 sidecar、版本 hash、布尔值解析和原子保存。

### `translators/`

仅负责供应商调用。

- `codex_sdk.py`：SDK 初始化、账户认证状态、thread start/resume、turn run、native compact 与 rotation fallback、model/effort、SDK 异常转换、thread close。

### `qa/`

对输出 PDF 实施独立检查。

## 6. GUI 设计

GUI 目标平台为 Windows 和 Linux，首期目标产物为：

- Windows portable bundle；
- Linux portable bundle 或 AppImage。

首期不承诺所有发行版的原生安装包，也不优先采用单文件 executable。BabelDOC、ONNX、字体和模型资源更适合使用可控的目录结构打包。

GUI 必须通过 Application Service 调用任务，翻译工作必须在 Worker Process 中执行，以保证 UI 不阻塞。

GUI 计划功能：

- PDF 拖放和选择；
- 源语言/目标语言；
- 单语/双语输出；
- Codex 登录和 BabelDOC 环境检查；
- 任务进度、取消、错误和输出目录；
- glossary 选择；
- QA 报告查看。

## 7. MCP Server 设计

MCP Server 使用本地 stdio 模式启动：

```bash
babelcodex mcp serve
```

推荐工具：

- `babelcodex_doctor`
- `babelcodex_start_translation`
- `babelcodex_get_job`
- `babelcodex_list_jobs`
- `babelcodex_cancel_job`
- `babelcodex_validate_output`
- `babelcodex_cleanup_job`

长任务采用异步 job 模式：启动工具返回 `job_id`，Codex 后续查询任务状态和产物。

MCP Server 必须实施：

- 输入/输出目录 allowlist；
- 绝对路径和符号链接校验；
- 禁止目录穿越；
- 禁止覆盖源 PDF；
- 删除操作仅限 job 工作目录；
- 不提供任意 shell 执行、任意文件读取或任意路径删除。

内层 Codex 翻译 thread 不注册 BabelCodex MCP Server，嵌套调用深度固定为 1。

## 8. Worker 协议与打包

Worker 使用版本化 JSON 请求和结果协议：

```text
stdin/request file  →  request JSON
stderr              →  JSONL progress/log
stdout/result file  →  final JSON result
exit code           →  process status
```

GUI、CLI 和 MCP 都调用同一个 `worker_client`。

首期发布优先使用：

```text
Windows: portable directory bundle
Linux: portable directory or AppImage
```

打包工具在实现阶段通过 PyInstaller、Nuitka 等方案进行技术验证，不在架构层提前锁死。

## 9. 核心数据模型

### PDF 请求

```python
@dataclass(slots=True)
class PdfTranslateRequest:
    protocol_version: int
    job_id: str
    source_path: Path
    output_dir: Path
    working_dir: Path
    lang_in: str
    lang_out: str
    backend_name: str
    backend_version: str
    produce_mono: bool
    produce_dual: bool
    config_fingerprint: str
```

### 翻译请求

```python
@dataclass(slots=True)
class TranslationRequest:
    request_id: str
    document_id: str
    sequence: int
    source_text: str
    source_hash: str
    lang_in: str
    lang_out: str
    placeholders: PlaceholderInventory
    glossary_version: str | None
    context_version: str | None
```

### 翻译结果

```python
@dataclass(slots=True)
class TranslationResult:
    request_id: str
    translated_text: str
    validation_status: str
    validation_errors: tuple[str, ...]
    attempts: int
    cache_hit: bool
    latency_ms: int
```

### JobState

```text
schema_version
job_id
source_path
source_fingerprint
config_fingerprint
status
stage
attempts
error_category
error_code
safe_error_message
backend_name
backend_version
translator_name
model
codex_thread_id
started_at
updated_at
completed_at
artifacts
qa_status
```

### Artifact

```text
artifact_type
path
size
sha256
created_at
validated
```

## 10. 任务状态机

```text
discovered
  → validating_input
  → preparing_runtime
  → translating
  → rendering
  → validating_output
  → failed
  → retry_pending
  → cancelled
  → completed
```

错误不直接作为主状态，而是存放在 `error_category` / `error_code` / `stage` 中。

## 11. 占位符与输出验证

### 必须保护的内容

- BabelDOC rich-text tags
- 公式 token
- 成对 HTML-like tags
- `{1}`、`{v1}` 等编号 token
- URL / DOI / 引用
- XML entity
- 不应被翻译的结构字符

### 验证规则

- token 类型一致
- token 集合一致
- 每个 token 数量一致
- 成对标签配对正确
- 不新增未知 token
- 必要时保持 token 顺序
- 无越界 token ID
- 无 token 内容变形

应使用 multiset，而不是普通 set。

### 输出清洁检查

拒绝 Markdown fence、解释性前缀、模型说明、道歉、注释、整体包裹引号、空结果、只返回 `READY`、结构化批次缺失 request ID、返回额外 request ID。

### 修复重试

1. 普通严格翻译提示
2. 带具体错误的 exact-output repair prompt
3. 新 turn 或新 thread 重试
4. 仍失败则终止该 segment，并使 PDF job 失败

禁止把无效译文交给 BabelDOC。

## 12. GUI 技术框架

### 12.1 总体选型

GUI 采用以下目标技术栈：

```text
Tauri 2
React
TypeScript
Vite
Tailwind CSS
shadcn/ui / Radix UI
Lucide Icons
Vitest + React Testing Library
WebdriverIO GUI E2E
```

该选型参考了 `15699122/CopyPolish` 的当前实现。CopyPolish 已验证 Tauri 2、React、设置分区组件、单一 IPC 封装、能力检测、结构化错误、无边框窗口和跨平台 GUI E2E 等模式。

BabelCodex 不直接复制 CopyPolish 的 Rust 排版引擎，因为 BabelCodex 的 PDF 解析、排版和翻译核心已经由 Python、BabelDOC 和 Codex SDK 组成。

### 12.2 产品界面定位

BabelCodex GUI 定位为“个人 PDF 翻译工作台”，而不是聊天窗口或在线翻译网站。视觉方向已调整为白色主色调的 Vercel 风格，并完成简体中文界面重排（Linux/WSL implementation `LINUX_VERIFIED`，Windows packaged interaction 仍为 `WINDOWS_VERIFICATION_PENDING`）：白底、黑白灰层级、黑色主按钮、语义色仅用于状态表达，强调文档处理、进度和人工复核；旧暖纸张/墨水蓝方向不再作为目标。设置页保留暂未启用的 i18n 语言选项，不改变运行时 locale 或 sidecar contract。详细重构范围见 `docs/development-plan.md` Phase 9B。

首期 GUI 使用系统原生窗口装饰，以降低 Windows、Linux、Wayland、DPI 和无边框窗口兼容风险。后续若确有品牌化需求，再评估类似 CopyPolish 的自定义标题栏。

### 12.3 页面信息架构

左侧固定导航包含：

```text
新建翻译
任务
术语表
诊断
设置
```

主页面包括：

1. **新建翻译**：PDF 拖放/选择、语言、输出模式、术语表、高级选项和开始按钮。
2. **任务中心**：排队中、运行中、已完成、失败和已取消任务。
3. **任务详情**：阶段时间线、整体进度、当前 batch、Codex turns、缓存命中、产物和安全事件。
4. **完成结果**：单语 PDF、双语 PDF、QA 摘要、打开输出目录。
5. **术语表**：全局/文档 glossary、CSV 导入导出、启停和版本。
6. **诊断**：Codex 登录、BabelDOC、模型资产、sidecar、磁盘和输出目录检查。
7. **设置**：常规、翻译、输出、Codex、BabelDOC、MCP、隐私和外观分区。

GUI 不在 MVP 中嵌入复杂 PDF 编辑器或 PDF viewer；首期通过系统默认程序打开产物。

### 12.4 前端目录建议

```text
frontend/src/
├── App.tsx
├── routes/
│   ├── NewTranslationPage.tsx
│   ├── JobsPage.tsx
│   ├── JobDetailsPage.tsx
│   ├── GlossaryPage.tsx
│   ├── DiagnosticsPage.tsx
│   └── SettingsPage.tsx
├── components/
│   ├── shell/
│   ├── translation/
│   ├── jobs/
│   ├── diagnostics/
│   ├── glossary/
│   ├── settings/
│   └── ui/
├── hooks/
│   ├── useAppController.ts
│   ├── useBackendConnection.ts
│   ├── useJobs.ts
│   ├── useJobEvents.ts
│   ├── useTranslationForm.ts
│   ├── useDiagnostics.ts
│   ├── useSettingsLoader.ts
│   ├── useSettingsPersistence.ts
│   ├── useTheme.ts
│   └── useWindowControls.ts
├── lib/
│   ├── babelcodex.ts
│   ├── errors.ts
│   ├── events.ts
│   ├── settings.ts
│   └── formatters.ts
└── test/
```

`App.tsx` 只负责页面编排。复杂状态由 controller hook 组合，单个 hook 负责单一领域。

### 12.5 Tauri Rust 层

Tauri Rust 层是安全的桌面宿主，不实现 PDF 翻译业务。职责包括：

- 窗口生命周期；
- 文件选择对话框；
- 打开输出目录；
- 受控 sidecar 启动、重启和终止；
- stdin/stdout JSONL 协议转发；
- sidecar 健康状态；
- GUI 事件转发；
- capability 权限限制。

Rust 层不得实现 BabelDOC 调用、Codex prompt、glossary、任务重试、任务数据库或 PDF QA。

### 12.6 Python sidecar

GUI 通过固定的 BabelCodex Python sidecar 调用 Application Service：

```text
Tauri Host
    ↕ JSON Lines over stdin/stdout
babelcodex-service
    ├── Application Service
    ├── Orchestrator
    ├── BabelDOC Worker Process
    ├── Translation Gateway
    └── Codex SDK
```

GUI 不直接执行系统 Python，也不允许前端传入任意可执行文件或 shell 参数。发布包应包含固定名称的 sidecar，并通过 Tauri capability 限制其可执行范围和参数。

Windows 发布包必须将 Python service 预构建为 Windows sidecar executable，而不是要求用户安装或由 GUI 启动系统 Python。Tauri 的 `externalBin` 逻辑名称保持为 `binaries/babelcodex-service`；实际资源文件必须按 Tauri target triple 命名，并在 Windows bundle 构建前校验 `.exe` 文件、资源清单和 SHA-256。Windows 原生启动、文件选择器、路径 allowlist、输出目录打开、sidecar 终止和干净用户环境运行属于平台验收，不能由 WSL/Linux 的 Rust 编译检查替代。

### 12.7 Sidecar 通信协议

请求示例：

```json
{
  "protocolVersion": 1,
  "requestId": "req-...",
  "method": "start_translation",
  "params": {
    "sourcePdf": "/absolute/input.pdf",
    "targetLanguage": "zh"
  }
}
```

事件示例：

```json
{
  "type": "event",
  "event": "job_progress",
  "sequence": 128,
  "payload": {
    "jobId": "job-...",
    "stage": "translating",
    "current": 126,
    "total": 314,
    "overallProgress": 0.42
  }
}
```

规则：

- stdout 只传协议消息；
- 普通日志进入 stderr 或日志文件；
- 每个事件具有单调递增 `sequence`；
- GUI 断线重连后通过 `get_job` 校准状态；
- 请求和响应使用稳定 `requestId`；
- 错误只返回安全错误码和可行动提示。

### 12.8 GUI 状态模型

```typescript
type BackendConnectionState =
  | { status: "starting" }
  | { status: "ready"; protocolVersion: number }
  | { status: "reconnecting"; attempt: number }
  | { status: "incompatible"; expected: number; actual: number }
  | { status: "failed"; error: SafeCommandError };

type JobStatus =
  | "queued"
  | "validating_input"
  | "preparing_runtime"
  | "parsing"
  | "layout"
  | "translating"
  | "rendering"
  | "validating_output"
  | "completed"
  | "failed"
  | "cancelled";
```

前端不得使用多个相互独立的布尔值表达任务状态；任务状态以互斥枚举为准。

### 12.9 设置持久化

参考 CopyPolish 的设置加载/保存分离模式：

- hydration 防重复；
- 设置读取和保存分离；
- 保存防抖；
- 保存序号防旧请求覆盖新设置；
- `loading/ready/saving/saved/error` 状态；
- 损坏设置和备份恢复提示；
- schema version；
- 不支持能力自动降级。

建议路径：

- Windows：`%APPDATA%/BabelCodex/config.toml`；
- Linux：`$XDG_CONFIG_HOME/BabelCodex/config.toml`；
- 便携模式：显式指定程序目录下的配置。

### 12.10 能力检测

GUI 启动后读取：

```json
{
  "babeldocInstalled": true,
  "babeldocVersion": "0.6.4",
  "codexSdkInstalled": true,
  "codexAuthenticated": true,
  "ocrAvailable": false,
  "tableTranslationAvailable": false,
  "mcpAvailable": true,
  "sidecarProtocolVersion": 1
}
```

不可用能力必须禁用或显示警告，不能让用户误以为功能可用。

## 13. MCP 与 GUI 的关系

GUI 与 MCP 都调用同一个 Application Service：

```text
GUI → Tauri sidecar → Application Service
MCP → Python Application Service
CLI → Python Application Service
```

MCP Server 是 Codex 的自动化入口，GUI 是个人用户的可视化控制入口；二者不共享前端代码，但共享任务协议、状态模型和错误码。
- 当前 MCP 实现使用标准库 newline-delimited JSON-RPC，工具调用仍限制在 Application Service 的任务、artifact 和诊断边界内；`validate_output` 只读取 job artifact，`cleanup_job` 只删除 job-owned worker 子目录。工具参数严格 allowlist，活动 job 绑定进程内 `cancel_event`，服务关闭时主动发出取消信号；注册示例和剩余平台验证见 `docs/mcp.md`。

## 14. 测试与发布

GUI 测试分为：

1. React/Vitest：页面、表单、任务状态、设置、错误动作和 capability 降级。
2. Tauri/Rust：sidecar 参数限制、JSONL 解析、进程终止和安全错误转换。
3. Python contract tests：Application Service、任务协议、事件、取消和恢复。
4. WebdriverIO E2E：启动、选择 PDF、mock 翻译、进度、取消、完成、设置持久化、GUI 重启、窄窗口和 DPI。
5. 视觉 artifact：正常、运行中、失败、完成、诊断警告、设置和 sidecar 离线状态。

首期发布目标：

```text
Windows: BabelCodex-Windows-x64.zip
Linux: BabelCodex-Linux-x86_64.tar.gz
后续: BabelCodex-x86_64.AppImage
```

首期不优先采用单文件 executable。发布流程应包括依赖检查、sidecar 资源清单、许可证清单、SBOM 和 SHA-256 校验。

平台验证边界：

- Linux/WSL：已验证 React/Vitest、Python contract、JSONL 协议、Rust 编译、bundle audit 和 Linux `.deb`/AppImage 构建；目标 Linux 机器运行 smoke 仍需单独验收；
- Windows 原生：已验证 Windows `.exe` sidecar、Tauri NSIS/MSI packaged bundle、WebView2 探测、在项目根工作目录并显式传入受控 `--config` 后的 MSI 解包 sidecar JSONL smoke 和 GUI 进程级启动；文件对话框、完整路径语义、权限 allowlist、退出清理和干净用户环境 GUI 交互仍未完成；
- Windows 当前状态为“原生构建与包内 sidecar smoke 通过”，不是“可发布”；只有目标平台完整 packaged GUI smoke、签名/发布审计和剩余路径矩阵通过后，才能标记对应平台为可发布。具体执行错误、处置方式和未执行原因记录在 docs/compatibility.md。Windows 取消状态持久化修复已在 Linux 侧增加回归覆盖，Windows 原生完整测试仍需复验。
