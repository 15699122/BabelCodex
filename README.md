# BabelCodex

**BabelCodex** 是一款面向个人用户的、本地优先的高保真 PDF 翻译工具：使用 BabelDOC 负责 PDF 解析与排版，使用官方 Codex SDK 在 ChatGPT 登录下提供翻译能力。

项目主要面向个人、本地 PDF 翻译场景，不以多租户在线服务、公共翻译 API 或商业级 SLA 为目标。项目不会上传 PDF 到开发者自建服务器，但 PDF 文本会发送到用户当前登录的 Codex 服务。

项目计划提供：

- `babelcodex` CLI；
- Windows/Linux GUI 可执行文件；
- 可由 Codex 调用的本地 MCP Server。

项目名称、公开仓库计划与个人使用边界见 `docs/decisions.md`。

## Architecture

```text
incoming/*.pdf
     |
     v
+-------------------+
| User Interfaces   |  CLI / Windows + Linux GUI / MCP Server
+-------------------+
     |
     v
+-------------------+
| Application       |  shared service API for all interfaces
| Service           |
+-------------------+
     |
     v
+-------------------+
| Orchestrator      |  discovery / state / retry / logging
+-------------------+
     |
     v
+-------------------+
| BabelDOC Worker   |  single-pass PDF parse / layout / render
│ Process           │  formula placeholders / mono + dual output
+-------------------+
     |
     | synchronous BaseTranslator bridge
     v
+-------------------+
| Translation       |  queue / batch / validate / retry / cache
| Gateway           |
+-------------------+
   |            |
   |            +--> mock / scripted tests
   |
   +--> CodexSdkTranslator
             |
             v
       openai-codex SDK
             |
             v
       existing Codex login
       (ChatGPT plan session)
```

## Why this shape?

1. **BabelDOC owns document fidelity.** It parses the PDF into an intermediate representation, protects formulas/rich text via placeholders, and reconstructs mono/dual PDFs.
2. **Codex owns language generation.** The translator bridge sends only the text segments BabelDOC asks to translate.
3. **Authentication is separated from document processing.** `openai-codex` reuses existing Codex authentication, including ChatGPT sign-in.
4. **BabelDOC instability is contained.** BabelDOC imports remain under `src/codex_babeldoc/backends/`, with a version-specific compatibility adapter and worker process.
5. **The default production path is single-pass.** Translation Gateway batching does not require running BabelDOC twice.
6. **CLI, GUI and MCP share one Application Service.** Interface-specific code must not duplicate translation orchestration.

详细规划文档：

- `docs/architecture.md`：总体架构与模块边界
- `docs/development-plan.md`：阶段、工作包、里程碑与验收标准
- `docs/decisions.md`：参考项目对比与架构决策记录
- `docs/privacy.md`：本地数据、Codex 数据流和公开仓库边界
- `docs/compatibility.md`：已验证的 Python、uv、BabelDOC 和 Codex SDK 基线
- `CONTRIBUTING.md`：贡献流程与数据规则
- `SECURITY.md`：安全边界与漏洞报告方式

## 产品定位

BabelCodex 主要面向个人、本地使用。用户需要自行确认待翻译文档的合法使用权限，并自行承担向 Codex 服务发送文档文本所产生的账户、隐私和使用责任。

当前 MIT License 允许修改、再分发和商业使用；“个人使用属性”描述的是项目当前的产品目标，不是额外的许可证限制。

## Status

### Implemented

- Project CLI (`cbpdf`, primary command: `babelcodex`)
- TOML configuration
- PDF discovery from `incoming/`
- SHA-256 based job identity
- JSON state files
- artifact manifest（大小、SHA-256、PDF header）和可验证的 completed-job skip / `--force`
- 保守 worker crash recovery：遗留 dead/unknown runner 标为 `WORKER_CRASHED`，仅通过显式 retry 重新开始
- 按错误类别的操作员可见 retry policy（`retry_policy` 覆盖、`max_retries` 为上限；认证错误不会自动循环）
- pipeline 元数据：`inspect` 直接可见 BabelDOC 版本、源 PDF 页数与 part-resume 评估（当前单遍流水线不支持）
- `babelcodex cleanup [--dry-run]` + `work_retention_days`（默认 7 天；活动任务永不清理）
- bounded retry with backoff
- file + console logging
- Codex Python SDK translator adapter
- one long-lived Codex thread per document
- serialized Codex calls for thread safety
- BabelDOC `BaseTranslator` bridge
- BabelDOC 0.6.x internal high-level async pipeline wrapper
- monolingual / bilingual output switches
- OCR/layout compatibility settings exposed in config
- mock translator for pipeline tests
- shared Application Service for CLI, GUI and MCP
- versioned glossary/context guidance with bounded Codex prompt input
- `babelcodex glossary list|import|export` local glossary management
- bounded PDF metadata/opening-page context extraction
- GUI glossary and document-context editor through the scoped sidecar protocol
- provider-neutral Codex thread identity persistence and resume contract
- placeholder and structured-output validation
- exact-output retry on validation failure
- BabelDOC worker process and versioned protocol
- paragraph translation cache independent of BabelDOC cache
- scoped local stdio MCP Server
- `babelcodex inspect|validate|retry <job-id>` 任务运维入口
- PDF QA battery：`babelcodex qa <job-id>`（L0/L1/L2、越界、渲染空白、未翻译比例、磁盘；JSON 报告 + 人类摘要）
- 输出异常不标记为完全成功：任何 QA error 使 `qa_status=failed`
- 发布操作文档：`docs/release.md`

### Experimental / needs validation on your machine

- End-to-end BabelDOC 0.6.4 + `openai-codex` execution
- Exact Codex model/effort combination available to your account
- Large-document throughput and ChatGPT-plan usage behavior
- Formula/rich-text placeholder integrity under Codex translation
- Scanned-PDF OCR quality
- Terminology consistency for very long books
- real Codex account/thread resume behavior and long-thread stability
- GUI glossary/context editor behavior against a packaged sidecar and clean user profile

### Planned

- batch translation requests to reduce Codex turn overhead
- 全量像素级视觉回归与字体级缺字检测
- experimental two-phase extract/translate/render mode
- remaining Windows/Linux GUI release audit and target-machine validation
- Codex client registration and packaged MCP smoke validation

## Planned interfaces

### CLI

```bash
babelcodex doctor
babelcodex translate document.pdf
babelcodex run
babelcodex inspect <job-id>
babelcodex validate <job-id>
babelcodex retry <job-id>
babelcodex qa <job-id>
babelcodex cleanup [--dry-run]
```

`cbpdf` will remain as a compatibility alias during migration.

### GUI

The GUI will use **Tauri 2 + React/TypeScript** and call the same Python Application Service as the CLI through a fixed `babelcodex-service` sidecar. BabelDOC and Codex work remain inside backend worker processes. Planned release formats are a Windows portable bundle and a Linux portable bundle/AppImage.

The first GUI is a personal PDF translation workbench with New Translation, Jobs, Job Details, Glossary, Diagnostics and Settings pages. It will not initially embed a full PDF editor or viewer.

### Local MCP server

The local MCP server uses stdio and exposes only scoped translation/job tools:

```bash
uv run babelcodex --config config/example.toml mcp serve
```

It shares the Python Application Service and persisted job state with the CLI
and GUI. It never exposes arbitrary shell execution, unrestricted file reads,
or unrestricted file deletion.
See `docs/mcp.md` for registration, tool scope and protocol details.
Packaged/clean-environment smoke validation and release audit remain release
tasks.

## Requirements

Recommended development environment:

- Python 3.11 or 3.12 (3.12 recommended)
- `uv`
- Codex CLI / Codex SDK authenticated with ChatGPT
- BabelDOC 0.6.x

## GUI development stack

- Tauri 2 desktop shell;
- React + TypeScript + Vite frontend;
- Tailwind CSS + shadcn/ui/Radix UI + Lucide Icons;
- Python `babelcodex-service` sidecar;
- Vitest/React Testing Library and WebdriverIO GUI E2E.

The GUI does not execute system Python or arbitrary shell commands. Tauri permissions must restrict execution to the fixed sidecar and its validated arguments.

## Installation

```bash
cd BabelCodex
uv venv --python 3.12
uv sync --extra runtime --extra dev
```

If your `uv` version uses dependency groups differently, the equivalent pip installation is:

```bash
python -m pip install -e ".[runtime,dev]"
```

### Authenticate Codex

If Codex is already signed in, the Python SDK should reuse the existing session.

Otherwise run:

```bash
codex
```

and choose **Sign in with ChatGPT**.

Do **not** add an OpenAI API key merely to make this scaffold work; doing so changes the intended billing/auth path.

## Warm up BabelDOC

After installing BabelDOC:

```bash
babeldoc --warmup
```

This downloads/verifies its required assets before the first real translation.

## Check environment

```bash
uv run cbpdf --config config/example.toml doctor
```

`doctor` returns a non-zero status when critical runtime checks fail or Codex is not authenticated. It reports the SDK-bundled Codex runtime separately from a system-wide `codex` command.

Expected fields include detection of:

- `codex`
- `babeldoc`
- `openai_codex`
- BabelDOC Python package

## First safe pipeline test

Before consuming Codex usage, change:

```toml
[translation]
translator = "mock"
```

Place a small PDF into `incoming/` and run:

```bash
uv run cbpdf --config config/example.toml run
```

This exercises the BabelDOC pipeline with a deliberately bad `[MOCK]` translation, useful only for integration testing.

## Codex translation mode

Restore:

```toml
[translation]
translator = "codex-sdk"
```

Then:

```bash
uv run cbpdf --config config/example.toml run
```

or one specific PDF:

```bash
uv run cbpdf --config config/example.toml one incoming/example.pdf
```

Force a completed document to run again:

```bash
uv run cbpdf --config config/example.toml one incoming/example.pdf --force
```

## GitHub

The public repository is:

```text
15699122/BabelCodex
```

The initial public baseline was published on September 8, 2026. Local `main` tracks `origin/main`.

The repository will contain source code and documentation only. User PDFs, generated outputs, state, logs, caches, credentials and private glossary data must remain ignored or outside the repository.

## Output layout

```text
BabelCodex/
├─ incoming/          # source PDFs
├─ translated/        # BabelDOC PDF outputs
├─ state/             # job JSON + BabelDOC working data
├─ logs/              # cbpdf.log
├─ config/
│  └─ example.toml
├─ src/codex_babeldoc/       # module rename planned separately
│  ├─ backends/
│  │  └─ babeldoc_internal.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ orchestrator.py
│  │  └─ state.py
│  └─ translators/
│     ├─ base.py
│     ├─ codex_sdk.py
│     ├─ mock.py
│     └─ openai_compatible.py
└─ tests/
```

## Important design limitation: Codex is not an OpenAI-compatible endpoint

This project does **not** pretend that ChatGPT Plus creates an `OPENAI_API_KEY` or a local OpenAI-compatible URL.

Instead, it uses the official Codex Python SDK as a translator adapter. The SDK retains a Codex thread and forwards each BabelDOC translation request as a Codex turn. This is the bridge between BabelDOC and a ChatGPT-authenticated Codex session.

## Performance caveat

The MVP intentionally favors correctness and inspectability over throughput. BabelDOC can produce many translation calls, while a Codex turn has more overhead than a normal low-latency translation API request. The adapter therefore sets `qps = 1` by default and serializes access to a single thread.

The next performance milestone should be a **batching bridge**: queue several BabelDOC segments, translate them in one structured Codex turn, verify placeholder IDs, then fan the answers back to waiting callers.

## Compatibility strategy

As of the scaffold date, BabelDOC 0.6.x exposes the PDF pipeline through:

```python
babeldoc.format.pdf.high_level.async_translate
```

and its CLI exposes `--files`, `--lang-in`, `--lang-out`, mono/dual controls, output path, QPS, OCR/layout-related options, and OpenAI-compatible translator arguments.

However, BabelDOC's own README warns that direct APIs should be treated as internal. For that reason, **never import BabelDOC internals outside `backends/babeldoc_internal.py` or translator bridge construction**.

## Safety / data notes

- PDF text sent to Codex is transmitted to the Codex service under the authentication/account settings of the signed-in Codex user.
- The scaffold does not scrape browser cookies or emulate undocumented ChatGPT endpoints.
- Secrets should never be committed to the repository.
- `incoming/*.pdf`, generated outputs, logs, and state are ignored by Git by default.

## Recommended development sequence

1. Create the public `15699122/BabelCodex` repository and synchronize the local baseline.
2. Run unit tests and `doctor`.
3. Lock Python, uv, BabelDOC and Codex SDK versions.
4. `babeldoc --warmup`.
5. Test a 1–2 page PDF with `mock`.
6. Add placeholder validation and exact-output retry.
7. Add the BabelDOC worker process and structured protocol.
8. Test the same PDF with `codex-sdk`.
9. Add Translation Gateway batching and cache.
10. Implement GUI and MCP only through the shared Application Service.

## Tests

```bash
uv run pytest
```

The included tests do not require a live Codex or BabelDOC installation.

## License

This scaffold is MIT licensed. BabelDOC and Codex SDK remain subject to their own licenses and terms.
