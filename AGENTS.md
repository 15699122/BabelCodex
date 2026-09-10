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
- Verified runtime compatibility: `docs/compatibility.md`

Phase 0A public GitHub bootstrap is complete. Phase 0B dependency, CI and BabelDOC warmup work is complete, but live Codex authentication is still required. The current implementation order is Phase 1 domain/error model → Phase 2 placeholder/output validation → Phase 3 BabelDOC compatibility layer → Phase 4 worker process → Phase 5 mock/live vertical slice → Phase 6 batching/cache → Phase 8 GUI sidecar spike → Phase 9 GUI Alpha/packaging → Phase 10 Codex MCP Server → Phase 11 glossary/context → Phase 12 recovery → Phase 13 PDF QA. Phase 14 Two-phase remains experimental.

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
# controlled packaged sidecar build (scripts/babelcodex-service.spec)
uv run --extra runtime --with pyinstaller pyinstaller \
    --clean --noconfirm scripts/babelcodex-service.spec
```

## Coding rules

- Python type hints for public functions.
- Keep optional heavy imports lazy.
- Use `logging`, not `print`, inside library modules.
- Never log auth tokens or full sensitive document text by default.
- Prefer small compatibility adapters over widespread version checks.
- Every bug fix gets a regression test when practical.

## Cross-platform development and Windows validation workflow

For Linux ↔ Windows development and validation workflow, follow:

`docs/development/cross-platform-validation.md`

This workflow is mandatory for Windows-specific implementation and validation tasks.

## Windows validation policy

The current WSL project directory is the source of truth for source code, project state, project documentation, and final validation records. A Windows `E:`-drive checkout is only a disposable validation workspace. Windows changes must not be synchronized back to WSL, except for validation results written to the designated WSL validation documentation.

### Deferred Windows validation rule

Linux is the primary development environment. Use **batch development, concentrated validation**:

```text
Linux Feature A → Linux Feature B → Linux Feature C
→ Linux verification → Windows Validation Preparation → Windows validation phase
```

Do not interrupt normal Linux development merely because a completed feature will eventually require Windows verification. After each Linux-implementable change, run its applicable Linux checks, add the Windows-only follow-up to the cumulative Windows Validation Queue in `docs/validation/windows.md`, and continue with the next non-blocked Linux task.

Use `WINDOWS_VERIFICATION_PENDING` by default. Use `WINDOWS_VERIFICATION_BLOCKING` only when a Windows-specific result is a hard prerequisite for reliable further development: for example, a critical Windows API/filesystem/process/installer assumption, a Windows-only reproducible failure that blocks progress, or an explicit user request for immediate Windows validation. See `docs/development/cross-platform-validation.md` for the required queue fields, preparation phase, and final handoff format.

Use `docs/validation/windows.md` for the detailed Windows validation procedure and result format. The procedure is mandatory whenever Windows platform validation is requested:

1. Investigate the current WSL repository before synchronization. Record the branch, commit, working-tree state, repository structure, languages/frameworks, Windows documentation, scripts/configuration, available test/lint/typecheck/build/package commands, compatibility requirements, agent instructions, and external dependencies or credentials.
2. Before synchronization, inspect both the WSL source and Windows target. Check for uncommitted, manually created, machine-specific, credential, cache, or other files that must be preserved. Do not blindly delete unknown files or overwrite Windows-local configuration.
3. Synchronize only from WSL to the Windows `E:` validation directory. Prefer existing checkout, worktree, deployment, or synchronization scripts. Do not copy `.git`, `node_modules`, Python virtual environments, Rust `target`, build/dist caches, IDE caches, temporary files, secrets, or machine-specific configuration unless project documentation explicitly requires them.
4. Verify that the Windows workspace contains the intended source state, including key files and any working-tree modifications. Record the WSL branch, commit, whether uncommitted changes were included, the Windows workspace path, and the synchronization date. Never describe a working-tree validation as a clean commit validation.
5. Derive the Windows validation scope from this repository's instructions, documentation, CI/build configuration, package scripts, and current implementation. Before execution, classify checks as `Required`, `Applicable`, or `Not applicable`; do not invent requirements that the project does not define.
6. In the Windows workspace, use the project's existing package managers, commands, and scripts. Do not change business code, architecture, dependencies, or configuration merely to make validation pass. Continue with independent checks after non-fatal failures, and mark dependent checks as `BLOCKED`.
7. Record every applicable check with its name, exact command, working directory, relevant versions, result, and concise output/error summary. Allowed result states are `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, and `NOT APPLICABLE`.
8. For every failure, preserve the key error or relevant stack trace, identify the likely category (`Windows-specific`, project code, environment configuration, missing dependency, external service, test defect, or unknown), state whether it blocks other checks, and document recommended follow-up work. Never mark a skipped or failed check as successful.
9. After Windows validation, write results back to the WSL repository's existing validation documentation, preferably `docs/validation/windows.md`, while preserving its structure and avoiding large raw logs. Include environment, source-state, synchronization, results, errors, and all not-run/blocked reasons.
10. Before finishing, confirm that the Windows workspace corresponds to the intended WSL state, every applicable check has a status, all `FAIL`/`BLOCKED`/`NOT RUN` entries have reasons, no validation-scope code changes were made, and the final WSL diff contains only expected documentation changes.

Windows validation is platform verification, not an excuse for opportunistic development. If a code change appears necessary, record the issue and proposed fix location in the validation document instead of implementing it as part of the validation run.
