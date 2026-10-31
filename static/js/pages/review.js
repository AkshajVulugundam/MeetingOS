import { api } from '../api.js';
import { $, $$, esc, PR, state, setPending, loading, go, refresh, toast } from '../ui.js';

const row = t => `<tr><td><input type="checkbox" class="ap" aria-label="Approve" ${t.ap === false ? '' : 'checked'} style="width:auto"></td>
  <td><input class="ti" value="${esc(t.title)}"></td><td><input class="as" value="${esc(t.assignee || '')}"></td>
  <td><input class="du" value="${esc(t.due_date || '')}" placeholder="YYYY-MM-DD"></td>
  <td><select class="pr">${PR.map(o => `<option ${o == (t.priority || 'Unknown') ? 'selected' : ''}>${o}</option>`).join('')}</select></td>
  <td><input class="ev" value="${esc(t.evidence || '')}"></td>
  <td class="cf" data-c="${t.confidence ?? .8}">${Math.round((t.confidence ?? .8) * 100)}%</td></tr>`;

export async function render(view) {
  const head = `<h2>Review AI Findings</h2><p class="sub">You stay in control: edit, approve or reject every proposed task before it is saved.</p>`;
  if (state.done) {
    view.innerHTML = head + `<div class="msg ok">🎉 ${esc(state.done)} Tasks are now tracked.</div><button class="btn pri" id="b">📊 View Task Board</button>`;
    $('#b').onclick = () => { state.done = ''; go('dashboard'); };
    return;
  }
  const r = state.pending;
  if (!r) {
    view.innerHTML = head + `<div class="msg info">Nothing pending review. Analyse a meeting first.</div><button class="btn pri" id="b">➕ New Meeting</button>`;
    $('#b').onclick = () => go('new');
    return;
  }
  const dec = r.decisions || [], tasks = r.tasks || [];
  let h = head + `<div class="msg ok">📁 Analysis loaded for meeting #${r.meeting_id}</div>
    <h3>Summary</h3><div class="glass" style="padding:18px 22px">${esc(r.summary || 'No summary generated.')}</div>
    <h3>Confirmed decisions (${dec.length})</h3>${dec.length ? dec.map((d, i) => `<div class="glass" style="padding:12px 18px;margin:8px 0"><b>${i + 1}.</b> ${esc(d)}</div>`).join('') : '<p class="sub">No confirmed decisions identified.</p>'}
    <h3>Proposed action items (${tasks.length})</h3>`;
  if (!tasks.length) { view.innerHTML = h + '<div class="msg warn">No action items were extracted from this transcript.</div>'; return; }
  view.innerHTML = h + `<div class="gap"><button class="btn" id="sa">Select all</button><button class="btn" id="da">Deselect all</button><button class="btn" id="ar">➕ Add row</button></div>
  <div class="glass tw"><table><thead><tr><th>Approve</th><th>Task</th><th>Assignee</th><th>Due</th><th>Priority</th><th>Evidence quote</th><th>AI conf.</th></tr></thead><tbody id="tb">${tasks.map(row).join('')}</tbody></table></div>
  <p id="sc"></p><div id="re"></div><button class="btn pri" id="ex">🚀 Authorize &amp; execute approved tasks</button>`;
  const upd = () => {
    const n = $$('.ap:checked').length;
    $('#sc').innerHTML = `<b>${n}</b> of ${$$('#tb tr').length} tasks selected`;
    $('#ex').disabled = !n;
  };
  $('#tb').onchange = upd; upd();
  $('#sa').onclick = () => { $$('.ap').forEach(c => (c.checked = true)); upd(); };
  $('#da').onclick = () => { $$('.ap').forEach(c => (c.checked = false)); upd(); };
  $('#ar').onclick = () => { $('#tb').insertAdjacentHTML('beforeend', row({ title: '', confidence: .8 })); upd(); };
  $('#ex').onclick = async () => {
    const list = $$('#tb tr').filter(r => $('.ap', r).checked && $('.ti', r).value.trim()).map(r => ({
      title: $('.ti', r).value.trim(), assignee: $('.as', r).value.trim() || null, due_date: $('.du', r).value.trim() || null,
      priority: $('.pr', r).value, evidence: $('.ev', r).value.trim(), confidence: +$('.cf', r).dataset.c, status: 'Pending',
    }));
    loading(true, 'Saving approved tasks...');
    try {
      const x = await api.execute({ meeting_id: r.meeting_id, tasks: list });
      loading(false);
      if (x.success) { state.done = x.message; setPending(null); toast('Tasks saved'); refresh(); }
      else $('#re').innerHTML = `<div class="msg bad">Execution failed: ${esc(x.message)}</div>`;
    } catch (e) { loading(false); $('#re').innerHTML = `<div class="msg bad">Error: ${esc(e.message)}</div>`; }
  };
}
