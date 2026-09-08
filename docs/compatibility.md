# Compatibility Baseline

Last verified: 2026-09-08

## Local development baseline

| Component | Verified version/status |
| --- | --- |
| Host | Ubuntu 26.04.1 LTS on WSL2, x86-64 |
| uv | 0.12.10 |
| Python | CPython 3.12.14 managed by uv |
| BabelDOC | 0.6.4 |
| openai-codex | 0.147.0 |
| openai-codex-cli-bin | 0.147.0 |
| pytest | 9.1.1 |
| Ruff | 0.16.6 |

The system Python is 3.14.4 and is intentionally not used because BabelCodex currently requires Python 3.11–3.12. `.python-version` pins local project commands to Python 3.12.

## Verified commands

```bash
uv sync --locked --extra runtime --extra dev
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run babeldoc --warmup
uv run babelcodex --config config/example.toml doctor
```

On 2026-09-08:

- dependency resolution completed successfully with 95 packages;
- BabelDOC warmup completed and downloaded the layout model/CMap assets;
- formatting and lint checks passed;
- the unit test suite reported 6 passing tests;
- the bundled Codex runtime reported `codex-cli 0.147.0`;
- Codex authentication was not active, so `doctor` correctly returned a non-zero status.

## Codex authentication requirement

The SDK runtime is installed, but live translation requires the user to authenticate Codex. Run the bundled or separately installed Codex CLI and choose ChatGPT sign-in, then verify:

```bash
uv run babelcodex --config config/example.toml doctor
```

`codex_authenticated` must be `true` before live Codex integration tests or PDF translation are attempted.

Authentication is intentionally not required by unit tests or GitHub Actions CI.

## CI baseline

GitHub Actions uses:

- Ubuntu hosted runner;
- Python 3.12;
- uv 0.12.10;
- `uv sync --locked --extra runtime --extra dev`;
- Ruff formatting/lint checks;
- pytest without live Codex usage or BabelDOC model warmup.

## Upgrade policy

Changing Python, BabelDOC, openai-codex or uv requires:

1. regenerating `uv.lock`;
2. running all local quality gates;
3. checking `doctor` output;
4. re-running BabelDOC warmup on a clean cache when practical;
5. updating this compatibility document;
6. validating at least one mock PDF fixture before enabling the new baseline.