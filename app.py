"""MeetingOS - AI-Powered Meeting-to-Execution Agent.

A complete application that transforms meeting conversations into
actionable, trackable tasks with human-in-the-loop approval.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.agent import execute_approved_tasks, process_meeting
from services.database import (
    get_meetings,
    get_meeting,
    get_tasks,
    get_task_statistics,
    init_db,
    update_task_status,
    delete_task,
    get_meeting_tasks,
)
from services.groq_service import transcribe_audio
from services.validation import is_overdue

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Page configuration
st.set_page_config(
    page_title="MeetingOS — Meeting to Execution Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
init_db()

# Check API key
api_key = os.getenv("GROQ_API_KEY", "").strip()


def render_sidebar() -> str:
    """Render the sidebar with navigation and status."""
    st.sidebar.title("🎙️ MeetingOS")
    st.sidebar.caption("From Meeting Conversations to Actual Execution")

    st.sidebar.divider()

    # Navigation pages as required by architecture
    pages = [
        "📊 Dashboard",
        "➕ New Meeting",
        "🔍 Review AI Findings",
        "📋 Task Manager",
        "📜 Meeting History",
        "ℹ️ About MeetingOS",
    ]

    # Handle page switching from buttons
    if "nav_page" in st.session_state and st.session_state["nav_page"] in pages:
        default_idx = pages.index(st.session_state["nav_page"])
    else:
        default_idx = 0

    page = st.sidebar.radio(
        "Navigation",
        pages,
        index=default_idx,
        key="navigation_radio",
    )
    # Sync session state
    st.session_state["nav_page"] = page

    st.sidebar.divider()

    # API key status
    if not api_key:
        st.sidebar.error("⚠️ Groq API key missing")
        st.sidebar.caption("Add your GROQ_API_KEY to the `.env` file.")
    else:
        st.sidebar.success("✅ Groq API Connected")

    # Quick meeting stats in sidebar
    stats = get_task_statistics()
    st.sidebar.divider()
    st.sidebar.markdown("**Quick Stats**")
    s_col1, s_col2 = st.sidebar.columns(2)
    s_col1.metric("Tasks", stats["total"])
    s_col2.metric("Overdue", stats["overdue"])

    st.sidebar.divider()
    st.sidebar.caption(
        "MeetingOS Architecture:\n"
        "1. Transcript/Audio → Groq Whisper\n"
        "2. Analysis → GPT-OSS-20B\n"
        "3. Human Review & Approval\n"
        "4. Python Direct DB Execution"
    )

    return page


def render_dashboard():
    """Render the main dashboard with metrics and task overview."""
    st.title("📊 MeetingOS Dashboard")
    st.markdown("Real-time tracking of decisions and action items from all meetings.")

    # Get statistics from SQLite
    stats = get_task_statistics()

    # Key Metrics Cards Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Tasks", stats["total"])
    with col2:
        st.metric("Pending", stats["pending"])
    with col3:
        st.metric("In Progress", stats["in_progress"])
    with col4:
        st.metric("Completed", stats["completed"])
    with col5:
        st.metric(
            "Overdue Tasks",
            stats["overdue"],
            delta=f"{stats['overdue']} require action" if stats["overdue"] > 0 else "All on track",
            delta_color="inverse" if stats["overdue"] > 0 else "normal",
        )

    st.divider()

    if stats["total"] == 0:
        st.info("👋 No tasks in the database yet. Process a meeting to extract action items!")
        if st.button("➕ Create Your First Meeting", type="primary"):
            st.session_state["nav_page"] = "➕ New Meeting"
            st.rerun()
        return

    # Filter controls
    st.subheader("Filter & Search Tasks")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Pending", "In Progress", "Completed", "Rejected"],
            key="dash_status_filter",
        )
    with filter_col2:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "High", "Medium", "Low", "Unknown"],
            key="dash_priority_filter",
        )
    with filter_col3:
        assignee_options = ["All"] + stats["assignees"]
        assignee_filter = st.selectbox(
            "Assignee",
            assignee_options,
            key="dash_assignee_filter",
        )
    with filter_col4:
        search_query = st.text_input(
            "Search Task Title",
            placeholder="Type keyword...",
            key="dash_search_query",
        )

    # Fetch filtered tasks from SQLite
    tasks = get_tasks(
        status=None if status_filter == "All" else status_filter,
        assignee=None if assignee_filter == "All" else assignee_filter,
        priority=None if priority_filter == "All" else priority_filter,
    )

    if search_query.strip():
        q = search_query.strip().lower()
        tasks = [t for t in tasks if q in t["title"].lower() or (t.get("evidence") and q in t["evidence"].lower())]

    st.subheader(f"Tasks ({len(tasks)})")

    if not tasks:
        st.warning("No tasks match the selected filters.")
    else:
        # Prepare display dataframe
        display_rows = []
        for t in tasks:
            due = t.get("due_date") or ""
            is_task_overdue = is_overdue(due, t.get("status", "Pending"))
            status_display = t.get("status", "Pending")
            if is_task_overdue:
                status_display = f"⚠️ {status_display} (Overdue)"

            display_rows.append({
                "ID": t["id"],
                "Meeting": t.get("meeting_title") or "Unknown",
                "Task Title": t["title"],
                "Assignee": t.get("assignee") or "Unassigned",
                "Due Date": due or "None",
                "Priority": t.get("priority", "Unknown"),
                "Status": status_display,
                "Confidence": f"{int((t.get('confidence') or 0.0) * 100)}%",
            })

        df = pd.DataFrame(display_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Quick Status Update Bar
        st.markdown("---")
        st.markdown("#### Quick Status Update")
        u_col1, u_col2, u_col3 = st.columns([3, 2, 1])

        task_dict = {f"#{t['id']}: {t['title']} ({t.get('assignee') or 'Unassigned'})": t["id"] for t in tasks}
        with u_col1:
            selected_label = st.selectbox("Select Task to Update", list(task_dict.keys()), key="dash_update_task")
        with u_col2:
            new_status = st.selectbox("New Status", ["Pending", "In Progress", "Completed", "Rejected"], key="dash_new_status")
        with u_col3:
            st.write("")
            st.write("")
            if st.button("Update Status", type="primary"):
                task_id = task_dict[selected_label]
                update_task_status(task_id, new_status)
                st.success(f"Task #{task_id} marked as {new_status}!")
                st.rerun()


def render_new_meeting():
    """Render the new meeting input page."""
    st.title("➕ New Meeting")
    st.markdown("Add meeting details and provide either an audio recording or text transcript.")

    if not api_key:
        st.error("⚠️ Groq API key is missing. Add your `GROQ_API_KEY` to the `.env` file before proceeding.")
        return

    # Button to quickly load sample test scenario for demo
    sample_file = BASE_DIR / "sample_transcript.txt"
    if sample_file.exists():
        if st.button("📋 Load Sample Hackathon Benchmark Scenario", help="Auto-fills the College Event Management Platform test case"):
            with open(sample_file, "r", encoding="utf-8") as f:
                content = f.read()
            st.session_state["input_title"] = "College Event Management Platform"
            st.session_state["input_date"] = datetime(2026, 10, 31).date()
            st.session_state["input_participants"] = "Rahul, Meera, Ananya, Arjun"
            st.session_state["pasted_transcript"] = content.split("Transcript:\n")[-1].strip()
            st.success("Sample benchmark loaded! Click 'Analyse Meeting' below.")

    # Meeting Metadata
    st.subheader("1. Meeting Details")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        meeting_title = st.text_input(
            "Meeting Title *",
            value=st.session_state.get("input_title", ""),
            placeholder="e.g., Sprint Planning or College Event Platform",
            key="input_title",
        )
    with m_col2:
        meeting_date = st.date_input(
            "Meeting Date *",
            value=st.session_state.get("input_date", datetime.now().date()),
            key="input_date",
        )

    participants = st.text_input(
        "Participants (optional)",
        value=st.session_state.get("input_participants", ""),
        placeholder="e.g., Rahul, Meera, Ananya, Arjun",
        key="input_participants",
    )

    st.divider()

    # Input Mode Selection
    st.subheader("2. Meeting Conversation Input")
    input_mode = st.radio(
        "Choose input method",
        ["Paste Transcript", "Upload Audio Recording"],
        horizontal=True,
    )

    transcript = ""

    if input_mode == "Upload Audio Recording":
        st.info("Upload recorded meeting audio (MP3, WAV, M4A, etc.). Maximum 25 MB on Groq Free Tier.")
        audio_file = st.file_uploader(
            "Choose an audio file",
            type=["mp3", "wav", "m4a", "mp4", "webm", "ogg", "flac"],
            help="Files larger than 25 MB will be rejected per Groq Whisper limits.",
        )
        audio_lang = st.text_input(
            "Audio Language (optional)",
            value="",
            placeholder="Auto-detect (or e.g. en, hi, te)",
            help="Leave blank for automatic detection",
        )

        if audio_file:
            st.audio(audio_file)
            size_mb = audio_file.size / (1024 * 1024)
            st.caption(f"File: {audio_file.name} ({size_mb:.2f} MB)")

            if size_mb > 25.0:
                st.error("⚠️ File exceeds 25 MB Groq limit. Please use a shorter recording or compressed audio.")
            else:
                if st.button("🎙️ Convert Audio to Transcript", type="primary"):
                    try:
                        with st.spinner("Transcribing audio using Groq whisper-large-v3-turbo..."):
                            transcribed_text = transcribe_audio(
                                audio_bytes=audio_file.getvalue(),
                                filename=audio_file.name,
                                language=audio_lang or None,
                            )
                            st.session_state["audio_transcript_content"] = transcribed_text
                            st.session_state["pasted_transcript"] = transcribed_text
                        st.success("Transcription complete! Review and edit the transcript below before analyzing.")
                    except Exception as e:
                        st.error(f"Transcription error: {e}")

        transcript = st.text_area(
            "Transcript (Review and edit before analysis) *",
            value=st.session_state.get("pasted_transcript", ""),
            height=260,
            placeholder="The audio transcription will appear here. You can also edit it before analyzing...",
            key="pasted_transcript",
        )

    else:
        transcript = st.text_area(
            "Paste Meeting Transcript *",
            value=st.session_state.get("pasted_transcript", ""),
            height=280,
            placeholder="Rahul: Let's review the progress...\nMeera: I will complete login testing by November 3...\nArjun: I will complete the database integration by November 5...",
            key="pasted_transcript",
        )

    st.divider()

    # Step 3: Analyze
    st.subheader("3. AI Meeting Analysis")
    can_analyze = bool(meeting_title.strip()) and bool(transcript.strip()) and len(transcript.strip()) >= 30

    if not can_analyze:
        st.caption("Please provide a Meeting Title and a Transcript of at least 30 characters to enable analysis.")

    if st.button("🧠 Analyse Meeting with AI", type="primary", disabled=not can_analyze):
        try:
            with st.spinner("Analyzing transcript with Groq (extracting decisions & action items)..."):
                result = process_meeting(
                    transcript=transcript.strip(),
                    title=meeting_title.strip(),
                    meeting_date=str(meeting_date),
                    participants=participants.strip(),
                )
                st.session_state["meeting_result"] = result
                st.session_state["review_tasks"] = result.get("tasks", [])
                st.session_state["nav_page"] = "🔍 Review AI Findings"
            st.success("Analysis complete! Redirecting to Review AI Findings...")
            st.rerun()
        except Exception as e:
            st.error(f"Analysis failed: {e}")


def render_review_findings():
    """Render the human-in-the-loop review and approval page."""
    st.title("🔍 Review AI Findings")
    st.markdown("Human-in-the-Loop Verification: Review, edit, approve, or reject proposed tasks before execution.")

    result = st.session_state.get("meeting_result")
    if not result:
        st.info("No meeting analysis currently pending review. Please add or analyze a meeting first.")
        if st.button("➕ Go to New Meeting", type="primary"):
            st.session_state["nav_page"] = "➕ New Meeting"
            st.rerun()
        return

    meeting_id = result.get("meeting_id")
    st.success(f"📁 Analysis loaded for Meeting #{meeting_id}")

    # Section A: Summary
    st.subheader("1. Meeting Summary")
    st.info(result.get("summary", "No summary generated."))

    # Section B: Decisions
    decisions = result.get("decisions", [])
    st.subheader(f"2. Confirmed Decisions ({len(decisions)})")
    if decisions:
        for idx, dec in enumerate(decisions, 1):
            st.markdown(f"- **Decision {idx}:** {dec}")
    else:
        st.caption("No confirmed decisions identified in this meeting.")

    st.divider()

    # Section C: Action Items Approval
    tasks = result.get("tasks", [])
    st.subheader(f"3. Proposed Action Items ({len(tasks)})")
    st.markdown("Edit fields directly in the table. Check the **Approve** box for tasks you authorize to be executed.")

    if not tasks:
        st.warning("No action items were extracted by the AI from this transcript.")
        return

    # Select all / Deselect all buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
    with btn_col1:
        if st.button("Select All"):
            st.session_state["approval_override"] = True
            st.rerun()
    with btn_col2:
        if st.button("Deselect All"):
            st.session_state["approval_override"] = False
            st.rerun()

    override = st.session_state.get("approval_override", None)

    # Prepare table rows
    table_rows = []
    for t in tasks:
        default_appr = override if override is not None else True
        table_rows.append({
            "Approve": default_appr,
            "Task Title": t.get("title", ""),
            "Assignee": t.get("assignee") or "",
            "Due Date (YYYY-MM-DD)": t.get("due_date") or "",
            "Priority": t.get("priority", "Unknown"),
            "Supporting Evidence (Quote)": t.get("evidence", ""),
            "Confidence": f"{int((t.get('confidence') or 0.8) * 100)}%",
        })

    # Render interactive data editor
    edited_df = st.data_editor(
        pd.DataFrame(table_rows),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Approve": st.column_config.CheckboxColumn("Approve", default=True, help="Check to approve this task for execution"),
            "Task Title": st.column_config.TextColumn("Task Title", required=True, width="medium"),
            "Assignee": st.column_config.TextColumn("Assignee", help="Person responsible", width="small"),
            "Due Date (YYYY-MM-DD)": st.column_config.TextColumn("Due Date", help="YYYY-MM-DD or leave blank", width="small"),
            "Priority": st.column_config.SelectboxColumn("Priority", options=["High", "Medium", "Low", "Unknown"], width="small"),
            "Supporting Evidence (Quote)": st.column_config.TextColumn("Evidence Quote", width="large"),
            "Confidence": st.column_config.TextColumn("AI Confidence", disabled=True, width="small"),
        },
        key="review_findings_editor",
    )

    approved_df = edited_df[edited_df["Approve"] == True]
    approved_count = len(approved_df)

    st.markdown(f"**Selected for Execution:** `{approved_count}` of `{len(tasks)}` tasks")

    # Execution Button
    st.divider()
    if st.button("🚀 Authorize & Execute Approved Tasks", type="primary", disabled=approved_count == 0):
        # Convert approved rows to clean task dicts
        approved_task_list = []
        for _, row in approved_df.iterrows():
            title = str(row["Task Title"]).strip()
            if not title:
                continue

            due = str(row["Due Date (YYYY-MM-DD)"]).strip()
            if not due or due.lower() in ("none", "null", "nan"):
                due = None

            assignee = str(row["Assignee"]).strip()
            if not assignee or assignee.lower() in ("none", "null", "nan"):
                assignee = None

            approved_task_list.append({
                "title": title,
                "assignee": assignee,
                "due_date": due,
                "priority": str(row["Priority"]).strip() or "Unknown",
                "evidence": str(row["Supporting Evidence (Quote)"]).strip(),
                "status": "Pending",
            })

        try:
            with st.spinner("Python execution layer persisting approved tasks into SQLite..."):
                exec_result = execute_approved_tasks(
                    meeting_id=meeting_id,
                    approved_tasks=approved_task_list,
                )

            if exec_result["success"]:
                st.success(f"🎉 {exec_result['message']} Tasks are now tracked in SQLite.")
                st.balloons()
                # Clear pending result so user doesn't re-execute by mistake
                st.session_state["meeting_result"] = None
                st.session_state["approval_override"] = None
                if st.button("📊 View Task Board on Dashboard"):
                    st.session_state["nav_page"] = "📊 Dashboard"
                    st.rerun()
            else:
                st.error(f"Execution failed: {exec_result['message']}")
        except Exception as exc:
            st.error(f"Error during execution: {exc}")


def render_task_manager():
    """Render the full task manager page with status updates and deletion."""
    st.title("📋 Task Manager")
    st.markdown("Detailed task management, status transitions, and audit trail.")

    stats = get_task_statistics()
    if stats["total"] == 0:
        st.info("No tasks recorded yet. Create and approve tasks from a meeting first.")
        return

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        status_f = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed", "Rejected"], key="tm_status")
    with f2:
        priority_f = st.selectbox("Priority", ["All", "High", "Medium", "Low", "Unknown"], key="tm_priority")
    with f3:
        assignee_f = st.selectbox("Assignee", ["All"] + stats["assignees"], key="tm_assignee")
    with f4:
        search_f = st.text_input("Search Title or Evidence", placeholder="Search...", key="tm_search")

    tasks = get_tasks(
        status=None if status_f == "All" else status_f,
        assignee=None if assignee_f == "All" else assignee_f,
        priority=None if priority_f == "All" else priority_f,
    )

    if search_f.strip():
        q = search_f.strip().lower()
        tasks = [t for t in tasks if q in t["title"].lower() or (t.get("evidence") and q in t["evidence"].lower())]

    st.markdown(f"**Showing {len(tasks)} tasks**")

    for task in tasks:
        due = task.get("due_date") or ""
        overdue_badge = "🚨 OVERDUE — " if is_overdue(due, task.get("status", "Pending")) else ""
        header_title = f"{overdue_badge}#{task['id']} — {task['title']} [{task.get('status', 'Pending')}]"

        with st.expander(header_title, expanded=False):
            t_col1, t_col2 = st.columns([3, 2])

            with t_col1:
                st.markdown(f"**Title:** {task['title']}")
                st.markdown(f"**Assignee:** `{task.get('assignee') or 'Unassigned'}`")
                st.markdown(f"**Due Date:** `{due or 'Not specified'}`")
                st.markdown(f"**Priority:** `{task.get('priority', 'Unknown')}`")
                st.markdown(f"**Origin Meeting:** {task.get('meeting_title') or 'N/A'}")
                if task.get("evidence"):
                    st.markdown(f"**Supporting Quote:** *\"{task['evidence']}\"*")
                st.caption(f"Created: {task.get('created_at', '')}")

            with t_col2:
                st.markdown("**Update Status**")
                curr_status = task.get("status", "Pending")
                status_choices = ["Pending", "In Progress", "Completed", "Rejected"]
                curr_idx = status_choices.index(curr_status) if curr_status in status_choices else 0

                new_st = st.selectbox(
                    "Change Status",
                    status_choices,
                    index=curr_idx,
                    key=f"tm_status_{task['id']}",
                )
                if st.button("Apply Status", key=f"apply_{task['id']}"):
                    update_task_status(task["id"], new_st)
                    st.success(f"Status changed to {new_st}")
                    st.rerun()

                st.divider()
                if st.button("🗑️ Delete Task", key=f"del_{task['id']}", help="Remove this task permanently"):
                    delete_task(task["id"])
                    st.warning(f"Task #{task['id']} deleted.")
                    st.rerun()


def render_meeting_history():
    """Render previous meetings with their summaries and linked tasks."""
    st.title("📜 Meeting History")
    st.markdown("Persistent meeting memory: Inspect past meetings, summaries, decisions, and tasks.")

    meetings = get_meetings()
    if not meetings:
        st.info("No meetings recorded in the database yet.")
        return

    for meeting in meetings:
        meeting_tasks = get_meeting_tasks(meeting["id"])
        with st.expander(f"📅 {meeting['title']} — {meeting['meeting_date']} ({len(meeting_tasks)} tasks)", expanded=False):
            m_c1, m_c2 = st.columns([3, 2])

            with m_c1:
                st.markdown("#### Summary")
                st.write(meeting.get("summary") or "No summary recorded.")

                participants = meeting.get("participants", "")
                if participants:
                    st.markdown(f"**Participants:** {participants}")

            with m_c2:
                st.markdown("#### Agreed Decisions")
                decisions = meeting.get("decisions", [])
                if decisions:
                    for idx, d in enumerate(decisions, 1):
                        st.markdown(f"{idx}. {d}")
                else:
                    st.caption("No explicit decisions recorded.")

            st.markdown("#### Extracted Tasks")
            if meeting_tasks:
                task_df = pd.DataFrame([
                    {
                        "ID": t["id"],
                        "Task": t["title"],
                        "Assignee": t.get("assignee") or "Unassigned",
                        "Due Date": t.get("due_date") or "None",
                        "Priority": t.get("priority", "Unknown"),
                        "Status": t.get("status", "Pending"),
                    }
                    for t in meeting_tasks
                ])
                st.dataframe(task_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No tasks were approved for this meeting.")


def render_about():
    """Render the about and documentation page."""
    st.title("ℹ️ About MeetingOS")
    st.markdown(
        """
        ### 🎙️ MeetingOS — AI-Powered Meeting-to-Execution Agent
        **Tagline:** *From Meeting Conversations to Actual Execution.*

        ---

        #### The Problem
        Meetings generate numerous decisions, assignments, responsibilities, and deadlines.
        However, most meeting tools focus on recording or summarizing conversations rather
        than ensuring that the discussed work actually gets completed. Action items are forgotten,
        responsibilities remain unclear, and deadlines are missed.

        #### The Solution
        MeetingOS bridges the gap between conversation and execution through a reliable
        **human-authorized agentic architecture**:

        ```
        Meeting (Audio/Transcript)
                   │
                   ▼
        Audio Transcription (Groq Whisper large-v3-turbo)
                   │
                   ▼
        AI Understanding & Extraction (Groq openai/gpt-oss-20b)
        - Meeting Summary
        - Confirmed Decisions
        - Evidence-Backed Action Items (Owners, Deadlines, Priorities)
                   │
                   ▼
        Human-in-the-Loop Review & Approval
        - Edit titles, assignees, deadlines, priorities
        - Approve or reject individual tasks
                   │
                   ▼
        Deterministic Python Execution Layer
        - Direct persistence into SQLite (No unreliable tool-call loop)
                   │
                   ▼
        Interactive Execution Dashboard
        - Real-time tracking, metrics, overdue alerts, status updates
        ```

        ---

        #### Technology Stack
        - **Frontend**: Streamlit
        - **LLM Provider**: Groq API
        - **Meeting Analysis Model**: `openai/gpt-oss-20b`
        - **Audio Transcription**: `whisper-large-v3-turbo`
        - **Database**: SQLite (local persistence, zero external db dependencies)
        - **Data Validation**: Pydantic v2
        - **Data Processing**: Pandas

        ---

        #### Security & Architecture Principles
        1. **Reliability over Complexity**: Deterministic Python execution replaces error-prone recursive LLM tool calls.
        2. **Human Authorization**: AI proposes; only the human authorizes task execution.
        3. **Untrusted Input Defense**: Transcripts are treated strictly as untrusted data, preventing prompt injections.
        4. **Zero Key Leakage**: API keys are isolated in `.env` and never logged or exposed.
        5. **No AI Hallucinations**: Every task requires an exact supporting quotation from the conversation.
        """
    )


def main():
    """Application entry point."""
    page = render_sidebar()

    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "➕ New Meeting":
        render_new_meeting()
    elif page == "🔍 Review AI Findings":
        render_review_findings()
    elif page == "📋 Task Manager":
        render_task_manager()
    elif page == "📜 Meeting History":
        render_meeting_history()
    elif page == "ℹ️ About MeetingOS":
        render_about()


if __name__ == "__main__":
    main()
