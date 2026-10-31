import { api } from '../api.js';
import { esc, pill } from '../ui.js';

export async function render(view) {
  const ms = await api.meetings();
  const head = `<h2>Meeting History</h2><p class="sub">Persistent memory of past meetings, decisions and tasks.</p>`;
  if (!ms.length) { view.innerHTML = head + '<div class="msg info">No meetings recorded yet.</div>'; return; }
  view.innerHTML = head + ms.map(m => `<details class="glass"><summary>📅 ${esc(m.title)} <span class="tag" style="margin-left:8px">${esc(m.meeting_date)}</span> <span class="tag">${m.tasks.length} tasks</span></summary>
    <p>${esc(m.summary || 'No summary recorded.')}</p>${m.participants ? `<p><b>Participants:</b> ${esc(m.participants)}</p>` : ''}
    <h3>Decisions</h3>${m.decisions.length ? '<ol>' + m.decisions.map(d => `<li>${esc(d)}</li>`).join('') + '</ol>' : '<p class="sub">None recorded.</p>'}
    <h3>Tasks</h3>${m.tasks.length ? `<div class="tw"><table><thead><tr><th>ID</th><th>Task</th><th>Assignee</th><th>Due</th><th>Priority</th><th>Status</th></tr></thead><tbody>${m.tasks.map(t => `<tr><td>${t.id}</td><td>${esc(t.title)}</td><td>${esc(t.assignee || 'Unassigned')}</td><td>${esc(t.due_date || 'None')}</td><td>${pill(t.priority)}</td><td>${pill(t.status)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="sub">No tasks approved for this meeting.</p>'}</details>`).join('');
}
