# Platform Ownership and Handoff

## Model

BabelCodex uses two owners:

- **Linux — Cross-platform Owner**: shared architecture, business logic, APIs, protocols, persistence formats, platform-neutral behavior, shared tests, and primary architecture documentation.
- **Windows — Windows Platform Owner**: Windows-native APIs, filesystem/process semantics, GUI, services, registry, PowerShell integration, permissions, packaging/installers, sidecars, compatibility fixes, and Windows validation.

Ownership includes design, implementation, validation, triage, and follow-up responsibility. A workspace is an execution environment, not the project’s source of truth. Canonical state is the integrated Git repository plus committed docs, Plan/task state, and recorded validation evidence.

## Routing

Ask in order:

1. Is the behavior shared by all platforms? Route to Linux.
2. Is the cause or implementation Windows-specific? Route to Windows.
3. Does a Windows fix require a shared API, protocol, data model, or architecture change? Windows records `CROSS_PLATFORM_CHANGE_REQUIRED` and hands the shared change to Linux.
4. Is the change small, contract-preserving, and an adapter-supporting correction? Windows may implement it and mark `CROSS_PLATFORM_REVIEW_REQUIRED` for Linux review.
5. If ownership is unclear, record `NEEDS_VERIFICATION` and do not expand the change.

Windows is not merely a validation environment. It may directly modify Windows production code, configuration, packaging, tests, and scripts. It must not change shared semantics solely to make a Windows check pass.

## Handoff

Prefer:

```text
Linux batch → Linux targeted verification → Windows handoff
→ Windows implementation/verification → Linux follow-up only if required
```

Do not ping-pong after every feature unless Windows behavior is `WINDOWS_BLOCKING`. Before handoff, record source revision, completed shared work, Windows work, required validation, risks, expected behavior, relevant modules, and priority in `docs/status/platform-handoff.md`. The receiving owner must inspect the current Git diff before acting. Windows changes must be integrated into canonical Git state before the next synchronization can overwrite or supersede them.

Formal handoff is Git-based and must identify branch, source commit, and handoff revision; direct filesystem sync is diagnostic-only, targets a scratch workspace, and never constitutes a formal handoff. See `docs/development/git-platform-handoff.md`.

## Completion

Do not use `DONE` to mean implementation and both-platform verification. Use the applicable states: `CROSS_PLATFORM_IN_PROGRESS`, `READY_FOR_WINDOWS`, `WINDOWS_IN_PROGRESS`, `WINDOWS_WORK_PENDING`, `WINDOWS_VERIFICATION_PENDING`, `WINDOWS_PASS`, `WINDOWS_FAIL`, `WINDOWS_BLOCKED`, `CROSS_PLATFORM_CHANGE_REQUIRED`, and `CROSS_PLATFORM_REVIEW_REQUIRED`.
