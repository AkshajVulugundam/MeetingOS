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
    """Sanitize and validate tasks; bad optional fields are fixed, not dropped."""
    validated = []
    for item in task_list:
        try:
            due = item.get("due_date")
            due = str(due).strip() if due else None
            if due:
                try:
                    datetime.strptime(due, "%Y-%m-%d")
                except ValueError:
                    due = None
            pr = str(item.get("priority") or "Unknown").strip().capitalize()
            if pr not in ("High", "Medium", "Low", "Unknown"):
                pr = "Unknown"
            try:
                conf = float(item.get("confidence", 0.0))
            except (TypeError, ValueError):
                conf = 0.0
            conf = 0.0 if conf != conf else min(max(conf, 0.0), 1.0)
            who = item.get("assignee")
            who = str(who).strip()[:200] if who else None
            if who and who.lower() in ("none", "null", "nan"):
                who = None
            status = item.get("status", "Pending")
            if status not in ("Pending", "In Progress", "Completed", "Rejected"):
                status = "Pending"
            task = TaskRecord(
                title=str(item.get("title", "")).strip()[:500],
                assignee=who,
                due_date=due,
                priority=pr,
                evidence=str(item.get("evidence", "")).strip()[:2000],
                confidence=conf,
                status=status,
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
    if not due_date or status in ("Completed", "Rejected"):
        return False
    try:
        deadline = datetime.strptime(due_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        return deadline < today
    except ValueError:
        return False
