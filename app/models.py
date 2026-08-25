from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_validator, model_validator


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("title must not be blank")
    if len(stripped) > 200:
        raise ValueError("title must be at most 200 characters")
    return stripped


MAX_TAGS = 10
MAX_TAG_LENGTH = 30


def _validate_tags(tags: Optional[list[str]]) -> Optional[list[str]]:
    if tags is None:
        return None
    if len(tags) > MAX_TAGS:
        raise ValueError(f"a task may have at most {MAX_TAGS} tags")
    cleaned = []
    for tag in tags:
        stripped = tag.strip()
        if not stripped:
            raise ValueError("tags must not be blank")
        if len(stripped) > MAX_TAG_LENGTH:
            raise ValueError(f"tags must be at most {MAX_TAG_LENGTH} characters")
        cleaned.append(stripped)
    return cleaned


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    tags: list[str] = []

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_tags(value) or []


# Update fields that may legitimately be set to null (to clear them). Any other
# field sent as an explicit null is rejected instead of being stored.
NULLABLE_UPDATE_FIELDS = frozenset({"assignee", "due_date"})


class TaskUpdate(BaseModel):
    """Partial update payload.

    Optional[...] here means "omit to leave unchanged", not "may be null".
    Only ``assignee`` and ``due_date`` are genuinely nullable — sending null
    for those clears the value. For every other field an explicit null is a
    client error and is rejected with 422 rather than silently stored.
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    tags: Optional[list[str]] = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        nulled = [
            name
            for name, value in data.items()
            if value is None
            and name in cls.model_fields
            and name not in NULLABLE_UPDATE_FIELDS
        ]
        if nulled:
            fields = ", ".join(sorted(nulled))
            raise ValueError(f"{fields} must not be null; omit the field to leave it unchanged")
        return data

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return _validate_tags(value)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_title(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    due_date: Optional[date] = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def overdue(self) -> bool:
        """A task is overdue if it has a due date in the past and isn't Done.

        Computed at serialization time (not stored) so it stays correct as
        the current date advances, without needing a background job.
        """
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        return self.due_date < datetime.now(timezone.utc).date()
