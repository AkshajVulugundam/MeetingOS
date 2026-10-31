"""Pydantic models for MeetingOS data validation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ActionItem(BaseModel):
    """A single action item extracted from a meeting."""

    title: str = Field(..., min_length=1, max_length=500)
    assignee: Optional[str] = Field(None, max_length=200)
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority: str = Field("Unknown", pattern=r"^(High|Medium|Low|Unknown)$")
    evidence: str = Field("", max_length=2000)
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    @field_validator("due_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            return None
        return v


class MeetingAnalysis(BaseModel):
    """Complete meeting analysis result."""

    summary: str = Field("", max_length=5000)
    decisions: list[str] = Field(default_factory=list)
    tasks: list[ActionItem] = Field(default_factory=list)


class MeetingInput(BaseModel):
    """User input for a new meeting."""

    title: str = Field(..., min_length=1, max_length=200)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    participants: str = Field("", max_length=1000)
    transcript: str = Field(..., min_length=30)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        return v


class TaskRecord(BaseModel):
    """A task record for database operations."""

    id: Optional[int] = None
    meeting_id: Optional[int] = None
    meeting_title: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    assignee: Optional[str] = Field(None, max_length=200)
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority: str = Field("Unknown", pattern=r"^(High|Medium|Low|Unknown)$")
    evidence: str = Field("", max_length=2000)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    status: str = Field("Pending", pattern=r"^(Pending|In Progress|Completed|Rejected)$")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"Pending", "In Progress", "Completed", "Rejected"}
        if v not in allowed:
            raise ValueError(f"Invalid status. Must be one of: {allowed}")
        return v


def validate_tasks(task_list: list[dict]) -> list[dict]:
    """Validate and clean a list of task dictionaries.

    Returns only valid tasks with at least a non-empty title.
    """
    validated = []
    for item in task_list:
        try:
            task = TaskRecord(
                title=str(item.get("title", "")).strip(),
                assignee=item.get("assignee"),
                due_date=item.get("due_date"),
                priority=item.get("priority", "Unknown"),
                evidence=str(item.get("evidence", "")).strip(),
                confidence=float(item.get("confidence", 0.0)),
                status=item.get("status", "Pending"),
            )
            if task.title:
                validated.append(task.model_dump(exclude_none=True))
        except Exception:
            continue
    return validated


def is_overdue(due_date: Optional[str], status: str) -> bool:
    """Check if a task is overdue.

    A task is overdue if:
    - It has a valid due_date
    - The due_date is before today
    - Status is not Completed
    """
    if not due_date or status == "Completed":
        return False
    try:
        deadline = datetime.strptime(due_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        return deadline < today
    except ValueError:
        return False
