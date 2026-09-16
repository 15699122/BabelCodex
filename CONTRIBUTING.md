# Contributing to BabelCodex

BabelCodex is primarily a personal, local-first PDF translation project. Contributions are welcome when they preserve the project's privacy, authentication and PDF-fidelity boundaries.

## Development environment

Recommended environment:

- Python 3.11 or 3.12 (3.12 recommended)
- `uv`
- Codex CLI / Codex SDK authenticated with ChatGPT
- BabelDOC 0.6.x

Setup:

```bash
cd BabelCodex
uv sync --extra runtime --extra dev
```

If your `uv` version uses dependency groups differently, the equivalent pip installation is:

```bash
python -m pip install -e ".[runtime,dev]"
```

## Development flow

1. Create a focused feature branch from `dev`.
2. Keep BabelDOC-specific imports under `src/codex_babeldoc/backends/`.
3. Add or update tests for behavior changes.
4. Run the available checks before opening a pull request:

   ```bash
   uv sync --extra runtime --extra dev
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest
   ```

   Validation scope should match the change risk: by default run the directly affected
   tests, their regressions and the relevant lint/compile checks. Reserve the full suite
   for release work, architecture or dependency overhauls, and changes whose blast radius
   cannot be determined. See the incremental validation strategy in
   `docs/development/testing.md`, and state explicitly which checks were not run.

5. Describe user-visible behavior, compatibility impact and test coverage in the pull request.

## GUI development

The GUI lives in `gui/` and uses Tauri 2 + React/TypeScript. See `gui/README.md` for local development, the bundle audit and Linux bundle build.

```bash
cd gui
npm ci
npm test
npm run build
```

## Documentation rules

- README is user-facing only; development state, verification records and internal order go in `docs/` documents.
- When you add, delete, rename or change the responsibility of a module, update `docs/development/codebase-map.md`.
- Commands in documents must match the registered CLI parser or package scripts.
- The documentation inventory check must pass: `uv run pytest tests/test_docs_inventory.py`.
- See `docs/README.md` for the authoritative document ownership table.

## Data and credential rules

Never commit:

- user PDFs or generated translations;
- job state, logs or translation caches;
- Codex/ChatGPT authentication data;
- API keys, cookies or tokens;
- private glossary content;
- third-party PDF fixtures without redistribution permission.

Tests that use live Codex access must be explicitly marked as integration tests and must not run by default.

## Architecture rules

- CLI, GUI and MCP share one Python Application Service.
- The GUI does not directly import BabelDOC or initialize Codex.
- The MCP Server does not expose arbitrary shell execution or unrestricted file access.
- Invalid translations must not reach BabelDOC rendering when placeholder or output validation fails.

See `AGENTS.md`, `docs/architecture.md`, `docs/development-plan.md` and `docs/decisions.md` for the current design baseline.