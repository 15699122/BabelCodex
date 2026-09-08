# Security Policy

## Supported status

BabelCodex is currently an early development scaffold. Security and privacy reports are welcome, but no production SLA is provided.

## Reporting a vulnerability

Please report vulnerabilities through GitHub's private security reporting feature when it is available for the repository. Do not include real user PDFs, authentication tokens or sensitive document text in a public issue.

Useful report details include:

- affected version or commit;
- operating system;
- minimal reproduction using synthetic data;
- expected and actual behavior;
- whether the issue affects path safety, sidecar execution, MCP permissions, logs or credentials.

## Security boundaries

BabelCodex must not:

- scrape browser cookies;
- emulate undocumented ChatGPT endpoints;
- silently fall back to separately billed API credentials;
- expose arbitrary shell execution through GUI or MCP;
- allow MCP cleanup outside a job-owned working directory;
- log authentication data or full sensitive document text by default.

PDF text is sent to the Codex service under the signed-in user's account settings. Users are responsible for deciding whether a document is appropriate to send to that service.