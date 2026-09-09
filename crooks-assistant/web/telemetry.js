/* CROOKS OS — what the tablet actually did, for a test session.
 *
 * While a test session is running on the Mac (the page learns it from /health and from every
 * /turn answer), the page keeps a small, structured account of itself: what it rendered —
 * screen, card types, tabs, the chips on the rail and whether they were enabled — what the
 * owner touched, where it navigated, what failed to load, when it lost the Mac. Semantic
 * state, never the DOM: no markup, no screenshots, no text the cards showed.
 *
 * Nothing here is ever waited for. Events go on a queue; the queue is posted every couple of
 * seconds, or at forty events, with fetch keepalive (sendBeacon on pagehide). A post that
 * fails is dropped. Off, `record` is a boolean test and a return.
 */
(function (root) {
  'use strict';

  const FLUSH_MS = 2000;
  const FLUSH_AT = 40;
  const MAX_QUEUE = 300;
  const MAX_STRING = 400;
  const MAX_ITEMS = 40;
  const ENDPOINT = '/telemetry';

  let enabled = false;
  let testSession = null;
  let queue = [];
  let timer = null;
  let seq = 0;
  let context = { session_id: '', turn_id: '' };
  let transport = null;   // tests hand in a function; the page uses fetch / sendBeacon
  let sent = 0;
  let dropped = 0;

  function now() { return Date.now(); }

  const MAX_DEPTH = 6;   // render → cards → card → actions → action → id

  function bounded(value, depth) {
    depth = depth || 0;
    if (depth > MAX_DEPTH) return undefined;
    if (value === null || value === undefined) return undefined;
    if (typeof value === 'boolean' || typeof value === 'number') return Number.isFinite(value) || typeof value === 'boolean' ? value : undefined;
    if (typeof value === 'string') return value.length > MAX_STRING ? value.slice(0, MAX_STRING) + '…' : value;
    if (Array.isArray(value)) return value.slice(0, MAX_ITEMS).map((v) => bounded(v, depth + 1));
    if (typeof value === 'object') {
      const out = {};
      let n = 0;
      for (const key of Object.keys(value)) {
        if (n++ >= MAX_ITEMS) break;
        const v = bounded(value[key], depth + 1);
        if (v !== undefined) out[key] = v;
      }
      return out;
    }
    return undefined;
  }

  // The session in force on the Mac. From /health (every poll) and from every /turn answer,
  // so a session started on the Mac is noticed within one poll and no reload is needed.
  function configure(observability) {
    const id = observability && observability.test_session ? String(observability.test_session) : (typeof observability === 'string' ? observability : '');
    const was = enabled;
    testSession = id || null;
    enabled = Boolean(id);
    if (!enabled) { queue = []; if (timer) { clearTimeout(timer); timer = null; } }
    else if (!was) record('session_joined', { name: observability && observability.name ? String(observability.name) : undefined });
    return enabled;
  }

  function setContext(fields) {
    if (!fields) return;
    if (fields.session_id !== undefined) context.session_id = String(fields.session_id || '');
    if (fields.turn_id !== undefined) context.turn_id = String(fields.turn_id || '');
  }

  function record(kind, fields) {
    if (!enabled) return null;
    const event = Object.assign(
      context.session_id ? { session_id: context.session_id } : {},
      context.turn_id ? { turn_id: context.turn_id } : {},
      bounded(fields || {}) || {},
      { kind: String(kind), t: now(), seq: ++seq },   // last: a field never overwrites these
    );
    queue.push(event);
    if (queue.length > MAX_QUEUE) { dropped += queue.length - MAX_QUEUE; queue.splice(0, queue.length - MAX_QUEUE); }
    if (queue.length >= FLUSH_AT) flush(false);
    else if (!timer) timer = setTimeout(() => { timer = null; flush(false); }, FLUSH_MS);
    return event;
  }

  function flush(unloading) {
    if (timer) { clearTimeout(timer); timer = null; }
    if (!queue.length || !enabled) return false;
    const batch = queue;
    queue = [];
    const body = JSON.stringify({ session_id: context.session_id, test_session_id: testSession, events: batch });
    sent += batch.length;
    try {
      if (transport) { transport(body, Boolean(unloading)); return true; }
      if (unloading && root.navigator && typeof root.navigator.sendBeacon === 'function') {
        if (root.navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'application/json' }))) return true;
      }
      if (typeof root.fetch === 'function') {
        root.fetch(ENDPOINT, { method: 'POST', headers: { 'content-type': 'application/json' }, body, keepalive: true, cache: 'no-store' })
          .catch(() => { dropped += batch.length; });
        return true;
      }
    } catch { dropped += batch.length; }
    return false;
  }

  // ---- the screen, read as structure. The card renderer marks what it draws with data
  // attributes (type, ref, proposal, pending) and classes; this reads those, never the text.
  function pathOnly(src) {
    try { const u = new URL(String(src || ''), 'https://x/'); return u.pathname; } catch { return ''; }
  }

  function cardState(card, index) {
    const ds = card.dataset || {};
    const out = { i: index, type: ds.type || card.className.replace(/^card\s*/, '').split(' ')[0] || 'card' };
    if (ds.ref) out.ref = ds.ref;
    if (ds.proposal) out.proposal_id = ds.proposal;
    if (ds.pending) out.pending = ds.pending.split(' ').filter(Boolean);
    const q = (sel) => (card.querySelectorAll ? Array.from(card.querySelectorAll(sel)) : []);
    const tabs = q('[role="tab"]');
    if (tabs.length) {
      out.tabs = tabs.map((t) => t.textContent.trim().slice(0, 40));
      const active = tabs.find((t) => t.getAttribute('aria-selected') === 'true');
      if (active) out.tab_active = active.textContent.trim().slice(0, 40);
    }
    const sections = q('.sec');
    if (sections.length) out.sections = sections.map((s) => String(s.getAttribute('aria-label') || '').slice(0, 40)).filter(Boolean);
    const chips = q('.rail-chip');
    if (chips.length) {
      out.actions = chips.map((c) => {
        const a = { id: (c.dataset && c.dataset.action) || '', enabled: c.getAttribute('aria-disabled') !== 'true' };
        const why = c.querySelector ? c.querySelector('.rail-why') : null;
        if (!a.enabled && why) a.reason = why.textContent.trim().slice(0, 80);
        return a;
      });
    }
    const surface = card.querySelector ? card.querySelector('.action-surface') : null;
    if (surface) {
      const kind = (surface.className.match(/kind-([a-z_]+)/) || [])[1] || '';
      out.surface = { kind, state: (surface.dataset && surface.dataset.state) || '' };
      if (out.surface.state === 'unavailable') out.surface.reason = surface.textContent.trim().slice(0, 80);
    }
    const images = q('img');
    if (images.length) out.images = { count: images.length, missing: q('.is-missing').length, loaded: q('.is-loaded').length };
    if (typeof card.scrollWidth === 'number' && typeof card.clientWidth === 'number' && card.clientWidth && card.scrollWidth > card.clientWidth + 1) out.clipped_x = card.scrollWidth - card.clientWidth;
    if (typeof card.getBoundingClientRect === 'function') { try { out.height = Math.round(card.getBoundingClientRect().height); } catch { /* shim */ } }
    return out;
  }

  function snapshot(cardsEl, extra) {
    const doc = root.document;
    const cards = cardsEl && cardsEl.children ? Array.from(cardsEl.children) : [];
    const out = Object.assign({
      screen: doc && doc.body && doc.body.dataset ? (doc.body.dataset.mode || '') : '',
      cards: cards.map(cardState),
      viewport: { w: root.innerWidth || 0, h: root.innerHeight || 0, dpr: root.devicePixelRatio || 1 },
      document: {
        height: doc && doc.documentElement ? doc.documentElement.scrollHeight || 0 : 0,
        cards_height: cardsEl ? cardsEl.scrollHeight || 0 : 0,
        cards_visible: cardsEl ? cardsEl.clientHeight || 0 : 0,
      },
    }, extra || {});
    out.overflow = { long_scroll: out.document.cards_height > out.document.cards_visible + 8, clipped: out.cards.filter((c) => c.clipped_x).length };
    return out;
  }

  function status() { return { enabled, test_session: testSession, queued: queue.length, sent, dropped, seq }; }

  function reset() { enabled = false; testSession = null; queue = []; if (timer) clearTimeout(timer); timer = null; seq = 0; context = { session_id: '', turn_id: '' }; sent = 0; dropped = 0; }

  const api = { configure, setContext, record, flush, snapshot, cardState, pathOnly, status, reset, _setTransport(fn) { transport = fn; } };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CrooksTelemetry = api;
})(typeof window !== 'undefined' ? window : globalThis);
