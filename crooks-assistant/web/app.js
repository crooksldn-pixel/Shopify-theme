/* CROOKS — the tablet client.
 *
 * Voice first: the owner holds the orb, speaks, releases. The backend transcribes, thinks,
 * looks things up and answers; the answer is spoken by the ElevenLabs voice generated on the
 * Mac and sent here as an MP3 by POST /speak, and shown beside cards the backend chose from
 * the tool results (the `ui` list — see app/presentation.py and ui.js). Android's own
 * speechSynthesis is still here, but only as the fallback for when ElevenLabs cannot answer.
 *
 * Four Android/Chrome behaviours dictate most of the awkward code here, and all four fail
 * silently rather than throwing:
 *   1. Media will not play until the user has touched the page. The hold region is that
 *      touch: the first pointerdown primes the <audio> element, speechSynthesis and the
 *      AudioContext that lets the orb see the voice.
 *   2. speechSynthesis needs a real user gesture too, so the same handler fires a zero-length
 *      utterance to unlock it.
 *   3. speechSynthesis truncates long utterances. We chunk to ~200 characters on sentence
 *      boundaries and chain on `onend`.
 *   4. getVoices() returns [] on the first call. We read it eagerly AND listen for
 *      `voiceschanged`.
 * speechSynthesis.pause() is never called: on Android it behaves as cancel(), so a "pause" is
 * unrecoverable. One <audio> element is reused for every answer — creating one per turn leaks
 * a decoder per question and eventually stops playing anything at all.
 *
 * The microphone is opened once and kept warm. Opening it on every press was the cause of the
 * first word of each question being clipped: getUserMedia takes a few hundred milliseconds to
 * hand over a live track, and the owner had already started speaking.
 */
'use strict';

const $ = (id) => document.getElementById(id);

const el = {
  body: document.body, stage: $('stage'), conn: $('conn'), connText: $('conn-text'),
  orb: $('orb'), orbFrame: $('orb-frame'), state: $('state-label'), sub: $('state-sub'),
  heard: $('heard'), answer: $('answer'), errline: $('errline'), timings: $('timings'),
  context: $('context'), stack: $('stack'), homeBtn: $('home-btn'), backBtn: $('back-btn'),
  deck: $('deck'), deckBack: $('deck-back'), cards: $('cards'),
  attention: $('attention'), attentionCount: $('attention-count'), attentionText: $('attention-text'),
  svc: { shopify: $('svc-shopify'), gmail: $('svc-gmail'), voice: $('svc-voice') },
  talk: $('talk'), talkLabel: $('talk-label'),
  settings: $('settings'), settingsBtn: $('settings-btn'), closeSettings: $('close-settings'),
  voiceStatus: $('voice-status'), voiceName: $('voice-name'),
  voiceSelect: $('voice-select'), voiceNote: $('voice-note'), preview: $('preview-voice'),
  micTest: $('mic-test'), speakToggle: $('speak-toggle'), timingToggle: $('timing-toggle'),
  health: $('health-detail'), resetSession: $('reset-session'),
  dev: $('dev'), devGrid: $('dev-grid'), devText: $('dev-text'),
};

const store = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : v; } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* private mode */ } },
};

// The developer gate. ?dev=1 turns fixtures on for this browser, ?dev=0 turns them off; the
// choice persists so the URL can be plain afterwards. Nothing else reads this flag.
const DEV = (() => {
  try {
    const params = new URLSearchParams(location.search);
    if (params.has('dev')) store.set('crooks.dev', params.get('dev') === '0' ? '0' : '1');
  } catch { /* no URL API */ }
  return store.get('crooks.dev', '0') === '1';
})();

const REDUCED = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false, addEventListener() {} };

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
let speakGeneration = 0;     // bumped on every stop; anything from an older generation gives up
let speakAbort = null;       // aborts an in-flight /speak so a new answer never queues behind it
let currentAudioUrl = null;  // the object URL the player is holding, revoked when it is done
let pendingStart = false;    // true between pointerdown and the recorder actually starting
let lastWasError = false;    // so an error stays on screen after it has been read out
let lastErrorTitle = '';
let speakingVia = null;      // 'player' while the ElevenLabs MP3 plays, 'browser' for the fallback

// One player, for the life of the page. 2ms of silence, used once inside the first touch to
// prove to Chrome that this element is allowed to make sound.
const player = new Audio();
player.preload = 'auto';
const SILENT_WAV = 'data:audio/wav;base64,UklGRjQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YRAAAACAgICAgICAgICAgICAgICA';

/* ------------------------------------------------------------- orb + audio */

// One AudioContext, created on the first touch. The orb reads two levels from it: the warm
// microphone while LISTENING, the ElevenLabs playback while SPEAKING. If either analyser is
// not available the orb falls back to a quiet synthetic pulse — never to silence on screen,
// and never at the cost of the audio itself.
const audio = window.CrooksAudio ? window.CrooksAudio.create() : null;

function syntheticLevel() {
  const t = performance.now();
  return 0.18 + 0.16 * Math.abs(Math.sin(t / 140)) * Math.abs(Math.sin(t / 310));
}

function orbLevel(state) {
  if (state === 'LISTENING') return audio && audio.hasMic ? audio.micLevel() : 0.12;
  if (state === 'SPEAKING') {
    if (speakingVia === 'player' && audio && audio.hasPlayer) return audio.playerLevel();
    return syntheticLevel();
  }
  return 0;
}

const orb = window.CrooksOrb
  ? window.CrooksOrb.create(el.orb, { size: 340, reducedMotion: REDUCED.matches, getLevel: orbLevel })
  : null;
REDUCED.addEventListener('change', (event) => { if (orb) orb.setReducedMotion(event.matches); });

/* ------------------------------------------------------------------ state */

const LABELS = {
  READY: ['System ready.', 'What do you need?'],
  LISTENING: ['Listening', 'Release to send'],
  TRANSCRIBING: ['Transcribing', ''],
  THINKING: ['Thinking', ''],
  'CHECKING SHOPIFY': ['Checking Shopify', ''],
  'CHECKING EMAIL': ['Checking email', ''],
  SPEAKING: ['Speaking', 'Hold to interrupt'],
  SUCCESS: ['Done', ''],
  ERROR: ['Something went wrong', 'Hold to try again'],
};

function setState(state, label) {
  el.stage.dataset.state = state;
  const [title, sub] = LABELS[state] || [state, ''];
  el.state.textContent = label || title;
  el.sub.textContent = sub;
  if (orb) orb.setState(state);
}

function setConn(state, text) {
  el.conn.dataset.state = state;
  el.connText.textContent = text;
}

function setMode(mode) {
  if (el.body.dataset.mode === mode) return;
  el.body.dataset.mode = mode;
  el.talk.setAttribute('aria-label', mode === 'orb' ? 'Hold to speak' : 'Hold to speak (dock)');
}

const HAPTIC = { start: 12, done: [10, 60, 10], error: [40, 50, 40] };
function haptic(pattern) {
  try { if (navigator.vibrate) navigator.vibrate(pattern); } catch { /* unsupported */ }
}

/* -------------------------------------------------------------- wake lock */

async function acquireWakeLock() {
  if (!('wakeLock' in navigator)) return;
  try {
    wakeLock = await navigator.wakeLock.request('screen');
    wakeLock.addEventListener('release', () => { wakeLock = null; });
  } catch { /* denied or unsupported; the screen will just sleep */ }
}

// Android drops the lock whenever the page is hidden, so re-acquire on every return. Hidden
// also means: stop talking, stop drawing, and let go of the microphone unless mid-sentence.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    acquireWakeLock();
    if (orb) orb.start();
    warmMic();
    pollHealth();
  } else {
    stopSpeaking();
    if (orb) orb.stop();
    if (!recording) releaseMicStream();
  }
});
window.addEventListener('pagehide', () => { stopSpeaking(); releaseMicStream(); });

/* ------------------------------------------------------------------ voices */

function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

function loadVoices() {
  const list = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  if (!list.length) return;                       // first call is empty in Chrome — wait for the event
  voices = list;
  const saved = store.get('crooks.voice', '');
  clear(el.voiceSelect);
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
    ? 'A British offline fallback voice is installed.'
    : 'No offline British fallback voice found. Settings → General management → Text-to-speech → Install voice data.';
}
if (window.speechSynthesis) {
  loadVoices();
  window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
}
el.voiceSelect.addEventListener('change', () => store.set('crooks.voice', el.voiceSelect.value));

/* ------------------------------------------------------------------ speech */

function unlockSpeech() {
  // Must happen inside a user gesture, for both engines and for the AudioContext. Chrome M71
  // removed speech without user activation and blocks audio the same way; the failure mode
  // for each is total silence with no error anywhere, so all three are primed on the first
  // touch and never again.
  if (speechUnlocked) return;
  speechUnlocked = true;
  if (audio) audio.ensure();
  try {
    player.src = SILENT_WAV;
    player.volume = 1.0;
    const primed = player.play();
    if (primed && primed.then) {
      primed.then(() => {
        player.pause();
        player.removeAttribute('src');
        // The context is running by now if it ever will be; bind the player to it once.
        if (audio) audio.attachPlayer(player);
      }).catch(() => {});
    }
  } catch { /* the play() below will show whether it mattered */ }
  if (!window.speechSynthesis) return;
  try {
    const primer = new SpeechSynthesisUtterance('');
    primer.volume = 0;
    window.speechSynthesis.speak(primer);
  } catch { /* nothing more we can do */ }
}

function releaseAudioUrl() {
  if (!currentAudioUrl) return;
  URL.revokeObjectURL(currentAudioUrl);
  currentAudioUrl = null;
}

// Silence, immediately and completely, whichever engine is talking. Called before every
// recording and before every new answer, so the assistant can never talk over itself or be
// recorded talking to itself.
function stopSpeaking() {
  speakGeneration += 1;   // anything still running belongs to an old generation now
  if (speakAbort) { try { speakAbort.abort(); } catch { /* noop */ } speakAbort = null; }
  try {
    player.pause();
    player.onended = null;
    player.onerror = null;
    player.removeAttribute('src');
    player.load();        // drops the decoder; without this Chrome keeps the last buffer alive
  } catch { /* nothing was playing */ }
  releaseAudioUrl();
  if (window.speechSynthesis) { try { window.speechSynthesis.cancel(); } catch { /* noop */ } }
  speakingVia = null;
}

// Where the screen lands once nothing is speaking any more.
function settle(isError) {
  speakingVia = null;
  if (!busy && !recording) setState(isError ? 'ERROR' : 'READY', isError ? lastErrorTitle : '');
}

function chunkForSpeech(text, limit = 200) {
  // A full stop between digits is a decimal point ("£430.50"), not a sentence end.
  const sentences = text.match(/(?:[^.!?]|\.(?=\d))+[.!?]*\s*/g) || [text];
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

// The fallback voice: Android's own, used only when ElevenLabs could not speak this answer.
// `reason` is logged rather than shown — the owner wants the answer, not an apology.
function browserSpeak(text, { isError = false, reason = '' } = {}) {
  if (!window.speechSynthesis || !el.speakToggle.checked || !text) { settle(isError); return; }
  console.warn(`[crooks] ElevenLabs voice unavailable (${reason || 'unknown'}) — using the Android voice`);
  const generation = speakGeneration;
  const parts = chunkForSpeech(text);
  const chosen = voices.find((v) => v.name === el.voiceSelect.value);
  let index = 0;
  const finish = () => { if (generation === speakGeneration) settle(isError); };
  const next = () => {
    if (generation !== speakGeneration) return;      // cancelled: do not re-arm the chain
    if (index >= parts.length) { finish(); return; }
    const utterance = new SpeechSynthesisUtterance(parts[index++]);
    if (chosen) { utterance.voice = chosen; utterance.lang = chosen.lang; }
    else utterance.lang = 'en-GB';
    utterance.rate = 1.0;
    utterance.onend = next;
    utterance.onerror = next;   // a failed chunk moves on; a cancelled chain stops above
    window.speechSynthesis.speak(utterance);
  };
  speakingVia = 'browser';
  setState('SPEAKING');
  next();
}

// The normal voice. The answer text is already on screen; this asks the Mac to say it.
//
// The MP3 arrives as one response and is played once it is complete. ElevenLabs streams it and
// the backend forwards it as it arrives, so the wait is the generation, not a second copy of
// the file — and for a two-sentence answer in eleven_flash_v2_5 that is a few hundred
// milliseconds. Every way this can fail ends in browserSpeak, never in silence.
async function speakAnswer(text, { isError = false } = {}) {
  if (!text) { settle(isError); return; }
  if (!el.speakToggle.checked) { settle(isError); return; }
  stopSpeaking();
  const generation = speakGeneration;
  setState('SPEAKING');
  const controller = new AbortController();
  speakAbort = controller;
  let response;
  try {
    response = await fetch('/speak', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text, session_id: sessionId }),
      signal: controller.signal,
      cache: 'no-store',
    });
    if (generation !== speakGeneration) return;    // interrupted while it was generating
    if (response.status === 204) { settle(isError); return; }   // nothing worth saying
    if (!response.ok) {
      let kind = `http ${response.status}`;
      try { kind = (await response.json()).kind || kind; } catch { /* not JSON */ }
      browserSpeak(text, { isError, reason: kind });
      return;
    }
    const blob = await response.blob();
    if (generation !== speakGeneration) return;
    if (!blob.size) { browserSpeak(text, { isError, reason: 'empty audio' }); return; }
    playAudio(blob, text, generation, isError);
  } catch (error) {
    // An abort is the owner interrupting, not a failure: they are already holding the orb.
    if (controller.signal.aborted || generation !== speakGeneration) return;
    browserSpeak(text, { isError, reason: 'backend unreachable' });
  } finally {
    if (speakAbort === controller) speakAbort = null;
  }
}

function playAudio(blob, text, generation, isError) {
  const url = URL.createObjectURL(blob);
  releaseAudioUrl();
  currentAudioUrl = url;
  const done = () => {
    if (generation !== speakGeneration) return;   // a newer answer owns the player now
    releaseAudioUrl();
    settle(isError);
  };
  player.onended = done;
  player.onerror = () => {
    if (generation !== speakGeneration) return;
    releaseAudioUrl();
    browserSpeak(text, { isError, reason: 'the tablet could not play the audio' });
  };
  // The analyser path: resume the context if Android suspended it, and bind the player to it
  // if the first touch did not manage to (the context was still starting). Binding is a
  // one-off; attachPlayer is a no-op once done. Playback is never delayed for it.
  if (audio) { audio.resume(); audio.attachPlayer(player); }
  speakingVia = 'player';
  player.src = url;
  player.volume = 1.0;
  const started = player.play();
  if (started && started.catch) {
    started.then(() => {
      // A player bound to a context that is not running plays silence. That is the one
      // failure this path can cause, so it is the one it checks for and hands to the fallback.
      if (!audio || !audio.hasPlayer || audio.state === 'running') return;
      setTimeout(() => {
        if (generation !== speakGeneration || audio.state === 'running') return;
        try { player.pause(); } catch { /* noop */ }
        releaseAudioUrl();
        browserSpeak(text, { isError, reason: 'audio context suspended' });
      }, 400);
    }).catch(() => {
      // Chrome refused to play without a gesture. The hold is one, so this should not happen
      // after the first question — but the answer still gets spoken.
      if (generation !== speakGeneration) return;
      releaseAudioUrl();
      browserSpeak(text, { isError, reason: 'autoplay blocked' });
    });
  }
}

/* ------------------------------------------------------------------ health */

function setService(name, ok) {
  const node = el.svc[name];
  if (!node) return;
  node.dataset.ok = ok === true ? 'true' : ok === false ? 'false' : 'unknown';
}

async function pollHealth() {
  if (document.hidden) return;
  try {
    const response = await fetch('/health', { cache: 'no-store' });
    const data = await response.json();
    const checks = data.checks || {};
    const failed = Object.entries(checks).filter(([, c]) => !c.ok).map(([k]) => k);
    if (!failed.length) setConn('ok', 'Online');
    else setConn('degraded', 'Degraded');
    setService('shopify', checks.shopify ? checks.shopify.ok : null);
    setService('gmail', checks.gmail ? checks.gmail.ok : null);
    const canHear = !checks.speech || checks.speech.ok;
    const canSpeak = !checks.tts || checks.tts.ok;
    setService('voice', canHear && canSpeak);
    el.health.textContent = Object.entries(checks)
      .map(([k, c]) => `${c.ok ? 'ok  ' : 'FAIL'} ${k.padEnd(15)} ${c.detail}`)
      .join('\n');
    const voice = data.voice || {};
    if (voice.voice) {
      el.voiceName.textContent = voice.enabled
        ? `${voice.voice} · ElevenLabs ${voice.model || ''}`.trim() + ' · generated on the Mac'
        : 'ElevenLabs voice switched off · the fallback voice below is in use';
      el.preview.textContent = voice.enabled ? `Preview ${voice.voice}` : 'Preview fallback voice';
    }
    el.voiceStatus.textContent = voice.ok === false ? 'Unavailable' : voice.enabled === false ? 'Off' : 'Ready';
    el.voiceStatus.className = `badge quiet ${voice.ok === false ? 'bad' : voice.enabled === false ? 'warn' : 'ok'}`;
  } catch {
    setConn('down', 'Offline');
    setService('shopify', null); setService('gmail', null); setService('voice', null);
    el.health.textContent = 'Cannot reach the backend.';
    el.voiceStatus.textContent = 'Unknown';
    el.voiceStatus.className = 'badge quiet';
  }
}
pollHealth();
setInterval(pollHealth, 15000);

/* ------------------------------------------------------------- microphone */

const MIC_CONSTRAINTS = {
  audio: {
    echoCancellation: true, noiseSuppression: true, autoGainControl: true,
    channelCount: 1,
    sampleRate: { ideal: 16000 },   // ideal, never exact — exact fails outright on some devices
  },
};
let micStream = null;     // the one warm stream; the recorder and the analyser both use it
let micOpening = null;    // the in-flight getUserMedia, shared so two presses open one stream

function micIsLive() {
  return Boolean(micStream) && micStream.getAudioTracks().some((track) => track.readyState === 'live');
}

async function ensureMicStream() {
  if (micIsLive()) return micStream;
  if (micOpening) return micOpening;
  micOpening = (async () => {
    const stream = await navigator.mediaDevices.getUserMedia(MIC_CONSTRAINTS);
    for (const track of stream.getAudioTracks()) {
      // Android ends the track when another app takes the microphone. Forget the stream so
      // the next press opens a fresh one rather than recording silence.
      track.addEventListener('ended', () => {
        if (micStream === stream) { micStream = null; if (audio) audio.detachMic(); }
      });
    }
    micStream = stream;
    if (audio) audio.attachMic(stream);   // analysis only; MediaRecorder reads the same tracks
    return stream;
  })();
  try { return await micOpening; } finally { micOpening = null; }
}

function releaseMicStream() {
  if (!micStream) return;
  if (audio) audio.detachMic();
  for (const track of micStream.getTracks()) track.stop();
  micStream = null;
}

function warmMic() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
  ensureMicStream().catch(() => { /* the press will report the real error */ });
}

// Warm on load when permission is already granted (no prompt), otherwise on the first touch.
if (navigator.permissions && navigator.permissions.query) {
  navigator.permissions.query({ name: 'microphone' })
    .then((status) => { if (status.state === 'granted') warmMic(); })
    .catch(() => {});
}
document.addEventListener('pointerdown', warmMic, { once: true, capture: true });

function pickMimeType() {
  const candidates = [
    'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4',
  ];
  for (const type of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) return type;
  }
  return '';
}

function showMicError(message) {
  lastWasError = true;
  lastErrorTitle = 'Microphone unavailable';
  el.errline.textContent = message;
  setState('ERROR', lastErrorTitle);
  haptic(HAPTIC.error);
}

async function startRecording() {
  if (recording || busy || pendingStart) return;
  pendingStart = true;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    pendingStart = false;
    showMicError(window.isSecureContext
      ? 'This browser has no microphone support.'
      : 'The microphone needs a secure HTTPS connection. Open the tailscale ts.net address, not the LAN address.');
    return;
  }
  stopSpeaking();
  try {
    // Warm path: no await, so the recorder starts inside the same task as the touch.
    const stream = micIsLive() ? micStream : await ensureMicStream();
    if (!pendingStart) return;   // the thumb lifted while permission was being granted
    const mimeType = pickMimeType();
    mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType, audioBitsPerSecond: 32000 } : {});
    chunks = [];
    mediaRecorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
    mediaRecorder.onstop = () => {
      // The stream stays open: the next press starts recording on the first sample.
      const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      if (blob.size > 800) sendAudio(blob);
      else { setState('READY'); el.sub.textContent = 'That was too short — hold while you speak.'; }
    };
    mediaRecorder.start(250);
    recording = true;
    el.talk.dataset.recording = 'true';
    el.talkLabel.textContent = 'Release to send';
    setState('LISTENING');
    if (orb) orb.pulse();
    haptic(HAPTIC.start);
  } catch (error) {
    showMicError(error && error.name === 'NotAllowedError'
      ? 'Microphone permission was refused. Allow it in the browser settings, choosing "While using the app".'
      : 'Could not open the microphone. Check nothing else is using it.');
    console.warn('[crooks] microphone', error);
  } finally {
    pendingStart = false;
  }
}

function stopRecording() {
  pendingStart = false;      // a release before the recorder started cancels the start
  if (!recording) return;
  recording = false;
  el.talk.dataset.recording = 'false';
  el.talkLabel.textContent = 'Hold to speak';
  try { mediaRecorder.stop(); } catch { /* already stopped */ }
}

/* ------------------------------------------------------------ context deck */

// What is on the surface, most recent last. Each entry is one turn's cards (or a fixture),
// kept as DOM so going back is a move, not a re-render. Bounded, because it is DOM.
const history = [];
const MAX_HISTORY = 6;
let historyIndex = -1;
let currentStack = [];
let attentionItems = [];

function entitiesOf(items) {
  const out = [];
  for (const item of items || []) {
    const d = item && item.data ? item.data : {};
    if (item.type === 'order' && d.order_id) out.push(String(d.order_id));
    if (item.type === 'customer' && d.customer_id) out.push(String(d.customer_id));
    if (item.type === 'email_thread' && d.thread_id) out.push(String(d.thread_id));
    if ((item.type === 'inventory' || item.type === 'product') && d.products && d.products[0] && d.products[0].product_id) {
      out.push(String(d.products[0].product_id));
    }
  }
  return out;
}

function pushContext(nodes, items, question) {
  history.push({ nodes, entities: entitiesOf(items), question: question || '' });
  while (history.length > MAX_HISTORY) history.shift();
  showHistory(history.length - 1);
}

function showHistory(index) {
  if (index < 0 || index >= history.length) return;
  historyIndex = index;
  clear(el.cards);
  for (const node of history[index].nodes) el.cards.appendChild(node);
  el.cards.scrollTop = 0;
  el.deck.dataset.depth = String(Math.min(2, index));
  el.backBtn.hidden = index === 0;
  renderStackChips();
  setMode('context');
}

function goBack() {
  if (historyIndex > 0) showHistory(historyIndex - 1);
  else goHome();
}

function goHome() {
  setMode('orb');
}

function renderStackChips() {
  clear(el.stack);
  if (!window.CrooksUI || !currentStack.length) return;
  const active = history[historyIndex] ? history[historyIndex].entities : [];
  const chips = window.CrooksUI.renderStack(currentStack, {
    active: active.find((ref) => currentStack.some((e) => e.ref === ref)) || '',
    onSelect: (entry) => {
      // Bring the most recent cards for that entity forward, if we still hold them.
      for (let i = history.length - 1; i >= 0; i--) {
        if (history[i].entities.indexOf(entry.ref) !== -1) { showHistory(i); haptic(HAPTIC.start); return; }
      }
    },
  });
  for (const chip of chips) el.stack.appendChild(chip);
}

function renderAttentionSurface() {
  if (!attentionItems.length) { el.attention.hidden = true; return; }
  el.attention.hidden = false;
  el.attentionCount.textContent = String(attentionItems.length);
  el.attentionText.textContent = attentionItems.length === 1 ? 'Requires attention' : 'Require attention';
}

// The answer to a turn: cards first, then the mode they need.
function renderTurn(data) {
  const ui = window.CrooksUI ? window.CrooksUI.render(data.ui, {}) : { nodes: [], skipped: [], stack: null, errors: [], hasContext: false };
  if (ui.skipped.length) console.warn('[crooks] skipped ui items:', ui.skipped.join(', '));
  el.errline.textContent = '';
  lastErrorTitle = '';
  if (ui.errors.length) {
    lastErrorTitle = ui.errors[0].title || 'Something went wrong';
    el.errline.textContent = ui.errors[0].recovery || '';
  }
  if (ui.stack) currentStack = ui.stack;
  const attention = (data.ui || []).filter((i) => i && i.type === 'attention' && i.data && Array.isArray(i.data.items));
  attentionItems = attention.length ? attention[0].data.items : attentionItems;
  renderAttentionSurface();

  const answer = data.answer || '';
  if (ui.hasContext) {
    pushContext(ui.nodes, data.ui, data.question);
  } else if (answer.length > 260 && window.CrooksUI) {
    // Too long to read beneath the orb: give it a card and the room that comes with one.
    const node = window.CrooksUI.renderItem({ type: 'assistant', data: { text: answer } });
    if (node) pushContext([node].concat(ui.nodes), [], data.question);
    else setMode('orb');
  } else {
    setMode('orb');
  }
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
  el.talk.dataset.busy = 'true';
  el.errline.textContent = '';
  setState('TRANSCRIBING', isAudio ? 'Transcribing' : 'Thinking');
  startStatePolling();
  try {
    const options = isAudio
      ? { method: 'POST', body }
      : { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) };
    if (isAudio) setTimeout(() => { if (busy && el.stage.dataset.state === 'TRANSCRIBING') setState('THINKING'); }, 1200);
    const response = await fetch('/turn', options);
    if (!response.ok) {
      lastWasError = true;
      lastErrorTitle = 'Backend error';
      el.errline.textContent = `The backend answered with an error (${response.status}). Try again.`;
      setState('ERROR', lastErrorTitle);
      haptic(HAPTIC.error);
      return;
    }
    const data = await response.json();

    sessionId = data.session_id || sessionId;
    store.set('crooks.session', sessionId);
    turns = typeof data.turns === 'number' ? data.turns : turns + 1;
    if (data.lost_thread) turns = 0;
    store.set('crooks.turns', String(turns));
    el.heard.textContent = data.question ? `“${data.question}”` : '';
    el.answer.textContent = data.answer;
    renderTimings(data.timings_ms);

    lastWasError = Boolean(data.error_kind);
    renderTurn(data);
    // The text is on screen before the voice is asked for; the answer never waits on audio.
    setState(lastWasError ? 'ERROR' : 'READY', lastWasError ? lastErrorTitle : '');
    haptic(lastWasError ? HAPTIC.error : HAPTIC.done);
    speakAnswer(data.answer, { isError: lastWasError });   // deliberately not awaited
  } catch (error) {
    lastWasError = true;
    lastErrorTitle = 'Connection lost';
    el.errline.textContent = 'I lost contact with the backend. It may have restarted.';
    setState('ERROR', lastErrorTitle);
    setConn('down', 'Offline');
    haptic(HAPTIC.error);
  } finally {
    stopStatePolling();
    busy = false;
    el.talk.dataset.busy = 'false';
    // If speech is off there is no onend to settle the state, so do it here.
    if (!el.speakToggle.checked) setState(lastWasError ? 'ERROR' : 'READY', lastWasError ? lastErrorTitle : '');
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

// The hold. Attached to the talk region (the whole stage in orb mode, the dock in context
// mode) and to the orb itself, so the small orb still answers to a thumb when cards are up.
function onHoldStart(event) {
  if (event.button !== undefined && event.button !== 0) return;
  event.preventDefault();
  // Capture the pointer so pointerup reaches this element even if the thumb drifts off it —
  // otherwise a slightly sliding thumb means the recording never stops.
  try { event.currentTarget.setPointerCapture(event.pointerId); } catch { /* unsupported */ }
  unlockSpeech();          // must be inside the gesture
  stopSpeaking();          // before anything else: the voice must not be recorded answering itself
  acquireWakeLock();
  if (busy) return;        // a turn is in flight; the label says so
  setState('LISTENING');   // the orb wakes on the touch itself, not on the recorder
  startRecording();        // start before any other UI work, or the first word is clipped
}
function onHoldEnd(event) {
  event.preventDefault();
  try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* noop */ }
  stopRecording();
}
for (const target of [el.talk, el.orbFrame]) {
  target.addEventListener('pointerdown', onHoldStart);
  target.addEventListener('pointerup', onHoldEnd);
  target.addEventListener('pointercancel', onHoldEnd);
  target.addEventListener('contextmenu', (event) => event.preventDefault());
}
// Keyboard: hold Space or Enter on the talk control.
el.talk.addEventListener('keydown', (event) => {
  if ((event.key === ' ' || event.key === 'Enter') && !event.repeat) {
    event.preventDefault(); unlockSpeech(); stopSpeaking(); if (!busy) { setState('LISTENING'); startRecording(); }
  }
});
el.talk.addEventListener('keyup', (event) => {
  if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); stopRecording(); }
});

el.homeBtn.addEventListener('click', goHome);
el.backBtn.addEventListener('click', goBack);
el.deckBack.addEventListener('click', goBack);
el.attention.addEventListener('click', () => {
  if (!window.CrooksUI || !attentionItems.length) return;
  const node = window.CrooksUI.renderItem({ type: 'attention', data: { items: attentionItems } });
  if (node) pushContext([node], [], '');
});

el.settingsBtn.addEventListener('click', () => { unlockSpeech(); loadVoices(); pollHealth(); el.settings.showModal(); });
el.closeSettings.addEventListener('click', () => el.settings.close());
el.settings.addEventListener('click', (event) => { if (event.target === el.settings) el.settings.close(); });
el.preview.addEventListener('click', () => {
  // Previews the real voice, through the real path — which is also the quickest way to tell
  // whether ElevenLabs is answering from the tablet itself.
  unlockSpeech();
  const previous = el.speakToggle.checked;
  el.speakToggle.checked = true;
  speakAnswer('Twelve orders today, four hundred and thirty pounds.');
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
  history.length = 0;
  historyIndex = -1;
  currentStack = [];
  clear(el.cards);
  renderStackChips();
  el.heard.textContent = '';
  el.answer.textContent = '';
  el.errline.textContent = '';
  lastWasError = false;
  el.settings.close();
  setMode('orb');
  setState('SUCCESS', 'New conversation');
  haptic(HAPTIC.done);
  setTimeout(() => { if (!busy && !recording && el.stage.dataset.state === 'SUCCESS') setState('READY'); }, 1400);
});

// M2's diagnostic, kept: records three seconds through the warm stream and reports what the
// backend actually decoded, then plays it back.
el.micTest.addEventListener('click', async () => {
  el.settings.close();
  setMode('orb');
  setState('LISTENING', 'Microphone test');
  el.sub.textContent = 'Recording three seconds…';
  try {
    const stream = await ensureMicStream();
    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    const parts = [];
    recorder.ondataavailable = (e) => { if (e.data.size) parts.push(e.data); };
    recorder.onstop = async () => {
      try {
        const form = new FormData();
        form.append('audio', new Blob(parts, { type: recorder.mimeType }), 'test.webm');
        const response = await fetch('/audio-test', { method: 'POST', body: form });
        if (!response.ok) throw new Error(`backend answered ${response.status}`);
        const data = await response.json();
        setState(data.ok && data.usable ? 'READY' : 'ERROR', data.ok && data.usable ? 'Microphone OK' : 'Microphone problem');
        el.answer.textContent = data.ok
          ? `${data.duration_s}s, ${data.sample_rate}Hz ${data.channels}ch, peak ${data.peak_dbfs}dBFS, RMS ${data.rms_dbfs}dBFS, clipped ${(data.clipped_ratio * 100).toFixed(2)}% (${data.clipped_ms}ms) — ${data.usable ? 'usable' : 'too quiet or clipped'}. Recorded as ${data.mime_type}. Playing back what the backend heard.`
          : `Decode failed: ${data.error}`;
        if (data.ok && data.wav_base64) {
          // Play back exactly what the backend decoded — the M2 "is it intelligible" check.
          const bytes = Uint8Array.from(atob(data.wav_base64), (c) => c.charCodeAt(0));
          const url = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
          const playback = new Audio(url);
          playback.onended = () => URL.revokeObjectURL(url);
          playback.onerror = () => URL.revokeObjectURL(url);
          playback.play().catch(() => { /* autoplay blocked: the stats still tell the story */ });
        }
      } catch (error) {
        setState('ERROR', 'Microphone test failed');
        el.errline.textContent = String(error && error.message ? error.message : error);
      }
    };
    recorder.start(250);
    setTimeout(() => recorder.stop(), 3000);
  } catch (error) {
    showMicError('Microphone test failed: the microphone could not be opened.');
  }
});

/* ------------------------------------------------------------- developer */

if (DEV) {
  el.dev.hidden = false;
  const banner = document.createElement('div');
  banner.className = 'dev-banner';
  banner.textContent = 'Developer mode · fixtures are not live data';
  document.body.appendChild(banner);
  const script = document.createElement('script');
  script.src = '/static/fixtures.js';
  script.onload = () => {
    const fixtures = window.CrooksFixtures ? window.CrooksFixtures.list : [];
    for (const fixture of fixtures) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn';
      button.textContent = fixture.label;
      button.addEventListener('click', () => {
        el.settings.close();
        const ui = window.CrooksUI.render(fixture.items, { fixture: true });
        if (ui.stack) { currentStack = ui.stack; }
        el.heard.textContent = `Fixture: ${fixture.label}`;
        el.answer.textContent = '';
        if (fixture.id === 'success') setState('SUCCESS');
        else if (fixture.id === 'error') setState('ERROR', ui.errors[0] ? ui.errors[0].title : '');
        else setState('READY');
        pushContext(ui.nodes, fixture.items, `fixture:${fixture.id}`);
      });
      el.devGrid.appendChild(button);
    }
  };
  document.body.appendChild(script);
  el.devText.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' || busy) return;
    event.preventDefault();   // closing the sheet moves focus to a button; Enter must not press it
    const text = el.devText.value.trim();
    if (!text) return;
    el.devText.value = '';
    el.settings.close();
    unlockSpeech();
    stopSpeaking();
    submit({ text, session_id: sessionId, turns }, false);
  });
}

acquireWakeLock();
setMode('orb');
setState('READY');
