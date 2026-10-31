import { api } from '../api.js';
import { $, $$, esc, pill, ST, filterBar, readFilters, bindFilters, refresh, toast } from '../ui.js';

export async function render(view) {
  const s = await api.stats();
  const head = `<h2>Task Manager</h2><p class="sub">Every task, its evidence, and its status in one place.</p>`;
  if (!s.total) { view.innerHTML = head + '<div class="msg info">No tasks yet. Approve tasks from a meeting first.</div>'; return; }
  view.innerHTML = head + filterBar(s.assignees) + `<h3 id="cnt"></h3><div class="cards" id="list"></div>`;
  const load = async () => {
    const t = await api.tasks(readFilters());
    $('#cnt').textContent = `Showing ${t.length} tasks`;
    $('#list').innerHTML = t.map((x, i) => `<div class="glass tc" style="animation-delay:${Math.min(i, 10) * 40}ms">
      <div class="meta">${pill(x.status)}${pill(x.priority)}${x.overdue ? pill('Overdue', 'over') : ''}<small style="margin-left:auto;color:var(--mute)">#${x.id}</small></div>
      <h4>${esc(x.title)}</h4>${x.evidence ? `<q>${esc(x.evidence)}</q>` : ''}
      <div class="meta"><span class="who">${esc((x.assignee || '?')[0].toUpperCase())}</span>${esc(x.assignee || 'Unassigned')} · 📅 ${esc(x.due_date || 'No date')}</div>
      <small style="color:var(--mute)">${esc(x.meeting_title || '')}</small>
      <div class="gap"><select data-s="${x.id}" aria-label="Status" style="flex:1">${ST.map(o => `<option ${o == x.status ? 'selected' : ''}>${o}</option>`).join('')}</select>
      <button class="btn pri" data-apply="${x.id}">Apply</button><button class="btn" data-del="${x.id}" aria-label="Delete task">🗑️</button></div></div>`).join('') || '<div class="msg warn">No tasks match.</div>';
  };
  $('#list').onclick = async e => {
    const a = e.target.closest('[data-apply]'), d = e.target.closest('[data-del]');
    try {
      if (a) { await api.setStatus(a.dataset.apply, $(`[data-s="${a.dataset.apply}"]`).value); toast('Status updated'); refresh(); }
      if (d && confirm('Delete this task permanently?')) { await api.deleteTask(d.dataset.del); toast('Task deleted', 'info'); refresh(); }
    } catch (err) { toast(err.message, 'bad'); }
  };
  bindFilters(load);
  await load();
}
