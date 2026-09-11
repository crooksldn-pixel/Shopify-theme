/* The geometry rules (web/collide.js), under Node.
 *
 * `check(records)` is arithmetic over plain rectangles, so every rule can be stated as a
 * picture of a screen and asserted without a browser. What is checked here is the rules
 * themselves: that they fire on the shapes the live session produced, and — just as
 * important — that they do NOT fire on the shapes that are correct, because a collision
 * report full of false positives is worth exactly as much as `clipped=0`.
 *
 * The browser half is scripts/browser/collision.js, which measures the real page at
 * 601 × 889 and 800 × 1280. This file is the arithmetic underneath it.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const C = require(path.join(__dirname, '..', '..', 'web', 'collide.js'));

const VIEW = { w: 601, h: 889 };

// A record, as `collect` builds them: a selector, a path in the tree, what kinds it is, and
// a rectangle. `at(x, y, w, h)` is the rectangle in the form a person can read.
function rec(sel, path, kinds, x, y, w, h, extra) {
  return Object.assign({
    sel, path, kinds, shown: true, decorative: false,
    rect: { left: x, top: y, right: x + w, bottom: y + h, width: w, height: h },
    asked: { width: w, height: h },
    covered_by: '',
  }, extra || {});
}

const fired = (result, rule) => result.counts[rule] || 0;

test('two controls in the same place is a collision; one inside the other is not', () => {
  const apart = C.check([
    rec('button.a', '/0/0', ['control'], 10, 100, 120, 48),
    rec('button.b', '/0/1', ['control'], 150, 100, 120, 48),
  ], { viewport: VIEW });
  assert.equal(fired(apart, 'control_over_control'), 0, 'two controls side by side');

  const over = C.check([
    rec('button.a', '/0/0', ['control'], 10, 100, 120, 48),
    rec('button.b', '/0/1', ['control'], 100, 120, 120, 48),
  ], { viewport: VIEW });
  assert.equal(fired(over, 'control_over_control'), 1);
  assert.equal(over.hits[0].a, 'button.a');
  assert.equal(over.hits[0].b, 'button.b');
  assert.deepEqual([over.hits[0].w, over.hits[0].h], [30, 28]);
  assert.ok(/10,100 120x48/.test(over.hits[0].at), `the hit carries the boxes: ${over.hits[0].at}`);

  // A stepper's buttons live inside the stepper, and an action surface contains its own
  // handle. Nesting is how a control is built, not a fault.
  const nested = C.check([
    rec('div.action-surface', '/0/0', ['control'], 10, 100, 400, 64),
    rec('div.action-handle', '/0/0/1', ['control'], 16, 106, 56, 52),
  ], { viewport: VIEW });
  assert.equal(fired(nested, 'control_over_control'), 0, 'a control inside a control');
});

test('a one-pixel touch of two boxes is not a collision, and three pixels is', () => {
  const kiss = C.check([
    rec('button.a', '/0/0', ['control'], 0, 0, 100, 44),
    rec('button.b', '/0/1', ['control'], 99, 43, 100, 44),
  ], { viewport: VIEW });
  assert.equal(fired(kiss, 'control_over_control'), 0, 'boxes that share an edge');
  const real = C.check([
    rec('button.a', '/0/0', ['control'], 0, 0, 100, 44),
    rec('button.b', '/0/1', ['control'], 96, 40, 100, 44),
  ], { viewport: VIEW });
  assert.equal(fired(real, 'control_over_control'), 1);
});

test('words printed across a control fire; a control\'s own label does not', () => {
  const label = C.check([
    rec('button.chip', '/0/0', ['control'], 10, 10, 120, 44),
    rec('span.chip-label', '/0/0/0', ['text'], 20, 22, 100, 20),
  ], { viewport: VIEW });
  assert.equal(fired(label, 'text_over_control'), 0, 'the label inside its own button');

  const across = C.check([
    rec('button.chip', '/0/0', ['control'], 10, 10, 120, 44),
    rec('p.card-sub', '/0/1', ['text'], 40, 30, 300, 20),
  ], { viewport: VIEW });
  assert.equal(fired(across, 'text_over_control'), 1);
});

test('the floating bubble the live session used is a collision, wherever it floats', () => {
  // 11 September, 00:24:53: "Merged. 2 changes still waiting over there." — a fixed bubble
  // 120px up from the bottom of a 889px screen, and the dock band underneath it. This is the
  // shape that rule exists for, and it fires whether the bubble is over the dock, over the
  // halves or over the orb.
  const dock = rec('button.dock-btn', '/9/0', ['chrome'], 57, 777, 64, 56);
  const halves = rec('button.branch-chip', '/2/3', ['chrome'], 120, 720, 160, 44);
  const orb = rec('div#orb-frame.orb-frame', '/1/0', ['chrome'], 130, 90, 340, 340);

  const bubble = rec('p#toast.toast', '/3', ['notification', 'text'], 40, 745, 520, 44);
  const over = C.check([dock, halves, orb, bubble], { viewport: VIEW });
  assert.equal(fired(over, 'notification_over_chrome'), 2, 'the dock and the halves, both');

  const onOrb = C.check([dock, halves, orb, rec('p#toast.toast', '/3', ['notification'], 40, 200, 520, 44)], { viewport: VIEW });
  assert.equal(fired(onOrb, 'notification_over_chrome'), 1, 'over the orb');

  // In flow above the deck — the three classes of web/notify.js — it touches none of them.
  const inFlow = C.check([dock, halves, orb, rec('p.note', '/2/4', ['notification'], 14, 470, 573, 44)], { viewport: VIEW });
  assert.equal(fired(inFlow, 'notification_over_chrome'), 0);
});

test('a message drawn inside the composer belongs to it and is not a collision', () => {
  const field = rec('input.field-input', '/2/5/0/1', ['chrome', 'control', 'essential'], 33, 300, 535, 48);
  const onIt = rec('p.note', '/2/5/0/1/0', ['notification'], 35, 306, 400, 40);
  assert.equal(fired(C.check([field, onIt], { viewport: VIEW }), 'notification_over_chrome'), 0);
});

test('an action rail over content fires; a rail below its content does not', () => {
  const rail = rec('div.rail', '/2/0/3', ['rail'], 33, 400, 535, 60);
  const below = rec('p.card-body', '/2/0/2', ['text'], 33, 320, 535, 60);
  assert.equal(fired(C.check([rail, below], { viewport: VIEW }), 'rail_over_content'), 0);
  const under = rec('p.card-body', '/2/0/2', ['text'], 33, 430, 535, 60);
  assert.equal(fired(C.check([rail, under], { viewport: VIEW }), 'rail_over_content'), 1);
});

test('a page that scrolls sideways is reported with the numbers', () => {
  const ok = C.check([], { viewport: VIEW, document: { scroll_width: 601, client_width: 601 } });
  assert.equal(fired(ok, 'document_overflow_x'), 0);
  const bad = C.check([], { viewport: VIEW, document: { scroll_width: 742, client_width: 601 } });
  assert.equal(fired(bad, 'document_overflow_x'), 1);
  assert.equal(bad.hits[0].note, '742 > 601');
});

test('a control folded away to nothing is reported, and a scrolled-off one is not', () => {
  const zero = C.check([rec('button.action', '/2/0/4', ['control'], 33, 300, 0, 44)], { viewport: VIEW });
  assert.equal(fired(zero, 'folded_action'), 1);
  assert.equal(zero.hits[0].note, 'zero size');

  const sliver = C.check([rec('button.action', '/2/0/4', ['control'], 33, 300, 4, 44)], { viewport: VIEW });
  assert.equal(fired(sliver, 'folded_action'), 1);
  assert.equal(sliver.hits[0].note, '4×44');

  // Half out of the deck: the box the layout gave it is fine, and the owner has simply not
  // scrolled to it. `asked` is what the rule reads, which is why it stays quiet.
  const scrolled = rec('button.action', '/2/0/4', ['control'], 33, 336, 200, 6, { asked: { width: 200, height: 48 } });
  assert.equal(fired(C.check([scrolled], { viewport: VIEW }), 'folded_action'), 0);
});

test('something the browser found another element on top of is reported', () => {
  const buried = rec('h2.card-title', '/2/0/0/0/1', ['essential', 'text'], 33, 800, 400, 30, { covered_by: 'button#talk.talk' });
  const result = C.check([buried], { viewport: VIEW });
  assert.equal(fired(result, 'content_under_chrome'), 1);
  assert.equal(result.hits[0].note, 'button#talk.talk');
});

test('nothing off screen or hidden is measured at all', () => {
  const off = C.check([
    rec('button.a', '/0/0', ['control'], -400, 100, 120, 48),
    rec('button.b', '/0/1', ['control'], -380, 110, 120, 48),
  ], { viewport: VIEW });
  assert.equal(off.total, 0, 'two controls that collide off the left of the screen');

  const hidden = C.check([
    rec('button.a', '/0/0', ['control'], 10, 100, 120, 48, { shown: false }),
    rec('button.b', '/0/1', ['control'], 20, 110, 120, 48, { shown: false }),
  ], { viewport: VIEW });
  assert.equal(hidden.total, 0);
});

test('every rule that fired keeps an example, however long the tail', () => {
  const many = [];
  for (let i = 0; i < 40; i++) many.push(rec(`button.n${i}`, `/0/${i}`, ['control'], 10, 100, 200, 48));
  many.push(rec('p.late', '/9', ['text'], 10, 100, 200, 48));
  const result = C.check(many, { viewport: VIEW, document: { scroll_width: 900, client_width: 601 } });
  assert.ok(result.total > 24, `a screen this bad has many hits: ${result.total}`);
  assert.ok(result.hits.length <= 24, 'and the report is bounded');
  for (const rule of ['control_over_control', 'text_over_control', 'document_overflow_x']) {
    assert.ok(result.hits.some((h) => h.rule === rule), `${rule} kept an example`);
  }
});

test('the thumb floor is measured on the box the layout gave, not on what is scrolled into view', () => {
  const small = C.touch([
    rec('button.row-btn', '/2/0/1', ['control'], 400, 200, 61, 34),
    rec('button.chip', '/2/1/0', ['control'], 14, 60, 120, 44),
    rec('span.badge', '/2/0/2', ['control'], 14, 20, 80, 26, { decorative: true }),
  ], { viewport: VIEW });
  assert.deepEqual(small, [{ sel: 'button.row-btn', w: 61, h: 34 }]);
  const halfScrolled = C.touch([
    rec('button.chip', '/2/1/0', ['control'], 14, 880, 120, 9, { asked: { width: 120, height: 44 } }),
  ], { viewport: VIEW });
  assert.deepEqual(halfScrolled, [], 'a control half out of the deck is not a small control');
});

// --------------------------------------------------------------------- the collector

/* A document just real enough to walk: tags, classes, children, rectangles and a computed
   style handed in. What is being tested is the clip — the reason the first run of the
   collision suite reported every tall card as colliding with the dock, when the card was
   simply scrolled and the part in the dock band was not drawn at all. */
function node(tag, cls, box, style, kids) {
  const el = {
    nodeType: 1, tagName: tag, className: cls || '', id: '', hidden: false,
    children: kids || [], childNodes: kids || [],
    _style: Object.assign({ display: 'block', position: 'static', overflowX: 'visible', overflowY: 'visible' }, style || {}),
    getBoundingClientRect: () => ({ left: box[0], top: box[1], width: box[2], height: box[3], right: box[0] + box[2], bottom: box[1] + box[3] }),
    getAttribute: () => null,
    matches(selector) {
      const wanted = String(selector).split(',').map((x) => x.trim());
      const classes = String(this.className).split(/\s+/).filter(Boolean);
      return wanted.some((w) => {
        // `button:not(#talk)` is in the real selector list, so the stand-in understands it.
        const not = w.match(/^(.*):not\(#([\w-]+)\)$/);
        if (not) return this.matches(not[1]) && this.id !== not[2];
        if (w.charAt(0) === '.') return classes.indexOf(w.slice(1)) !== -1;
        if (w.charAt(0) === '#') return this.id === w.slice(1);
        if (/^[a-z]+$/i.test(w)) return w.toLowerCase() === String(this.tagName).toLowerCase();
        return false;   // attribute selectors: not what this stand-in is for
      });
    },
    contains(other) { return other === this; },
  };
  return el;
}

test('a card scrolled past the bottom of the deck is measured as the part that is drawn', () => {
  // The deck is 174..342 and clips; the card inside it runs 161..804, which is a real
  // rectangle and mostly not on the screen. The dock band is 342..418.
  const button = node('BUTTON', 'action-surface', [33, 500, 535, 48]);
  const card = node('ARTICLE', 'card', [33, 161, 535, 643], { overflowX: 'hidden', overflowY: 'hidden' }, [button]);
  const cards = node('DIV', 'cards', [14, 174, 573, 168], { overflowX: 'auto', overflowY: 'auto', position: 'relative' }, [card]);
  const dockBtn = node('BUTTON', 'dock-btn', [57, 356, 64, 48]);
  const dock = node('NAV', 'dock', [0, 342, 601, 76], { position: 'fixed' }, [dockBtn]);
  const body = node('BODY', '', [0, 0, 601, 418], { overflowX: 'hidden', overflowY: 'hidden' }, [cards, dock]);

  const records = C.collect({ body }, { root: body, viewport: { w: 601, h: 418 }, styleOf: (n) => n._style });
  const surface = records.find((r) => r.sel === 'button.action-surface');
  assert.ok(surface, 'the surface was collected');
  assert.equal(surface.shown, false, 'and it is not drawn at all: the deck clipped it away');
  assert.deepEqual(surface.asked, { width: 535, height: 48 }, 'its own box is still recorded');

  // The dock is fixed, so the deck's clip does not apply to it: its rectangle is its own.
  const chrome = records.find((r) => r.sel === 'button.dock-btn');
  assert.ok(chrome && chrome.shown);
  assert.deepEqual([chrome.rect.top, chrome.rect.bottom], [356, 404]);

  const result = C.check(records, { viewport: { w: 601, h: 418 } });
  assert.equal(result.total, 0, 'a card scrolled under the dock is not a collision');
});

test('a control the deck really does draw in the dock band is a collision', () => {
  // The same screen, with the deck reaching the bottom of the page the way it did before the
  // section 9 pass: the surface is drawn in the dock's band, and a tap there never reaches it.
  const button = node('BUTTON', 'action-surface', [33, 350, 535, 48]);
  const card = node('ARTICLE', 'card', [33, 161, 535, 643], { overflowX: 'hidden', overflowY: 'hidden' }, [button]);
  const cards = node('DIV', 'cards', [14, 174, 573, 244], { overflowX: 'auto', overflowY: 'auto', position: 'relative' }, [card]);
  const dockBtn = node('BUTTON', 'dock-btn', [57, 356, 64, 48]);
  const dock = node('NAV', 'dock', [0, 342, 601, 76], { position: 'fixed' }, [dockBtn]);
  const body = node('BODY', '', [0, 0, 601, 418], { overflowX: 'hidden', overflowY: 'hidden' }, [cards, dock]);

  const records = C.collect({ body }, { root: body, viewport: { w: 601, h: 418 }, styleOf: (n) => n._style });
  const result = C.check(records, { viewport: { w: 601, h: 418 } });
  assert.equal(fired(result, 'control_over_control'), 1, JSON.stringify(result.hits));
  assert.equal(result.hits[0].b, 'button.dock-btn');
});

test('a control that cannot be touched is not counted as one', () => {
  const ghost = node('BUTTON', 'talk', [0, 342, 601, 76], { position: 'fixed', pointerEvents: 'none' });
  const dockBtn = node('BUTTON', 'dock-btn', [57, 356, 64, 48]);
  const body = node('BODY', '', [0, 0, 601, 418], {}, [ghost, dockBtn]);
  const records = C.collect({ body }, { root: body, viewport: { w: 601, h: 418 }, styleOf: (n) => n._style });
  const result = C.check(records, { viewport: { w: 601, h: 418 } });
  assert.equal(fired(result, 'control_over_control'), 0);
});

test('scan says nothing rather than throwing when there is no document to read', () => {
  const empty = C.scan({ document: null });
  assert.equal(empty.total, 0);
  assert.deepEqual(empty.hits, []);
});
