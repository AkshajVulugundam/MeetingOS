# 🎙️ MeetingOS

**From Meeting Conversations to Actual Execution.**

An AI-powered meeting-to-execution agent. Feed it a meeting recording or transcript and it extracts a summary, confirmed decisions, and evidence-backed action items. You review and approve them, then track progress on a live dashboard.

---

## ✨ Features

- 🎧 **Audio transcription** with Groq Whisper (`whisper-large-v3-turbo`), up to 25 MB
- 🧠 **AI meeting analysis** with `openai/gpt-oss-20b`: summary, decisions, tasks, owners, deadlines, priorities
- 🔎 **Evidence-backed tasks**: every task carries an exact quote from the conversation, plus an AI confidence score
- ✅ **Human-in-the-loop approval**: edit, approve or reject each task before anything is saved
- 💾 **Persistent storage** in SQLite, with meeting history and linked tasks
- 📊 **Progress tracking**: completion ring, status filters, overdue alerts, task manager
- 🎨 **Glassmorphism UI**: bright theme, animated aurora background, floating dock navigation

## 🧭 How it works

```
Meeting (audio / transcript)
        ▼
Groq Whisper transcription
        ▼
AI extraction (summary · decisions · tasks with quotes)
        ▼
Human review & approval
        ▼
Deterministic Python execution layer → SQLite
        ▼
Interactive dashboard
```

No second LLM call happens after approval. Python saves exactly the tasks you approved.

## 🛡️ Design principles

1. **Reliability over complexity**: deterministic execution instead of fragile tool-call loops
2. **Human authorization**: the AI proposes, you approve
3. **Untrusted input defense**: transcripts are treated as data, never as instructions
4. **No key leakage**: the API key stays in `.env`
5. **No hallucinated tasks**: every task needs a supporting quote

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (ES modules, no framework) |
| Backend | Python, Flask |
| AI | Groq API (Whisper + GPT-OSS-20B, Llama 3.3 70B fallback) |
| Database | SQLite |
| Validation | Pydantic v2 |

## 📁 Project structure

```
meetingos/
├── server.py                 # Flask app + JSON API
├── services/
│   ├── agent.py              # Orchestrates analysis and approved-task execution
│   ├── database.py           # SQLite operations
│   ├── groq_service.py       # Transcription + analysis, with model fallback
│   └── validation.py         # Pydantic models and task sanitising
├── static/
│   ├── index.html
│   ├── css/                  # base.css · components.css · pages.css
│   └── js/                   # api.js · ui.js · app.js · pages/
├── sample_transcript.txt     # optional demo data
├── requirements.txt
└── .env                      # your API key (not committed)
```

## 🚀 Getting started

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com/)

### Installation

```bash
git clone https://github.com/<your-username>/meetingos.git
cd meetingos

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

### Run

```bash
python server.py
```

Open **http://localhost:5000**.

> Open the app through the server. The frontend uses ES modules, so double-clicking `index.html` won't work.

## 🧪 Quick test

1. Go to **New Meeting**.
2. Paste a transcript such as:
   ```
   Rahul: Let's review the progress.
   Meera: I will complete login testing by November 3.
   Arjun: I will finish the database integration by November 5.
   ```
3. Click **Analyse with AI**.
4. On **Review**, edit and approve tasks, then click **Authorize & execute**.
5. Check the **Dashboard** and **Tasks** pages.

Optional: add a `sample_transcript.txt` (with a line `Transcript:` followed by the meeting text) to enable the **Load sample** button.

## 🔌 API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/config` | API key and sample availability |
| GET | `/api/stats` | Task counts and assignees |
| GET | `/api/tasks` | List tasks (`status`, `priority`, `assignee`, `q`) |
| POST | `/api/tasks/<id>/status` | Update task status |
| DELETE | `/api/tasks/<id>` | Delete a task |
| GET | `/api/meetings` | Meetings with their tasks |
| POST | `/api/transcribe` | Audio → transcript |
| POST | `/api/analyze` | Transcript → summary, decisions, proposed tasks |
| POST | `/api/execute` | Save approved tasks |

## 🩹 Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit`/`flask` not recognized | Activate the virtual environment and run `pip install -r requirements.txt` |
| "API key missing" | Add `GROQ_API_KEY` to `.env` and restart the server |
| `unexpected keyword argument` from Groq | Run `pip install -U groq` |
| Analysis returns no output | The app retries automatically with a fallback model; check your Groq quota and rate limits |
| Audio rejected | Files must be under 25 MB (free-tier limit) |

## 🗺️ Roadmap

- Task assignment notifications (email / Slack)
- Export to CSV and calendar
- Multi-language transcripts
- User accounts

## 📄 License

MIT. See `LICENSE`.

---

Built with ❤️ using Groq, Flask and SQLite.
