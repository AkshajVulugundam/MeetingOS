const STEPS = [['🎙️', 'Audio / transcript', 'Groq Whisper'], ['🧠', 'AI extraction', 'Summary, decisions, evidence-backed tasks'], ['✅', 'Human review', 'Edit, approve, reject'], ['💾', 'Python execution', 'Direct SQLite save'], ['📊', 'Dashboard', 'Live tracking & overdue alerts']];
export async function render(view) {
  view.innerHTML = `<h2>About MeetingOS</h2><p class="sub">From conversations to actual execution.</p>
  <div class="glass pad"><h3>The problem</h3><p>Meetings produce decisions, owners and deadlines, but most tools only record or summarize. Action items get forgotten and deadlines slip.</p>
  <h3>The pipeline</h3><div class="grid pipe">${STEPS.map(([i, a, b], n) => `<div class="glass stat" style="animation-delay:${n * 80}ms"><div style="font-size:1.8rem">${i}</div><b style="font-size:1.05rem">${a}</b><span>${b}</span></div>`).join('')}</div>
  <h3>Principles</h3><p><b>Reliability over complexity</b> · <b>Human authorization</b> · <b>Untrusted-input defense</b> · <b>Zero key leakage</b> · <b>Every task needs a quote</b></p>
  <h3>Stack</h3><p>HTML/CSS/JS modules · Flask · Groq (Whisper + GPT-OSS-20B) · SQLite · Pydantic v2</p></div>`;
}
