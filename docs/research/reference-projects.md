# 参考项目调研

本文档记录 BabelCodex 设计时调研的开源项目、借鉴点与明确不复制的原因。它是分析性文档，不记录工作日志；当前系统结构见 `docs/architecture.md`，架构决策（ADR）见 `docs/decisions.md`。

## AiNiee

- **定位**：面向多平台 LLM 的通用翻译工具，覆盖字幕、文本等批量翻译场景。
- **借鉴**：
  - 批量请求合并与结果回填的思路（对应 `translation/batching.py`、`translation/gateway.py`）；
  - 缓存与重试分离为独立层的设计；
  - “翻译输出必须与占位符严格对应”的校验意识（`translation/validation.py`）。
- **不复制**：其管线面向纯文本，不处理 PDF 解析与排版；其直连各家 HTTP API 的适配方式与本项目“ChatGPT 会话认证 + 官方 SDK”的边界冲突（AGENTS 不变量 2、3）。

## PDFMathTranslate（v1）

- **定位**：学术 PDF 翻译，保留双栏与公式布局。
- **借鉴**：两阶段“先抽取、后翻译、再回填渲染”的可行性与局限。BabelCodex 将该路线保留为实验路径（Phase 14），生产默认走 BabelDOC 单遍管线（不变量 11）。
- **不复制**：其渲染栈与特定 PDF 库强绑定；逐句回填对公式/富文本占位符的保护不足，无法满足不变量 5（占位符精确保全）。

## PDFMathTranslate-next

- **定位**：v1 的社区演进版，改进服务化与多翻译器插件机制。
- **借鉴**：
  - 翻译器插件化接口（`src/codex_babeldoc/translators/base.py` 与 `factory.py`）；
  - 按文档术语表存储与文档级上下文（P2 计划的参照）；
  - GUI 与翻译服务分离的进程模型（对应 sidecar 架构）。
- **不复制**：其多租户服务化方向与“个人、本地优先”的产品定位不符。

## BabelDOC

- **定位**：本项目的直接上游依赖（0.6.x），负责 PDF 解析、占位符化与排版回填。
- **借鉴/直接使用**：
  - `BaseTranslator` 同步翻译合同（`src/codex_babeldoc/translators/base.py` 与 BabelDOC 侧契约保持一致）；
  - high-level `async_translate` 单遍管线（在 `src/codex_babeldoc/backends/babeldoc_worker.py` 中隔离调用）；
  - 占位符标记体系（`translation/placeholders.py` 校验其恒等性）。
- **不复制/不扩散依赖**：所有 BabelDOC 导入收敛在 `src/codex_babeldoc/backends/` 内（不变量 1），经兼容适配层（`babeldoc_internal.py`、`babeldoc_v064.py`）隔离版本差异；其余模块不得直接导入 BabelDOC。
