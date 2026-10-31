import { api } from '../api.js';
import { $, esc, state, setPending, loading, go, toast } from '../ui.js';

export async function render(view) {
  const head = `<h2>New Meeting</h2><p class="sub">Add meeting details, then paste a transcript or upload a recording.</p>`;
  if (!state.cfg.api_key) {
    view.innerHTML = head + `<div class="msg bad">⚠️ Groq API key is missing. Add <code>GROQ_API_KEY</code> to your .env file and restart the server.</div>`;
    return;
  }
  view.innerHTML = head + `${state.cfg.sample ? '<button class="btn" id="smp">📋 Load sample scenario</button>' : ''}
  <h3>1 · Details</h3><div class="glass pad"><div class="row"><div><label for="m_t">Meeting title *</label><input id="m_t" placeholder="e.g., Sprint Planning"></div><div><label for="m_d">Date *</label><input type="date" id="m_d"></div></div>
  <label for="m_p">Participants (optional)</label><input id="m_p" placeholder="Rahul, Meera, Ananya, Arjun"></div>
  <h3>2 · Conversation</h3><div class="glass pad"><label for="m_f">Audio recording (optional · max 25 MB)</label>
  <div class="row"><input type="file" id="m_f" accept=".mp3,.wav,.m4a,.mp4,.webm,.ogg,.flac"><input id="m_l" placeholder="Language (blank = auto: en, hi, te)"><button class="btn" id="m_tr">🎙️ Convert to transcript</button></div>
  <label for="m_x">Transcript * (paste or edit)</label><textarea id="m_x" rows="11" placeholder="Rahul: Let's review progress...&#10;Meera: I will finish login testing by November 3..."></textarea></div>
  <h3>3 · Analysis</h3><div class="gap"><button class="btn pri" id="m_go">🧠 Analyse with AI</button><span id="m_h" class="sub" style="margin:0;font-size:.85rem"></span></div><div id="m_e"></div>`;
  const m = { t: $('#m_t'), d: $('#m_d'), p: $('#m_p'), x: $('#m_x') };
  const f = state.form; m.t.value = f.title; m.d.value = f.date; m.p.value = f.parts; m.x.value = f.text;
  const check = () => {
    Object.assign(state.form, { title: m.t.value, date: m.d.value, parts: m.p.value, text: m.x.value });
    const ok = m.t.value.trim() && m.d.value && m.x.value.trim().length >= 30;
    $('#m_go').disabled = !ok;
    $('#m_h').textContent = ok ? '' : 'Needs a title and at least 30 characters of transcript.';
  };
  Object.values(m).forEach(e => (e.oninput = check)); check();

  if ($('#smp')) $('#smp').onclick = async () => {
    try { const r = await api.sample(); m.t.value = 'College Event Management Platform'; m.d.value = '2026-10-31'; m.p.value = 'Rahul, Meera, Ananya, Arjun'; m.x.value = r.transcript; check(); toast('Sample loaded', 'info'); }
    catch (e) { toast(e.message, 'bad'); }
  };
  $('#m_tr').onclick = async () => {
    const file = $('#m_f').files[0];
    if (!file) return toast('Choose an audio file first', 'info');
    if (file.size > 25 * 1048576) return toast('File exceeds the 25 MB limit', 'bad');
    loading(true, 'Transcribing audio...');
    try { m.x.value = (await api.transcribe(file, $('#m_l').value.trim())).transcript; check(); toast('Transcription complete. Review it before analysing.'); }
    catch (e) { $('#m_e').innerHTML = `<div class="msg bad">Transcription error: ${esc(e.message)}</div>`; }
    loading(false);
  };
  $('#m_go').onclick = async () => {
    loading(true, 'Extracting decisions & action items...');
    try {
      setPending(await api.analyze({ title: m.t.value.trim(), date: m.d.value, participants: m.p.value.trim(), transcript: m.x.value.trim() }));
      state.done = ''; loading(false); go('review');
    } catch (e) { loading(false); $('#m_e').innerHTML = `<div class="msg bad">Analysis failed: ${esc(e.message)}</div>`; }
  };
}
