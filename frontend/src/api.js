const BASE = import.meta.env.VITE_BACKEND_URL || '';

export async function apiNewSession(){
  const res = await fetch(`${BASE}/api/session/new`, { method: 'POST' });
  if(!res.ok) throw new Error('session_new_failed');
  return res.json();
}

export async function apiTranscribe(file){
  const form = new FormData();
  form.append('file', file, file.name || 'audio.webm');
  const res = await fetch(`${BASE}/api/voice/transcribe`, { method: 'POST', body: form });
  const data = await res.json();
  if(!res.ok || !data.ok) throw new Error(data.detail || data.error || 'transcription_failed');
  return data.text;
}

export async function apiConverse(sessionId, userText){
  const res = await fetch(`${BASE}/api/voice/converse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, user_text: userText })
  });
  if(!res.ok) throw new Error('converse_failed');
  return res.json();
}

export async function apiAvailabilityToday(){
  const res = await fetch(`${BASE}/api/bookings/today`);
  if(!res.ok) throw new Error('availability_failed');
  return res.json();
}

/* NEW */
export async function apiCreateBooking(payload){
  const res = await fetch(`${BASE}/api/bookings/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if(!res.ok || !data.ok){
    const msg = data?.detail || data?.error || 'create_failed';
    throw new Error(msg);
  }
  return data.booking;
}
