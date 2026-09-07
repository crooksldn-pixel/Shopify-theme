/* CROOKS Assistant — tablet client.
 *
 * Three Android/Chrome behaviours dictate most of the awkward code here, and all three fail
 * silently rather than throwing:
 *   1. speechSynthesis needs a real user gesture before it will ever speak. We fire a
 *      zero-length utterance inside the first touch handler to unlock it.
 *   2. speechSynthesis truncates long utterances. We chunk to ~200 characters on sentence
 *      boundaries and chain on `onend`.
 *   3. getVoices() returns [] on the first call. We read it eagerly AND listen for
 *      `voiceschanged`.
 * pause() is never called: on Android it behaves as cancel(), so a "pause" is unrecoverable.
 */
'use strict';

const $ = (id) => document.getElementById(id);

const el = {
  conn: $('conn'), stage: $('stage'), state: $('state-label'), heard: $('heard'),
  answer: $('answer'), timings: $('timings'), talk: $('talk'), talkLabel: $('talk-label'),
  settings: $('settings'), settingsBtn: $('settings-btn'), closeSettings: $('close-settings'),
  voiceSelect: $('voice-select'), voiceNote: $('voice-note'), preview: $('preview-voice'),
  micTest: $('mic-test'), speakToggle: $('speak-toggle'), timingToggle: $('timing-toggle'),
  health: $('health-detail'), resetSession: $('reset-session'),
};

const store = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : v; } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* private mode */ } },
};

let sessionId = store.get('crooks.session', '') || (Math.random().toString(36).slice(2, 14));
store.set('crooks.session', sessionId);
// How many turns this conversation has had, as far as the tablet knows. Sent with each turn
// so the backend can tell "new conversation" from "I restarted and forgot yours".
let turns = parseInt(store.get('crooks.turns', '0'), 10) || 0;
let statePoll = null;

let mediaRecorder = null;
let chunks = [];
let recording = false;
let busy = false;
let wakeLock = null;
let speechUnlocked = false;
let voices = [];

/* ------------------------------------------------------------------ state */

function setState(state, label) {
  el.stage.dataset.state = state;
  el.state.textContent = label || state.toLowerCase().replace(/^./, (c) => c.toUpperCase());
}

function setConn(state, text) {
  el.conn.dataset.state = state;
  el.conn.textContent = text;
}

/* -------------------------------------------------------------- wake lock */

async function acquireWakeLock() {
  if (!('wakeLock' in navigator)) return;
  try {
    wakeLock = await navigator.wakeLock.request('screen');
    wakeLock.addEventListener('release', () => { wakeLock = null; });
  } catch { /* denied or unsupported; the screen will just sleep */ }
}
// Android drops the lock whenever the page is hidden, so re-acquire on every return.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') acquireWakeLock();
  else stopSpeaking();
});

/* ------------------------------------------------------------------ voices */

function loadVoices() {
  const list = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  if (!list.length) return;                       // first call is empty in Chrome — wait for the event
  voices = list;
  const saved = store.get('crooks.voice', '');
  el.voiceSelect.innerHTML = '';
  const sorted = [...voices].sort((a, b) => {
    const rank = (v) => (v.lang === 'en-GB' ? 0 : v.lang.startsWith('en') ? 1 : 2);
    return rank(a) - rank(b) || a.name.localeCompare(b.name);
  });
  for (const voice of sorted) {
    const option = document.createElement('option');
    option.value = voice.name;
    option.textContent = `${voice.name} · ${voice.lang}${voice.localService ? ' · offline' : ''}`;
    if (voice.name === saved) option.selected = true;
    el.voiceSelect.appendChild(option);
  }
  const anyLocalGB = voices.some((v) => v.lang === 'en-GB' && v.localService);
  el.voiceNote.textContent = anyLocalGB
    ? 'A British offline voice is installed.'
    : 'No offline British voice found. Settings → General management → Text-to-speech → Install voice data.';
}
if (window.speechSynthesis) {
  loadVoices();
  window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
}
el.voiceSelect.addEventListener('change', () => store.set('crooks.voice', el.voiceSelect.value));

/* ------------------------------------------------------------------ speech */

function unlockSpeech() {
  // Must happen inside a user gesture. Chrome M71 removed speech without user activation, and
  // the failure mode is total silence with no error anywhere.
  if (speechUnlocked || !window.speechSynthesis) return;
  try {
    const primer = new SpeechSynthesisUtterance('');
    primer.volume = 0;
    window.speechSynthesis.speak(primer);
    speechUnlocked = true;
  } catch { /* nothing more we can do */ }
}

function stopSpeaking() {
  if (window.speechSynthesis) { try { window.speechSynthesis.cancel(); } catch { /* noop */ } }
}

function chunkForSpeech(text, limit = 200) {
  const sentences = text.match(/[^.!?]+[.!?]*\s*/g) || [text];
  const out = [];
  let current = '';
  for (const sentence of sentences) {
    if ((current + sentence).length > limit && current) { out.push(current.trim()); current = ''; }
    if (sentence.length > limit) {
      for (const piece of sentence.match(new RegExp(`.{1,${limit}}(\\s|$)`, 'g')) || [sentence]) {
        out.push(piece.trim());
      }
    } else {
      current += sentence;
    }
  }
  if (current.trim()) out.push(current.trim());
  return out.filter(Boolean);
}

function speak(text) {
  if (!window.speechSynthesis || !el.speakToggle.checked || !text) return;
  stopSpeaking();
  const parts = chunkForSpeech(text);
  const chosen = voices.find((v) => v.name === el.voiceSelect.value);
  let index = 0;
  const next = () => {
    if (index >= parts.length) { if (!busy) setState('READY'); return; }
    const utterance = new SpeechSynthesisUtterance(parts[index++]);
    if (chosen) { utterance.voice = chosen; utterance.lang = chosen.lang; }
    else utterance.lang = 'en-GB';
    utterance.rate = 1.0;
    utterance.onend = next;
    utterance.onerror = next;   // never leave the chain hanging on a failed chunk
    window.speechSynthesis.speak(utterance);
  };
  setState('SPEAKING');
  next();
}

/* ------------------------------------------------------------------ health */

async function pollHealth() {
  try {
    const response = await fetch('/health', { cache: 'no-store' });
    const data = await response.json();
    const failed = Object.entries(data.checks).filter(([, c]) => !c.ok).map(([k]) => k);
    if (!failed.length) setConn('ok', 'Connected');
    else setConn('degraded', `${failed.join(', ')} down`);
    el.health.textContent = Object.entries(data.checks)
      .map(([k, c]) => `${c.ok ? 'ok  ' : 'FAIL'} ${k.padEnd(15)} ${c.detail}`)
      .join('\n');
  } catch {
    setConn('down', 'Backend unreachable');
    el.health.textContent = 'Cannot reach the backend.';
  }
}
pollHealth();
setInterval(pollHealth, 15000);

/* --------------------------------------------------------------- recording */

function pickMimeType() {
  const candidates = [
    'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4',
  ];
  for (const type of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) return type;
  }
  return '';
}

async function startRecording() {
  if (recording || busy) return;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setState('ERROR');
    el.answer.textContent = window.isSecureContext
      ? 'This browser has no microphone support.'
      : 'The microphone needs a secure HTTPS connection. Open the tailscale ts.net address, not the LAN address.';
    return;
  }
  stopSpeaking();
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true, noiseSuppression: true, autoGainControl: true,
        channelCount: 1,
        sampleRate: { ideal: 16000 },   // ideal, never exact — exact fails outright on some devices
      },
    });
    const mimeType = pickMimeType();
    mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType, audioBitsPerSecond: 32000 } : {});
    chunks = [];
    mediaRecorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      if (blob.size > 800) sendAudio(blob);
      else { setState('READY'); el.answer.textContent = 'That was too short — hold the button while you speak.'; }
    };
    mediaRecorder.start(250);
    recording = true;
    el.talk.dataset.recording = 'true';
    el.talkLabel.textContent = 'Listening…';
    setState('LISTENING');
  } catch (error) {
    setState('ERROR');
    el.answer.textContent = error && error.name === 'NotAllowedError'
      ? 'Microphone permission was refused. Allow it in the browser settings, choosing "While using the app".'
      : `Could not open the microphone: ${error}`;
  }
}

function stopRecording() {
  if (!recording) return;
  recording = false;
  el.talk.dataset.recording = 'false';
  el.talkLabel.textContent = 'Hold to talk';
  try { mediaRecorder.stop(); } catch { /* already stopped */ }
}

/* -------------------------------------------------------------------- turn */

function renderTimings(timings) {
  if (!el.timingToggle.checked || !timings) { el.timings.hidden = true; return; }
  el.timings.hidden = false;
  el.timings.textContent = Object.entries(timings).map(([k, v]) => `${k} ${v}ms`).join('  ·  ');
}

// While a turn is in flight, ask the backend what it is actually doing. The state on screen
// is driven by the tool that is running, never inferred from the question.
function startStatePolling() {
  stopStatePolling();
  statePoll = setInterval(async () => {
    if (!busy) return;
    try {
      const data = await (await fetch(`/state/${encodeURIComponent(sessionId)}`, { cache: 'no-store' })).json();
      if (busy && data.known && data.state && data.state !== 'READY' && data.state !== 'ERROR') setState(data.state);
    } catch { /* the turn response will carry the outcome */ }
  }, 400);
}
function stopStatePolling() { if (statePoll) { clearInterval(statePoll); statePoll = null; } }

async function submit(body, isAudio) {
  busy = true;
  el.talk.disabled = true;
  setState('TRANSCRIBING', isAudio ? 'Transcribing' : 'Thinking');
  startStatePolling();
  try {
    const options = isAudio
      ? { method: 'POST', body }
      : { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) };
    if (isAudio) setTimeout(() => { if (busy && el.stage.dataset.state === 'TRANSCRIBING') setState('THINKING'); }, 1200);
    const response = await fetch('/turn', options);
    const data = await response.json();

    sessionId = data.session_id || sessionId;
    store.set('crooks.session', sessionId);
    turns = typeof data.turns === 'number' ? data.turns : turns + 1;
    if (data.lost_thread) turns = 0;
    store.set('crooks.turns', String(turns));
    el.heard.textContent = data.question ? `“${data.question}”` : '';
    el.answer.textContent = data.answer;
    renderTimings(data.timings_ms);

    if (data.error_kind) { setState('ERROR'); speak(data.answer); }
    else { setState('READY'); speak(data.answer); }
  } catch (error) {
    setState('ERROR');
    el.answer.textContent = 'I lost contact with the backend. It may have restarted.';
    setConn('down', 'Backend unreachable');
  } finally {
    stopStatePolling();
    busy = false;
    el.talk.disabled = false;
    // If speech is off there is no onend to return us to READY, so do it here.
    if (!el.speakToggle.checked && el.stage.dataset.state !== 'ERROR') setState('READY');
  }
}

function sendAudio(blob) {
  const form = new FormData();
  form.append('audio', blob, 'turn.webm');
  form.append('session_id', sessionId);
  form.append('turns', String(turns));
  submit(form, true);
}

/* ------------------------------------------------------------------ events */

el.talk.addEventListener('pointerdown', (event) => {
  event.preventDefault();
  // Capture the pointer so pointerup reaches this button even if the thumb drifts off it —
  // otherwise a slightly sliding thumb means the recording never stops.
  try { el.talk.setPointerCapture(event.pointerId); } catch { /* unsupported */ }
  unlockSpeech();          // must be inside the gesture
  acquireWakeLock();
  startRecording();        // start before any other UI work, or the first word is clipped
});
for (const type of ['pointerup', 'pointercancel']) {
  el.talk.addEventListener(type, (event) => {
    event.preventDefault();
    try { el.talk.releasePointerCapture(event.pointerId); } catch { /* noop */ }
    stopRecording();
  });
}
el.talk.addEventListener('contextmenu', (event) => event.preventDefault());

el.settingsBtn.addEventListener('click', () => { unlockSpeech(); loadVoices(); pollHealth(); el.settings.showModal(); });
el.closeSettings.addEventListener('click', () => el.settings.close());
el.preview.addEventListener('click', () => {
  const previous = el.speakToggle.checked;
  el.speakToggle.checked = true;
  speak('Twelve orders today, four hundred and thirty pounds.');
  el.speakToggle.checked = previous;
});
el.timingToggle.addEventListener('change', () => { if (!el.timingToggle.checked) el.timings.hidden = true; });
el.resetSession.addEventListener('click', async () => {
  const form = new FormData();
  form.append('session_id', sessionId);
  try { await fetch('/reset', { method: 'POST', body: form }); } catch { /* noop */ }
  sessionId = Math.random().toString(36).slice(2, 14);
  store.set('crooks.session', sessionId);
  turns = 0;
  store.set('crooks.turns', '0');
  el.heard.textContent = '';
  el.answer.textContent = 'Started a new conversation.';
  el.settings.close();
});

// M2's diagnostic, kept: records three seconds and reports what the backend actually decoded.
el.micTest.addEventListener('click', async () => {
  el.settings.close();
  setState('LISTENING', 'Microphone test');
  el.answer.textContent = 'Recording three seconds…';
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    const parts = [];
    recorder.ondataavailable = (e) => { if (e.data.size) parts.push(e.data); };
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const form = new FormData();
      form.append('audio', new Blob(parts, { type: recorder.mimeType }), 'test.webm');
      const data = await (await fetch('/audio-test', { method: 'POST', body: form })).json();
      setState(data.ok && data.usable ? 'READY' : 'ERROR');
      el.answer.textContent = data.ok
        ? `${data.duration_s}s, ${data.sample_rate}Hz ${data.channels}ch, peak ${data.peak_dbfs}dBFS, RMS ${data.rms_dbfs}dBFS — ${data.usable ? 'usable' : 'too quiet or clipped'}. Recorded as ${data.mime_type}.`
        : `Decode failed: ${data.error}`;
    };
    recorder.start(250);
    setTimeout(() => recorder.stop(), 3000);
  } catch (error) {
    setState('ERROR');
    el.answer.textContent = `Microphone test failed: ${error}`;
  }
});

acquireWakeLock();
setState('READY');
