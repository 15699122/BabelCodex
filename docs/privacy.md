# Privacy and Local Data

BabelCodex is designed primarily for personal, local PDF translation.

## What remains local

The application stores job state, generated PDFs, logs, translation caches, configuration and glossary data on the user's machine. The public source repository must not contain these user-specific files.

## What is sent to Codex

Text segments selected by BabelDOC for translation are sent to the Codex service through the official `openai-codex` SDK and the user's existing Codex/ChatGPT authentication. BabelCodex does not operate a developer-owned document upload server.

## Authentication

BabelCodex does not scrape browser cookies, store ChatGPT credentials in project configuration, or convert ChatGPT authentication into a fake OpenAI-compatible API.

## Logging

Logs should contain job identifiers, stages, safe error codes, timings and aggregate metrics. Full source text, full translated text, prompts and authentication tokens must not be logged by default.

## Public repository boundary

The following content must remain excluded from the public repository:

- source and translated PDFs;
- state and worker directories;
- logs and caches;
- credentials and environment files;
- private glossary data;
- test documents without redistribution permission.

## User responsibility

Users are responsible for confirming that they have permission to translate a document and that sending its text to the Codex service is compatible with their privacy and account requirements.