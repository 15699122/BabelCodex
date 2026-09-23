---
name: windows-validation
description: Run risk-based Windows implementation and validation for BabelCodex.
---

# Windows validation

Read `docs/validation/validation-policy.md`, `docs/development/platform-ownership.md`, `docs/development/git-platform-handoff.md`, and `docs/development/cross-platform-validation.md`. Inspect the current Git revision and Windows-local state before synchronization; update the formal Windows working tree only through Git at the recorded handoff revision, never by direct file sync from Linux. Direct-sync results belong to a separate scratch workspace and are experimental until integrated through the normal Git workflow. Windows may fix Windows-owned production code and tests. Mark shared contract or architecture changes `CROSS_PLATFORM_CHANGE_REQUIRED` or `CROSS_PLATFORM_REVIEW_REQUIRED`. Record exact commands, evidence, and `PASS`/`FAIL`/`BLOCKED`/`NOT_RUN`/`NOT_APPLICABLE` bound to the tested revision; never promote Linux evidence to Windows PASS. If GUI automation is unavailable, use `COMPUTER_USE_UNAVAILABLE`, continue independent checks, and add a manual queue item.
