import { api } from '../api.js';
import { $, esc, pill, sel, ST, state, filterBar, readFilters, bindFilters, go, refresh, toast } from '../ui.js';

export async function render(view) {
  const s = await api.stats(), pct = s.total ? Math.round(s.completed / s.total * 100) : 0;
  const head = `<h2>Dashboard</h2><p class="sub">Real-time tracking of decisions and action items from every meeting.</p>`;
  if (!s.total) {
    view.innerHTML = head + `<div class="glass hero empty"><div><div class="empty-ico">🎙️</div><h3>No tasks yet</h3><p class="sub">Process a meeting to extract your first action items.</p><button class="btn pri" id="first">➕ Create Your First Meeting</button></div></div>`;
    $('#first').onclick = () => go('new');
    return;
  }
  const tiles = [['Pending', s.pending], ['In Progress', s.in_progress], ['Completed', s.completed], ['Overdue', s.overdue]];
  view.innerHTML = head + `
  <div class="glass hero"><div class="ring"><svg width="150" height="150" viewBox="0 0 150 150"><defs><linearGradient id="g"><stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#ff5c9d"/></linearGradient></defs><circle class="t" cx="75" cy="75" r="65"/><circle class="v" id="rv" cx="75" cy="75" r="65"/></svg><div><span data-n="${pct}">0</span>%</div></div>
    <div><h3 style="margin:0 0 4px">Execution rate</h3><p class="sub" style="margin-bottom:14px">${s.completed} of ${s.total} tasks completed</p>
    <div class="grid">${tiles.map(([a, b]) => `<div class="glass stat"><b data-n="${b}">0</b><span>${a}</span></div>`).join('')}</div></div></div>
  <div class="msg ${s.overdue ? 'bad' : 'ok'}">${s.overdue ? '⚠️ ' + s.overdue + ' task(s) require action' : '✨ All deadlines on track'}</div>
  <h3>Filter &amp; search</h3>${filterBar(s.assignees)}
  <h3 id="cnt"></h3><div class="glass tw" id="tbl"></div>
  <h3>Quick status update</h3>
  <div class="row"><div><label for="u_t">Task</label><select id="u_t"></select></div><div><label for="u_s">New status</label>${sel('u_s', ST)}</div><button class="btn pri" id="u_b">Update Status</button></div>`;
  setTimeout(() => ($('#rv').style.strokeDashoffset = 408 * (1 - pct / 100)), 60);

  const load = async () => {
    const t = await api.tasks(readFilters());
    $('#cnt').textContent = `Tasks (${t.length})`;
    $('#tbl').innerHTML = t.length ? `<table><thead><tr><th>ID</th><th>Meeting</th><th>Task</th><th>Assignee</th><th>Due</th><th>Priority</th><th>Status</th><th>Conf.</th></tr></thead><tbody>${t.map(x => `<tr>
      <td>${x.id}</td><td>${esc(x.meeting_title || 'Unknown')}</td><td>${esc(x.title)}</td><td>${esc(x.assignee || 'Unassigned')}</td><td>${esc(x.due_date || 'None')}</td>
      <td>${pill(x.priority)}</td><td>${pill(x.status)} ${x.overdue ? pill('Overdue', 'over') : ''}</td><td>${Math.round((x.confidence || 0) * 100)}%</td></tr>`).join('')}</tbody></table>`
      : '<div class="msg warn">No tasks match the selected filters.</div>';
    $('#u_t').innerHTML = t.map(x => `<option value="${x.id}">#${x.id}: ${esc(x.title)} (${esc(x.assignee || 'Unassigned')})</option>`).join('');
  };
  bindFilters(load);
  $('#u_b').onclick = async () => {
    const id = $('#u_t').value; if (!id) return;
    try { await api.setStatus(id, $('#u_s').value); toast(`Task #${id} updated`); refresh(); } catch (e) { toast(e.message, 'bad'); }
  };
  await load();
}
