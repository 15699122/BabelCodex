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
