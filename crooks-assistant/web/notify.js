/* CROOKS OS — one place messages come from, and three places they can appear.
 *
 * The live session floated two bubbles over whatever was on screen: "Divided. Tap a half to
 * talk to it…" and "Merged. 2 changes still waiting over there." The second is the clearer
 * fault — it is a sentence about the OTHER half, printed over the half the owner was looking
 * at — but both are the same mistake: a message with no home, drawn on top of the furniture.
 *
 * So a message declares where it belongs, and that decides where it is drawn:
 *
 *   CONTROL    the invalid email, the quantity that changed, the microphone that is armed.
 *              Drawn on the control, directly after it, inside the card. It moves and scrolls
 *              with the thing it is about, so it cannot cover anything else.
 *   WORKSPACE  the draft that saved, the archive that was proved, the refund that went
 *              through, the half that divided or merged. Drawn in the workspace, above the
 *              deck, IN FLOW — a workspace message takes space rather than borrowing it.
 *   GLOBAL     the Mac cannot be reached; this build must be updated. Two states of the
 *              machine itself, and the only ones allowed to appear over every screen — and
 *              even then in flow, at the top, above the wordmark, pushing the screen down.
 *
 * Nothing here floats over the dock, the orb, the halves, Back, Next, Split, the composer or
 * an approval surface, because nothing here is positioned over anything: every host is a
 * normal block in the document. That is not a style choice, it is the mechanism — and
 * web/collide.js measures it in Chromium so it stays true.
 *
 * Four other rules the session earned:
 *   - a message about a half carries its `branch`, and is hidden while the other half is
 *     focused. It is still there when the owner comes back to it.
 *   - the same message twice is one row with a count, not two rows.
 *   - a failure persists until it is dismissed; a low-risk success goes on its own.
 *   - a message is never a way to get anywhere. The only control a row may carry is Dismiss.
 *
 * Text reaches the page through textContent, like everything else the owner did not type.
 */
(function (root) {
  'use strict';

  const CLASSES = ['control', 'workspace', 'global'];
  const TONES = ['info', 'good', 'warn', 'bad'];
  // A low-risk success goes by itself. Four seconds is what the old bubble used, and it was
  // long enough to read "Draft saved" and short enough not to sit over the next thing.
  const TTL_MS = { info: 4000, good: 4000, warn: 9000, bad: 0 };   // 0 = until dismissed
  // Per host, so a run of failures cannot push the deck off the screen. The oldest goes.
  const MAX_PER_HOST = 3;
  // Same message, said again, inside this window: one row, with a count.
  const REPEAT_MS = 20000;

  let doc = null;
  let hosts = { global: null, orbWorkspace: null, deckWorkspace: null };
  let onRecord = null;         // the app hands in its telemetry recorder
  let modeOf = () => '';       // and its way of asking which screen is up
  let focused = '';            // the half whose messages are the ones on screen
  let seq = 0;
  const live = [];             // every message that has not been dismissed yet, in order

  function now() { return Date.now(); }

  const el = (tag, cls) => {
    const node = doc.createElement(tag);
    if (cls) node.className = cls;
    return node;
  };

  /* Where this message goes, given what it is and which screen is up.
     A workspace message with no workspace on screen is drawn in the orb screen's own slot —
     still in flow, still under the caption, still above the halves. */
  function hostFor(entry) {
    if (entry.class === 'global') return hosts.global;
    if (entry.class === 'workspace') {
      return modeOf() === 'context' ? (hosts.deckWorkspace || hosts.global) : (hosts.orbWorkspace || hosts.global);
    }
    return entry.host || null;    // control-local: the slot beside the control
  }

  function tone(value) {
    const word = String(value || 'info');
    return TONES.indexOf(word) === -1 ? 'info' : word;
  }

  function keyOf(entry) {
    return `${entry.class}:${entry.code || ''}:${entry.text}:${entry.branch || ''}`;
  }

  // ---- drawing -------------------------------------------------------------------------

  function build(entry) {
    const row = el('p', `note note-${entry.class} tone-${entry.tone}`);
    row.dataset.notify = entry.class;
    row.dataset.tone = entry.tone;
    if (entry.branch) row.dataset.branch = entry.branch;
    // A word as well as a colour, always: a workbench light and a cheap panel take the
    // colour out of a border long before they take a word out of a line.
    const mark = el('span', 'note-mark');
    mark.textContent = entry.tone === 'bad' ? 'Failed' : entry.tone === 'warn' ? 'Check' : entry.tone === 'good' ? 'Done' : 'Note';
    row.appendChild(mark);
    const words = el('span', 'note-words');
    words.textContent = entry.text;
    row.appendChild(words);
    const count = el('span', 'note-count');
    count.textContent = '';
    count.hidden = true;
    row.appendChild(count);
    // Dismiss, and nothing else. A message must never become a way to get somewhere: that is
    // how a transient line turns into navigation, and how a tap lands on a screen that has
    // already gone. Only a message that will not leave on its own carries one.
    if (!entry.ttl) {
      const close = el('button', 'note-dismiss');
      close.type = 'button';
      close.setAttribute('aria-label', 'Dismiss this message');
      close.textContent = 'Dismiss';
      close.addEventListener('click', () => dismiss(entry.id));
      row.appendChild(close);
    }
    entry.node = row;
    entry.countNode = count;
    return row;
  }

  /* One host, redrawn from `live`: the order on screen is the order they arrived in, which is
     the only order a person can follow. Nothing is moved by a later message arriving. */
  function paint(host) {
    if (!host) return;
    const mine = live.filter((e) => e.node && e.node.parentNode === host);
    while (host.firstChild) host.removeChild(host.firstChild);
    for (const entry of mine) {
      entry.node.hidden = Boolean(entry.branch) && Boolean(focused) && entry.branch !== focused;
      host.appendChild(entry.node);
    }
    host.hidden = mine.every((e) => e.node.hidden);
  }

  function attach(entry) {
    const host = hostFor(entry);
    if (!host) return false;
    const node = build(entry);
    // Control-local: after the control, never inside it — a button that grows a paragraph
    // changes size under the thumb that is still on it.
    if (entry.class === 'control') {
      const anchor = entry.after || null;
      if (anchor && anchor.parentNode === host) host.insertBefore(node, anchor.nextSibling);
      else host.appendChild(node);
      entry.hostEl = host;
      return true;
    }
    entry.hostEl = host;
    host.appendChild(node);
    const mine = live.filter((e) => e.hostEl === host);
    while (mine.length > MAX_PER_HOST) {
      const oldest = mine.shift();
      remove(oldest);
    }
    paint(host);
    return true;
  }

  function remove(entry) {
    if (entry.timer) { clearTimeout(entry.timer); entry.timer = null; }
    const index = live.indexOf(entry);
    if (index !== -1) live.splice(index, 1);
    if (entry.node && entry.node.parentNode) entry.node.parentNode.removeChild(entry.node);
    if (entry.hostEl && entry.hostEl !== entry.host) paint(entry.hostEl);
    else if (entry.hostEl) entry.hostEl.hidden = !entry.hostEl.firstChild;
  }

  // ---- the api -------------------------------------------------------------------------

  /* The page hands in its hosts once. `global` is above the wordmark, `orbWorkspace` under
     the orb's caption, `deckWorkspace` above the deck — all three in flow. */
  function init(config) {
    const c = config || {};
    doc = c.document || (typeof document !== 'undefined' ? document : null);
    hosts = {
      global: c.global || null,
      orbWorkspace: c.orbWorkspace || null,
      deckWorkspace: c.deckWorkspace || null,
    };
    if (typeof c.record === 'function') onRecord = c.record;
    if (typeof c.mode === 'function') modeOf = c.mode;
    return Boolean(doc);
  }

  /* Say something.
   *
   *   text     the words
   *   class    'control' | 'workspace' | 'global'
   *   tone     'info' | 'good' | 'warn' | 'bad'   (bad persists; info and good go)
   *   code     a short stable name for this kind of message, for deduplication and telemetry
   *   branch   the half this is about, if it is about one
   *   host     control-local only: the element to draw inside
   *   after    control-local only: the control to sit directly after
   *   persist  keep it until dismissed even if the tone would let it go
   */
  function show(message) {
    const m = message || {};
    const words = String(m.text || '').trim();
    if (!doc || !words) return null;
    const entry = {
      id: `note_${++seq}`,
      class: CLASSES.indexOf(String(m.class)) === -1 ? 'workspace' : String(m.class),
      tone: tone(m.tone),
      text: words,
      code: String(m.code || ''),
      branch: String(m.branch || ''),
      host: m.host || null,
      after: m.after || null,
      at: now(),
      repeats: 1,
    };
    // A global message is the machine's own state and nothing else. Anything else that asks
    // to be global is a workspace message that has not been told where it belongs.
    if (entry.class === 'global' && !m.machine) entry.class = 'workspace';
    entry.ttl = m.persist || entry.tone === 'bad' ? 0 : (typeof m.ttl === 'number' ? m.ttl : TTL_MS[entry.tone]);

    const key = keyOf(entry);
    const same = live.find((e) => keyOf(e) === key && entry.at - e.at < REPEAT_MS);
    if (same) {
      same.repeats += 1;
      same.at = entry.at;
      if (same.countNode) {
        same.countNode.textContent = `×${same.repeats}`;
        same.countNode.hidden = false;
      }
      if (same.timer) { clearTimeout(same.timer); same.timer = null; }
      if (same.ttl) same.timer = setTimeout(() => remove(same), same.ttl);
      if (onRecord) onRecord('notify', { name: same.class, code: same.code || undefined, tone: same.tone, repeat: same.repeats });
      return same;
    }

    live.push(entry);
    if (!attach(entry)) { live.pop(); return null; }
    if (entry.ttl) entry.timer = setTimeout(() => remove(entry), entry.ttl);
    if (onRecord) {
      onRecord('notify', {
        name: entry.class, code: entry.code || undefined, tone: entry.tone,
        branch: entry.branch || undefined, persists: entry.ttl === 0,
      });
    }
    return entry;
  }

  function dismiss(id) {
    const entry = live.find((e) => e.id === id);
    if (entry) remove(entry);
    return Boolean(entry);
  }

  /* Which half is on screen. Messages about the other one stay where they are and stop being
     drawn; they are still theirs when it is focused again. */
  function focusBranch(branchId) {
    focused = String(branchId || '');
    for (const host of [hosts.global, hosts.orbWorkspace, hosts.deckWorkspace]) paint(host);
    return focused;
  }

  /* The mode changed, so a workspace message may have the other host now. */
  function remode() {
    const wanted = modeOf() === 'context' ? hosts.deckWorkspace : hosts.orbWorkspace;
    for (const entry of live) {
      if (entry.class !== 'workspace' || !entry.node) continue;
      if (wanted && entry.node.parentNode !== wanted) { entry.hostEl = wanted; wanted.appendChild(entry.node); }
    }
    for (const host of [hosts.global, hosts.orbWorkspace, hosts.deckWorkspace]) paint(host);
  }

  /* Everything that has not gone yet, as data — for a test, and for the telemetry snapshot. */
  function list() {
    return live.map((e) => ({
      id: e.id, class: e.class, tone: e.tone, code: e.code, branch: e.branch,
      persists: e.ttl === 0, repeats: e.repeats, shown: Boolean(e.node && !e.node.hidden),
    }));
  }

  function clear(filter) {
    const f = filter || {};
    for (const entry of live.slice()) {
      if (f.class && entry.class !== f.class) continue;
      if (f.branch && entry.branch !== f.branch) continue;
      if (f.code && entry.code !== f.code) continue;
      if (f.keepFailures && entry.ttl === 0) continue;
      remove(entry);
    }
  }

  function reset() {
    for (const entry of live.slice()) remove(entry);
    live.length = 0;
    seq = 0;
    focused = '';
    onRecord = null;
    modeOf = () => '';
    hosts = { global: null, orbWorkspace: null, deckWorkspace: null };
  }

  const api = { CLASSES, TONES, TTL_MS, MAX_PER_HOST, REPEAT_MS, init, show, dismiss, focusBranch, remode, list, clear, reset };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CrooksNotify = api;
})(typeof window !== 'undefined' ? window : globalThis);
