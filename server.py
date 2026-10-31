"""MeetingOS web server: serves static/index.html and a small JSON API."""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

from services.agent import execute_approved_tasks, process_meeting
from services.database import (delete_task, get_meeting_tasks, get_meetings, get_task_statistics,
                               get_tasks, init_db, update_task_status)
from services.groq_service import transcribe_audio
from services.validation import is_overdue

app = Flask(__name__, static_folder="static", static_url_path="/static")
init_db()


def err(e, code=500):
    return jsonify({"error": str(e)}), code


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/config")
def config():
    sample = BASE / "sample_transcript.txt"
    return jsonify({"api_key": bool(os.getenv("GROQ_API_KEY", "").strip()), "sample": sample.exists()})


@app.get("/api/sample")
def sample():
    txt = (BASE / "sample_transcript.txt").read_text(encoding="utf-8")
    return jsonify({"transcript": txt.split("Transcript:\n")[-1].strip()})


@app.get("/api/stats")
def stats():
    return jsonify(get_task_statistics())


@app.get("/api/tasks")
def tasks():
    a = request.args
    rows = get_tasks(status=a.get("status") or None, assignee=a.get("assignee") or None,
                     priority=a.get("priority") or None)
    q = (a.get("q") or "").strip().lower()
    if q:
        rows = [t for t in rows if q in t["title"].lower() or q in (t.get("evidence") or "").lower()]
    for t in rows:
        t["overdue"] = is_overdue(t.get("due_date"), t.get("status", "Pending"))
    return jsonify(rows)


@app.post("/api/tasks/<int:tid>/status")
def set_status(tid):
    try:
        return jsonify({"ok": update_task_status(tid, (request.json or {}).get("status", ""))})
    except Exception as e:
        return err(e, 400)


@app.delete("/api/tasks/<int:tid>")
def del_task(tid):
    return jsonify({"ok": delete_task(tid)})


@app.get("/api/meetings")
def meetings():
    out = get_meetings()
    for m in out:
        m.pop("transcript", None)
        m["tasks"] = get_meeting_tasks(m["id"])
    return jsonify(out)


@app.post("/api/transcribe")
def transcribe():
    try:
        f = request.files["audio"]
        return jsonify({"transcript": transcribe_audio(f.read(), f.filename, request.form.get("language") or None)})
    except Exception as e:
        return err(e)


@app.post("/api/analyze")
def analyze():
    d = request.json or {}
    try:
        return jsonify(process_meeting(transcript=d.get("transcript", "").strip(), title=d.get("title", "").strip(),
                                       meeting_date=d.get("date", ""), participants=d.get("participants", "").strip()))
    except Exception as e:
        return err(e)


@app.post("/api/execute")
def execute():
    d = request.json or {}
    try:
        return jsonify(execute_approved_tasks(meeting_id=d.get("meeting_id"), approved_tasks=d.get("tasks", [])))
    except Exception as e:
        return err(e)


if __name__ == "__main__":
    print("MeetingOS running at http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
