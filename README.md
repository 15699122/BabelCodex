# BabelCodex

**BabelCodex** 是一款面向个人用户的、本地优先的高保真 PDF 翻译工具：使用 BabelDOC 负责 PDF 解析与排版，使用官方 Codex SDK 在 ChatGPT 登录下提供翻译能力。

项目主要面向个人、本地 PDF 翻译场景，不以多租户在线服务、公共翻译 API 或商业级 SLA 为目标。项目不会上传 PDF 到开发者自建服务器，但 PDF 文本会发送到用户当前登录的 Codex 服务。

## 功能

- **CLI**：`babelcodex`（兼容别名 `cbpdf`）提供完整的 PDF 翻译工作流；
- **GUI**：基于 Tauri 2 的 Windows/Linux 桌面应用，处于 Alpha 阶段，源码与开发包可构建；
- **本地 MCP Server**：可由 Codex 调用的 scoped 任务接口，仅暴露翻译/任务操作。

核心能力：

- 单语（mono）与双语（dual）PDF 输出；
- 按文档保持上下文的 Codex 会话（每文档一个 thread、串行调用）；
- 公式/富文本占位符保护与输出验证；
- 任务状态、目录批量运行、崩溃恢复与显式重试；
- 输出 PDF QA 检查（结构、文本质量、布局越界、渲染空白、未翻译比例、资源）；
- 本地术语表（glossary）与文档上下文管理；
- 翻译段落缓存；
- 可验证的产物清单（artifact manifest）。

## 技术栈

| 组成部分 | 技术 |
|---|---|
| PDF 解析/排版引擎 | BabelDOC 0.6.x |
| 翻译能力 | 官方 `openai-codex` SDK（ChatGPT 登录） |
| 命令行 | Python 3.11–3.12 + `uv` |
| 桌面 GUI | Tauri 2 + React/TypeScript + Vite |
| 本地协议 | JSONL sidecar（CLI/GUI/MCP 共用 Application Service） |

## 系统要求

- Python 3.11 或 3.12（推荐 3.12）
- `uv`
- 已通过 ChatGPT 登录的 Codex CLI / Codex SDK 会话
- BabelDOC 0.6.x

## 安装

```bash
cd BabelCodex
uv venv --python 3.12
uv sync --extra runtime --extra dev
```

`uv sync` 会安装 BabelDOC 与 `openai-codex` 等运行依赖。

### 登录 Codex

如果 Codex 已登录，Python SDK 会复用现有会话：

```bash
codex
```

选择 **Sign in with ChatGPT**。请勿仅为使项目工作而添加 OpenAI API Key —— 这会改变项目预期的计费/认证路径。

### 预热 BabelDOC

```bash
babeldoc --warmup
```

首次真实翻译前会下载/验证 BabelDOC 所需资源。

## 配置

配置文件使用 TOML 格式，默认路径为 `config/example.toml`。

常用配置项（详见 `config/example.toml`）：

```toml
[project]
input_dir = "incoming"       # 源 PDF 目录
output_dir = "translated"    # 输出 PDF 目录
state_dir = "state"          # 任务状态目录

[translation]
translator = "codex-sdk"     # 或 "mock"（不做真实翻译的管道测试）
lang_in = "en"
lang_out = "zh"
max_retries = 2

[babeldoc]
worker_mode = "subprocess"   # 或 "inprocess"
```

## 检查环境

```bash
uv run cbpdf --config config/example.toml doctor
```

`doctor` 返回非零退出码时表示关键运行检查失败或 Codex 未认证。

## 运行

从 `input/` 中的一个 PDF 开始：

```bash
uv run cbpdf --config config/example.toml run
```

GUI 与 MCP 模式使用相同的配置文件与应用程序服务。更多启动/开发方式见项目文档。

## 项目状态

BabelCodex 仍在开发中，当前定位为个人本地使用的 Alpha。

## 许可证

参见 [LICENSE](./LICENSE)。

## 文档

- 项目文档索引：[docs/README.md](./docs/README.md)
- 架构：[docs/architecture.md](./docs/architecture.md)
- 开发计划：[docs/development-plan.md](./docs/development-plan.md)
- 相关决策：[docs/decisions.md](./docs/decisions.md)
- 兼容性：[docs/compatibility.md](./docs/compatibility.md)

## 更多信息

用法细节、验证记录和 GUI 开发指引请参考项目文档。
