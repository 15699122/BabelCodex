# Contributing to BabelCodex

BabelCodex is primarily a personal, local-first PDF translation project. Contributions are welcome when they preserve the project's privacy, authentication and PDF-fidelity boundaries.

## Development flow

1. Create a focused feature branch from `main`.
2. Keep BabelDOC-specific imports under `src/codex_babeldoc/backends/`.
3. Add or update tests for behavior changes.
4. Run the available checks before opening a pull request:

   ```bash
   uv sync --extra runtime --extra dev
   uv run ruff check .
   uv run pytest
   ```

5. Describe user-visible behavior, compatibility impact and test coverage in the pull request.

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