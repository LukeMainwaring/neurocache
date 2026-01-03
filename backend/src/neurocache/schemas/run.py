import uuid
from enum import StrEnum

from .base import BaseSchema


class RunStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RunSchema(BaseSchema):
    id: uuid.UUID
    status: RunStatus
    thread_id: str
