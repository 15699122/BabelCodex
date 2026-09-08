# Architecture Decisions

本文档记录项目在参考 AiNiee、PDFMathTranslate v1、PDFMathTranslate-next 与 BabelDOC 后形成的关键架构决策。

相关文档：

- 架构总览：`docs/architecture.md`
- 开发计划：`docs/development-plan.md`
- 项目说明：`README.md`
- 架构约束：`AGENTS.md`

## 1. 总体决策

### 决策

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

### 原因

- 让 BabelDOC 负责 PDF fidelity
- 让 Codex 负责语言生成
- 让项目负责任务编排、验证、缓存和恢复
- 更接近 PDFMathTranslate-next 的参考实现
- 避免主进程加载 ONNX/字体资源
- 避免主进程修改 BabelDOC 全局对象
- 避免默认执行两遍 BabelDOC

### 不采用

- BabelDOC CLI 黑盒调用
- 自行复制 PDFMathTranslate v1 的 PDF content stream 重写
- 主进程修改 BabelDOC 全局对象
- 默认执行两遍 BabelDOC 的 Extract/Render
- 抓取 ChatGPT Cookie
- 调用未公开 ChatGPT HTTP API
- 将 ChatGPT 登录伪装成 OpenAI-compatible endpoint
- Codex 失败后静默切换到付费 API Key
- 在同一个 Codex thread 上并发执行多个 turn

## 2. 参考项目分析

### AiNiee

#### 借鉴

- BabelDOC 应作为嵌入式 Python PDF 引擎
- PDF 翻译可以接入独立的通用翻译系统
- PDF 文本应转换成可缓存的翻译单元
- 单语和双语 PDF 应复用同一次 BabelDOC 输出
- 翻译结果需要独立持久化
- PDF Reader、Translator、Writer 应保持职责分离

#### 不直接复制

- 主进程 monkey-patch `ILTranslator`
- 替换 BabelDOC 全局 executor
- 依赖私有 `_WorkItem`
- 仅用原文字符串匹配译文
- 成功或失败后无条件删除临时状态
- 两遍解析时假设段落顺序必然一致

### PDFMathTranslate v1

#### 借鉴

- 高保真的关键不是"翻译更强"，而是：
  - 识别正文和非正文区域
  - 保护公式、图片、表格和图注
  - 保留字符字体、坐标和图形关系
  - 译文适应原始段落边界
  - 正确生成目标语言字体
  - 原始公式对象不进入普通自然语言翻译
  - 单语和双语输出需要共享同一 PDF 处理结果

#### 不复制

- pdfminer 字符级 PDF 重写
- 手工 CID 字体编码
- 手工生成 `TJ/Tm` 等 PDF 指令
- 公式坐标重新定位
- 大量针对 PDF 生成器的兼容 hack
- 自建完整 PDF 排版引擎

这些职责全部交给 BabelDOC。

### PDFMathTranslate-next

#### 借鉴

- 使用 BabelDOC 高层 Python API
- 通过 `BaseTranslator` 扩展翻译服务
- PDF 核心运行在独立子进程
- 使用统一 Request/Result 协议
- 结构化转发进度、错误和产物信息
- 主程序与具体 PDF 内核解耦
- 记录 part、耗时、token 和输出信息
- 对依赖冲突严重的新内核使用隔离环境

这是与当前目标最接近的工程参考。

## 3. 关键决策

### ADR-001：默认使用单次 BabelDOC 高层流水线

**状态：已接受**

默认使用单次 `async_translate` 流水线，通过 Translation Gateway 在同步 translator contract 之上实现批处理。

原因：少一次 PDF 解析和 ONNX 模型运行，避免 extraction/render 段落错位，不依赖 BabelDOC 内部 stage monkey-patch，同时与 PDFMathTranslate-next 的参考实现一致。

Two-phase 模式降级为实验模式，不进入首个稳定版关键路径。

### ADR-002：BabelDOC 运行在独立 Worker Process

**状态：已接受**

每个文档使用独立 worker，通过版本化 JSON 协议通信。

原因：隔离 BabelDOC 内部 API、ONNX/字体资源、全局状态、stdout 污染、超时和崩溃风险。

### ADR-003：Translation Gateway 负责正确性与吞吐

**状态：已接受**

在 translator adapter 之上引入 Translation Gateway，实现短窗口批处理、稳定 request ID、占位符验证、输出清洁检查、精确重试和缓存。

### ADR-004：不自行维护 PDF 内容流和公式排版

**状态：已接受**

不复制 PDFMathTranslate v1 的 PDF content stream 重写、CID 编码、公式坐标重定位和手工排版逻辑，全部交给 BabelDOC。

### ADR-005：不默认执行两遍 BabelDOC

**状态：已接受**

AiNiee 的两遍 Extract/Render 方式保留为实验方向，但默认不启用，因为它更深地依赖 BabelDOC 内部 hook、调用顺序和段落对齐假设。

### ADR-006：使用官方 `openai-codex` SDK

**状态：已接受**

使用官方 SDK 复用现有 Codex/ChatGPT 登录状态；不通过 CLI subprocess 解析终端文本作为主翻译路径。

### ADR-007：不抓取 Cookie、不模拟未公开接口

**状态：已接受**

不抓取浏览器 Cookie、不模拟未公开 ChatGPT HTTP 接口、不将 ChatGPT 登录伪装成 OpenAI-compatible endpoint。

### ADR-008：不静默回退到 API Key

**状态：已接受**

Codex 认证失败时要求用户重新认证，不自动切换到单独计费的 OpenAI API。

### ADR-009：不在同一个 Codex thread 上并发调用

**状态：已接受**

每个文档一个 thread，每个 thread 一个 turn lock；通过 batching 降低 turn 数，而不是并发操作同一 thread。

## 4. 兼容策略

### 首期目标

```text
Python 3.12
BabelDOC 0.6.4
openai-codex 锁定版本
```

### 兼容边界

以下 BabelDOC import 只能位于 `src/codex_babeldoc/backends/`：

```text
babeldoc.format.pdf.high_level
babeldoc.format.pdf.translation_config
babeldoc.translator.translator
babeldoc.docvision.*
```

### 版本升级

未来支持新版本时新增版本化适配器，例如：

```text
babeldoc_v064.py
babeldoc_v06x.py
babeldoc_v07x.py
```

不要在全项目散落 BabelDOC 版本判断。

### 配置映射

项目配置不能直接等于 BabelDOC `TranslationConfig`，必须经过：

```text
Stable AppConfig
→ BabelDocCompatibilityMapper
→ Version-specific TranslationConfig
```

## 5. 错误分类与重试

```text
CONFIG_INVALID
INPUT_NOT_FOUND
INPUT_PDF_INVALID
PDF_NO_EXTRACTABLE_TEXT
PDF_SCANNED_DOCUMENT
BABELDOC_NOT_INSTALLED
BABELDOC_VERSION_UNSUPPORTED
BABELDOC_ASSET_MISSING
BABELDOC_RUNTIME_ERROR
BABELDOC_NO_FINISH_RESULT
CODEX_NOT_INSTALLED
CODEX_NOT_LOGGED_IN
CODEX_AUTH_EXPIRED
CODEX_MODEL_UNAVAILABLE
CODEX_TIMEOUT
CODEX_OVERLOADED
CODEX_EMPTY_OUTPUT
CODEX_INVALID_OUTPUT
PLACEHOLDER_MISMATCH
BATCH_RESPONSE_MISMATCH
WORKER_TIMEOUT
WORKER_CRASHED
OUTPUT_PDF_MISSING
OUTPUT_PDF_INVALID
DISK_FULL
CANCELLED
UNKNOWN
```

认证、模型不可用、输入损坏、磁盘不足和 BabelDOC 不兼容默认不自动重试；网络超时、服务过载、空响应、非法输出和占位符错误可进行有界重试。

## 6. 后续演进路径

### 短期

- 完成 MVP
- 完成 Translation Gateway
- 完成 SQLite 缓存
- 完成 glossary

### 中期

- 完成 PDF QA
- 完成 worker 恢复
- 完成 thread 轮换
- 评估 part-level resume

### 长期

- 评估 Two-phase 模式
- 评估多供应商翻译
- 评估 Web SaaS
- 评估更多 PDF 内核

## 7. 风险控制

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
| Two-phase 段落错配 | 高 | 非默认、严格对齐、后续研究 |

## 8. 产品与发布决策

### ADR-010：项目名称采用 BabelCodex

**状态：已接受**

产品名称采用 **BabelCodex**，公开仓库为 `15699122/BabelCodex`。仓库已于 2026 年 9 月 8 日创建并完成首次推送。

名称同时覆盖 BabelDOC PDF 引擎与 Codex 翻译能力，适用于 CLI、桌面 GUI 和 MCP Server。

### ADR-011：公开仓库与个人本地使用定位并存

**状态：已接受**

GitHub 仓库计划设置为 public，但产品主要面向个人、本地 PDF 翻译。

这不是额外的许可证限制。项目继续使用 MIT License；“个人使用”描述产品目标，不禁止用户依法修改、再分发或商业使用。

公开仓库不得包含用户 PDF、译文、日志、任务状态、翻译缓存、Codex 登录状态、token、Cookie、API Key 或私有 glossary。

### ADR-012：CLI、GUI 和 MCP 共用 Application Service

**状态：已接受**

CLI、Windows/Linux GUI 和 MCP Server 必须调用同一个 Application Service，不得各自复制翻译编排、状态管理、重试和产物处理逻辑。

目标结构：

```text
CLI / GUI / MCP
       ↓
Application Service
       ↓
Orchestrator
       ↓
BabelDOC Worker + Translation Gateway
```

### ADR-013：GUI 不直接加载 BabelDOC

**状态：已接受**

GUI 只负责交互、任务展示和控制。BabelDOC、ONNX、RapidOCR、字体资源和 Codex 翻译均由 Worker/后台服务负责。

首期目标平台为 Windows 和 Linux，优先发布 portable bundle；Linux 后续可增加 AppImage。首期不承诺所有 Linux 发行版原生安装包，也不优先采用单文件 executable。

### ADR-014：MCP 使用本地 stdio 和异步 Job 模式

**状态：已接受**

MCP Server 通过本地 stdio 启动：

```bash
babelcodex mcp serve
```

长时间 PDF 翻译不阻塞单个 MCP 调用：启动工具返回 `job_id`，后续通过查询工具获取进度、错误、产物和 QA 状态。

MCP 只提供受限的翻译和任务管理工具，不提供任意 shell 执行、任意文件读取或任意路径删除。

### ADR-015：MCP 使用路径 allowlist 并阻止 Codex 递归

**状态：已接受**

MCP Server 必须对输入和输出目录实施 allowlist、绝对路径校验、符号链接解析和目录穿越防护。

内层 Codex 翻译 thread 不注册 BabelCodex MCP Server，嵌套调用深度固定为 1，避免外层 Codex → MCP → 内层 Codex → MCP 的递归。

### ADR-016：发布优先使用 portable bundle

**状态：已接受**

Windows 首期发布 `BabelCodex-Windows-x64.zip`，Linux 首期发布 portable tarball，后续再评估 AppImage。

打包工具通过 PyInstaller、Nuitka 等方案进行技术验证，不在架构层提前锁死。发布包必须包含所需运行时、BabelDOC 资产说明、许可证清单和 SHA-256 校验文件，但不得包含开发者或用户的认证状态。

### ADR-017：GUI 采用 Tauri 2 + React/TypeScript

**状态：已接受，需先通过技术验证**

GUI 参考 `15699122/CopyPolish` 的工程实践，采用 Tauri 2、React、TypeScript、Vite、Tailwind CSS、shadcn/ui/Radix UI、Lucide Icons，并使用 Vitest、React Testing Library 和 WebdriverIO 进行测试。

原因：

- CopyPolish 已验证该技术栈在 Windows/Linux 桌面应用中的可行性；
- 前端组件、状态和 E2E 测试生态成熟；
- GUI 与 Python PDF 核心可以通过 sidecar 清晰隔离；
- 适合构建任务中心、诊断页、设置页和多状态进度界面。

如果 Tauri sidecar 无法稳定承载 BabelCodex 发布包，再评估 PySide6 等 Python 原生 GUI 方案。

### ADR-018：GUI 通过固定 Python sidecar 调用 Application Service

**状态：已接受**

GUI 不直接调用系统 Python、不直接导入 BabelDOC、不直接初始化 Codex SDK，也不复制 Orchestrator。Tauri 只管理固定的 `babelcodex-service` sidecar，并通过版本化 JSONL 协议调用 Python Application Service。

目标结构：

```text
Tauri 2 Host
  → fixed babelcodex-service sidecar
  → Python Application Service
  → Orchestrator / BabelDOC Worker / Translation Gateway
```

### ADR-019：Tauri sidecar 使用最小 capability 权限

**状态：已接受**

Tauri shell capability 只允许启动固定 sidecar 和预定义参数，不允许任意 shell、任意 executable、任意 `-c` 参数或任意命令拼接。sidecar 使用平台 target triple 命名并随 Windows/Linux portable bundle 发布。

### ADR-020：GUI、CLI、MCP 共用任务状态和事件协议

**状态：已接受**

GUI、CLI 和 MCP 使用同一个 Application Service、JobState、ProgressEvent、ErrorCode 和 Artifact 模型。GUI 断线重连后通过查询任务状态校准，而不只依赖瞬时事件。

### ADR-021：MCP 与 GUI 都采用异步 Job 交互

**状态：已接受**

PDF 翻译属于长任务。GUI 启动任务后显示 `job_id` 和事件流；MCP 启动工具返回 `job_id`，Codex 通过后续查询获取进度和产物。两者不得阻塞在一次请求中等待完整 PDF 翻译结束。

### ADR-022：GUI 首期采用任务工作台而非实时文本编辑器

**状态：已接受**

参考 CopyPolish 的清晰分区和设置管理，但不复制其“输入即实时处理”的交互。BabelCodex GUI 以新建翻译、任务中心、任务详情、完成结果、术语表、诊断和设置为主要页面。

首期不实现内嵌 PDF 编辑器、复杂 PDF viewer、页面级人工重排或多任务并行控制。

### ADR-023：GUI 发行版优先使用 portable bundle

**状态：已接受**

Windows 首期发布 portable ZIP，Linux 首期发布 portable tarball，后续评估 AppImage。发布包必须包括固定 sidecar、资源清单、许可证和 SHA-256 校验，不包括用户数据、登录状态或开发环境。
