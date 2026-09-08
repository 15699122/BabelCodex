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

**状态：Python sidecar 协议切片已完成；Tauri、跨平台打包和桌面端 E2E 待完成（2026 年 9 月 8 日）**

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
- 已覆盖协议往返、非法 JSON、协议错误、路径越界、shutdown 和无 shell 暴露测试；
- 尚未实现 Tauri 2 host、Windows/Linux target triple 打包、实时事件流和桌面 E2E。

验收：GUI 不直接导入 BabelDOC；前端不执行系统 Python 或任意 shell；翻译期间界面不冻结；Windows 和 Linux 最小 GUI 可运行；sidecar 只允许固定二进制和受控参数。

### Phase 9：GUI Alpha 与 Windows/Linux 打包

**优先级：P1 | 复杂度：XL | 预计：8–15 个开发日**

任务：

- AppShell、左侧导航和页面路由
- 新建翻译页：文件拖放、语言选择、单语/双语选项
- 任务中心、任务详情、完成结果和产物卡片
- Codex/BabelDOC/sidecar 环境检查
- 任务列表、阶段时间线、进度、取消、错误、输出目录
- glossary 选择和分区设置页面
- 暖纸张/墨水蓝视觉主题、浅色/深色模式和 UI 缩放
- Windows portable bundle
- Linux portable bundle 或 AppImage
- sidecar target triple 和资源清单
- GitHub Release workflow、SBOM 和 SHA-256 checksums

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

### Phase 10：Codex MCP Server Alpha

**优先级：P1 | 复杂度：L | 预计：5–10 个开发日**

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

### Phase 11：Glossary 与文档上下文

**优先级：P2 | 复杂度：L | 预计：5–8 个开发日**

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
