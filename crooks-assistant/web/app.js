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
  system: $('system'), systemTitle: $('system-title'), systemSub: $('system-sub'), systemNote: $('system-note'),
  orb: $('orb'), orbFrame: $('orb-frame'), state: $('state-label'), sub: $('state-sub'),
  heard: $('heard'), answer: $('answer'), errline: $('errline'), timings: $('timings'),
  context: $('context'), stack: $('stack'), homeBtn: $('home-btn'), backBtn: $('back-btn'),
  deck: $('deck'), deckBack: $('deck-back'), cards: $('cards'),
  attention: $('attention'), attentionCount: $('attention-count'), attentionText: $('attention-text'),
  recent: $('recent'), recentLabel: $('recent-label'),
  svc: { shopify: $('svc-shopify'), gmail: $('svc-gmail'), voice: $('svc-voice') },
  talk: $('talk'), talkLabel: $('talk-label'),
  settings: $('settings'), settingsBtn: $('settings-btn'), closeSettings: $('close-settings'),
  voiceStatus: $('voice-status'), voiceName: $('voice-name'),
  voiceSelect: $('voice-select'), voiceNote: $('voice-note'), preview: $('preview-voice'),
  micTest: $('mic-test'), speakToggle: $('speak-toggle'), streamToggle: $('stream-toggle'), timingToggle: $('timing-toggle'),
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
  // The Mac gives up on ElevenLabs after ten seconds; a voice whose headers have not arrived
  // by then is not coming, and Android's should start. The body may stream for longer.
  const headersTimer = setTimeout(() => { controller.timedOut = true; controller.abort(); }, SPEAK_HEADERS_TIMEOUT_MS);
  let response;
  try {
    response = await fetch('/speak', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text, session_id: sessionId }),
      signal: controller.signal,
      cache: 'no-store',
    });
    clearTimeout(headersTimer);
    if (generation !== speakGeneration) return;    // interrupted while it was generating
    if (response.status === 204) { settle(isError); return; }   // nothing worth saying
    if (!response.ok) {
      let kind = `http ${response.status}`;
      try { kind = (await response.json()).kind || kind; } catch { /* not JSON */ }
      browserSpeak(text, { isError, reason: kind });
      return;
    }
    if (el.streamToggle.checked && canStream() && response.body) {
      // Play as the bytes arrive: the first sentence starts while the last is still being
      // generated. Every failure inside falls back to the whole-file path, then to Android.
      await playStream(response, text, generation, isError);
      return;
    }
    const blob = await response.blob();
    if (generation !== speakGeneration) return;
    if (!blob.size) { browserSpeak(text, { isError, reason: 'empty audio' }); return; }
    playAudio(blob, text, generation, isError);
  } catch (error) {
    clearTimeout(headersTimer);
    if (generation !== speakGeneration) return;
    // An abort is the owner interrupting, not a failure: they are already holding the orb —
    // unless it was the timer, in which case the Mac's voice is not coming.
    if (controller.signal.aborted && !controller.timedOut) return;
    browserSpeak(text, { isError, reason: controller.timedOut ? 'voice timed out' : 'the Mac unreachable' });
  } finally {
    if (speakAbort === controller) speakAbort = null;
  }
}

// Media Source Extensions: the MP3 is appended to the player as it streams from the Mac.
// Chrome on Android supports the mp3 byte stream; if this tablet ever does not, or anything
// goes wrong mid-stream, the bytes already received are played whole instead.
function canStream() {
  try {
    return Boolean(window.MediaSource) && typeof MediaSource.isTypeSupported === 'function'
      && MediaSource.isTypeSupported('audio/mpeg');
  } catch { return false; }
}

async function playStream(response, text, generation, isError) {
  const source = new MediaSource();
  const url = URL.createObjectURL(source);
  releaseAudioUrl();
  currentAudioUrl = url;
  const received = [];        // every chunk, so a fallback needs no second request
  const queue = [];
  let buffer = null;
  let ended = false;
  let failed = false;
  let total = 0;

  const fallback = (reason) => {
    if (failed) return;
    failed = true;
    console.warn(`[crooks] streaming playback stopped (${reason}); playing whole`);
  };
  const pump = () => {
    if (failed || !buffer || buffer.updating) return;
    if (queue.length) {
      try { buffer.appendBuffer(queue.shift()); } catch (error) { fallback('append failed'); }
      return;
    }
    if (ended && source.readyState === 'open') {
      try { source.endOfStream(); } catch { /* already ended */ }
    }
  };
  source.addEventListener('sourceopen', () => {
    if (generation !== speakGeneration) return;
    try {
      buffer = source.addSourceBuffer('audio/mpeg');
      buffer.addEventListener('updateend', pump);
      buffer.addEventListener('error', () => fallback('buffer error'));
      pump();
    } catch (error) {
      fallback('no source buffer');
    }
  });

  const done = () => {
    if (generation !== speakGeneration) return;
    releaseAudioUrl();
    settle(isError);
  };
  player.onended = done;
  player.onerror = () => {
    if (generation !== speakGeneration) return;
    fallback('player error');
  };
  if (audio) { audio.resume(); audio.attachPlayer(player); }
  speakingVia = 'player';
  player.src = url;
  player.volume = 1.0;
  const started = player.play();
  if (started && started.catch) {
    started.then(() => guardSilentContext(generation, () => fallback('audio context suspended')))
      .catch(() => fallback('autoplay blocked'));
  }

  const reader = response.body.getReader();
  try {
    for (;;) {
      const { done: finished, value } = await reader.read();
      if (generation !== speakGeneration) { try { reader.cancel(); } catch { /* noop */ } return; }
      if (finished) break;
      if (value && value.length) { received.push(value); queue.push(value); total += value.length; pump(); }
    }
  } catch (error) {
    fallback('stream broke');
  }
  ended = true;
  pump();
  if (generation !== speakGeneration) return;
  if (!total) { releaseAudioUrl(); browserSpeak(text, { isError, reason: 'empty audio' }); return; }
  if (failed) {
    // Whatever stopped the stream, the answer is in hand: play it the plain way, from where
    // the stream got to rather than from the start — the owner should not hear it twice.
    let reached = 0;
    try { reached = player.currentTime || 0; player.pause(); } catch { /* noop */ }
    playAudio(new Blob(received, { type: 'audio/mpeg' }), text, generation, isError, reached);
  }
}

// A player bound to an AudioContext that is not running plays silence. That is the one
// failure the analyser path can cause, so it is the one both playback paths check for.
function guardSilentContext(generation, onSilent) {
  if (!audio || !audio.hasPlayer || audio.state === 'running') return;
  setTimeout(() => {
    if (generation !== speakGeneration || audio.state === 'running') return;
    onSilent();
  }, 400);
}

function playAudio(blob, text, generation, isError, startAt = 0) {
  const url = URL.createObjectURL(blob);
  releaseAudioUrl();
  currentAudioUrl = url;
  if (startAt > 0.5) {
    player.addEventListener('loadedmetadata', () => {
      if (generation === speakGeneration) { try { player.currentTime = startAt; } catch { /* not seekable */ } }
    }, { once: true });
  }
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
      guardSilentContext(generation, () => {
        try { player.pause(); } catch { /* noop */ }
        releaseAudioUrl();
        browserSpeak(text, { isError, reason: 'audio context suspended' });
      });
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

// The badge names the thing that is down, in the owner's words, worst first.
function faultLabel(checks) {
  const down = (k) => checks[k] && checks[k].ok === false;
  if (down('claude')) return 'Claude offline';
  if (down('speech')) return 'Cannot hear you';
  if (down('shopify') && down('gmail')) return 'Shopify and Gmail offline';
  if (down('shopify')) return 'Shopify offline';
  if (down('gmail')) return 'Gmail offline';
  if (down('tts') || down('scribe')) return 'Voice fallback in use';
  if (down('whisper')) return 'No offline recogniser';
  return 'Partly offline';
}

let knownBuild = null;
function maybeReloadForNewBuild(build) {
  if (!build) return;
  if (knownBuild === null) { knownBuild = build; return; }
  if (build === knownBuild) return;
  // The Mac now serves newer page files. Take them the moment nothing is in progress.
  if (busy || recording || speakingVia || el.settings.open) return;
  knownBuild = build;
  if (swRegistration) {
    // Let the worker fetch the new build first, so the reload lands on a shell that is
    // already cached; if no new worker takes over, reload anyway after a grace period.
    swRegistration.update().catch(() => {});
    setTimeout(() => { if (!reloadingForUpdate && idle()) location.reload(); }, UPDATE_GRACE_MS);
    return;
  }
  location.reload();
}

function setService(name, ok) {
  const node = el.svc[name];
  if (!node) return;
  node.dataset.ok = ok === true ? 'true' : ok === false ? 'false' : 'unknown';
}

// One health request in flight at a time, and never one that waits forever. Without both, a
// pad on a bad link queues a poll every interval and releases them all at once when the link
// returns — hundreds of requests in a second, seen on a second pad — and the Mac runs a
// whisper inference for each.
let healthInFlight = false;
const HEALTH_TIMEOUT_MS = 20000;   // the Mac's own checks give up at 6 s each

async function pollHealth(fresh = false) {
  if (document.hidden || healthInFlight) return;
  healthInFlight = true;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
  try {
    const response = await fetch(fresh ? '/health?fresh=1' : '/health', { cache: 'no-store', signal: controller.signal });
    const data = await response.json();
    if (reachable !== true) wentOnline();
    applyUpdateWhenIdle();
    const checks = data.checks || {};
    const failed = Object.entries(checks).filter(([, c]) => !c.ok).map(([k]) => k);
    if (!failed.length) setConn('ok', 'Online');
    else setConn('degraded', faultLabel(checks));
    maybeReloadForNewBuild(data.build);
    setService('shopify', checks.shopify ? checks.shopify.ok : null);
    setService('gmail', checks.gmail ? checks.gmail.ok : null);
    const canHear = !checks.speech || checks.speech.ok;
    const canSpeak = !checks.tts || checks.tts.ok;
    setService('voice', canHear && canSpeak);
    renderHealthRows(checks);
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
    clear(el.health);
    el.health.appendChild(healthRow(false, 'the Mac', 'Cannot reach the assistant. Is the Mac awake and is it running (make up)?'));
    el.voiceStatus.textContent = 'Unknown';
    el.voiceStatus.className = 'badge quiet';
    wentOffline();
  } finally {
    clearTimeout(timer);
    healthInFlight = false;
  }
}
const HEALTH_NAMES = {
  claude: 'Claude', speech: 'Hearing', scribe: 'ElevenLabs hearing', whisper: 'Offline hearing',
  tts: 'Voice', shopify: 'Shopify', gmail: 'Gmail', knowledge_base: 'Knowledge', terminology: 'Product names',
  writes: 'Changes',
};
function healthRow(ok, name, detail) {
  const row = document.createElement('div');
  row.className = 'hrow';
  row.dataset.ok = ok ? 'true' : 'false';
  const dot = document.createElement('span'); dot.className = 'hdot';
  const label = document.createElement('span'); label.className = 'hname'; label.textContent = name;
  const text = document.createElement('span'); text.className = 'hdetail'; text.textContent = detail || '';
  row.appendChild(dot); row.appendChild(label); row.appendChild(text);
  return row;
}
function renderHealthRows(checks) {
  clear(el.health);
  const order = ['claude', 'speech', 'tts', 'shopify', 'gmail', 'writes', 'scribe', 'whisper', 'knowledge_base', 'terminology'];
  for (const key of order) {
    const c = checks[key];
    if (!c) continue;
    el.health.appendChild(healthRow(c.ok, HEALTH_NAMES[key] || key, c.detail));
  }
}

pollHealth();
setInterval(() => pollHealth(false), 30000);

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
  renderRecent();
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
  renderRecent();
}

// The orb screen keeps one quiet way back to what was last shown.
function renderRecent() {
  const entry = history[history.length - 1];
  if (!entry) { el.recent.hidden = true; return; }
  el.recent.hidden = false;
  el.recentLabel.textContent = entry.question && !entry.question.startsWith('fixture:')
    ? entry.question : 'Last context';
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
  const ui = window.CrooksUI ? window.CrooksUI.render(data.ui, renderOpts()) : { nodes: [], skipped: [], stack: null, errors: [], hasContext: false };
  if (ui.skipped.length) console.warn('[crooks] skipped ui items:', ui.skipped.join(', '));
  el.errline.textContent = '';
  lastErrorTitle = '';
  if (ui.errors.length) {
    lastErrorTitle = ui.errors[0].title || 'Something went wrong';
    el.errline.textContent = ui.errors[0].recovery || '';
  }
  if (ui.stack) currentStack = ui.stack;
  // The attention surface shows only what this turn returned; a count from this morning
  // must not sit on the screen at four o'clock as if it were still true.
  const attention = (data.ui || []).filter((i) => i && i.type === 'attention' && i.data && Array.isArray(i.data.items));
  attentionItems = attention.length ? attention[0].data.items : [];
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

/* ----------------------------------------------------------------- actions */

// The owner tapped a proposal. Send its id — and only its id — to the Mac, which executes
// what it stored when the proposal was staged, proves it, and answers with what to show.
// Never sent twice: if the connection drops mid-tap the tablet asks what happened instead.
const ACTION_TIMEOUT_MS = 30000;   // a precondition read, the change, a verifying read

// A tap counts only when the voice interaction is quiet. Holding to speak wins.
function actionBlocked() {
  return recording || pendingStart || busy;
}

function renderOpts() {
  return { onCommit: commitAction, blocked: actionBlocked };
}

async function commitAction(proposalId, node) {
  if (actionBlocked()) { settleActionNode(node, 'armed'); return; }
  haptic(HAPTIC.start);
  const form = new FormData();
  form.append('session_id', sessionId);
  let payload = null;
  let status = 0;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ACTION_TIMEOUT_MS);
  try {
    const response = await fetch(`/actions/${encodeURIComponent(proposalId)}/commit`, {
      method: 'POST', body: form, signal: controller.signal, cache: 'no-store',
    });
    status = response.status;
    payload = await response.json();
  } catch {
    // The request may have reached the Mac. It is never resent; the Mac's record decides.
    payload = await recoverActionState(proposalId);
  } finally {
    clearTimeout(timer);
  }
  settleAction(node, payload, status);
}

async function recoverActionState(proposalId) {
  for (let attempt = 0; attempt < 4; attempt++) {
    await new Promise((r) => setTimeout(r, 1500 * (attempt + 1)));
    try {
      const response = await fetch(`/actions/${encodeURIComponent(proposalId)}?session_id=${encodeURIComponent(sessionId)}`, { cache: 'no-store' });
      const data = await response.json();
      if (data && data.status && data.status !== 'executing') return data;
    } catch { /* still unreachable; try again */ }
  }
  return null;
}

// Everything on screen follows from what the Mac answered. Success is shown only when the
// Mac says VERIFIED; anything else is shown as exactly what it is.
function settleAction(node, payload, status) {
  if (!payload) {
    settleActionNode(node, 'unknown', "Couldn't reach the Mac · check the order");
    el.errline.textContent = 'The Mac did not confirm that. Check the order before trying again.';
    haptic(HAPTIC.error);
    return;
  }
  const code = String(payload.code || payload.status || (status >= 400 ? 'not_authorised' : 'failed'));
  const items = Array.isArray(payload.ui) ? payload.ui : [];
  if (payload.status === 'verified' && payload.undo && items.length && items[0].type === 'success') {
    items[0].data.undo = Object.assign({ label: 'Undo', armed_after_ms: 650 }, payload.undo);
  }
  const rendered = window.CrooksUI ? window.CrooksUI.render(items, renderOpts()) : { nodes: [] };
  if (rendered.nodes.length) {
    replaceCard(node, rendered.nodes);
  } else {
    settleActionNode(node, code === 'verified' ? 'verified' : code, ACTION_LABELS[code] || 'Not applied');
  }
  if (status >= 400 && !items.length) {
    el.errline.textContent = ACTION_REASONS[code] || String(payload.detail || 'That could not be applied.');
  }
  haptic(payload.status === 'verified' ? HAPTIC.done : HAPTIC.error);
  if (payload.spoken) speakAnswer(String(payload.spoken), { isError: payload.status !== 'verified' });
}

const ACTION_LABELS = {
  verified: 'Applied', stale: 'Not applied', expired: 'Expired', revoked: 'Withdrawn', already_executed: 'Already applied',
  unverified: 'Not confirmed', service_unavailable: 'Not applied', not_authorised: 'Not allowed', writes_disabled: 'Switched off',
  allow_list_missing: 'Not configured', scope_missing: 'Not permitted', unknown: 'Unknown', wrong_session: 'Not this conversation',
};
const ACTION_REASONS = {
  not_authorised: 'This tablet is not allowed to apply changes. Check CROOKS_ALLOWED_LOGINS on the Mac.',
  writes_disabled: 'Changes are switched off on the Mac (CROOKS_WRITES_ENABLED).',
  allow_list_missing: 'No allowed logins are configured on the Mac (CROOKS_ALLOWED_LOGINS).',
  scope_missing: 'The Shopify app has not been granted permission to write orders.',
  unknown: 'The Mac no longer has that proposal. Ask again.',
  wrong_session: 'That proposal belongs to another conversation.',
};

function settleActionNode(node, state, label) {
  if (node && typeof node.settle === 'function') node.settle(state, label);
}

// Pending surfaces on screen, in every context the deck still holds.
function settlePendingActions(state, label) {
  const seen = new Set();
  const visit = (node) => {
    if (!node || seen.has(node)) return;
    seen.add(node);
    if (typeof node.settle === 'function') {
      const surface = node.querySelector ? node.querySelector('.action-surface') : null;
      const current = surface ? surface.dataset.state : '';
      if (current === 'arming' || current === 'armed') node.settle(state, label);
    }
  };
  for (const entry of history) for (const node of entry.nodes) visit(node);
  if (el.cards) for (const node of Array.from(el.cards.children)) visit(node);
}

// A settled action replaces its card, and a verified re-read of the entity replaces every
// card that showed that entity, so the screen shows Shopify as it now is.
function replaceCard(oldNode, newNodes) {
  const first = newNodes[0];
  const rest = newNodes.slice(1);
  for (const entry of history) {
    const at = entry.nodes.indexOf(oldNode);
    if (at !== -1) entry.nodes.splice(at, 1, ...newNodes);
  }
  if (oldNode.parentNode) {
    oldNode.parentNode.replaceChild(first, oldNode);
    let after = first;
    for (const node of rest) { after.parentNode.insertBefore(node, after.nextSibling); after = node; }
  }
  for (const node of newNodes) {
    if (node.dataset && node.dataset.type === 'order' && node.dataset.ref) refreshEntityCards(node);
  }
}

function refreshEntityCards(fresh) {
  const ref = fresh.dataset.ref;
  const replaceIn = (list) => {
    for (let i = 0; i < list.length; i++) {
      const node = list[i];
      if (node !== fresh && node.dataset && node.dataset.type === 'order' && node.dataset.ref === ref) {
        const copy = fresh.cloneNode(true);
        copy.dataset.ref = ref;
        if (node.parentNode) node.parentNode.replaceChild(copy, node);
        list[i] = copy;
      }
    }
  };
  for (const entry of history) replaceIn(entry.nodes);
}

/* -------------------------------------------------------------------- turn */

function renderTimings(timings, transcript) {
  if (!el.timingToggle.checked || !timings) { el.timings.hidden = true; return; }
  el.timings.hidden = false;
  const parts = Object.entries(timings).map(([k, v]) => `${k} ${v}ms`);
  if (transcript && transcript.engine) parts.unshift(`heard by ${transcript.engine}`);
  el.timings.textContent = parts.join('  ·  ');
}

// While a turn is in flight, ask the backend what it is actually doing. The state on screen
// is driven by the tool that is running, never inferred from the question.
const STATE_POLL_MS = 400;
const STATE_POLL_TIMEOUT_MS = 5000;
function startStatePolling() {
  stopStatePolling();
  let inFlight = false;   // a tick while the last poll is still out is skipped, never stacked
  statePoll = setInterval(async () => {
    if (!busy || inFlight || document.hidden) return;
    inFlight = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), STATE_POLL_TIMEOUT_MS);
    try {
      const data = await (await fetch(`/state/${encodeURIComponent(sessionId)}`, { cache: 'no-store', signal: controller.signal })).json();
      if (!busy || !data.known) return;
      if (data.state && data.state !== 'READY' && data.state !== 'ERROR') setState(data.state);
      // The transcript, the moment the Mac has it: a mis-heard question shows before the
      // answer to it is paid for.
      if (data.heard && !el.heard.textContent) el.heard.textContent = `“${data.heard}”`;
    } catch { /* the turn response will carry the outcome */ } finally {
      clearTimeout(timer);
      inFlight = false;
    }
  }, STATE_POLL_MS);
}
function stopStatePolling() { if (statePoll) { clearInterval(statePoll); statePoll = null; } }

const SPEAK_HEADERS_TIMEOUT_MS = 15000;   // the Mac's own TTS timeout is 10 s
let turnAbort = null;         // the in-flight /turn, so holding through a slow one can drop it
const TURN_TIMEOUT_MS = 130000; // a little over the backend's own 120 s turn timeout

async function submit(body, isAudio) {
  busy = true;
  el.talk.dataset.busy = 'true';
  // A new instruction withdraws whatever was proposed under the last one. The Mac decides
  // the same thing on its side; the card goes quiet here so it cannot be tapped meanwhile.
  settlePendingActions('revoked', 'Withdrawn');
  el.errline.textContent = '';
  el.heard.textContent = '';
  setState('TRANSCRIBING', isAudio ? 'Transcribing' : 'Thinking');
  startStatePolling();
  const controller = new AbortController();
  turnAbort = controller;
  const timeout = setTimeout(() => {
    controller.abort();
    // The Mac may still be holding the turn; tell it to let go so the next question is not
    // queued behind a dead one.
    const form = new FormData();
    form.append('session_id', sessionId);
    fetch('/cancel', { method: 'POST', body: form }).catch(() => { /* it will time out on its own */ });
  }, TURN_TIMEOUT_MS);
  try {
    const options = isAudio
      ? { method: 'POST', body, signal: controller.signal }
      : { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), signal: controller.signal };
    if (isAudio) setTimeout(() => { if (busy && el.stage.dataset.state === 'TRANSCRIBING') setState('THINKING'); }, 1200);
    const response = await fetch('/turn', options);
    if (!response.ok) {
      lastWasError = true;
      lastErrorTitle = 'The Mac hit a problem';
      el.errline.textContent = `The assistant on the Mac answered with an error (${response.status}). Try again.`;
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
    renderTimings(data.timings_ms, data.transcript);

    lastWasError = Boolean(data.error_kind);
    renderTurn(data);
    // The text is on screen before the voice is asked for; the answer never waits on audio.
    setState(lastWasError ? 'ERROR' : 'READY', lastWasError ? lastErrorTitle : '');
    haptic(lastWasError ? HAPTIC.error : HAPTIC.done);
    speakAnswer(data.answer, { isError: lastWasError });   // deliberately not awaited
  } catch (error) {
    if (controller.signal.aborted && controller.cancelled) {
      // The owner moved on: nothing to report, the next question is already being asked.
      el.heard.textContent = '';
      el.answer.textContent = '';
      setState('READY');
      return;
    }
    lastWasError = true;
    lastErrorTitle = controller.signal.aborted ? 'The Mac took too long' : 'The Mac did not answer';
    el.errline.textContent = controller.signal.aborted
      ? 'That question was abandoned after two minutes. Ask again.'
      : 'Is the Mac awake, and is the assistant running on it? (make up)';
    setState('ERROR', lastErrorTitle);
    setConn('down', 'Offline');
    haptic(HAPTIC.error);
    if (!controller.signal.aborted) setTimeout(checkReachable, 0);   // after `finally` clears busy
  } finally {
    clearTimeout(timeout);
    if (turnAbort === controller) turnAbort = null;
    stopStatePolling();
    busy = false;
    el.talk.dataset.busy = 'false';
    applyUpdateWhenIdle();
    // If speech is off there is no onend to settle the state, so do it here.
    if (!el.speakToggle.checked) setState(lastWasError ? 'ERROR' : 'READY', lastWasError ? lastErrorTitle : '');
  }
}

function sendAudio(blob) {
  const form = new FormData();
  form.append('audio', blob, 'turn.webm');
  form.append('session_id', sessionId);
  form.append('turns', String(turns));
  form.append('speak', el.speakToggle.checked ? '1' : '0');
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
  holding = true;
  unlockSpeech();          // must be inside the gesture
  stopSpeaking();          // before anything else: the voice must not be recorded answering itself
  acquireWakeLock();
  if (busy) {
    // A turn is in flight. Say so; and if the hold goes on, take it as "forget that one".
    showBusyHint();
    clearTimeout(cancelHoldTimer);
    cancelHoldTimer = setTimeout(cancelTurnAndListen, CANCEL_HOLD_MS);
    return;
  }
  setState('LISTENING');   // the orb wakes on the touch itself, not on the recorder
  startRecording();        // start before any other UI work, or the first word is clipped
}
let busyHintTimer = null;
let cancelHoldTimer = null;
let holding = false;         // the thumb is down on a hold surface
const CANCEL_HOLD_MS = 900;   // hold this long through a turn in flight to abandon it

function showBusyHint() {
  el.talkLabel.textContent = 'Keep holding to ask something else';
  if (orb) orb.pulse();
  clearTimeout(busyHintTimer);
  busyHintTimer = setTimeout(() => { if (!recording) el.talkLabel.textContent = 'Hold to speak'; }, 1600);
}

// The owner is still holding: the question in flight is not the one he wants answered.
// Drop it on the tablet, tell the Mac to stop thinking about it, and start listening.
function cancelTurnAndListen() {
  cancelHoldTimer = null;
  if (!busy || !turnAbort) return;
  turnAbort.cancelled = true;
  turnAbort.abort();
  const form = new FormData();
  form.append('session_id', sessionId);
  fetch('/cancel', { method: 'POST', body: form }).catch(() => { /* the abort already freed the tablet */ });
  haptic(HAPTIC.start);
  // submit()'s finally clears busy once the abort lands; start listening right after it —
  // if the thumb is still down. A thumb that lifted meanwhile just wanted the question gone.
  setTimeout(() => { if (holding && !busy && !recording) { setState('LISTENING'); startRecording(); } }, 60);
}

function onHoldEnd(event) {
  event.preventDefault();
  holding = false;
  try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* noop */ }
  if (cancelHoldTimer) { clearTimeout(cancelHoldTimer); cancelHoldTimer = null; }   // a tap, not a hold
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
el.recent.addEventListener('click', () => { if (history.length) showHistory(history.length - 1); });
el.attention.addEventListener('click', () => {
  if (!window.CrooksUI || !attentionItems.length) return;
  const node = window.CrooksUI.renderItem({ type: 'attention', data: { items: attentionItems } });
  if (node) pushContext([node], [], '');
});

el.settingsBtn.addEventListener('click', () => { unlockSpeech(); loadVoices(); pollHealth(true); el.settings.showModal(); });
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
el.streamToggle.checked = store.get('crooks.stream', '1') !== '0';
el.streamToggle.addEventListener('change', () => store.set('crooks.stream', el.streamToggle.checked ? '1' : '0'));
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
  renderRecent();
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
        const ui = window.CrooksUI.render(fixture.items, Object.assign(renderOpts(), { fixture: true }));
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
    submit({ text, session_id: sessionId, turns, speak: el.speakToggle.checked }, false);
  });
}

/* ------------------------------------------------------------- system layer */

// The Mac is the only server. While it cannot be reached the page is a fixture with nothing
// behind it, so it says so in CROOKS's own words, keeps asking quietly, and comes back on its
// own. /ping costs the Mac nothing and is never cached, so the answer is always the truth.
const PING_TIMEOUT_MS = 4000;
const RECONNECT_MIN_MS = 3000;
const RECONNECT_MAX_MS = 15000;
let reachable = null;            // null until the first answer, then true or false
let reconnectTimer = null;
let reconnectDelay = RECONNECT_MIN_MS;
let pingInFlight = false;

function idle() {
  return !busy && !recording && !speakingVia && !pendingStart && !el.settings.open;
}

function setSystem(phase, title, sub, note) {
  el.system.dataset.phase = phase;
  if (title !== undefined) el.systemTitle.textContent = title;
  if (sub !== undefined) el.systemSub.textContent = sub;
  if (note !== undefined) el.systemNote.textContent = note;
}

async function checkReachable() {
  if (pingInFlight) return;
  pingInFlight = true;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PING_TIMEOUT_MS);
  try {
    const response = await fetch('/ping', { cache: 'no-store', signal: controller.signal });
    if (!response.ok) throw new Error(`ping ${response.status}`);
    const data = await response.json();
    if (!data.ok) throw new Error('ping not ok');
    wentOnline();
  } catch {
    wentOffline();
  } finally {
    clearTimeout(timer);
    pingInFlight = false;
  }
}

function wentOnline() {
  const wasDown = reachable === false;
  reachable = true;
  clearTimeout(reconnectTimer);
  reconnectTimer = null;
  reconnectDelay = RECONNECT_MIN_MS;
  setSystem('online');
  if (wasDown) {
    // Back after an outage: the pill, the sheet's rows, the lock and the microphone all need
    // re-establishing, and a build shipped while we were away should be taken.
    setConn('connecting', 'Connecting');
    pollHealth(true);
    acquireWakeLock();
    warmMic();
    if (swRegistration) swRegistration.update().catch(() => {});
  }
}

function wentOffline() {
  reachable = false;
  // Never over a question in flight, a recording, or Derek mid-sentence: the turn's own
  // error copy covers those, and the layer takes over once the screen is quiet.
  if (idle()) {
    setSystem('offline', 'System offline', 'Waiting for CROOKS Assistant…', 'Checking quietly · tap to check now');
  }
  clearTimeout(reconnectTimer);
  reconnectTimer = setTimeout(checkReachable, reconnectDelay);
  reconnectDelay = Math.min(Math.round(reconnectDelay * 1.6), RECONNECT_MAX_MS);
}

el.system.addEventListener('click', () => { if (reachable === false) { reconnectDelay = RECONNECT_MIN_MS; checkReachable(); } });
window.addEventListener('online', () => { if (reachable !== true) checkReachable(); });
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && reachable === false) checkReachable();
});

/* ------------------------------------------------------------- installed app */

// The service worker keeps the shell — page, scripts, styles, icons — and nothing else, so the
// installed app opens instantly and opens at all when the Mac is away. A newer build installs
// in the background and is taken only when nothing is in progress; the page then reloads
// once onto the shell the new worker has already cached.
const UPDATE_GRACE_MS = 20000;
let swRegistration = null;
let updateWaiting = null;        // a newer build, installed and waiting for an idle moment
let updateApplied = false;       // we asked it to take over; the next controllerchange is ours
let reloadingForUpdate = false;

function applyUpdateWhenIdle() {
  if (!updateWaiting || !idle()) return;
  const worker = updateWaiting;
  updateWaiting = null;
  updateApplied = true;
  worker.postMessage({ type: 'SKIP_WAITING' });
}

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register('/sw.js').then((registration) => {
    swRegistration = registration;
    if (registration.waiting && navigator.serviceWorker.controller) {
      updateWaiting = registration.waiting;
      applyUpdateWhenIdle();
    }
    registration.addEventListener('updatefound', () => {
      const worker = registration.installing;
      if (!worker) return;
      worker.addEventListener('statechange', () => {
        // Installed behind a running page: a new build is ready. Without a controller it is
        // the first install, and the page is already the current build.
        if (worker.state === 'installed' && navigator.serviceWorker.controller) {
          updateWaiting = worker;
          applyUpdateWhenIdle();
        }
      });
    });
  }).catch(() => { /* the page works without it; only instant, offline startup is lost */ });
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!updateApplied || reloadingForUpdate) return;
    reloadingForUpdate = true;
    location.reload();
  });
}

registerServiceWorker();
checkReachable();
acquireWakeLock();
setMode('orb');
setState('READY');
