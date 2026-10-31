export const ST = ['Pending', 'In Progress', 'Completed', 'Rejected'];
export const PR = ['High', 'Medium', 'Low', 'Unknown'];
export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];
export const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const pill = (t, c) => `<span class="tag ${esc(c || t)}">${esc(t)}</span>`;
export const sel = (id, opts, cur) => `<select id="${id}">${opts.map(o => `<option ${o == cur ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select>`;

/* shared app state (persisted pieces live in localStorage) */
export const state = {
  cfg: { api_key: false, sample: false },
  pending: JSON.parse(localStorage.getItem('pending') || 'null'),
  done: '',
  form: { title: '', date: new Date().toISOString().slice(0, 10), parts: '', text: '' },
};
export function setPending(p) {
  state.pending = p;
  p ? localStorage.setItem('pending', JSON.stringify(p)) : localStorage.removeItem('pending');
}

/* routing helpers: pages never import app.js (no circular imports) */
export const refresh = () => document.dispatchEvent(new CustomEvent('mos:refresh'));
export const go = page => { location.hash === '#/' + page ? refresh() : (location.hash = '#/' + page); };

export function loading(on, text) {
  $('#ld').classList.toggle('on', on);
  if (text) $('#ldt').textContent = text;
}
export function toast(msg, type = 'ok') {
  const t = document.createElement('div');
  t.className = `toast ${type}`; t.textContent = msg;
  $('#toasts').appendChild(t);
  setTimeout(() => { t.style.transition = 'opacity .4s'; t.style.opacity = 0; setTimeout(() => t.remove(), 400); }, 3200);
}
export function countUp(root = document) {
  $$('[data-n]', root).forEach(e => {
    const n = +e.dataset.n, t0 = performance.now();
    (function f(t) {
      const p = Math.min((t - t0) / 700, 1);
      e.textContent = Math.round(n * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(f);
    })(t0);
  });
}
/* filter bar shared by Dashboard and Task Manager */
export const filterBar = assignees => `<div class="row">
  <div><label for="f_s">Status</label>${sel('f_s', ['All', ...ST])}</div>
  <div><label for="f_p">Priority</label>${sel('f_p', ['All', ...PR])}</div>
  <div><label for="f_a">Assignee</label>${sel('f_a', ['All', ...assignees])}</div>
  <div><label for="f_q">Search</label><input id="f_q" placeholder="Type keyword..."></div></div>`;
export const readFilters = () => {
  const v = id => ($('#' + id).value === 'All' ? '' : $('#' + id).value);
  return new URLSearchParams({ status: v('f_s'), priority: v('f_p'), assignee: v('f_a'), q: $('#f_q').value });
};
export function bindFilters(fn) {
  let t;
  ['f_s', 'f_p', 'f_a'].forEach(i => ($('#' + i).onchange = fn));
  $('#f_q').oninput = () => { clearTimeout(t); t = setTimeout(fn, 200); };
}
