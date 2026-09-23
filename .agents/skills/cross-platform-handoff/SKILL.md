---
name: cross-platform-handoff
description: Prepare and reconcile Linux/Windows platform handoffs for BabelCodex.
---

# Cross-platform handoff

Read `docs/development/platform-ownership.md`, `docs/development/git-platform-handoff.md`, `docs/status/platform-handoff.md`, and the current Git diff. Formal handoff is Git-based: commit the batch, push to the configured remote, and record branch, source revision, and handoff revision; direct file sync is diagnostic-only, must target a scratch workspace, and never overwrites the formal Windows Owner repository. Record ownership, completed work, required implementation and validation, risks, expected behavior, modules, and priority. Keep active state in the status file and historical evidence in validation history.
