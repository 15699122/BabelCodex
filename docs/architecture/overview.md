# Architecture Overview

The stable software architecture is documented in [`../architecture.md`](../architecture.md). This file is the routed overview entry point for the shared-core/platform-adapter boundary; ownership and handoff rules belong in [`../development/platform-ownership.md`](../development/platform-ownership.md), not here.

```text
Shared Application Service / contracts / persistence
                 │
        platform-neutral core
          ┌──────┴──────┐
          │             │
   Linux integration  Windows adapter/native GUI
                        │
                 sidecar/package/runtime
```

CLI, GUI, and MCP continue to share the Application Service. Platform adapters may differ in process, filesystem, GUI, and packaging behavior while preserving the shared protocol and safe public boundaries.
