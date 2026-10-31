"""Generator for a modern, responsive HTML/JS dashboard for MeetingOS.

Can be embedded directly inside Streamlit via st.components.v1.html or
downloaded as a standalone, presentation-ready HTML report.
"""

from __future__ import annotations

import json
from datetime import datetime
from services.validation import is_overdue


def generate_cool_html_dashboard(tasks: list[dict], stats: dict, meeting_title: str = "All Meetings") -> str:
    """Generate a self-contained, interactive modern dark-mode HTML dashboard."""
    total = stats.get("total", 0)
    completed = stats.get("completed", 0)
    pending = stats.get("pending", 0)
    in_progress = stats.get("in_progress", 0)
    overdue = stats.get("overdue", 0)
    completion_pct = int((completed / total * 100)) if total > 0 else 0

    # Build assignee counts for charts
    assignee_counts = {}
    for t in tasks:
        owner = t.get("assignee") or "Unassigned"
        assignee_counts[owner] = assignee_counts.get(owner, 0) + 1

    chart_labels_status = ["Pending", "In Progress", "Completed"]
    chart_data_status = [pending, in_progress, completed]

    chart_labels_assignee = list(assignee_counts.keys())
    chart_data_assignee = list(assignee_counts.values())

    # Build tasks data for JS filtering
    tasks_json = []
    for t in tasks:
        due = t.get("due_date") or ""
        task_overdue = is_overdue(due, t.get("status", "Pending"))
        tasks_json.append({
            "id": t["id"],
            "title": t["title"],
            "assignee": t.get("assignee") or "Unassigned",
            "due_date": due or "No deadline",
            "priority": t.get("priority", "Unknown"),
            "status": t.get("status", "Pending"),
            "evidence": t.get("evidence", ""),
            "meeting": t.get("meeting_title") or "Meeting",
            "overdue": task_overdue,
            "confidence": int((t.get("confidence") or 0.8) * 100),
        })

    tasks_json_str = json.dumps(tasks_json, ensure_ascii=False)
    current_time_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MeetingOS — Command Center</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #07090e;
            color: #e2e8f0;
            overflow-x: hidden;
        }}
        .font-mono {{
            font-family: 'JetBrains Mono', monospace;
        }}
        .glass-card {{
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 1rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .glass-card:hover {{
            border-color: rgba(56, 189, 248, 0.3);
            box-shadow: 0 10px 30px -10px rgba(56, 189, 248, 0.15);
            transform: translateY(-2px);
        }}
        .glow-cyan {{
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.25);
        }}
        .glow-emerald {{
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.25);
        }}
        .glow-rose {{
            box-shadow: 0 0 25px rgba(244, 63, 94, 0.25);
        }}
        .glow-amber {{
            box-shadow: 0 0 25px rgba(245, 158, 11, 0.25);
        }}
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: #0b0f19;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #1e293b;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #334155;
        }}
        .badge-priority-High {{
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.3);
        }}
        .badge-priority-Medium {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .badge-priority-Low {{
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .badge-priority-Unknown {{
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.3);
        }}
        .pulse-dot {{
            animation: pulseAnimation 2s infinite;
        }}
        @keyframes pulseAnimation {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <!-- Top Header -->
    <header class="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
            <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-xl shadow-lg shadow-cyan-500/20">
                    🎙️
                </div>
                <div>
                    <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                        MeetingOS <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 ml-2">PRO EXECUTION</span>
                    </h1>
                    <p class="text-xs md:text-sm text-slate-400 mt-0.5">
                        {meeting_title} &bull; <span class="text-slate-500">{current_time_str}</span>
                    </p>
                </div>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <div class="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300">
                <span class="h-2 w-2 rounded-full bg-emerald-400 pulse-dot"></span>
                <span>Agentic Execution Engine Active</span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto space-y-8">

        <!-- Metrics KPI Row -->
        <section class="grid grid-cols-2 md:grid-cols-5 gap-4">

            <!-- Total Tasks -->
            <div class="glass-card p-5 relative overflow-hidden">
                <div class="absolute -right-4 -bottom-4 w-16 h-16 bg-cyan-500/10 rounded-full blur-xl"></div>
                <div class="text-xs font-medium uppercase tracking-wider text-slate-400">Total Tasks</div>
                <div class="text-3xl md:text-4xl font-extrabold text-white mt-2 font-mono">{total}</div>
                <div class="mt-2 text-xs text-slate-400 flex items-center gap-1">
                    <span>From conversation audio</span>
                </div>
            </div>

            <!-- Pending -->
            <div class="glass-card p-5 relative overflow-hidden">
                <div class="absolute -right-4 -bottom-4 w-16 h-16 bg-amber-500/10 rounded-full blur-xl"></div>
                <div class="text-xs font-medium uppercase tracking-wider text-amber-400">Pending</div>
                <div class="text-3xl md:text-4xl font-extrabold text-amber-300 mt-2 font-mono">{pending}</div>
                <div class="mt-2 text-xs text-slate-400">Awaiting action</div>
            </div>

            <!-- In Progress -->
            <div class="glass-card p-5 relative overflow-hidden">
                <div class="absolute -right-4 -bottom-4 w-16 h-16 bg-blue-500/10 rounded-full blur-xl"></div>
                <div class="text-xs font-medium uppercase tracking-wider text-blue-400">In Progress</div>
                <div class="text-3xl md:text-4xl font-extrabold text-blue-300 mt-2 font-mono">{in_progress}</div>
                <div class="mt-2 text-xs text-slate-400">Currently active</div>
            </div>

            <!-- Completed -->
            <div class="glass-card p-5 relative overflow-hidden">
                <div class="absolute -right-4 -bottom-4 w-16 h-16 bg-emerald-500/10 rounded-full blur-xl"></div>
                <div class="text-xs font-medium uppercase tracking-wider text-emerald-400">Completed</div>
                <div class="text-3xl md:text-4xl font-extrabold text-emerald-300 mt-2 font-mono">{completed}</div>
                <div class="mt-2 text-xs text-emerald-400/80 font-medium">{completion_pct}% Execution Rate</div>
            </div>

            <!-- Overdue -->
            <div class="glass-card p-5 relative overflow-hidden border-rose-900/40">
                <div class="absolute -right-4 -bottom-4 w-16 h-16 bg-rose-500/10 rounded-full blur-xl"></div>
                <div class="text-xs font-medium uppercase tracking-wider text-rose-400 flex items-center justify-between">
                    <span>Overdue</span>
                    {f'<span class="h-2 w-2 rounded-full bg-rose-500 pulse-dot"></span>' if overdue > 0 else ''}
                </div>
                <div class="text-3xl md:text-4xl font-extrabold { 'text-rose-400' if overdue > 0 else 'text-slate-400' } mt-2 font-mono">{overdue}</div>
                <div class="mt-2 text-xs { 'text-rose-400' if overdue > 0 else 'text-slate-400' }">
                    { f'{overdue} deadline alerts' if overdue > 0 else 'All deadlines on track' }
                </div>
            </div>

        </section>

        <!-- Visual Analytics Row (Charts & Progress) -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <!-- Overall Progress Bar Card -->
            <div class="glass-card p-6 flex flex-col justify-between">
                <div>
                    <h2 class="text-base font-bold text-white mb-1 flex items-center gap-2">
                        <span>🎯 Execution Velocity</span>
                    </h2>
                    <p class="text-xs text-slate-400 mb-4">Real-time completion percentage across all assigned action items</p>

                    <div class="space-y-3">
                        <div class="flex justify-between text-sm">
                            <span class="text-slate-300 font-medium">Completion Ratio</span>
                            <span class="font-mono font-bold text-emerald-400">{completed} / {total}</span>
                        </div>
                        <div class="w-full h-3.5 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700">
                            <div class="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-1000" style="width: {completion_pct}%"></div>
                        </div>
                    </div>
                </div>

                <div class="mt-6 pt-4 border-t border-slate-800/80 grid grid-cols-3 gap-2 text-center text-xs">
                    <div class="p-2 rounded-lg bg-slate-900/60">
                        <div class="text-slate-400">Pending</div>
                        <div class="font-bold text-amber-400 font-mono mt-0.5">{pending}</div>
                    </div>
                    <div class="p-2 rounded-lg bg-slate-900/60">
                        <div class="text-slate-400">Active</div>
                        <div class="font-bold text-blue-400 font-mono mt-0.5">{in_progress}</div>
                    </div>
                    <div class="p-2 rounded-lg bg-slate-900/60">
                        <div class="text-slate-400">Done</div>
                        <div class="font-bold text-emerald-400 font-mono mt-0.5">{completed}</div>
                    </div>
                </div>
            </div>

            <!-- Status Doughnut Chart -->
            <div class="glass-card p-6 flex flex-col items-center">
                <h2 class="text-base font-bold text-white mb-1 w-full text-left">📊 Task Status Breakdown</h2>
                <p class="text-xs text-slate-400 mb-4 w-full text-left">Distribution by execution stage</p>
                <div class="relative w-48 h-48 flex items-center justify-center">
                    <canvas id="statusChart"></canvas>
                </div>
            </div>

            <!-- Assignee Bar Chart -->
            <div class="glass-card p-6 flex flex-col justify-between">
                <div>
                    <h2 class="text-base font-bold text-white mb-1">👥 Team Workload</h2>
                    <p class="text-xs text-slate-400 mb-4">Task distribution by team member</p>
                </div>
                <div class="h-44 w-full">
                    <canvas id="assigneeChart"></canvas>
                </div>
            </div>

        </section>

        <!-- Tasks Filter & Card Grid -->
        <section class="space-y-4">

            <!-- Controls Bar -->
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
                <!-- Filter Pills -->
                <div class="flex flex-wrap gap-2" id="filterPills">
                    <button onclick="filterTasks('ALL')" class="filter-btn active px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 text-white shadow-sm" data-filter="ALL">
                        All ({total})
                    </button>
                    <button onclick="filterTasks('Pending')" class="filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="Pending">
                        Pending ({pending})
                    </button>
                    <button onclick="filterTasks('In Progress')" class="filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="In Progress">
                        In Progress ({in_progress})
                    </button>
                    <button onclick="filterTasks('Completed')" class="filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="Completed">
                        Completed ({completed})
                    </button>
                    {f'''<button onclick="filterTasks('OVERDUE')" class="filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-950/80 text-rose-300 hover:bg-rose-900 border border-rose-800" data-filter="OVERDUE">
                        Overdue ({overdue})
                    </button>''' if overdue > 0 else ''}
                </div>

                <!-- Instant Search Box -->
                <div class="w-full sm:w-64">
                    <input type="text" id="taskSearchInput" onkeyup="searchTasks()" placeholder="🔍 Search tasks or evidence..."
                        class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors">
                </div>
            </div>

            <!-- Task Cards Grid -->
            <div id="tasksGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Rendered dynamically by JavaScript -->
            </div>

            <!-- Empty State Container -->
            <div id="emptyTasksState" class="hidden glass-card p-12 text-center">
                <div class="text-4xl mb-3">🔍</div>
                <h3 class="text-base font-bold text-white">No tasks match your criteria</h3>
                <p class="text-xs text-slate-400 mt-1">Try switching filters or search terms.</p>
            </div>

        </section>

    </main>

    <!-- Footer -->
    <footer class="max-w-7xl mx-auto mt-12 pt-6 border-t border-slate-800/80 text-center text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-2">
        <div>
            MeetingOS &bull; Powered by <span class="text-cyan-400 font-medium">Groq (Whisper + GPT-OSS-20B)</span> &bull; Local SQLite
        </div>
        <div class="font-mono text-[11px] text-slate-600">
            Human-in-the-Loop Verified Architecture
        </div>
    </footer>

    <!-- Interactive Logic -->
    <script>
        const allTasks = {tasks_json_str};
        let currentFilter = 'ALL';
        let searchQuery = '';

        function renderTasks() {{
            const grid = document.getElementById('tasksGrid');
            const emptyState = document.getElementById('emptyTasksState');
            grid.innerHTML = '';

            const filtered = allTasks.filter(task => {{
                // Status filter
                if (currentFilter === 'OVERDUE' && !task.overdue) return false;
                if (currentFilter !== 'ALL' && currentFilter !== 'OVERDUE' && task.status !== currentFilter) return false;

                // Search query
                if (searchQuery.trim() !== '') {{
                    const q = searchQuery.toLowerCase();
                    const inTitle = task.title.toLowerCase().includes(q);
                    const inAssignee = task.assignee.toLowerCase().includes(q);
                    const inEvidence = (task.evidence || '').toLowerCase().includes(q);
                    if (!inTitle && !inAssignee && !inEvidence) return false;
                }}
                return true;
            }});

            if (filtered.length === 0) {{
                grid.classList.add('hidden');
                emptyState.classList.remove('hidden');
                return;
            }}

            grid.classList.remove('hidden');
            emptyState.classList.add('hidden');

            filtered.forEach(task => {{
                const card = document.createElement('div');
                card.className = `glass-card p-5 flex flex-col justify-between relative overflow-hidden ${{task.overdue ? 'border-rose-700/60' : ''}}`;

                const statusBadgeColors = {{
                    'Pending': 'bg-amber-950/80 text-amber-300 border-amber-800',
                    'In Progress': 'bg-blue-950/80 text-blue-300 border-blue-800',
                    'Completed': 'bg-emerald-950/80 text-emerald-300 border-emerald-800',
                    'Rejected': 'bg-slate-800 text-slate-400 border-slate-700'
                }};
                const statusBadge = statusBadgeColors[task.status] || 'bg-slate-800 text-slate-400 border-slate-700';

                card.innerHTML = `
                    <div>
                        <!-- Top Meta -->
                        <div class="flex items-center justify-between gap-2 mb-2.5">
                            <span class="text-[11px] font-mono text-slate-500 font-semibold">#${{task.id}} &bull; ${{task.meeting}}</span>
                            <div class="flex items-center gap-1.5">
                                ${{task.overdue ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800 animate-pulse">OVERDUE</span>' : ''}}
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${{statusBadge}}">${{task.status}}</span>
                            </div>
                        </div>

                        <!-- Title -->
                        <h4 class="text-sm font-bold text-white tracking-tight leading-snug mb-3">
                            ${{task.title}}
                        </h4>

                        <!-- Evidence Quote -->
                        ${{task.evidence ? `
                            <div class="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800/80 text-xs text-slate-300 italic mb-4">
                                <span class="text-cyan-500 font-bold not-italic">Quote:</span> "${{task.evidence}}"
                            </div>
                        ` : ''}}
                    </div>

                    <!-- Bottom Details -->
                    <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                        <div class="flex items-center gap-1.5">
                            <span class="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center text-[10px] text-cyan-400 font-bold">
                                ${{task.assignee.charAt(0).toUpperCase()}}
                            </span>
                            <span class="font-medium text-slate-200">${{task.assignee}}</span>
                        </div>

                        <div class="flex items-center gap-2">
                            <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold badge-priority-${{task.priority}}">${{task.priority}}</span>
                            <span class="text-[11px] font-mono ${{task.overdue ? 'text-rose-400 font-bold' : 'text-slate-400'}}">📅 ${{task.due_date}}</span>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function filterTasks(filter) {{
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                if (btn.getAttribute('data-filter') === filter) {{
                    btn.className = 'filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 text-white shadow-sm';
                }} else {{
                    btn.className = 'filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700';
                }}
            }});
            renderTasks();
        }}

        function searchTasks() {{
            searchQuery = document.getElementById('taskSearchInput').value;
            renderTasks();
        }}

        // Initialize Charts
        window.onload = function() {{
            renderTasks();

            // Status Doughnut Chart
            const ctxStatus = document.getElementById('statusChart').getContext('2d');
            new Chart(ctxStatus, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(chart_labels_status)},
                    datasets: [{{
                        data: {json.dumps(chart_data_status)},
                        backgroundColor: ['#f59e0b', '#38bdf8', '#10b981'],
                        borderColor: '#07090e',
                        borderWidth: 3,
                        hoverOffset: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    cutout: '72%'
                }}
            }});

            // Assignee Workload Bar Chart
            const ctxAssignee = document.getElementById('assigneeChart').getContext('2d');
            new Chart(ctxAssignee, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(chart_labels_assignee)},
                    datasets: [{{
                        label: 'Tasks',
                        data: {json.dumps(chart_data_assignee)},
                        backgroundColor: 'rgba(56, 189, 248, 0.45)',
                        borderColor: '#38bdf8',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}
                        }},
                        y: {{
                            beginAtZero: true,
                            grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                            ticks: {{ color: '#94a3b8', stepSize: 1, font: {{ size: 10 }} }}
                        }}
                    }}
                }}
            }});
        }};
    </script>
</body>
</html>"""
    return html_code
