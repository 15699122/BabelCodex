# BabelCodex 文档索引

本文档是 BabelCodex 仓库文档的唯一入口。它说明每一份文档的读者、负责内容、不负责内容以及更新触发条件，防止同一事实被复制到多个文档后漂移。

## 文档归属总则

| 信息类型 | 唯一权威位置 |
|---|---|
| 产品功能、安装、使用、许可证 | `README.md` |
| 贡献流程、开发环境、测试命令、PR 规则 | `CONTRIBUTING.md` |
| 安全边界、漏洞报告 | `SECURITY.md` |
| 编码不变量、文档归属规则、模块设计规则 | `AGENTS.md` |
| 当前稳定架构、进程模型、数据流 | `docs/architecture.md` |
| 当前开发进度、剩余路线图、Phase 状态 | `docs/development-plan.md` |
| 架构决策（ADR） | `docs/decisions.md` |
| 参考项目调研（AiNiee、PDFMathTranslate、BabelDOC） | `docs/research/reference-projects.md` |
| 当前版本兼容矩阵、平台支持、升级策略 | `docs/compatibility.md` |
| 本地数据、发送到 Codex 的数据、日志与缓存边界 | `docs/privacy.md` |
| MCP 启动、工具、协议、安全范围 | `docs/mcp.md` |
| 构建、审计、签名、打包与发布操作 | `docs/release.md` |
| Windows 验证工作流（Linux→Windows 同步、状态模型） | `docs/development/cross-platform-validation.md` |
| 逐文件职责、公共入口、对应测试和维护提示 | `docs/development/codebase-map.md` |
| Linux 测试矩阵、markers、付费测试边界、增量验证策略 | `docs/development/testing.md` |
| 当前 Windows 验证状态、活跃队列、handoff | `docs/validation/windows.md` |
| Windows 历史验证运行记录与产物哈希 | `docs/validation/history/` |
| GUI 子项目开发与打包 | `gui/README.md` |

## 根目录文档

| 文档 | 读者 | 负责内容 | 不负责内容 |
|---|---|---|---|
| `README.md` | 用户、首次访问者 | 产品功能、技术栈、安装、认证、配置、使用、CLI/GUI/MCP 入口、隐私摘要、许可证 | 开发机信息、分支/commit、测试数量、Windows 验证轮次、内部开发顺序 |
| `CONTRIBUTING.md` | 贡献者 | 开发环境、分支/PR 流程、测试与 lint 命令、数据与凭证规则、文档同步要求 | 用户安装步骤（见 README）、ADR（见 decisions）、历史验证记录 |
| `SECURITY.md` | 用户、安全报告者 | 支持状态、安全边界、漏洞报告方式 | 架构论证、开发计划 |
| `AGENTS.md` | 后续编码 Agent | 项目目标、架构不变量、开发优先级、文档归属规则、模块设计规则、Windows 验证约束 | 用户文档、逐文件职责细节（见 codebase map） |

## `docs/` 下级文档

| 文档 | 读者 | 负责内容 | 不负责内容 |
|---|---|---|---|
| `architecture.md` | 开发者、架构师 | 当前稳定架构、进程边界、模块职责、核心模型、协议边界 | 进度状态、验证结果、参考项目调研 |
| `development-plan.md` | 项目负责人 | 当前进度快照、已完成能力、Phase 状态、剩余路线图、验收条件 | 逐日流水账、Windows 验证复述、产物哈希 |
| `decisions.md` | 开发者 | ADR：状态、日期、背景、决策、后果、替代方案 | 参考项目调研、工作日志 |
| `compatibility.md` | 开发者 | 当前版本矩阵、平台支持、上游 API 边界、升级策略 | 验证流水账、产物 SHA、临时事件 |
| `privacy.md` | 用户、开发者 | 本地数据、Codex 数据流、日志与缓存边界、公开仓库边界 | 安全漏洞报告流程（见 SECURITY.md） |
| `mcp.md` | 开发者、Codex 客户端 | MCP 启动、工具 schema、协议、安全范围、客户端注册 | MCP 源码逐函数说明（见 codebase map） |
| `release.md` | 发布责任人 | 发布门禁、构建、审计、签名、打包、发布后收尾 | 架构决策、开发计划 |
| `research/reference-projects.md` | 开发者 | AiNiee、PDFMathTranslate v1、PDFMathTranslate-next、BabelDOC 的借鉴与不复制分析 | 当前系统架构（见 architecture.md） |
| `development/codebase-map.md` | 开发者 | 逐文件职责、公共入口、调用关系、运行进程、对应测试、维护提示 | 架构级叙述（见 architecture.md） |
| `development/testing.md` | 开发者 | Linux 测试矩阵、markers、付费测试边界、增量验证策略（范围选择与升级规则）、GUI/集成/打包检查步骤 | Windows 验证结果（见 validation/） |
| `development/cross-platform-validation.md` | 开发者 | Linux→Windows 工作流、同步规则、状态模型、结果分类与处理、Windows 验证最小化与复验规则 | 具体某次验证结果（见 validation/） |

## `docs/validation/` 文档

| 文档 | 读者 | 负责内容 | 不负责内容 |
|---|---|---|---|
| `windows.md` | 验证责任人 | 当前 Windows 验证状态、活跃队列（WVQ）、下一轮 handoff、最近一次结果摘要 | 历史运行完整记录（见 history/） |
| `history/windows-YYYY-MM.md` | 验证责任人 | 对应月份的完整 Windows 运行记录、产物哈希、已解决 FAIL、截图证据 | 当前活跃队列（见 windows.md） |

历史验证记录只允许归档，不允许无理由删除或改写。归档时保留原始日期、结论和证据；历史 FAIL 不得改写为 PASS。

## 更新触发条件

- **新增、删除、重命名或改变模块职责**：更新 `docs/development/codebase-map.md`，必要时更新 `docs/architecture.md`。
- **改变 CLI 参数、sidecar/MCP 协议字段**：更新 `docs/mcp.md`、`README.md` 中的命令示例、`docs/development/codebase-map.md`。
- **完成或取消一个 Phase**：更新 `docs/development-plan.md`。
- **做出架构决策**：在 `docs/decisions.md` 新增 ADR。
- **完成一轮 Windows 验证**：结果摘要写入 `docs/validation/windows.md`，完整记录归档到 `docs/validation/history/`。
- **版本矩阵变化**：更新 `docs/compatibility.md`。
- **调整验证策略、测试层级或范围升级规则**：更新 `docs/development/testing.md`；Windows 侧最小化与复验规则同步到 `docs/development/cross-platform-validation.md`。
- **影响用户的使用方式或隐私边界**：更新 `README.md` 和 `docs/privacy.md`。

## 防漂移检查

`scripts/check_docs_inventory.py`（配合 `tests/test_docs_inventory.py`）自动检查：

- 所有受管理源码/脚本/配置文件是否在 codebase map 中登记；
- codebase map 是否引用不存在的文件；
- README 中的 CLI 命令是否至少对应一个已注册 parser 子命令；
- 文档间链接是否指向存在的文件。

该检查加入 Linux CI，不引入新依赖。

## 相关文档

- 架构总览：`docs/architecture.md`
- 开发计划：`docs/development-plan.md`
- 架构决策：`docs/decisions.md`
- 兼容基线：`docs/compatibility.md`
- 隐私边界：`docs/privacy.md`