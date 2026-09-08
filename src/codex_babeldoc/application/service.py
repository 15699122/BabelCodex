from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.orchestrator import Orchestrator
from codex_babeldoc.core.state import JobState


class InvocationSource(StrEnum):
    CLI = "cli"
    GUI = "gui"
    MCP = "mcp"


@dataclass(slots=True, frozen=True)
class StartTranslationCommand:
    source_path: Path
    force: bool = False
    invocation_source: InvocationSource = InvocationSource.CLI


class BabelCodexService:
    """Shared application boundary for CLI, GUI and MCP callers."""

    def __init__(self, config: AppConfig, orchestrator: Orchestrator | None = None) -> None:
        self.config = config
        self.orchestrator = orchestrator or Orchestrator(config)

    def start_translation(self, command: StartTranslationCommand) -> JobState:
        resolved = command.source_path.resolve()
        self.orchestrator.run_one(
            resolved,
            force=command.force,
            invocation_source=command.invocation_source.value,
        )
        return self.orchestrator.state.load(
            resolved,
            config_fingerprint=self.config.fingerprint(),
        )

    def get_job(self, job_id: str) -> JobState | None:
        return self.orchestrator.state.load_by_job_id(job_id)

    def list_jobs(self) -> list[JobState]:
        return self.orchestrator.state.list_jobs()

    def close(self) -> None:
        """Release resources owned by the shared application service."""
        close = getattr(self.orchestrator, "close", None)
        if callable(close):
            close()
