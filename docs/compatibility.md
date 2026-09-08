# Compatibility Baseline

Last verified: 2026-09-08

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
```

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

Windows 原生验证已于 2026-09-08 在 E 盘 checkout 完成一轮。以下结果来自 Windows 11 x86-64（OS build 10.0.29648）：

- Python 3.12.13、uv 0.12.10；
- Node.js 24.19.0、npm 11.17.0；
- Rust 1.98.0、`stable-x86_64-pc-windows-msvc`；
- Visual Studio 2022 Build Tools 17.14.39，WebView2 runtime 已检测到；
- PyInstaller 6.22.2 用于本轮 sidecar 技术验证。

已完成：

1. `uv sync --locked --extra runtime --extra dev` 成功，解析并安装 95 个包；
2. `uv lock --check`、Ruff format/check 和 `uv run pytest -q` 通过（112 passed，3 deselected）；
3. `npm ci` 成功（158 packages，0 vulnerabilities），GUI Vitest 12 tests 通过，`npm run build` 通过；
4. Windows 原生 `cargo check` 通过；
5. `babelcodex-service-x86_64-pc-windows-msvc.exe` 已构建并通过 JSONL `list_jobs` smoke test，sidecar 退出码为 0；
6. NSIS 与 MSI bundle 已生成。MSI 隔离解包后，包内 sidecar 与 target-triple sidecar 的 SHA-256 一致，并再次通过 JSONL smoke test；
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
- Defender/SmartScreen 行为、签名发布、SBOM，以及 Linux target bundle；
- 可重复的无覆盖参数 `tauri build` 配置。本轮 bundle 使用了命令行 `bundle.icon` JSON 覆盖，未修改 WSL 源配置。

原生 Windows 仍是必要条件，WSL/Linux 结果不能替代上述尚未完成的 GUI 交互验收：

WSL/Linux 的 `cargo check`、浏览器端 Vitest 和 Vite build 可以作为先决检查，但不能替代原生 Windows packaged GUI smoke test。Windows 桌面边界测试应继续使用 mock transport/fixture；真实 Codex 集成另行标记为付费或 ChatGPT-plan integration test。

## Upgrade policy

Changing Python, BabelDOC, openai-codex or uv requires:

1. regenerating `uv.lock`;
2. running all local quality gates;
3. checking `doctor` output;
4. re-running BabelDOC warmup on a clean cache when practical;
5. updating this compatibility document;
6. validating at least one mock PDF fixture before enabling the new baseline.