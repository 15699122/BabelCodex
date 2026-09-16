# BabelCodex Release Operations

本文档定义发布前的自动检查、产物构建、QA 报告与最终安全清单。当前发布目标仅为 Windows portable directory；Linux 仅用于开发和可执行验证，不生成当前发布包。

## 1. 发布前自动门禁

```bash
uv sync --extra runtime --extra dev
uv run pytest -q
uv run pytest -q -m integration tests/test_e2e_mock.py
uv run ruff check .
uv run ruff format --check .
python -m compileall -q src
git diff --check
```

预期：默认套件和 mock integration 套件全部通过；ruff/format/compileall/diff check 全绿。测试数量以当前运行结果为准，不在发布文档中固定。

## 2. 运行时健康检查

```bash
uv run cbpdf --config config/config.yaml doctor
```

确认 `python_supported`、`babeldoc_python`（0.6.x）、`openai_codex`、`codex_cli`/`codex_bundled_runtime` 均为有效值；`codex_authenticated` 在正式发布验收时为 `true`（需要真实 Codex/ChatGPT 登录）。

## 3. 输出质量报告（发布前对代表文档生成）

```bash
babelcodex inspect <job-id>
babelcodex validate <job-id>     # artifact manifest：缺失/篡改会失败
babelcodex qa <job-id>           # PDF QA battery；--verbose 包含 info findings
babelcodex qa --verbose <job-id>
```

- QA 报告写入 `translated/qa/<stem>.<artifact-type>.qa.json`，是**摘要**不是全文：只含 finding 代码、严重度、页码与短 detail，不含敏感段落文本。
- 任何 `error` 级 finding 会把 `qa_status` 置为 `failed` —— 输出异常永不标记为完全成功。
- `MAYBE_UNTRANSLATED` 等 `warning` 级 finding 不阻断，但应在发布验收中解释或确认。

## 4. 产物构建

### Python sidecar（Windows/Linux）

```bash
uv run --extra runtime --with pyinstaller pyinstaller \
    --clean --noconfirm scripts/babelcodex-service.spec
```

### GUI（Tauri 2，Windows portable）

```bash
cd gui
npm ci
npm run build        # React/TypeScript 产物
npm run build
powershell -ExecutionPolicy Bypass -File ..\scripts\build_windows_portable.ps1
powershell -ExecutionPolicy Bypass -File ..\scripts\audit_windows_portable.ps1 -Bundle ..\build\windows-portable
```

构建产物、SBOM 与 checksums 必须匹配 `docs/validation/windows.md` 中 `WVQ-005` 的发布安全验收条目。

## 5. 发布位置与发布安全

- 候选产物：Windows portable directory、sidecar 可执行文件、QA 报告样例、SBOM、SHA-256 checksums。
- 发布前检查：签名/证书、SmartScreen/Defender 表现、SBOM 完整性、checksum 一致性、不含用户 PDF/状态/日志/凭据（仓库规则 #15）。
- 参考：`README.md`（接口与定位）、`docs/validation/windows.md`（Windows 发布验证）、`docs/development/cross-platform-validation.md`（跨平台流程）。

## 6. 发布后收尾

- 更新 `docs/compatibility.md`（新增验证过的运行环境组合）。
- 更新 `README.md` Implemented/Experimental 分区。
- 在 `docs/validation/windows.md` 记录 Windows 侧已执行项与结果，未执行项保留 `WINDOWS_VERIFICATION_PENDING`。