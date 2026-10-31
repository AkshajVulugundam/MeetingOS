import { api } from './api.js';
import { $, state } from './ui.js';
import { countUp } from './ui.js';
import * as dashboard from './pages/dashboard.js';
import * as newMeeting from './pages/newMeeting.js';
import * as review from './pages/review.js';
import * as tasks from './pages/tasks.js';
import * as history from './pages/history.js';
import * as about from './pages/about.js';

const ROUTES = {
  dashboard: ['📊', 'Dashboard', dashboard],
  new: ['➕', 'New Meeting', newMeeting],
  review: ['🔍', 'Review', review],
  tasks: ['📋', 'Tasks', tasks],
  history: ['📜', 'History', history],
  about: ['ℹ️', 'About', about],
};

function renderDock(active) {
  $('#dock').innerHTML = Object.entries(ROUTES).map(([k, [i, l]]) =>
    `<a href="#/${k}" class="${k === active ? 'on' : ''}" aria-label="${l}" ${k === active ? 'aria-current="page"' : ''}><em>${i}</em><span>${l}</span></a>`).join('');
}
async function renderChips() {
  const s = await api.stats().catch(() => ({ total: 0, overdue: 0 }));
  $('#chips').innerHTML = `<span class="chip"><i class="dot ${state.cfg.api_key ? '' : 'off'}"></i>${state.cfg.api_key ? 'Groq connected' : 'API key missing'}</span>
    <span class="chip">${s.total} tasks</span><span class="chip">${s.overdue} overdue</span>`;
}
let seq = 0;
async function route(scroll = true) {
  const key = location.hash.replace('#/', '') || 'dashboard';
  const name = ROUTES[key] ? key : 'dashboard';
  const me = ++seq, view = $('#view');
  renderDock(name);
  renderChips();
  view.classList.remove('enter'); void view.offsetWidth; view.classList.add('enter');
  if (scroll) window.scrollTo({ top: 0, behavior: 'smooth' });
  try {
    await ROUTES[name][2].render(view);
    if (me === seq) countUp(view);
  } catch (e) {
    view.innerHTML = `<div class="msg bad">Something went wrong: ${String(e.message).replace(/</g, '&lt;')}</div>`;
  }
}
window.addEventListener('hashchange', () => route());
document.addEventListener('mos:refresh', () => route(false));
(async () => {
  try { state.cfg = await api.config(); } catch {}
  route();
})();
