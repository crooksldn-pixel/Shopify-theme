/* The touch-ownership rules (web/touch.js), under Node.
 *
 * D-1, as arithmetic. The machine is a pure state machine over pointer ids and hit facts, so
 * every rule §7 states can be written here as a picture of a finger going down and asserted
 * without a browser — and, just as important, the rules that must NOT fire are asserted too:
 * a voice hold that is a genuine question has to stay a question.
 *
 * The browser half is scripts/browser/touch.js, which drives real Chromium touches at
 * 601 × 889 and 800 × 1280 and counts what the page posts. This file is the logic underneath
 * it: if the logic is wrong here the browser gate can only tell you that something is.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const T = require(path.join(__dirname, '..', '..', 'web', 'touch.js'));

const VIEW = { w: 601, h: 889 };

// A hit, as the page reads it off the DOM: what was under the finger, named.
const hit = (over) => Object.assign({ pointerId: 1, x: 300, y: 700, button: 0 }, over || {});
const onVoice = (over) => hit(Object.assign({ voice: true }, over || {}));
const onControl = (sel, over) => hit(Object.assign({ control: sel || 'button.branch-act', voice: true }, over || {}));

function at(x, y, w, h) {
  return { left: x, top: y, width: w, height: h, right: x + w, bottom: y + h };
}
const zone = (name, layer, x, y, w, h, extra) =>
  Object.assign({ name, layer, interactive: true, rect: at(x, y, w, h) }, extra || {});

// ------------------------------------------------------------------ the owners

test('the five owners exist, are named, and four of them can never speak', () => {
  assert.deepEqual(T.OWNERS.slice().sort(), [
    'APPROVAL_GESTURE', 'CONTROL', 'NONE', 'SCROLL', 'SPLIT_GESTURE', 'VOICE',
  ]);
  // Every owner but VOICE is on the list that can never submit a recording. This is the whole
  // of D-1 in one assertion: there is no owner that is "sort of" voice.
  assert.deepEqual(T.NEVER_VOICE.slice().sort(),
    T.OWNERS.filter((o) => o !== 'VOICE').slice().sort());
});

test('RULE 1 — a touch beginning on an interactive control can NEVER become voice', () => {
  // The exact shape of D-1: the finger is inside the voice target AND on a branch control.
  // Split, Merge and Close each, because those are the three he hammered 26 times.
  for (const control of ['button.branch-act', 'button.branch-chip', 'button.chip', 'button.dock-btn']) {
    assert.equal(T.classify(onControl(control)), 'CONTROL', control);
  }
  const m = T.create();
  const claim = m.down(onControl('button.branch-act'));
  assert.equal(claim.owner, 'CONTROL');
  assert.equal(claim.voice, false, 'a control tap must not arm the voice');
  const done = m.up({ pointerId: 1 });
  assert.equal(done.owner, 'CONTROL');
  assert.equal(done.submit, false, 'a control tap submitted a recording');
  assert.equal(m.audit().submits, 0);
});

test('RULE 2 — a touch beginning as a scroll can never become voice', () => {
  assert.equal(T.classify(hit({ scroll: true, voice: true })), 'SCROLL');
  const m = T.create();
  // A scroll that starts on a card and travels 300px up: still a scroll on release.
  m.down(hit({ pointerId: 7, scroll: true, voice: true, y: 700 }));
  for (let y = 690; y >= 400; y -= 30) m.move({ pointerId: 7, x: 300, y });
  const done = m.up({ pointerId: 7 });
  assert.equal(done.owner, 'SCROLL');
  assert.equal(done.submit, false);
  assert.equal(m.audit().submits, 0);
});

test('an approval drag is its own owner, and is not voice either', () => {
  assert.equal(T.classify(hit({ approval: '.action-surface', control: 'button', voice: true })), 'APPROVAL_GESTURE');
  const m = T.create();
  m.down(hit({ approval: '.action-surface', voice: true }));
  assert.equal(m.up({ pointerId: 1 }).submit, false);
});

test('RULE 3 — voice activates ONLY from a deliberate voice target', () => {
  assert.equal(T.classify(hit({})), 'NONE', 'nothing under the finger is not a question');
  assert.equal(T.classify(onVoice()), 'VOICE');
  const m = T.create();
  // A finger on the ground between things: no owner, and nothing is recorded.
  assert.equal(m.down(hit({ pointerId: 3 })).owner, 'NONE');
  assert.equal(m.up({ pointerId: 3 }).submit, false);
  // And the real thing, for contrast: this one IS a question.
  assert.equal(m.down(onVoice({ pointerId: 4 })).voice, true);
  assert.equal(m.up({ pointerId: 4 }).submit, true);
  assert.equal(m.audit().submits, 1);
});

test('a genuine one-finger hold is still a question, and its length is reported', () => {
  let clock = 1000;
  const m = T.create({ now: () => clock });
  assert.equal(m.down(onVoice()).voice, true);
  clock += 1400;
  const done = m.up({ pointerId: 1 });
  assert.equal(done.submit, true);
  assert.equal(done.ms, 1400);
  assert.equal(done.owner, 'VOICE');
});

test('a pointercancel discards rather than submits — a stray scroll must not send the room', () => {
  const m = T.create();
  m.down(onVoice());
  const done = m.up({ pointerId: 1, cancelled: true });
  assert.equal(done.submit, false);
  assert.equal(done.discard, true);
  assert.equal(done.why, 'pointercancel');
  assert.equal(m.audit().submits, 0);
});

// ------------------------------------------------------------------ the owner never changes

test('an owner is decided once and never changes, however the finger moves', () => {
  const m = T.create();
  m.down(onControl('button.branch-act', { pointerId: 2, x: 100, y: 100 }));
  assert.equal(m.owner(2), 'CONTROL');
  // Dragged clean across the voice target and back.
  for (const y of [200, 400, 600, 800, 300]) m.move({ pointerId: 2, x: 300, y });
  assert.equal(m.owner(2), 'CONTROL', 'the owner changed under a moving finger');
  assert.equal(m.up({ pointerId: 2 }).submit, false);
});

test('down is idempotent per pointer, so both listeners can ask and only one thing happens', () => {
  // The page asks twice on purpose: once in the document capture listener, which classifies
  // from the deepest node, and once in the voice surface's own handler.
  const seen = [];
  const m = T.create({ onOwner: (o) => seen.push(o.owner) });
  const first = m.down(onVoice({ pointerId: 9 }));
  const again = m.down(onVoice({ pointerId: 9 }));
  assert.equal(first.first, true);
  assert.equal(again.first, false);
  assert.equal(again.owner, 'VOICE');
  assert.deepEqual(seen, ['VOICE'], 'the second ask assigned an owner a second time');
  assert.equal(m.audit().downs, 1);
});

test('a second ask cannot re-classify a pointer the first ask gave to a control', () => {
  const m = T.create();
  m.down(onControl('button.chip', { pointerId: 5 }));
  const again = m.down(onVoice({ pointerId: 5 }));       // the voice surface asks about it
  assert.equal(again.owner, 'CONTROL');
  assert.equal(m.up({ pointerId: 5 }).submit, false);
});

test('a non-primary button is ignored outright', () => {
  const m = T.create();
  const claim = m.down(onVoice({ button: 2 }));
  assert.equal(claim.owner, 'NONE');
  assert.equal(m.count(), 0);
});

// ------------------------------------------------------------------ multitouch

test('RULE 4 — a second finger cancels the pending voice BEFORE anything can be submitted', () => {
  const order = [];
  const m = T.create({ onCancelVoice: (why) => order.push(`cancel:${why}`) });
  m.down(onVoice({ pointerId: 1, x: 240, y: 700 }));
  assert.equal(m.voicePending(), true);
  const second = m.down(onVoice({ pointerId: 2, x: 360, y: 700 }));
  order.push(`paired:${second.owner}`);

  // The cancel is reported BEFORE the caller even learns a pair exists. That ordering is the
  // rule: a page told "a pair formed" first could still flush the recorder.
  assert.deepEqual(order, ['cancel:multitouch', 'paired:SPLIT_GESTURE']);
  assert.equal(second.cancelledVoice, true);
  assert.equal(m.voicePending(), false);
  assert.equal(m.owner(1), 'SPLIT_GESTURE', 'the first finger joined the pair');
  assert.equal(m.pairing(), true);

  // And whichever finger lifts first, nothing is sent. The 11 September timeline holds 18
  // multitouch hold phases; every one of them had a recording open.
  const one = m.up({ pointerId: 2 });
  const two = m.up({ pointerId: 1 });
  assert.equal(one.submit, false);
  assert.equal(two.submit, false);
  assert.equal(m.audit().submits, 0, 'a two-finger gesture submitted a turn');
  assert.equal(m.audit().cancels, 1);
});

test('a pair pulled apart is a spread, pinched together is a pinch, and each fires once', () => {
  const m = T.create({ splitTravel: 70 });
  m.down(onVoice({ pointerId: 1, x: 250, y: 700 }));
  m.down(onVoice({ pointerId: 2, x: 350, y: 700 }));     // 100px apart
  assert.equal(m.move({ pointerId: 2, x: 400, y: 700 }), null, '150px is not travel enough');
  const fired = m.move({ pointerId: 2, x: 480, y: 700 });  // 230px apart: +130
  assert.equal(fired.gesture, 'spread');
  assert.equal(fired.travel, 130);
  assert.equal(m.move({ pointerId: 2, x: 560, y: 700 }), null, 'a pair fired twice');

  const back = T.create({ splitTravel: 70 });
  back.down(onVoice({ pointerId: 1, x: 150, y: 700 }));
  back.down(onVoice({ pointerId: 2, x: 450, y: 700 }));   // 300 apart
  assert.equal(back.move({ pointerId: 2, x: 350, y: 700 }).gesture, 'pinch');
});

test('a finger on a control does NOT pair with a voice hold, and does not disturb it', () => {
  // Two fingers, one of them on the dock's Orders icon. That is a press and a hold, not a
  // gesture: the hold is still the owner's question and the press is still a press.
  const m = T.create();
  m.down(onVoice({ pointerId: 1 }));
  const second = m.down(onControl('button.dock-btn', { pointerId: 2 }));
  assert.equal(second.owner, 'CONTROL');
  assert.equal(second.cancelledVoice, false);
  assert.equal(m.pairing(), false);
  assert.equal(m.owner(1), 'VOICE');
  assert.equal(m.up({ pointerId: 2 }).submit, false);
  assert.equal(m.up({ pointerId: 1 }).submit, true, 'a control press ate the question beside it');
});

test('a third finger joining a pair still submits nothing', () => {
  const m = T.create();
  m.down(onVoice({ pointerId: 1, x: 250, y: 700 }));
  m.down(onVoice({ pointerId: 2, x: 350, y: 700 }));
  m.down(onVoice({ pointerId: 3, x: 300, y: 600 }));
  for (const id of [1, 2, 3]) assert.equal(m.up({ pointerId: id }).submit, false, `finger ${id}`);
  assert.equal(m.audit().submits, 0);
});

test('clear() drops everything down and submits nothing', () => {
  const m = T.create();
  m.down(onVoice({ pointerId: 1 }));
  m.down(onVoice({ pointerId: 2, x: 400 }));
  assert.deepEqual(m.clear('mode change').sort(), [1, 2]);
  assert.equal(m.count(), 0);
  assert.equal(m.up({ pointerId: 1 }), null, 'a cleared pointer still answered for itself');
  assert.equal(m.audit().submits, 0);
});

// ------------------------------------------------------------------ the tap storm, replayed

test("the 11 September burst: 26 taps on branch controls submit nothing", () => {
  // The real thing, from the timeline: 23:08:31–23:08:41, twenty-six consecutive presses,
  // 39–140 ms each, every one of which became a recording. Replayed through the machine as
  // what they were — taps on the Split / Merge / Close chips.
  const lengths = [104, 88, 81, 118, 88, 82, 97, 92, 101, 89, 119, 89,
                   81, 39, 90, 118, 58, 79, 103, 55, 79, 96, 81, 115, 140, 114];
  assert.equal(lengths.length, 26);
  let clock = 0;
  const m = T.create({ now: () => clock });
  const controls = ['button.branch-act', 'button.branch-chip', 'button.branch-act'];
  lengths.forEach((ms, i) => {
    const id = 100 + i;
    m.down(onControl(controls[i % 3], { pointerId: id }));
    clock += ms;
    const done = m.up({ pointerId: id });
    assert.equal(done.owner, 'CONTROL', `tap ${i + 1} was not a control`);
    assert.equal(done.submit, false, `tap ${i + 1} submitted a recording`);
  });
  const audit = m.audit();
  assert.equal(audit.downs, 26);
  assert.equal(audit.submits, 0, 'the evening would have repeated itself');
  assert.equal(audit.byOwner.CONTROL, 26);
  assert.equal(audit.byOwner.VOICE, undefined);
});

// ------------------------------------------------------------------ §8, the layer ladder

test('the layer ladder is the order the stylesheet documents', () => {
  const order = Object.keys(T.LAYERS).sort((a, b) => T.LAYERS[a] - T.LAYERS[b]);
  assert.deepEqual(order, ['content', 'actions', 'nav', 'branch', 'voice', 'overlay']);
  assert.ok(T.LAYERS.voice > T.LAYERS.branch, 'voice paints above the branch chrome');
  assert.ok(T.LAYERS.voice > T.LAYERS.nav, 'voice paints above the navigation chrome');
  assert.ok(T.LAYERS.overlay > T.LAYERS.voice, 'an emergency overlay wins over everything');
});

test('THE RULE — a voice zone over the branch chips is a fault, and it is the fault of 11 September', () => {
  // The screen as it was: the voice target the size of the stage, the branch bar under it.
  const wasBroken = T.covering([
    zone('#talk', 'voice', 0, 50, VIEW.w, 780),
    zone('#branch-bar', 'branch', 120, 520, 360, 58),
    zone('#dock', 'nav', 0, 777, VIEW.w, 112),
  ]);
  const names = wasBroken.map((f) => `${f.over}>${f.under}`).sort();
  assert.deepEqual(names, ['#talk>#branch-bar', '#talk>#dock']);
  assert.equal(wasBroken[0].w, 360, 'the whole chip was underneath it');

  // And as it must be: the voice band stops above the branch band, which stops above the dock.
  const separated = T.covering([
    zone('#talk', 'voice', 0, 50, VIEW.w, 470),
    zone('#branch-bar', 'branch', 120, 530, 360, 58),
    zone('#dock', 'nav', 0, 777, VIEW.w, 112),
  ]);
  assert.deepEqual(separated, [], JSON.stringify(separated));
});

test('a zone may be covered when it is deliberately switched off, and only then', () => {
  const off = T.covering([
    zone('#talk', 'voice', 0, 0, VIEW.w, 400),
    zone('#context-nav', 'actions', 14, 100, 570, 52, { disabled: true }),
  ]);
  assert.deepEqual(off, [], 'a zone switched off on purpose is not a fault');
  const on = T.covering([
    zone('#talk', 'voice', 0, 0, VIEW.w, 400),
    zone('#context-nav', 'actions', 14, 100, 570, 52),
  ]);
  assert.equal(on.length, 1);
});

test('words and ground may be covered; a lower layer cannot cover a higher one', () => {
  assert.deepEqual(T.covering([
    zone('#talk', 'voice', 0, 0, VIEW.w, 400),
    zone('.orb-caption', 'content', 40, 200, 520, 120, { interactive: false }),
  ]), [], 'the caption is words, not a control');
  // The rule is not about listing order: a content zone listed FIRST does not "cover" the
  // voice band above it, and the report says so in one direction only.
  const decked = T.covering([
    zone('#deck', 'content', 0, 0, VIEW.w, 600),
    zone('#talk', 'voice', 0, 500, VIEW.w, 112),
  ]);
  assert.deepEqual(decked.map((f) => `${f.over}>${f.under}`), ['#talk>#deck'],
    'reported once, and in the direction of the covering');

  // And a deck that stops above the voice band — which is what
  // `body[data-mode="context"] .context{padding-bottom:var(--dock)}` is for — is clean.
  assert.deepEqual(T.covering([
    zone('#deck', 'content', 0, 0, VIEW.w, 500),
    zone('#talk', 'voice', 0, 500, VIEW.w, 112),
  ]), []);
});

test('a zone the caller says is nested inside another is not covering it', () => {
  assert.deepEqual(T.covering([
    zone('#dock', 'nav', 0, 777, VIEW.w, 112),
    zone('.dock-btn', 'nav', 20, 800, 64, 56, { within: '#dock' }),
    zone('#talk', 'voice', 175, 777, 252, 112),
  ]).map((f) => `${f.over}>${f.under}`), ['#talk>#dock'],
  'only the cross-layer overlap is reported');
});

test('two rectangles sharing an edge are side by side, not on top of each other', () => {
  assert.equal(T.overlaps(at(0, 0, 100, 48), at(100, 0, 100, 48)), null);
  assert.equal(T.overlaps(at(0, 0, 100, 48), at(101, 0, 100, 48)), null);
  assert.deepEqual(T.overlaps(at(0, 0, 100, 48), at(50, 10, 100, 48)), { w: 50, h: 38 });
  // Both axes, or it is not an overlap: a column beside a row is not a collision.
  assert.equal(T.overlaps(at(0, 0, 100, 48), at(50, 100, 100, 48)), null);
});

test('the control selector names the branch chrome, the dock and the nav chips', () => {
  for (const piece of ['.branch-chip', '.branch-act', '.dock-btn', '.chip', '.rail-chip', '[data-action]']) {
    assert.ok(T.CONTROL_SELECTOR.includes(piece), `${piece} is not in the control selector`);
  }
  // And it must NOT claim the voice target itself, or voice becomes unreachable.
  assert.ok(T.CONTROL_SELECTOR.includes('button:not(#talk)'), 'the voice button is claimed as a control');
  assert.ok(!/#orb-frame/.test(T.CONTROL_SELECTOR), 'the orb is claimed as a control');
});
