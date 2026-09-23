# Validation Policy

Validation is risk-based and incremental. Select the smallest scope that reasonably covers the change:

```text
Targeted → Module → Subsystem → Full
```

Before testing, inspect the Git diff, changed modules, call/dependency relationships, API or protocol changes, platform behavior, and reusable prior results. Prefer affected unit/regression tests, then integration, module checks, and relevant build/type/lint checks. Record `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, and `NOT_APPLICABLE`; every skipped or blocked item needs a reason.

Expand scope after a targeted failure, unexpected behavior, shared-contract change, unclear dependency impact, multi-subsystem change, security boundary change, or uncertain blast radius. Full regression is normally for releases, major refactors, architecture/core changes, migrations, dependency overhauls, large cross-module changes, security-critical changes, or uncertain blast radius. State explicitly when full regression was not run.

Reuse a prior PASS only when related code, dependencies, platform contracts, and environment requirements remain valid. Otherwise mark `REVALIDATION_REQUIRED`.

Windows validation is normally deferred and accumulated as `WINDOWS_WORK_PENDING` or `WINDOWS_VERIFICATION_PENDING`; use `WINDOWS_BLOCKING` only when it gates safe continuation. Computer Use failure is not a product failure: retry briefly, then mark the GUI item `BLOCKED` with `COMPUTER_USE_UNAVAILABLE`, continue independent checks, and add a manual queue item. A CLI/API/log/filesystem substitute may be PASS only when it proves the same acceptance target.

Every validation round records source revision, change scope, selected/skipped tests, reasons, evidence, deferred work, and manual requirements. GUI manual items must include ID, purpose, preconditions, steps, expected result, evidence, result, and notes. Detailed Windows execution remains in `docs/development/cross-platform-validation.md` and current status in `docs/status/platform-handoff.md`.
