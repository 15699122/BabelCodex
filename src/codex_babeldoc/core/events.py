from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EventType(StrEnum):
    JOB_CREATED = "job_created"
    STATUS_CHANGED = "status_changed"
    PROGRESS = "progress"
    WARNING = "warning"
    ARTIFACT_CREATED = "artifact_created"
    JOB_FAILED = "job_failed"
    JOB_COMPLETED = "job_completed"


@dataclass(slots=True, frozen=True)
class JobEvent:
    event_type: EventType
    job_id: str
    sequence: int
    timestamp: str
    payload: dict[str, object] = field(default_factory=dict)
