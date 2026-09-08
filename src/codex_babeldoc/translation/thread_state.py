"""Provider-neutral persistence contract for Codex translation thread IDs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock


@dataclass(frozen=True, slots=True)
class ThreadState:
    document_id: str
    thread_id: str
    provider: str = "codex-sdk"
    generation: int = 0


class ThreadStateStore:
    """Persist only thread identity metadata, never prompts or document text."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _path(self, document_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in "-_." else "_" for char in document_id)
        return self.root / f"thread-{safe_id}.json"

    def load(self, document_id: str) -> ThreadState | None:
        path = self._path(document_id)
        if not path.is_file():
            return None
        values = json.loads(path.read_text(encoding="utf-8"))
        return ThreadState(
            document_id=str(values["document_id"]),
            thread_id=str(values["thread_id"]),
            provider=str(values.get("provider", "codex-sdk")),
            generation=int(values.get("generation", 0)),
        )

    def save(self, state: ThreadState) -> None:
        with self._lock:
            target = self._path(state.document_id)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=target.parent,
                prefix=".thread-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(
                    {
                        "document_id": state.document_id,
                        "thread_id": state.thread_id,
                        "provider": state.provider,
                        "generation": state.generation,
                    },
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.flush()
                os.fsync(handle.fileno())
                temporary = Path(handle.name)
            try:
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)

    def rotate(self, document_id: str, thread_id: str) -> ThreadState:
        previous = self.load(document_id)
        state = ThreadState(
            document_id=document_id,
            thread_id=thread_id,
            provider=previous.provider if previous else "codex-sdk",
            generation=(previous.generation + 1) if previous else 0,
        )
        self.save(state)
        return state
