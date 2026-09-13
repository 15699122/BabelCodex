# Linux 测试矩阵

本文档描述在 Linux 开发机上应当运行的验证命令、测试标记与付费测试边界。Windows 验证流程与结果见 `docs/validation/windows.md`；逐文件职责见 `docs/development/codebase-map.md`。

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

改动合入前至少运行：pytest、ruff、GUI 测试与构建，以及文档防漂移检查（若改动涉及文档或模块增删）。

## 测试标记（markers）

- **无标记**：默认单元测试。不得访问网络、不得消耗 Codex/ChatGPT 计划用量、不得调用真实翻译服务。
- **`integration`**：真实子进程的端到端测试（仍使用 scripted/mock translator，不产生付费用量）。默认被 deselect，需显式 `-m integration` 运行。
- **付费/真实 Codex 测试**：当前不存在。未来引入时必须额外标记（如 `live`）、默认跳过，并在本文件登记其边界与运行条件（架构不变量 8）。

## 付费测试边界

1. 单元测试只允许使用 `scripted` / `mock` translator；
2. 任何会建立真实 Codex 连接的测试必须显式标记且默认跳过；
3. `tests/test_e2e_mock.py` 属于 `integration`：真实子进程 + BabelDOC 管线 + scripted translator，不付费。

## 打包与 GUI 附加检查

- 打包 sidecar：`uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec`
- 打包产物校验：`uv run python scripts/check_gui_bundle.py <bundle-dir>`
- GUI E2E（WebdriverIO）、Windows 打包与人工验证见 `gui/README.md` 与 `docs/validation/windows.md`。
