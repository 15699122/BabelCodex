# Cross-platform Development and Windows Validation Workflow

## 1. Canonical state and ownership

BabelCodex uses a dual-owner model:

- Linux is the **Cross-platform Owner** for shared architecture, core behavior, contracts, persistence, protocols, platform-neutral tests, and primary architecture docs.
- Windows is the **Windows Platform Owner** for Windows APIs, filesystem/process semantics, native GUI, services, registry, PowerShell, permissions, packaging/installers, sidecars, compatibility fixes, and Windows validation.

The canonical project state is the integrated Git repository, committed project documentation, current Plan/task state, and recorded platform validation results. Linux and Windows workspaces are execution environments; neither is the sole source of truth. A Windows-owned production change must be integrated into canonical Git state before a later synchronization can overwrite or supersede it.

See `docs/development/platform-ownership.md` for routing, `docs/development/git-platform-handoff.md` for the Git-based exchange workflow, workspace model and direct-sync boundary, and `docs/status/platform-handoff.md` for the active batch.

## 2. Ownership routing

If behavior is shared by all platforms, route it to Linux. If the cause or implementation is Windows-specific, route it to Windows. If a Windows issue requires changing a shared API, protocol, data model, persistence format, or architecture, record `CROSS_PLATFORM_CHANGE_REQUIRED` and hand the shared change to Linux. A small, contract-preserving adapter correction may be implemented by Windows but must be marked `CROSS_PLATFORM_REVIEW_REQUIRED`. Unclear ownership is `NEEDS_VERIFICATION`.

Windows is not merely a validation environment. It may modify Windows production code, configuration, packaging, tests, and scripts. It must not change shared semantics solely to make a Windows check pass.

## 3. Batched handoff flow

Prefer:

```text
Linux batch
  → Linux targeted verification
  → READY_FOR_WINDOWS handoff
  → Windows implementation and targeted verification
  → Linux follow-up only for shared changes
```

Do not switch platforms after every feature. Accumulate `WINDOWS_WORK_PENDING` or `WINDOWS_VERIFICATION_PENDING`; use `WINDOWS_BLOCKING` only when Windows behavior is a hard prerequisite for safe continuation.

Before handoff record source revision, completed shared work, Windows implementation required, Windows validation required, known risks, expected behavior, relevant modules, and priority. The receiving owner reads the current Git diff and local state before acting. Formal handoff is Git-based: commit the batch, push to the configured remote, and record the handoff revision in `docs/status/platform-handoff.md`; direct file sync never constitutes a formal handoff (see `docs/development/git-platform-handoff.md`).

## 4. Validation policy

Use the smallest sufficient scope:

```text
Targeted → Module → Subsystem → Full
```

Inspect the diff, changed modules, dependencies, API/protocol impact, platform behavior, and reusable prior results. Expand after failure, unexpected behavior, shared-contract changes, unclear blast radius, multi-subsystem impact, or security-sensitive changes. Full regression is normally reserved for release, major architecture/core changes, migrations, dependency overhauls, large cross-module changes, security-critical changes, or uncertain blast radius.

Reuse a prior PASS only when related code, dependencies, platform contracts, and environment requirements remain valid; otherwise use `REVALIDATION_REQUIRED`. Record `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, and `NOT_APPLICABLE` with reasons and evidence. Linux evidence never becomes Windows PASS without native Windows execution.

## 5. Windows execution and Computer Use fallback

Before Windows work, inspect canonical revision, Git diff, Windows-local configuration, credentials, caches, and user data. Synchronization must preserve Windows-local state and exclude dependencies, build caches, secrets, PDFs, logs, and state unless the documented procedure requires them. Direct filesystem sync is diagnostic-only: it must target a disposable scratch workspace (`E:\Scratch\<project>`), must never overwrite the formal Windows Owner repository (`E:\Projects\<project>`), and never replaces Git-based handoff (see `docs/development/git-platform-handoff.md`). Windows-specific code changes are integrated deliberately; never use unconditional mirroring.

Windows records exact commands, working directory, versions, evidence, failure category, dependent blocked checks, and follow-up. If Computer Use is unavailable, retry briefly, then mark the GUI item `BLOCKED` with blocker `COMPUTER_USE_UNAVAILABLE`, continue independent checks, and add a manual validation queue item. An equivalent CLI/API/log/filesystem check is PASS only if it proves the same target.

## 6. States and history

Use implementation/flow states separately from test results:

- Flow: `CROSS_PLATFORM_IN_PROGRESS`, `READY_FOR_WINDOWS`, `WINDOWS_IN_PROGRESS`, `WINDOWS_WORK_PENDING`, `WINDOWS_VERIFICATION_PENDING`, `WINDOWS_PASS`, `WINDOWS_FAIL`, `WINDOWS_BLOCKED`, `CROSS_PLATFORM_CHANGE_REQUIRED`, `CROSS_PLATFORM_REVIEW_REQUIRED`.
- Results: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, `NOT_APPLICABLE`.

The active batch belongs in `docs/status/platform-handoff.md`. Completed rounds belong in `docs/validation/windows-validation-history.md` and the existing monthly archive. Historical FAIL results are never rewritten as PASS.
