# Current Platform Handoff

This file contains only the active handoff, using the template defined in `docs/development/git-platform-handoff.md` §16. Completed rounds belong in `docs/validation/windows-validation-history.md` or the monthly archive under `docs/validation/history/`; the current Windows validation queue stays in `docs/validation/windows.md`.

## Batch

- Task: Documentation batch — formalize Git-based cross-platform handoff (new `docs/development/git-platform-handoff.md`, expanded root `AGENTS.md` platform-handoff rules, docs index and workflow cross-references).
- Branch: `dev`
- Current owner: Cross-platform Owner (Linux)
- Current state: `CROSS_PLATFORM_IN_PROGRESS` (uncommitted working-tree batch; no formal handoff yet)

## Revisions

- Cross-platform input revision: `d56f3e4`
- Cross-platform handoff revision: `NOT_RUN` (batch must be committed and pushed before formal handoff)
- Windows input revision: `NOT_RUN`
- Windows implementation revision: `NOT_RUN`
- Windows validation revision: `NOT_RUN`

## Cross-platform Work Completed

- Root `AGENTS.md`: canonical-state rule (formal state via Git; direct sync diagnostics-only), Git-based formal handoff, direct-sync boundary (`E:\Projects\<project>` Git-only; `E:\Scratch\<project>` sync target), workspace model, ownership boundaries, batch principle, general platform rules.
- New `docs/development/git-platform-handoff.md`: workspace model, canonical state, formal handoff procedures, branch strategy, revision recording, direct-sync fast path/restrictions/promotion, dirty-workspace protection, conflict handling, review, validation reuse, states, template, batch principle, core rules, daily operating prompts.
- `docs/README.md`: ownership table, docs table and update triggers registered for the new document.
- `docs/development/platform-ownership.md` and `docs/development/cross-platform-validation.md`: cross-references to the Git handoff workflow.
- `.agents/skills/cross-platform-handoff/SKILL.md` and `.agents/skills/windows-validation/SKILL.md`: Git-only formal handoff and scratch-only direct sync.
- Changed shared modules: `None; documentation-only batch.` See the current Git diff and `docs/development-plan.md`.

## Windows Work Required

- `None from this documentation-only batch.`

## Windows Validation Required

- Continue the existing native GUI/path/package queue in `docs/validation/windows.md`, executed against the revision recorded by the formal handoff.

## Expected Behavior

- `Windows-specific behavior must be confirmed natively; Linux evidence is not Windows PASS.`

## Known Risks

- Native GUI, filesystem/process semantics, packaging, and clean-environment behavior must not be inferred from Linux.
- This batch is currently uncommitted; no formal handoff exists until it is committed and pushed to the configured remote.

## Windows Results

- Implementation: `NOT_RUN`
- PASS: `None from this documentation-only batch.`
- FAIL: `None from this documentation-only batch.`
- BLOCKED: `None from this documentation-only batch.`
- Manual validation required: `GUI, filesystem/process, packaging, and clean-environment checks remain subject to documented prerequisites.`

## Cross-platform Follow-up

- `CROSS_PLATFORM_CHANGE_REQUIRED`: `None from this documentation-only batch.`
- `CROSS_PLATFORM_REVIEW_REQUIRED`: `None from this documentation-only batch.`

## Next Owner

- Owner: Windows Platform Owner — after Linux commits and pushes this batch
- Required actions:
  - Linux: review final `git diff`, update this file and the Plan, commit this documentation batch, push to the configured remote, record the handoff revision above, set state `READY_FOR_WINDOWS`.
  - Windows: fetch remote, verify a clean working tree, update the formal Windows repository to the handoff revision, confirm it against this file, then start the Windows batch. Never overwrite the formal Windows working tree by direct file sync.
