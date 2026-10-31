"""SQLite database operations for MeetingOS."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "meetingos.db"


_db_initialized = False


@contextmanager
def get_connection():
    """Yield a connection that commits on success and always closes."""
    global _db_initialized
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        if not _db_initialized:
            _init_db_tables(connection)
            _db_initialized = True
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _init_db_tables(connection: sqlite3.Connection) -> None:
    """Internal helper to create or migrate tables on a connection."""
    # Meetings table
    connection.execute(
        """CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            participants TEXT,
            summary TEXT,
            decisions TEXT,
            transcript TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    # Tasks table with meeting linkage
    connection.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER,
            title TEXT NOT NULL,
            assignee TEXT,
            due_date TEXT,
            priority TEXT NOT NULL DEFAULT 'Unknown',
            evidence TEXT,
            confidence REAL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        )"""
    )

    # Check and migrate columns if database already existed with older schema
    cursor = connection.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]
    if "meeting_id" not in columns:
        connection.execute("ALTER TABLE tasks ADD COLUMN meeting_id INTEGER REFERENCES meetings(id)")
    if "confidence" not in columns:
        connection.execute("ALTER TABLE tasks ADD COLUMN confidence REAL DEFAULT 0.0")

    # Create indexes for faster queries
    connection.execute("CREATE INDEX IF NOT EXISTS idx_tasks_meeting_id ON tasks(meeting_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee)")
    connection.commit()


def init_db() -> None:
    """Public helper to explicitly initialize database with meetings and tasks tables."""
    with get_connection():
        pass


def create_meeting(
    title: str,
    meeting_date: str,
    participants: str = "",
    summary: str = "",
    decisions: list[str] | None = None,
    transcript: str = "",
) -> int:
    """Create a new meeting record and return its ID."""
    import json

    decisions_json = json.dumps(decisions or [], ensure_ascii=False)
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO meetings (title, meeting_date, participants, summary, decisions, transcript)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, meeting_date, participants, summary, decisions_json, transcript),
        )
        return cursor.lastrowid


def get_meetings() -> list[dict]:
    """Get all meetings ordered by date descending."""
    import json

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM meetings ORDER BY meeting_date DESC, created_at DESC"
        ).fetchall()

    meetings = []
    for row in rows:
        meeting = dict(row)
        meeting["decisions"] = json.loads(meeting.get("decisions") or "[]")
        meetings.append(meeting)
    return meetings


def get_meeting(meeting_id: int) -> dict | None:
    """Get a single meeting by ID."""
    import json

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
    if row:
        meeting = dict(row)
        meeting["decisions"] = json.loads(meeting.get("decisions") or "[]")
        return meeting
    return None


def create_tasks(tasks: list[dict], meeting_id: int | None = None) -> int:
    """Create tasks and link them to a meeting, preventing duplicates on retry.

    Returns count of newly inserted tasks.
    """
    if not tasks:
        return 0

    inserted_count = 0
    with get_connection() as connection:
        # Check existing tasks for this meeting to prevent duplicates
        existing_titles = set()
        if meeting_id is not None:
            existing = connection.execute(
                "SELECT LOWER(TRIM(title)) FROM tasks WHERE meeting_id = ?", (meeting_id,)
            ).fetchall()
            existing_titles = {row[0] for row in existing}

        for item in tasks:
            title = str(item.get("title", "")).strip()
            if not title:
                continue

            # Prevent duplicate insertion if already exists for this meeting
            if meeting_id is not None and title.lower() in existing_titles:
                continue

            due_date = item.get("due_date")
            if due_date and (not isinstance(due_date, str) or len(due_date.strip()) == 0):
                due_date = None

            connection.execute(
                """INSERT INTO tasks (meeting_id, title, assignee, due_date, priority, evidence, confidence, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    meeting_id,
                    title,
                    item.get("assignee") or None,
                    due_date,
                    item.get("priority", "Unknown"),
                    str(item.get("evidence", "")).strip(),
                    float(item.get("confidence", 0.0)),
                    item.get("status", "Pending"),
                ),
            )
            existing_titles.add(title.lower())
            inserted_count += 1

    return inserted_count


def get_tasks(
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    priority: Optional[str] = None,
    meeting_id: Optional[int] = None,
) -> list[dict]:
    """Get tasks with optional filters."""
    query = """
        SELECT t.*, m.title as meeting_title
        FROM tasks t
        LEFT JOIN meetings m ON t.meeting_id = m.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND t.status = ?"
        params.append(status)
    if assignee:
        query += " AND t.assignee = ?"
        params.append(assignee)
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
    if meeting_id:
        query += " AND t.meeting_id = ?"
        params.append(meeting_id)

    query += " ORDER BY (t.due_date IS NULL OR TRIM(t.due_date) = '') ASC, t.due_date ASC, t.created_at DESC"

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_task(task_id: int) -> dict | None:
    """Get a single task by ID."""
    with get_connection() as connection:
        row = connection.execute(
            """SELECT t.*, m.title as meeting_title
               FROM tasks t
               LEFT JOIN meetings m ON t.meeting_id = m.id
               WHERE t.id = ?""",
            (task_id,),
        ).fetchone()
    return dict(row) if row else None


def update_task_status(task_id: int, status: str) -> bool:
    """Update a task's status. Returns True if successful."""
    allowed = {"Pending", "In Progress", "Completed", "Rejected"}
    if status not in allowed:
        raise ValueError(f"Invalid status. Must be one of: {allowed}")

    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE tasks SET status = ? WHERE id = ?", (status, task_id)
        )
        return cursor.rowcount > 0


def get_task_statistics() -> dict:
    """Get aggregate task statistics for the dashboard."""
    with get_connection() as connection:
        # Total count
        total = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        # Status breakdown
        status_rows = connection.execute(
            "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
        ).fetchall()
        status_counts = {row["status"]: row["count"] for row in status_rows}

        # Overdue count (valid due_date < today AND status not in Completed/Rejected)
        today = datetime.now().strftime("%Y-%m-%d")
        overdue = connection.execute(
            """SELECT COUNT(*) FROM tasks
               WHERE due_date IS NOT NULL
                 AND TRIM(due_date) != ''
                 AND LENGTH(TRIM(due_date)) = 10
                 AND due_date < ?
                 AND status NOT IN ('Completed', 'Rejected')""",
            (today,),
        ).fetchone()[0]

        # Unique assignees
        assignees = connection.execute(
            "SELECT DISTINCT assignee FROM tasks WHERE assignee IS NOT NULL AND assignee != ''"
        ).fetchall()
        assignee_list = [row["assignee"] for row in assignees]

    return {
        "total": total,
        "pending": status_counts.get("Pending", 0),
        "in_progress": status_counts.get("In Progress", 0),
        "completed": status_counts.get("Completed", 0),
        "rejected": status_counts.get("Rejected", 0),
        "overdue": overdue,
        "assignees": assignee_list,
    }


def delete_task(task_id: int) -> bool:
    """Delete a task. Returns True if successful."""
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0


def get_meeting_tasks(meeting_id: int) -> list[dict]:
    """Get all tasks for a specific meeting."""
    return get_tasks(meeting_id=meeting_id)
