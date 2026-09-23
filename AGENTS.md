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

- Documentation index: `docs/README.md` (read this first to place information in the right document)
- Overall architecture: `docs/architecture.md`
- Detailed development plan: `docs/development-plan.md`
- Architecture decisions and reference-project comparison: `docs/decisions.md`
- Verified runtime compatibility: `docs/compatibility.md`
- Per-file responsibility and maintenance map: `docs/development/codebase-map.md`

Phase 0A/0B, the domain/error model, placeholder validation, BabelDOC compatibility layer, worker process, mock vertical slice, Translation Gateway/cache, GUI sidecar foundation, MCP contract, glossary/context, recovery and baseline PDF QA are implemented and Linux-verified to the extent recorded in the development and validation documents. The current implementation order is: (1) Linux-only GUI/application-service contract completion and regression coverage; (2) authorized live Codex and long-document validation; (3) batching/cache and QA benchmark evidence; (4) concentrated Windows lifecycle/path/package validation; (5) release security and target-platform acceptance. Phase 14 Two-phase remains experimental.

## GUI framework baseline

- Target stack: Tauri 2, React, TypeScript, Vite, Tailwind CSS, shadcn/ui/Radix UI, Lucide Icons.
- Target platforms: Windows and Linux portable bundles; Linux AppImage is a later option.
- Runtime boundary: fixed `babelcodex-service` Python sidecar over a versioned JSONL protocol.
- UI architecture: New Translation, Jobs, Job Details, Glossary, Diagnostics and Settings pages.
- GUI E2E: Vitest/React Testing Library for frontend behavior and WebdriverIO for packaged/desktop flows.
- Tauri MCP development bridge: `tauri-plugin-mcp-bridge` is a committed Rust
  dependency and is enabled only for Debug builds, bound to `127.0.0.1`; Release
  builds must not start the bridge. The MCP server package is an external Agent
  tool and must not be added to the project npm dependencies.
- Linux Cline development must not start Tauri MCP or pretend to validate a
  desktop GUI without a targetable desktop. Linux may run Rust/config/schema
  checks, frontend tests/builds and non-GUI integration tests; Windows/native
  desktop validation remains concentrated and is recorded as
  `WINDOWS_VERIFICATION_PENDING` until directly executed.

## Commands

```bash
uv sync --extra runtime --extra dev
uv run pytest
uv run cbpdf --config config/config.yaml doctor
uv run cbpdf --config config/config.yaml run
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
- Default to incremental validation: pick the smallest sufficient test scope for the change, escalate only when evidence requires it, and record which checks were not run. Strategy in `docs/development/testing.md`; Windows minimization and revalidation rules in `docs/development/cross-platform-validation.md`.

## Documentation ownership

Every document has a single responsibility. Do not duplicate the same state across documents; link instead. The authoritative placement table lives in `docs/README.md`.

1. README is user-facing only. It must not record developer machines, branches, commit SHAs, test pass counts, Windows validation rounds, or recommended internal development order.
2. Current progress and future roadmap go only in `docs/development-plan.md`.
3. Architecture documents describe the stable structure and runtime logic only — never transient validation status or per-round results.
4. Windows validation run records go only under `docs/validation/`; current active queue and latest summary in `docs/validation/windows.md`, full historical runs archived in `docs/validation/history/`.
5. `docs/compatibility.md` records current compatibility conclusions derived from validation, not the validation logs themselves.
6. ADRs in `docs/decisions.md` record decisions, not work logs. Reference-project research lives in `docs/research/reference-projects.md`.
7. When you add, delete, rename, or change the responsibility of a module, update `docs/development/codebase-map.md` (and `docs/architecture.md` if the change is structural).
8. Never copy a status text into multiple docs; link to the single source document.
9. Historical validation records may only be archived, never silently deleted or rewritten. A historical `FAIL` must never be rewritten as `PASS`.
10. Commands written in any document must match the registered CLI parser, package scripts, or build script. `scripts/check_docs_inventory.py` enforces this for README CLI commands and codebase-map entries.
11. The documentation CI check must pass before a merge: `uv run pytest tests/test_docs_inventory.py`.

## Module design

Keep responsibility separable, but never split files mechanically by line count. A module may be refactored into a package or submodules only when the split improves cohesion and keeps public entry points stable.

1. One module has one primary responsibility: protocol definition, transport, task execution, persistence, and UI presentation are distinct concerns.
2. Public façades stay stable (`BabelCodexService`, `JsonlSidecar`, `McpServer`, `state.StateStore`, `worker_client.run_worker`). Internal implementations may delegate to submodules.
3. External callers must not reach through the public façade into internals. In particular, MCP/sidecar code must not directly touch `service.orchestrator.state`; route all mutation through `BabelCodexService` methods.
4. Do not duplicate orchestration logic between CLI, GUI, and MCP.
5. New modules need a module docstring, type hints on public functions, and matching tests.
6. Refactors must preserve behavior, wire protocol, and public import paths. Run the full Linux suite plus GUI tests after each refactor batch.
7. Split tests by the responsibility they cover instead of accumulating one aggregate test file.
8. Every module entry, its runtime location (which process), its main dependencies, and its tests must be documented in `docs/development/codebase-map.md`.
## Platform ownership and handoff

### Development model

This repository uses a dual-owner model:

- Linux is the **Cross-platform Owner**.
- Windows is the **Windows Platform Owner**.

Linux owns shared and cross-platform implementation: shared architecture, shared APIs and contracts, cross-platform business logic, shared persistence/data models, protocol definitions, platform abstractions, and cross-platform tests.

Windows owns Windows-specific implementation, integration, runtime behavior, GUI, packaging, and platform validation: Windows-native integration, filesystem/process behavior, Windows-specific GUI behavior, services/registry integration, Windows configuration, compatibility fixes, installer/packaging, and Windows-specific tests.

Detailed ownership and routing rules: `docs/development/platform-ownership.md`.

### Canonical project state

**正式开发状态通过 Git 交接；直接文件同步只用于临时诊断，不产生正式项目状态。**

The canonical project state is the Git repository state plus committed project documentation, current Plan/task state, and recorded platform validation results. A machine-local working directory is not, by itself, the canonical project state. Both owners must integrate their changes into the canonical repository before those changes are considered project state.

Formal platform handoff must always identify:

- branch;
- source commit;
- handoff commit when applicable;
- uncommitted-state status;
- current owner.

Do not treat copied files as a formal handoff.

### Formal platform handoff

The normal production workflow is Git-based:

```text
Linux working tree → Git commit → Git remote → Windows working tree
Windows working tree → Git commit → Git remote → Linux working tree
```

The configured Git remote (GitHub) is the exchange point between platform owners. Formal handoff must use Git history and record the handoff revision. Full workflow: `docs/development/git-platform-handoff.md`.

### Direct sync — diagnostics only

Direct filesystem synchronization from Linux to Windows is allowed only as a temporary diagnostic or experimental path. It must not be used as the normal ownership handoff mechanism.

- Direct sync must target a disposable or explicitly designated scratch workspace.
- It must never overwrite the Windows Platform Owner's canonical working tree.
- Direct-sync results are experimental until reproduced or integrated through the formal Git workflow.
- Never treat a direct-sync workspace as the source of truth.
- Use direct sync only for a fast Windows experiment, an undesirable-to-commit intermediate state, behavior needed to unblock design, or an experiment that can be safely discarded.

Hard rule:

- `E:\Projects\<project>` (the formal Windows Owner repository) is updated **only through Git**.
- `E:\Scratch\<project>` (the scratch workspace) is the **only** target allowed for direct Linux sync.

### Workspace model

- Linux uses a Linux-native filesystem working tree, owns cross-platform development, and should not perform normal development from `/mnt/<drive>`.
- Windows uses an NTFS working tree such as `E:\Projects\<project>`, owns Windows platform development, and should not use the WSL repository itself as its normal working tree.

The two owner workspaces are independent Git working trees; they exchange formal state through Git revisions, not file mirroring.

### Ownership boundaries

Routing: shared behavior → Linux; Windows-specific cause or implementation → Windows. If a Windows fix requires changing a shared contract, architecture, protocol, schema, or cross-platform behavior, Windows marks `CROSS_PLATFORM_CHANGE_REQUIRED` and hands the shared change to Linux. A small, contract-preserving shared implementation change may be implemented by Windows and must be marked `CROSS_PLATFORM_REVIEW_REQUIRED`. Unclear ownership is `NEEDS_VERIFICATION`.

Windows is not merely a validation environment: it may modify Windows production code, configuration, packaging, tests, and scripts within its ownership boundary. It must not change shared semantics solely to make a Windows check pass.

### Batch development

Prefer batch ownership:

```text
Cross-platform batch → handoff → Windows batch → handoff if required
```

Default flow is batched Linux cross-platform work → targeted Linux verification → Windows handoff → Windows implementation/verification → Linux follow-up only for shared changes. Avoid unnecessary platform ping-pong; a normal Windows validation requirement does not interrupt Linux development. Accumulate non-blocking Windows work/verification into the next Windows batch. Use `WINDOWS_BLOCKING` only when Windows behavior must be a known hard prerequisite before cross-platform development can safely continue.

### Validation

Use risk-based incremental validation (`Targeted → Module → Subsystem → Full`); do not run the full test suite after every change. Detailed rules: `docs/validation/validation-policy.md`; Windows minimization and revalidation: `docs/development/cross-platform-validation.md`. Validation results must identify the revision they tested.

Computer Use / GUI automation failure is an automation failure, not a product failure: perform limited retry, mark affected tests `BLOCKED` with blocker `COMPUTER_USE_UNAVAILABLE`, continue independent validation, and create or update the Manual Windows Validation Queue. Never mark an unexecuted GUI test as PASS.

### Handoff state

Current platform handoff state (batch, branch, revisions, owner) is maintained in `docs/status/platform-handoff.md`; that file describes the current batch, not the complete historical log. Validation history stays in the `docs/validation/` history documents.

Routing index:

- `docs/development/platform-ownership.md` — ownership and routing
- `docs/development/git-platform-handoff.md` — Git-based handoff workflow, workspace model, direct-sync boundary
- `docs/validation/validation-policy.md` — risk-based validation and Computer Use fallback
- `docs/status/platform-handoff.md` — active batch state
- `docs/review/code-audit-guidelines.md` — audit rules
- `docs/development/cross-platform-validation.md` — Windows validation execution details

Use repository Skills under `.agents/skills/` for repeatable audits, handoffs, and Windows validation. A nearer `AGENTS.md` may refine these rules for a platform-specific directory.

### General rules

All agents must:

- inspect the current repository before relying on previous assumptions;
- prefer the smallest correct change;
- avoid unrelated refactoring;
- respect platform ownership;
- use Git for formal handoff;
- distinguish implementation from verification;
- distinguish experimental direct-sync results from formal project state;
- use minimal necessary validation;
- review final `git diff` before finishing;
- never claim platform validation that was not actually performed.
