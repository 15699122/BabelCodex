# BabelCodex Local MCP Server

## Scope

The MCP server is a local stdio adapter over the shared Python Application
Service. It is not an HTTP service and it does not expose a general-purpose
filesystem or shell interface.

Start it from the repository root with:

```bash
uv run babelcodex --config config/example.toml mcp serve
```

An MCP client should launch this command with stdin/stdout pipes and treat each
newline-delimited JSON object as one JSON-RPC message. The server supports the
MCP `initialize`, `tools/list`, `tools/call`, `ping`, and
`notifications/initialized` methods.

## Tools

| Tool | Scope |
| --- | --- |
| `babelcodex_doctor` | Report local runtime and Codex authentication diagnostics. |
| `babelcodex_start_translation` | Start an asynchronous PDF job inside the configured input directory. |
| `babelcodex_get_job` | Read one persisted job by ID. |
| `babelcodex_list_jobs` | List persisted jobs. |
| `babelcodex_cancel_job` | Signal cancellation for an active job started by this MCP process. |
| `babelcodex_validate_output` | Re-hash and validate only the job's configured output artifacts. |
| `babelcodex_cleanup_job` | Remove only the terminal job-owned worker directory. |

`source_path` is constrained to the configured input directory and must be an
existing PDF. Artifact validation resolves paths beneath the configured output
directory, checks file existence, size, SHA-256 and the PDF magic header. Cleanup
rejects active jobs, symlinks and any path outside the configured worker root.

All tool arguments are strictly allowlisted. Unknown tools, arbitrary method
calls, shell-like arguments, unrestricted file reads and unrestricted deletion
are rejected by the protocol boundary.

## Client registration example

The registration entry must point to the fixed project command, not to a shell
string or user-provided executable:

```json
{
  "mcpServers": {
    "babelcodex": {
      "command": "uv",
      "args": ["run", "babelcodex", "--config", "config/example.toml", "mcp", "serve"]
    }
  }
}
```

Use an absolute `cwd` or an absolute config path in a client-specific setting
when the client does not start in the repository root. Do not place tokens,
PDF contents, generated state, or private glossary data in this document or in
the repository.

## Limitations

The server does not register itself with the inner Codex translation thread.
Real Codex PDF translation, target-package registration, clean-environment
smoke, and release signing remain separate validation tasks. Unit and contract
tests use mock or local fixtures and do not consume paid model usage.