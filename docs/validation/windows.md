# Windows Platform Validation

This document defines the reproducible procedure for validating the latest BabelCodex development state from the WSL project directory on Windows. It is both a validation runbook and the location for Windows validation results.

## Purpose and source of truth

The WSL project directory is the authoritative source for:

- source code and working-tree state;
- project documentation, configuration, and scripts;
- the final Windows validation record.

The Windows `E:`-drive project directory is only a Windows validation workspace. Synchronization is strictly one-way:

```text
WSL project directory  ───────────────▶  Windows E: validation workspace
       source of truth                         disposable validation copy
```

Do not synchronize Windows code or configuration back to WSL. The only intended write-back is the validation result recorded in this WSL document.

## Deferred Windows Validation Queue and Handoff

Linux development accumulates Windows-only work here and normally validates it in a single concentrated Windows phase. Do not create a separate Windows run merely because one feature will eventually need native validation, unless the item is `WINDOWS_VERIFICATION_BLOCKING` or the user explicitly requests immediate Windows validation.

### Queue states

- `WINDOWS_VERIFICATION_PENDING`: default; the item is accumulated and does not block further Linux development.
- `WINDOWS_VERIFICATION_BLOCKING`: use only when a Windows-specific result is a hard prerequisite for reliable further Linux development.

## Computer Use Failure Handling

Computer Use, screen interaction and GUI automation are optional capabilities of
the Windows validation environment. Their unavailability must reduce GUI
automation coverage, not terminate the Windows validation phase or reduce the
amount of independent validation performed.

### Classification rule

If a test cannot continue because of any of the following:

- Computer Use is unavailable;
- GUI automation is unavailable;
- screen interaction is unavailable;
- the application window cannot be controlled;
- the automation session was lost;
- a temporary UI-control failure persists;

record the test as:

```text
Status: BLOCKED
Blocker: COMPUTER_USE_UNAVAILABLE
```

`BLOCKED` means that the test has no conclusion. It is not evidence that the
product failed, and it is not evidence that the product passed. Do not record
such a test as `FAIL`, `PASS` or `NOT_APPLICABLE`.

The validation record must also state:

- the original validation target;
- the exact Computer Use or GUI automation error;
- whether one reasonable retry was attempted;
- whether the retry produced the same blocker;
- whether a non-GUI alternative exists;
- whether that alternative verifies the same behavior or only a narrower
  contract;
- the manual test queue entry that remains open.

### Retry and continuation policy

For a suspected transient Computer Use failure, allow at most one reasonable
retry unless this project documents a stricter policy. Do not spend the
validation phase repeatedly trying to restore the same UI-control capability.
After the retry fails:

1. mark the affected test `BLOCKED`;
2. record `Blocker: COMPUTER_USE_UNAVAILABLE` and the evidence;
3. skip that test for the current run;
4. continue every independent build, CLI, unit, integration, filesystem,
   configuration, log, service and process check;
5. mark a dependent test `BLOCKED` only when it genuinely requires the blocked
   result or the unavailable capability;
6. collect all blocked and manual-only items into the manual queue at the end
   of the Windows phase.

For example, a blocked GUI startup observation must not stop Cargo checks,
CLI integration, filesystem checks, installer construction, sidecar protocol
smoke or log inspection. A later test that requires clicking through that same
GUI must be `BLOCKED` with the dependency stated explicitly.

### Prefer equivalent non-GUI evidence

When an existing CLI, project script, test API, log, filesystem inspection,
process check, configuration check, generated-artifact inspection or endpoint
can verify the **same behavior**, use that evidence and record `PASS` only for
the behavior it actually proves. Do not change the test's meaning merely to
avoid Computer Use. If the alternative proves only a narrower contract, keep
the original GUI test `BLOCKED` and record the narrower automated result
separately.

### Required end-of-phase result groups

Every Windows validation summary must separate at least:

1. **Automated PASS** — executed automatically and met the expected result;
2. **Automated FAIL** — executed and exposed a product or validation defect;
3. **BLOCKED** — no conclusion because of Computer Use or another documented
   environment blocker;
4. **Manual validation required** — a GUI-only, manual or otherwise unavailable
   capability remains to be executed.

Computer Use failure is not a product failure:

```text
Computer Use unavailable  -> BLOCKED
Function executed incorrectly -> FAIL
Function executed correctly -> PASS
```

The Windows phase must continue all independent validation after a `BLOCKED`
result and must summarize the incomplete work only after those checks finish.

### Active queue template

Add new items while Linux development continues. Do not mark an item `PASS` until Windows directly executes it.

| ID | Validation item | Related feature/change | Files/modules | Why Windows is required | Exact behavior to verify | Prerequisites | Expected result | Priority | Development impact | Blocks further Linux development |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WVQ-...` |  |  |  |  |  |  |  | `P0` / `P1` / `P2` | `WINDOWS_VERIFICATION_PENDING` / `WINDOWS_VERIFICATION_BLOCKING` | Yes / No |

### Current accumulated queue

| ID | Validation item | Related feature/change | Files/modules | Why Windows is required | Exact behavior to verify | Prerequisites | Expected result | Priority | Development impact | Blocks further Linux development |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WVQ-001` | Packaged Chinese UI and keyboard acceptance | Simplified-Chinese GUI layout, labels, job states and disabled i18n placeholder | `gui/src/App.tsx`, `gui/src/styles.css`, `gui/src/App.test.tsx` | DOM tests and process smoke cannot establish native WebView rendering or desktop keyboard behavior | Installed/portable UI displays Chinese labels without clipping, focus order is logical, and the disabled `界面语言` selector is understandable | Fresh current-source package; Windows desktop | Core screens, task flows and settings are readable and keyboard-operable | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux implementation and automated checks can continue |
| `WVQ-002` | DPI, NVDA and window interaction matrix | Responsive Chinese layout and accessibility behavior | `gui/src/App.tsx`, `gui/src/styles.css`, Tauri host/window configuration | Native DPI scaling, screen reader behavior and window interaction require Windows desktop evidence | Validate 125%/150%/200% DPI, NVDA reading/focus order, resize and window-close behavior | Packaged GUI; NVDA; Windows display scaling access | No clipped critical controls, usable focus order and readable status/error feedback | `P1` | `WINDOWS_VERIFICATION_PENDING` | No; not a hard prerequisite for further Linux development |
| `WVQ-003` | Picker, allowlist, artifact-integrity and path/permission matrix | GUI file intake, job orchestration and Phase 12 artifact manifest/recovery | `gui/src/filePicker.ts`, `gui/src/App.tsx`, Tauri dialog permissions, sidecar path checks, `src/codex_babeldoc/core/artifact_manifest.py`, `src/codex_babeldoc/core/state.py` | Windows path syntax, Unicode/path-space behavior and native picker behavior need platform execution | Test allowed/denied paths, drive letters, non-ASCII names, spaces, cancellation, reconnection and output behavior; after a completed mock job, delete or alter one packaged output and confirm validate reports failure and the next run does not unsafe-skip it; confirm an active PID is not falsely recovered by a second service instance | Packaged GUI; disposable test directories and fixture PDF | GUI and sidecar enforce allowlists; manifest rejects missing/tampered artifacts; active cross-process jobs are preserved and recovery feedback is safe/actionable | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; current contracts and Linux tests remain sufficient for Linux work |
| `WVQ-004` | Clean-user installation, first launch, sidecar restart and job-recovery smoke | NSIS/MSI/portable packaging, sidecar startup and Phase 12 CLI/service recovery | `gui/src-tauri`, `scripts/babelcodex-service.spec`, package artifacts, `src/codex_babeldoc/application/service.py`, `src/codex_babeldoc/core/orchestrator.py`, `src/codex_babeldoc/core/state.py`, `src/codex_babeldoc/cli.py` | Developer workspace smoke cannot establish an isolated-user installation experience or Windows process lifecycle behavior | Install or extract under a clean Windows user, launch, start/cancel a mock job and exit cleanly; invoke packaged job inspection/validation or the scoped UI flow; terminate a disposable runner before completion, restart the sidecar/service and verify the persisted job becomes `WORKER_CRASHED` with no automatic rerun, then verify explicit retry begins a new attempt | Fresh unsigned package; disposable clean-user environment and mock fixture; controlled process termination procedure | No dependence on repository, development dependencies or pre-existing user state; dead/unknown runners are terminalized safely, live jobs are not falsely reclaimed, and recovery remains explicit | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; packaging implementation is already source/package-smoke verified |
| `WVQ-005` | Release-security audit | Signing and release deliverables | release workflow, package artifacts, SBOM/checksum process | SmartScreen, signatures and release artifact composition are Windows/release-process specific | Check Defender/SmartScreen, signatures, SBOM, checksums and final installer contents | Release candidate, signing material and SBOM workflow | Artifacts satisfy the documented release-security criteria | `P1` | `WINDOWS_VERIFICATION_PENDING` | No; release workflow has not started |
| `WVQ-006` | Live Codex/PDF integration | Usage-bearing end-to-end translation acceptance | Codex authentication, BabelDOC worker, fixture PDF | Requires authorized real account usage and desktop/PDF environment | Translate the authorized fixture and inspect output/QA behavior | Explicit authorization, active Codex session and safe fixture | End-to-end translation completes without placeholder or output-QA regressions | `P2` | `WINDOWS_VERIFICATION_PENDING` | No; ordinary tests must not consume paid or plan usage |
| `WVQ-007` | Work-dir retention, cleanup and category retry policy on Windows | Phase 12 cleanup/retention and error-category retry policy | `src/codex_babeldoc/core/workdir.py`, `src/codex_babeldoc/core/errors.py`, `src/codex_babeldoc/core/config.py`, `src/codex_babeldoc/cli.py`, `src/codex_babeldoc/application/mcp.py` | Directory removal semantics (locked files, long paths, junctions) and per-process PID semantics differ on Windows and cannot be validated from Linux | Run a terminal mock job, keep its `job-<stem>` work dir within `work_retention_days` and verify `babelcodex cleanup --dry-run` reports it without deleting; age it (temporarily lower the setting) and verify `cleanup` removes it while an active `RUNNING`/`RETRY_PENDING` job dir survives; confirm an open file handle during removal is tolerated by the bounded retry; verify an injected AUTH failure does not auto-loop (`attempts == 1`) and that `retry_policy` caps total attempts | Disposable fixture PDF and config; a live mock job; controlled file-lock procedure | Terminal dirs removed only after retention and never while active; locked-file removal retries then reports; auth/input failures never auto-retry on Windows | `P1` | `WINDOWS_VERIFICATION_PENDING` | No; Linux unit/integration checks pass |
| `WVQ-008` | PDF QA rendering/glyph behavior on Windows | Phase 13 QA battery (`babelcodex qa`) and render-blank/glyph heuristics | `src/codex_babeldoc/qa/`, `src/codex_babeldoc/application/service.py`, `src/codex_babeldoc/cli.py`, `tests/test_e2e_mock.py` | Glyph rasterization, font subsetting and media-box behavior can differ across platforms and cannot be proven from Linux | Run the fixture mock job on Windows and `babelcodex qa <job-id>`; confirm the report is PASS and the same for mono/dual artifacts, that a deliberately removed output marks `qa_status=failed`, and that `RENDER_BLANK_PAGE`/`TEXT_OVERFLOW` heuristics behave deterministically on the fixture | Fixture PDF, mock config, packaged or dev-sidecar CLI on Windows | QA emits identical stable findings/status for the fixture; missing outputs never pass; no spurious blank/overflow on known-good output | `P2` | `WINDOWS_VERIFICATION_PENDING` | No; Linux QA unit/integration baseline passes |
| `WVQ-009` | Stale-sidecar handshake and bundle freshness audit on packaged GUI | Stale-sidecar defense (ADR-029): sidecar `get_server_info` runtime handshake and `check_gui_bundle --source-tree` freshness audit | `src/codex_babeldoc/application/sidecar.py`, `scripts/check_gui_bundle.py`, `gui/src/sidecar.ts`, `gui/src/protocol.ts`, `scripts/babelcodex-service.spec` | Windows packaging is the only path that can embed a stale sidecar binary (the 2026-09-11 validation caught exactly this drift); filesystem mtime semantics and packaged GUI startup must be observed on Windows | Build a fresh package and confirm the GUI handshake succeeds on launch; then rebuild a package with a deliberately stale sidecar (or revert one sidecar-affecting source after packaging) and confirm the audit script flags it and the GUI surfaces a clear handshake/connection error instead of a protocol failure mid-job; confirm `check_gui_bundle --source-tree` passes on a correct package | Packaged GUI (fresh + stale-sidecar variant); Windows desktop | Fresh package passes audit and handshake; stale sidecar is rejected with an actionable startup error, never a mid-translation protocol mismatch | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux guards and tests pass |
| `WVQ-010` | Windows ACLs for local private data | POSIX private-data hardening and worker-request restrictions | `src/codex_babeldoc/core/private_data.py`, `core/config.py`, `core/state.py`, `translation/cache.py`, `translation/thread_state.py`, `backends/worker_client.py` | Linux mode bits do not prove Windows ACL isolation | In a clean Windows user profile, inspect state/cache/glossary/context/thread/worker/log directories and files; confirm another standard user cannot read them; confirm worker request files are not left world-readable and are removed/retained only according to the documented lifecycle | Fresh package or dev-sidecar run under two disposable standard users; no real PDFs or credentials | User data is private to the owning Windows user and worker request files do not expose document configuration to other users | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux permission checks and tests can continue |
| `WVQ-011` | Fixed Tauri config capability and path rejection | Tauri shell capability now accepts only `config/example.toml` | `gui/src-tauri/capabilities/default.json`, `gui/src/sidecar.ts` | Tauri capability regex and Windows packaging/runtime enforcement require native target validation | Inspect generated capability schema and launch packaged GUI; verify absolute paths, `..` traversal and alternate TOML paths are rejected while the bundled fixed config starts successfully | Current Windows target build and packaged GUI | Renderer cannot select an arbitrary config that changes input/output/state roots | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux configuration checks can continue |
| `WVQ-012` | Bounded sidecar event recovery and DTO privacy | Bounded event deque, `oldest_sequence` resync and reduced job views | `src/codex_babeldoc/application/sidecar.py`, `application/service.py`, `gui/src/jobStore.ts`, `gui/src/protocol.ts` | Native packaged process lifetime and reconnect behavior need Windows evidence | Generate more than the event retention window, disconnect/reconnect the GUI, verify it detects a stale cursor, refreshes jobs, and does not expose absolute paths/PIDs/thread IDs in GUI/sidecar responses | Packaged sidecar; mock job; controlled sidecar restart | Memory/event history remains bounded, reconnect converges to persisted state, and external DTOs stay minimized | `P1` | `WINDOWS_VERIFICATION_PENDING` | No; Linux contract tests can continue |
| `WVQ-013` | Codex deny-all boundary and isolated working directory | Explicit `ApprovalMode.deny_all`, read-only sandbox, isolated cwd and minimal worker environment | `src/codex_babeldoc/translators/codex_sdk.py`, `backends/worker_client.py` | Windows packaged Codex runtime and environment/working-directory behavior require native execution | With a synthetic prompt-injection PDF and authorized mock/live policy, confirm no approval/tool/MCP/file access occurs, the Codex cwd is the per-document isolated directory, and unrelated environment variables are not inherited by the worker | Authorized Codex integration only; synthetic fixture; no production documents | Translation remains text-only and cannot use the repository/workspace as a tool surface | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; live usage requires explicit authorization |
| `WVQ-014` | Windows worker environment allowlist revalidation | `worker_environment()` allowlist now retains the Windows runtime/profile keys (`SystemRoot`, `USERPROFILE`, `TEMP`, `TMP`, `APPDATA`, `LOCALAPPDATA`, `PROGRAMDATA`) beside the POSIX keys; Linux unit regression `TestWorkerEnvironment` pins the allowlist and non-inheritance of unrelated variables | `src/codex_babeldoc/backends/worker_client.py`, `tests/test_worker.py` | The 2026-09-12 incremental run reproduced `WinError 10106` with the smaller allowlist; the fix is designed on Linux and needs the native subprocess path confirmed | Run the subprocess mock integration and a worker-based mock job with a Windows-size allowlist; verify the worker starts, translates, completes, supports cancellation/reconnection and does not inherit unrelated parent variables (`SECRET`-style keys) | Current Windows source; fresh PyInstaller sidecar or dev worker; mock translator | Subprocess mock integration passes and no `WinError 10106`-class runtime failure appears | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux unit and integration checks pass |
| `WVQ-015` | QA CLI stdout JSON contract revalidation | Production QA/pipeline imports now use the official `pymupdf` package name; regression `test_qa_cli_stdout_is_machine_readable_in_clean_subprocess` launches the CLI in a clean interpreter and asserts stdout is one JSON document | `src/codex_babeldoc/qa/*.py`, `src/codex_babeldoc/core/pipeline_meta.py`, `src/codex_babeldoc/translation/context.py`, `tests/test_cli.py` | The PyMuPDF `fitz` shim printed its deprecation notice to stdout (reproduced as `JSONDecodeError` on Windows); only a clean native run proves a machine consumer can parse the QA JSON | Run `cbpdf qa` positive/tamper cases and `cbpdf doctor`/`validate` in a clean Windows interpreter subprocess and assert every stdout payload parses as JSON with dependency notices absent | Current Windows source; frozen sidecar or dev CLI; mock job | QA/doctor/validate stdout remains machine-readable with no PyMuPDF deprecation noise | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux clean-subprocess regression passes |
| `WVQ-016` | Tauri MCP Bridge Debug-only localhost configuration | Add `tauri-plugin-mcp-bridge`, register only in Debug, bind the WebSocket Bridge to localhost, and keep the external MCP server out of the project package | `gui/src-tauri/Cargo.toml`, `gui/src-tauri/src/lib.rs`, `gui/src-tauri/capabilities/default.json`, `gui/src-tauri/tauri.conf.json` | Native Tauri Debug startup, WebSocket reachability and capability behavior require a target desktop; Linux Rust/config checks do not prove the desktop Bridge | On a current native Windows Debug run, start `npm run tauri dev`, verify the Bridge is reachable only on `127.0.0.1`, use the external `npx.cmd -y @hypothesi/tauri-mcp-server`, and verify a Release build does not start the Bridge | Windows desktop; Node/npm; current Debug build; external MCP server; no Release credentials | Debug Bridge is localhost-only and usable by the external MCP server; Release has no Bridge listener; no project npm dependency is added | `P1` | `WINDOWS_VERIFICATION_PENDING` | No; Linux Rust/config/schema checks can continue |
| `WVQ-017` | WebdriverIO native desktop E2E | `@wdio/tauri-service` embedded provider, real Tauri WebView, Python sidecar lifecycle, Windows-only specs (`tests/e2e/windows/*`) | Phase 15 WDIO E2E infrastructure | In the Windows workspace: `npm.cmd --prefix gui ci`, `npm.cmd --prefix gui run build`, `npm.cmd --prefix gui run e2e:native`. On failure: `npm.cmd --prefix gui run e2e:native:debug` then `npm.cmd --prefix gui run e2e:external` to separate driver-layer failures from product failures. Record results separately for embedded and external providers. | Windows desktop; WebView2; Node/npm; packaged or debug `babelcodex-gui.exe`; fixed Python sidecar binary | All common native specs pass; Windows-only specs (`.exe` path resolution, Windows path allowlist, packaged-binary behavior) pass; no GUI/sidecar/worker residue after run; failure artifacts (screenshots, frontend/backend logs) captured | `P0` | `WINDOWS_VERIFICATION_PENDING` | No; Linux infrastructure work and Rust/config checks can continue |


### Windows Validation Preparation and final handoff

At the end of the Linux Development Phase, consolidate this queue against the final diff, current Plan, changed modules, CI/build configuration, Windows code paths and historical validation evidence. Merge duplicate scenarios and organize the handoff as Build / Toolchain, Runtime, Filesystem, Integration, Packaging and Regression.

Each final item must provide ID, test name, purpose, related changes, prerequisites, exact steps/command, expected result, P0/P1/P2 priority and whether manual interaction is required. Preserve the completed-run history below; the active queue and handoff describe future concentrated Windows work only.

## Phase 1 — Repository investigation

Before synchronizing or running Windows commands, inspect the WSL repository and record:

- current Git branch, commit, and working-tree status;
- repository structure and relevant source files;
- languages, frameworks, package managers, and build systems;
- `AGENTS.md` and other agent/project instructions;
- Windows-related documentation, scripts, CI jobs, and configuration;
- test, formatter, linter, typecheck, build, packaging, startup, CLI, filesystem, subprocess, and sidecar commands;
- existing platform compatibility requirements and validation documents;
- required runtimes, SDKs, environment variables, credentials, external services, and hardware;
- whether the source contains uncommitted changes.

Prioritize evidence in this order:

1. `AGENTS.md` and project agent instructions;
2. project documentation;
3. CI, build, and test configuration;
4. package/build scripts;
5. current implementation.

Do not create Windows validation requirements that are not supported by the repository.

## Phase 2 — Pre-sync safety check

The WSL directory is the synchronization source and the Windows `E:` directory is the target. Before copying:

- confirm that the Windows target exists or determine the documented target creation procedure;
- inspect the target for uncommitted, manually created, machine-specific, credential, cache, or other files that may need to remain;
- do not blindly delete unknown files;
- do not overwrite Windows-local configuration, credentials, caches, logs, or generated data without an explicit project rule;
- inspect `.gitignore`, project documentation, build configuration, and existing synchronization scripts;
- exclude platform-independent copies of `.git`, `node_modules`, Python virtual environments, Rust `target`, build/dist caches, IDE caches, temporary files, secrets, and machine-specific settings unless the project explicitly requires them.

If the project has an existing checkout, worktree, synchronization, deployment, or packaging workflow, use it instead of creating a competing copy mechanism.

## Phase 3 — Synchronize and verify the workspace

Synchronize the required WSL content to the Windows `E:` validation workspace in one direction only. After synchronization, verify:

- key source files and project documents are current;
- the Windows workspace corresponds to the intended WSL branch/commit and working-tree state;
- uncommitted WSL changes are present when they are part of the requested validation;
- path separators, case sensitivity, symbolic links, permissions, and non-ASCII names did not cause missing files;
- Windows-local configuration was not overwritten;
- excluded caches, dependencies, generated files, credentials, and user data were not accidentally copied.

Record at minimum:

| Field | Value |
| --- | --- |
| WSL source path | absolute path |
| Windows workspace path | absolute `E:` path |
| WSL branch | branch name |
| WSL commit | commit hash, if available |
| Working-tree changes included | yes/no, with summary |
| Synchronization method | existing script/checkout/manual documented method |
| Synchronization date | `YYYY-MM-DD` |

If the WSL tree is dirty, state this explicitly. Do not represent the Windows run as validation of a clean commit.

## Phase 4 — Determine validation scope

Derive the validation checklist from the current repository. Classify each candidate before execution:

- **Required** — explicitly required by project documentation or CI;
- **Applicable** — supported by the current Windows environment and relevant to the current implementation;
- **Not applicable** — irrelevant to this project or not a Windows concern.

Typical candidates, only when supported by project evidence, include:

- dependency and runtime setup;
- code generation;
- formatting, lint, and type checking;
- unit, integration, and Windows-specific tests;
- GUI/browser tests;
- Rust host checks;
- sidecar build and JSONL protocol smoke;
- CLI and filesystem/path behavior;
- subprocess, cancellation, reconnection, and startup behavior;
- application build, NSIS/MSI/portable packaging, and package contents;
- application startup and clean-environment checks;
- network, authentication, or external-service integration.

Do not expand the scope merely because a tool is available. Do not use unit tests to consume paid Codex or ChatGPT-plan usage unless the test is explicitly marked integration and authorized.

## Phase 5 — Execute Windows validation

Run checks in the Windows workspace with the project's documented commands and tools. Do not replace failed commands with arbitrary alternatives, modify business code, upgrade dependencies, or change architecture to obtain a passing result.

For every check, record:

| Field | Required content |
| --- | --- |
| Validation item | concise name |
| Classification | Required / Applicable / Not applicable |
| Command | exact command as executed |
| Working directory | absolute path |
| Versions | relevant runtime/toolchain versions |
| Status | PASS / FAIL / BLOCKED / NOT RUN / NOT APPLICABLE |
| Result | concise summary |

Continue with independent validation after a non-fatal failure. If a check depends on a failed prerequisite, mark it `BLOCKED` and name the dependency.

## Phase 6 — Analyze errors

For each `FAIL` or relevant `BLOCKED` result, record:

- failed phase and command;
- key error text and the most relevant stack trace or log path;
- likely category:
  - Windows platform compatibility;
  - project code;
  - environment configuration;
  - missing dependency/toolchain;
  - external service or credential;
  - test defect;
  - unknown;
- whether the issue blocks other checks;
- recommended follow-up or proposed fix location.

Do not paste huge raw logs into this document. Keep detailed logs in the Windows workspace or an explicitly documented artifact location, and include only the relevant excerpt and path here.

## Modification policy

The primary purpose of this process is validation. Unless project documentation explicitly requires local Windows configuration generation:

- do not modify business code;
- do not modify the WSL project's functional implementation;
- do not fix tests or platform issues during the validation run;
- do not perform unrelated refactors;
- do not upgrade dependencies or alter architecture.

Normal Windows build artifacts, dependency caches, test artifacts, logs, temporary files, and machine-local settings may be created in the Windows workspace. If a code change appears necessary, record the problem and suggested fix instead of implementing it during validation.

## Validation record

Each completed run should contain the following sections.

### Validation environment

- Validation date: `YYYY-MM-DD`
- Windows version and OS build, if available:
- Architecture:
- Relevant Python/uv/Node/npm/Rust/Visual Studio/WebView2/tool versions:
- WSL source path:
- Windows workspace path:
- Linux/WSL source branch:
- Linux/WSL source commit:
- Working-tree changes included:
- Synchronization method:
- Credentials/external services required and availability:

### Validation checklist

| Item | Classification | Command | Working directory | Status | Result |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### Errors and analysis

| Item | Key error/log path | Likely category | Blocks other checks | Follow-up |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

### Not executed / blocked

Every omitted item must have a reason, such as:

- prerequisite failed;
- required external service unavailable;
- missing credential;
- unavailable hardware or Windows capability;
- not applicable on Windows;
- not defined by current project documentation;
- insufficient environment capability.

“Not tested” alone is not a sufficient reason.

For Computer Use-related omissions, use the following explicit form:

```text
Status: BLOCKED
Blocker: COMPUTER_USE_UNAVAILABLE
Retry: one reasonable retry attempted / not attempted because the failure was persistent
Alternative: CLI/script/log/process/filesystem evidence available or unavailable
Manual queue: WIN-MANUAL-<id>
```

### Final review

Before closing a run, confirm:

1. the Windows workspace corresponds to the intended WSL source state;
2. every applicable Windows validation item has an explicit status;
3. every `FAIL`, `BLOCKED`, and `NOT RUN` result has a reason;
4. no failure was recorded as a success;
5. Windows-specific behavior was not omitted without explanation;
6. no out-of-scope Linux code changes were made;
7. this WSL validation document contains the result and error analysis;
8. the final WSL Git diff contains only expected validation documentation changes.

## Reporting requirements

The final report must state:

1. Linux/WSL branch, commit, and working-tree state;
2. Windows synchronization result;
3. PASS items;
4. FAIL items;
5. BLOCKED / NOT RUN items and reasons;
6. Windows-specific issues discovered;
7. WSL documents updated;
8. follow-up development tasks, if any.

Never report only “validation completed” when failures, blockers, or unexecuted items remain.

## Manual Windows Validation Queue

At the end of each Windows validation phase, generate or update this queue for
every item that remains incomplete because Computer Use is unavailable, the
workflow is GUI-only, manual interaction is required, or the automation
capability was unavailable. The queue is not a substitute for execution and
must not be converted to `PASS` until a human or working automation session
performs the steps and records the result.

Each entry must contain all of these fields:

- **Test ID** — unique ID such as `WIN-MANUAL-001`;
- **Test name**;
- **Current status** — normally `BLOCKED`;
- **Blocker** — use `COMPUTER_USE_UNAVAILABLE` when applicable;
- **Purpose**;
- **Related change**;
- **Preconditions**;
- **Manual test steps**;
- **Expected result**;
- **Failure evidence to collect**;
- **Result** — `PASS`, `FAIL` or `BLOCKED`;
- **Notes**, **Error** and **Evidence** fields for completion.

### Current Manual Windows Validation Queue

The following entries correspond to the current validation record. Their
status is updated only from direct Windows desktop evidence. The static
stale-bundle audit, sidecar handshake, MSI payload parity, process smoke, CLI
tests and other non-GUI checks are separate automated evidence and must not be
repeated as a substitute for these manual observations.

#### WIN-MANUAL-001 — Packaged stale-sidecar GUI error presentation

- **Test ID:** `WIN-MANUAL-001`
- **Test name:** Stale sidecar is rejected with an actionable GUI connection error
- **Current status:** `BLOCKED`
- **Blocker:** `COMPUTER_USE_UNAVAILABLE`
- **Purpose:** Prove that a packaged GUI detects a stale/incompatible sidecar at
  startup and presents a clear connection or compatibility error before a job
  can start, rather than failing later with a protocol mismatch.
- **Related change:** `src/codex_babeldoc/application/sidecar.py`,
  `gui/src/sidecar.ts`, `gui/src/protocol.ts`,
  `scripts/check_gui_bundle.py`, `scripts/babelcodex-service.spec` and
  `WVQ-009`.
- **Preconditions:**
  1. A current Windows package has been built from the intended WSL source
     revision.
  2. The current package's fresh GUI and sidecar startup smoke checks pass.
  3. A stale-sidecar package variant is available, created by replacing the
     packaged sidecar with the preserved older binary without changing the GUI.
  4. A Windows desktop session with Computer Use or a human operator is
     available; no live Codex request is required.
- **Manual test steps:**
  1. Copy the stale-sidecar package variant to a disposable directory outside
     the source checkout.
  2. Start the packaged `babelcodex-gui.exe`.
  3. Wait for the main window and startup connection check to finish.
  4. Observe the first visible status, banner or dialog related to sidecar
     connectivity.
  5. If the GUI remains usable, open the New Translation flow and attempt to
     reach the first job-start action without selecting a real user document.
  6. Capture the exact displayed error and close the GUI.
  7. Inspect the sidecar/GUI log for the protocol version, connection error or
     compatibility category; do not include credentials or full document text.
- **Expected result:**
  - The GUI does not silently report a healthy connection.
  - It displays an actionable connection/compatibility error before translation
    starts, or disables the affected action with an equivalent clear message.
  - No crash, hang or mid-job protocol mismatch occurs.
  - The log identifies the handshake/sidecar incompatibility without secrets.
- **Failure evidence to collect:** Screenshot or screen recording; exact error
  text; GUI and sidecar logs; Windows Event Viewer entry if the process crashes;
  package and stale-sidecar SHA-256 values; exact reproduction steps.
- **Result:** `PASS` / `FAIL` / `BLOCKED`
- **Notes:**
- **Error:**
- **Evidence:**

#### WIN-MANUAL-002 — Packaged GUI interaction, Chinese rendering and keyboard flow

- **Test ID:** `WIN-MANUAL-002`
- **Test name:** Packaged GUI renders Simplified Chinese and supports keyboard navigation
- **Current status:** `BLOCKED`
- **Blocker:** `COMPUTER_USE_UNAVAILABLE`
- **Purpose:** Prove native WebView rendering, readable Chinese labels, logical
  focus order, disabled-language-selector behavior and basic task navigation.
- **Related change:** `gui/src/App.tsx`, `gui/src/styles.css`,
  `gui/src/jobStore.ts`, `gui/src/sidecar.ts`, `gui/src/protocol.ts` and
  `WVQ-001`.
- **Preconditions:**
  1. Fresh current-source portable or installed GUI package is available.
  2. The package's sidecar handshake has passed automated smoke.
  3. A disposable Windows user/profile and mock fixture directory are
     available; no live Codex request is required.
  4. The operator can capture screenshots and keyboard focus behavior.
- **Manual test steps:**
  1. Start the packaged GUI and wait for the main window to appear.
  2. Confirm the main navigation, New Translation, Jobs, Job Details,
     Glossary, Diagnostics and Settings labels are visible.
  3. Check that Chinese text is not clipped, overlapped, replaced by tofu or
     truncated at the default window size.
  4. Use `Tab` and `Shift+Tab` from the first focusable control through the
     primary controls; record the focus order.
  5. Open Settings and inspect the disabled `界面语言` control. Confirm that
     its disabled state is understandable and does not block unrelated controls.
  6. Return to New Translation, use keyboard-only navigation to focus the file
     selection/action controls, and cancel without selecting a real document.
  7. Open Jobs and Job Details, then return to the main view and close the
     window normally.
- **Expected result:**
  - The window opens without crash or visible layout corruption.
  - Required Chinese labels and status text are readable with no critical
    clipping or overlap.
  - Focus order is logical, visible and reversible with `Shift+Tab`.
  - Disabled language selection is clearly disabled but does not disable
    unrelated navigation.
  - Cancellation and normal close complete without a stuck process.
- **Failure evidence to collect:** Screenshots at default size; screen recording
  of keyboard traversal; exact window size and Windows display scale; GUI log;
  process exit status; reproduction steps.
- **Result:** `PASS` / `FAIL` / `BLOCKED`
- **Notes:**
- **Error:**
- **Evidence:**

#### WIN-MANUAL-003 — DPI, NVDA and window lifecycle

- **Test ID:** `WIN-MANUAL-003`
- **Test name:** DPI scaling, screen-reader focus and window lifecycle
- **Current status:** `NOT RUN`
- **Blocker:** `none; SKIPPED_BY_USER_REQUEST`
- **Purpose:** Prove that the packaged GUI remains usable at Windows display
  scaling 125%, 150% and 200%, exposes a sensible focus/read order to NVDA,
  and handles resize and close behavior safely.
- **Related change:** `gui/src/App.tsx`, `gui/src/styles.css`, Tauri window
  configuration and `WVQ-002`.
- **Preconditions:**
  1. Current packaged GUI is available.
  2. A Windows display profile or test machine allows changing scale to 125%,
     150% and 200% and restarting the app between changes.
  3. NVDA is installed and can be started for the test user.
  4. Screenshots and accessibility notes can be collected.
- **Manual test steps:**
  1. Set Windows display scaling to 125% and restart the GUI.
  2. Inspect each primary screen and resize the window from normal size to a
     narrow but usable width.
  3. Repeat the inspection at 150% and 200%, restarting the GUI after each
     scale change.
  4. At one supported scale, start NVDA and move through navigation, status,
     buttons, inputs and disabled controls using `Tab`, `Shift+Tab` and NVDA
     reading commands.
  5. Resize the window, navigate to Jobs/Job Details, and close the window.
  6. Reopen the GUI and confirm the sidecar connection/status is not left in a
     stale or misleading state.
- **Expected result:**
  - No critical control or error/status text is clipped at 125%, 150% or 200%.
  - Resize does not overlap controls or make the primary flow unreachable.
  - NVDA announces meaningful names, roles and state for interactive controls;
    focus remains visible and logical.
  - Close/reopen does not crash or leave a stuck GUI/sidecar process.
- **Failure evidence to collect:** Screenshots for all scales; display settings
  values; NVDA speech viewer or notes; GUI/sidecar logs; process list before and
  after close; exact reproduction steps.
- **Result:** `PASS` / `FAIL` / `BLOCKED`
- **Notes:**
- **Error:**
- **Evidence:**

#### WIN-MANUAL-004 — Picker, allowlist, paths, cancellation and reconnection

- **Test ID:** `WIN-MANUAL-004`
- **Test name:** File picker, path safety and sidecar reconnection flow
- **Current status:** `BLOCKED`
- **Blocker:** `COMPUTER_USE_UNAVAILABLE`
- **Purpose:** Prove the packaged GUI's user-facing file intake and recovery
  behavior for allowed/denied paths, Unicode and space-containing paths,
  cancellation, reconnection and permissions.
- **Related change:** `gui/src/filePicker.ts`, `gui/src/App.tsx`, Tauri dialog
  permissions, sidecar path checks, artifact manifest/state handling and
  `WVQ-003`/`WVQ-004`.
- **Preconditions:**
  1. Current packaged GUI and sidecar are available.
  2. Prepare disposable directories named with spaces and non-ASCII
     characters, an allowed input directory, a denied directory, a missing
     file and a read-only or permission-restricted test location.
  3. Prepare the documented mock PDF fixture and a disposable output/state
     directory.
  4. Ensure no user PDFs, credentials or private glossary data are used.
- **Manual test steps:**
  1. Start the GUI and open New Translation.
  2. Use the native picker to select the allowed fixture from a path containing
     spaces; confirm the selected path is shown safely.
  3. Repeat with a non-ASCII directory/file name.
  4. Attempt to select a file outside the configured allowlist and a missing
     file; record the displayed validation result.
  5. Cancel the picker and confirm the form remains usable without creating a
     job.
  6. Start a disposable mock job, observe progress, and cancel it through the
     GUI.
  7. Stop and restart only the disposable sidecar/service, reconnect the GUI,
     and inspect the job state.
  8. Alter or delete one generated artifact, reopen the job details/validation
     view, and inspect whether the UI reports the artifact problem rather than
     silently treating the job as complete.
  9. Repeat one operation from a permission-restricted directory and record the
     user-facing error.
- **Expected result:**
  - Allowed paths are accepted; denied, missing and restricted paths are
    rejected with actionable errors.
  - Spaces and Unicode names survive selection and job inspection unchanged.
  - Picker cancellation creates no unintended job.
  - Cancellation reaches a terminal state and does not leave an orphaned GUI
    process.
  - Reconnection shows the persisted job state and does not falsely reclaim an
    active job.
  - Missing or tampered artifacts are reported as invalid/failed and are never
    silently skipped.
- **Failure evidence to collect:** Screenshots; exact paths with sensitive
  portions redacted; job ID and state JSON; GUI/sidecar logs; process list;
  generated artifact and checksum; exact reproduction steps.
- **Result:** `PASS` / `FAIL` / `BLOCKED`
- **Notes:**
- **Error:**
- **Evidence:**

#### WIN-MANUAL-005 — Clean-user installation, restart and recovery

- **Test ID:** `WIN-MANUAL-005`
- **Test name:** Clean-user first launch, sidecar restart and persisted-job recovery
- **Current status:** `NOT RUN / PERMANENT_SKIP_BY_USER_REQUEST`.
- **Blocker:** none; the clean-user installation/restart/recovery check was
  permanently skipped by explicit user request. No clean-user conclusion is
  inferred.
- **Purpose:** Prove that installation/first launch does not depend on the
  developer workspace and that a restarted service recovers persisted state
  safely without automatic unsafe reruns.
- **Related change:** Tauri packaging, `scripts/babelcodex-service.spec`,
  `src/codex_babeldoc/application/service.py`, orchestrator/state/CLI recovery
  and `WVQ-004`.
- **Preconditions:**
  1. Current unsigned NSIS/MSI or portable package and verified MSI payload are
     available.
  2. A disposable Windows user/profile with no repository checkout, Python
     environment, cached state or prior BabelCodex configuration is available.
  3. A disposable mock fixture and permitted working directories are prepared.
  4. The operator can terminate and restart only the disposable app/service
     processes.
- **Manual test steps:**
  1. Install or extract the package under the clean user/profile.
  2. Launch the GUI before opening the repository or installing development
     dependencies.
  3. Confirm the first-run window and sidecar status appear without a crash.
  4. Start a disposable mock job and record its job ID and state.
  5. Terminate the disposable runner/service before completion, without
     deleting its state directory.
  6. Restart the packaged service or GUI and inspect the persisted job.
  7. Confirm a dead runner is represented as a safe terminal worker-crash state
     and is not automatically rerun.
  8. Use the explicit retry action and confirm a new attempt begins only after
     that action.
  9. Close and relaunch the GUI, then inspect the same job once more.
- **Expected result:**
  - First launch works without repository or development-environment
    dependencies.
  - Persisted state is readable after restart.
  - A dead runner is terminalized safely, with actionable recovery guidance;
    no automatic translation or Codex usage starts.
  - Explicit retry starts a new attempt and normal close leaves no orphaned
    process.
- **Failure evidence to collect:** Installer/extraction command and checksum;
  screenshots; job/state JSON; sidecar and GUI logs; Windows Event Viewer;
  process list; exact profile and reproduction steps.
- **Result:** `PASS` / `FAIL` / `BLOCKED`
- **Notes:**
- **Error:**
- **Evidence:**

#### WIN-MANUAL-006 — Release security and live integration authorization

- **Test ID:** `WIN-MANUAL-006`
- **Test name:** Release security audit and authorized live Codex/PDF acceptance
- **Current status:** `NOT_RUN`
- **Blocker:** None until explicitly scheduled; if required GUI interaction is
  unavailable, record `BLOCKED` with `COMPUTER_USE_UNAVAILABLE` rather than
  claiming a result.
- **Purpose:** Separately verify release security controls and, only with
  explicit authorization, run a usage-bearing live Codex/PDF acceptance.
- **Related change:** Release artifacts, signing/Defender/SmartScreen/SBOM
  workflow (`WVQ-005`) and live integration (`WVQ-006`).
- **Preconditions:** Written authorization for any live model request; approved
  representative PDF with no private data; unsigned/signed artifact inventory;
  Defender/SmartScreen and certificate tooling; a controlled Windows desktop
  session.
- **Manual test steps:**
  1. Record package filenames, versions, SHA-256 values, signing status and
     build revision.
  2. Run the documented certificate/signature, Defender/SmartScreen and SBOM
     checks without suppressing warnings.
  3. Record each warning, verdict and any Windows Event Viewer evidence.
  4. Only after written authorization, authenticate the approved Codex session.
  5. Translate the approved fixture once through the documented live path.
  6. Inspect placeholder preservation, output PDF validity, QA result, logs and
     persisted job state; do not expose credentials or full document text.
  7. Record usage, model/session identity as permitted, output checksum and
     cleanup result.
- **Expected result:**
  - Release security results are explicit and reproducible; unsigned development
    artifacts are not described as release-signed.
  - Authorized live translation completes without placeholder, output-QA or
    state regressions; no unauthorized fallback or extra live request occurs.
- **Failure evidence to collect:** Signature/certificate output; Defender or
  SmartScreen message; SBOM; Event Viewer entry; exact command output; job
  state; output checksum; QA report; authorization record; reproduction steps.
- **Result:** `PASS` / `FAIL` / `BLOCKED`
- **Notes:**
- **Error:**
- **Evidence:**

## Validation run: 2026-09-09

### Validation environment

- Validation date: 2026-09-09
- Windows version and OS build: Windows 11, 10.0.29661 (observed by PyInstaller)
- Architecture: x86-64
- Python/uv: Python 3.12.13, uv 0.12.10
- Node/npm: Node.js 24.19.0, npm 11.17.0
- Rust: rustc/cargo 1.98.0, stable-x86_64-pc-windows-msvc
- Visual Studio: Build Tools 17.14.39, complete installation detected
- WebView2: Microsoft Edge WebView2 Runtime 152.0.4191.66 detected
- Temporary PyInstaller environment: PyInstaller 6.22.2
- WSL source path: W:\home\shiraishi\VSCode Workspace\Codex_Translator
- Windows workspace path: E:\Shiraishi\VSCode Workspace\Codex_Translator
- Linux/WSL source branch: dev
- Linux/WSL source commit: 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab
- Working-tree changes included: yes; AGENTS.md, the Linux bundle script mode change, and untracked docs/development/ and docs/validation/ were included
- Synchronization method: one-way filtered robocopy from WSL to E:, excluding .git, virtual environments, node_modules, Rust target, build/log/state/input/output directories, caches, secrets and generated document/database files
- Synchronization date: 2026-09-09
- Credentials/external services: doctor reports Codex authenticated through ChatGPT; no live translation or paid model request was made

### Validation checklist

| Item | Classification | Command | Working directory | Status | Result |
| --- | --- | --- | --- | --- | --- |
| Dependency synchronization | Required | uv sync --locked --extra runtime --extra dev | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | Resolved 95 packages and checked 91 installed packages |
| Lock consistency | Required | uv lock --locked | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | Lock resolved successfully |
| Python formatting | Required | uv run ruff format --check . | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | 75 files already formatted after temporary build helper cleanup |
| Python lint | Required | uv run ruff check . | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | All checks passed after temporary helper cleanup |
| Python full test suite | Required | uv run pytest -q | E:\Shiraishi\VSCode Workspace\Codex_Translator | FAIL | 2 failed, 138 passed, 3 deselected |
| Runtime doctor | Required | uv run cbpdf --config config/example.toml doctor | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | Python/BabelDOC/Codex checks passed; ChatGPT login available |
| GUI dependency install | Required | npm.cmd --prefix gui ci | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | Exit 0; 158 packages installed, with 2 moderate audit advisories and esbuild pending-script warning |
| GUI tests | Required | npm.cmd --prefix gui test -- --run | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | 3 files, 17 tests passed |
| GUI production build | Required | npm.cmd --prefix gui run build | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | TypeScript and Vite build passed |
| Tauri Rust host | Required | cargo check --manifest-path gui/src-tauri/Cargo.toml | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | Dev profile check passed |
| Current-source sidecar JSONL | Applicable | .venv\Scripts\babelcodex-service.exe --config config/example.toml with list_jobs JSONL stdin | E:\Shiraishi\VSCode Workspace\Codex_Translator | PASS | Response ok=true, jobs=[], exit 0 |
| Windows sidecar rebuild | Required | uv run --with pyinstaller python -m PyInstaller --noconfirm --clean --onefile ... | E:\Shiraishi\VSCode Workspace\Codex_Translator | BLOCKED | Temporary PyInstaller 6.22.2 analysis did not produce an exe after several minutes and was stopped; the legacy launcher also pointed to a missing Python 3.11 executable |
| Current-source target-triple sidecar smoke | Required | packaged sidecar list_jobs smoke | E:\Shiraishi\VSCode Workspace\Codex_Translator | BLOCKED | Current-source sidecar rebuild is blocked; the existing binary belongs to an earlier source state and was not used as current validation evidence |
| Current-source NSIS/MSI rebuild | Required | Tauri NSIS/MSI build with current target-triple sidecar | E:\Shiraishi\VSCode Workspace\Codex_Translator | BLOCKED | Depends on the blocked current-source sidecar rebuild |
| Packaged GUI interactive E2E | Required | desktop file-picker/path/cancel/output/close matrix | E:\Shiraishi\VSCode Workspace\Codex_Translator | NOT RUN | No current-source packaged bundle was available; this run only covered source GUI tests and process-independent checks |
| Clean-user environment | Required | packaged GUI in clean Windows user profile | E:\Shiraishi\VSCode Workspace\Codex_Translator | NOT RUN | Requires a current-source packaged bundle and isolated profile; existing project-root configuration cannot prove clean-user behavior |
| Defender/SmartScreen, signing and SBOM | Required | release security and artifact audit | E:\Shiraishi\VSCode Workspace\Codex_Translator | NOT RUN | Current artifacts are unsigned development outputs and the release audit workflow was not entered |
| Live Codex/PDF integration | Applicable | real Codex translation fixture | E:\Shiraishi\VSCode Workspace\Codex_Translator | NOT RUN | Not authorized for this validation; ordinary tests must not consume paid or ChatGPT-plan usage |
| Target Linux machine smoke | Not applicable to Windows execution | target Linux runtime command | E:\Shiraishi\VSCode Workspace\Codex_Translator | NOT APPLICABLE | Must be executed on a target Linux machine; WSL/Windows cannot substitute for that platform run |
| npm audit remediation | Applicable | npm audit fix | E:\Shiraishi\VSCode Workspace\Codex_Translator\gui | NOT RUN | Not defined as a required validation command and would change dependency state; advisory was recorded for follow-up |

### Errors and analysis

| Item | Key error/log path | Likely category | Blocks other checks | Follow-up |
| --- | --- | --- | --- | --- |
| Temporary PyInstaller launcher | PyInstaller launcher failed because its Python 3.11 target did not exist | environment configuration | Yes, current packaged-sidecar checks | Provide a reproducible supported Windows sidecar build path; do not solve by changing business code |
| Temporary PyInstaller build | build/babelcodex-service.spec and PyInstaller process tree; no dist exe was produced before stop | environment/build resource or packaging setup | Yes, current target-triple and NSIS/MSI rebuild | Linux development should assess a bounded/reproducible PyInstaller build and then request Windows re-validation |
| Ruff contamination by temporary helper | build/_windows_sidecar_entry.py was initially included in lint and caused I001; helper was removed and Ruff rerun passed | validation setup | No | Keep temporary build helpers outside lint scope or remove them before quality gates |
| Glossary CLI test | tests/test_cli.py:63; TOMLDecodeError: Invalid hex value at line 2, column 18 because C:\Users... was written into a TOML basic string without escaping backslashes | Windows-specific test defect/path serialization | No, independent checks continued | Linux follow-up: make the test fixture emit valid TOML Windows paths or add a tested path serialization helper |
| MCP cleanup test | tests/test_mcp.py:107; MCP internal error with [WinError 32] another process is using the file, while shutil.rmtree removes work\job-paper | Windows-specific project lifecycle or test synchronization issue | No, GUI/build checks continued | Linux follow-up: inspect worker/process handle closure before cleanup; preserve cleanup allowlist and add a Windows regression test |

### Not executed / blocked

- The current-source packaged sidecar, NSIS/MSI rebuild and packaged GUI smoke are BLOCKED by the PyInstaller build environment. Existing older artifacts were deliberately not treated as evidence for commit 7ba4ddf.
- Full Python validation is FAIL, not PASS. The two failing tests are independent of the GUI and source-sidecar protocol checks, so those checks were continued.
- The current Windows source state is therefore WINDOWS_VERIFICATION_PENDING: native toolchain, GUI source checks and source sidecar protocol pass, but the full Python gate has Windows failures and current-source packaging is blocked.

### Linux follow-up required

1. Investigate the Windows TOML path fixture failure in tests/test_cli.py and determine whether the correction belongs in the fixture or a shared path serializer.
2. Investigate the WinError 32 cleanup failure at src/codex_babeldoc/application/mcp.py:321-340 and the worker lifecycle around tests/test_mcp.py:77-111; do not weaken the cleanup allowlist.
3. After Linux-side fixes, run the Linux regression suite and mark Windows verification as WINDOWS_VERIFICATION_PENDING until the current source is rebuilt and rechecked on Windows.
4. Establish a reproducible Windows sidecar build path, then rebuild the target-triple sidecar and NSIS/MSI packages before repeating packaged smoke and clean-user E2E.
5. Treat the npm moderate advisories as dependency maintenance, not as an automatic npm audit fix during this validation task.

### Final review

- Source hashes for AGENTS.md, current state/CLI/test files, Plan and validation documents matched between WSL and E: PASS.
- Windows-side code was not synchronized back to WSL: PASS.
- No business code, dependency manifest or architecture was modified during validation: PASS.
- Every applicable check above has an explicit status; FAIL, BLOCKED and NOT RUN entries include reasons.

## Validation run: 2026-09-09 (latest Linux state re-validation)

### Scope and source state

- Validation source: current WSL checkout, branch dev, commit 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab.
- The WSL checkout had existing local changes in application code, tests, build scripts and documentation; these changes were included in the validation source.
- No business code was modified during this Windows validation. A temporary PyInstaller entrypoint and temporary build directories were created under build/ in the E: working copy and removed after the build attempt.

### One-way synchronization

- Direction: WSL → Windows only.
- Destination: E:/Shiraishi/VSCode Workspace/Codex_Translator.
- The synchronization used filtered robocopy /E /COPY:DAT /DCOPY:DAT /XJ, excluding Git metadata, virtual environments, dependency caches, logs, state/user-data directories, generated outputs and GUI build artifacts. PDF, log, bytecode and database files were also excluded.
- Key source/document hashes matched between WSL and E: after synchronization. The copy operation returned Robocopy exit code 3, which indicates copied or mismatched files and is expected for this controlled mirror operation.

### Windows environment

- Windows 11 build 10.0.29661.
- Python 3.12.13 (uv-managed), uv 0.12.10.
- Node 24.19.0, npm 11.17.0.
- Rust/Cargo 1.98.0, stable MSVC toolchain.
- Visual Studio Build Tools 17.14.39.
- WebView2 152.0.4191.66.
- Codex authentication was available through the local CLI session.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization: uv sync --locked --extra runtime --extra dev | PASS | Resolved 95 packages and checked 91 packages. |
| Lockfile consistency: uv lock --locked | PASS | Lockfile accepted without changes. |
| Python formatting: uv run ruff format --check . | PASS | 75 files already formatted. |
| Python lint: uv run ruff check . | PASS | No lint violations. |
| Python full test suite: uv run pytest -q | FAIL | 138 passed, 2 failed, 3 deselected. See failure analysis below. |
| CLI doctor: uv run cbpdf --config config/example.toml doctor | PASS | Python/BabelDOC/Codex SDK versions were detected; Codex authentication was reported active; configured paths were accepted. |
| GUI dependency install: npm --prefix gui ci | PASS | 158 packages installed. npm reported 2 moderate audit advisories and an esbuild pending-script warning; no automatic audit fix was run. |
| GUI tests: npm --prefix gui test -- --run | PASS | 3 test files, 17 tests passed. |
| GUI production build: npm --prefix gui run build | PASS | TypeScript/Vite build completed. |
| Tauri Rust compilation check: cargo check --manifest-path gui/src-tauri/Cargo.toml | PASS | Cargo check completed successfully. |
| Current-source Python sidecar JSONL smoke | PASS | The sidecar from the current E: virtual environment accepted list_jobs and returned an empty job list with exit code 0. |
| Current-source packaged sidecar rebuild | BLOCKED | The legacy PyInstaller launcher referenced a missing Python 3.11 executable. A uv-provided PyInstaller 6.22.2 attempt remained in dependency analysis without producing an executable and was stopped after several minutes. |
| Existing target-triple sidecar/package evidence | NOT RUN | Existing artifacts predated this latest Linux source and were not reused as current-source evidence. |
| Packaged GUI interactive/clean-user/path matrix | BLOCKED | A current-source packaged sidecar/bundle was unavailable because the rebuild was blocked. |
| npm advisory remediation | NOT RUN | Not required by this validation and would mutate dependency state; no npm audit fix was executed. |
| Linux-only checks | NOT APPLICABLE | This run was scoped to Windows validation; Linux results remain recorded in the Linux project documents. |

### Failure analysis

1. tests/test_cli.py::test_glossary_cli_import_and_list failed with TOMLDecodeError: Invalid hex value when a Windows path such as C:/Users/... was written into a TOML basic string. The fixture/path serialization does not escape Windows backslashes correctly.
2. tests/test_mcp.py::test_start_get_validate_and_cleanup_are_scoped failed during cleanup with Windows [WinError 32] (another process is using the file). The failure occurs while removing work/job-paper, indicating that a worker/process or file handle remains active when the scoped cleanup runs. This needs Linux-side lifecycle/cleanup handling and a Windows re-run; it was not changed in this validation.
3. The packaged sidecar build is an environment/tooling blocker rather than a passing-package result: the configured legacy launcher points to Python 3.11, which is absent, while the uv-isolated PyInstaller attempt did not finish producing the executable. Consequently, packaged GUI acceptance cannot be inferred from the direct sidecar smoke or from stale artifacts.

### Remaining follow-up required

- Re-sync the updated Linux source to Windows and rerun the focused tests for TOML Windows-path serialization and MCP cleanup, followed by the full Windows Python suite. These items remain `WINDOWS_VERIFICATION_PENDING` until executed on Windows.
- Establish a reproducible current-source PyInstaller/sidecar build path, rebuild the target-triple sidecar and Windows installer/package, and record fresh hashes. This remains `WINDOWS_BLOCKED` while the build environment is unavailable.
- After a fresh package exists, execute the packaged GUI interactive, clean-user, cancellation/reconnection and path/permission matrix.
- Review the two npm moderate advisories separately; do not apply automatic dependency remediation as part of this validation.

### Overall status

Windows verification for commit 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab is WINDOWS_VERIFICATION_PENDING: the dependency, static, doctor, GUI source, Tauri check and direct current-source sidecar checks passed, but the full Python suite failed and packaged validation remains blocked.

## Validation run: 2026-09-09 (repeat after re-sync)

### Scope and source state

- Validation source: the same current WSL checkout, branch dev, commit 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab.
- The source was synchronized again from WSL to E: using the documented filtered one-way mirror. No Windows code or generated output was synchronized back.
- No business code was modified during this repeat validation.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | uv sync --locked --extra runtime --extra dev and uv lock --locked both completed successfully. |
| Python formatting and lint | PASS | Ruff format check and Ruff lint both passed; 75 files were already formatted. |
| Python full test suite | FAIL | The run visibly reported one failure among the 142 selected tests; 3 tests were deselected. The runner did not emit its final summary in this invocation. Independent file runs recorded CLI 5 passed and MCP 10 passed, 1 failed. |
| CLI Windows-path regression coverage | PASS | tests/test_cli.py passed all 5 tests; the previously recorded TOML Windows-path failure was not reproduced after the latest re-sync. |
| MCP scoped lifecycle/cleanup | FAIL | tests/test_mcp.py failed test_start_get_validate_and_cleanup_are_scoped with internal MCP server error caused by Windows WinError 32 while removing work/job-paper; the other 10 MCP tests passed. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication were detected. |
| GUI dependency install | PASS | 158 packages installed; the same 2 moderate audit advisories and esbuild pending-script warning were reported. |
| GUI tests | PASS | 3 files, 17 tests passed. |
| GUI production build | PASS | TypeScript/Vite build passed. |
| Tauri Rust host | PASS | cargo check completed successfully with the Windows MSVC toolchain. |
| Current-source sidecar JSONL smoke | PASS | list_jobs returned ok=true with jobs=[] and exit code 0. |
| Current-source sidecar/package rebuild | BLOCKED | The legacy PyInstaller launcher still referenced missing Python 3.11; the uv-provided PyInstaller environment was available, but no current-source executable was produced by the prior bounded build attempt. |
| Current-source target-triple sidecar, NSIS/MSI and packaged GUI matrix | BLOCKED | These checks depend on a fresh current-source sidecar/package, which remains unavailable. |
| Clean-user, Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | No current-source release package was available and this validation did not enter the release audit workflow. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation and would mutate dependency state; npm audit fix was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Current failure and blocking analysis

- The TOML Windows-path failure from the earlier run is not a current failure: the CLI test file passed all 5 tests in this repeat.
- The remaining project-level Windows failure is MCP scoped cleanup. A worker/process or file handle remains active when the cleanup path removes work/job-paper. The relevant test location is tests/test_mcp.py:107; the cleanup implementation is in src/codex_babeldoc/application/mcp.py:321-340.
- The full test runner did not return a final summary in this invocation, while the focused file runs completed. This observation should be checked together with the MCP worker/file-handle lifecycle fix; it is not evidence of a pass.
- Packaging remains blocked by the Windows build environment/tooling path. Direct current-source sidecar smoke is not package evidence, and stale target-triple artifacts were deliberately not reused.

### Linux follow-up required

1. [Linux fix completed, Windows pending] MCP cleanup now checks the current MCP future before deleting a job-owned directory; re-sync this source and rerun `tests/test_mcp.py::test_start_get_validate_and_cleanup_are_scoped` plus the full Windows Python suite.
2. Confirm that the full Windows test runner exits cleanly and reports its final summary after the cleanup lifecycle fix.
3. Establish a reproducible current-source PyInstaller/sidecar build path, rebuild the target-triple sidecar and NSIS/MSI package, and record fresh hashes.
4. After a fresh package exists, execute packaged GUI interactive, clean-user, cancellation/reconnection and path/permission checks.
5. Review the npm moderate advisories separately; do not apply automatic dependency remediation within this validation task.

### Overall status

The latest Windows status for commit 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab remains WINDOWS_VERIFICATION_PENDING: CLI Windows-path coverage is WINDOWS_PASS, source-level checks and direct sidecar protocol validation pass, MCP cleanup failed in the prior run and has a new Linux lifecycle fix awaiting Windows re-validation, and current-source packaging remains WINDOWS_BLOCKED.

## Linux reconciliation after latest Windows validation

- Linux full verification after the MCP lifecycle fix: `uv run pytest -q` reported `144 passed, 3 deselected`; GUI tests reported `17 passed`; Vite build, Ruff, and compileall passed.
- The CLI TOML Windows-path fixture is `WINDOWS_PASS` based on the latest Windows focused run.
- The MCP cleanup lifecycle fix is `LINUX_VERIFIED` and `WINDOWS_PASS`: the focused cleanup test, active-job guard, retry test and Future lifecycle coverage passed on Windows.
- The Linux follow-up also covers the race where a very fast completed future could remain in the MCP context after its callback ran; this regression is `LINUX_VERIFIED` and `WINDOWS_PASS`.
- Final Linux verification after the Future lifecycle refinement: `uv run pytest -q` reported `144 passed, 3 deselected`; the same updated implementation passed the latest Windows focused and full Python checks.

## Validation run: 2026-09-09 (latest Linux lifecycle fix re-validation)

### Scope and source state

- Validation source: current WSL working tree at HEAD 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab, including the uncommitted Linux MCP lifecycle changes and their regression tests.
- The source was synchronized again from WSL to E: with the documented filtered Linux-to-Windows mirror. Key source and document hashes matched after the forced timestamp-aware copy.
- The Linux changes under test track MCP futures, handle the completion-callback/registration race, reject cleanup of active jobs, and retry transient Windows deletion failures. Linux verification for these changes was recorded as 144 passed, 3 deselected.
- No business code was modified during this Windows validation.

### Windows environment

- Windows 11 build 10.0.29661; uv 0.12.10.
- Project Python 3.12.13, Node 24.19.0, npm 11.17.0.
- Rust/Cargo 1.98.0 with Windows MSVC; Visual Studio Build Tools 17.14.37614.0.
- WebView2 152.0.4191.66.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | uv sync --locked --extra runtime --extra dev and uv lock --locked completed successfully. |
| Python formatting and lint | PASS | Ruff format check and Ruff lint passed; 75 files were already formatted. |
| Python focused CLI/MCP regression tests | PASS | tests/test_cli.py and tests/test_mcp.py: 18 tests passed. |
| Python full test suite | PASS | 144 passed, 3 deselected in 19.79 seconds. |
| CLI Windows-path regression coverage | PASS | The TOML Windows-path serializer test and all other CLI tests passed. |
| MCP scoped lifecycle/cleanup | PASS | The Future lifecycle, active-job guard, cleanup retry and scoped cleanup tests passed on Windows. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI dependency install | PASS | npm ci completed; 158 packages installed. npm still reports 2 moderate audit advisories and an esbuild pending-script warning. |
| GUI tests | PASS | 3 files, 17 tests passed. |
| GUI production build | PASS | TypeScript/Vite build passed. |
| Tauri Rust host | PASS | cargo check passed with the Windows MSVC toolchain. |
| Current-source sidecar JSONL smoke | PASS | list_jobs returned ok=true with jobs=[] and exit code 0. |
| Current-source sidecar/package rebuild | BLOCKED | The legacy PyInstaller launcher still references missing Python 3.11; the available uv PyInstaller environment was not used to claim a current packaged artifact. |

## Validation run: 2026-09-10 (current GUI working tree)

### Scope and source state

- Validation source: `/home/shiraishi/VSCode Workspace/Codex_Translator`, branch `dev`, commit `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca`.
- The Linux working tree was dirty before synchronization and contained four uncommitted GUI files: `gui/src/App.test.tsx`, `gui/src/App.tsx`, `gui/src/jobStore.ts`, and `gui/src/styles.css`. This was a working-tree validation, not a clean-commit validation.
- The Windows target was `E:\Shiraishi\VSCode Workspace\Codex_Translator`.
- Synchronization was Linux → Windows only. A controlled file-by-file copy updated the current source/configuration/document files and did not delete or overwrite the target's existing `.venv`, `gui\node_modules`, `build`, `dist`, Tauri `target`, logs, state, or generated artifacts. Key SHA-256 hashes for the synchronized GUI source and validation documents matched between Linux and Windows.
- No Windows-side source changes were synchronized back to Linux. No business code was modified during the Windows validation.

### Windows environment

- Windows 11 build `10.0.29661`, x86-64.
- Project Python: `3.12.13` from `E:\Shiraishi\VSCode Workspace\Codex_Translator\.venv\Scripts\python.exe`.
- System Python: `3.14.7`; not used for project checks because it is outside the supported `3.11–3.12` range.
- uv `0.12.10`.
- Node.js `24.19.0`, npm `11.17.0`.
- Rust/Cargo `1.98.0`, Windows MSVC toolchain; Visual Studio Build Tools were available for `cargo check`.
- WebView2 was not re-probed in this run; packaged GUI validation remained pending.
- Codex credentials were not used for translation. The existing local Codex runtime was present, but no paid or ChatGPT-plan translation was started.

### Validation checklist

| Item | Classification | Command | Working directory | Status | Result |
| --- | --- | --- | --- | --- | --- |
| Source synchronization and hash verification | Required | Controlled Linux → Windows copy; PowerShell `Get-FileHash` | WSL source and `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Current GUI source and selected documents matched; target local generated/dependency directories were preserved. |
| Python runtime compatibility | Required | `.venv\Scripts\python.exe --version` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Python 3.12.13. |
| Lock consistency | Required | `uv lock --locked` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Lockfile accepted without changes. |
| Python formatting | Required | `.venv\Scripts\ruff.exe format --check .` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | 78 files already formatted. |
| Python lint | Required | `.venv\Scripts\ruff.exe check .` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | No lint violations. |
| Python bytecode compilation | Applicable | `.venv\Scripts\python.exe -m compileall -q src tests scripts` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Completed with exit code 0. |
| Python focused CLI/path tests | Applicable | `.venv\Scripts\python.exe -m pytest -q tests\test_cli.py::test_collect_doctor_checks_detects_installed_runtime tests\test_cli.py::test_doctor_fails_when_codex_is_not_authenticated tests\test_cli.py::test_glossary_cli_import_and_list tests\test_cli.py::test_toml_string_escapes_windows_path` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | 4 passed. |
| Python full test suite | Required | `.venv\Scripts\python.exe -m pytest -q` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | FAIL | 156 passed, 3 deselected, 1 failed. `tests\test_cli.py::test_doctor_succeeds_when_all_critical_checks_pass` received `doctor() == 1` because `babeldoc_cli` is `null` on this Windows installation, although BabelDOC Python 0.6.4 and the Codex runtime were present. |
| GUI tests | Required | `npm.cmd test -- --run` | `E:\Shiraishi\VSCode Workspace\Codex_Translator\gui` | FAIL | The GUI build/test environment started successfully, but the current App tests were not stable: the mock transport generated duplicate `mock-job-1` entries/React duplicate-key warnings, and the cancel/details tests timed out while querying the job row. The isolated queue test passed. |
| GUI production build | Required | `npm.cmd run build` | `E:\Shiraishi\VSCode Workspace\Codex_Translator\gui` | PASS | TypeScript and Vite build completed successfully. |
| Tauri Rust host | Applicable | `cargo.exe check` | `E:\Shiraishi\VSCode Workspace\Codex_Translator\gui\src-tauri` | PASS | Windows MSVC cargo check completed successfully. |
| Tauri configuration JSON | Applicable | Python `json.tool` against `gui\src-tauri\tauri.conf.json` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Configuration parsed successfully; icon files were present. |
| Current-source sidecar JSONL smoke | Required | `list_jobs` and `shutdown` JSONL piped to `scripts\sidecar_entry.py --config config\example.toml` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Both responses returned `ok=true`; process exit code 0. |
| Current-source bundle audit | Applicable | `python scripts\check_gui_bundle.py ... --target x86_64-pc-windows-msvc` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | Existing current-source staging audit passed. It was static audit evidence, not packaged GUI execution evidence. |
| Current-source PyInstaller sidecar rebuild | Required | `.venv\Scripts\pyinstaller.exe --clean --noconfirm scripts\babelcodex-service.spec` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | BLOCKED | `.venv\Scripts\pyinstaller.exe` was absent. Existing target-triple binaries were not treated as rebuilt evidence for this working tree. |
| NSIS/MSI packaged build | Required | Tauri package build | `E:\Shiraishi\VSCode Workspace\Codex_Translator\gui` | BLOCKED | Dependent on the current-source sidecar rebuild, which was blocked by missing PyInstaller. |
| Packaged GUI process and interaction smoke | Required | Packaged executable launch/file picker/job/cancel/output checks | Windows desktop | NOT RUN | Current-source NSIS/MSI packages were not produced; existing historical packages were not used as evidence for this source state. |

### Errors and analysis

| Item | Key error | Likely category | Blocks other checks | Follow-up |
| --- | --- | --- | --- | --- |
| GUI cancel/details tests | React warning: duplicate key `mock-job-1`; job-row query timed out although the row appeared in the rendered output | Project code: `gui/src/sidecar.ts` mock transport and/or `gui/src/jobStore.ts` event reconciliation | No; GUI build, Tauri check, sidecar smoke and static audit continued | Fix mock job/event reconciliation so `job_created` does not duplicate a job already returned by `list_jobs`; add deterministic App regression coverage, then rerun Linux and Windows GUI tests. |
| Full Python suite | `doctor()` returned 1 because `babeldoc_cli` was `null` on Windows | Project CLI health-check contract or Windows installation shape | No; independent checks continued | Decide whether Windows should provide a BabelDOC CLI executable or whether `doctor()` should treat the Python BabelDOC backend as sufficient for the configured `python-internal` backend; add a platform regression test. |
| Current-source packaging | `.venv\Scripts\pyinstaller.exe` absent | Environment/dependency availability | Yes for current-source NSIS/MSI and packaged GUI checks | Install or provision the documented PyInstaller environment on Windows, rebuild the sidecar from this source state, then rebuild and smoke-test NSIS/MSI packages. |

### Not executed / blocked

- Current-source NSIS/MSI packaging and packaged GUI smoke are `BLOCKED` because PyInstaller was not available in the target project's virtual environment. Historical artifacts were deliberately excluded from current-source evidence.
- Full packaged file-picker, input/output allowlist, spaces/backslashes/non-ASCII paths, cancellation, reconnection, completion artifact, output-directory, window-close and cleanup interaction matrices are `NOT RUN` because current-source packages were unavailable.
- NVDA/screen-reader validation, DPI 125%/150%/200% validation, clean-user first launch, Defender/SmartScreen, signing, SBOM, portable release audit and target-user release smoke are `NOT RUN`; these require the Windows desktop/package validation path and were not implied by source-level checks.
- Real Codex PDF translation and usage/throughput benchmarking were `NOT RUN` to avoid paid or ChatGPT-plan usage in validation.

### Final review

- Windows workspace corresponds to the intended Linux source state for all synchronized control files: PASS.
- Synchronization direction remained Linux → Windows; no Windows code was copied back: PASS.
- No business code or dependency manifest was modified during validation: PASS.
- Every applicable check has an explicit status; all FAIL/BLOCKED/NOT RUN entries include reasons: PASS.
- Current overall Windows status: `WINDOWS_VERIFICATION_PENDING`.

### Linux follow-up required

1. Fix the shared mock transport/job-store duplicate-event reconciliation and add deterministic cancel/details GUI regression tests.
2. Re-run Linux GUI Vitest and full GUI build after the mock reconciliation fix.
3. Clarify `doctor()` semantics for the configured Windows `python-internal` BabelDOC backend when the `babeldoc` CLI executable is absent; add a regression test that covers Windows installation shape without weakening backend checks.
4. Provision PyInstaller in the Windows validation environment, rebuild the current-source target-triple sidecar, and repeat NSIS/MSI plus packaged GUI validation.
5. Keep packaged desktop interaction, NVDA, DPI, clean-user, signing/SBOM and release statuses as `WINDOWS_VERIFICATION_PENDING` until directly executed.

## Linux reconciliation after the 2026-09-10 Windows result

### Windows failure disposition

- The Windows GUI duplicate-key failure was classified as a shared project-code issue, not a Windows-only environment issue. The failing behavior was that `JobStore.applyEvent()` inserted a `job_created` event even when the same job had already arrived through `list_jobs`.
- The Windows `doctor()` failure remains a separate installation-shape/check-contract issue: the target exposed BabelDOC 0.6.4 through the Python backend but had no `babeldoc` executable (`babeldoc_cli = null`). Linux did not weaken the critical doctor checks without a confirmed backend contract decision.
- The PyInstaller absence remains an environment/dependency block on the Windows validation copy. It was not worked around by reusing stale artifacts.

### Linux implementation and verification

- `gui/src/jobStore.ts` now applies `job_created` idempotently. An existing `job_id` is merged in place and retains richer state from `list_jobs` or reconciliation; only an unseen `job_id` is inserted.
- `gui/src/jobStore.test.ts` adds regression coverage for a created event replayed after `list_jobs`, including the single-job invariant and preservation of stage/attempt state.
- `gui/src/App.tsx` now exposes `Job details` as the actual accessible heading and renders the job ID as separate metadata, resolving the remaining Linux test/accessibility mismatch.
- Linux checks completed after the fix:
  - GUI Vitest: `3 files, 18 tests passed`;
  - GUI production build: `npm run build` passed;
  - Python suite: `uv run pytest -q --tb=short` → `157 passed, 3 deselected`;
  - Ruff format check and lint: passed;
  - Python compileall: passed;
  - `git diff --check`: passed.

### Current cross-platform status

- The duplicate-job fix is `LINUX_VERIFIED` and requires Windows re-validation. It is not `WINDOWS_PASS`.
- Windows GUI Vitest must be rerun against the synchronized fixed source. The Windows `doctor()` failure still requires a separate decision about the `python-internal` BabelDOC backend versus the `babeldoc` executable check.
- Current-source Windows PyInstaller/NSIS/MSI rebuild remains blocked until PyInstaller is provisioned in the Windows validation environment.
- Packaged GUI interaction, clean-user/path-permission coverage, NVDA, DPI, Defender/SmartScreen, signing/SBOM and release checks remain `WINDOWS_VERIFICATION_PENDING`, `WINDOWS_BLOCKED` or `NOT RUN` as applicable; no Linux result substitutes for those native checks.
| Current-source target-triple sidecar, NSIS/MSI and packaged GUI matrix | BLOCKED | These checks depend on a fresh current-source sidecar/package, which is unavailable. Existing binaries were not reused as latest-source evidence. |
| Clean-user, Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | No current-source release package was available and the release audit workflow was not entered. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation and would mutate dependency state; npm audit fix was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Failure and blocking analysis

- The Linux MCP lifecycle fix is now Windows-verified: the focused MCP suite and the full Python suite both pass. The previous Windows WinError 32 failure is therefore historical and remains documented, but is no longer an active failure for this source state.
- Packaging remains blocked independently of the test result. The legacy PyInstaller launcher points to a missing Python 3.11 executable, and the existing target-triple sidecar belongs to an earlier source state. No stale package was used to claim current-source packaging success.
- Because no fresh current-source package exists, packaged GUI interaction, clean-user behavior, installer behavior and release-security checks cannot be inferred from source tests or direct sidecar smoke.

### Linux follow-up required

1. Provide a reproducible supported Windows current-source sidecar build path, or explicitly document the approved build environment and command. **Linux side completed 2026-09-09**: the repository now ships a controlled PyInstaller spec (`scripts/babelcodex-service.spec`), a frozen-capable top-level entry point (`scripts/sidecar_entry.py`) that dispatches the `--worker-request` BabelDOC worker subcommand (`src/codex_babeldoc/backends/worker_client.py::worker_command`), and documented build commands. Building the packaged sidecar from this source and rerunning packaged sidecar smoke remains a Windows execution item.
2. Rebuild the target-triple sidecar and NSIS/MSI package from this source, record fresh hashes, and rerun packaged sidecar smoke (now possible with the controlled spec/entry above; status `WINDOWS_VERIFICATION_PENDING`).
3. Execute packaged GUI interactive, clean-user, cancellation/reconnection and Windows path/permission validation after a fresh package exists.
4. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
5. Review the npm moderate advisories separately; do not apply automatic dependency remediation during this validation.

### Linux follow-up completed (2026-09-09) — reproducible sidecar build path

The Linux side added the controlled packaging and frozen-worker path requested above:

- `scripts/sidecar_entry.py`: stable top-level PyInstaller entry point (replaces the previously temporary, uncommitted entry that caused the missing-Python-3.11 launcher workaround).
- `scripts/babelcodex-service.spec`: platform-neutral PyInstaller spec with BabelDOC/openai_codex hidden imports and data collection.
- `src/codex_babeldoc/backends/worker_client.py`: new `worker_command()` builds the worker subprocess command; frozen executables dispatch through `--worker-request` instead of `python -m` (which cannot work inside a PyInstaller bundle).
- `src/codex_babeldoc/application/sidecar.py`: `main()` now hands `--worker-request <path>` to the BabelDOC worker entry point, so one packaged binary serves both JSONL sidecar and worker subprocess.
- Regression tests added in `tests/test_worker.py::TestWorkerCommand`.

Linux verification for this round: `uv run pytest -q` reported `147 passed, 3 deselected`; Ruff lint, Ruff format check, Python compileall, and spec syntax validation (AST parse) passed. Additionally, a real Linux PyInstaller 6.22.2 build from `scripts/babelcodex-service.spec` produced a working sidecar (~218 MB on Linux) that passed JSONL `list_jobs`/`list_glossary`/`shutdown` smoke and the frozen `--worker-request` dispatch (protocolized `WORKER_REQUEST_INVALID` with exit 2 for a missing request file). These checks are `LINUX_VERIFIED` only; the Windows target-triple packaged sidecar build, `--worker-request` behavior inside the Windows frozen executable, packaged GUI and installers must still be executed and verified on Windows and are therefore `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_PASS`.

### Overall status

The latest Windows status for the Linux working tree is split by validation scope: current source-level, full Python, GUI source, Tauri and direct sidecar checks are `WINDOWS_PASS`; current-source packaging and packaged GUI/release validation remain `WINDOWS_BLOCKED` or `NOT RUN`. The newly added frozen worker dispatch and the reproducible sidecar build path are `WINDOWS_VERIFICATION_PENDING` — the Linux implementation and regression tests are verified on Linux only, and must be exercised inside a real PyInstaller binary on Windows before any packaged-scope item may be marked `WINDOWS_PASS`.

## Validation run: 2026-09-09 (repeat after current-source sync)

### Scope and source state

- Validation source: current WSL working tree at HEAD 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab, including the uncommitted Linux MCP lifecycle changes.
- The source was synchronized from WSL to E: with the filtered, timestamp-aware one-way mirror. Key source and document hashes matched after synchronization.
- No business code was modified during this Windows validation.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | uv sync --locked --extra runtime --extra dev and uv lock --locked completed successfully. |
| Python formatting and lint | PASS | Ruff format check and Ruff lint passed; 75 files were already formatted. |
| Python full test suite | PASS | 144 passed, 3 deselected in 20.73 seconds. |
| CLI/MCP focused regression tests | PASS | 18 tests passed. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI dependency install | PASS | npm ci installed 158 packages; 2 moderate audit advisories and an esbuild pending-script warning remain recorded. |
| GUI tests | PASS | The first concurrent invocation was invalidated by npm ci replacing node_modules; the required sequential rerun passed 3 files and 17 tests. |
| GUI production build | PASS | The first concurrent invocation was invalidated by npm ci replacing node_modules; the sequential TypeScript/Vite build passed. |
| Tauri Rust host | PASS | cargo check passed with the Windows MSVC toolchain. |
| Current-source sidecar JSONL smoke | PASS | list_jobs returned ok=true with jobs=[] and exit code 0. |
| Current-source sidecar/package rebuild | BLOCKED | The legacy PyInstaller launcher references missing Python 3.11; the current target-triple binary is an older artifact dated 2026-09-08. |
| Current-source target-triple sidecar, NSIS/MSI and packaged GUI matrix | BLOCKED | No fresh current-source package was available; old binaries were not reused as evidence. |
| Clean-user, Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | Requires a fresh current-source release package and a release audit workflow. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation and would mutate dependency state; npm audit fix was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Error and blocking analysis

- The initial GUI test/build failure was a validation orchestration error: npm ci was running concurrently and temporarily removed/replaced node_modules. After npm ci completed, the GUI test and build were rerun sequentially and passed; this is not a product failure.
- The previous MCP WinError 32 and TOML Windows-path failures remain historical only; the latest Linux fix and current Windows rerun pass both the focused and full Python checks.
- Packaging remains independently blocked because the configured legacy PyInstaller entrypoint targets an absent Python 3.11 installation. Direct current-source sidecar success does not establish packaged success.

### Linux follow-up required

1. Provide a reproducible supported Windows current-source sidecar build path or document the approved build environment and command.
2. Rebuild the target-triple sidecar and NSIS/MSI package from this source, record fresh hashes, and rerun packaged sidecar smoke.
3. Execute packaged GUI interactive, clean-user, cancellation/reconnection and Windows path/permission checks after a fresh package exists.
4. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
5. Review the npm moderate advisories separately; do not apply automatic dependency remediation during this validation.

### Overall status

The latest Windows status for the Linux working tree is WINDOWS_VERIFICATION_PENDING: current source-level, full Python, GUI source, Tauri and direct sidecar checks are WINDOWS_PASS; current-source packaging and packaged GUI/release validation remain WINDOWS_BLOCKED or NOT RUN.

## Validation run: 2026-09-09 (current Windows packaging source)

### Scope and source state

- Validation source: current WSL working tree at HEAD 7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab, including the uncommitted sidecar spec, frozen entry point, worker dispatch changes and regression tests.
- The source was synchronized from WSL to E: with the filtered timestamp-aware one-way mirror; key source and document hashes matched.
- No business code was modified during this Windows validation. Build outputs and staging files remained in the disposable E: workspace.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | uv sync --locked --extra runtime --extra dev and uv lock --locked completed successfully; 95 packages resolved and 91 checked. |
| Python formatting and lint | PASS | Ruff format check and Ruff lint passed; 76 files were already formatted. |
| Python full test suite | PASS | 147 passed, 3 deselected in 20.83 seconds. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI tests | PASS | 3 files, 17 tests passed. |
| GUI production build | PASS | TypeScript/Vite build passed. |
| Tauri Rust host | PASS | cargo check passed with the Windows MSVC toolchain. |
| Current-source PyInstaller build | PASS | Project command uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec completed successfully with PyInstaller 6.22.2 and Python 3.12.13. |
| Frozen sidecar JSONL smoke | PASS | The new dist/babelcodex-service.exe returned ok=true with jobs=[] and exit code 0 for list_jobs. |
| Frozen worker dispatch negative-path smoke | PASS | --worker-request for a missing request file returned structured WORKER_REQUEST_INVALID and exit code 2, as expected. |
| Tauri target-triple sidecar smoke | PASS | The freshly copied x86_64-pc-windows-msvc sidecar returned ok=true with jobs=[] and exit code 0. |
| Current GUI/sidecar staging bundle audit | PASS | scripts/check_gui_bundle.py passed and generated a SHA-256 manifest; the current GUI executable and sidecar were audited together. |
| Current-source NSIS bundle | PASS | Tauri generated BabelCodex_0.1.0_x64-setup.exe; size 195,757,696 bytes; SHA-256 D653629B7F40AAA30311107A17956E12976DF39B42BEF9F5391E859B489DB28D. |
| Current-source MSI bundle | FAIL | npm.cmd --prefix gui run tauri -- build --bundles nsis,msi exited 1 at the MSI stage with Couldn't find a .ico icon. The existing MSI file has an older timestamp and was not treated as current evidence. |
| Packaged GUI interactive and clean-user matrix | NOT RUN | No installer was installed or interactively executed in this validation; source GUI tests, release build and non-executing bundle audit were run instead. |
| Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | The release-security workflow was not entered. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation and would mutate dependency state; npm audit fix was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Failure and blocking analysis

- The current-source sidecar build itself passed, including frozen JSONL and worker-dispatch checks. PyInstaller emitted warnings for optional/missing hidden imports during analysis, but the executable was produced and the defined smoke checks passed.
- The NSIS bundle was generated from the current GUI and freshly built target-triple sidecar. The combined NSIS/MSI command nevertheless failed in the MSI phase because Tauri could not find a .ico icon. This is a Windows packaging/configuration failure and blocks current MSI acceptance; it does not invalidate the independently generated NSIS artifact.
- The MSI file present in the output directory has an older timestamp and was not used as evidence. No packaged GUI or clean-user claim is made from that stale file.

### Linux follow-up required

1. Provide a valid Windows .ico resource and update the project packaging configuration or build inputs as appropriate; do not treat the old MSI as current.
2. Re-run the current-source MSI build and record a fresh MSI hash after the icon issue is resolved.
3. Execute current NSIS/MSI packaged sidecar smoke, packaged GUI interaction, clean-user, cancellation/reconnection and Windows path/permission checks.
4. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
5. Review the npm moderate advisories separately; do not apply automatic dependency remediation during this validation.

### Overall status

The latest Windows status for the Linux working tree is WINDOWS_VERIFICATION_PENDING: current source-level, full Python, GUI source, Tauri, frozen sidecar, target-triple sidecar and NSIS checks are WINDOWS_PASS; current MSI packaging is WINDOWS_FAIL due to the missing .ico icon, while packaged GUI/release checks remain NOT RUN.

## Validation run: 2026-09-09 (latest current Linux working tree)

### Scope and source state

- Validation source: the current WSL working tree at HEAD `7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab`, including the uncommitted Windows sidecar spec, frozen entry point, icon asset/configuration change, worker dispatch changes and regression tests.
- The source was synchronized one-way from WSL to `E:\Shiraishi\VSCode Workspace\Codex_Translator` with filtered exclusions for `.git`, environments, dependencies, caches, state, logs and build artifacts. Key source, spec, test and document hashes matched after synchronization.
- No business code or project configuration was changed during this validation. Windows build outputs and staging files remained in the disposable E: workspace.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | `uv sync --locked --extra runtime --extra dev` and `uv lock --locked` completed successfully; 95 packages resolved and 91 checked. |
| Python formatting and lint | PASS | Ruff format check and Ruff lint passed; 76 files were already formatted. |
| Python full test suite | PASS | 147 passed, 3 deselected in 20.83 seconds. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI tests | PASS | 3 files, 17 tests passed. |
| GUI production build | PASS | TypeScript/Vite build passed. |
| Tauri Rust host | PASS | `cargo check` passed with the Windows MSVC toolchain. |
| Current-source PyInstaller build | PASS | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` completed successfully with PyInstaller 6.22.2 and Python 3.12.13. |
| Frozen sidecar JSONL smoke | PASS | The new `dist/babelcodex-service.exe` returned `ok=true` with `jobs=[]` and exit code 0 for `list_jobs`. |
| Frozen worker dispatch negative-path smoke | PASS | A missing worker request returned structured `WORKER_REQUEST_INVALID` and exit code 2, as expected. |
| Tauri target-triple sidecar smoke | PASS | The freshly copied `x86_64-pc-windows-msvc` sidecar returned `ok=true` with `jobs=[]` and exit code 0. |
| Current GUI/sidecar staging bundle audit | PASS | `scripts/check_gui_bundle.py` passed and generated a SHA-256 manifest for the current GUI executable and sidecar. |
| Current-source NSIS bundle | PASS | Tauri generated `BabelCodex_0.1.0_x64-setup.exe`; size 195,757,696 bytes; SHA-256 `D653629B7F40AAA30311107A17956E12976DF39B42BEF9F5391E859B489DB28D`. |
| Current-source MSI bundle | PASS | The first attempt exposed a stale E: copy of `tauri.conf.json` and exited with `Couldn't find a .ico icon`; after one-way resynchronization, the current MSI build completed successfully. Fresh artifact size 195,715,072 bytes; SHA-256 `4E885B1E35A3C566D9257A701608BA383B2E5577C40A30A6E93A1578B02F57A4`. |
| Packaged GUI interactive and clean-user matrix | NOT RUN | No installer was installed or interactively executed; source GUI tests, release build and non-executing bundle audit were run instead. |
| Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | The release-security workflow was not entered. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation and would mutate dependency state; `npm audit fix` was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Failure and blocking analysis

- The current-source sidecar build passed, including frozen JSONL and worker-dispatch checks. PyInstaller emitted warnings for optional/missing hidden imports during analysis, but the executable was produced and the defined smoke checks passed.
- The NSIS bundle was generated from the current GUI and freshly built target-triple sidecar. The first MSI attempt failed because the E: validation copy still had the older `tauri.conf.json` containing only `icon.png`; the synchronized WSL copy contains `icon.ico` and `icon.png`, while the ICO file itself was present on E:.
- After resynchronizing the tracked Tauri configuration from WSL and verifying matching hashes, the MSI build completed successfully. The initial error was therefore a synchronization-state issue, not a confirmed current-source MSI bundler defect.
- The stale MSI from before the corrected synchronization was not used as evidence. No packaged GUI or clean-user claim is made from an installer merely being generated.

### Linux follow-up required

1. Keep the WSL-to-E synchronization check for tracked packaging configuration and verify hashes before each package run.
2. Execute current NSIS/MSI packaged sidecar smoke, packaged GUI interaction, clean-user, cancellation/reconnection and Windows path/permission checks.
3. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
4. Review the npm moderate advisories separately; do not apply automatic dependency remediation during this validation.

### Overall status

The latest Windows status for the Linux working tree is `WINDOWS_VERIFICATION_PENDING`: current source-level, full Python, GUI source, Tauri, frozen sidecar, target-triple sidecar, bundle audit, NSIS and MSI checks are `WINDOWS_PASS`; packaged GUI interaction and release-security checks remain `NOT RUN`.

## Validation run: 2026-09-09 (repeat, latest current Linux working tree)

### Scope and source state

- Validation source: the current WSL working tree at HEAD `7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab`, including its uncommitted sidecar packaging, icon/configuration, worker and test changes.
- The current source was synchronized one-way from WSL to `E:\Shiraishi\VSCode Workspace\Codex_Translator` with the documented exclusions for `.git`, environments, dependencies, caches, state, logs and build artifacts. Key source, Tauri configuration, icon, spec and test hashes matched after synchronization.
- No business code or project configuration was modified during validation. All Windows build output and staging files remained on E:.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | `uv sync --locked --extra runtime --extra dev` and `uv lock --locked` completed; 95 packages resolved and 91 checked. |
| Python formatting and lint | PASS | `uv run ruff format --check .` reported 77 files already formatted; `uv run ruff check .` passed. |
| Python full test suite, first invocation | FAIL | `uv run pytest -q --tb=short` had 1 failure and 146 passes; `tests/test_mcp.py::test_validate_rejects_artifact_outside_output_allowlist` hit `PermissionError: [Errno 13] Permission denied` while reading a Windows temporary state JSON file. |
| Focused reproduction of failed test | PASS | The failed test passed when run alone: `1 passed in 2.35s`. |
| Python full test suite, sequential rerun | PASS | The immediate rerun passed: 147 passed, 3 deselected in 16.45 seconds. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI dependency install | PASS | `npm.cmd --prefix gui ci` installed 158 packages; npm reported 2 moderate advisories and an esbuild pending-script warning. |
| GUI tests | PASS | 3 files, 17 tests passed. |
| GUI production build | PASS | TypeScript/Vite build passed. |
| Tauri Rust host | PASS | `cargo check --manifest-path gui/src-tauri/Cargo.toml` passed with the Windows MSVC toolchain. |
| Current-source PyInstaller build | PASS | The documented PyInstaller command completed successfully with PyInstaller 6.22.2 and Python 3.12.13. |
| Frozen sidecar JSONL smoke | PASS | New `dist/babelcodex-service.exe` returned `ok=true`, `jobs=[]`, exit code 0 for `list_jobs`; SHA-256 `49CA895091F0DE862903E4C0C3295B28D2C7CECACCC6A59A6A58C5CB02E2A827`. |
| Frozen worker dispatch negative-path smoke | PASS | Missing worker request returned structured `WORKER_REQUEST_INVALID` and exit code 2. |
| Tauri target-triple sidecar smoke | PASS | Fresh `x86_64-pc-windows-msvc` sidecar returned `ok=true`, `jobs=[]`, exit code 0; its hash matched the frozen executable. |
| Current GUI/sidecar staging bundle audit | PASS | After correcting the temporary staging layout to match `scripts/check_gui_bundle.py`, the audit passed and generated a SHA-256 manifest. |
| Current-source NSIS bundle | PASS | Generated successfully; size 195,746,208 bytes; SHA-256 `4138276E5FF18532F8EE9BB3B306192E63EC09E6B59EE619311D56ED5CF010C7`. |
| Current-source MSI bundle | PASS | Generated successfully after the synchronized `.ico` configuration; size 195,715,072 bytes; SHA-256 `1AA47BD6DDDFAC6E1391F5CC9821C03B9A39A850DFFF2DD6ADF3A85C9E47B73D`. |
| Packaged GUI executable launch smoke | PASS | Current release `babelcodex-gui.exe` stayed running for 8 seconds and closed cleanly; no installer was installed. |
| Packaged GUI interactive and clean-user matrix | NOT RUN | The current automation session did not expose a usable native GUI window for interaction, and no MSI/NSIS installer was installed. |
| Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | The release-security workflow was not entered. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation; `npm audit fix` was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Failure and blocking analysis

- The first Python full-suite invocation exposed a transient Windows filesystem/fixture issue: a test-created state JSON was denied during immediate readback. The focused test passed independently and the sequential full-suite rerun passed, so this is recorded as an intermittent Windows test-infrastructure/file-lock observation rather than a confirmed product-code failure. No code change was made.
- The first bundle-audit invocation used an incorrect disposable staging layout and returned a missing-sidecar error. Reading the existing audit script showed that the target-triple sidecar belongs at the staging root; the corrected invocation passed. This was a validation-command error, not a product failure.
- PyInstaller still emitted warnings for optional hidden imports, but the executable built and its defined positive and negative-path smoke checks passed.
- NSIS and MSI both generated successfully from the synchronized current source. The previous stale-configuration MSI incident remains historical; this run verified matching WSL/E configuration and icon hashes before packaging.
- No current `BLOCKED` item was encountered. Interactive GUI and release-security checks are explicitly `NOT RUN` with reasons above.

### Linux follow-up required

1. Keep the WSL-to-E source/configuration hash preflight before each Windows package run.
2. Investigate and, if practical, harden the intermittent Windows temporary-file permission failure in `tests/test_mcp.py::test_validate_rejects_artifact_outside_output_allowlist`; do not treat the current rerun pass as proof that the flake is eliminated.
3. Run installed NSIS/MSI sidecar smoke, GUI interaction, clean-user, cancellation/reconnection and Windows path/permission checks in a suitable disposable Windows user/environment.
4. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
5. Review the npm moderate advisories separately; do not apply automatic dependency remediation during this validation.

### Linux follow-up completed (2026-09-09) — transient state-read hardening

Linux-side follow-up for follow-up item 2 above:

- Root cause: `StateStore.save()` swaps state files atomically via `os.replace` (with bounded write-side backoff), but the three read paths (`load`, `load_by_job_id`, `list_jobs`) performed bare `read_text`. On Windows, a job-status poll (`service.get_job` → `load_by_job_id`) racing a concurrent terminal-status save can transiently fail with `PermissionError: [Errno 13]`, matching the observed flake in `tests/test_mcp.py::test_validate_rejects_artifact_outside_output_allowlist`.
- Fix: added `_read_state_json()` in `src/codex_babeldoc/core/state.py`; all state reads now retry transient `PermissionError` with the same bounded exponential backoff as the write path (5 attempts, 0.02 s base). Constants were unified as `STATE_TRANSIENT_RETRIES` / `STATE_TRANSIENT_BACKOFF_SECONDS`. Persistent `PermissionError` is still raised after the bounded budget.
- Regression tests added in `tests/test_state.py`: deterministic transient-retry recovery, persistent-failure raise, and bounded attempt count.
- Linux verification: `uv run pytest -q` reports `150 passed, 3 deselected`; Ruff lint/format and compileall pass.
- Status: this hardening is `LINUX_VERIFIED` and `WINDOWS_VERIFICATION_PENDING`. The Windows intermittent `FAIL` observation above remains recorded; it may only be retired after a Windows full-suite rerun on a working tree containing this fix. Rerun-pass alone was never treated as proof that the flake was eliminated.

### Overall status

At the time of this validation record, the Windows status was `WINDOWS_VERIFICATION_PENDING`: the read-side transient `PermissionError` hardening was `LINUX_VERIFIED` and required a Windows rerun before it could be marked `WINDOWS_PASS`. The subsequent rerun is recorded below and retires that pending condition.

## Validation run: 2026-09-09 (latest state-read hardening)

### Scope and source state

- Validation source: the current WSL working tree at HEAD `7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab`, now including the Linux-side state-read retry hardening in `src/codex_babeldoc/core/state.py` and its regression tests in `tests/test_state.py`.
- The source was synchronized one-way from WSL to `E:\Shiraishi\VSCode Workspace\Codex_Translator` with the documented exclusions for `.git`, environments, dependencies, caches, state, logs and build artifacts. Key state, test, sidecar spec, Tauri configuration, icon and document hashes matched.
- No business code or project configuration was modified during Windows validation. All build output and staging files remained on E:.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | `uv sync --locked --extra runtime --extra dev` and `uv lock --locked` completed; 95 packages resolved and 91 checked. |
| Python formatting and lint | PASS | Ruff format check reported 77 files already formatted; Ruff lint passed. |
| Python full test suite with state-read hardening | PASS | `uv run pytest -q --tb=short`: 150 passed, 3 deselected in 27.31 seconds. The prior transient Windows `PermissionError` test observation did not recur. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI dependency install | PASS | `npm.cmd --prefix gui ci` installed 158 packages; 2 moderate advisories and an esbuild pending-script warning remain. |
| GUI tests | PASS | 3 files, 17 tests passed. |
| GUI production build | PASS | TypeScript/Vite build passed. |
| Tauri Rust host | PASS | `cargo check --manifest-path gui/src-tauri/Cargo.toml` passed with the Windows MSVC toolchain. |
| Current-source PyInstaller build including state hardening | PASS | The documented PyInstaller command completed successfully with PyInstaller 6.22.2 and Python 3.12.13. |
| Frozen sidecar JSONL smoke | PASS | New frozen sidecar returned `ok=true`, `jobs=[]`, exit code 0 for `list_jobs`; SHA-256 `FF3555AE6958898BCBC985F869EFAB639B9BE2D07ABE1D05393B345775E960F8`. |
| Frozen worker dispatch negative-path smoke | PASS | Missing worker request returned structured `WORKER_REQUEST_INVALID` and exit code 2. |
| Tauri target-triple sidecar smoke | PASS | Fresh target-triple sidecar returned `ok=true`, `jobs=[]`, exit code 0; its hash matched the frozen sidecar. |
| Current GUI/sidecar staging bundle audit | PASS | `scripts/check_gui_bundle.py` passed for the newly built GUI and sidecar. |
| Current-source NSIS bundle | PASS | Generated successfully; size 195,746,324 bytes; SHA-256 `8D022FEE8E737FB4EBE148987030409DC6A57738690A3EBFE9D32BA22299BF39`. |
| Current-source MSI bundle | PASS | Generated successfully; size 195,715,072 bytes; SHA-256 `D1F56078EA680D496D39B5699B03BF1B61A3AA13D757360D861333A5FE0B7922`. |
| Packaged GUI executable launch smoke | PASS | Current release GUI executable stayed running for 8 seconds and closed cleanly; no installer was installed. |
| Packaged GUI interactive and clean-user matrix | NOT RUN | No MSI/NSIS installer was installed and the current automation session did not expose a usable native GUI window for interaction. |
| Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | The release-security workflow was not entered. |
| Live Codex/PDF integration | NOT RUN | Not authorized; ordinary tests must not consume paid or ChatGPT-plan usage. |
| npm advisory remediation | NOT RUN | Not part of validation; `npm audit fix` was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a target Linux execution, not a Windows validation item. |

### Failure and blocking analysis

- The Linux-side `_read_state_json()` bounded retry hardening was present in the synchronized Windows source. The full suite passed with 150 tests, including the new state regression tests, and the previous transient read-side `PermissionError` did not recur.
- PyInstaller continued to report warnings for optional hidden imports, but the frozen executable built and passed both positive and negative-path smoke checks. These warnings are not treated as a failure without a failing runtime check.
- NSIS and MSI were rebuilt after the sidecar rebuild, so their evidence corresponds to the latest synchronized WSL state rather than the previous round’s artifacts.
- No current `FAIL` or `BLOCKED` item was encountered. Interactive GUI, clean-user and release-security checks remain explicitly `NOT RUN`.

### Linux follow-up required

1. Keep the WSL-to-E source/configuration hash preflight before each Windows package run.
2. Run installed NSIS/MSI sidecar smoke, GUI interaction, clean-user, cancellation/reconnection and Windows path/permission checks in a suitable disposable Windows user/environment.
3. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
4. Review the npm moderate advisories separately; do not apply automatic dependency remediation during this validation.

### Overall status

The latest Windows status for the Linux working tree is `WINDOWS_VERIFICATION_PENDING`: the state-read hardening, dependency, Python, GUI source, Tauri, frozen sidecar, target-triple sidecar, bundle audit, release GUI launch, NSIS and MSI checks are `WINDOWS_PASS`; interactive GUI/clean-user and release-security checks remain `NOT RUN`.

## Validation run: 2026-09-09 (repeat confirmation, no source delta)

### Scope and source state

- Validation source: the same current WSL working tree at HEAD `7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab`; no source changes were detected after the state-read hardening recorded above.
- The current WSL tree was synchronized one-way to `E:\Shiraishi\VSCode Workspace\Codex_Translator`, and hashes for `state.py`, `test_state.py`, the sidecar spec, Tauri configuration, icon and validation documents matched.
- No business code or project configuration was modified. Windows build output remained on E:.

### Results

| Validation item | Status | Evidence / reason |
|---|---|---|
| Dependency synchronization and lock consistency | PASS | `uv sync --locked --extra runtime --extra dev` and `uv lock --locked` completed; 95 packages resolved and 91 checked. |
| Python formatting and lint | PASS | Ruff format check reported 77 files already formatted; Ruff lint passed. |
| Python full test suite | PASS | `uv run pytest -q --tb=short`: 150 passed, 3 deselected in 27.31 seconds. |
| Runtime doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0 and active ChatGPT authentication detected. |
| GUI dependency install | PASS | `npm.cmd --prefix gui ci` installed 158 packages; 2 moderate advisories and an esbuild pending-script warning remain. |
| GUI tests and production build | PASS | 3 files, 17 tests passed; TypeScript/Vite build passed. |
| Tauri Rust host | PASS | `cargo check --manifest-path gui/src-tauri/Cargo.toml` passed. |
| Current-source PyInstaller and frozen sidecar checks | PASS | Rebuilt sidecar passed JSONL `list_jobs`, structured invalid-worker-request exit 2, and target-triple smoke; frozen/target SHA-256 `FF3555AE6958898BCBC985F869EFAB639B9BE2D07ABE1D05393B345775E960F8`. |
| Current GUI/sidecar bundle audit | PASS | `scripts/check_gui_bundle.py` passed for the latest GUI and sidecar. |
| Current-source NSIS bundle | PASS | Size 195,746,324 bytes; SHA-256 `8D022FEE8E737FB4EBE148987030409DC6A57738690A3EBFE9D32BA22299BF39`. |
| Current-source MSI bundle | PASS | Size 195,715,072 bytes; SHA-256 `D1F56078EA680D496D39B5699B03BF1B61A3AA13D757360D861333A5FE0B7922`. |
| Packaged GUI executable launch smoke | PASS | Release GUI stayed running for 8 seconds and closed cleanly; no installer was installed. |
| Packaged GUI interactive and clean-user matrix | NOT RUN | No installer was installed and native GUI interaction was not available in the current validation session. |
| Defender/SmartScreen, signing/SBOM and release audit | NOT RUN | Release-security workflow not entered. |
| Live Codex/PDF integration | NOT RUN | Not authorized. |
| npm advisory remediation | NOT RUN | `npm audit fix` was not run. |
| Target Linux machine smoke | NOT APPLICABLE | Not a Windows validation item. |

### Failure and blocking analysis

- No failure or blocking condition occurred in this repeat confirmation. The previous Windows state-read `PermissionError` did not recur with the hardening present.
- PyInstaller optional hidden-import warnings remained non-fatal; the generated sidecar passed its defined runtime checks.
- Interactive GUI, clean-user and release-security checks remain `NOT RUN`, not `PASS`.

### Linux follow-up required

1. Run installed NSIS/MSI sidecar smoke, GUI interaction, clean-user, cancellation/reconnection and Windows path/permission checks in a suitable disposable Windows user/environment.
2. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
3. Review npm moderate advisories separately; do not apply automatic dependency remediation during validation.

### Overall status

The latest Windows status remains `WINDOWS_VERIFICATION_PENDING`: all executed source, test, sidecar and package checks are `WINDOWS_PASS`; interactive GUI/clean-user and release-security checks remain `NOT RUN`.

## Validation run: 2026-09-09 (current-source Windows revalidation, 21:02-21:24 CST)

### Validation environment and source state

- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; WebView2 `152.0.4191.66`.
- `uv 0.12.10`; project-managed Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; Visual Studio Build Tools `17.14.39`.
- WSL source `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `7ba4ddf82cfffb9c2bd81ad8a39f2750556870ab`; uncommitted changes were included.
- One-way filtered robocopy to `E:\Shiraishi\VSCode Workspace\Codex_Translator`, excluding `.git`, environments, `node_modules`, Rust target, build/dist, caches, state/logs and user input/output. Exit `3`, zero failed files; 18 key hashes matched; E: local data was preserved.
- `doctor` found active ChatGPT authentication, but real Codex/PDF translation was not authorized and was not run.

### Validation checklist

| Item | Classification | Command | Working directory | Status | Result |
|---|---|---|---|---|---|
| Dependency and lock consistency | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | `E:\Shiraishi\VSCode Workspace\Codex_Translator` | PASS | 95 resolved, 91 checked; exit 0. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | same | PASS | 77 formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | same | PASS | Exit 0. |
| Python non-integration tests | Required | `uv run pytest -q --tb=short` | same | PASS | `150 passed, 3 deselected` in 22.26s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | same | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0, ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | same | PASS | 158 packages; 2 moderate advisories and esbuild pending-script warning reported. |
| GUI tests | Required | `npm.cmd --prefix gui test -- --run` | same | PASS | 3 files, 17 tests. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | same | PASS | TypeScript/Vite passed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | same | PASS | Windows native cargo check passed. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | same | PASS | PyInstaller 6.22.2 produced `dist/babelcodex-service.exe`; warnings non-fatal. |
| Frozen sidecar JSONL smoke | Required | frozen exe with `list_jobs` and `shutdown` requests | same | PASS | `ok=true`, `jobs=[]`, exit 0. |
| Frozen worker invalid request | Required | frozen exe `--worker-request build\\missing-worker-request-validation-2.json` | same | PASS | `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar smoke | Required | target-triple exe `--config config/example.toml` with JSONL requests | same | PASS | `ok=true`, `jobs=[]`, exit 0; SHA-256 `2E660B342DF856D2260BE2D9E88434F3411969535DC5DC41A6B99CB3F1F11CB8`. |
| GUI/sidecar staging bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260909-2108 --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | same | FAIL | Audit rejected normal `https://` strings in generated JS/CSS as absolute paths (`s://` matches `[A-Za-z]:[\\\\/]`). No real `E:\\...` path was found in the diagnostic. |
| Current-source NSIS bundle | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | same | PASS | 195,746,309 bytes; SHA-256 `259D35315741EF3DA4D7318C1DEF36016031524133601108EBE580E55E608FD3`; `NotSigned`. |
| Current-source MSI bundle | Required | same combined Tauri command | same | PASS | 195,715,072 bytes; SHA-256 `8307FD99E183E0B8074E1EC863B5CF3EEB12C69BAB9C839D647502624B8A3DE7`; `NotSigned`. |
| MSI administrative isolation extract | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...` with quoted paths | same | PASS | Extracted to `build\\windows-msi-extract-current-20260909-2120-quoted`. |
| MSI-extracted sidecar JSONL smoke | Required | extracted `PFiles\\BabelCodex\\babelcodex-service.exe --config config/example.toml` with `list_jobs`/`shutdown` | same | PASS | `ok=true`, `jobs=[]`, exit 0; package sidecar hash matched target-triple sidecar. |
| MSI-extracted GUI launch smoke | Applicable | start extracted `PFiles\\BabelCodex\\babelcodex-gui.exe`, wait 8s, stop validation process | same | PASS | Process remained running for 8s and was stopped after smoke. |
| Packaged GUI interactive, clean-user, cancellation/reconnection and path/permission matrix | Required | Project-defined matrix; no native GUI automation/isolated user workflow available | same | NOT RUN | Process launch is not evidence for picker, allowlist, clean profile, non-ASCII/path, cancellation or reconnection behavior. |
| Defender/SmartScreen, signing, SBOM and release audit | Required | Release-security workflow | same | NOT RUN | Development packages are unsigned; workflow was not entered. |
| Live Codex/PDF integration | Applicable | Real Codex translation fixture | same | NOT RUN | Not authorized; ordinary tests remain usage-free. |
| npm advisory remediation | Applicable | `npm audit fix` | same | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | target Linux runtime command | same | NOT APPLICABLE | Must run on a target Linux machine. |

### Errors and analysis

| Item | Key error/log path | Likely category | Blocks other checks | Follow-up |
|---|---|---|---|---|
| `check_gui_bundle.py` audit | `build\\windows-validation-staging-20260909-2108`; possible absolute path in `assets\\index-BRF5O_XD.js` and `index-Ciks3U42.css` | Test/validation script defect (over-broad absolute-path regex) | Blocks claiming this audit as PASS; does not block NSIS/MSI generation or executable smoke | Linux-side review of `scripts/check_gui_bundle.py`, add URL/absolute-path regression tests, then rerun audit. No fix was made during validation. |

The first frozen-smoke wrapper returned exit 1 because PowerShell applied `-notmatch` to an output array; the strict stringified assertion was rerun and passed. The first two MSI extraction attempts returned `1639` because the validation command did not preserve the quoted `TARGETDIR` argument; the corrected quoted invocation passed. These are validation-command errors, not product failures.

### Linux follow-up required

1. Fix or narrow the bundle-audit absolute-path detection in Linux development, add a regression test for `https://`/`http://`, and rerun the current bundle audit; until then this item remains `WINDOWS_FAIL` and overall status remains `WINDOWS_VERIFICATION_PENDING`.
2. Run installed NSIS/MSI GUI interaction, clean-user, cancellation/reconnection and Windows path/permission checks in a suitable disposable Windows user/environment.
3. Complete Defender/SmartScreen, signing, SBOM and release artifact audit when the release workflow is entered.
4. Review the two npm moderate advisories separately; do not apply automatic remediation as part of this validation.
5. Run live Codex/PDF integration only as an explicitly authorized usage-bearing integration task.

### Linux follow-up completed (2026-09-09) — bundle-audit URL false positive

Linux-side follow-up for follow-up item 1 above:

- Root cause: `ABSOLUTE_PATH` in `scripts/check_gui_bundle.py` used a bare `[A-Za-z]:[\\/]` pattern; inside ordinary strings such as `https://tauri.app`, the substring `s://` matched it, so generated JS/CSS assets were flagged as "possible development-machine absolute path" even though no real drive path was present.
- Fix: added `contains_development_machine_absolute_path()`, which strips `scheme://authority` prefixes (not URL paths) before matching, so `https://…` no longer trips the drive-letter pattern while `file:///home/...` and `file:///C:/...` remain detectable; a negative lookbehind (`(?<![A-Za-z0-9])`) adds defense-in-depth against scheme-like false matches.
- Regression tests added in `tests/test_check_gui_bundle.py` (7 tests): https/http/wss URLs pass, Windows drive paths and Unix `/home/`/`/tmp/` paths are flagged, `file://` URLs with real paths are still flagged, missing-sidecar and forbidden `.env` behavior preserved.
- Linux audit rerun: a staging bundle built from the actual Vite output (`assets/index-BRF5O_XD.js`, `assets/index-Ciks3U42.css`, which contain `https://` strings and previously triggered the Windows FAIL) now passes `scripts/check_gui_bundle.py` on Linux.
- Linux verification: `uv run pytest -q` reports `157 passed, 3 deselected`; Ruff lint/format and compileall pass; GUI 17 tests pass.
- Status: this fix is `LINUX_VERIFIED` and `WINDOWS_VERIFICATION_PENDING`. The audit item above remains `WINDOWS_FAIL` for this round's record; it may only move to `WINDOWS_PASS` after the bundle audit is rerun on the Windows staging bundle with this fix synchronized.

### Final review

- The E: workspace matches the intended WSL source state for all checked key files; WSL changes were included and this is not a clean-commit validation.
- Every applicable item has an explicit status. The only current `FAIL` is the bundle-audit script result; all `NOT RUN` items have reasons.
- No business code, project configuration, dependency lockfile or architecture was modified during validation. Windows outputs and staging files remain on E:.
- Latest overall state: `WINDOWS_VERIFICATION_PENDING`; executed source, test, sidecar, MSI/NSIS generation and package-level launch checks pass, while bundle audit is `WINDOWS_FAIL` and interactive/clean-user/release checks remain `NOT RUN`.

## Validation run: 2026-09-10 (latest Linux working tree, current GUI revalidation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca` (`docs: record windows validation follow-ups and plan white Vercel-style GUI redesign`).
- The working tree was dirty: the current uncommitted GUI redesign (`gui/src/App.tsx`, `gui/src/App.test.tsx`, `gui/src/jobStore.ts`, `gui/src/styles.css`), documentation updates, and a mode-only script change were included. This is a working-tree validation, not a clean-commit validation.
- One-way filtered `robocopy` synchronized WSL to `E:\Shiraishi\VSCode Workspace\Codex_Translator`; exit `3`, zero failed files. `.git`, `.venv`, `node_modules`, Rust `target`, build/dist caches, logs/state/user data and temporary files were excluded or preserved on E:. Key source/document hashes matched after synchronization (`HASH_MISMATCHES=0`).
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; project Python `3.12.13` (system Python `3.14.7` not used); Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Dependency synchronization | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | PASS | 78 files already formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `157 passed, 3 deselected` in 60.46s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex versions detected; ChatGPT login reported active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; npm reported 2 moderate advisories and an esbuild pending-script warning. |
| GUI tests | Required | `npm.cmd --prefix gui test -- --run` | FAIL | 3 files, 17 tests: 15 passed, 2 failed in `src/App.test.tsx`; duplicate `mock-job-1` rows caused multiple-element failures in cancel and details tests. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 7 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Release-compatible Rust host check passed. |
| Tauri config/icon parse | Required | JSON parse of `gui/src-tauri/tauri.conf.json` and existence check for `icons/icon.ico`, `icons/icon.png` | PASS | `productName=BabelCodex`; both configured icons exist. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh `dist/babelcodex-service.exe` built successfully. |
| Frozen sidecar JSONL | Required | Frozen exe with protocol version 1 `list_jobs`/`shutdown` requests | PASS | `ok=true`, `jobs=[]`, closing response, exit 0. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-current-gui.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Fresh copied `babelcodex-service-x86_64-pc-windows-msvc.exe` with protocol version 1 JSONL requests | PASS | `ok=true`, `jobs=[]`, exit 0; SHA-256 `8E899E6833943E1BF201313E8F3EF25BEA0F8F95C69BAB4A9709AAF679F307B668`. |
| GUI/sidecar bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260910-current-gui --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | PASS | Current generated JS/CSS and fresh target sidecar passed; manifest written. |
| Current-source NSIS/MSI | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 195,748,979 bytes, SHA-256 `CB6476F09664D5B6F8AD4E188FD48E733B069FA13D0D65A006768353AB600708`; MSI 195,710,976 bytes, SHA-256 `AF0F910308C1BC412484417FF6EFD929C1EBA49040FEC0DFDD76812C139552E8`. |
| Packaged GUI process smoke | Applicable | Start current `gui\\src-tauri\\target\\release\\babelcodex-gui.exe`, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| MSI administrative extraction | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...` | PASS | Exit 0; extracted GUI, sidecar and MSI payload. |
| MSI-extracted sidecar smoke | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with `list_jobs`/`shutdown` | PASS | `ok=true`, `jobs=[]`, exit 0; package sidecar SHA-256 matched fresh target sidecar. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| Packaged GUI interaction/path matrix | Required | Installed/portable GUI picker, allowlist, cancellation, reconnection, clean-user and path/permission matrix | NOT RUN | No native desktop interaction and isolated-user acceptance evidence in this run; process launch is not a substitute. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Release-security workflow | NOT RUN | Development artifacts are unsigned; release workflow not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

| Item | Evidence | Category | Blocks | Linux follow-up |
|---|---|---|---|---|
| GUI full test suite | React duplicate-key warning for `mock-job-1`; cancel and details tests found multiple matching rows; 2/17 failed | Project code / mock event reconciliation | GUI automated acceptance only; independent Python/build/package checks continued | Fix the shared mock transport/store reconciliation so a `job_created` event cannot duplicate a job already returned by `list_jobs`; add deterministic regression coverage and rerun Linux and Windows GUI tests. |

The first frozen JSONL probe omitted the required `protocol_version` field and correctly returned `CONFIG_INVALID`; it was rerun with the repository-defined protocol and passed. An initial disposable staging command used the wrong sidecar layout and failed the audit with “missing target-triple sidecar”; the staging directory was rebuilt using the documented root layout and the audit passed. These were validation-command errors, not product failures.

### Linux follow-up required

1. Resolve the GUI duplicate-job reconciliation failure in Linux source, add/retain a regression test, and rerun the full GUI suite on Linux and Windows.
2. Run installed/portable GUI interaction, clean-user, non-ASCII/path-space/path-permission, cancellation/reconnection and window-close checks in a suitable disposable Windows environment.
3. Complete Defender/SmartScreen, signing, SBOM and formal release artifact audit when the release workflow is entered.
4. Run live Codex/PDF integration only as a separately authorized usage-bearing task.

### Final review

- The E: workspace was synchronized from the intended WSL working tree; current GUI/document changes were included, and no Windows changes were synchronized back as source.
- Every applicable check has an explicit status. The only product-related `FAIL` is the GUI test failure; the interaction/security/integration items are explicitly `NOT RUN` and the Linux target smoke is `NOT APPLICABLE`.
- No business code, architecture, dependency lockfile or configuration was modified during this validation. Windows build, package, extraction and staging outputs remain disposable artifacts on E:.
- Overall status: `WINDOWS_VERIFICATION_PENDING`.

## Validation run: 2026-09-10 (latest Linux working tree, GUI reconciliation revalidation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca`.
- The working tree remained dirty and included the current uncommitted GUI reconciliation changes (`gui/src/App.tsx`, `gui/src/App.test.tsx`, `gui/src/jobStore.ts`, `gui/src/jobStore.test.ts`, `gui/src/styles.css`), documentation changes and the mode-only script change. This is a working-tree validation, not a clean-commit validation.
- One-way filtered `robocopy` to `E:\Shiraishi\VSCode Workspace\Codex_Translator` completed with exit `3` and zero failed files; dependencies, `.git`, caches, build/dist outputs, state, logs and user data were excluded or preserved on E:. Key source/document hashes matched (`HASH_MISMATCHES=0`).
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; project Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | PASS | 78 files already formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `157 passed, 3 deselected` in 51.35s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Project Python/BabelDOC/Codex versions detected; ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; npm reported 2 moderate advisories and an esbuild pending-script warning. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 3 files, 18 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 8 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Windows-native Cargo check passed. |
| Tauri config/icon parse | Required | JSON parse of `gui/src-tauri/tauri.conf.json` and configured icon existence checks | PASS | `productName=BabelCodex`; `icon.ico` and `icon.png` exist. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh Windows frozen sidecar built successfully. |
| Frozen sidecar JSONL | Required | Frozen exe with protocol version 1 `list_jobs`/`shutdown` requests | PASS | `ok=true`, `jobs=[]`, closing response, exit 0. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260910-rerun.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Fresh target-triple exe with protocol version 1 JSONL requests | PASS | `ok=true`, `jobs=[]`, exit 0; SHA-256 `CDE9A9DBDD4F47671EBE576BB2DCBED5DAF19E88615E56AC344D8A6CC7F0956A`. |
| GUI/sidecar bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260910-latest --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | PASS | Current JS/CSS and fresh target sidecar passed; manifest written. |
| Current-source NSIS/MSI | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 195,747,786 bytes, SHA-256 `14975F49B62A070D97B1649460BCD87955559541209BD259EFDD8F64C9A9AC27`; MSI 195,710,976 bytes, SHA-256 `C8CD3C61AF7E97890B97B7FD17C0D000B50BC34318B5D1E0B6D5BE315D905275`. |
| Packaged GUI process smoke | Applicable | Start current release GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| MSI administrative extraction | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...` | PASS | Exit 0; extracted GUI and sidecar payloads. |
| MSI-extracted sidecar smoke | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with `list_jobs`/`shutdown` | PASS | `ok=true`, `jobs=[]`, exit 0; package sidecar hash matched target-triple sidecar. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| Packaged GUI interaction/path matrix | Required | Installed/portable GUI picker, allowlist, cancellation, reconnection, clean-user and path/permission matrix | NOT RUN | No native desktop interaction or isolated-user acceptance evidence was available; process launch is not a substitute. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Release-security workflow | NOT RUN | Development artifacts are unsigned; release workflow not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

- No product `FAIL` or `BLOCKED` result occurred in this revalidation. The previous GUI duplicate `mock-job-1` failure was not reproduced after the synchronized Linux working-tree reconciliation changes; the full suite passed 18/18.
- npm still reported two moderate advisories and an esbuild pending-script warning. These are recorded as environment/package warnings, not silently treated as a clean security result; remediation was intentionally `NOT RUN`.
- One combined PowerShell probe did not emit its target-sidecar exit marker, so the target-triple smoke was rerun as an independent command and passed. This was a validation-wrapper issue, not a product failure.

### Linux follow-up required

1. Preserve the GUI job/event reconciliation regression coverage and rerun the GUI suite after any further GUI changes.
2. Run installed/portable GUI interaction, clean-user, non-ASCII/path-space/path-permission, cancellation/reconnection and window-close checks in a suitable disposable Windows environment.
3. Complete Defender/SmartScreen, signing, SBOM and formal release artifact audit when the release workflow is entered.
4. Run live Codex/PDF integration only as a separately authorized usage-bearing task.

### Final review

- E: matched the intended current WSL source and documentation state before validation; only the three validation documents are eligible for write-back to WSL.
- Every applicable item has an explicit status. This round has no `FAIL` or `BLOCKED`; the remaining acceptance gaps are explicitly `NOT RUN`, and target Linux smoke is `NOT APPLICABLE`.
- No business code, architecture, dependency lockfile or configuration was modified during validation. Windows outputs remain disposable artifacts on E:.
- Overall status remains `WINDOWS_VERIFICATION_PENDING` because real desktop interaction, clean-user and release-security checks are still outstanding.

## Validation run: 2026-09-12 (latest Linux state, MSI revalidation)

### Validation environment and source state

- Linux source of truth: WSL Ubuntu `/home/shiraishi/VSCode Workspace/Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`). The current dirty tree contains five documentation files and eleven code/test files, including the CLI log-handler release change and its regression test. This was a working-tree validation, not a clean-commit validation; no business code was modified during this run.
- Windows disposable workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`. Existing `.venv`, `gui\node_modules`, Rust target, build/dist, state/logs and user-content directories were inspected and preserved. Filtered WSL → E: `robocopy` dry-run and actual sync each reported 68 copied files, 0 failed files, and 17 E: extras preserved; `.git`, environments, dependencies, caches, generated GUI assets, build/dist, logs, state and user-content directories were excluded.
- SHA-256 parity was confirmed for all eleven changed/untracked code/test files. Generated sidecars, GUI assets, staging directories and installer outputs remained only in E:. No Windows source changes were synchronized back to Linux.
- Toolchain: `uv 0.12.10`, project Python 3.12.13, Node.js 24.19.0, npm 11.17.0, Rust/cargo 1.98.0, PyInstaller 6.22.2, BabelDOC 0.6.4 and openai-codex 0.147.0. `doctor` confirmed configured Windows paths and authenticated Codex state; no usage-bearing live request was made.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy` with `/FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ` and documented exclusions, then SHA-256 comparison | PASS | 68 files copied, 0 failed; 11 changed/untracked code/test hashes matched; E: extras preserved. |
| Dependency synchronization and lock | Required | `uv --directory E:\Shiraishi\VSCode Workspace\Codex_Translator sync --locked --extra runtime --extra dev`; `uv --directory ... lock --check` | PASS | 95 resolved, 91 checked; lock valid. The first restricted-context uv cache initialization was retried in the approved Windows validation context and did not affect the project result. |
| Python format/lint/compile | Required | `uv --directory ... run ruff format --check .`; `ruff check .`; `python -m compileall -q src tests scripts` | PASS | 91 files formatted; Ruff and compileall passed. |
| Python test suite | Required | `uv --directory ... run pytest -q --tb=short` | PASS | `201 passed, 5 deselected` in 73.09s; CLI handler-release regression included. |
| Runtime doctor | Required | `uv --directory ... run cbpdf --config config/example.toml doctor` | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0, configured paths and ChatGPT login reported. |
| GUI dependency install | Required | `npm.cmd --prefix E:\Shiraishi\VSCode Workspace\Codex_Translator\gui ci` | PASS | 158 packages installed; npm reported 2 moderate advisories and esbuild postinstall pending approval; no remediation was attempted. |
| GUI full tests | Required | `npm.cmd --prefix ... test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI production build | Required | `npm.cmd --prefix ... run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path ...\gui\src-tauri\Cargo.toml`; parse config; check `icon.ico` and `icon.png` | PASS | Cargo passed; `productName=BabelCodex`; both required icons exist. |
| Mock PDF integration | Required | `uv --directory ... run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 233.28s; mock path only. |
| QA CLI and artifact tamper detection | Required | Temporary PDF/job; `cbpdf --config <temp-config> qa <job-id>`; delete artifact and rerun | PASS | Initial `exit 0 / qa_status=passed`; tampered run `exit 1 / qa_status=failed`. The helper emitted only the known fitz deprecation warning. |
| QA fixture temporary cleanup | Applicable | Automatic cleanup of the same temporary QA directory | PASS | Cleanup completed without the previous `WinError 32`; CLI root file handlers were released by the current source. |
| Current-source PyInstaller sidecar | Required | `uv --directory ... run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | `dist\babelcodex-service.exe` built; SHA-256 `B892AD806BD7E579BBA153C373BFFC4F1A03CFCF04D184E576B00D06827D4EB5`; 194,439,503 bytes. |
| Frozen sidecar protocol v1 | Required | JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Protocol 1, package 0.1.0, expected capabilities, preserved E: state visible, exit 0. |
| Frozen invalid-worker request | Applicable | `dist\babelcodex-service.exe --worker-request build\missing-worker-request-validation-current-rerun.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui\src-tauri\binaries\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | SHA-256 matched; handshake and shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | `check_gui_bundle.py <fresh-stage> --target x86_64-pc-windows-msvc --source-tree <root> --manifest <stage>\sha256.txt` | PASS | Current HTML/JS/CSS and both fresh sidecars passed the audit; exit 0. |
| WVQ-009 stale bundle negative audit | Required | Same audit with the 2026-09-10 sidecar | PASS | Expected exit 1: `sidecar predates newer Python sources`; stale input rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix ... run tauri -- build --bundles nsis,msi` | PASS | Release GUI SHA-256 `8B1450D6872EBC57133AA88C4BB8C62A30F78A49D8D6B074740A8A66252FA934`; NSIS `EFE0FF2D3E93FA5BF93428E62BF22DDD9FD79A699FBF7007550506AD671A448A` (195,791,175 bytes); MSI `28F5206CD54C559623863285BA6A1B2E576D0F10AA0FB225BA969DC78C4F3576` (195,751,936 bytes). |
| Release GUI process smoke | Applicable | Start `gui\src-tauri\target\release\babelcodex-gui.exe`, wait 8s, stop only the validation process | PASS | Process remained alive for 8s. |
| MSI administrative extraction, package parity and extracted smoke | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads; run extracted sidecar v1 handshake and GUI process smoke | PASS | Exit 0; verbose log and 2 payloads produced. Extracted sidecar SHA-256 `B892AD806BD7E579BBA153C373BFFC4F1A03CFCF04D184E576B00D06827D4EB5` matched fresh sidecar; extracted sidecar handshake/shutdown exit 0; extracted GUI remained alive for 8s. |
| Packaged stale-GUI error observation | Required | Launch stale-sidecar GUI variant and observe native connection error | BLOCKED | `sky.list_apps()` failed with `Trusted RPC service is not configured: sky`; no native UI action was performed. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, cancellation, reconnection and permissions | BLOCKED | Same unavailable native Windows GUI automation prerequisite. |
| Clean-user install/restart/recovery | Applicable | Fresh user profile, install/portable launch, sidecar restart and recovery | NOT RUN | Requires a real clean-user desktop session; not inferred from process smoke. |
| WVQ-007 full workdir/lock/retry/cancel/reconnect semantics | Applicable | Native Windows lifecycle and file-handle matrix | NOT RUN | The QA cleanup path now passes, but the broader lifecycle matrix remains unexecuted. |
| WVQ-005 release security audit | Applicable | Defender/SmartScreen, signing/certificate, SBOM and release checksum audit | NOT RUN | No security-setting or release-signing workflow was authorized in this validation. |
| Live Codex/PDF integration | Applicable | Authorized live translation against representative PDF | NOT RUN | No usage-bearing live request was authorized; mock integration remains scoped evidence only. |
| Dependency advisory remediation | Not required for this validation | `npm audit fix` or major-version upgrade | NOT RUN | Advisories were recorded; no dependency or architecture change was made to force a clean report. |
| Linux-only platform target | Not applicable | Linux AppImage/native Linux acceptance | NOT APPLICABLE | This round verifies the Windows E: workspace. |

### Failure, blocking and follow-up analysis

- No current project `FAIL` remains. The previous QA temporary-cleanup `WinError 32` was directly re-tested against the current CLI handler-release path and the temporary directory cleaned successfully. This clears only the QA harness cleanup path; it does not prove the full WVQ-007 lifecycle matrix.
- The first restricted-context uv invocation could not initialize the user cache (`os error 183`); the same documented commands passed in the approved Windows validation context. This is an execution-environment observation, not a project failure. The fresh PyInstaller build also emitted known optional hidden-import warnings but produced a working artifact and all defined smoke checks passed.
- The MSI administrative extraction blocker is resolved for the current package when invoked with the documented quoted `/a`, `TARGETDIR` and `/L*v` arguments. Current extraction produced a log and payload; extracted sidecar parity and extracted GUI process smoke passed.
- Native GUI checks remain `BLOCKED` because the Computer Use trusted `sky` RPC service is unavailable. Process-liveness smoke is not evidence for rendering, accessibility, stale-GUI error presentation or interactive path acceptance.
- Current status counts: `PASS 21`, `FAIL 0`, `BLOCKED 2`, `NOT RUN 5`, `NOT APPLICABLE 1`.

### Linux follow-up required

1. Provision a usable native Windows UI automation environment and run `WVQ-001` through `WVQ-004` plus the stale-GUI portion of `WVQ-009`: Chinese rendering, keyboard, DPI, NVDA, picker/allowlist, Unicode and space-containing paths, permissions, cancellation, reconnection, window close, clean user and sidecar restart.
2. Run the broader native Windows `WVQ-007` workdir/lock/retry/cancel/reconnect matrix; retain strict cleanup assertions even though the CLI QA cleanup path now passes.
3. Schedule Defender/SmartScreen, signing/SBOM/release audit and any live Codex/PDF test with explicit authorization; review npm advisories separately without changing dependencies during validation.

### Linux reconciliation after the MSI revalidation

- The MSI administrative-extraction blocker is closed with native evidence: extraction with the documented quoted `/a`, `TARGETDIR` and `/L*v` arguments returned exit 0 with a verbose log and payloads, the extracted sidecar SHA-256 exactly matched the fresh build (`B892AD80...`), the extracted sidecar v1 handshake/shutdown exited 0, and the extracted GUI process stayed alive for 8 seconds. Linux accepts this as package-parity evidence for the current MSI only; the WVQ queue items that still require native desktop work remain untouched.
- The QA fixture temporary cleanup passed for a second consecutive round with the CLI handler-release hardening, and the stale bundle negative audit again rejected the older sidecar. Status counts: `PASS 21`, `FAIL 0`, `BLOCKED 2`, `NOT RUN 5`, `NOT APPLICABLE 1`.
- Linux makes no code change this round: every remaining gap (native UI automation prerequisite, clean-user session, full `WVQ-007` lifecycle matrix, `WVQ-005` release security, live Codex/PDF) requires the Windows-native environment and cannot be advanced by Linux-only edits. All `WVQ-*` items stay `WINDOWS_VERIFICATION_PENDING`; overall status remains `WINDOWS_VERIFICATION_PENDING`.

Overall status remains `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_VERIFICATION_BLOCKING`.

## Validation run: 2026-09-12 (latest Linux CLI/QA change revalidation)

### Validation environment and source state

- Linux source of truth: WSL Ubuntu `/home/shiraishi/VSCode Workspace/Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`). The dirty tree now includes five documentation files and eleven code/test files, including the new CLI log-handler release change in `src/codex_babeldoc/cli.py`, its regression coverage in `tests/test_cli.py`, and untracked `gui/src/protocol.test.ts`. This was not a clean-commit validation; this run did not modify business code, configuration or dependencies.
- Windows disposable workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`. Existing `.venv`, `gui\node_modules`, Rust target, build/dist, state/logs and user-content directories were inspected and preserved. A filtered one-way `robocopy` sync from `\\wsl.localhost\Ubuntu\home\shiraishi\VSCode Workspace\Codex_Translator` to E: used `/FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ`; `.git`, virtual environments, dependencies, caches, generated GUI assets, build/dist, logs, state and user-content directories were excluded. Dry-run and actual sync each reported 68 copied files, 0 failed files, and 17 E: extras preserved.
- Eleven changed/untracked code/test files were compared by SHA-256 after sync; all matched. Generated GUI assets, frozen sidecar, target-triple sidecar, staging directories and installer outputs were created only in E: and were not reverse-synced.
- Toolchain: `uv 0.12.10`; project Python 3.12.13; Node.js 24.19.0; npm 11.17.0; Rust/cargo 1.98.0; PyInstaller 6.22.2; BabelDOC 0.6.4; openai-codex 0.147.0. `doctor` reported authenticated ChatGPT state; no usage-bearing live Codex request was made.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy` from the WSL source path to E: with documented exclusions, then SHA-256 comparison | PASS | 68 files copied, 0 failed; 11 changed/untracked code/test hashes matched; E: extras preserved. |
| Dependency synchronization and lock | Required | `uv --directory E:\Shiraishi\VSCode Workspace\Codex_Translator sync --locked --extra runtime --extra dev`; `uv --directory ... lock --check` | PASS | 95 resolved, 91 checked; lock valid. |
| Python format/lint/compile | Required | `uv --directory ... run ruff format --check .`; `ruff check .`; `python -m compileall -q src tests scripts` | PASS | 91 files formatted; Ruff and compileall passed. |
| Python test suite | Required | `uv --directory ... run pytest -q --tb=short` | PASS | `201 passed, 5 deselected` in 38.12s; CLI handler-release regression included. |
| Runtime doctor | Required | `uv --directory ... run cbpdf --config config/example.toml doctor` | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0, configured Windows paths and ChatGPT login reported. |
| GUI dependency install | Required | `npm.cmd --prefix E:\Shiraishi\VSCode Workspace\Codex_Translator\gui ci` | PASS | 158 packages installed; npm reported 2 moderate advisories and esbuild postinstall pending approval; no remediation was attempted. |
| GUI full tests | Required | `npm.cmd --prefix ... test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI production build | Required | `npm.cmd --prefix ... run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path ...\gui\src-tauri\Cargo.toml`; parse config; check `icon.ico` and `icon.png` | PASS | Cargo passed; `productName=BabelCodex`; both required icons exist. |
| Mock PDF integration | Required | `uv --directory ... run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 247.01s. |
| QA CLI and artifact tamper detection | Required | Temporary PDF/job; `qa <job-id>`; delete artifact and rerun | PASS | Initial `exit 0 / qa_status=passed`; tampered run `exit 1 / qa_status=failed`; one report generated. |
| QA harness temporary cleanup | Applicable | Automatic cleanup of the temporary QA directory after both CLI calls | PASS | Cleanup completed without the previous `WinError 32`; the new CLI `finally` path detached and closed root file handlers. |
| Current-source PyInstaller sidecar | Required | `uv --directory ... run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Complete `dist\babelcodex-service.exe` produced; SHA-256 `617E3B38440B3BAAF884844480AD3825B79C645CC35B9B261E0BEB38DE08FB53`; 194,438,420 bytes. |
| Frozen sidecar protocol v1 | Required | JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Protocol 1, package 0.1.0, expected capabilities, preserved E: state visible, exit 0. |
| Frozen invalid-worker request | Applicable | `dist\babelcodex-service.exe --worker-request build\missing-worker-request-validation-current-cli.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui\src-tauri\binaries\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | SHA-256 matched; handshake and shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | Real `gui\dist\assets` staging; `check_gui_bundle.py --target x86_64-pc-windows-msvc --source-tree ... --manifest ...` | PASS | Fresh audit passed with current sidecar and manifest; JS/CSS/HTML and both sidecar names present. |
| WVQ-009 stale bundle negative audit | Required | Same audit with the preserved older sidecar | PASS | Expected exit 1: `sidecar predates newer Python sources`; stale input rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix ... run tauri -- build --bundles nsis,msi` | PASS | NSIS SHA-256 `645CB227A80CD9A65656F3D68D761D4CE8DEAC37DC1720441F9E53BEC9358744` (195,781,816 bytes); MSI SHA-256 `FEDCF16AE47F0F1599E8F12075F7FD6C7642C6363C23844B105548E99D9B31CB` (195,751,936 bytes). |
| Release GUI process smoke | Applicable | Start `gui\src-tauri\target\release\babelcodex-gui.exe`, wait 8s, stop only the validation process | PASS | Process remained alive for 8s. GUI SHA-256 `4801F1565974DA99368271EE5A298C89A40AD00695B7FADBF052004BE55A615F`; 4,597,248 bytes. |
| MSI administrative extraction and package parity | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads | BLOCKED | Current MSI invocation timed out after 90s with no log, no extracted executable and no payload; the validation process was stopped. No current-package extraction evidence exists. |
| Packaged stale-GUI error observation | Required | Launch stale-sidecar GUI variant and observe native connection error | BLOCKED | `sky.list_apps()` failed with `Trusted RPC service is not configured: sky`; no native UI action was performed. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, cancellation, reconnection and permissions | BLOCKED | Same unavailable native Windows GUI automation prerequisite. |
| Clean-user install/restart/recovery | Applicable | Fresh user profile, install/portable launch, sidecar restart and recovery | NOT RUN | Requires a real clean-user desktop session; not inferred from process smoke. |
| WVQ-007 full workdir/lock/retry/cancel/reconnect semantics | Applicable | Native Windows lifecycle and file-handle matrix | NOT RUN | The CLI QA cleanup path now passes, but the broader lifecycle matrix remains unexecuted. |
| WVQ-005 release security audit | Applicable | Defender/SmartScreen, signing/certificate, SBOM and release checksum audit | NOT RUN | No security-setting or release-signing workflow was authorized in this validation. |
| Live Codex/PDF integration | Applicable | Authorized live translation against representative PDF | NOT RUN | No usage-bearing live request was authorized; mock integration remains scoped evidence only. |
| Dependency advisory remediation | Not required for this validation | `npm audit fix` or major-version upgrade | NOT RUN | Advisories were recorded; no dependency or architecture change was made to force a clean report. |
| Linux-only platform target | Not applicable | Linux AppImage/native Linux acceptance | NOT APPLICABLE | This round verifies the Windows E: workspace. |

### Failure, blocking and follow-up analysis

- No `FAIL` remains in this revalidation. The previous Windows `WinError 32` on `logs\cbpdf.log` was directly retested against the new CLI handler-release path and the temporary QA directory cleaned successfully. This clears only that QA harness path; it does not prove the full WVQ-007 lifecycle matrix.
- The PyInstaller and Tauri outer sessions lost their final wrapper output while child build work was still finishing; filesystem inspection then confirmed complete artifacts, no residual build processes, and independently verified hashes. This is a command-observation nuisance, not a product failure.
- The MSI extraction blocker is unchanged: the current package build exists, but administrative extraction produces no log or payload within 90 seconds. Native GUI checks remain blocked because the trusted `sky` service is unavailable.
- Current status counts: `PASS 21`, `FAIL 0`, `BLOCKED 3`, `NOT RUN 5`, `NOT APPLICABLE 1`.

### Linux follow-up required

1. Run the broader native Windows `WVQ-007` workdir/lock/retry/cancel/reconnect matrix; retain the strict cleanup assertions even though the CLI QA path now passes.
2. Provision a usable Windows Installer administrative-extraction path and obtain current-MSI payload/sidecar parity evidence.
3. Run native Windows desktop validation for `WVQ-001` through `WVQ-004` and the stale-GUI portion of `WVQ-009`: Chinese rendering, keyboard, DPI, NVDA, picker/allowlist, Unicode and space-containing paths, permissions, cancellation, reconnection, window close, clean user and sidecar restart.
4. Keep `WVQ-009` freshness plus runtime handshake as release gates; separately schedule the Defender/SmartScreen/signing/SBOM audit and any live Codex/PDF test with explicit authorization.

Overall status remains `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_VERIFICATION_BLOCKING`.

## Validation run: 2026-09-12 (latest Linux state revalidation, current dirty tree)

### Validation environment and source state

- Linux source of truth: WSL Ubuntu `/home/shiraishi/VSCode Workspace/Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`). The tree was already dirty before this run: five documentation files plus nine code/test files (including the untracked `gui/src/protocol.test.ts`) were present. This was not a clean-commit validation, and this run did not modify business code, configuration, or dependencies.
- Windows disposable workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`. Existing `.venv`, `gui\node_modules`, Rust target, build/dist, state/logs and user-content directories were inspected and preserved. A filtered one-way `robocopy` sync from `\\wsl.localhost\Ubuntu\home\shiraishi\VSCode Workspace\Codex_Translator` to E: used `/FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ`; `.git`, virtual environments, dependencies, caches, generated GUI assets, build/dist, logs, state and user-content directories were excluded. Dry-run and actual sync each reported 68 copied files, 0 failed files, and 17 E: extras preserved.
- The nine changed/untracked code/test files were compared by SHA-256 after sync; all matched. Generated GUI assets, frozen sidecar, target-triple sidecar, staging directories and installer outputs were created only in E: and were not reverse-synced.
- Toolchain: `uv 0.12.10`; project Python 3.12.13; Node.js 24.19.0; npm 11.17.0; Rust/cargo 1.98.0; PyInstaller 6.22.2; BabelDOC 0.6.4; openai-codex 0.147.0. `doctor` reported authenticated ChatGPT state; no usage-bearing live Codex request was made.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy` from the WSL source path to E: with the documented exclusions, then SHA-256 comparison | PASS | 68 files copied, 0 failed; 9 changed/untracked code/test hashes matched; E: extras preserved. |
| Dependency synchronization and lock | Required | `uv --directory E:\Shiraishi\VSCode Workspace\Codex_Translator sync --locked --extra runtime --extra dev`; `uv --directory ... lock --check` | PASS | 95 resolved, 91 checked; lock valid. |
| Python format/lint/compile | Required | `uv --directory ... run ruff format --check .`; `ruff check .`; `python -m compileall -q src tests scripts` | PASS | 91 files formatted; Ruff and compileall passed. |
| Python test suite | Required | `uv --directory ... run pytest -q --tb=short` | PASS | `200 passed, 5 deselected` in 75.64s. |
| Runtime doctor | Required | `uv --directory ... run cbpdf --config config/example.toml doctor` | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0, configured Windows paths and ChatGPT login reported. |
| GUI dependency install | Required | `npm.cmd --prefix E:\Shiraishi\VSCode Workspace\Codex_Translator\gui ci` | PASS | 158 packages installed; npm reported 2 moderate advisories and esbuild postinstall pending approval; no remediation was attempted. |
| GUI full tests | Required | `npm.cmd --prefix ... test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI production build | Required | `npm.cmd --prefix ... run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path ...\gui\src-tauri\Cargo.toml`; parse config; check `icon.ico` and `icon.png` | PASS | Cargo passed; `productName=BabelCodex`; both required icons exist. |
| Mock PDF integration | Required | `uv --directory ... run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 221.16s. |
| QA CLI and artifact tamper detection | Required | Temporary PDF/job; `qa <job-id>`; delete artifact and rerun | PASS | Initial `exit 0 / qa_status=passed`; tampered run `exit 1 / qa_status=failed`; one report generated. |
| QA harness temporary cleanup | Applicable | Automatic cleanup of the temporary QA directory | FAIL | Assertions completed, but cleanup reproduced `PermissionError: [WinError 32]` on `logs\cbpdf.log`; exact temporary directory was later removed with elevated cleanup. |
| Current-source PyInstaller sidecar | Required | `uv --directory ... run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | SHA-256 `CBAD9089F3E952A62CE5E1A666340A8B0CBF1FD40354A789A5C56A1FBEEA7841`; 194,439,871 bytes. |
| Frozen sidecar protocol v1 | Required | JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Protocol 1, package 0.1.0, expected capabilities, preserved E: state visible, exit 0. |
| Frozen invalid-worker request | Applicable | `dist\babelcodex-service.exe --worker-request build\missing-worker-request-validation-20260912-rerun.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui\src-tauri\binaries\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | SHA-256 matched; handshake and shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | Real `gui\dist\assets` staging; `check_gui_bundle.py --target x86_64-pc-windows-msvc --source-tree ... --manifest ...` | PASS | Fresh audit passed with current sidecar and manifest; JS/CSS/HTML and both sidecar names present. |
| WVQ-009 stale bundle negative audit | Required | Same audit with the preserved older sidecar | PASS | Expected exit 1: `sidecar predates newer Python sources`; stale input rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix ... run tauri -- build --bundles nsis,msi` | PASS | NSIS SHA-256 `AE89EB2F737D755C9634AA182C1CBDBB2B488CF967E56EB30325F6B6E85477E1` (195,786,695 bytes); MSI SHA-256 `DA6380426405FF7F07E22EB22BE8C1C689CC41FB1A7D5EF320B23A8C1D442AD3` (195,751,936 bytes). |
| Release GUI process smoke | Applicable | Start `gui\src-tauri\target\release\babelcodex-gui.exe`, wait 8s, stop only the validation process | PASS | Process remained alive for 8s. GUI SHA-256 `452E86E9EC1EC7CB0F384854C03ABDDFE32899AEFCF29FF4A934E972B8B0274F`; 4,597,248 bytes. |
| MSI administrative extraction and package parity | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads | BLOCKED | The current MSI invocation timed out after 90s with no log, no extracted executable and no payload; the validation process was stopped. No current-package extraction evidence exists. |
| Packaged stale-GUI error observation | Required | Launch stale-sidecar GUI variant and observe native connection error | BLOCKED | `sky.list_apps()` failed with `Trusted RPC service is not configured: sky`; no native UI action was performed. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, cancellation, reconnection and permissions | BLOCKED | Same unavailable native Windows GUI automation prerequisite. |
| Clean-user install/restart/recovery | Applicable | Fresh user profile, install/portable launch, sidecar restart and recovery | NOT RUN | Requires a real clean-user desktop session; not inferred from process smoke. |
| WVQ-007 full workdir/lock/retry/cancel/reconnect semantics | Applicable | Native Windows lifecycle and file-handle matrix | NOT RUN | Only the QA cleanup failure was observed; the full semantic matrix remains a separate follow-up. |
| WVQ-005 release security audit | Applicable | Defender/SmartScreen, signing/certificate, SBOM and release checksum audit | NOT RUN | No security-setting or release-signing workflow was authorized in this validation. |
| Live Codex/PDF integration | Applicable | Authorized live translation against representative PDF | NOT RUN | No usage-bearing live request was authorized; mock integration remains scoped evidence only. |
| Dependency advisory remediation | Not required for this validation | `npm audit fix` or major-version upgrade | NOT RUN | Advisories were recorded; no dependency or architecture change was made to force a clean report. |
| Linux-only platform target | Not applicable | Linux AppImage/native Linux acceptance | NOT APPLICABLE | This round verifies the Windows E: workspace. |

### Failure, blocking and validation-input analysis

- The unresolved `FAIL` is a Windows file-handle lifecycle issue in the temporary validation harness: the QA CLI assertions passed, but the Python logging file `logs\cbpdf.log` was still locked during `TemporaryDirectory` cleanup. This does not identify a production-code failure and remains tracked under `WVQ-007`; cleanup assertions were not weakened.
- The first unprivileged `uv` attempt was blocked by this machine's user-level uv cache/trampoline access boundary (`os error 183` / `os error 5`). The same commands passed under the approved validation command context; this is an execution-environment incident, not a project result.
- The first fresh staging attempt used an invalid directory-creation parameter and flattened assets. It was discarded; a second staging with the real `assets\` layout passed. The first audit must not be counted as package evidence.
- The stale audit failure was expected negative evidence and is recorded as a `PASS` for the rejection requirement. No business code, configuration or dependency was modified.
- Current status counts: `PASS 20`, `FAIL 1`, `BLOCKED 3`, `NOT RUN 5`, `NOT APPLICABLE 1`.

### Linux reconciliation after the CLI/QA-change revalidation

- The revalidation input already contained the CLI log-handler release hardening (`src/codex_babeldoc/cli.py` + `tests/test_cli.py`), and the previously failing QA harness temporary cleanup **passed without the previous `WinError 32`**. Linux confirms the Windows-side scoping: this clears only the QA-harness cleanup path; it is not proof of the full `WVQ-007` work-dir/lock/retry/cancel/reconnect matrix, which remains `WINDOWS_VERIFICATION_PENDING`.
- The `WVQ-009` stale bundle **negative audit** obtained direct native evidence this round (the preserved older sidecar was rejected with `sidecar predates newer Python sources`, expected exit 1). The `WVQ-009` queue item stays `WINDOWS_VERIFICATION_PENDING` overall because the packaged stale-GUI error observation and native desktop interaction are still `BLOCKED`.
- The MSI administrative-extraction `BLOCKED` (90-second timeout without log/payload) and the native GUI `BLOCKED` groups are unchanged; clean-user, `WVQ-005` release security and live Codex/PDF remain `NOT RUN`. Overall status remains `WINDOWS_VERIFICATION_PENDING`.
- No further Linux code change is made this round: the remaining failure owners are Windows-environment observations (Installer extraction path, native automation prerequisite), and speculative Linux-only changes would not be evidence for them.


### Linux follow-up required

1. Investigate and rerun the Windows fixture/log handle lifecycle under `WVQ-007`; preserve strict cleanup assertions and identify whether the holder is logging shutdown, a child process, the uv wrapper or Defender/antivirus.
2. Provision a usable Windows Installer administrative-extraction path and obtain current-MSI payload/sidecar parity evidence; the current package build alone is insufficient.
3. Run native Windows desktop validation for `WVQ-001` through `WVQ-004` and the stale-GUI portion of `WVQ-009`: Chinese rendering, keyboard, DPI, NVDA, picker/allowlist, Unicode and space-containing paths, permissions, cancellation, reconnection, window close, clean user and sidecar restart.
4. Keep `WVQ-009` freshness plus runtime handshake as release gates; separately schedule the Defender/SmartScreen/signing/SBOM audit and any live Codex/PDF test with explicit authorization.

Overall status remains `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_VERIFICATION_BLOCKING`.

## Validation run: 2026-09-12 (current dirty tree revalidation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`). The working tree remains dirty and includes the pre-existing sidecar/GUI/freshness/test/documentation changes; this is not a clean-commit validation.
- Windows disposable workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`. After inspecting and preserving E: local state, a filtered one-way WSL → E: sync on 2026-09-12 used `/FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ`; `.git`, virtual environments, `gui/node_modules`, Rust target, `build`, `dist`, `gui/dist`, caches, logs, state and user-content directories were excluded. Dry run and actual sync each reported 68 files, 0 failed files, and 17 E: extras preserved.
- Ten changed/untracked code/test files were checked by SHA-256 after sync; `HASH_MISMATCHES=0`. Generated GUI assets were rebuilt locally in E: and were not reverse-synced.
- Toolchain: `uv 0.12.10`; project `uv run` Python 3.12.13; system Python 3.14.7 was not used for project checks; Node.js 24.19.0; npm 11.17.0; Rust/cargo 1.98.0; PyInstaller 6.22.2; BabelDOC 0.6.4; openai-codex 0.147.0. `doctor` confirmed the configured Windows paths and authenticated Codex state; no usage-bearing live request was made.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy WSL E: /FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ` with documented exclusions, then SHA-256 comparison | PASS | 68 files copied, failed 0; 10 code/test hashes matched; E: extras preserved. |
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock valid. |
| Python format/lint/compile | Required | `uv run ruff format --check .`; `uv run ruff check .`; `uv run python -m compileall -q src tests scripts` | PASS | 91 files formatted; Ruff and compileall passed. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `200 passed, 5 deselected` in 29.15s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0, configured paths and ChatGPT login reported. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; esbuild postinstall remains pending approval; no dependency remediation was attempted. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml`; parse `tauri.conf.json`; check `icon.ico`/`icon.png` | PASS | Cargo passed; `productName=BabelCodex`; both required icons exist. |
| Mock PDF integration | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 231.37s; local mock path only. |
| WVQ-008 QA CLI and artifact tamper detection | Required | Temporary mock job; `uv run cbpdf --config <temp-config> qa <job-id>`; delete one artifact and rerun | PASS | Initial `exit 0 / qa_status=passed / 2 artifacts`; tampered run `exit 1 / qa_status=failed`. |
| QA fixture temporary cleanup | Applicable | Automatic cleanup of the same temporary fixture directory | FAIL | Reproduced `PermissionError: [WinError 32]` deleting `incoming\\fixture_two_column.pdf` after QA assertions. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | SHA-256 `232198B0EF1A65C0D633F7423D6CE0C66DE7794C65389767EF6E6C4D441983F4`; 194,438,039 bytes. |
| Frozen sidecar protocol v1 | Required | JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Protocol 1, package 0.1.0, expected capabilities, preserved E: state visible, exit 0. |
| Frozen invalid-worker request | Applicable | `dist\\babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260912-current.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui/src-tauri/binaries/babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | SHA-256 matched; handshake and shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260912 --target x86_64-pc-windows-msvc --source-tree . --manifest ...\\sha256.txt` | PASS | Corrected staging contained HTML/JS/CSS and both sidecars; audit passed. |
| WVQ-009 stale bundle negative audit | Required | Same audit with preserved older sidecar | PASS | Expected exit 1: `sidecar predates newer Python sources`; stale input rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS SHA-256 `8662431EF3FB8FD73876EF3AE3461C17909BDE2044C4F7406965FC135A40FB5A` (195,784,569 bytes); MSI SHA-256 `56B0100F2A515B4CB4E55343FB8B224917F6587C3EB3C7D55BA2761B33677C19` (195,751,936 bytes). |
| Release GUI process smoke | Applicable | Start `gui/src-tauri/target/release/babelcodex-gui.exe`, wait 8s, stop validation process | PASS | Process remained alive for 8s. GUI SHA-256 `78DA33D072FC911CE86946E021B563BC8AF02481696477F4ADF2CC992D644B8E`; 4,597,248 bytes. |
| MSI administrative extraction and package parity | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads | BLOCKED | First invocation hung over 3 minutes with no target/log output and was stopped; direct retry returned 0 but left a matching MSI process running and still produced no log or extracted exe. That validation process was stopped; no valid current-package extraction evidence. |
| Packaged stale-GUI error observation | Required | Launch stale-sidecar GUI variant and observe native connection error | BLOCKED | `sky.list_apps()` failed: `Trusted RPC service is not configured: sky`; no native UI action was performed. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, cancellation, reconnection, permissions | BLOCKED | Same unavailable native Windows GUI automation prerequisite. |
| Clean-user installation and first launch | Required | Isolated Windows user/profile installation and first launch | NOT RUN | No disposable clean-user profile was entered. |
| WVQ-007 work-dir cleanup/lock/retry semantics | Required | Cleanup, retention, locked-file retry, cancellation and reconnection matrix | NOT RUN | Separate semantic matrix remains outstanding; fixture cleanup FAIL is recorded independently. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Formal release-security workflow | NOT RUN | Unsigned development packages; workflow not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration not authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Would mutate dependency state and is outside validation. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Requires a target Linux machine. |

### Failure and blocking analysis

- The unresolved product-adjacent execution failure is the Windows `WinError 32` during temporary fixture cleanup. QA generation and artifact tamper rejection passed before cleanup; the failure is categorized as Windows file-handle/resource lifecycle and blocks claiming a clean fixture/work-directory lifecycle. No cleanup assertion was weakened.
- Two validation-wrapper inputs were corrected and are not product failures: the first frozen-sidecar probe omitted `protocol_version=1` and received the expected structured unsupported-version error; the first fresh-audit staging copy used a literal wildcard and omitted GUI assets. The corrected v1 probe and corrected full-asset audit passed.
- MSI admin extraction is `BLOCKED`, not `PASS`: the first explicit `msiexec` process had no target/log progress and was stopped; a direct retry returning exit 0 without payload is insufficient evidence. The native GUI rows are likewise `BLOCKED`, not passed; process-liveness smoke does not establish rendering, accessibility or interaction acceptance.
- npm’s known moderate development-tool advisories and esbuild pending-script warning remain warnings; no automatic remediation was run. No business code, architecture, dependency lockfile or project configuration was modified during validation.

### Linux reconciliation and hardening after the 2026-09-12 log-handle result

- The failed artifact changed across rounds while the failure class stayed identical: earlier rounds locked `incoming\fixture_two_column.pdf` during temporary fixture cleanup, and this round locked the QA CLI's own freshly written `logs\cbpdf.log`. Two different artifacts failing the same way points at the short-lived CLI command's handle lifecycle rather than any single test artifact.
- Linux-side hardening driven by this observation: `babelcodex` CLI `main()` now closes and detaches every root-logger `FileHandler` in a `finally` block (`_release_log_file_handlers`) at command completion, shortening the window in which the log file handle stays open instead of relying only on the `logging.shutdown()` atexit hook. A regression test (`test_cli_releases_log_file_handlers_at_exit`) pins handler detachment and stream closure. Linux gates after the change: `200 -> 201 passed, 5 deselected`, Ruff/format clean, GUI Vitest and `tsc --noEmit` clean.
- This is a handle-exposure mitigation, not a claimed fix for the Windows cleanup failure. The `WinError 32` row above stays a historical `FAIL`, remains tracked under `WVQ-007`, and must be confirmed by a native Windows re-run with the current source; it must not be converted to `PASS` by this Linux-only change, and no cleanup assertion was weakened.

### Linux follow-up required

1. Investigate the Windows fixture file-handle cleanup failure and rerun the full WVQ-007 retention/cleanup/lock/retry/cancel/reconnect matrix; do not mask the issue with ignored cleanup errors.
2. Resolve or provision the Windows Installer environment so current MSI administrative extraction can be performed with verifiable payloads and sidecar parity.
3. Arrange native Windows desktop automation for WVQ-001/002/003/004 and WVQ-009 stale-GUI presentation: Chinese rendering, keyboard, DPI, NVDA, picker/allowlist, Unicode/path-space/permissions, cancellation, reconnection, window close, clean-user and sidecar restart/recovery.
4. Retain WVQ-009 freshness audit and runtime handshake as regression gates after sidecar, protocol, PyInstaller or packaging changes.
5. Complete Defender/SmartScreen, signing, SBOM and formal release audit; assess npm advisories separately; authorize live Codex/PDF integration only as a distinct usage-bearing task.

### Final review

- The current dirty WSL tree was synchronized one-way to E: with generated artifacts excluded; source parity was verified and every scoped item has an explicit status.
- Current run summary: `PASS 19`, `FAIL 1`, `BLOCKED 3`, `NOT RUN 5`, `NOT APPLICABLE 1`. Overall status remains `WINDOWS_VERIFICATION_PENDING`; it is not `WINDOWS_VERIFICATION_BLOCKING`.
- Validation produced no business-code, dependency, architecture or configuration changes. Only validation documentation is eligible for WSL write-back.

## Validation run: 2026-09-11 (current dirty tree, WVQ-008/WVQ-009)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`). This is a dirty working-tree validation: the tree contains the pre-existing documentation changes, sidecar handshake and GUI protocol changes, `scripts/check_gui_bundle.py` freshness changes, their regression tests, `tests/test_e2e_mock.py` resource-scope changes, `scripts/build_linux_gui_bundle.sh` mode-only change, and untracked `gui/src/protocol.test.ts`; it is not a clean-commit validation.
- Existing E: `.venv`, `gui/node_modules`, Rust target, build/dist, state/logs and user-data directories were inspected and preserved. The dry-run identified 71 source files to update and 20 E: extras; actual filtered WSL-to-E sync copied 71 files with zero failures (robocopy exit `3`). Fourteen changed/untracked source files were checked after sync and had `HASH_MISMATCHES=0`.
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy WSL E: /E /COPY:DAT /DCOPY:DAT /IS /IT /XJ` with dependency/cache/state/user-data exclusions, then SHA-256 comparison | PASS | 71 files copied, failed 0; 14 changed/untracked source files matched. E: extras were preserved. |
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint/compile | Required | `uv run ruff format --check .`; `uv run ruff check .`; `uv run python -m compileall -q src tests scripts` | PASS | 91 files formatted; Ruff and compileall passed. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `200 passed, 5 deselected` in 58.58s, including new handshake/freshness tests. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex detected; ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; 2 moderate advisories and an esbuild pending-script warning were reported. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 4 files, 22 tests passed, including `protocol.test.ts` and stale-handshake coverage. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed; current JS asset `index-BEtFhpWU.js`. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml`; JSON/icon existence check | PASS | Cargo passed; `productName=BabelCodex`; `icon.ico` and `icon.png` exist. |
| Current-source PDF QA mock integration | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 194.44s; local mock fixture only, no paid Codex usage. |
| WVQ-008 fixture QA CLI and tamper detection | Required | Windows temporary `fixture_two_column.pdf` mock job; subprocess `uv run cbpdf --config <temp-config> qa <job-id>`; delete one artifact and rerun | PASS | Initial QA returned `qa_status=passed` with 2 artifacts; after deletion CLI returned exit 1 and `qa_status=failed` as required. |
| QA fixture temporary cleanup | Applicable | Cleanup of the same temporary mock-job directory after the CLI smoke | FAIL | `PermissionError: [WinError 32]` while unlinking `incoming\\fixture_two_column.pdf`; category: Windows-specific file-handle/resource cleanup. QA assertions completed before cleanup; cleanup behavior itself remains unresolved. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh sidecar built; SHA-256 `701D83EF04689C87BFAFE93FB6A22D44A15903CA46843C5E9C431E40384BD97C`, 194,438,558 bytes. |
| Frozen sidecar handshake and JSONL | Required | Frozen exe with protocol v1 `get_server_info`/`list_jobs`/`shutdown` | PASS | `protocol_version=1`, `package_version=0.1.0`, capability list includes `get_server_info`; exit 0. Preserved E: state was visible, so this was not an empty-state test. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260911-handshake.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | `gui/src-tauri/binaries/babelcodex-service-x86_64-pc-windows-msvc.exe` with `get_server_info`/`shutdown` | PASS | Exit 0; input SHA-256 matched fresh sidecar. |
| WVQ-009 fresh bundle source-tree audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260911-handshake --target x86_64-pc-windows-msvc --source-tree . --manifest ...\\sha256.txt` | PASS | Fresh Vite assets and sidecar passed source freshness and forbidden-content audit. |
| WVQ-009 stale bundle negative audit | Required | Same audit with a preserved older sidecar fixture | PASS | Audit returned the expected exit 1 and reported `sidecar predates newer Python sources`; stale input was rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | Both bundles rebuilt using the fresh target-triple sidecar. |
| Packaged GUI process smoke | Applicable | Start current `gui/src-tauri/target/release/babelcodex-gui.exe`, wait 8s, stop it | PASS | Process remained running for 8s. |
| MSI administrative extraction and package parity | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...`; inspect extracted payloads and hashes | PASS | Admin extraction exit 0; extracted sidecar SHA-256 matched `701D...97C`; GUI and sidecar present. |
| MSI-extracted sidecar handshake | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with `get_server_info`/`shutdown` | PASS | `protocol_version=1`, `package_version=0.1.0`, exit 0. |
| MSI-extracted GUI process smoke | Applicable | Start extracted `babelcodex-gui.exe`, wait 8s, stop it | PASS | Process remained running for 8s. |
| WVQ-009 packaged stale-GUI error observation | Required | Build/launch stale-sidecar GUI variant and observe native connection error | BLOCKED | Native GUI automation helper reported `Trusted RPC service is not configured: sky`; no desktop clicks or typing were performed. Static stale audit and GUI mock handshake tests passed, but packaged stale-GUI rendering/error presentation was not observed. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, cancellation, reconnection, permissions | BLOCKED | Same unavailable native GUI automation/desktop observation prerequisite. |
| Clean-user installation and first launch | Required | Isolated Windows user/profile install and first launch | NOT RUN | No disposable clean-user profile was entered. |
| WVQ-007 work-dir cleanup/lock/retry semantics | Required | `cleanup --dry-run`, retained terminal dir, active-job survival, locked-file retry and category retry checks | NOT RUN | The separate semantic matrix was not run; the fixture cleanup `WinError 32` is recorded independently. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Formal release-security workflow | NOT RUN | Development artifacts are unsigned; release-security workflow was not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized; mock integration is not live acceptance. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

- The `WinError 32` cleanup failure is the only unresolved execution failure in this round. The QA command itself and its tamper-detection assertion passed before cleanup; the failure indicates a Windows file-handle/lifecycle issue in the temporary fixture workflow and should not be converted to a pass by ignoring cleanup errors. It does not block the independent static, unit, integration, sidecar, GUI-build or installer checks, but it blocks claiming the complete Windows cleanup path is clean.
- The native GUI checks are `BLOCKED`, not passed: the available computer-use runtime has no configured trusted RPC service (`sky`). Process survival is insufficient evidence for native Chinese rendering, accessibility, stale-GUI error presentation or path interaction.
- npm advisories and the pending esbuild script are warnings; no automatic remediation was attempted. No validation-scope business code, dependency lockfile or project configuration was modified.

### Linux reconciliation and corrected attribution

- The 2026-09-11 dirty-tree validation input already contained the `tests/test_e2e_mock.py` resource-scope change (PyMuPDF documents opened with context managers; recorded in the run header above). The QA assertions and tamper detection passed, but the harness-level temporary fixture cleanup still reported `PermissionError: [WinError 32]` while unlinking `incoming\fixture_two_column.pdf`. The test-scope change is therefore retained as test hygiene only and is not the cause of or a fix for this Windows cleanup failure.
- Linux static review of the QA boundary found no handle leak in production code: `pdf_sanity.py`, `text_checks.py` and `layout_checks.py` close every PyMuPDF document with `try/finally` (or `with`). The remaining candidates for the `WinError 32` are in the Windows validation harness lifecycle (a not-yet-exited subprocess, an antivirus/Defender scan, or a `uv run` wrapper process still holding the fixture handle at deletion time).
- Because the failure is a Windows-observed file-handle lifecycle issue with no reproducible Linux counterpart and no identified production-code owner, it stays recorded here as a historical `FAIL` and is tracked under `WVQ-007` (work-dir cleanup/retention/lock/retry semantics) for a native Windows re-run. It must not be converted to `PASS` by a Linux-only change, and no cleanup assertion was weakened.

### Linux follow-up required

1. Re-run the Windows QA fixture cleanup and the documented `WVQ-007` work-dir retention, cleanup, locked-file retry and category-retry matrix with the current source, and observe the harness-level fixture deletion directly. Do not weaken cleanup assertions merely to obtain a pass.
2. Arrange a native Windows desktop/automation environment for `WVQ-001`/`WVQ-002`/`WVQ-003`/`WVQ-004` and the packaged stale-GUI error path: Chinese rendering, keyboard navigation, DPI 125%/150%/200%, NVDA, picker/allowlist, Unicode/path-space/permission cases, cancellation, reconnection, window close, clean-user install and sidecar restart/recovery.
3. Retain the `WVQ-009` source-tree freshness audit and runtime handshake as regression gates; rerun them after future sidecar, protocol, PyInstaller or packaging changes.
4. Complete Defender/SmartScreen, code-signing, SBOM and formal release-artifact audit (`WVQ-005`) before release claims.
5. Assess the two npm moderate advisories and esbuild pending-script warning separately; do not auto-fix during validation.
6. Run real Codex/PDF integration only as an explicitly authorized usage-bearing task.

### Final review

- The current WSL dirty tree was synchronized to E: and all current-source automated, mock-PDF, QA CLI, handshake, freshness-audit, GUI-build and NSIS/MSI checks were executed. Fresh sidecar SHA-256 is `701D83EF04689C87BFAFE93FB6A22D44A15903CA46843C5E9C431E40384BD97C`; GUI is `FBBDE4A9461FB6ADE3F4BDF9F515E8D0B0D91F6D5A3B3F3B80B0044EFB9FF8FA` (4,597,248 bytes); NSIS is `6BBBDAE445BB514A1A2DBE244B26F96F9F0D5936A7BA4B53AFAE1C242AF4A77F` (195,785,152 bytes); MSI is `6EBEC6E108667A3D8EC7D43DC1F0C4B17E5EB2F74BDC8966B5E315B054E436F1` (195,751,936 bytes).
- The current run has one unresolved `FAIL` (Windows fixture cleanup) and two `BLOCKED` native GUI groups; all other executed checks are `PASS`. Remaining unexecuted items are explicitly `NOT RUN`, and target Linux smoke is `NOT APPLICABLE`.
- No business code, architecture, dependency lockfile or project configuration was modified. Only generated validation artifacts changed in E:, and only validation documentation is eligible for WSL write-back.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`; the new failure and blockers do not make Linux development blocking, but they must be resolved or explicitly accepted before Windows release/desktop acceptance claims.

## Validation run: 2026-09-11 (current Linux HEAD, PDF QA and release path)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`, 2026-09-11 09:56:34 +08:00). The working tree is dirty only by the pre-existing mode-only change to `scripts/build_linux_gui_bundle.sh`; this is a working-tree validation, not a clean-commit validation.
- Existing E: `.venv`, `gui/node_modules`, Rust target, build/dist, state/logs and user-data directories were inspected and preserved. The first filtered sync did not copy the newly committed PDF-QA/release files; validation was not run on that incomplete copy. A corrective WSL-to-E sync with `/IS /IT /XJ` copied 68 files with zero failures, and all newly required file hashes matched (`NEW_FILE_HASH_MISMATCHES=0`).
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy WSL E: /E /COPY:DAT /DCOPY:DAT /IS /IT /XJ` with dependency/cache/state/user-data exclusions, then SHA-256 comparison | PASS | Corrective sync copied 68 files, failed 0; current QA/release files matched. |
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | PASS | 91 files already formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `196 passed, 5 deselected` in 53.28s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex detected; ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; npm reported 2 moderate advisories and an esbuild pending-script warning. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 3 files, 19 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 8 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml`; JSON/icon existence check for `gui/src-tauri/tauri.conf.json` | PASS | Cargo passed; `productName=BabelCodex`; `icon.ico` and `icon.png` exist. |
| Current-source PDF QA mock integration | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 411.37s; local mock fixture only, no paid Codex usage. |
| QA CLI/service/MCP coverage | Required | Full Python suite including `test_qa_cli_reports_passing_output`, `test_run_qa_tool_is_scoped` and QA end-to-end tests | PASS | Covered by the 196-test suite; generated QA reports and passing QA status were asserted. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh sidecar built; SHA-256 `DD99EFC90C3960A27025CC5913BE0835CAA521D8DF332678D7A57D2DEE1496E6`, 194,430,767 bytes. |
| Frozen sidecar JSONL | Required | Frozen exe with protocol v1 `list_jobs`/`shutdown` | PASS | `ok=true`, structured responses, exit 0; preserved E: state was visible, so the list was not an empty-state test. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260911-current.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | `gui/src-tauri/binaries/babelcodex-service-x86_64-pc-windows-msvc.exe` with protocol v1 `list_jobs`/`shutdown` | PASS | Exit 0; target input hash matched fresh sidecar `DD99...496E6`. |
| First GUI bundle audit attempt | Applicable | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260911-current --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | FAIL | Temporary staging used only `babelcodex-service.exe`; audit required the target-triple filename. Validation wrapper/staging error, not product code. |
| Corrected GUI/sidecar bundle audit | Required | Same audit after adding `babelcodex-service-x86_64-pc-windows-msvc.exe` | PASS | Current Vite assets and fresh sidecar passed; manifest written. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | Both bundles rebuilt from current GUI and refreshed sidecar input. |
| Packaged GUI process smoke | Applicable | Start `gui/src-tauri/target/release/babelcodex-gui.exe`, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| First MSI-extracted sidecar smoke | Required | First rebuilt MSI, `msiexec /a ... TARGETDIR=... /qn`, then extracted sidecar with current example config | FAIL | MSI embedded stale target-triple sidecar hash `4577E0D4...`; config load failed with `TranslationConfig.__init__() got an unexpected keyword argument 'retry_policy'`. Packaging input was stale. |
| Corrected MSI administrative extraction | Applicable | Replaced only the E: target-triple sidecar input with fresh `DD99...496E6`, rebuilt MSI, then `msiexec /a ... /qn /L*v ...` | PASS | Admin extraction exit 0; extracted GUI and sidecar found. |
| Corrected MSI-extracted sidecar smoke | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with protocol v1 `list_jobs`/`shutdown` and `config/example.toml` | PASS | Exit 0; extracted sidecar hash `DD99...496E6` matched fresh sidecar. |
| Corrected MSI-extracted GUI process smoke | Applicable | Start extracted `babelcodex-gui.exe`, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| Packaged GUI interaction/path matrix | Required | Installed/portable picker, Chinese rendering, keyboard/DPI/NVDA, allowlist, cancellation, reconnection, clean-user and permission matrix | NOT RUN | No suitable disposable native desktop/isolated-user acceptance environment was entered. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Formal release-security workflow | NOT RUN | Development artifacts are unsigned; release-security workflow was not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized; mock PDF integration is not a live-acceptance substitute. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

- The two `FAIL` results were resolved validation-input issues, not unresolved current-source product failures. The first bundle audit staging missed the required target-triple filename. The first Tauri/MSI build consumed the stale E: target-triple sidecar (`4577E0D4...`) instead of the freshly rebuilt current-source sidecar; its `retry_policy` config incompatibility was therefore a packaging-input drift finding. After refreshing that generated E: input and rebuilding, direct target-triple, NSIS/MSI extraction, extracted sidecar and extracted GUI checks passed.
- No check was `BLOCKED`. npm advisories and the pending esbuild script are warnings, not automatic remediation targets for this validation.

### Linux follow-up required

1. Treat the current PDF QA battery and local mock-PDF gate as retained regression coverage; rerun it on Linux and Windows after future QA, BabelDOC, worker or artifact-manifest changes.
2. Arrange native Windows installed/portable GUI acceptance for Chinese rendering, keyboard navigation, DPI 125%/150%/200%, NVDA, picker/allowlist, non-ASCII and space-containing paths, cancellation, reconnection, window close and permissions.
3. Run clean-user first-launch validation separately.
4. Complete Defender/SmartScreen, code-signing, SBOM and formal release-artifact audit (`WVQ-005`) before release claims.
5. Assess the two npm moderate advisories and esbuild pending-script warning as a separate dependency decision; do not auto-fix them during validation.
6. Run real Codex/PDF integration only as an explicitly authorized usage-bearing task.

### Final review

- All current-source automated, mock-PDF, frozen-sidecar, GUI-build, bundle-audit and NSIS/MSI package checks completed after corrective synchronization. The run contains two recorded `FAIL` attempts caused by validation staging/package-input drift; their corrected reruns are `PASS`.
- Remaining gaps are explicitly `NOT RUN`; target Linux smoke is `NOT APPLICABLE`; there are no `BLOCKED` checks.
- No business code, architecture, dependency lockfile or project configuration was modified. Only generated validation artifacts changed in E:, and only the three validation documents are eligible for Linux write-back.
- Overall status remains `WINDOWS_VERIFICATION_PENDING` because real desktop interaction, clean-user, accessibility, security/release and live Codex/PDF checks remain outstanding.

## Validation run: 2026-09-10 (latest Linux working tree, current UI revalidation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca`.
- The working tree was dirty and included uncommitted architecture/validation documentation, current GUI source and tests, and a mode-only build-script change. This is a working-tree validation, not a clean-commit validation.
- Existing E: `.venv`, `gui/node_modules`, Rust target, build/dist outputs, state/logs and user data were inspected and preserved. Filtered one-way `robocopy` completed with exit `3`, zero failed files; 10 source files were copied. Key source/document hashes matched (`HASH_MISMATCHES=0`).
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; project Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | PASS | 78 files already formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `157 passed, 3 deselected` in 45.41s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex versions detected; ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; 2 moderate advisories and an esbuild pending-script warning reported. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 3 files, 19 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 8 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Windows-native Cargo check passed. |
| Tauri config/icon parse | Required | JSON parse of `gui/src-tauri/tauri.conf.json` and icon existence checks | PASS | `productName=BabelCodex`; `icon.ico` and `icon.png` exist. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh Windows frozen sidecar built successfully. |
| Frozen sidecar JSONL | Required | Frozen exe with protocol version 1 `list_jobs`/`shutdown` requests | PASS | `ok=true`, `jobs=[]`, closing response, exit 0. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260910-current.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Fresh target-triple exe with protocol version 1 JSONL requests | PASS | `ok=true`, `jobs=[]`, exit 0; SHA-256 `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`. |
| GUI/sidecar bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260910-current --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | PASS | Current Vite assets and fresh target sidecar passed. |
| Current-source NSIS/MSI | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 195,743,723 bytes, SHA-256 `9C9332AD3FE09FAFFB71AAE35F157D1333DEAC6F57E369BA052B3511DA4B4F1B`; MSI 195,715,072 bytes, SHA-256 `D0C5D8B87EB9BA7D5F21F66445C46BD827F0A0558E28F1416573ECE848B7CC23`. |
| Packaged GUI process smoke | Applicable | Start current release GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| MSI administrative extraction | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...` | PASS | Exit 0; extracted GUI and sidecar payloads. |
| MSI-extracted sidecar smoke | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with `list_jobs`/`shutdown` | PASS | `ok=true`, `jobs=[]`, exit 0; package sidecar hash matched target-triple sidecar. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| Packaged GUI interaction/path matrix | Required | Installed/portable picker, allowlist, cancellation, reconnection, clean-user and path/permission matrix | NOT RUN | No native desktop interaction or isolated-user acceptance evidence in this run. |
| Chinese UI rendering/accessibility matrix | Required | Packaged Chinese labels, keyboard navigation, DPI 125/150/200%, NVDA and window interaction | NOT RUN | Process-level launch and automated DOM tests do not establish native rendering/accessibility acceptance. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Release-security workflow | NOT RUN | Development artifacts are unsigned; release workflow not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

- No product `FAIL` or `BLOCKED` result occurred. The current Windows GUI suite passes 19/19; the earlier duplicate `mock-job-1` failure remains historical.
- npm’s two moderate advisories and esbuild pending-script warning are recorded as warnings; automatic remediation was intentionally not run.
- One combined PowerShell probe omitted its final target exit marker; the target-triple command was rerun independently and passed. This was a validation-wrapper issue, not a product failure.

### Linux follow-up required

1. Preserve the GUI reconciliation regression tests and rerun Linux/Windows GUI checks after future GUI changes.
2. Execute real packaged Chinese UI rendering/accessibility, keyboard, DPI, NVDA, picker, clean-user, path/permission, cancellation/reconnection and window-close checks.
3. Complete Defender/SmartScreen, signing, SBOM and formal release artifact audit when release validation begins.
4. Assess npm advisories separately; do not apply automatic dependency changes as part of validation.
5. Run live Codex/PDF integration only as a separately authorized usage-bearing task.

### Final review

- E: matched the intended current WSL state before validation; only validation documentation is eligible for write-back.
- Every applicable item has an explicit status. This round has no `FAIL` or `BLOCKED`; remaining gaps are explicitly `NOT RUN`, and target Linux smoke is `NOT APPLICABLE`.
- No business code, architecture, dependency lockfile or configuration was modified during validation. Windows outputs remain disposable E: artifacts.
- Overall status remains `WINDOWS_VERIFICATION_PENDING` because real desktop interaction, Chinese UI/accessibility, clean-user and release-security checks are still outstanding.

## Validation run: 2026-09-10 (latest Linux working tree, current GUI confirmation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca`.
- The working tree was dirty and included uncommitted architecture/validation documentation, current GUI source and tests (`App.tsx`, `App.test.tsx`, `jobStore.ts`, `jobStore.test.ts`, `styles.css`), and a mode-only build-script change. This is a working-tree validation, not a clean-commit validation.
- Existing E: local `.venv`, `gui/node_modules`, Rust target, build/dist outputs, state/logs and user data were inspected and preserved. Filtered one-way `robocopy` from WSL to E: completed with exit `3`, zero failed files; 10 files were copied. Key source/document hashes matched (`HASH_MISMATCHES=0`).
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; project Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | PASS | 78 files already formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `157 passed, 3 deselected` in 45.41s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex versions detected; ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; 2 moderate advisories and an esbuild pending-script warning reported. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 3 files, 19 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 8 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Windows-native Cargo check passed. |
| Tauri config/icon parse | Required | JSON parse of `gui/src-tauri/tauri.conf.json` and icon existence checks | PASS | `productName=BabelCodex`; `icon.ico` and `icon.png` exist. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh Windows frozen sidecar built successfully. |
| Frozen sidecar JSONL | Required | Frozen exe with protocol version 1 `list_jobs`/`shutdown` requests | PASS | `ok=true`, `jobs=[]`, closing response, exit 0. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260910-current.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Fresh target-triple exe with protocol version 1 JSONL requests | PASS | `ok=true`, `jobs=[]`, exit 0; SHA-256 `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`. |
| GUI/sidecar bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260910-current --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | PASS | Current Vite assets and fresh target sidecar passed. |
| Current-source NSIS/MSI | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 195,743,723 bytes, SHA-256 `9C9332AD3FE09FAFFB71AAE35F157D1333DEAC6F57E369BA052B3511DA4B4F1B`; MSI 195,715,072 bytes, SHA-256 `D0C5D8B87EB9BA7D5F21F66445C46BD827F0A0558E28F1416573ECE848B7CC23`. |
| Packaged GUI process smoke | Applicable | Start current release GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| MSI administrative extraction | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...` | PASS | Exit 0; extracted GUI and sidecar payloads. |
| MSI-extracted sidecar smoke | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with `list_jobs`/`shutdown` | PASS | `ok=true`, `jobs=[]`, exit 0; package sidecar SHA-256 matched target-triple sidecar. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| Packaged GUI interaction/path matrix | Required | Installed/portable picker, allowlist, cancellation, reconnection, clean-user and path/permission matrix | NOT RUN | No native desktop interaction or isolated-user acceptance evidence in this run. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Release-security workflow | NOT RUN | Development artifacts are unsigned; release workflow not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

- No product `FAIL` or `BLOCKED` result occurred. The prior GUI duplicate `mock-job-1` issue remains historical and is not reproduced; the current Windows GUI suite passes 19/19.
- npm’s two moderate advisories and esbuild pending-script warning are recorded as warnings; automatic remediation was intentionally not run.
- One combined PowerShell probe omitted its final target exit marker; the target-triple command was rerun independently and passed. This is a validation-wrapper issue, not a product failure.

### Linux follow-up required

1. Preserve the GUI reconciliation regression tests and rerun Linux/Windows GUI checks after future GUI changes.
2. Execute real installed/portable GUI interaction, clean-user, non-ASCII/path-space/path-permission, cancellation/reconnection and window-close checks in a suitable disposable Windows environment.
3. Complete Defender/SmartScreen, signing, SBOM and formal release artifact audit when release validation begins.
4. Assess npm advisories separately; do not apply automatic dependency changes as part of validation.
5. Run live Codex/PDF integration only as a separately authorized usage-bearing task.

### Final review

- E: matched the intended current WSL state before validation; only validation documentation is eligible for write-back.
- Every applicable item has an explicit status. This round has no `FAIL` or `BLOCKED`; remaining gaps are explicitly `NOT RUN`, and target Linux smoke is `NOT APPLICABLE`.
- No business code, architecture, dependency lockfile or configuration was modified during validation. Windows outputs remain disposable E: artifacts.
- Overall status remains `WINDOWS_VERIFICATION_PENDING` because real desktop interaction, clean-user and release-security checks are still outstanding.

## Linux follow-up after Chinese GUI layout update (2026-09-10)

- Linux changed only the GUI presentation layer and tests: navigation, page headings, form labels, job states, glossary/context editor, diagnostics and settings are now in Simplified Chinese. Existing sidecar, file allowlist, job state and Application Service contracts were preserved.
- Settings now exposes a disabled `界面语言` selector with `简体中文（当前）` and the explanation `语言切换功能将在后续版本提供。` This is a visible i18n placeholder only; no locale persistence, runtime dictionary or backend parameter was added.
- Linux verification after this UI update: GUI Vitest `3 files, 19 tests passed`; GUI production build passed; Python `157 passed, 3 deselected`; Ruff format/check and compileall passed; current Linux staged bundle audit passed.
- Because the GUI text and layout changed after the previous Windows package run, Windows packaged Chinese rendering, keyboard navigation, DPI 125%/150%/200%, NVDA, file selection, cancellation/reconnection and clean-user checks are `WINDOWS_VERIFICATION_PENDING`. Linux test/build results must not be promoted to Windows PASS.

## Validation run: 2026-09-10 (latest Linux working tree, post-reconciliation confirmation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `8f6ee91b2fe449845ccc8abaa59f55f689ab82ca`.
- The working tree was dirty and included uncommitted `docs/architecture.md`, the validation/plan documents, the current GUI sources/tests/styles, and a mode-only build-script change. This is a working-tree validation, not a clean-commit validation.
- Before synchronization, the existing E: checkout was inspected. Its `.venv`, `gui/node_modules`, Rust target, build/dist outputs, state/logs and user-data directories were preserved. Filtered one-way `robocopy` from WSL to E: completed with exit `3`, zero failed files; 9 source files were copied. Key source/document hashes matched (`HASH_MISMATCHES=0`).
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; project Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock check passed. |
| Python format/lint | Required | `uv run ruff format --check .`; `uv run ruff check .` | PASS | 78 files already formatted; Ruff passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `157 passed, 3 deselected` in 51.35s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex versions detected; ChatGPT login active. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; 2 moderate advisories and an esbuild pending-script warning reported. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 3 files, 18 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 8 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Windows-native Cargo check passed. |
| Tauri config/icon parse | Required | JSON parse of `gui/src-tauri/tauri.conf.json` and icon existence checks | PASS | `productName=BabelCodex`; `icon.ico` and `icon.png` exist. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | Fresh Windows frozen sidecar built successfully. |
| Frozen sidecar JSONL | Required | Frozen exe with protocol version 1 `list_jobs`/`shutdown` requests | PASS | `ok=true`, `jobs=[]`, closing response, exit 0. |
| Frozen worker invalid request | Required | `dist/babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260910-rerun.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Fresh target-triple exe with protocol version 1 JSONL requests | PASS | `ok=true`, `jobs=[]`, exit 0; SHA-256 `CDE9A9DBDD4F47671EBE576BB2DCBED5DAF19E88615E56AC344D8A6CC7F0956A`. |
| GUI/sidecar bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260910-latest --target x86_64-pc-windows-msvc --manifest ...\\sha256.txt` | PASS | Current Vite assets and fresh target sidecar passed. |
| Current-source NSIS/MSI | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 195,747,786 bytes, SHA-256 `14975F49B62A070D97B1649460BCD87955559541209BD259EFDD8F64C9A9AC27`; MSI 195,710,976 bytes, SHA-256 `C8CD3C61AF7E97890B97B7FD17C0D000B50BC34318B5D1E0B6D5BE315D905275`. |
| Packaged GUI process smoke | Applicable | Start current release GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| MSI administrative extraction | Applicable | `msiexec /a ... TARGETDIR=... /qn /L*v ...` | PASS | Exit 0; extracted GUI and sidecar payloads. |
| MSI-extracted sidecar smoke | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with `list_jobs`/`shutdown` | PASS | `ok=true`, `jobs=[]`, exit 0; package sidecar hash matched target-triple sidecar. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8s, stop validation process | PASS | Process remained running for 8s. |
| Packaged GUI interaction/path matrix | Required | Installed/portable picker, allowlist, cancellation, reconnection, clean-user and path/permission matrix | NOT RUN | No native desktop interaction or isolated-user acceptance evidence in this run. |
| Defender/SmartScreen/signing/SBOM/release audit | Required | Release-security workflow | NOT RUN | Development artifacts are unsigned; release workflow not entered. |
| Live Codex/PDF integration | Applicable | Real Codex-authenticated translation fixture | NOT RUN | Usage-bearing integration was not authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` | NOT RUN | Not part of validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Must run on a target Linux machine. |

### Failure and blocking analysis

- No product `FAIL` or `BLOCKED` result occurred. The previous GUI duplicate `mock-job-1` failure remains historical; after the synchronized Linux reconciliation changes, Windows GUI tests passed 18/18.
- npm’s two moderate advisories and esbuild pending-script warning are recorded as warnings; no automatic dependency remediation was attempted.
- One combined PowerShell probe did not print its target-sidecar exit marker; the target-triple smoke was rerun independently and passed. This was a validation-wrapper issue, not a product failure.

### Linux follow-up required

1. Preserve the idempotent GUI job/event reconciliation and its regression tests; rerun Linux/Windows GUI tests after future GUI changes.
2. Execute real installed/portable GUI interaction, clean-user, non-ASCII/path-space/path-permission, cancellation/reconnection and window-close checks in a suitable disposable Windows environment.
3. Complete Defender/SmartScreen, signing, SBOM and formal release artifact audit when release validation begins.
4. Run live Codex/PDF integration only as a separately authorized usage-bearing task.

### Final review

- E: matched the intended current WSL state before validation; only validation documentation is eligible for write-back.
- Every applicable item has an explicit status. This round has no `FAIL` or `BLOCKED`; remaining gaps are explicitly `NOT RUN`, and target Linux smoke is `NOT APPLICABLE`.
- No business code, architecture, dependency lockfile or configuration was modified during validation. Windows outputs remain disposable E: artifacts.
- Overall status remains `WINDOWS_VERIFICATION_PENDING` because real desktop interaction, clean-user and release-security checks are still outstanding.

## Validation run: 2026-09-12 (current Linux dirty tree, fresh sidecar/package rerun)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb` (`feat: add PDF QA battery, qa command and release operations guide`). The working tree was dirty and included 12 code/test files (including untracked `gui\src\protocol.test.ts`), five documentation files, and a mode-only script change; this was a working-tree validation, not a clean-commit validation.
- Windows disposable workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`. The target was inspected before sync. Filtered one-way `robocopy` WSL → E: used `/E /FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ /R:0 /W:0`, excluding `.git`, `.venv`, `.pytest_cache`, `.ruff_cache`, `gui\node_modules`, Rust target, `build`, `dist`, `gui\dist`, `logs`, `state`, `incoming`, `translated`, `glossary`, `context`, and `*.pdf/*.log/*.pyc/*.db/*.sqlite`. Dry-run and actual sync each copied 67 files, failed 0 files, and preserved 17 E: extras; Robocopy exit 3 is expected for this non-purge mirror.
- SHA-256 matched for 24 selected changed/control files, including all 12 changed or untracked code/test files and the validation/Plan/configuration documents (`HASH_MISMATCHES=0`). E: local `.venv`, `gui\node_modules`, Rust target, existing generated artifacts, state and logs remained outside the sync scope. No Windows source or generated output was synchronized back to WSL.
- Windows 11 Professional Workstation Insider Preview `10.0.29661`, x64; `uv 0.12.10`; project Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; PyInstaller `6.22.2`; BabelDOC `0.6.4`; openai-codex `0.147.0`; Visual Studio Build Tools `17.14.39`; WebView2 `152.0.4191.66`. `doctor` reported authenticated ChatGPT state; no usage-bearing live request was made.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy` and SHA-256 comparison | PASS | 67 files copied, 0 failed, 17 E: extras preserved; selected source/control hashes matched. |
| Dependency synchronization and lock | Required | `uv sync --locked --extra runtime --extra dev`; `uv lock --check` | PASS | 95 resolved, 91 checked; lock valid. |
| Python format/lint/compile | Required | `uv run ruff format --check .`; `uv run ruff check .`; `uv run python -m compileall -q src tests scripts` | PASS | 91 files formatted; Ruff and compileall passed. |
| Python test suite | Required | `uv run pytest -q --tb=short` | PASS | `201 passed, 5 deselected` in 50.42s. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex runtime, configured paths and ChatGPT login reported. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; 2 moderate advisories and esbuild pending-script warning recorded, no remediation run. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host and config/icons | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml`; parse `tauri.conf.json`; check `icon.ico`/`icon.png` | PASS | Cargo passed; `productName=BabelCodex`; both icons exist. |
| Mock PDF integration | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py` | PASS | `5 passed` in 180.16s; local mock path only. |
| WVQ-008 QA CLI and artifact tamper detection | Required | Temporary mock job; `uv run cbpdf --config <temp-config> qa <job-id>`; delete one artifact and rerun | PASS | Initial QA `exit 0 / qa_status=passed` for mono/dual outputs; tampered run `exit 1 / qa_status=failed`; 2 reports generated. |
| QA fixture temporary cleanup | Applicable | Automatic cleanup of the same temporary QA directory | PASS | Cleanup completed; previous `WinError 32` was not reproduced on the current CLI handler-release path. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | `dist\babelcodex-service.exe`, SHA-256 `29D0A257C35835440831EAF13AD4A4F788C490A52CBB8521FD3FC76B0BD02AC4`, 194,439,805 bytes. |
| Frozen sidecar protocol v1 | Required | Frozen exe JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Protocol 1, package 0.1.0, expected capabilities, preserved E: state visible, exit 0. |
| Frozen invalid worker request | Applicable | `dist\babelcodex-service.exe --worker-request build\missing-worker-request-validation-20260912-current-run.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui\src-tauri\binaries\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | SHA-256 matched fresh sidecar; handshake and shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | `uv run python scripts/check_gui_bundle.py <fresh-stage> --target x86_64-pc-windows-msvc --source-tree . --manifest <stage>\sha256.txt` with real `gui\dist` assets | PASS | Fresh HTML/JS/CSS and target sidecar passed; exit 0. |
| WVQ-009 stale bundle negative audit | Required | Same audit with preserved 2026-09-10 sidecar (`4577E0D4...`) | PASS | Expected exit 1 with `sidecar predates newer Python sources`; stale input rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS SHA-256 `D7AD204A78D299942BDAD69D864F8ED15447AA5E512E46898D757D4C024BD2B2`, 195,785,769 bytes; MSI SHA-256 `114EE0EC1878C0E836CADF6884BA537286A4BBB78F20E3D55EEDF09B551F30BB`, 195,751,936 bytes. |
| Release GUI process smoke | Applicable | Start `gui\src-tauri\target\release\babelcodex-gui.exe`, wait 8s, stop only validation process | PASS | Process remained alive for 8s; GUI SHA-256 `DAEEBE7F5555DFB7AA61FD68D6DF24177FE3C188FF2F672A44845226BA8F7597`, 4,597,248 bytes. |
| MSI administrative extraction and package parity | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads and hashes | PASS | Exit 0; 84,772-byte log and two payloads produced; extracted sidecar SHA-256 matched fresh sidecar. |
| MSI-extracted sidecar handshake | Required | Extracted `PFiles\BabelCodex\babelcodex-service.exe` with v1 `get_server_info`/`list_jobs`/`shutdown` | PASS | Protocol 1, package 0.1.0, expected capabilities, exit 0. |
| MSI-extracted GUI process smoke | Applicable | Start extracted `PFiles\BabelCodex\babelcodex-gui.exe`, wait 8s, stop validation process | PASS | Process remained alive for 8s. |
| Packaged stale-GUI error observation | Required | Launch stale-sidecar GUI variant and observe native connection error | BLOCKED | `Blocker: COMPUTER_USE_UNAVAILABLE`. One reasonable retry was attempted after the trusted Node process exited; the retry returned `helper_unknown_error: setup refresh had errors`. No native UI action/evidence was obtained. See `WIN-MANUAL-001`. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, cancellation, reconnection and permissions | BLOCKED | `Blocker: COMPUTER_USE_UNAVAILABLE`. The same unavailable desktop-control capability prevented interaction; one retry was not useful after the shared automation prerequisite had failed. Process smoke, GUI tests, bundle audit and sidecar checks are narrower non-GUI evidence and do not replace this item. See `WIN-MANUAL-002` through `WIN-MANUAL-005`. |
| Clean-user installation and first launch | Required | Isolated Windows user/profile installation and first launch | NOT RUN | No disposable clean-user profile was entered. |
| WVQ-007 work-dir cleanup/lock/retry/cancel/reconnect semantics | Applicable | Native Windows lifecycle and file-handle matrix | NOT RUN | Broader semantic matrix remains outstanding; QA harness cleanup pass does not prove it. |
| WVQ-005 Defender/SmartScreen/signing/SBOM/release audit | Applicable | Formal release-security workflow | NOT RUN | Development artifacts are unsigned; formal workflow was not entered. Read-only signatures were `NotSigned`. |
| Live Codex/PDF integration | Applicable | Authorized live translation fixture | NOT RUN | No usage-bearing request was authorized; mock integration is not live acceptance. |
| Dependency advisory remediation | Applicable | `npm audit fix` or upgrade | NOT RUN | Outside validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable | Linux-native runtime command | NOT APPLICABLE | Requires a target Linux machine. |

### Failure, blocking and follow-up analysis

- No current product `FAIL` occurred. The earlier Windows `WinError 32` temporary QA cleanup failure was re-tested against the current CLI handler-release path and cleanup passed. This clears only the QA harness cleanup path; the full WVQ-007 work-dir/lock/retry/cancel/reconnect matrix remains unexecuted.
- The native GUI and packaged stale-GUI presentation checks are `BLOCKED`, not failed: `Blocker: COMPUTER_USE_UNAVAILABLE`. The stale-GUI probe received one reasonable retry (trusted Node process exit, then `helper_unknown_error: setup refresh had errors`); the shared GUI interaction probe was not repeatedly retried after the same capability failure. No native UI action or evidence was obtained.
- Independent validation continued after these blockers: builds, CLI tests, unit/integration tests, filesystem/package checks, configuration checks, log-independent sidecar/process checks and installer verification were executed. Existing non-GUI evidence proves only narrower contracts and does not reclassify the GUI-only observations as `PASS`.
- Manual queue mapping: stale-GUI presentation → `WIN-MANUAL-001`; packaged GUI rendering/keyboard → `WIN-MANUAL-002`; DPI/NVDA/window lifecycle → `WIN-MANUAL-003`; picker/path/cancellation/reconnection → `WIN-MANUAL-004`; clean-user/restart/recovery → `WIN-MANUAL-005`. The manual entries remain incomplete until a human operator or working automation session records `PASS`, `FAIL` or `BLOCKED` with evidence.
- MSI administrative extraction is current native PASS evidence: the documented quoted `/a`, `TARGETDIR` and `/L*v` invocation produced a log and payloads; the extracted sidecar matched the fresh build and both extracted smoke checks passed.
- The two moderate npm advisories, esbuild pending-script warning, and unsigned development artifacts are recorded observations. No automatic dependency remediation, signing workflow, business-code change, configuration change or lockfile change was performed.

### End-of-validation result summary

#### Automated PASS

- WSL-to-E synchronization and selected source/control hash parity;
- dependency synchronization and lock validation;
- Python formatting, linting, compilation and full tests (`201 passed, 5 deselected`);
- runtime doctor, GUI tests (`22`), TypeScript/Vite build, Tauri checks and mock PDF integration;
- QA positive/tamper detection and temporary cleanup;
- current-source PyInstaller sidecar, protocol-v1/target-triple handshake, invalid-worker negative path, fresh/stale bundle audit, NSIS/MSI build, MSI extraction/parity and extracted sidecar/GUI process smoke.

#### Automated FAIL

- None in the current run. Historical failures remain in their original validation records and are not erased by this run.

#### BLOCKED

- **Packaged stale-GUI error observation** — `Blocker: COMPUTER_USE_UNAVAILABLE`. One reasonable retry was attempted: the trusted Node process exited, then the retry returned `helper_unknown_error: setup refresh had errors`. No native UI action or conclusion was obtained. Manual queue: `WIN-MANUAL-001`.
- **Packaged GUI interaction/path/DPI/NVDA matrix** — `Blocker: COMPUTER_USE_UNAVAILABLE`. The shared desktop-control capability was unavailable; no repeated retries were made after the capability failure. Process smoke, GUI tests, bundle audit and sidecar checks continued independently but prove narrower contracts only. Manual queue: `WIN-MANUAL-002` through `WIN-MANUAL-005`.

#### Manual validation required

- `WIN-MANUAL-001` through `WIN-MANUAL-005` remain `NOT_RUN` until a human operator or working Windows automation session performs the detailed procedures and records `PASS`, `FAIL` or `BLOCKED` with evidence.
- `WIN-MANUAL-006` remains `NOT_RUN` pending release authorization and the separately controlled live Codex/PDF workflow. It must not be started by ordinary validation or consume paid/plan model usage implicitly.

### Linux follow-up required

1. Provision a usable native Windows desktop automation surface and run `WVQ-001` through `WVQ-004` plus the stale-GUI portion of `WVQ-009`: Chinese rendering, keyboard, DPI, NVDA, picker/allowlist, Unicode and path-space/permission cases, cancellation, reconnection, window close, clean-user and sidecar restart/recovery.
2. Run the broader native Windows `WVQ-007` work-dir retention/cleanup/lock/retry/cancel/reconnect matrix; retain strict cleanup assertions even though the isolated QA cleanup now passes.
3. Complete `WVQ-005` Defender/SmartScreen, signing, SBOM and formal release audit when release validation is authorized; assess npm advisories separately.
4. Run live Codex/PDF integration only as a separately authorized usage-bearing task.

### Final review

- Current dirty WSL source was synchronized one-way to E:; 24 selected control/changed files matched, excluded local state remained preserved, and no validation process remained running.
- Current row summary: `PASS 23`, `FAIL 0`, `BLOCKED 2`, `NOT RUN 5`, `NOT APPLICABLE 1`. Overall status remains `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_VERIFICATION_BLOCKING`.
- This validation changed no WSL business code, dependencies, architecture or configuration. The only intended WSL write-back is this validation record and the matching plan/compatibility summaries.
## Manual Windows Validation Queue handoff (2026-09-12)

The automated native desktop surface was unavailable. The automated rows above
therefore remain `BLOCKED` with `Blocker: COMPUTER_USE_UNAVAILABLE`; this
handoff does not reclassify them as `PASS`. The detailed entries in the
`Manual Windows Validation Queue` above are the authoritative manual checklist.
Until an operator returns observations, the manual attempts have no conclusion
and must remain `NOT_RUN` (or become `BLOCKED` with the applicable blocker if
the human session itself cannot be controlled).

| Test ID | Test name | Automated status | Blocker | Manual status | Manual procedure |
|---|---|---|---|---|---|
| `WIN-MANUAL-001` | Packaged stale-sidecar GUI error presentation | `BLOCKED` | `COMPUTER_USE_UNAVAILABLE` | `BLOCKED` | Use the stale-sidecar package and follow the detailed steps above; verify an actionable startup/connection error before any job begins. |
| `WIN-MANUAL-002` | Packaged GUI Chinese rendering and keyboard flow | `BLOCKED` | `COMPUTER_USE_UNAVAILABLE` | `PASS` | Follow the default-size, screen-label and `Tab`/`Shift+Tab` steps above; capture focus and layout evidence. |
| `WIN-MANUAL-003` | DPI, NVDA and window lifecycle | `BLOCKED` | `COMPUTER_USE_UNAVAILABLE` | `NOT_RUN` | Repeat at 125%, 150% and 200%, run NVDA, resize, close and reopen; record scale and accessibility evidence. |
| `WIN-MANUAL-004` | Picker, allowlist, paths, cancellation and reconnection | `BLOCKED` | `COMPUTER_USE_UNAVAILABLE` | `NOT_RUN` | Exercise allowed/denied, Unicode/space, missing/restricted paths, cancellation, artifact tamper and sidecar restart steps above. |
| `WIN-MANUAL-005` | Clean-user installation, restart and recovery | `NOT_RUN` | Clean-user session pending; use `COMPUTER_USE_UNAVAILABLE` if the required desktop cannot be controlled | `NOT_RUN` | Install in an isolated user profile, start a mock job, restart the service, verify safe recovery and explicit retry. |
| `WIN-MANUAL-006` | Release security and authorized live Codex/PDF acceptance | `NOT_RUN` | Authorization and release workflow pending | `NOT_RUN` | Execute only after written authorization and follow the security/live-integration steps above; no live request is permitted from this handoff. |
Handoff directory: `E:\Shiraishi\VSCode Workspace\Codex_Translator\build\manual-gui-validation-20260912-152358`.

The fresh pair contains the current GUI (`DAEEBE7F...8F7597`) and current sidecar (`29D0A257...BD02AC4`). The stale pair contains the same current GUI and the preserved older sidecar (`4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`, built 2026-09-10). A read-only probe of that old sidecar reproduced `TypeError: TranslationConfig.__init__() got an unexpected keyword argument 'retry_policy'`, so the stale-GUI check must verify whether the GUI presents that startup incompatibility as an actionable user-facing error. Do not start a live Codex translation during this manual handoff.

Until the manual result fields are returned, the Linux follow-up remains:
complete `WVQ-001` through `WVQ-004`, the packaged stale-GUI part of `WVQ-009`,
and the clean-user/release checks on a native Windows desktop, then reconcile
the statuses here. No business code, dependency, architecture or
configuration was changed for this handoff.

For each completed manual entry, fill in:

```text
Result: PASS | FAIL | BLOCKED
Notes:
Error:
Evidence:
```

Collect screenshots, exact error text, relevant GUI/sidecar logs, Windows Event
Viewer entries for crashes, process status, package and sidecar hashes, and
reproduction steps. Do not include credentials or full document text.

## Manual GUI validation results (2026-09-12, operator report)

The operator completed the prepared fresh/stale GUI handoff and returned observations without screenshots. The following statuses are based on the report; screenshots are supplementary evidence, not required to record the initial result.

| Check | Classification | Status | Actual observation |
|---|---|---|---|
| M-GUI-01 fresh/stale launch and native window operations | Required | PASS | Both fresh and stale GUIs opened; title, move, resize, minimize, restore and close had no reported abnormality. |
| M-GUI-02 page navigation and layout stability | Required | FAIL | Page switching was basically usable, but elements visibly jumped on some pages, including Settings. The operator suspects the New Translation page scrollbar changes the layout width; this remains a hypothesis until isolated. |
| M-GUI-03 keyboard and focus | Required | NOT RUN | Explicitly skipped. |
| M-GUI-03 NVDA | Required | NOT RUN | Explicitly skipped. |
| M-GUI-04 display scaling/DPI | Required | NOT RUN | Explicitly skipped. |
| M-GUI-05 native file picker open/cancel and PDF select/load | Required | PASS | Picker opened and cancelled normally; a PDF could be selected and loaded. |
| M-GUI-05 native PDF drag-and-drop | Required | FAIL | Dragging a PDF into the drop zone did not load it. |
| M-GUI-06 sidecar cancellation/restart/reconnect lifecycle | Applicable | NOT RUN | No observation was supplied and no live translation was started. |
| Packaged stale-GUI error presentation | Required | FAIL | The stale GUI opened and behaved normally as reported, with no reported actionable stale/incompatible-sidecar error. This does not satisfy the stale-GUI presentation requirement. |

Manual sub-result summary: `PASS 2 / FAIL 3 / BLOCKED 0 / NOT RUN 4 / NOT APPLICABLE 0`. The earlier automated native-desktop rows remain `BLOCKED` as automation evidence; these manual results supersede the observation gap but do not turn an observed GUI failure into a pass. Overall status remains `WINDOWS_VERIFICATION_PENDING`.

### Failure analysis and Linux follow-up

- **Settings/page element jump — likely project UI/CSS issue, not yet proven.** The current layout uses a state-dependent document height and a flex `.app-shell`/`.workspace` arrangement (`gui/src/styles.css:42-73`); the scrollbar appearing on the taller New Translation view can change the available content width when navigating. Reproduce at a fixed window size and compare scrollbar presence before changing layout code. Candidate follow-up area: `gui/src/styles.css` and the view containers in `gui/src/App.tsx`.
- **Native PDF drag-and-drop — project/platform integration failure.** The drop handler is a DOM `onDrop` path (`gui/src/App.tsx:183-213`) and the browser-file adapter returns only `file.name` (`gui/src/filePicker.ts:28-31`). On Windows/Tauri, an OS file drop may not arrive as a browser `File` with a usable filesystem path, which is a likely reason the PDF was not loaded. Confirm the native event payload and preserve an absolute path before implementing a fix. Candidate follow-up area: `gui/src/App.tsx` and `gui/src/filePicker.ts`.
- **Stale-GUI presentation — project UI error-display gap.** The Tauri transport starts the sidecar and performs the handshake (`gui/src/sidecar.ts:21-37`); `JobStore.connect()` stores a failed connection and error (`gui/src/jobStore.ts:74-79`), but the main shell renders only a generic connection label and notice (`gui/src/App.tsx:154-169`). The old sidecar independently reproduced `TranslationConfig.__init__() got an unexpected keyword argument 'retry_policy'`, yet the manual GUI report did not include an actionable compatibility explanation. Candidate follow-up area: render the safe connection error and a rebuild/recovery action without exposing a traceback or secrets.

### Optional screenshot request

No screenshot is strictly required to retain these statuses. If available, the most useful evidence is: (1) stale GUI immediately after launch showing its connection/status area, (2) Settings and New Translation at the same window size showing the position jump, and (3) the drop zone before and after dragging the PDF. Exact text or a short screen recording is preferable to a general desktop screenshot.

The Linux follow-up is now to triage the three observed `FAIL` items, add regression coverage where practical, and schedule the skipped keyboard/NVDA/DPI checks separately. Do not alter the validation result by changing code solely to make this record pass.

## Manual GUI screenshot evidence update (2026-09-12)

The operator supplied three screenshots. All three were captured from the stale-GUI pair; no fresh-GUI screenshot was supplied. The images were copied into the E: validation pack and retained outside the WSL source tree.

| Evidence | Observation | Validation impact |
|---|---|---|
| [Figure 1](<E:\Shiraishi\VSCode Workspace\Codex_Translator\build\manual-gui-validation-20260912-152358\evidence\stale-gui-01-new-translation-starting.png>) | New Translation view; top banner shows `Starting sidecar`, right status shows `正在连接本地服务`; the lower-left local-first notice is not completely visible. The drop zone has its default appearance. | Confirms stale-GUI startup state is visible, but not yet an actionable compatibility explanation; supports the layout/visibility issue. |
| [Figure 2](<E:\Shiraishi\VSCode Workspace\Codex_Translator\build\manual-gui-validation-20260912-152358\evidence\stale-gui-02-new-translation-unavailable.png>) | New Translation view after startup failure; top banner shows `Sidecar unavailable`, right status shows `本地服务不可用`; the lower-left notice is still not completely visible. | Confirms a generic sidecar failure is surfaced. The stale-GUI criterion remains `FAIL` because the visible message does not explain the `retry_policy` incompatibility or give a rebuild/recovery action. |
| [Figure 3](<E:\Shiraishi\VSCode Workspace\Codex_Translator\build\manual-gui-validation-20260912-152358\evidence\stale-gui-03-settings-unavailable.png>) | Settings view; the right-side `本地服务不可用` indicator is in a different horizontal position, while the lower-left local-first notice is completely visible. | Confirms the state-dependent layout/scrollbar-width hypothesis as a reproducible visual symptom; M-GUI-02 remains `FAIL`. |

The operator additionally reports that the PDF drop zone looks the same before and after dragging a PDF, matching the default appearance in Figure 1, and no PDF is loaded. M-GUI-05 native drag-and-drop remains `FAIL`; file-picker selection/load remains `PASS`.

The screenshots strengthen the existing manual results but do not change the skipped keyboard/NVDA/DPI checks. No business-code change was made.

### Evidence hashes

- `stale-gui-01-new-translation-starting.png`: 210,206 bytes, SHA-256 `DA1E5277CFAF35A8AB6EAC539C4B9E036092763D38535D2BB416E14C9C500C66`
- `stale-gui-02-new-translation-unavailable.png`: 208,627 bytes, SHA-256 `7BB83A5A37A5D0EF2084F8ED843C54552674AED7DC45FFB07CB09174DE3906F9`
- `stale-gui-03-settings-unavailable.png`: 162,906 bytes, SHA-256 `36C0057940AF3FA689A4F60B74627615D054B03C28210F94DB48AE6BC3855C66`

## Validation run: 2026-09-12 (incremental continuation after interrupted validation)

### Scope and source state

- WSL source remained branch `dev`, HEAD `4e709d922849516c8162f5b17d387b32b5f42ceb`, with the same dirty working tree recorded above. A scoped SHA-256 recheck for the worker, CLI/QA, integration-test and validation-document inputs returned `TARGET_HASH_MISMATCHES=0`; the prior filtered WSL -> E: synchronization was therefore not repeated.
- Previously completed checks were intentionally skipped: dependency/lock, Ruff, compileall, Python full suite, doctor, GUI tests/build, Cargo/Tauri checks, PyInstaller build, frozen/target-triple handshake, fresh/stale bundle audit, NSIS/MSI build and release GUI process smoke remain covered by the immediately preceding current-source record. No Linux business code, dependency, architecture or configuration change occurred between the records.

### Incremental validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Subprocess mock integration revalidation | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py::TestMockEndToEnd::test_subprocess_mock_translation -vv --tb=short` | FAIL | Reproduced on current source: `RuntimeError: Translation failed after 1 attempts`; worker client reported a failed worker result. The earlier same-request environment diagnostic remains reproducible: the worker allowlist containing only available `PATH`/home-like variables omitted Windows runtime directory variables and returned `WinError 10106`; adding `SystemRoot`, `USERPROFILE`, `TEMP`, `TMP`, `APPDATA`, `LOCALAPPDATA` and `PROGRAMDATA` allowed the same request to complete. |
| QA CLI JSON contract revalidation | Required | `uv run pytest -q tests/test_cli.py::test_qa_cli_reports_passing_output --tb=short -vv` | FAIL | Reproduced: `JSONDecodeError` at `tests/test_cli.py:162`. The QA CLI writes the PyMuPDF warning `The fitz API is deprecated...` to stdout before the JSON document, so a machine consumer cannot parse the documented JSON output. |
| Corrected MSI administrative extraction | Applicable | Quoted `msiexec.exe /a "<MSI>" TARGETDIR="<extract>" /qn /norestart /L*v "<log>"` | PASS | Corrected rerun returned `MSIEXEC_EXIT=0`; verbose log was 84,202 bytes and both GUI/sidecar payloads were present. The preceding empty extraction was a command-argument validation-input issue, not product evidence. |
| MSI payload sidecar parity | Applicable | SHA-256 comparison of fresh `dist\\babelcodex-service.exe` and extracted `PFiles\\BabelCodex\\babelcodex-service.exe` | PASS | Fresh and extracted SHA-256 both `32D98B814C4DFA71DD1D2BCD5EF2662DDC0AFBFC239918B3CC80027D6EDB39FB`. |
| MSI-extracted sidecar protocol v1 | Required | Extracted sidecar with `get_server_info`, `list_jobs`, `shutdown`, `protocol_version=1` and `config/example.toml` | PASS | Protocol 1, package `0.1.0`, expected capabilities, preserved E: state visible, and clean shutdown exit 0. |
| MSI-extracted GUI process smoke | Applicable | Start extracted `babelcodex-gui.exe`, wait 8 seconds, stop only the validation process | PASS | Process remained alive after 8 seconds and was then stopped by PID. |
| Native GUI interaction, clean-user, WVQ-007 lifecycle, release security and live Codex/PDF | Required / Applicable | Existing queue procedures | NOT RUN | Intentionally not repeated in this incremental run; prior manual GUI observations and the outstanding authorization/environment prerequisites remain authoritative. |

### Failure and blocking analysis

- **Worker subprocess - FAIL; likely category: Windows-specific project code.** `src/codex_babeldoc/backends/worker_client.py` constructs a restricted child environment that is too small for Windows Python/BabelDOC runtime initialization. The missing Windows runtime/profile variables cause a reproducible worker failure (`WinError 10106` in the minimal environment, followed by a home-directory error when only `SystemRoot` is restored). This blocks the Windows subprocess mock integration and dependent worker-based cancellation/reconnection/recovery acceptance. Linux follow-up: revise the Windows-safe environment allowlist and add a regression test that launches the worker with the intended restricted environment.
- **QA CLI stdout contamination - FAIL; likely category: project CLI/dependency integration.** The QA result body is correct when invoked directly (`qa_status=passed`/`failed` and exit 0/1), but the PyMuPDF `fitz` deprecation warning precedes stdout JSON. Linux follow-up: keep stdout machine-readable and route dependency warnings to stderr or replace the deprecated import path; add a clean-subprocess JSON parsing regression test.
- **MSI extraction - no product failure.** The first invocation produced no payload because the path-with-spaces arguments were not quoted correctly. The documented quoted invocation was then executed and passed; this correction did not alter source or package inputs.

### Incremental result summary

- New evidence in this continuation: `PASS 4`, `FAIL 2`, `BLOCKED 0`.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`; the two current `FAIL` items require Linux follow-up and Windows revalidation. No status was promoted to `WINDOWS_PASS`.

### Linux follow-up required

1. Fix and test the Windows worker environment allowlist in `src/codex_babeldoc/backends/worker_client.py`; rerun `WVQ-007`-related worker subprocess, cancellation, reconnection and recovery checks.
2. Fix the QA CLI stdout/stderr contract around the PyMuPDF deprecation warning; rerun the QA CLI positive/tamper checks and the JSON regression.
3. After Linux regression checks pass, repeat the Windows subprocess integration and QA CLI checks; retain the MSI parity evidence from this continuation.

## Linux follow-up completed (2026-09-12) and Windows revalidation queue

This section records the Linux work requested by the incremental 2026-09-12 run above. Both `FAIL` items were addressed and closed on the Linux side; the native Windows revalidation remains queued.

### Worker environment allowlist fix

`src/codex_babeldoc/backends/worker_client.py` now exposes a single testable builder `worker_environment(env_extra=None)` instead of an inline comprehension. The allowlist retains:

- POSIX runtime keys: `PATH`, `HOME`, `USER`, `TMPDIR`, `LANG`, `LC_ALL`;
- Windows runtime/profile keys: `SYSTEMROOT`, `USERPROFILE`, `TEMP`, `TMP`, `APPDATA`, `LOCALAPPDATA`, `PROGRAMDATA` — the full set named by the 2026-09-12 diagnosis (`SystemRoot`, `USERPROFILE`, `TEMP`, `TMP`, `APPDATA`, `LOCALAPPDATA`, `PROGRAMDATA`).

Missing allowlist keys are skipped, so the same code is safe on POSIX (no Windows keys) and Windows (no POSIX keys), and `env_extra` always wins for explicit caller overrides. New regression coverage in `tests/test_worker.py::TestWorkerEnvironment`:

- Windows runtime keys are preserved when present in the parent environment;
- POSIX keys are preserved when present;
- `env_extra` overrides the allowlist;
- `run_worker` passes only the allowlisted keys (plus overrides) to `Popen`, never unrelated parent variables such as a `BABELCODEX_TEST_SECRET`.

### QA CLI stdout contamination fix

The PyMuPDF deprecation notice is emitted by the legacy `fitz` compatibility shim directly to **stdout** via a print, so `-W` filters cannot suppress it and a machine consumer sees `warning: The fitz API is deprecated...` before the JSON document. All production and test modules that used PyMuPDF now import the official `pymupdf` package instead:

- `src/codex_babeldoc/qa/pdf_sanity.py`, `src/codex_babeldoc/qa/text_checks.py`, `src/codex_babeldoc/qa/layout_checks.py`;
- `src/codex_babeldoc/core/pipeline_meta.py`, `src/codex_babeldoc/translation/context.py`;
- matching fixtures in `tests/test_*.py`.

New regression `tests/test_cli.py::test_qa_cli_stdout_is_machine_readable_in_clean_subprocess` launches the CLI (`python -m codex_babeldoc.cli qa`) from a fresh interpreter with a clean `PYTHONPATH` and asserts `returncode == 0` and the entire stdout payload parses as one JSON document with `ok == true`.

### Linux verification results (current working tree)

| Check | Result |
|---|---|
| `python -m compileall -q src tests` | PASS |
| `uv run ruff check` (affected files) | PASS |
| `uv run ruff format --check` (affected files) | PASS |
| Python unit/default suite | 206 passed, 5 deselected (includes new `TestWorkerEnvironment` + clean-subprocess QA JSON regression) |
| GUI Vitest | 22 passed |
| GUI Vite production build | PASS |
| Mock PDF integration (`-m integration tests/test_e2e_mock.py`) | 5 passed, 10 warnings |

No dependency, configuration or architecture change was introduced by these fixes; they are code + regression-test changes only.

### Windows revalidation queue for this round

- `WVQ-014` — run the Windows subprocess mock integration and worker-based mock job with the allowlisted environment; confirm the worker starts, completes, supports cancellation/reconnection and does not inherit unrelated parent variables.
- `WVQ-015` — run `cbpdf qa` positive/tamper and `cbpdf doctor`/`validate` in a clean Windows interpreter subprocess; assert stdout is a single parseable JSON document with no PyMuPDF deprecation noise.

Both remain `WINDOWS_VERIFICATION_PENDING` until executed natively. Neither blocks further Linux development; no item was promoted to `WINDOWS_PASS` by this Linux work.

## Validation run: 2026-09-13 (current Linux HEAD, worker and package revalidation)

### Validation environment and source state

- WSL source of truth: `W:\home\shiraishi\VSCode Workspace\Codex_Translator`, branch `dev`, HEAD `14b4856bf37cf06674b6319da8f0ab6451728348` (`docs: fill codebase-map descriptions, fix worker process location`, 2026-09-13 15:02:16 +08:00). The working tree remained dirty only by the pre-existing mode-only change to `scripts/build_linux_gui_bundle.sh`; this is a working-tree validation, not a clean-commit validation. Since the prior 2026-09-12 source, the tree includes the worker facade/process-location change, QA and documentation-inventory checks, sidecar/MCP contracts, GUI protocol/capability updates and related tests.
- Before synchronization, the E: disposable workspace was inspected. Filtered one-way `robocopy` from `\\wsl.localhost\Ubuntu\home\shiraishi\VSCode Workspace\Codex_Translator` to `E:\Shiraishi\VSCode Workspace\Codex_Translator` used `/E /FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ /R:0 /W:0`, excluding `.git`, `.venv`, `.pytest_cache`, `.ruff_cache`, `.babelcodex-codex`, `gui\node_modules`, Rust target, `build`, `dist`, `gui\dist`, logs, state, incoming/translated/glossary/context user-content directories, and `*.pdf/*.log/*.pyc/*.db/*.sqlite/*.sqlite3`. Dry-run and actual sync each reported 87 controlled files, 0 failed files; 17 E: extra files and 3 extra directories were preserved. No E: code or generated output was synchronized back to WSL.
- SHA-256 parity after synchronization was `SELECTED_HASH_MISMATCHES=0` for 40 selected current source, test, configuration and validation-control files. E: `.venv`, `gui\node_modules`, Rust target, build/dist, state/logs, user-content directories and prior generated validation assets remained present. The target-triple sidecar was refreshed only as a generated E: packaging input.
- Windows 11 Professional Workstation Insider Preview `10.0.29661.1000`, AMD64; Visual Studio Build Tools `17.14.40` (`17.14.37628.2`); WebView2 `152.0.4191.66`; `uv 0.12.10`; project Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; BabelDOC `0.6.4`; openai-codex `0.147.0`; PyInstaller `6.22.3`. `doctor` reported authenticated ChatGPT state, but no usage-bearing live request was made.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy` and selected SHA-256 comparison | PASS | 87 controlled files copied, 0 failed; 17 extra files and 3 extra directories preserved; selected hashes matched. |
| Dependency synchronization | Required | `uv sync --locked --extra runtime --extra dev` | PASS | 95 packages resolved, 91 checked. |
| Lock validation | Required | `uv lock --check` | PASS | Lock resolved successfully. |
| Python format | Required | `uv run ruff format --check .` | PASS | 100 files already formatted. |
| Python lint | Required | `uv run ruff check .` | PASS | All checks passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Documentation inventory tests | Required | `uv run pytest -q tests/test_docs_inventory.py` | FAIL | `14 passed, 1 failed`; `test_check_without_map_reports_missing_file` expected `/` but Windows returned `docs\\development\\codebase-map.md`. |
| Documentation inventory CLI | Required | `uv run python scripts/check_docs_inventory.py` | PASS | `docs inventory check passed`, exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | FAIL | `220 passed, 1 failed, 5 deselected in 70.00s`; the only failure was the documentation-inventory path-separator assertion above. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex runtime and configured paths detected; `codex_authenticated=true`, `Logged in using ChatGPT`. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; full tree reported 2 moderate advisories and an esbuild pending install-script warning. |
| Production dependency advisory read | Applicable | `npm.cmd --prefix gui audit --omit=dev` | PASS | 0 production vulnerabilities; no remediation was run. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 9 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Windows release host dependencies compiled/check passed. |
| Tauri config, capability and icons | Required | Parse `gui/src-tauri/tauri.conf.json` and `capabilities/default.json`; check `icon.ico`/`icon.png` | PASS | JSON valid; `productName=BabelCodex`; 5 capability permissions; both icons exist. |
| Mock PDF integration | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py --tb=short` | PASS | `5 passed in 218.20s`; local scripted/mock path only, no paid usage. |
| QA CLI positive and artifact tamper detection | Required | Temporary mock job; `uv run cbpdf --config <temp-config> qa <job-id>`; remove the output artifact and rerun | PASS | Good run exit 0/`ok=true`/`qa_status=passed`; tampered run exit 1/`ok=false`/`qa_status=failed`; one report each. |
| QA fixture cleanup | Applicable | Remove the same temporary QA directory after both CLI runs | PASS | Cleanup completed without a Windows file-lock error. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | `dist\\babelcodex-service.exe`, 194,468,829 bytes, SHA-256 `2416E557906C9DB4218D80CFB535D57762553C0C5B66A7B71ABE5F080C3C4ABF`. |
| Frozen sidecar protocol v1 | Required | Frozen exe JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Protocol 1, package `0.1.0`, 11 capabilities, 2 preserved E: jobs visible, exit 0. |
| Frozen invalid worker request | Required | `dist\\babelcodex-service.exe --worker-request build\\missing-worker-request-validation-20260913-153320.json` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Frozen worker valid mock request | Required | Frozen exe `--worker-request` with `tests\\fixtures\\fixture_two_column.pdf` and `mock` translator | FAIL | Process returned structured `BABELDOC_RUNTIME_ERROR`, exit 3: `No module named 'bitstring.bitstore_bitarray'`. The normal project Python import succeeds; this is a frozen-runtime packaging dependency failure. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui\\src-tauri\\binaries\\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | Fresh and target-triple hashes matched; handshake/list/shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | `uv run python scripts/check_gui_bundle.py <fresh-stage> --target x86_64-pc-windows-msvc --source-tree . --manifest <stage>\\sha256.txt` | PASS | Current HTML/JS/CSS and both fresh sidecar names passed; exit 0. |
| WVQ-009 stale bundle negative audit | Required | Same audit with preserved 2026-09-10 sidecar SHA-256 `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A` | PASS | Expected audit exit 1 with `sidecar predates newer Python sources`; stale input rejected. |
| Current-source NSIS/MSI build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 195,799,129 bytes, SHA-256 `896EBFD1660A44DA672A92233DFCA06A61E1879343464D2F93AAA5D89B97765E`; MSI 195,768,320 bytes, SHA-256 `42B5CFAB2ED7A0E58108A1D9A900477950DF55098D8E3683A6360A9DF7F7E9F6`. |
| Current release GUI process smoke | Applicable | Start `gui\\src-tauri\\target\\release\\babelcodex-gui.exe`, wait 8s, stop only validation process | PASS | Process remained alive for 8s; exited after stop. GUI SHA-256 `E9ADCDCAFCF091419E68FBCB0710B21F3B391E1DA946D33889C91E891A41810B`, 4,597,248 bytes. |
| MSI administrative extraction and parity | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads and hashes | PASS | Exit 0; 83,274-byte log; GUI and sidecar payloads present; extracted sidecar hash matched fresh sidecar. |
| MSI-extracted sidecar protocol v1 | Required | Extracted `PFiles\\BabelCodex\\babelcodex-service.exe` with v1 `get_server_info`/`list_jobs`/`shutdown` | PASS | Protocol 1, package `0.1.0`, 11 capabilities, 2 jobs visible, exit 0. |
| MSI-extracted GUI process smoke | Applicable | Start extracted `PFiles\\BabelCodex\\babelcodex-gui.exe`, wait 8s, stop validation process and its package child | PASS | Process remained alive for 8s; package sidecar child was cleaned and no BabelCodex validation process remained. |
| Packaged stale-GUI error observation | Required | Launch current GUI with preserved stale sidecar and observe native connection error | BLOCKED | `COMPUTER_USE_UNAVAILABLE`: the computer-use initialization returned `helper_unknown_error: setup refresh had errors`; no native UI action or current-source stale-GUI observation was obtained. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Installed/portable picker, Chinese rendering, keyboard, DPI 125%/150%/200%, NVDA, allowlist, Unicode/path-space/permissions, cancellation and reconnection | BLOCKED | Same unavailable desktop-control prerequisite; process smoke, DOM tests and bundle checks are narrower evidence only. |
| Clean-user installation and first launch | Required | Isolated Windows user/profile installation and first launch | NOT RUN | No disposable clean-user profile was entered. |
| WVQ-007 work-dir cleanup/lock/retry/cancel/reconnect semantics | Applicable | Native Windows lifecycle and file-handle matrix | NOT RUN | The isolated QA temp-directory cleanup passed, but the broader semantic matrix was not run. |
| WVQ-005 Defender/SmartScreen/signing/SBOM/release audit | Applicable | Formal release-security workflow | NOT RUN | Development artifacts are unsigned; no security-setting or release-signing workflow was authorized. |
| Live Codex/PDF integration | Applicable | Authorized live translation fixture | NOT RUN | No usage-bearing request was authorized; mock integration is not live acceptance. |
| Dependency advisory remediation | Applicable | `npm audit fix` or dependency upgrade | NOT RUN | Outside validation and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Requires a target Linux machine. |

### Failure, blocking and follow-up analysis

- The documentation-inventory test failure is a Windows test portability defect at `tests/test_docs_inventory.py:145`: the expected diagnostic uses POSIX separators while the implementation returns the native `Path` representation. The CLI inventory command itself passed. Linux should make this assertion platform-independent, add/retain a Windows regression, and rerun the full suite; no validation-only change was made.
- The full Python suite has no additional failure beyond that same assertion (`220 passed, 1 failed, 5 deselected`). This is a real current-source `FAIL`, not a prerequisite omission, but it did not prevent independent GUI, Tauri, sidecar or packaging checks from running.
- The valid frozen worker failure is a current packaging/runtime `FAIL`: `bitstring.bitstore_bitarray` imports successfully from the project `.venv`, while the fresh PyInstaller worker returned `BABELDOC_RUNTIME_ERROR`/exit 3. The likely owner is dynamic dependency collection in `scripts/babelcodex-service.spec` (the current `collect_all("babeldoc")` path did not make this runtime module available). Linux should investigate explicit hidden-import or submodule collection, add a frozen-worker regression, rebuild on Linux, and schedule Windows revalidation. No spec or business-code change was made here.
- The stale bundle audit's exit 1 is a successful negative test (`PASS`): it rejected the preserved older sidecar with `sidecar predates newer Python sources`. The first GUI smoke wrapper had a PowerShell output-capture defect, so it was not used as evidence; corrected direct probes passed current and MSI-extracted process smoke. This wrapper issue is not a product result.
- Native GUI/stale-GUI rows are `BLOCKED`, not `FAIL`: the permitted computer-use fallback was initialized only to diagnose the desktop capability and returned `helper_unknown_error: setup refresh had errors`; no clicks, typing or native UI conclusion was made. Previous 2026-09-12 human GUI observations are not reused as current-source acceptance evidence because the GUI/sidecar code changed after that source state.
- No check was `BLOCKED` by dependencies, credentials or external services outside the two desktop-control rows. `doctor` authentication is recorded as environment evidence only; no live Codex/PDF request was started.

### End-of-validation result summary

- `PASS 29 / FAIL 3 / BLOCKED 2 / NOT RUN 5 / NOT APPLICABLE 1`.
- Automated PASS coverage includes synchronization/parity, locked dependencies, Ruff/compileall, QA CLI/tamper, mock PDF integration, GUI tests/build, Tauri checks, frozen sidecar protocol, invalid-worker path, target-triple handshake, fresh/stale freshness audit, NSIS/MSI, extraction parity and GUI process smokes.
- Current overall status remains `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_VERIFICATION_BLOCKING`: the documentation and frozen-worker Linux follow-ups are complete, but their repaired source still requires native Windows revalidation; native desktop, clean-user, WVQ-007, release-security and live-usage gaps also remain outside this validation run.

### Linux follow-up disposition

1. **Completed on Linux:** normalized the documentation-inventory path assertion across host separators, added a Windows-style separator regression, and reran the Python/doc gates.
2. **Completed on Linux:** expanded frozen-sidecar collection for `bitstring`, `tiktoken`, and `tiktoken_ext`, removed unsafe standard-library exclusions, added a spec regression, rebuilt the sidecar, and completed a frozen mock worker request with exit 0 and mono/dual artifacts.
3. **Pending on Windows:** synchronize the repaired source and rerun the valid frozen-worker request plus the dependent `WVQ-009` freshness/handshake, target-triple, NSIS/MSI and extracted-sidecar gates. These remain `WINDOWS_VERIFICATION_PENDING`; Linux success must not be promoted to `WINDOWS_PASS`.
4. **Still pending on Windows:** provision usable native desktop automation and run the remaining `WVQ-001` through `WVQ-004` and stale-GUI checks, including DPI, NVDA, picker/allowlist, Unicode/path-space/permissions, cancellation, reconnection and window lifecycle.
5. **Still pending on Windows:** run the broader `WVQ-007` lifecycle matrix, clean-user first launch, and separately authorized `WVQ-005` release-security and live Codex/PDF workflows. Do not remediate npm advisories automatically during validation.

### Final review

- WSL source remained unchanged by validation except for its pre-existing mode-only script diff; `git diff --check` passed. E: was the disposable validation target, and only generated E: build/state/log/process artifacts were created or refreshed.
- The final source state was rechecked as `dev`/HEAD `14b4856`; no business code, dependency, architecture, configuration or lockfile was modified. Only this validation record and its matching Linux summaries are eligible for write-back.

### Linux reconciliation after this Windows run (2026-09-13)

- The two actionable Linux follow-ups from this run were implemented and verified without changing dependencies or architecture. The inventory check now normalizes host-specific separators, with a regression test simulating Windows-style paths. The PyInstaller spec now collects `bitstring` submodules, `tiktoken`, and `tiktoken_ext`, and no longer excludes dynamically imported standard-library modules.
- Linux verification passed: default Python suite `223 passed, 5 deselected`; focused documentation-inventory/worker suite `39 passed`; Ruff check and format; compileall; documentation-inventory CLI; GUI Vitest `22 passed`; GUI TypeScript/Vite build; and Linux PyInstaller build. A Linux frozen worker mock request completed with exit 0 and generated both mono and dual PDF artifacts.
- These results do not rewrite the Windows checklist: the original Windows documentation-inventory and frozen-worker rows remain historical `FAIL` evidence for the 2026-09-13 source. The repaired source must be synchronized and rerun natively before those Windows checks can become `PASS`; their current handoff state is `WINDOWS_VERIFICATION_PENDING`.
- The next Windows phase should rerun the frozen worker valid-mock request and dependent package gates (`WVQ-009` freshness/handshake, target-triple, NSIS/MSI and extracted sidecar), then separately execute the remaining native GUI/path/lifecycle, clean-user, release-security and authorized live Codex/PDF checks. Existing `BLOCKED`, `NOT RUN`, `NOT APPLICABLE` and limited manual `PASS` classifications remain unchanged.

### Current operator disposition (2026-09-13)

- `WIN-MANUAL-003 / WVQ-002` — `NOT RUN`.
- Reason: explicitly skipped at the user's request; no DPI, NVDA or window-lifecycle test was executed in this round.
- Blocker: none; disposition marker `SKIPPED_BY_USER_REQUEST`.
- This updates the current manual queue disposition only. Historical validation rows and the automated result summary are preserved unchanged.
- This disposition supersedes the earlier `BLOCKED` placeholder for this item in the current manual queue; it does not claim a test result.

### Current operator evidence (2026-09-13, WVQ-003)

- `WIN-MANUAL-004 / WVQ-003` — `BLOCKED`.
- Operator-provided diagnostic screenshot shows the packaged GUI with `本地服务不可用`, the banner `Sidecar unavailable`, `本地服务协议: failed`, and `Codex 会话: 尚未检查`; the `重新连接` action is visible.
- Blocker: `PACKAGED_SIDECAR_STARTUP_FAILED`.
- The screenshot is direct evidence of the packaged GUI's fail-closed state, but it does not establish a successful sidecar session. Therefore the service-dependent WVQ-003 checks were not completed: allowed/denied-path job submission, Unicode/space path round trips, cancellation, reconnection, active-PID protection, permission-restricted operation, and missing/tampered-artifact validation through the GUI.
- Existing packaged-sidecar diagnosis remains applicable: the extracted package sidecar exited before the protocol handshake because `config/example.toml` was missing from the package working directory. The GUI currently collapses the underlying startup error into the generic `Sidecar unavailable` notice, so the screenshot is `BLOCKED` evidence, not `PASS` or a product acceptance result.
- This current evidence supersedes the earlier `COMPUTER_USE_UNAVAILABLE` placeholder for the active manual item. Historical validation rows and the automated result summary remain unchanged.
- Linux follow-up: repair the packaged sidecar config/runtime-path contract, expose a safe actionable startup/recovery explanation, rebuild the Windows package, and rerun `WVQ-003` end to end. No business-code change was made during this documentation update.

### Current operator result update (2026-09-13, WVQ-001 and WIN-MANUAL-001)

- `WIN-MANUAL-001` — `BLOCKED`.
- Evidence: the operator launched the stale-GUI variant and observed `本地服务不可用` plus the banner `Sidecar unavailable`; no lingering process remained after the GUI was stopped. The reported SHA-256 values were GUI `6FC9F69FEEE226A8149D2D231780EF29F79A36431591B6A115A0343932EDD758` and stale packaged sidecar `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`.
- Blocker: `PACKAGED_SIDECAR_STARTUP_FAILED`. The packaged sidecar exited before the protocol handshake because `config/example.toml` was missing from the packaged working directory. The GUI therefore showed a generic fail-closed notice, but the intended actionable stale/incompatible-handshake path was not completed.
- `WIN-MANUAL-002 / WVQ-001` — `PASS`.
- Evidence: the operator confirmed that the packaged GUI's Chinese labels/display and keyboard operations were normal. The supplied screenshot shows the navigation, page title, status text, form labels and action controls rendered and usable, with no reported clipping, overlap or keyboard-navigation failure.
- Scope note: this `PASS` is limited to the manually observed Chinese rendering and keyboard flow. It does not claim that the sidecar or live translation path is healthy; the separate sidecar failure remains recorded under `WIN-MANUAL-001` and `WVQ-003`.
- These current manual results supersede the earlier `NOT_RUN` placeholders only. Automated `BLOCKED` rows, historical records and the overall automated result summary remain unchanged. No business-code change was made.

## Validation run: 2026-09-13 (current Linux HEAD, repaired worker/package gates)

### Validation environment and source state

- Linux/WSL source of truth: `dev`, HEAD `62f23d9e26b0a76e02482fa6e1b9ab192b64446b` (`fix: harden cross-platform inventory and frozen worker packaging`, 2026-09-13 20:09:40 +08:00). The working tree was dirty only by the pre-existing mode-only change to `scripts/build_linux_gui_bundle.sh`; this was a working-tree validation, not a clean-commit validation.
- The disposable E: target was inspected before synchronization. Filtered Linux → Windows `robocopy` used `/E /FFT /COPY:DAT /DCOPY:DAT /IS /IT /XJ /R:0 /W:0`, excluding `.git`, `.venv`, Python/GUI/Rust caches and dependencies, build/dist output, state/log/user-content directories, and `*.pdf/*.log/*.pyc/*.db/*.sqlite/*.sqlite3`. Dry-run and actual sync reported 87 controlled files, 0 failed files; 17 extra files and 4 extra directories on E: were preserved. No E: code or generated output was synchronized back to Linux.
- SHA-256 parity for 13 selected current source, test, configuration and validation-control files was `SELECTED_HASH_MISMATCHES=0`, `SELECTED_HASH_MISSING=0`.
- Windows environment: Windows 11 `10.0.29667` AMD64; `uv 0.12.10`; Python `3.12.13`; Node.js `24.19.0`; npm `11.17.0`; Rust/cargo `1.98.0`; BabelDOC `0.6.4`; openai-codex `0.147.0`; PyInstaller `6.22.3`. `doctor` reported `codex_authenticated=true`, but no usage-bearing live request was made.
- Native desktop prerequisite probe returned no targetable native apps, and the Computer Use trusted RPC reported `Trusted RPC service is not configured: sky`. No native GUI input action was performed in this run.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Controlled WSL-to-E synchronization and source parity | Required | Filtered `robocopy` and selected SHA-256 comparison | PASS | 87 controlled files copied, 0 failed; 17 extra files and 4 extra directories preserved; 13 selected hashes matched. |
| Dependency synchronization | Required | `uv sync --locked --extra runtime --extra dev` | PASS | 95 packages resolved, 91 checked. |
| Lock validation | Required | `uv lock --check` | PASS | Lock resolved successfully. |
| Python format | Required | `uv run ruff format --check .` | PASS | 100 files already formatted. |
| Python lint | Required | `uv run ruff check .` | PASS | All checks passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Documentation inventory tests | Required | `uv run pytest -q tests/test_docs_inventory.py --tb=short` | FAIL | `15 passed, 1 failed`; `test_check_without_map_reports_missing_file` expected `/` but Windows returned `docs\\development\\codebase-map.md`. |
| Documentation inventory CLI | Required | `uv run python scripts/check_docs_inventory.py` | PASS | `docs inventory check passed`, exit 0. |
| Python test suite | Required | `uv run pytest -q --tb=short` | FAIL | `222 passed, 1 failed, 5 deselected in 41.01s`; the only failure was the same documentation-inventory path assertion. |
| Runtime doctor | Required | `uv run cbpdf --config config/example.toml doctor` | PASS | Python/BabelDOC/Codex runtime and configured paths detected; authenticated state was observed but not used. |
| GUI dependency install | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; full tree reported 2 moderate advisories and one pending esbuild install-script approval. |
| Production dependency advisory read | Applicable | `npm.cmd --prefix gui audit --omit=dev` | PASS | 0 production vulnerabilities; no remediation was run. |
| GUI full tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 4 files, 22 tests passed. |
| GUI focused store tests | Applicable | `npm.cmd --prefix gui test -- --run src/jobStore.test.ts` | PASS | 9 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust host | Required | `cargo check --manifest-path gui/src-tauri/Cargo.toml` | PASS | Windows release host check passed. |
| Tauri config, capability and icons | Required | Parse `gui/src-tauri/tauri.conf.json` and `capabilities/default.json`; check `icon.ico`/`icon.png` | PASS | `productName=BabelCodex`; 5 capability permissions; both icons exist. |
| Mock PDF integration | Required | `uv run pytest -q -m integration tests/test_e2e_mock.py --tb=short` | PASS | `5 passed in 239.94s`; local scripted/mock path only, no paid usage. |
| QA positive and artifact tamper detection | Required | Isolated mock job; `uv run cbpdf --config <temp-config> qa <job-id>`; remove the mono output and rerun | PASS | Positive `exit 0 / ok=true / qa_status=passed` with mono/dual reports; tampered `exit 1 / ok=false / qa_status=failed`. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | `dist\\babelcodex-service.exe`, 195,132,280 bytes, SHA-256 `711431851D5852E5DD4D8E2D10D706460CB7FCE177D12CEFFA2AD826D98F4FCB`. |
| Frozen sidecar protocol v1 | Required | Frozen exe JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | Three structured responses, all `ok=true`, exit 0, no stderr output. |
| Frozen invalid worker request | Required | `dist\\babelcodex-service.exe --worker-request <missing-request>` | PASS | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Frozen worker valid mock request | Required | Frozen exe `--worker-request` with `fixture_two_column.pdf` and `mock` translator | PASS | Exit 0, `status=completed`, two PDF artifacts generated, BabelDOC `0.6.4`; worker progress remained on stderr. |
| Windows target-triple sidecar | Required | Copy fresh sidecar to `gui\\src-tauri\\binaries\\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | Fresh and target-triple SHA-256 both `711431851D5852E5DD4D8E2D10D706460CB7FCE177D12CEFFA2AD826D98F4FCB`; handshake/list/shutdown exit 0. |
| WVQ-009 fresh bundle audit | Required | `uv run python scripts/check_gui_bundle.py <fresh-stage> --target x86_64-pc-windows-msvc --source-tree . --manifest <stage>\\sha256.txt` | PASS | Current HTML/JS/CSS and fresh target sidecar passed. |
| WVQ-009 stale bundle negative audit | Required | Same audit with preserved `windows-validation-staging-20260913-stale` sidecar | PASS | Expected audit exit 1 with `sidecar predates newer Python sources`; stale input was rejected. |
| Current release GUI process smoke | Applicable | Start `gui\\src-tauri\\target\\release\\babelcodex-gui.exe`, wait 8 seconds, stop only validation PID | PASS | Process remained alive for 8 seconds; PID was cleaned. GUI SHA-256 `07B3D78227522C3E4A776C49057D2CF29086CE90A02FD5C61714FA6BCA4B938A`. |
| Current NSIS/MSI bundle build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 196,464,931 bytes, SHA-256 `1CB4511E6FC5CF25213C7BA1983E1FC138EF2C7E64AFB8236061F9FB43EAB4B2`; MSI 196,431,872 bytes, SHA-256 `19778F968DB0EAB107494A1163F698D4D5E4206BBC1C69C3A40772206D95D712`. |
| MSI administrative extraction and parity | Applicable | `msiexec /a <MSI> TARGETDIR=<temp> /qn /norestart /L*v <log>`; inspect payloads and hashes | PASS | Exit 0; extraction log 84,424 bytes; GUI and sidecar payloads present; extracted sidecar matched fresh SHA-256. |
| MSI-extracted sidecar protocol v1 | Required | Extracted sidecar with absolute example config and v1 `get_server_info`/`list_jobs`/`shutdown` | PASS | Three responses, all `ok=true`, exit 0, no stderr output. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8 seconds, stop only validation PID | PASS | Process remained alive for 8 seconds and was cleaned. |
| Packaged stale-GUI error observation | Required | Launch current GUI with stale sidecar and observe native connection error | BLOCKED | No targetable native app/trusted RPC; no current-source stale-GUI observation was claimed. Existing `PACKAGED_SIDECAR_STARTUP_FAILED` operator evidence remains historical/current queue evidence. |
| Packaged GUI interaction/path/DPI/NVDA matrix | Required | Picker, Unicode/space paths, permissions, cancellation/reconnection, DPI and NVDA matrix | BLOCKED | Native Computer Use prerequisite unavailable; process smoke and DOM tests are narrower evidence only. |
| Clean-user installation and first launch | Required | Isolated Windows user/profile installation and first launch | NOT RUN | No disposable clean-user profile was entered. |
| WVQ-007 work-dir cleanup/lock/retry/cancel/reconnect semantics | Applicable | Native Windows lifecycle and file-handle matrix | NOT RUN | The isolated mock/QA path passed, but the broader lifecycle and lock matrix was not run. |
| WVQ-005 Defender/SmartScreen/signing/SBOM/release audit | Applicable | Formal release-security workflow | NOT RUN | Artifacts are unsigned development packages; no release-security workflow was authorized. |
| Live Codex/PDF integration | Applicable | Authorized live translation fixture | NOT RUN | No usage-bearing request was authorized; mock integration is not live acceptance. |
| Dependency advisory remediation | Applicable | `npm audit fix` or dependency upgrade | NOT RUN | Outside validation scope and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Requires a target Linux machine. |

### Failure, blocking and follow-up analysis

- The only current code/test failure is the Windows path-separator assertion at `tests/test_docs_inventory.py:145`. `scripts/check_docs_inventory.py:174` formats the `MAP_REL` `Path` object directly, so the diagnostic uses the host separator on Windows. The existing Windows-style regression covers `_managed_files()` but not this `check()` diagnostic. Linux should normalize this return value with a POSIX representation or make the assertion platform-independent, add a regression for the `check()` result, and rerun the Linux and Windows Python gates.
- The full-suite `FAIL` is not an additional defect: it is the same documentation-inventory assertion (`222 passed, 1 failed, 5 deselected`). No worker, GUI, package or mock-PDF failure was observed in this run.
- The previous frozen-worker packaging failure (`bitstring.bitstore_bitarray`) did not reproduce after synchronization: the fresh Windows frozen worker completed the valid mock request with exit 0 and generated both artifacts. Fresh/stale freshness, target-triple, NSIS/MSI, extraction parity and extracted-sidecar handshake also passed.
- The first QA harness attempt merged stderr logs with stdout and used an invalid assumed job ID; it was corrected by reading the generated state file and rerunning with separated streams. The corrected product checks passed and the CLI stdout files contained parseable JSON without the prior PyMuPDF warning.
- Native GUI/stale-GUI rows are `BLOCKED`, not `FAIL`: the permitted Computer Use surface exposed no native apps and the trusted RPC service was not configured. No UI action or stale-GUI conclusion was inferred from process smoke, DOM tests or bundle audit.

### End-of-validation result summary

- Checklist counts: `PASS 29 / FAIL 2 / BLOCKED 2 / NOT RUN 5 / NOT APPLICABLE 1`.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`, not `WINDOWS_VERIFICATION_BLOCKING`: the fresh worker/package gates are now Windows-verified, but the documentation-inventory portability defect and native desktop/clean-user/lifecycle/release/live-service gaps remain.
- No business code, dependency, architecture, configuration or lockfile was modified for validation. E: received only validation-local dependencies, caches, state/logs and generated build/package artifacts; Linux remains the source of truth.

### Linux follow-up required

1. Fix and regression-test the Windows-stable documentation-inventory diagnostic (`scripts/check_docs_inventory.py:174` / `tests/test_docs_inventory.py:145`), then rerun the Linux suite and this Windows Python gate.
2. Provision the Computer Use trusted RPC/native desktop automation and complete the stale-GUI, picker/allowlist, Unicode/path-space/permissions, cancellation, reconnection, DPI/NVDA and window-lifecycle items in `WVQ-001`–`WVQ-004`/`WVQ-009`.
3. Separately run the full `WVQ-007` work-dir/lock/retry/cancel/reconnect matrix and clean-user first launch; schedule `WVQ-005` release-security and authorized live Codex/PDF validation without auto-remediating npm advisories.

### Current operator result update (2026-09-13, manual GUI and bundle audit)

- `WIN-MANUAL-002 / WVQ-001` — `PASS` for the observed current Release GUI
  connection state and basic Chinese UI rendering. The operator reports that
  the GUI correctly displayed `本地服务已连接`; the supplied screenshot also
  shows the green status indicator and `Sidecar handshake ready` banner. This
  is direct desktop evidence for the visible connection/handshake state and
  basic rendering, not evidence for the unexecuted DPI/NVDA or full picker,
  path, cancellation and reconnection matrix.
- `WIN-MANUAL-001 / WVQ-009` — `PASS` for the stale-sidecar startup rejection
  observed in the manual stale-GUI copy. The operator reports that it correctly
  displayed `本地服务不可用`; the supplied screenshot shows the
  `Sidecar unavailable` banner. The GUI did not falsely present a healthy
  connection. This result covers the visible fail-closed startup behavior; it
  does not claim that the generic message identifies the exact stale binary
  cause or that a complete translation attempt was made.
- `WVQ-009` fresh bundle audit — `PASS`. The operator reran:
  `uv run python scripts/check_gui_bundle.py <stage> --target
  x86_64-pc-windows-msvc --source-tree . --manifest <stage>\sha256.txt`.
  The audit reported `GUI bundle audit passed` for
  `build\windows-validation-staging-20260913-204303-current` with these
  recorded SHA-256 values: `assets/index-CLcKEYy-.js`/
  `4B4D5B1615BB1614BFCBC7D8F6B282A598C0BDC19DF995FDBA187557F2B593C`,
  `assets/index-CuHS_YZ0.css`/
  `D5BC281CDFA8566CCB7A646B597689C18E5538FD77D472E6BFE8F53FA44083C5`,
  `babelcodex-service-x86_64-pc-windows-msvc.exe`/
  `711431851D5852E5DD4D8E2D10D706460CB7FCE177D12CEFFA2AD826D98F4FCB`,
  `index.html`/
  `956D34F1410A421F30644FFFC8110A3C17365CCD5DD3E0B71ED1BC76AC7C3C4C`,
  and `sha256.txt`/
  `5045111DBF8C3B9596E745F6E3DA0687BB1831A6A86967A7A00D4AE08C8F6630`.
- `WIN-MANUAL-003 / WVQ-002` remains `NOT RUN` with disposition
  `SKIPPED_BY_USER_REQUEST`; no DPI, NVDA or window-lifecycle conclusion is
  inferred.
- `WIN-MANUAL-004 / WVQ-003` remains `BLOCKED` for the broader picker,
  allowlist, Unicode/path-space, cancellation, reconnection, permission and
  artifact-integrity matrix. The two screenshots establish the GUI's fresh
  and stale connection indicators only; they do not establish those flows.
- These operator results supersede only the current manual placeholders. The
  historical validation rows and their original counts remain unchanged. No
  business code, dependency, architecture or configuration was modified.

### Remaining Linux follow-up after manual GUI evidence

1. Keep the current stale-sidecar freshness audit and runtime handshake gates
   in the Windows validation procedure.
2. If a more diagnostic stale-sidecar message is required, separately improve
   the user-facing startup error so it explains the compatibility/startup
   category without exposing paths or implementation details; this was not
   changed during validation.
3. Schedule the still-open `WVQ-003` path/permission/cancellation/reconnection
   matrix and `WIN-MANUAL-005` clean-user recovery test. `WVQ-002` remains
   skipped as requested, and `WVQ-005`/live Codex-PDF remain outside this run.

## Linux handoff: non-Windows work completed on 2026-09-13

The Linux implementation batch completed the platform-independent GUI contract
work without changing the architecture or running Windows-only validation:

- `BabelCodexService.job_view()` now returns only the artifact filename, never a
  local absolute path, preserving the external DTO privacy boundary.
- The JSONL sidecar now advertises and dispatches `retry_job`, `validate_output`
  and `run_qa`; retry is scheduled on the sidecar executor and does not block the
  protocol thread.
- GUI `JobStore` and Job Details now expose explicit retry, artifact validation
  and PDF QA actions. Artifact output is displayed as a filename only; the GUI
  does not expose arbitrary path opening or shell execution.
- Linux regression coverage was added for the redacted artifact DTO, sidecar
  capabilities and GUI-side contract routing.

Linux verification for this batch:

- Python focused service/sidecar/worker tests: `43 passed`;
- final Python suite: `225 passed, 5 deselected`;
- mock PDF integration: `5 passed`;
- final GUI Vitest: `23 passed`;
- GUI TypeScript/Vite build: `PASS`;
- Ruff, format, compile and documentation-inventory checks: `PASS`.

These are Linux/WSL results only. No Windows result is inferred from them, and
the Windows handoff remains `WINDOWS_VERIFICATION_PENDING`.

## Consolidated Windows-only validation handoff

The following items remain Windows-required and should be executed together in
the next native Windows validation phase. Items blocked by unavailable desktop
automation must be skipped as `BLOCKED`, not converted to `PASS` or `FAIL`.

### Manual procedure for `BLOCKED` desktop items

Use a disposable Windows user/profile and a current package. Before starting,
record package filenames, source revision, SHA-256 values and whether the
package is unsigned. Do not use private PDFs, credentials or private glossary
data.

1. Launch the packaged GUI and record the initial connection banner.
2. If desktop automation is unavailable, record:
   `Status: BLOCKED` and `Blocker: COMPUTER_USE_UNAVAILABLE` (or the precise
   packaged startup blocker, such as `PACKAGED_SIDECAR_STARTUP_FAILED`).
3. Preserve the screenshot, GUI/sidecar log excerpt, package hash and exact
   reproduction step. Do not claim the underlying behavior passed.
4. Continue independent CLI, filesystem, protocol, build and package checks.
5. When desktop control is available, run the manual cases below and record
   `PASS`/`FAIL`/`BLOCKED` separately for each case.

### Consolidated manual cases

#### WVQ-003 / WIN-MANUAL-004 — picker, paths, permissions and reconnection

1. Prepare allowed, denied, missing, read-only, space-containing and
   non-ASCII input/output directories.
2. Select the allowed fixture with the native picker; confirm the job starts.
3. Try denied and missing paths; confirm an actionable allowlist error and no
   job creation.
4. Cancel the picker; confirm no job is created.
5. Start a mock job, cancel it, and confirm persisted `cancelled` state.
6. Stop/restart only the sidecar, reconnect, and confirm persisted job state is
   recovered without unsafe rerun.
7. Delete or alter an output artifact; use Job Details `校验产物` and `运行 PDF QA`.
   Confirm the UI reports failure and does not silently skip the job.
8. Confirm artifact details show only safe filenames, while validation still
   operates on the configured output allowlist.

#### WVQ-004 / WIN-MANUAL-005 — clean-user startup and recovery

1. Extract/install the current unsigned package under a disposable user profile
   with no repository checkout, Python environment or prior BabelCodex state.
2. Start the GUI and confirm sidecar handshake without relying on the developer
   workspace.
3. Start a mock job, terminate the disposable runner before completion, and
   restart the service/GUI.
4. Confirm the job becomes `WORKER_CRASHED`/failed, is not automatically rerun,
   and requires the explicit `显式重试` action.
5. Confirm retry begins only after the button action and that normal close leaves
   no orphaned process.

#### WVQ-007 — workdir, lock, retry and cleanup lifecycle

1. Run terminal, active, cancelled and failed mock jobs.
2. Exercise retention cleanup with `cleanup --dry-run` and normal cleanup.
3. Hold a disposable work file open, run cleanup, and record bounded retry or
   the exact lock failure; do not weaken cleanup assertions.
4. Verify active jobs and symlinked/out-of-root directories are never removed.
5. Repeat after sidecar reconnect and process close; record any orphan process or
   stale state.

#### WVQ-005 / WIN-MANUAL-006 — release security and authorized live integration

1. Record package version, source revision, signing status, SHA-256 and SBOM.
2. Run signature, Defender/SmartScreen and clean-package-content checks.
3. Only with written authorization, run one approved live Codex fixture.
4. Verify placeholder preservation, PDF validity, QA result, state, logs and
   cleanup; do not authorize API-key fallback or additional unplanned requests.

#### WVQ-002 / WIN-MANUAL-003 — DPI/NVDA and window lifecycle

This remains `NOT_RUN` with `SKIPPED_BY_USER_REQUEST` for the current handoff.
If later authorized, test 125%/150%/200% scaling, NVDA focus/name/state
announcements, resize, close and relaunch. If the desktop session cannot be
controlled, record `BLOCKED` with `COMPUTER_USE_UNAVAILABLE`.

Overall handoff state remains `WINDOWS_VERIFICATION_PENDING`. Linux completion
of these implementation and test steps must not be promoted to `WINDOWS_PASS`.

## Validation run: 2026-09-14 (Linux HEAD `f0d9ecd`, current dirty tree)

### Validation environment and source state

- Linux/WSL source of truth: branch `dev`, HEAD
  `f0d9ecd56a543a5bf990174240053d2448c65ed2` (`docs: record latest Windows
  validation handoff`). The source working tree was dirty in 16 tracked files,
  including the current GUI, sidecar, service, tests and validation documents;
  this was a working-tree validation, not a clean-commit validation.
- The Plan and queue made the current GUI/service/sidecar changes, frozen
  worker, protocol-v1 handshake, `WVQ-009` freshness audit and NSIS/MSI paths
  applicable. Native desktop, clean-user, `WVQ-007`, release-security and live
  Codex/PDF checks remained separate queue items.
- Windows toolchain: `uv 0.12.10`, project Python `3.12.13`, Node.js
  `24.19.0`, npm `11.17.0`, Rust/cargo `1.98.0`, PyInstaller `6.22.3`.
- The final filtered Linux → E: sync used absolute `/XD` exclusions for `.git`,
  `.venv`, GUI `node_modules`, Rust `target`, build/dist, state, logs, caches
  and user-content directories, plus PDF/log/database file exclusions. The
  corrected `robocopy` returned `3` (changes/extras, no robocopy failure), and
  SHA-256 parity for all 16 current modified files was
  `SELECTED_HASH_MISMATCHES=0`. E: local validation artifacts and extras were
  not synchronized back to Linux.
- An initial relative-exclusion sync attempt was stopped after it was observed
  traversing `gui\\src-tauri\\target`; it was not used as validation evidence.
  The final absolute-exclusion run was the authoritative sync for this round.

### Validation checklist

| Item | Classification | Exact command or procedure | Status | Result |
|---|---|---|---|---|
| Filtered WSL-to-E: synchronization and source parity | Required | Corrected `robocopy` with absolute `/XD` and `/XF` exclusions; SHA-256 comparison of 16 modified files | PASS | `ROBOCOPY_EXIT=3`; 16/16 selected hashes matched. |
| Dependency synchronization | Required | `uv sync --locked --extra runtime --extra dev` | PASS | 95 packages resolved, 91 checked. |
| Lock validation | Required | `uv lock --check` | PASS | Lock resolved successfully. |
| Python format | Required | `uv run ruff format --check .` | PASS | 99 files already formatted. |
| Python lint | Required | `uv run ruff check .` | PASS | All checks passed. |
| Python compileall | Applicable | `uv run python -m compileall -q src tests scripts` | PASS | Exit 0. |
| Documentation inventory test with default Temp | Required | `uv run pytest -q tests/test_docs_inventory.py --tb=short` | BLOCKED | Windows `WinError 5` while creating `C:\\Users\\Shiraishi\\AppData\\Local\\Temp\\pytest-of-Shiraishi`; 6 passed and 11 setup errors, no product assertion conclusion. |
| Documentation inventory test with controlled Temp | Required | Same test with `--basetemp build\\pytest-windows-docs-f0d9ecd` | PASS | 17 passed. |
| Documentation inventory CLI | Required | `uv run python scripts/check_docs_inventory.py` | PASS | `docs inventory check passed`, exit 0. |
| Python suite with default Temp | Required | `uv run pytest -q --tb=short` | BLOCKED | Same Windows Temp ACL blocker; 110 passed, 5 deselected and 115 setup errors. |
| Python suite with controlled Temp | Required | `uv run pytest -q --tb=short --basetemp build\\pytest-windows-full-f0d9ecd` | PASS | 225 passed, 5 deselected in 60.06s. |
| Runtime doctor | Required | `uv run cbpdf --config config\\example.toml doctor` | PASS | Python 3.12.13, BabelDOC 0.6.4 and openai-codex 0.147.0 detected; authenticated state observed but no live request made. |
| GUI dependency installation | Required | `npm.cmd --prefix gui ci` | PASS | 158 packages installed; full tree reported 2 moderate advisories and one pending esbuild script approval. |
| Production dependency audit | Applicable | `npm.cmd --prefix gui audit --omit=dev` | PASS | 0 production vulnerabilities; no remediation run. |
| GUI tests | Required | `npm.cmd --prefix gui test -- --run` | PASS | 4 files, 23 tests passed. |
| GUI production build | Required | `npm.cmd --prefix gui run build` | PASS | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust format | Required | `cargo fmt --manifest-path gui\\src-tauri\\Cargo.toml --all -- --check` | PASS | Exit 0. |
| Tauri Rust host | Required | `cargo check --manifest-path gui\\src-tauri\\Cargo.toml` | PASS | Windows host check passed. |
| Tauri config, capability and icons | Required | Parse `tauri.conf.json`/`capabilities/default.json`; check `icon.ico`/`icon.png` | PASS | `productName=BabelCodex`; 5 permissions; both icons present. |
| Mock PDF integration | Required | `uv run pytest -q -m integration tests\\test_e2e_mock.py --tb=short --basetemp build\\pytest-windows-integration-f0d9ecd` | PASS | 5 passed in 149.39s; mock translator only. |
| Current-source PyInstaller sidecar | Required | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | PASS | `dist\\babelcodex-service.exe`, 195,133,332 bytes, SHA-256 `A867E6AE4731783A6F80E28C44D37AC24541D097C2CE74321F80DF63DBBE6719`. |
| Frozen sidecar protocol v1 | Required | Frozen exe JSONL `get_server_info`, `list_jobs`, `shutdown` with `protocol_version=1` | PASS | 3/3 responses `ok=true`, protocol 1, package 0.1.0, 14 capabilities, exit 0, stderr 0 bytes. |
| Frozen invalid worker request | Required | `dist\\babelcodex-service.exe --worker-request build\\missing-worker-request-f0d9ecd.json` | PASS | Corrected assertion verified `WORKER_REQUEST_INVALID`, `ok=false`, exit 2. |
| Frozen worker valid mock request | Required | Frozen exe `--worker-request` with `fixture_two_column.pdf` and `mock` translator | PASS | Exit 0, `status=completed`, 2 artifacts present; worker stderr contained progress only. |
| Windows target-triple sidecar | Required | Current sidecar copied to `gui\\src-tauri\\binaries\\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | PASS | 3/3 responses valid, exit 0; target-triple hash matched `A867E6AE...E6719`. |
| `WVQ-009` fresh bundle audit | Required | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260914-f0d9ecd-current --target x86_64-pc-windows-msvc --source-tree . --manifest <stage>\\sha256.txt` | PASS | Complete stage contained `index.html`, 2 assets and target-triple sidecar; audit passed. |
| `WVQ-009` stale bundle negative audit | Required | Same audit with preserved stale sidecar SHA-256 `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A` | PASS | Expected exit 1 with `sidecar predates newer Python sources`. |
| Current NSIS/MSI build | Required | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | PASS | NSIS 196,471,116 bytes, SHA-256 `858ADE77C98AE33CA0695394D2A1702EC0BD6AFC0F1B5DFD3FBEB725528656D9`; MSI 196,431,872 bytes, SHA-256 `53EBF1B8A42F555369F8C9FB0F0FBC0F532552CFE8148A8845363E1014DB81CC`. |
| Current Release GUI process smoke | Applicable | Start `gui\\src-tauri\\target\\release\\babelcodex-gui.exe`, wait 8s, stop validation PID | PASS | Process was alive and responding after 8s; no GUI or sidecar process remained after stop. GUI SHA-256 `770A1C059FB0E8E6D9E0187CF344EB10551F380F06325B36FDFE431A0D22CA01`, 4,598,272 bytes. |
| MSI administrative extraction | Applicable | `Start-Process msiexec.exe` with quoted `/a`, `TARGETDIR`, `/qn`, `/norestart` and `/L*v` arguments | PASS | Corrected extraction exit 0; log 84,898 bytes; GUI and sidecar payloads present. |
| MSI payload sidecar parity | Applicable | SHA-256 comparison of extracted `PFiles\\BabelCodex\\babelcodex-service.exe` and `dist\\babelcodex-service.exe` | PASS | Extracted hash matched `A867E6AE...E6719`. |
| MSI-extracted sidecar protocol v1 | Required | Extracted sidecar with absolute `config\\example.toml`, `get_server_info`, `list_jobs`, `shutdown` | PASS | 3/3 responses valid, protocol 1, package 0.1.0, exit 0, stderr 0 bytes. |
| MSI-extracted GUI process smoke | Applicable | Start extracted GUI, wait 8s, stop validation PID | PASS | Process was alive and responding after 8s; no BabelCodex process remained. |
| Current-source native stale-GUI observation | Required | Launch current GUI with preserved stale sidecar and observe native error | BLOCKED | No targetable native app/Computer Use trusted RPC was available; no current-source visual conclusion was inferred from process smoke or static audit. |
| Packaged GUI picker/path/permission/cancel/reconnect matrix | Required | Native picker, Unicode/space paths, allowlist, cancellation, reconnection and artifact integrity | NOT RUN | Explicitly skipped by the user for this round; no result is inferred from process smoke, DOM tests or bundle checks. Disposition: `SKIPPED_BY_USER_REQUEST`. |
| DPI/NVDA/window-lifecycle matrix | Required | Project manual matrix | NOT RUN | Explicitly skipped by user request; disposition `SKIPPED_BY_USER_REQUEST`. |
| Clean-user installation and recovery | Required | Isolated Windows user/profile install and restart/recovery procedure | NOT RUN | No disposable clean-user profile was entered. |
| `WVQ-007` workdir/lock/retry/cancel/reconnect lifecycle | Applicable | Native Windows file-handle and lifecycle matrix | NOT RUN | Broader lifecycle matrix was not entered; mock integration is narrower evidence. |
| `WVQ-005` Defender/SmartScreen/signing/SBOM/release audit | Applicable | Formal release-security workflow | NOT RUN | Packages are unsigned development artifacts; release-security workflow was not authorized. |
| Live Codex/PDF integration | Applicable | Authorized live translation fixture | NOT RUN | No usage-bearing request was authorized. |
| Dependency advisory remediation | Applicable | `npm audit fix` or dependency upgrade | NOT RUN | Outside validation scope and would mutate dependency state. |
| Target Linux machine smoke | Not applicable to Windows execution | Target Linux runtime command | NOT APPLICABLE | Requires a target Linux machine. |

### Failure, blocking and validation-harness analysis

- No current product-code or test-assertion `FAIL` was found after the
  controlled-Temp reruns. The default pytest commands were `BLOCKED` by the
  Windows user Temp ACL (`WinError 5`), not by repository behavior.
- The first relative-exclusion `robocopy` attempt was stopped because it
  traversed the Rust target directory; the corrected absolute-exclusion sync
  is the only sync evidence used above.
- Three validation-input issues were corrected and are not product failures:
  the first GUI staging copy used `Copy-Item -LiteralPath` with an unexpanded
  wildcard and produced a sidecar-only stage; the first two direct MSI
  invocations returned 0 without a log or payload until `Start-Process` with
  fully quoted arguments was used; and the first invalid-worker PowerShell
  assertion treated JSON `false` as an empty display. Each corrected rerun
  produced the expected result.
- Native GUI and stale-GUI observations remain `BLOCKED`, not `FAIL`, because
  the current environment exposed no targetable native desktop surface and no
  trusted Computer Use RPC. Previous screenshots from an older source state
  were not reused as current-source acceptance evidence.
- The package signature probe reported `NotSigned` for the development EXE,
  NSIS and MSI artifacts. This is recorded as an unsigned development package;
  formal signing, Defender/SmartScreen, SBOM and release checks remain
  `NOT RUN`.

### End-of-validation result summary

- Current checklist counts: `PASS 31 / FAIL 0 / BLOCKED 4 / NOT RUN 6 / NOT APPLICABLE 1`.
- Overall status remains `WINDOWS_VERIFICATION_PENDING`, not
  `WINDOWS_VERIFICATION_BLOCKING`. Windows build/runtime/package gates passed,
  while native desktop, clean-user, lifecycle, release-security and live-use
  evidence remain incomplete.
- No Linux business code, dependency, architecture, configuration or lockfile
  was modified by validation. E: received generated validation artifacts,
  dependencies and logs only; Linux remains the source of truth.

### Linux follow-up required

1. Provision a usable native Windows desktop/Computer Use surface and rerun the
   current-source stale-GUI error observation plus the picker, allowlist,
   Unicode/path-space, permission, cancellation, reconnection and artifact
   integrity matrix.
2. Keep the current frozen-worker, protocol-v1, target-triple and fresh/stale
   `WVQ-009` audits as gates after future sidecar or GUI packaging changes.
3. Schedule the full `WVQ-007` workdir/lock/retry/cancel/reconnect lifecycle
   and `WVQ-004` clean-user recovery test.
4. Separately schedule `WVQ-005` release-security validation and explicitly
   authorized live Codex/PDF acceptance. Do not auto-remediate npm advisories
   as part of validation.

## 2026-09-14 latest-source reconciliation — commit 7cd978e

### Source and synchronization

- Linux source of truth: WSL Ubuntu, branch `dev`.
- Current Linux HEAD: `7cd978eaa3bd1b9e4d7226d626603a0bdc3b7a9a` (`feat: complete Linux GUI job operations`).
- Parent: `f0d9ecd56a543a5bf990174240053d2448c65ed2`.
- The commit was observed during this validation at `2026-09-13T23:57:48+08:00` and contains the same 16 tracked files that had already been validated from the preceding dirty working tree. The commit was not created by this validation run.
- After the commit was observed, the current source was synchronized again, one way, from `\\wsl.localhost\Ubuntu\home\shiraishi\VSCode Workspace\Codex_Translator` to `E:\Shiraishi\VSCode Workspace\Codex_Translator`.
- Synchronization log: `build\windows-sync-20260914-7cd978e.log`; `robocopy` exit `3` means files changed or extras were detected, with no copy error. The sync used absolute exclusions for `.git`, virtual environments, `node_modules`, Rust `target`, build/dist caches, runtime state, logs, credentials and user-data directories, plus PDF/log/database/bytecode file filters.
- Post-sync parity: 16 selected current files, `PARITY_MISMATCHES=0`. No Windows source or generated artifact was synchronized back to WSL.
- The WSL working tree after write-back contains only the expected modification to `docs/validation/windows.md`.

### Latest-source validation basis and quick recheck

The parent-to-HEAD commit contains the exact dirty source content validated in the preceding Windows phase; the re-synchronization then verified those bytes against the latest Linux tree. Therefore the current-source build, frozen-sidecar, bundle, installer, protocol and mock-integration evidence in the immediately preceding 2026-09-14 run applies to HEAD `7cd978e`, with the updated source identity recorded above.

Additional post-sync checks on the same E: copy:

| Check | Status | Evidence |
|---|---|---|
| Documentation inventory | PASS | `uv run python scripts/check_docs_inventory.py` → `docs inventory check passed`. |
| GUI tests | PASS | `npm.cmd --prefix gui test -- --run` → 4 files, 23 tests passed. |
| Project-source Ruff lint | PASS | `uv run ruff check src tests scripts` → all checks passed. |
| Project-source Ruff formatting | PASS | `uv run ruff format --check src tests scripts` → 75 files already formatted. |
| Unscoped Ruff traversal after pytest fixtures were generated | FAIL — validation harness contamination | `uv run ruff check .` traversed generated `build\pytest-windows-*\...\src\codex_babeldoc\cli.py` fixtures and reported `F821 sub`; the project source scopes above passed, and this is not a product-code failure. |

The previously recorded current-source package and runtime results remain:

- Python full suite with controlled E: temp: `225 passed, 5 deselected`; the default temp location separately produced `WinError 5` and is recorded as a Windows Temp ACL blocker.
- PyInstaller frozen sidecar, target-triple sidecar, JSONL handshake, invalid/valid worker requests, fresh/stale `WVQ-009` bundle audits, NSIS/MSI build, MSI extraction, extracted-sidecar handshake, release GUI process smoke and mock integration: `PASS`.
- Native current-source stale-GUI observation: `FAIL` for the manually observed
  green unavailable-state indicator; the broader GUI picker/path/permission/
  cancellation/reconnection matrix: `NOT RUN` because it was explicitly
  skipped by the user for this round.
- DPI/NVDA/window lifecycle: `NOT RUN`, explicitly skipped by user request. Clean-user, WVQ-007 lifecycle, WVQ-005 release security, live Codex/PDF and dependency remediation remain `NOT RUN` for their documented reasons.

### Reconciled result

- Product validation summary remains: `PASS 31 / FAIL 0 / BLOCKED 4 / NOT RUN 6 / NOT APPLICABLE 1`.
- In addition, the post-sync unscoped Ruff command has one explicitly classified validation-harness `FAIL`; it does not change the product-code summary because the source-scoped lint passed and the generated fixtures are not repository source.
- Overall status: `WINDOWS_VERIFICATION_PENDING`.

Linux follow-up after this run: the failed-state status-color mapping and
conservative PID-query recovery behavior are implemented and covered by Linux
regression tests. The corresponding native Windows stale-GUI and live
Codex/recovery behavior remain `WINDOWS_VERIFICATION_PENDING`; Linux evidence
does not change their Windows status.

### Linux follow-up

1. Keep the GUI picker/path/permission/cancellation/reconnection matrix as
   `NOT RUN` with disposition `SKIPPED_BY_USER_REQUEST` for this round. When
   separately authorized, provide a trusted native Windows desktop/Computer
   Use surface and execute the matrix; the current stale-GUI color defect must
   also be retested after its Linux fix.
2. Keep the frozen-worker, protocol-v1, target-triple and fresh/stale `WVQ-009` checks as gates after future sidecar or GUI packaging changes.
3. Schedule the `WVQ-007` Windows workdir/lock/retry/cancel/reconnect lifecycle and `WVQ-004` clean-user recovery test.
4. Schedule `WVQ-005` signing/Defender/SmartScreen/SBOM/release validation and explicitly authorize any live Codex/PDF acceptance. Do not remediate npm advisories during validation.

## 2026-09-14 operator-initiated real Codex benchmark attempt

This is a separate usage-bearing benchmark attempt after the automated Windows
validation above. It is recorded independently and does not convert the
formal `WVQ-006` live Codex/PDF acceptance queue item into a pass.

### Input and configuration

- Windows workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`.
- Isolated benchmark directory: `build\real-codex-bench-20260914-095234`.
- Input: `incoming\redacted-long-document.pdf`, SHA-256
  `507c1dacfc7a9a018c89a9251e939cf987213f1805aad2bb177c806524b01369`,
  834,127 bytes.
- `pipeline_meta.source_page_count`: `6`; this input is therefore not yet a
  sufficient long-document stability corpus even if the run later succeeds.
- Translator: `codex-sdk`; worker mode: `subprocess`; cache disabled; maximum
  whole-job attempts: 1; automatic compact disabled (`max_turns_before_compact=0`).
- The run used the current source content corresponding to Linux `dev` HEAD
  `7cd978eaa3bd1b9e4d7226d626603a0bdc3b7a9a`.

### Execution evidence

- Job ID: `91170c528e24db59bb669f6a3d774ef2d8e3310d48e37b6016a1a393903d0851`.
- Persisted state at follow-up inspection: `status=running`,
  `stage=translating`, `attempts=1`, `runner_pid=4376`, no error category/code,
  no safe error message and no artifacts.
- `logs\cbpdf.log` contains only:
  `Starting BabelDOC worker for job job-redacted-long-document`.
- A separate thread-state file was created, but this is not evidence that the
  document translation completed or that the output passed QA.
- At follow-up inspection no process with PID 4376 remained. The state is an
  orphaned `RUNNING` record; the runner did not persist a terminal state.

### Result matrix

| Check | Status | Evidence and interpretation |
|---|---|---|
| Real Codex long-document translation | BLOCKED | Runner disappeared after worker startup; the state remained `RUNNING`, output directory was empty and the original runner failure was not captured. |
| Direct state inspection from JSON | PASS | The state file was read without starting the application service; it accurately shows the orphaned job and the last persisted stage. |
| `cbpdf inspect` after runner loss | FAIL — Windows-specific state-recovery error | `_process_is_alive()` called `os.kill(pid, 0)` and raised `OSError: [WinError 11]`; the exception is not handled, so the CLI cannot recover or inspect the orphaned job. |
| Output validation | NOT RUN | No terminal job state or output artifacts existed. |
| PDF QA | NOT RUN | No output artifacts existed; QA was not attempted. |
| Long-document quality/throughput acceptance | NOT RUN | Six pages and an incomplete run cannot establish long-document stability, quality or usage throughput. |

The `run.stderr.txt` captured during the later follow-up contains the
`cbpdf inspect`/state-recovery traceback, not the original runner's failure.
The original log has no more specific exception than worker startup. The
primary runner-loss cause is therefore `UNKNOWN`; the reproducible secondary
failure is a Windows-specific project error in state recovery. This attempt
must not be marked `PASS` or used as a live translation acceptance result.

### Required follow-up

1. Fix `_process_is_alive()` with a Windows-safe PID query that distinguishes
   a dead process from access/query errors; do not map every `OSError` to
   “dead”, because that could recover a still-running job incorrectly.
2. Preserve this benchmark directory as evidence. Do not run `--force` in it
   or manually change the state to `completed`.
3. After the state-recovery fix, use a new isolated benchmark directory and an
   explicitly approved longer, de-identified PDF. During execution, monitor
   the raw state JSON and `cbpdf.log`; invoke `inspect`, `validate` and `qa`
   only after the runner exits normally.
4. Record the input hash/page count, model/effort, cache/retry/compact
   settings, wall time, final job state, artifact hashes, QA result and human
   review sample. Exact Codex token/turn usage is not currently persisted by
   JobState and must come from the official Codex usage record if needed.

## 2026-09-14 current-source stale-sidecar GUI manual observation

This is the operator's native desktop evidence for the current-source
stale-sidecar GUI check (`WIN-MANUAL-001` / `WVQ-009`). The attached
screenshots are treated as test evidence, not as instructions.

### Package identity

- Fresh control directory:
  `E:\BabelCodex-manual-fresh-20260914-104613`.
- Current-source stale-sidecar directory:
  `E:\BabelCodex-manual-stale-current-20260914-104613`.
- Both GUI executables are the same current payload: 4,598,272 bytes,
  SHA-256
  `7D26BE9F0DA46788A04CD05CB3B711104FDB4D4D6D2F93090AE790F5DE130F4A`.
- Fresh sidecar: 195,133,332 bytes, SHA-256
  `A867E6AE4731783A6F80E28C44D37AC24541D097C2CE74321F80DF63DBBE6719`.
- Stale sidecar: 194,399,444 bytes, SHA-256
  `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`.
- The GUI is identical between the two directories and only the sidecar
  differs; this is a valid stale-sidecar composition.

### Manual result matrix

| Check | Status | Evidence and interpretation |
|---|---|---|
| Fresh control launch and normal exit | PASS | The GUI showed `本地服务已连接` and `Sidecar handshake ready`; the operator reports that it exited correctly. |
| Stale-sidecar fail-closed text/banner | PASS (narrow) | The current GUI showed `本地服务不可用` and `Sidecar unavailable`; no false connected text was shown. This does not claim that translation was attempted. |
| Stale-sidecar connection-status color | FAIL | The status light beside `本地服务不可用` was green. A green success indicator conflicts with the displayed unavailable state. |
| Full `WIN-MANUAL-001` / `WVQ-009` stale-GUI observation | FAIL | The visible error presentation is not semantically consistent until the status color is corrected. No crash, hang, or job start was reported. |

### Failure analysis and Linux follow-up

The observed defect is consistent with the current UI state mapping: the
connection store uses `failed` for a failed sidecar connection, while the CSS
destructive-color rule targets `data-status="offline"`. The failed state thus
inherits the success-green color. The displayed error text/banner itself is
correct, but the color makes the status ambiguous.

Required Linux follow-up, outside this validation task:

1. Align the CSS selector with the actual failed state (or consistently expose
   the existing offline state) so unavailable is rendered with the destructive
   color.
2. Add a GUI regression test asserting that the unavailable/failed state does
   not use the success color.
3. Rebuild the current GUI and repeat the fresh-control and stale-sidecar
   manual observation, including SHA-256 identity capture.

No business code was changed during this validation write-back. The automated
product summary above remains unchanged; this new operator evidence adds a
current manual `FAIL`, so the overall status remains
`WINDOWS_VERIFICATION_PENDING`.

## Linux reconciliation after the 2026-09-14 operator observations

- Linux implemented the failed-state status-color correction in
  `gui/src/styles.css` and added a GUI regression for the `failed`/`ready`
  connection-tone mapping. The historical stale-GUI color `FAIL` above remains
  unchanged; native Windows retest is required and remains
  `WINDOWS_VERIFICATION_PENDING`.
- Linux implemented conservative handling for indeterminate native PID queries
  in `src/codex_babeldoc/core/state.py`; `OSError` from `os.kill(pid, 0)` no
  longer causes unsafe recovery of a possibly running job as dead. A regression
  test covers the behavior. The Windows recovery path and authorized live
  Codex benchmark remain `WINDOWS_VERIFICATION_PENDING`; no benchmark pass is
  inferred.
- Linux verification after these fixes: Python `226 passed, 5 deselected`, mock
  PDF integration `5 passed` with 10 non-blocking fork deprecation warnings,
  GUI `24 passed`, GUI build PASS, Ruff/format/compileall PASS and docs
  inventory PASS.

### Next Windows validation queue disposition

- Retest the repaired stale-GUI status color and the PID-recovery behavior on a
  native current-source package: `WINDOWS_VERIFICATION_PENDING`.
- Keep the picker/path/permission/cancellation/reconnection matrix as
  `NOT RUN` with `SKIPPED_BY_USER_REQUEST` until separately authorized.
- Keep clean-user, WVQ-007 lifecycle, WVQ-005 release security and live
  Codex/PDF as `NOT RUN`/pending under their existing queue entries.

## 2026-09-14 Windows revalidation after Linux status/PID fixes

This run validates the latest WSL working tree, including the Linux changes
that correct the GUI `failed` status tone and make indeterminate Windows PID
queries conservative. It does not rewrite the historical stale-GUI color
`FAIL` or the earlier live-benchmark records.

### Source state and one-way synchronization

- WSL source: branch `dev`, HEAD
  `7cd978eaa3bd1b9e4d7226d626603a0bdc3b7a9a` (`7cd978e`), dirty working tree.
- The dirty source contained the three validation/plan documents plus
  `gui/src/App.tsx`, `gui/src/App.test.tsx`, `gui/src/styles.css`,
  `src/codex_babeldoc/core/state.py` and `tests/test_state.py`.
- Windows workspace: `E:\Shiraishi\VSCode Workspace\Codex_Translator`.
- Synchronization was WSL -> E: only, using `robocopy /E /XJ /COPY:DAT /DCOPY:T`
  without `/MIR`. `.git`, `.venv`, `node_modules`, `build`, `dist`, Rust
  `target`, caches, `incoming`, `translated`, `state`, `logs`, `context` and
  `glossary` were excluded and existing E: validation state was preserved.
- The list-only preview returned Robocopy code `3` (updates present). After
  the copy, selected source/test/document bytes matched the WSL source; this
  included the five changed code/test files and the three changed documents.
- The current Windows source was therefore a dirty-tree validation, not a
  clean-commit validation.

### Automated result matrix

| Check | Status | Exact command or evidence | Summary |
|---|---|---|---|
| Locked Python dependency synchronization | PASS | `uv sync --locked --extra runtime --extra dev` | Resolved 95 packages and checked 91 packages. |
| Lock consistency | PASS | `uv lock --check` | Exit 0. |
| Project Ruff lint | PASS | `uv run ruff check src tests scripts` | All checks passed. |
| Project Ruff format | PASS | `uv run ruff format --check src tests scripts` | 75 files already formatted. |
| Python compileall | PASS | `uv run python -m compileall -q src tests scripts` | Exit 0. |
| Documentation inventory CLI | PASS | `uv run python scripts/check_docs_inventory.py` | `docs inventory check passed`. |
| Python test suite | PASS | `uv run pytest -q --tb=short --basetemp build\\pytest-windows-full-20260914-7cd978e-fix-rerun` | `226 passed, 5 deselected in 28.08s`. |
| Runtime doctor | PASS | `uv run cbpdf --config config\\example.toml doctor` | Python 3.12.13, BabelDOC 0.6.4 and openai-codex 0.147.0; authenticated state detected, no live request sent. |
| GUI dependency installation | PASS | `npm.cmd --prefix gui ci` | 158 packages installed; deprecation and pending esbuild-script warnings were retained, no remediation run. |
| Production dependency audit | PASS | `npm.cmd --prefix gui audit --omit=dev` | 0 vulnerabilities. |
| GUI regression tests | PASS | `npm.cmd --prefix gui test -- --run` | 4 files, 24 tests passed, including `failed` connection tone mapping. |
| GUI production build | PASS | `npm.cmd --prefix gui run build` | TypeScript/Vite passed; 1,590 modules transformed. |
| Tauri Rust format/check | PASS | `cargo fmt --manifest-path gui\\src-tauri\\Cargo.toml --all -- --check`; `cargo check --manifest-path gui\\src-tauri\\Cargo.toml` | Format passed; check finished in the dev profile with exit 0. |
| Mock PDF integration | PASS | `uv run pytest -q -m integration tests\\test_e2e_mock.py --tb=short --basetemp build\\pytest-windows-integration-20260914-7cd978e-current` | `5 passed in 186.21s`; mock translator only. |
| Current PyInstaller sidecar | PASS | `uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec` | Current artifact generated: 195,133,920 bytes, SHA-256 `5605BEF9D62386909D0D1EC2064873AACCDEB15F98BE8F020E11EECFBC849943`. |
| Frozen valid mock worker function | PASS | `dist\\babelcodex-service.exe --worker-request build\\frozen-worker-20260914-7cd978e-current\\request.json` | `status=completed`, BabelDOC 0.6.4, two PDF artifacts generated; output QA was `ok=true` for both. |
| Frozen worker subprocess stderr cleanliness | FAIL | Same valid frozen-worker request; inspect `stderr.txt` | BabelDOC emitted `--multiprocessing-fork ...` unrecognized-argument messages and `PDF save with clean=False failed` warnings, although final artifacts were produced. Linux has since added `multiprocessing.freeze_support()` before importing the frozen sidecar entrypoint; this repaired source remains `WINDOWS_VERIFICATION_PENDING` until a fresh native revalidation. |
| Frozen invalid worker request | PASS | `dist\\babelcodex-service.exe --worker-request build\\missing-worker-request-20260914-7cd978e-current.json` | Structured `WORKER_REQUEST_INVALID`, exit 2. |
| Frozen sidecar protocol v1 | PASS | JSONL `get_server_info`, `list_jobs`, `shutdown` to `dist\\babelcodex-service.exe --config config\\example.toml` | All responses `ok=true`, protocol 1, package 0.1.0, exit 0. |
| Target-triple sidecar parity/protocol | PASS | Copy fresh sidecar to `gui\\src-tauri\\binaries\\babelcodex-service-x86_64-pc-windows-msvc.exe`; repeat v1 handshake | Fresh/target SHA-256 both `5605BEF9...849943`; protocol and shutdown passed. |
| Fresh GUI bundle audit | PASS | `uv run python scripts/check_gui_bundle.py build\\windows-validation-staging-20260914-7cd978e-current --target x86_64-pc-windows-msvc --source-tree . --manifest <stage>\\sha256.txt` | Audit passed; current HTML/JS/CSS and target sidecar present. |
| Stale GUI bundle negative audit | PASS | Same audit against preserved stale sidecar stage | Expected exit 1 with `sidecar predates newer Python sources`. |
| Tauri config/capability/icons | PASS | Parse `tauri.conf.json` and `capabilities/default.json`; inspect `icon.ico`/`icon.png` | `BabelCodex` 0.1.0, one window, five capability permissions, fixed sidecar/config validator and both icons present. |
| NSIS/MSI bundle build | PASS | `npm.cmd --prefix gui run tauri -- build --bundles nsis,msi` | Tauri finished both bundles after release compilation. NSIS 196,474,152 bytes; MSI 196,431,872 bytes. |
| MSI administrative extraction | PASS | Quoted `Start-Process msiexec.exe` `/a`, `TARGETDIR`, `/qn`, `/norestart`, `/L*v` | `MSIEXEC_EXIT=0`, 83,460-byte log, GUI and sidecar payloads present. |
| MSI payload sidecar parity | PASS | SHA-256 of extracted `PFiles\\BabelCodex\\babelcodex-service.exe` vs `dist` | Both `5605BEF9D62386909D0D1EC2064873AACCDEB15F98BE8F020E11EECFBC849943`. |
| MSI-extracted sidecar protocol | PASS | Extracted sidecar v1 `get_server_info`, `list_jobs`, `shutdown` | All responses `ok=true`, exit 0, stderr empty. |
| Release GUI process smoke | PASS | Start `gui\\src-tauri\\target\\release\\babelcodex-gui.exe`, wait 8s, stop validation PID | Alive after 8s; three expected child processes observed; no validation process remained. |
| MSI-extracted GUI process smoke | PASS | Start extracted `PFiles\\BabelCodex\\babelcodex-gui.exe`, wait 8s, stop validation PID | Alive after 8s; no validation process remained. |
| Current-source stale-GUI native visual observation | BLOCKED | Prepared current fresh/stale pair; Computer Use `getState()` and one retry | Both attempts returned `Unable to load browser request-header policy`; no targetable app/window was returned. Process smoke, DOM tests and static CSS/test assertions do not prove native color rendering. |

### Manual and deferred result matrix

| Check | Status | Reason |
|---|---|---|
| GUI picker/path/permission/cancellation/reconnection interaction matrix | NOT RUN | Explicitly skipped by user for this round; disposition `SKIPPED_BY_USER_REQUEST`. No result is inferred from process smoke or GUI unit tests. |
| DPI/NVDA/window-lifecycle matrix | NOT RUN | Explicitly skipped by user request; disposition `SKIPPED_BY_USER_REQUEST`. |
| Clean-user installation and recovery | NOT RUN | No disposable clean-user profile was entered. |
| `WVQ-007` workdir/lock/retry/cancel/reconnect lifecycle | NOT RUN | Broader native lifecycle matrix was not entered; mock integration is narrower evidence. |
| `WVQ-005` Defender/SmartScreen/signing/SBOM/release audit | NOT RUN | Development packages are unsigned and no release-security workflow was authorized. |
| Live Codex/PDF integration and long-document acceptance | NOT RUN | No new usage-bearing request was authorized; the earlier incomplete benchmark remains separately recorded. |
| Dependency advisory remediation | NOT RUN | Outside validation scope; `npm audit fix` was not run. |
| Target Linux machine smoke | NOT APPLICABLE | This is a Windows execution phase. |

### Failure, warning and blocker analysis

- The only current automated `FAIL` is the frozen worker stderr/subprocess path.
  The binary functionally completed, but BabelDOC attempted to start
  multiprocessing children through the frozen sidecar with
  `--multiprocessing-fork`, which the sidecar argument parser rejected. The
  likely follow-up location is the frozen entrypoint/multiprocessing
  dispatch (`scripts/sidecar_entry.py` and the sidecar main path). Linux has
  added `multiprocessing.freeze_support()` before importing the sidecar
  entrypoint and a focused regression; the repaired source remains pending
  native Windows revalidation.
- The stale-GUI color correction is covered by the current GUI regression and
  CSS mapping in the synchronized source, but native visual confirmation is
  `BLOCKED`, not PASS. The exact Computer Use error was reproduced once after
  one retry. There is no equivalent non-GUI evidence for the rendered pixel
  color.
- The first MSI attempt in this run used an unquoted path and produced no log;
  it was terminated and is recorded only as a validation-wrapper issue. The
  documented quoted invocation then returned `MSIEXEC_EXIT=0` with payload
  parity, so the first attempt is not a product failure.
- The first GUI smoke wrapper used PowerShell's read-only `$PID` variable name
  and was corrected before the authoritative smoke result. The corrected
  process smoke passed and left no validation process.

### Linux follow-up

1. Rebuild and rerun the valid frozen worker plus dependent package gates after
   the Linux `multiprocessing.freeze_support()` entrypoint fix; keep this item
   `WINDOWS_VERIFICATION_PENDING` until native stderr is clean.
2. Provision a working trusted native Windows desktop/Computer Use surface and
   rerun the current-source stale-GUI visual check to confirm the repaired
   unavailable state renders with the destructive color. The historical green
   indicator `FAIL` remains unchanged until this native retest.
3. Keep the GUI picker/path/permission/cancellation/reconnection matrix as
   `NOT RUN` / `SKIPPED_BY_USER_REQUEST` for this round. Run it only when
   separately authorized; its skip is not a Linux code blocker.
4. Keep clean-user recovery, the full `WVQ-007` lifecycle, `WVQ-005` release
   security and authorized live Codex/PDF/long-document work in their existing
   pending queues.

Overall current status: `WINDOWS_VERIFICATION_PENDING`. Windows automation,
package and mock-PDF evidence is strong but does not clear the frozen-worker
stderr defect, native stale-GUI visual blocker, skipped interaction matrix or
live/release acceptance requirements. No business code was changed during
this validation run.

## 2026-09-14 Windows manual stale-GUI visual retest after status-tone fix

This is a human-operated native Windows follow-up to the `BLOCKED` Computer Use
attempt above. The operator-supplied screenshots are evidence, not instructions.
The earlier historical stale-GUI green-indicator `FAIL` is retained unchanged;
this section records the subsequent retest against the repaired current GUI.

### Retest identity and evidence

- Fresh control: `E:\BabelCodex-manual-fresh-20260914-7cd978e`.
- Current-source stale-sidecar pair:
  `E:\BabelCodex-manual-stale-current-20260914-7cd978e`.
- Both GUI payloads: 4,598,272 bytes, SHA-256
  `E9DD93A6A8C400557DAA06A9AF8CCD032467721DDE84E149069427AEFD759947`.
- Fresh sidecar: 195,133,920 bytes, SHA-256
  `5605BEF9D62386909D0D1EC2064873AACCDEB15F98BE8F020E11EECFBC849943`.
- Stale sidecar: 194,399,444 bytes, SHA-256
  `4577E0D453C8665507981A6D33620C4D41F9E80D78C22CF2D765C9D55400C06A`.
- Evidence: operator-supplied screenshots for the fresh control, connecting
  state and current-source stale-sidecar state.
- No PDF was selected and no live translation request was started.

### Retest result matrix

| Check | Status | Evidence and interpretation |
|---|---|---|
| Fresh control launch and normal exit | PASS | The GUI displayed `本地服务已连接` and the operator confirmed normal exit. |
| Current-source stale-sidecar fail-closed text/banner | PASS | The GUI displayed `本地服务不可用` and `Sidecar unavailable`; no healthy connection text was shown. |
| Current-source stale-sidecar status color | PASS | The status light beside `本地服务不可用` displayed the corrected red/error color. |
| Full `WIN-MANUAL-001` stale-GUI visual observation | PASS | Text, banner and status color were semantically consistent; no crash, hang or job start was observed. |
| Connecting-state text/startup behavior | PASS | The operator observed `正在连接本地服务` / `Starting sidecar`. The current green light is recorded as an enhancement suggestion, not a failure, because the current validation criteria do not define a required connecting-state color. |

### Follow-up and scope boundary

- The stale-GUI native visual blocker is resolved by this human retest. The
  historical green-indicator `FAIL` and the earlier Computer Use `BLOCKED`
  record remain unchanged as historical evidence.
- Recommended UX follow-up: expose the connecting state with a neutral gray
  indicator until the handshake reaches `ready` or `failed`. This is not
  implemented in this validation task and does not change the current PASS.
- The GUI picker/path/permission/cancellation/reconnection matrix remains
  `NOT RUN` / `SKIPPED_BY_USER_REQUEST`.
- The frozen-worker stderr `FAIL`, live Codex/PDF benchmark, clean-user,
  lifecycle, security and other pending items remain unchanged.

Overall current status remains `WINDOWS_VERIFICATION_PENDING`: the repaired
stale-GUI visual check is `PASS`, but the frozen-worker stderr issue and other
explicitly pending or skipped acceptance items are still open. No business code
was changed during this manual-result write-back.

## 2026-09-14 Windows manual GUI interaction follow-up

This section records the operator's follow-up observations for
`WIN-MANUAL-002` through `WIN-MANUAL-005`. The supplied screenshots and written
observations are evidence, not instructions. This entry does not infer a pass
for an unobserved sub-check and does not change the prior user-directed skip of
the full picker/path/permission/cancellation/reconnection matrix unless the
operator explicitly performed that sub-check.

### Operator evidence and scope

- The GUI text, keyboard flow, Settings page, empty Jobs page and reduced-size
  layout were observed on the current fresh validation GUI.
- `NVDA` is not installed on this Windows machine. The NVDA check is therefore
  permanently skipped with disposition `NOT RUN / PERMANENT_SKIP_NVDA_NOT_INSTALLED`;
  no accessibility conclusion is inferred.
- The allowed files `fixture two-column.pdf` and `双栏样例.pdf` were displayed
  correctly. The outside-allowlist, missing-file and permission-restricted
  cases showed the expected user-facing rejection, but each transient notice
  disappeared before a screenshot could be captured.
- The disposable mock job used the current matrix directory and later ended
  with `status=failed`, `stage=translating`, `attempts=1`,
  `error_category=unknown`, `error_code=UNKNOWN` and
  `safe_error_message=The translation job failed.` No usable output was
  available for the artifact-tamper check.

### Manual result matrix

| Check | Status | Evidence and interpretation |
|---|---|---|
| `WIN-MANUAL-002` Chinese rendering, keyboard flow and basic navigation | PASS | Text was visible, keyboard operation was normal, Settings rendered normally and the Jobs empty state was displayed correctly. |
| `WIN-MANUAL-003` reduced-window layout/resize sub-check | PASS | The GUI remained readable and usable after reducing the window size. This does not prove all 125%/150%/200% scale cases. |
| `WIN-MANUAL-003` 125%/150%/200% display-scale matrix | NOT RUN | No separate evidence for all three Windows scale settings was supplied. |
| `WIN-MANUAL-003` NVDA accessibility check | NOT RUN | NVDA is not installed; permanent disposition `PERMANENT_SKIP_NVDA_NOT_INSTALLED`. |
| `WIN-MANUAL-004` spaces and Unicode input paths | PASS | `fixture two-column.pdf` and `双栏样例.pdf` were shown correctly after selection. |
| `WIN-MANUAL-004` outside-allowlist rejection | PASS | `outside-fixture.pdf` was rejected with the expected prompt; the prompt was transient and not captured in a screenshot. |
| `WIN-MANUAL-004` missing-file rejection | PASS | The missing-file case showed the expected prompt; the prompt was transient and not captured in a screenshot. |
| `WIN-MANUAL-004` picker cancellation | PASS | Cancelling the native picker left the GUI usable without selecting a document. |
| `WIN-MANUAL-004` mock-job cancellation | FAIL | The GUI cancellation did not take effect; the task later displayed `The translation job failed.` The final state is independently consistent with a failed worker, so the precise cancellation root cause remains unresolved. |
| `WIN-MANUAL-004` sidecar reconnection | FAIL | After the disposable sidecar interruption, the GUI showed no visible reconnection/state change. |
| `WIN-MANUAL-004` permission-restricted input | PASS | The expected permission prompt was observed, but it disappeared before a screenshot could be captured. |
| `WIN-MANUAL-004` artifact tamper validation | BLOCKED | No completed translation artifact was available because the disposable mock translation failed; the tamper operation was not performed. |
| `WIN-MANUAL-005` clean-user installation/recovery | NOT RUN | Permanently skipped by explicit user request; disposition `PERMANENT_SKIP_BY_USER_REQUEST`. No clean-user installation or recovery conclusion is inferred. |

### Newly reported GUI notice-banner dismissal issue

- **Status:** `FAIL` (current user-visible behavior).
- **Affected behavior:** a top notice/banner such as `Sidecar handshake ready`
  cannot be permanently dismissed. Clicking its `x` closes it momentarily, then
  the same notice immediately reappears.
- **Reproduction:**
  1. Launch the current GUI with a healthy sidecar.
  2. Observe the top `Sidecar handshake ready` notice.
  3. Click the notice's `x` button.
  4. Observe that the same notice is recreated immediately.
- **Expected:** dismissal remains effective for the current notice, or the
  notice is recreated only for a genuinely new state/event.
- **Observed:** the notice reappears immediately after dismissal.
- **Category:** GUI notification/state lifecycle. This is a product behavior
  `FAIL`, not an automation availability blocker.
- **Evidence:** operator-supplied manual observation; no credentials or PDF
  content were involved.
- **Linux follow-up:** inspect the notice dismissal handler and the `App` /
  `JobStore` state-update path, then add a regression test proving that clicking
  `x` does not immediately restore an unchanged notice.
- Linux has since implemented shared-store notice dismissal and added GUI
  regression coverage. Native Windows notice dismissal remains
  `WINDOWS_VERIFICATION_PENDING` until rerun.

### Failure and follow-up analysis

1. The cancellation observation is a real user-visible `FAIL`, but it is
   currently confounded by the separate frozen-worker failure already recorded
   above. Linux should first resolve/revalidate the frozen worker path, then
   repeat cancellation with a long-enough successful mock run and capture the
   cancel request, terminal state and process list.
2. The reconnection observation is a separate current `FAIL`: the GUI did not
   visibly transition or converge after the disposable sidecar interruption.
   Linux should inspect the `JobStore` reconnect scheduling/transport-close
   path and revalidate with before/after sidecar PIDs and GUI status evidence;
   no business code was changed during this validation write-back.
3. The transient rejection prompts are recorded as narrow `PASS` observations,
   not screenshot-backed full evidence. A future UI change should make such
   notices persist long enough for users and operators to read them, but that
   is not implemented here.
4. The full GUI picker/path/permission/cancellation/reconnection matrix remains
   subject to the prior scope decision and should not be promoted to a broad
   acceptance PASS from these sub-checks alone.

Overall current status remains `WINDOWS_VERIFICATION_PENDING`: `WIN-MANUAL-002`
and the observed resize/path sub-checks passed, but frozen-worker stderr,
mock-job cancellation, reconnection and notice-banner dismissal remain open;
artifact tamper remains blocked and `WIN-MANUAL-005` is permanently skipped by
user request. No business code was changed during this manual-result write-back.

## 2026-09-14 Windows validation rerun for current Linux HEAD

This rerun validates current Linux HEAD `7cd978eaa3bd1b9e4d7226d626603a0bdc3b7a9a`
after the frozen-sidecar entrypoint fix. The Linux/WSL tree remains the source
of truth; the Windows tree was a disposable one-way validation copy. No
business code was changed during validation.

### Result summary

| Check | Status | Evidence |
|---|---|---|
| Controlled dependency, source and documentation gates | PASS | `uv sync --locked`, `uv lock --check`, source-scoped Ruff, compileall, docs inventory and `17 passed` focused test |
| Controlled full Python suite | PASS | `227 passed, 5 deselected` with project-local basetemp |
| Default Python suite | BLOCKED | `115` Windows Temp ACL errors (`PermissionError: [WinError 5]`); controlled basetemp is the reliable result |
| CLI doctor | PASS | Python 3.12.13, BabelDOC 0.6.4, openai-codex 0.147.0; authenticated state detected, no live request |
| GUI install/audit/tests/build and Rust checks | PASS | Production audit 0 vulnerabilities; `26` GUI tests passed; Vite, `cargo fmt --check`, and `cargo check` passed |
| Mock PDF integration | PASS | `5 passed`, mock translator only |
| Fresh PyInstaller sidecar and protocol tests | PASS | 195,133,832 bytes; SHA-256 `B9FF1224B7C3B13659B5EAE13FD580398C65987B46714AF7E8890A50620B618C`; v1 and invalid-request checks passed |
| Fresh frozen mock worker and PDF QA | PASS | Fresh isolated request completed in 34.64s; mono/dual PDFs produced and opened successfully |
| Frozen worker stderr cleanliness | FAIL | Targeted `freeze_support()` messages are gone, but validation-retry/fallback and PyMuPDF deprecation warnings remain |
| Target sidecar, fresh/stale audit, NSIS/MSI and MSI extraction | PASS | Hash parity, expected stale rejection, both bundles, extraction and extracted protocol passed |
| Release and MSI-extracted GUI process smoke | PASS | Both stayed alive for 8s and validation processes were cleaned up |
| Tauri MCP Debug bridge and narrow GUI checks | PASS | Bridge on `127.0.0.1:9223`; unavailable state, red indicator, notice dismissal and Settings/Jobs navigation checked |
| Unscoped repository Ruff | FAIL | Preserved `build\\uv-cache-current` third-party cache was traversed; source-scoped Ruff passed, so this is workspace contamination |

### Deferred checks

| Check | Status | Reason |
|---|---|---|
| Picker/path/permission/cancellation/reconnection; DPI/NVDA/window lifecycle | NOT RUN | User-directed concentrated round; broad manual matrix remains pending |
| Clean-user recovery; `WVQ-007`; `WVQ-005` security audit | NOT RUN | Not entered in this round |
| Live Codex/PDF and long-document acceptance | NOT RUN | No new usage-bearing request authorized |
| npm remediation | NOT RUN | Outside validation scope |
| Target Linux machine smoke | NOT APPLICABLE | Windows execution phase |
| Tauri MCP focus helper | NOT APPLICABLE | Bridge plugin 0.12.0 reported server expectation 0.13.0; direct focus unavailable, while DOM/screenshot interaction worked |

### Failure and blocker analysis

1. Default pytest is blocked by the Windows Temp ACL/cleanup problem, not a
   test assertion. Linux follow-up: keep a controlled-basetemp Windows
   command or diagnose the machine Temp ACL before claiming an unqualified
   default pytest pass.
2. Unscoped Ruff is contaminated by preserved build/cache artifacts;
   source-scoped Ruff is green. Linux follow-up: keep the scoped command or
   make validation-workspace exclusions explicit; no source cleanup was done.
3. The valid frozen worker now completes without the targeted
   `--multiprocessing-fork` or `save with clean=False` messages. Residual
   retry/fallback and PyMuPDF deprecation stderr remain a separate FAIL for
   stderr cleanliness. Linux follow-up: classify or suppress expected output,
   then repeat fresh native worker/package gates.
4. The Tauri MCP version mismatch limits only the focus helper; the bridge,
   DOM, screenshot and click/navigation checks were usable.

### Linux follow-up queue

- Resolve or explicitly classify residual frozen-worker stderr and repeat
  native worker/package validation.
- Choose a controlled-basetemp policy or investigate the Windows Temp ACL.
- Keep Ruff scoped away from preserved build/cache artifacts.
- Keep the picker/path/cancellation/reconnection, clean-user, lifecycle,
  release-security and live Codex/PDF checks pending until authorized.
- The earlier historical GUI cancellation/reconnection/banner issues remain
  open; this rerun did not promote them to broad GUI acceptance.

Overall current status: `WINDOWS_VERIFICATION_PENDING`. Automated/package and
mock-PDF evidence is strong, but the default-temp blocker, residual frozen
stderr, deferred acceptance matrices and live/release checks remain open.

## 2026-09-14 Windows manual GUI basic-interaction result

This entry records the operator's manual result for the current GUI basic
interaction guide. The attached screenshots are operator evidence; the
PowerShell transcript is retained at
build/gui-manual-20260914-163943/manual-session.log. No business code was
changed.

### Identity and launch evidence

- Windows host: TUF-A14, Windows build 10.0.29667, PowerShell 7.6.6.
- Tauri Debug launcher PID: 46564; Debug GUI PID: 34180.
- Debug stdout confirms Vite readiness and the MCP Bridge on
  127.0.0.1:9223; Debug Rust compilation completed successfully.
- Release GUI PID: 54848; Release sidecar children were observed at
  53656 and 54104.
- The final process check showed no remaining GUI or sidecar process under the
  current repository path. The transcript also contained an older unrelated
  sidecar at PID 43812 from
  E:\BabelCodex-manual-winmanual004-20260914-7cd978e; it is not evidence
  for the current run.

### Manual result matrix

| Check | Status | Evidence and interpretation |
|---|---|---|
| Debug Tauri launch and Debug Bridge initialization | PASS | Vite became ready, Rust Debug build completed, and the Bridge listened on 127.0.0.1:9223. |
| Debug GUI fail-closed unavailable presentation | PASS | The GUI showed 本地服务不可用, Sidecar unavailable, and a red status indicator; the message and color were semantically consistent. |
| Debug sidecar healthy handshake | FAIL | The Debug GUI remained unavailable after startup. The captured Tauri logs contain no sidecar error, so the exact Debug handshake cause remains unresolved. |
| Notice dismissal in unavailable state | PASS | The unavailable-state notice could be closed normally. |
| Mouse navigation | PASS | Basic pages were navigable with the mouse. |
| Keyboard navigation | PASS | Basic page navigation and controls worked with the keyboard. |
| Start without selecting a PDF | PASS | No job was created and the expected user-facing guard was displayed. |
| Native file-picker cancellation | PASS | Cancelling the picker left the GUI usable without selecting a document. |
| Valid PDF selection | PASS | The selected PDF was displayed in the GUI. |
| Unicode and space-containing paths | PASS | The Chinese filename and the path containing spaces were displayed correctly. |
| Window resize/basic layout | PASS | The reduced window remained readable and controls were not visibly clipped or overlapped. |
| Release sidecar startup and handshake | PASS | Release GUI showed 本地服务已连接 with a green status indicator. |
| Release valid PDF selection | PASS | Release GUI displayed the selected file path correctly. |
| Release selection notice persistence | FAIL | The selection notice appeared and disappeared immediately, before it could be reliably read. This is a GUI notification lifecycle issue; file selection itself passed. |

### Follow-up

1. Diagnose the Debug-only handshake failure using a fresh isolated config and
   sidecar stdout/stderr capture. Release handshake passing shows that the
   packaged sidecar path is functional, but it does not clear the Debug path.
2. Change or verify the selection notice lifecycle so that the selected-file
   notice remains visible long enough to read, or remains until explicit
   dismissal. Add a GUI regression test if the behavior is confirmed as
   unintended.
3. Repeat the manual check with PID-specific cleanup. The transcript used a
   broad Stop-Process -Name babelcodex-service -Force command; future
   validation must not terminate unrelated sidecars.

Linux follow-up after this result: notices now flow through a shared
`JobStore.setNotice()` and rejected translations use a one-shot request that
does not schedule global reconnect, with GUI regression coverage. The repaired
source is `LINUX_VERIFIED`; the Windows selection-notice and Debug-handshake
results remain `WINDOWS_VERIFICATION_PENDING`.

Overall manual basic-interaction status: the visual, navigation, picker,
path-display and resize checks passed; Debug healthy handshake and Release
selection-notice persistence remain open. This result does not close the full
picker/permission/cancellation/reconnection, DPI/NVDA, clean-user or release
security matrices.

## 2026-09-14 Windows manual file-selection and path result

This entry records the operator's follow-up manual verification of the native
file picker and configured input-path boundary. Six operator-supplied
screenshots are the visual evidence. No business code was changed.

### Manual result matrix

| Check | Status | Evidence and interpretation |
|---|---|---|
| Connected GUI baseline | PASS | The GUI reached 本地服务已连接 before the path cases. |
| Native picker PDF filter | PASS | The Windows picker displayed PDF documents (*.pdf); the PDF fixture was visible under the filter. |
| Picker cancellation | PASS | Cancelling the native picker returned to the GUI without selecting a document. |
| Valid PDF and space-containing path | PASS | The selected PDF and path containing a space were displayed correctly. |
| Unicode path and uppercase extension | PASS | The Chinese directory/file name and uppercase .PDF extension were displayed correctly. |
| PDF outside configured input directory | PASS | Submission returned source_path is outside the configured input directory; the outside path itself was displayed correctly before submission. |
| File moved away after selection | PASS | Submission returned Input file was not found.; the selected path remained visible and no successful job was inferred. |
| Non-PDF filtering | PASS | The non-PDF file was not visible under the native PDF filter. |
| Path-error notice persistence | FAIL | In the outside-directory and missing-file cases, the error notice appeared briefly and was then replaced or obscured by Starting sidecar / 正在重新连接. The path validation result was correct, but the user-facing error was not stable enough to read. |
| Connection state after path rejection | FAIL | The screenshots show 正在重新连接 while the path error is displayed. A rejected input should not silently make a previously healthy sidecar appear to reconnect; the transport/state transition needs separate diagnosis. |

### Follow-up

1. Inspect the JobStore notice updates around path errors, poll/reconnect
   scheduling and transport-close handling. Add GUI regression coverage for
   both outside-directory and missing-file errors, asserting that the error
   notice remains visible until dismissal or a genuinely newer event.
2. Capture the sidecar PID and connection-state sequence during a rejected
   path submission. Determine whether the reconnecting state is a real
   transport failure or only a notice/status overwrite.
3. Preserve the current PASS results for picker filtering, cancellation,
   Unicode/space display and path validation. This new FAIL concerns feedback
   and connection-state presentation, not the input-path security boundary.

Linux follow-up after this result: shared notice updates and a one-shot
translation request now keep a rejected-path error visible and preserve the
healthy `ready` state, with GUI regressions. The repaired source remains
`WINDOWS_VERIFICATION_PENDING` for native retest.

Overall file-selection/path status: the selection and path-safety checks
passed. Error-notice persistence and the connection-state transition after
path rejection remain open GUI lifecycle issues.

## WVQ-017 — WebdriverIO native desktop E2E

- **状态**: `WINDOWS_VERIFICATION_PENDING`
- **类型**: 自动化 GUI 桌面 E2E
- **添加日期**: 2026-09-14
- **相关变更**:
  - 新增 `@wdio/tauri-service` 作为 GUI 桌面 E2E 基础设施
  - 新增 `gui/wdio.shared.conf.ts`、`gui/wdio.browser.conf.ts`、`gui/wdio.native.conf.ts`、`gui/wdio.external.conf.ts`
  - 新增 `gui/tests/e2e/browser/*.spec.ts`、`gui/tests/e2e/native/*.spec.ts`、`gui/tests/e2e/windows/*.spec.ts`
  - 新增 `gui/scripts/prepare-e2e.mjs`、`gui/scripts/prepare-e2e-rust.mjs`、`gui/scripts/capabilities/*.json`
  - 新增 `config/e2e.toml`（`translator = "mock"`，无付费）
  - 新增 `gui/src-tauri/tauri.e2e.conf.json`、`gui/src-tauri/tauri.mcp.conf.json`
  - Cargo features: `e2e`（WDIO 插件）、`mcp-dev`（MCP Bridge），两者互斥
  - 前端条件加载 `@wdio/tauri-plugin`（`VITE_E2E=1` 控制）

### 验证目标

1. Windows 上运行仓库标准 `npm run e2e:native`，不单独配置测试体系
2. 通用 native specs（`gui/tests/e2e/native/*.spec.ts`）在 Windows 上全部通过
3. Windows-only specs（`gui/tests/e2e/windows/*.spec.ts`）自动执行
4. Linux specs 在 Windows 上自动 skip
5. embedded provider 作为默认结论路径
6. external provider 仅用于 driver 层诊断
7. E2E binary 不包含 MCP Bridge 或生产权限以外的能力
8. 测试不访问真实 Codex，不消耗计划用量
9. 测试结束后无 GUI/sidecar/worker 残留进程

### Windows 标准命令

```powershell
cd gui
npm ci
npm test -- --run
npm run build
npm run e2e:native
```

失败时诊断：

```powershell
npm run e2e:native:debug
npm run e2e:external
```

### 通用 native specs（全部平台）

| Spec | 覆盖 |
|---|---|
| `native/smoke.spec.ts` | WebView 启动、main window 通过 Tauri API 可见、连接状态 ready |
| `native/sidecar-handshake.spec.ts` | 真实 sidecar 启动、get_server_info、GUI 显示"本地服务已连接" |
| `native/path-rejection.spec.ts` | 允许列表外路径被拒绝、连接保持 ready、错误 notice 不被轮询覆盖 |
| `native/mock-lifecycle.spec.ts` | 提交 fixture、观察阶段变化、取消/完成、重启后 job state 恢复 |

### Windows-only specs

| Spec | 覆盖 |
|---|---|
| `windows/paths.spec.ts` | `.exe` 路径解析、Windows 路径 allowlist 拒绝系统目录 |
| `windows/lifecycle.spec.ts` | packaged binary 启动、WebView2 运行时、Windows 文件锁 |

### 结果记录要求

WDIO 失败时必须保存：
- spec 名称与 provider（embedded/external）
- 完整 WDIO 日志（`--logLevel debug`）
- service-captured frontend/backend logs under `gui/logs`; @wdio/tauri-service 1.4.0 does not expose getFrontendLogs/getBackendLogs as browser.tauri methods
- failure screenshot
- 进程残留列表
- failure category：`PRODUCT` / `TEST` / `DRIVER` / `ENVIRONMENT` / `FLAKY` / `BLOCKED`

### 已知风险

- `@wdio/tauri-service` 1.x 仍在快速成熟中；embedded provider 在某些 `invoke()` 场景下可能有 session 卡住的风险
- Windows 上若 embedded 失败，使用 external provider + service 自动管理的 Edge WebDriver 作为诊断对照
- BabelCodex 当前主要通过 plugin-shell sidecar 完成任务，而非自定义 `invoke()`，因此受该风险影响的可能性较低，但仍需记录

### Computer Use 补充边界

WDIO 无法覆盖的场景留给 Computer Use 或人工验收：

| 场景 | WDIO | Computer Use |
|---|---|---:|
| WebView 按钮/表单/菜单 | ✅ | 可选 |
| Tauri IPC / sidecar 生命周期 | ✅ | ❌ |
| Windows 文件选择器原生对话框 | 有限 | ✅ |
| DPI / 多显示器 | 部分 | ✅ |
| 安装器 / 托盘 / 通知 | 不适合 | ✅ |
| 视觉布局检查 | 部分 | ✅ |

### 验证完成标准

- [ ] Windows 上 `npm run e2e:native` 执行成功
- [ ] 通用 specs 全部通过
- [ ] Windows-only specs 自动执行（非 skip）
- [ ] Linux specs 在 Windows 上 skip
- [ ] 普通 Release 构建不包含 WDIO 插件
- [ ] 普通 Release 构建不包含 MCP Bridge listener
- [ ] E2E 构建与 MCP-dev 构建不能同时启用（互斥）
- [ ] 测试结束后无 GUI/sidecar/worker 残留
- [ ] 测试不访问真实 Codex
- [ ] 文档 inventory 通过


## Windows WDIO revalidation: 2026-09-15

### Source, synchronization and scope

- Source of truth: WSL branch dev, HEAD f6d3fd02322052b34ad92bb0dbd6aa8885f9b2c3, dirty tree containing the current Linux GUI/WDIO development changes. This is not a clean-commit validation.
- Synchronization: W:\home\shiraishi\VSCode Workspace\Codex_Translator to E:\Shiraishi\VSCode Workspace\Codex_Translator, one-way, controlled robocopy excluding dependencies, caches, state, user data, logs and build artifacts, with the pre-existing E: sidecar preserved. The Windows validation tree was not synchronized back to WSL.
- Runtime: Node v24.19.0, npm 11.17.0, Windows WebView2/Edge 152.0.4191.66; @wdio/cli 9.31.9; @wdio/tauri-service 1.4.0; @wdio/tauri-plugin 1.4.0; Tauri CLI 2.11.4; Python frozen sidecar package 0.1.0.
- Scope: the standard embedded provider path from WVQ-017, VITE_E2E=1, deterministic mock translator, real Tauri WebView and Windows-only specs. No live Codex request was made.

### Results

| Check | Status | Evidence |
|---|---|---|
| npm ci | PASS | Dependencies rebuilt in the Windows GUI workspace; npm audit --omit=dev reported 0 production vulnerabilities. npm emitted the existing dev-tree advisory warning and pending optional build-script notices; no audit fix was run. |
| npm test -- --run | PASS | 4 files, 27 tests passed. |
| npm run build | PASS | TypeScript and Vite production bundle completed. |
| npm run e2e:prepare | PASS | Target-aware E2E workspace and e2e capability generation completed; Windows target required the existing x86_64-pc-windows-msvc sidecar. |
| npm run e2e:build | PASS | Tauri debug E2E binary built with the e2e feature; linker emitted only the known linker_messages warning. |
| npm run e2e:native:mock | PASS | mock-lifecycle.spec.ts: 4 passing; WebDriver/WebView2 startup succeeded. |
| native handshake and embedded smoke | PASS | sidecar-handshake.spec.ts: 3 passing; smoke.spec.ts: 4 passing; these use the deterministic E2E transport, not a GUI-to-real-sidecar claim. |
| Windows lifecycle | PASS | windows/lifecycle.spec.ts: 2 passing; Windows .exe launch and native job submission completed. |
| standard npm run e2e:native | FAIL | 4 spec files passed and 2 failed. native/path-rejection.spec.ts and windows/paths.spec.ts failed because the E2E mock transport accepted an outside path and the UI showed the queue notice. This is an E2E transport coverage gap, not evidence that the production sidecar allowlist is broken. |
| frozen sidecar protocol and allowlist | PASS | Target-triple sidecar SHA-256 C1D1503FB34595133F8B7E314AD4E16A1B4DE20C3C3F8CA7227B528C793747B6. With --config ..\config\e2e.toml, get_server_info returned protocol 1/package 0.1.0; outside start returned ok=false, CONFIG_INVALID and source_path is outside the configured input directory; shutdown returned ok=true and process exit was 0. |
| validation process cleanup | PASS | After the run, no BabelCodex, sidecar, tauri-driver or msedgedriver process remained. Two stale validation helpers from an earlier run were identified by their exact 4444/56711 command lines and stopped; no unrelated process was touched. |
| Linux GUI re-run in this Windows turn | NOT RUN | This turn validated the Windows E: tree. Existing Linux results remain historical evidence; no Linux result is promoted from the Windows environment. |
| external-provider diagnostic | NOT RUN | Embedded provider is the WVQ-017 conclusion path; external provider is reserved for driver-layer diagnosis after a reproducible embedded failure. |

### Warnings and follow-up

- The service diagnostics reported 5 checks passed and one disk-space warning. Captured frontend logs also contain the known tauri-service/tauri-plugin messages about invoke interception fallback, postMessage IPC fallback and null u32 diagnostic payloads; they did not prevent the passing WebView/spec checks.
- WVQ-017 remains WINDOWS_VERIFICATION_PENDING. The two failed GUI allowlist specs must be split into a contract-compatible deterministic negative transport test or a separately controlled real-sidecar GUI path on the Linux development side; this was not implemented during Windows validation because the project rules prohibit changing production business code merely to make a validation run pass.
- Native GUI real file-picker, DPI/accessibility, clean-user package, release security, live Codex and long-document acceptance remain unexecuted or separately queued.

### Linux follow-up after this Windows run: 2026-09-15

- Linux source-only follow-up completed after the Windows E2E path-allowlist result:
  - `gui/src/sidecar.ts` now applies the configured `build/e2e/incoming` allowlist only to the persistent E2E mock transport; production transport/allowlist code was not weakened.
  - `gui/src/jobStore.test.ts` adds a regression for accepted/rejected E2E mock paths.
  - Native path specs clear persistent mock state between cases so one job cannot contaminate the next case.
- Linux verification:
  - GUI Vitest: `28/28` passed;
  - Linux native embedded WDIO: `4 spec files, 15 tests passed` via `npm run e2e:native`;
  - TypeScript/Vite build, Ruff, docs inventory `17/17`, and `git diff --check`: passed;
  - Browser mode: `BLOCKED` because Chrome/Chromedriver was not available; the service dev server startup worked, but WDIO browser setup could not download the required browser binaries in this environment.
- Windows disposition:
  - The historical 2026-09-15 Windows `standard npm run e2e:native` failure remains preserved as history.
  - WVQ-017 stays `WINDOWS_VERIFICATION_PENDING`; after one-way synchronization of the Linux fix, rerun `npm.cmd --prefix gui run e2e:native`, especially `native/path-rejection.spec.ts` and `windows/paths.spec.ts`, then rerun the frozen sidecar allowlist probe.
  - Do not mark Windows path safety `PASS` from the Linux native result or from the previous frozen-sidecar-only result; the GUI-to-Windows-native result needs fresh evidence.