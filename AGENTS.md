# AGENTS.md

## Project goal

Build **BabelCodex**, a reliable, high-fidelity PDF translation pipeline primarily intended for personal, local use. BabelDOC owns PDF parsing/typesetting and Codex supplies translation through official Codex authentication, preferably a ChatGPT-plan session rather than an API key. The planned product surfaces are a CLI, Windows/Linux GUI executables, and a Codex-callable local MCP Server.

## Architectural invariants

1. Keep BabelDOC-specific imports isolated under `src/codex_babeldoc/backends/` or a narrowly scoped compatibility bridge.
2. Do not emulate undocumented ChatGPT HTTP endpoints, extract cookies, or convert ChatGPT auth into a fake OpenAI-compatible API.
3. Prefer the official `openai-codex` SDK for ChatGPT-authenticated Codex access.
4. Never silently fall back from Codex/ChatGPT-plan authentication to separately billed OpenAI API use.
5. Preserve BabelDOC placeholders exactly. Any future batching/structured-output layer must validate placeholder identity before returning translated text.
6. Persist enough state to safely skip completed documents and resume/retry failures.
7. Keep translation adapters independent of PDF orchestration.
8. Unit tests must not consume paid/plan model usage unless explicitly marked integration.
9. Default PDF execution is a single-pass BabelDOC high-level pipeline isolated in a worker process.
10. Translation batching, validation, retry, caching, and glossary logic belong in a translator-independent gateway.
11. The two-phase extract/translate/render flow is experimental and must not be the default production path.
12. CLI, GUI and MCP must share one Application Service and must not duplicate orchestration logic.
13. The MCP Server must expose only scoped translation/job operations, never arbitrary shell execution or unrestricted file deletion.
14. The inner Codex translation thread must not register or recursively invoke the BabelCodex MCP Server.
15. Public repository contents must not include user PDFs, generated outputs, state, logs, caches, credentials or private glossary data.
16. The planned GUI uses Tauri 2 + React/TypeScript and must call the Python Application Service through a fixed, permission-scoped sidecar.
17. The Tauri GUI must not directly import BabelDOC, initialize the Codex SDK, execute system Python, or expose arbitrary shell commands.
18. GUI, CLI and MCP must share the same job state, event protocol, error codes and Application Service.
19. GUI long-running work must remain responsive; translation runs in the Python service/worker, not on the UI thread.
20. GUI and MCP paths must be tested with explicit allowlists, sidecar failure cases, cancellation, reconnection and clean-environment packaging.

## Current upstream compatibility target

- Python: 3.11–3.12
- BabelDOC: 0.6.x (observed 0.6.4)
- Current PDF async entrypoint: `babeldoc.format.pdf.high_level.async_translate`
- Current translator base: `babeldoc.translator.translator.BaseTranslator`
- Codex SDK package: `openai-codex`

BabelDOC warns that direct Python APIs are internal. Treat every direct import as a compatibility boundary.

## Development priorities

### P0 — correctness

- Add placeholder validator (rich-text/formula tokens).
- Detect accidental Markdown fences/explanations from Codex.
- Add exact-output retry prompt on validation failure.
- Add integration fixture PDF containing formulas, links, citations, and two-column text.
- Add BabelDOC compatibility mapper and structured worker protocol.
- Add worker-based single-pass end-to-end mock pipeline.

### P1 — throughput

- Implement translation batching without breaking BabelDOC's synchronous translator contract.
- Consider a worker thread + request queue + short batching window.
- Return results to callers by stable request IDs.
- Do not concurrently call one Codex thread unless the SDK explicitly documents that as safe.
- Measure batch turn reduction, latency, cache hits, validation retries, and peak memory.

### P2 — consistency

- Per-document glossary store.
- Initial document-context extraction pass.
- Feed terminology guidance to the persistent Codex thread.
- Periodically compact/resume thread if context becomes too large.

### P3 — resilience

- Detect Codex authentication expiry separately from translation errors.
- Store error category in job state.
- Resume BabelDOC parts if upstream exposes stable part-level artifacts.
- Add output PDF sanity checks.
- Add GUI sidecar spike and Tauri capability validation.
- Add Codex MCP Server contract and path-safety tests.

## Product and repository

- Product name: `BabelCodex`
- Public repository: `15699122/BabelCodex`
- Product positioning: personal, local-first PDF translation; not a multi-tenant SaaS or commercial translation API

## Planning documents

- Overall architecture: `docs/architecture.md`
- Detailed development plan: `docs/development-plan.md`
- Architecture decisions and reference-project comparison: `docs/decisions.md`

Phase 0A public GitHub bootstrap is complete. The current implementation order is Phase 0B environment baseline → Phase 1 domain/error model → Phase 2 placeholder/output validation → Phase 3 BabelDOC compatibility layer → Phase 4 worker process → Phase 5 mock/live vertical slice → Phase 6 batching/cache → Phase 8 GUI sidecar spike → Phase 9 GUI Alpha/packaging → Phase 10 Codex MCP Server → Phase 11 glossary/context → Phase 12 recovery → Phase 13 PDF QA. Phase 14 Two-phase remains experimental.

## GUI framework baseline

- Target stack: Tauri 2, React, TypeScript, Vite, Tailwind CSS, shadcn/ui/Radix UI, Lucide Icons.
- Target platforms: Windows and Linux portable bundles; Linux AppImage is a later option.
- Runtime boundary: fixed `babelcodex-service` Python sidecar over a versioned JSONL protocol.
- UI architecture: New Translation, Jobs, Job Details, Glossary, Diagnostics and Settings pages.
- GUI E2E: Vitest/React Testing Library for frontend behavior and WebdriverIO for packaged/desktop flows.

## Commands

```bash
uv sync --extra runtime --extra dev
uv run pytest
uv run cbpdf --config config/example.toml doctor
uv run cbpdf --config config/example.toml run
```

## Coding rules

- Python type hints for public functions.
- Keep optional heavy imports lazy.
- Use `logging`, not `print`, inside library modules.
- Never log auth tokens or full sensitive document text by default.
- Prefer small compatibility adapters over widespread version checks.
- Every bug fix gets a regression test when practical.
