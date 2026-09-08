from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


@dataclass(slots=True)
class JobState:
    source: str
    fingerprint: str
    status: str = "pending"
    attempts: int = 0
    last_error: str | None = None
    updated_at: str = ""

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def file_fingerprint(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class StateStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, fingerprint: str) -> Path:
        return self.root / f"{fingerprint}.json"

    def load(self, source: Path) -> JobState:
        fp = file_fingerprint(source)
        path = self._path(fp)
        if not path.exists():
            job = JobState(source=str(source), fingerprint=fp)
            job.touch()
            return job
        return JobState(**json.loads(path.read_text(encoding="utf-8")))

    def save(self, job: JobState) -> None:
        job.touch()
        self._path(job.fingerprint).write_text(
            json.dumps(asdict(job), ensure_ascii=False, indent=2), encoding="utf-8"
        )
