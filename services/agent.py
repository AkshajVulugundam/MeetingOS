"""MeetingOS Agent - Orchestrates meeting analysis and task execution.

This module implements the agentic workflow:
1. LLM analyzes transcript and proposes tasks
2. Python validates the AI-generated JSON
3. User reviews and approves tasks
4. Python saves approved tasks directly to database (no second LLM call)
"""

from __future__ import annotations

from typing import Any

from .database import create_meeting, create_tasks, get_meeting
from .groq_service import analyze_meeting, transcribe_audio
from .validation import validate_tasks


def process_meeting(
    transcript: str,
    title: str,
    meeting_date: str,
    participants: str = "",
) -> dict[str, Any]:
    """Process a meeting transcript and return analysis results.

    This is the main orchestration function that:
    1. Analyzes the transcript using the LLM
    2. Validates the extracted data
    3. Creates a meeting record (without tasks yet)

    Args:
        transcript: Meeting transcript text
        title: Meeting title
        meeting_date: Meeting date in YYYY-MM-DD format
        participants: Optional comma-separated list of participants

    Returns:
        Dictionary with meeting_id, summary, decisions, and proposed tasks
    """
    # Step 1: Analyze with LLM
    analysis = analyze_meeting(transcript, meeting_date=meeting_date)

    # Step 2: Validate extracted tasks
    validated_tasks = validate_tasks(analysis.get("tasks", []))

    # Step 3: Create meeting record (tasks added after user approval)
    meeting_id = create_meeting(
        title=title,
        meeting_date=meeting_date,
        participants=participants,
        summary=analysis.get("summary", ""),
        decisions=analysis.get("decisions", []),
        transcript=transcript,
    )

    return {
        "meeting_id": meeting_id,
        "summary": analysis.get("summary", ""),
        "decisions": analysis.get("decisions", []),
        "tasks": validated_tasks,
    }


def execute_approved_tasks(
    meeting_id: int,
    approved_tasks: list[dict],
) -> dict[str, Any]:
    """Save user-approved tasks to the database.

    This function does NOT make a second LLM call.
    It directly saves the exact tasks the user approved.

    Args:
        meeting_id: ID of the meeting these tasks belong to
        approved_tasks: List of task dictionaries approved by user

    Returns:
        Dictionary with execution results
    """
    if not approved_tasks:
        return {"success": False, "message": "No tasks to execute.", "count": 0}

    # Validate the approved tasks one more time
    validated = validate_tasks(approved_tasks)

    if not validated:
        return {
            "success": False,
            "message": "No valid tasks after validation.",
            "count": 0,
        }

    # Save directly to database - NO LLM call here
    count = create_tasks(validated, meeting_id=meeting_id)

    # Verify the meeting exists
    meeting = get_meeting(meeting_id)

    return {
        "success": True,
        "message": f"Successfully created {count} task(s).",
        "count": count,
        "meeting_title": meeting.get("title", "Unknown") if meeting else "Unknown",
    }


def process_audio_meeting(
    audio_bytes: bytes,
    filename: str,
    title: str,
    meeting_date: str,
    participants: str = "",
    language: str | None = None,
) -> dict[str, Any]:
    """Process an audio recording: transcribe, analyze, and create meeting record.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename
        title: Meeting title
        meeting_date: Meeting date in YYYY-MM-DD format
        participants: Optional participants
        language: Optional ISO language code

    Returns:
        Dictionary with meeting_id, transcript, summary, decisions, and tasks
    """
    # Step 1: Transcribe audio
    transcript = transcribe_audio(audio_bytes, filename, language=language)

    # Step 2: Process the transcript
    result = process_meeting(
        transcript=transcript,
        title=title,
        meeting_date=meeting_date,
        participants=participants,
    )

    result["transcript"] = transcript
    return result
