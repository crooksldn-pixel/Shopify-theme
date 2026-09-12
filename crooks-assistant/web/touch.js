/* CROOKS OS — who owns this finger. Phase 5 §7, the machine behind D-1.
 *
 * WHAT HAPPENED. 11 September, 132 hold-starts in one evening; 131 of them reported
 * `target: "dock"` and one `orb`, and no other target exists in the file — because nothing
 * else ever got a touch. 63 of those "holds" were under 200 ms, in 19 bursts, and 26 of them
 * came in ten consecutive seconds while the owner said, out loud, "I cannot click the merge or
 * close button or any of the other buttons for the two blobs, because wherever I press just
 * leads to you listening". The transparent voice target was the size of the viewport
 * (`body[data-mode="orb"] .talk{inset:0}`), the branch chips were trapped in a lower stacking
 * context under it, and so every tap on Split, Merge or Close became a recording. The speech
 * pipeline reported them as "too short"; the analyser reported 62 "a value had to be exact and
 * a voice could not make it so" and made speech the top improvement candidate of a session in
 * which speech was the one thing working. One HCI defect produced a false engineering priority.
 *
 * THE FIX IS NOT A BIGGER HIT REGION WITH MORE EXCEPTIONS. It is an owner, decided once, per
 * pointer, from what the finger actually landed on:
 *
 *   CONTROL            it came down on something a finger presses. Never a sentence. Ever.
 *   SCROLL             it came down on a scroll container. Never a sentence.
 *   VOICE              it came down on a deliberate voice target and nothing else.
 *   SPLIT_GESTURE      it is one of a pair; the pair divides or merges the orb.
 *   APPROVAL_GESTURE   it came down on an action surface, which has its own drag.
 *   NONE               it came down on nothing that wants it. Also never a sentence.
 *
 * The rules, stated so they can be tested rather than reasoned about:
 *
 *   1. An owner is assigned on `down` and NEVER changes. `down` is idempotent per pointer id,
 *      so the document's capture listener and the voice surface's own listener can both ask
 *      and get the same answer with no second side effect.
 *   2. CONTROL beats VOICE on the same pointer, always, whatever the geometry says. This is
 *      the belt to §8's braces: even if a voice region is ever painted over a control again,
 *      the pointer that starts on the control cannot become a sentence.
 *   3. SCROLL beats VOICE on the same pointer.
 *   4. A second finger forming a pair CANCELS the pending single-finger voice interaction
 *      BEFORE anything can be submitted. `up` on a cancelled voice pointer returns
 *      `submit: false`, and `submits` never counts it. The 11 September timeline holds 18
 *      `multitouch` hold phases and two GESTURE_COLLISION turns; this is the invariant those
 *      were about.
 *   5. Voice activates ONLY from a deliberate voice target — `hit.voice` true, set by the page
 *      from `#talk`/`#orb-frame` and nothing else.
 *
 * And the geometry half, §8: `covering()` is the documented layering RULE as arithmetic — no
 * layer may visually cover another INTERACTIVE layer without intentionally disabling it. The
 * layer order it enforces is the one written into web/style.css:
 *
 *   content → workspace actions → navigation chrome → branch chrome → voice → emergency
 *
 * Two halves, deliberately, exactly as web/collide.js is built: everything here is arithmetic
 * over plain values and runs under Node (tests/web/touch.test.js), and the page supplies the
 * DOM facts. Nothing in this file reads the DOM, and nothing in it reads a word of content.
 */
(function (root) {
  'use strict';

  const OWNER = {
    CONTROL: 'CONTROL',
    SCROLL: 'SCROLL',
    VOICE: 'VOICE',
    SPLIT: 'SPLIT_GESTURE',
    APPROVAL: 'APPROVAL_GESTURE',
    NONE: 'NONE',
  };
  const OWNERS = [OWNER.CONTROL, OWNER.SCROLL, OWNER.VOICE, OWNER.SPLIT, OWNER.APPROVAL, OWNER.NONE];

  // The owners that can never, under any circumstance, submit a recording.
  const NEVER_VOICE = [OWNER.CONTROL, OWNER.SCROLL, OWNER.APPROVAL, OWNER.SPLIT, OWNER.NONE];

  const SPLIT_TRAVEL = 70;    // CSS px of change in separation; about 9mm on the Tab A
  const TOL = 2;              // px of overlap in BOTH axes before two rectangles count

  /* Everything a finger presses, as one selector. The page passes the match in; this is here
     so the page and the tests agree on the list. `#talk` and `#orb-frame` are deliberately
     absent: they ARE the voice target, and matching them as controls would make voice
     impossible rather than deliberate. */
  const CONTROL_SELECTOR = [
    'button:not(#talk)', '[role="button"]', '[role="tab"]', 'a[href]', 'input', 'select', 'textarea',
    'summary', 'label', '[data-action]', '[data-command]', '[data-ask]', '[data-offer]',
    '.row.tappable', '.link-strip', '.variant-row', '.ws-opt', '.chip', '.dock-btn',
    '.branch-chip', '.branch-act', '.rail-chip', '.note-dismiss', '.note-close',
  ].join(',');

  // An action surface owns its own drag (the approval gesture); it is not a plain control.
  const APPROVAL_SELECTOR = '.action-surface,.action-handle';

  /* The layer ladder, named. The numbers are the paint order in web/style.css and the
     comparison `covering()` makes; they are NOT z-index values, which the stylesheet owns. */
  const LAYERS = {
    content: 1,        // the orb, the deck, the cards
    actions: 2,        // workspace-local actions: the nav rail, the action surfaces
    nav: 3,            // navigation chrome: the wordmark row, the footer, the dock
    branch: 4,         // branch chrome: Split, the two halves, Merge, Close
    voice: 5,          // the voice target, and only the voice target
    overlay: 6,        // emergency overlays: the settings sheet, the system layer
  };

  // ---- the arithmetic ------------------------------------------------------------------

  function rectOf(box) {
    if (!box) return null;
    const left = Number(box.left !== undefined ? box.left : box.x) || 0;
    const top = Number(box.top !== undefined ? box.top : box.y) || 0;
    const width = Number(box.width !== undefined ? box.width : (box.right || 0) - left) || 0;
    const height = Number(box.height !== undefined ? box.height : (box.bottom || 0) - top) || 0;
    return { left, top, width, height, right: left + width, bottom: top + height };
  }

  /* Do two rectangles share more than a hair of space, in BOTH axes? Two controls that share
     an edge are side by side, not on top of each other. */
  function overlaps(a, b, tol) {
    const one = rectOf(a);
    const two = rectOf(b);
    if (!one || !two) return null;
    const slack = tol === undefined ? TOL : tol;
    const w = Math.min(one.right, two.right) - Math.max(one.left, two.left);
    const h = Math.min(one.bottom, two.bottom) - Math.max(one.top, two.top);
    if (w <= slack || h <= slack) return null;
    return { w: Math.round(w), h: Math.round(h) };
  }

  // One rectangle wholly inside another: a handle inside its surface, a label inside its
  // button. That is how a control is built, not a fault.
  function contains(outer, inner) {
    const a = rectOf(outer);
    const b = rectOf(inner);
    if (!a || !b) return false;
    return a.left <= b.left + TOL && a.top <= b.top + TOL
      && a.right >= b.right - TOL && a.bottom >= b.bottom - TOL;
  }

  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

  /* §8's RULE, as arithmetic. A zone is `{ name, layer, interactive, disabled, rect }`.
   *
   * A pair is a fault when a HIGHER layer's zone overlaps a LOWER layer's INTERACTIVE zone
   * and that lower zone is not deliberately switched off. Two zones on the SAME layer are the
   * stylesheet's business (and web/collide.js's), not this rule's: this rule is about one
   * layer eating another. `zones` is the page's list of top-level interaction REGIONS, one
   * per layer per area, not every node in the tree — a button inside its own nav bar is not
   * two zones, and `within` marks a zone the caller knows to be nested inside another.
   */
  function covering(zones) {
    const list = (zones || []).filter((z) => z && z.rect);
    const faults = [];
    for (let i = 0; i < list.length; i++) {
      for (let j = 0; j < list.length; j++) {
        if (i === j) continue;
        const over = list[i];
        const under = list[j];
        const above = (LAYERS[over.layer] || 0) - (LAYERS[under.layer] || 0);
        if (above <= 0) continue;                       // same layer, or underneath: not this rule
        if (!under.interactive) continue;               // words and ground may be covered
        if (under.disabled) continue;                   // covered ON PURPOSE, and said so
        if (under.within === over.name || over.within === under.name) continue;   // nested, by the caller's own word
        const hit = overlaps(over.rect, under.rect);
        if (!hit) continue;
        faults.push({ over: over.name, overLayer: over.layer, under: under.name,
                      underLayer: under.layer, w: hit.w, h: hit.h });
      }
    }
    return faults;
  }

  // ---- the machine ---------------------------------------------------------------------

  /* What the finger landed on, as the page reads it:
   *   { pointerId, x, y, voice, control, scroll, approval, button }
   * `control` and `approval` are selectors (or any truthy string) naming what was hit;
   * `voice` and `scroll` are booleans. Nothing here is inferred from a rectangle: the page
   * asks the DOM what is under the finger, which is the only reliable answer. */
  function classify(hit) {
    if (!hit) return OWNER.NONE;
    if (hit.approval) return OWNER.APPROVAL;
    // Rule 2. Before voice, always: this is the line that makes D-1 impossible to reintroduce
    // by a stylesheet change.
    if (hit.control) return OWNER.CONTROL;
    // Rule 3.
    if (hit.scroll) return OWNER.SCROLL;
    // Rule 5. A deliberate voice target, and nothing else, can be voice.
    if (hit.voice) return OWNER.VOICE;
    return OWNER.NONE;
  }

  function create(opts) {
    const options = opts || {};
    const travel = Number(options.splitTravel) || SPLIT_TRAVEL;
    const clock = options.now || (() => Date.now());
    const onCancelVoice = typeof options.onCancelVoice === 'function' ? options.onCancelVoice : null;
    const onOwner = typeof options.onOwner === 'function' ? options.onOwner : null;

    const points = new Map();      // pointerId -> { owner, x, y, at, cancelled, why }
    const tally = { downs: 0, submits: 0, cancels: 0, pairs: 0, byOwner: {} };
    let pair = null;               // { ids: [a, b], from, fired }

    const held = () => Array.from(points.values());
    const voicePointer = () => held().find((p) => p.owner === OWNER.VOICE && !p.cancelled) || null;

    // Everything that is or could still become a voice interaction, cancelled at once, and
    // cancelled BEFORE the caller is told a pair has formed — so nothing can be submitted in
    // between. Rule 4.
    function cancelPendingVoice(why) {
      let cancelled = 0;
      for (const point of points.values()) {
        if (point.owner !== OWNER.VOICE || point.cancelled) continue;
        point.cancelled = true;
        point.why = why;
        cancelled += 1;
        tally.cancels += 1;
      }
      if (cancelled && onCancelVoice) onCancelVoice(why);
      return cancelled;
    }

    /* A finger goes down. Idempotent per pointer id: the second caller gets the same claim
     * back with `first: false` and nothing happens twice. */
    function down(hit) {
      const id = hit && hit.pointerId !== undefined ? hit.pointerId : 1;
      const existing = points.get(id);
      if (existing) {
        return { owner: existing.owner, pointerId: id, first: false, voice: false,
                 cancelledVoice: false, pairing: Boolean(pair && pair.ids.indexOf(id) >= 0) };
      }
      if (hit && hit.button !== undefined && hit.button !== null && hit.button !== 0) {
        return { owner: OWNER.NONE, pointerId: id, first: false, voice: false,
                 cancelledVoice: false, pairing: false, ignored: 'not the primary button' };
      }
      let owner = classify(hit);
      const x = Number(hit && hit.x) || 0;
      const y = Number(hit && hit.y) || 0;
      let cancelledVoice = false;

      // A second finger on a gesture-capable surface makes a pair, and a third joining them
      // joins the pair rather than starting a question of its own. Only VOICE-classified
      // pointers pair: a finger on a control is a control, and a finger on a card is a
      // scroll, whatever else is on the glass.
      const partnerId = firstPairable();
      const partner = partnerId === null ? null : points.get(partnerId);
      const pairable = owner === OWNER.VOICE && Boolean(partner);
      if (pairable) {
        // Cancelled FIRST, before the caller is even told a pair exists, so there is no
        // window in which a release could submit. Rule 4.
        cancelledVoice = cancelPendingVoice('multitouch') > 0;
        owner = OWNER.SPLIT;
        partner.owner = OWNER.SPLIT;
        points.set(id, { owner, x, y, at: clock(), cancelled: false, why: '', id });
        if (pair) pair.ids.push(id);
        else { pair = { ids: [partnerId, id], from: 0, fired: false }; tally.pairs += 1; }
        pair.from = spread();
        tally.downs += 1;
        tally.byOwner[owner] = (tally.byOwner[owner] || 0) + 1;
        if (onOwner) onOwner({ pointerId: id, owner, hit });
        return { owner, pointerId: id, first: true, voice: false, cancelledVoice, pairing: true };
      }

      points.set(id, { owner, x, y, at: clock(), cancelled: false, why: '', id });
      tally.downs += 1;
      tally.byOwner[owner] = (tally.byOwner[owner] || 0) + 1;
      if (onOwner) onOwner({ pointerId: id, owner, hit });
      return { owner, pointerId: id, first: true, voice: owner === OWNER.VOICE,
               cancelledVoice: false, pairing: false };
    }

    /* The finger this one can make a pair with: any pointer already down that is itself a
       voice hold or already part of the pair. A hand resting three fingers on the orb is one
       gesture, not one gesture and a question — the third finger used to lift and send. */
    function firstPairable() {
      for (const [id, point] of points) {
        if (point.owner === OWNER.VOICE || point.owner === OWNER.SPLIT) return id;
      }
      return null;
    }

    function spread() {
      const pts = held().filter((p) => p.owner === OWNER.SPLIT);
      if (pts.length < 2) return 0;
      return distance(pts[0], pts[1]);
    }

    /* A finger moves. Only a pair is measured, and only once per pair: the intent is reported
     * as a word and the page decides what it means for the branches it has. */
    function move(at) {
      const id = at && at.pointerId !== undefined ? at.pointerId : 1;
      const point = points.get(id);
      if (!point) return null;
      point.x = Number(at.x) || 0;
      point.y = Number(at.y) || 0;
      if (!pair || pair.fired || point.owner !== OWNER.SPLIT) return null;
      const now = spread();
      if (!now) return null;
      const moved = now - pair.from;
      if (moved > travel) { pair.fired = true; return { owner: point.owner, gesture: 'spread', travel: Math.round(moved) }; }
      if (moved < -travel) { pair.fired = true; return { owner: point.owner, gesture: 'pinch', travel: Math.round(moved) }; }
      return null;
    }

    /* A finger lifts. The one answer the whole file exists to get right: `submit` is true for
     * exactly one case — a VOICE pointer that was never cancelled, lifting normally. */
    function up(at) {
      const id = at && at.pointerId !== undefined ? at.pointerId : 1;
      const point = points.get(id);
      if (!point) return null;
      points.delete(id);
      const cancelled = Boolean(at && at.cancelled);
      const wasPaired = Boolean(pair && pair.ids.indexOf(id) >= 0);
      if (points.size === 0) pair = null;
      const submit = point.owner === OWNER.VOICE && !point.cancelled && !cancelled;
      if (submit) tally.submits += 1;
      return {
        owner: point.owner, pointerId: id, submit,
        discard: point.owner === OWNER.VOICE ? !submit : false,
        why: point.cancelled ? point.why : (cancelled ? 'pointercancel' : ''),
        paired: wasPaired, remaining: points.size,
        ms: Math.max(0, Math.round(clock() - point.at)),
      };
    }

    // Everything down, dropped, submitting nothing. For a mode change, a reset, a blur.
    function clear(why) {
      const dropped = Array.from(points.keys());
      cancelPendingVoice(why || 'cleared');
      points.clear();
      pair = null;
      return dropped;
    }

    return {
      OWNER, OWNERS, NEVER_VOICE, classify,
      down, move, up, clear, cancelPendingVoice,
      owner: (id) => { const p = points.get(id === undefined ? 1 : id); return p ? p.owner : ''; },
      cancelled: (id) => { const p = points.get(id === undefined ? 1 : id); return Boolean(p && p.cancelled); },
      voicePending: () => Boolean(voicePointer()),
      pairing: () => Boolean(pair),
      count: () => points.size,
      audit: () => ({ downs: tally.downs, submits: tally.submits, cancels: tally.cancels,
                      pairs: tally.pairs, byOwner: Object.assign({}, tally.byOwner),
                      down_now: points.size }),
    };
  }

  const api = {
    OWNER, OWNERS, NEVER_VOICE, LAYERS, SPLIT_TRAVEL, TOL,
    CONTROL_SELECTOR, APPROVAL_SELECTOR,
    classify, create, covering, overlaps, contains, rectOf,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CrooksTouch = api;
})(typeof window !== 'undefined' ? window : globalThis);
