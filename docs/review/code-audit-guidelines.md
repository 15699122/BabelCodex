# Code Audit Guidelines

Audit findings must be evidence-bound and routed by ownership:

- shared or cross-platform finding → Linux Cross-platform Owner;
- Windows API/runtime/GUI/filesystem/packaging finding → Windows Platform Owner;
- unclear boundary → `NEEDS_VERIFICATION` before implementation.

For each finding record file/module, observed behavior, evidence, impact, likely owner, recommended smallest change, and validation scope. Do not infer Windows failure from Linux-only evidence or treat a GUI automation failure as a product failure. A proposed change to shared API, protocol, data model, persistence, or architecture is `CROSS_PLATFORM_CHANGE_REQUIRED`; a small contract-preserving adapter correction is `CROSS_PLATFORM_REVIEW_REQUIRED`.

Review the final Git diff, preserve unrelated work, check security/privacy boundaries, and distinguish implementation, platform validation, and release acceptance. Use the result states in `docs/validation/validation-policy.md`.
