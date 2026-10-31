async function req(url, opt = {}) {
  let res;
  try { res = await fetch(url, opt); } catch { throw new Error('Cannot reach the server. Is it running?'); }
  let data = {};
  try { data = await res.json(); } catch {}
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}
const send = (url, body, method = 'POST') =>
  req(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const api = {
  config: () => req('/api/config'),
  sample: () => req('/api/sample'),
  stats: () => req('/api/stats'),
  tasks: (params) => req('/api/tasks?' + params),
  meetings: () => req('/api/meetings'),
  setStatus: (id, status) => send(`/api/tasks/${id}/status`, { status }),
  deleteTask: (id) => req(`/api/tasks/${id}`, { method: 'DELETE' }),
  transcribe: (file, language) => {
    const fd = new FormData(); fd.append('audio', file); fd.append('language', language || '');
    return req('/api/transcribe', { method: 'POST', body: fd });
  },
  analyze: (body) => send('/api/analyze', body),
  execute: (body) => send('/api/execute', body),
};
