/* Progressive disclosure (brief §22), under Node.
 *
 * The physical session recorded compound surfaces taller than the viewport — one over 3,300
 * CSS px — and the measurement at 601 × 889 found the Products landing stacking two full
 * rankings at 1,498 px on an 889 px screen. The Mac marks the second card of a kind
 * `secondary` (app/presentation.py:_merge) and the tablet folds it behind its own title.
 *
 * What must hold: the card inside is COMPLETE (this is disclosure, not truncation), it is
 * hidden until asked for, the header says what is inside, and the control is a real button
 * with a state a screen reader can read.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
globalThis.document = shim.document;
globalThis.document.body = shim.document.createElement('body');
globalThis.document.documentElement = shim.document.createElement('html');
globalThis.innerWidth = 601;
globalThis.innerHeight = 889;
globalThis.devicePixelRatio = 1.33;
const UI = require(path.join(__dirname, '..', '..', 'web', 'ui.js'));

function ranking(title, rows, extra) {
  return {
    type: 'ranking',
    data: Object.assign({ title, rows: rows.map((label, i) => ({ label, units: 10 - i, revenue: 100 - i })), mode: 'units' }, extra || {}),
  };
}

test('a card the Mac did not mark stays open', () => {
  const out = UI.render([ranking('Best sellers', ['Convict Hoodie', 'Tee'])], {});
  assert.equal(out.nodes.length, 1);
  assert.equal(out.nodes[0].dataset.type, 'ranking', 'an only ranking is the answer, not evidence');
});

test('a secondary card is folded, complete, and closed until asked for', () => {
  const out = UI.render([
    ranking('Best sellers', ['Convict Hoodie', 'Tee']),
    ranking('Closest to running out', ['Balaclava', 'Cap'], { secondary: true, mode: 'restock' }),
  ], {});
  assert.equal(out.nodes.length, 2);
  const [first, second] = out.nodes;
  assert.equal(first.dataset.type, 'ranking');
  assert.equal(second.dataset.type, 'folded');
  assert.equal(second.dataset.of, 'ranking', 'the fold says what kind of card it holds');

  const head = second.querySelector('.fold-head');
  const body = second.querySelector('.fold-body');
  assert.ok(head && body);
  assert.equal(head.getAttribute('aria-expanded'), 'false');
  assert.equal(body.hidden, true, 'the second ranking costs no height until it is opened');
  // The header names what is inside, from the card's own title.
  assert.match(head.textContent, /Closest to running out/);
  // The card inside is the whole card: every row is there, nothing truncated.
  const inner = body.querySelector('.card-ranking') || body.querySelector('[data-type="ranking"]');
  assert.ok(inner, 'the folded card holds a real ranking');
  assert.match(inner.textContent, /Balaclava/);
  assert.match(inner.textContent, /Cap/);

  head.dispatch('click');
  assert.equal(head.getAttribute('aria-expanded'), 'true');
  assert.equal(body.hidden, false, 'one tap opens it');
  head.dispatch('click');
  assert.equal(body.hidden, true, 'and another closes it again');
});

test('the fold falls back to words when the card has no title', () => {
  const out = UI.render([
    { type: 'order_list', data: { title: 'Orders', orders: [], count: 0 } },
    { type: 'order_list', data: { orders: [], count: 0, secondary: true } },
  ], {});
  const head = out.nodes[1].querySelector('.fold-head');
  assert.match(head.textContent, /orders/i, 'a card with no title still says what it is');
});

test('a folded card is still counted as context, so the deck knows the screen is not empty', () => {
  const out = UI.render([
    { type: 'order', data: { order_number: '#1938', order_id: 'gid://shopify/Order/1', detail: true } },
    ranking('Best sellers', ['Tee']),
    ranking('Running out', ['Cap'], { secondary: true }),
  ], {});
  assert.equal(out.hasContext, true);
  assert.deepEqual(out.skipped, []);
});
