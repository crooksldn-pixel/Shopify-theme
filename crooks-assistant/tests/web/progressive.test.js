/* Patching in place, under Node (§7, §25 — D-5 and D-13).
 *
 * The Mac now stages the workspace in pieces: a skeleton, then each read's cards as it lands,
 * then the turn's own presentation reconciled against what is already on the glass
 * (app/progressive.py). This file holds the five rules the glass has to keep while that
 * happens, each one a defect the live session would otherwise repeat:
 *
 *   1. an enrichment does not redraw the page — only the card the patch names moves;
 *   2. a control is not moved while the owner is touching it;
 *   3. keyboard focus, the typed characters and the caret survive;
 *   4. the scroll position is not reset;
 *   5. no flicker, no duplicate card, no repeated identical render.
 *
 * The renderer is exercised against the small DOM stand-in in dom-shim.js, which has no
 * layout — so what is asserted here is IDENTITY and STATE: which nodes survived, which were
 * replaced, what the scroller and the keyboard were left holding. Height is measured in a
 * real browser at 601 × 889 instead (scripts/browser/density.js).
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
globalThis.document = shim.document;
const UI = require(path.join(__dirname, '..', '..', 'web', 'ui.js'));

const ORDER = { order_id: 'gid://shopify/Order/1', order_number: '#1938', detail: true, total: '£84.00' };

function deck() {
  const host = shim.document.createElement('div');
  host.scrollTop = 0;
  return host;
}

function patch(op, item, extra) {
  return Object.assign({ id: UI.surfaceId(item), op, type: item.type, item }, extra || {});
}

function shell(kind) {
  return { type: kind, data: { shell: true, loading: true, title: 'Orders', placeholder: 3 } };
}

// --------------------------------------------------------------------- the shell

test('a shell is drawn for any card that says it is one, and says no values', () => {
  const node = UI.renderItem(shell('order_list'), {});
  assert.equal(node.dataset.type, 'order_list');
  assert.equal(node.dataset.shell, '1');
  assert.equal(node.getAttribute('aria-busy'), 'true');
  assert.equal(node.querySelectorAll('.sk-row').length, 3);
  // A placeholder must never look like a value: no digits, no money, no names.
  assert.match(node.allText(), /Reading/);
  assert.ok(!/£|\d{2,}/.test(node.allText()), node.allText());
});

test('the real card takes the shell\'s place rather than appearing below it', () => {
  const host = deck();
  UI.applyPatches(host, [patch('add', shell('order_list'))]);
  assert.equal(host.children.length, 1);
  const list = { type: 'order_list', data: { title: 'Today', count: 1, orders: [{ order_id: 'g1', order_number: '#1938' }] } };
  const out = UI.applyPatches(host, [patch('add', list, { replaces: 'order_list:~shell' })]);
  assert.equal(host.children.length, 1, 'one card, not a skeleton and a list');
  assert.equal(host.children[0].dataset.shell, undefined);
  assert.match(host.children[0].allText(), /#1938/);
  assert.equal(out.added, 1);
});

// --------------------------------------------------------------------- rule 1

test('an enrichment moves one card and leaves every other node alone', () => {
  const host = deck();
  const order = { type: 'order', data: ORDER };
  const mail = { type: 'email_list', data: { title: 'Email', count: 1, threads: [{ thread_id: 't1', subject: 'Hi' }] } };
  UI.applyPatches(host, [patch('add', order), patch('add', mail)]);
  const [before, kept] = host.children;
  const enriched = { type: 'order', data: Object.assign({}, ORDER, { history: { orders: 4, spent: '£410.00' } }) };
  const out = UI.applyPatches(host, [patch('data', enriched)]);
  assert.equal(out.changed, 1);
  assert.equal(host.children.length, 2);
  assert.notEqual(host.children[0], before, 'the order card was rebuilt');
  assert.equal(host.children[1], kept, 'the card beside it is the same node it was');
  assert.equal(host.children[0].dataset.render, UI.surfaceId(order), 'and it kept its identity');
});

test('a visual-state patch keeps the node itself', () => {
  const host = deck();
  const order = { type: 'order', data: Object.assign({}, ORDER, { pending: ['history', 'email'] }) };
  UI.applyPatches(host, [patch('add', order)]);
  const node = host.children[0];
  const out = UI.applyPatches(host, [patch('visual', { type: 'order', data: Object.assign({}, ORDER, { pending: [] }) })]);
  assert.equal(out.visual, 1);
  assert.equal(host.children[0], node, 'the same DOM node: nothing was rebuilt');
  assert.equal(node.dataset.pending, '');
});

// --------------------------------------------------------------------- rule 2

test('nothing is patched while a finger is on the glass, and it lands when the hand is off', () => {
  const host = deck();
  UI.applyPatches(host, [patch('add', { type: 'order', data: ORDER })]);
  const node = host.children[0];
  let touching = true;
  const enriched = { type: 'order', data: Object.assign({}, ORDER, { note: 'he called' }) };
  const held = UI.applyPatches(host, [patch('data', enriched)], { held: () => touching });
  assert.equal(held.deferred, 1);
  assert.equal(held.changed, 0);
  assert.equal(host.children[0], node, 'the card under the finger did not move');
  touching = false;
  const landed = UI.applyPatches(host, [patch('data', enriched)], { held: () => touching });
  assert.equal(landed.changed, 1);
  assert.notEqual(host.children[0], node);
});

// --------------------------------------------------------------------- rule 3

test('a half-typed address keeps the keyboard, the characters and the caret', () => {
  const host = deck();
  const composer = {
    type: 'email_compose',
    data: {
      compose_id: 'c1', kind: 'new', about: 'A reply',
      to: { value: '', status: 'ok' }, subject: { value: 'Return address', status: 'ok' },
      body: { value: 'Unit 4', status: 'uncertain' }, actions: [],
    },
  };
  UI.applyPatches(host, [patch('add', composer)]);
  // The LABEL and the control both carry data-field; the one the keyboard is in is the
  // control, so that is the one the test types into.
  const boxes = host.querySelectorAll('[data-field="body"]').filter((n) => n.tagName === 'TEXTAREA' || n.tagName === 'INPUT');
  const box = boxes[0];
  assert.ok(box, 'the composer has a body field');
  box.value = 'Unit 4, Bermondsey Trading Est';
  box.selectionStart = 7;
  box.selectionEnd = 7;
  box.focus();
  assert.equal(shim.document.activeElement, box);

  // The Mac answers with the card again — a perfectly ordinary enrichment — while he types.
  const echoed = JSON.parse(JSON.stringify(composer));
  echoed.data.body.value = 'Unit 4';
  echoed.data.subject.hint = 'read it back to him';
  UI.applyPatches(host, [patch('data', echoed)]);

  const now = host.querySelectorAll('[data-field="body"]').filter((n) => n.tagName === 'TEXTAREA' || n.tagName === 'INPUT')[0];
  assert.notEqual(now, box, 'the card was rebuilt');
  assert.equal(shim.document.activeElement, now, 'the keyboard is still in the same field');
  assert.equal(now.value, 'Unit 4, Bermondsey Trading Est', 'his characters are his');
  assert.equal(now.selectionStart, 7, 'and the caret is where he left it');
});

// --------------------------------------------------------------------- rule 4

test('patching does not touch the scroller', () => {
  const host = deck();
  UI.applyPatches(host, [patch('add', { type: 'order', data: ORDER }), patch('add', { type: 'attention', data: { for: 'gid://shopify/Order/1', items: [{ title: 'Paid, not shipped' }] } })]);
  host.scrollTop = 640;
  UI.applyPatches(host, [patch('data', { type: 'order', data: Object.assign({}, ORDER, { note: 'x' }) })]);
  assert.equal(host.scrollTop, 640, 'the owner was 640 px down and he still is');
});

// --------------------------------------------------------------------- rule 5

test('the same patch twice leaves one card and no flicker', () => {
  const host = deck();
  const order = patch('add', { type: 'order', data: ORDER });
  UI.applyPatches(host, [order]);
  UI.applyPatches(host, [order]);
  assert.equal(host.querySelectorAll('[data-type="order"]').length, 1, 'one card, not two');
  // A replaced card is marked so the CSS does not run the entry animation again: the card
  // sliding in every time an enrichment landed is the flicker the brief forbids.
  assert.equal(host.children[0].dataset.patched, '1');
});

test('two different orders are two cards, and neither is the other', () => {
  const host = deck();
  const one = { type: 'order', data: ORDER };
  const two = { type: 'order', data: { order_id: 'gid://shopify/Order/2', order_number: '#1939', detail: true } };
  UI.applyPatches(host, [patch('add', one), patch('add', two)]);
  assert.equal(host.children.length, 2);
  assert.notEqual(UI.surfaceId(one), UI.surfaceId(two));
});

test('a shell whose read never landed is taken down', () => {
  const host = deck();
  UI.applyPatches(host, [patch('add', shell('email_list'))]);
  const out = UI.applyPatches(host, [{ id: 'email_list:~shell', op: 'remove', type: 'email_list' }]);
  assert.equal(out.removed, 1);
  assert.equal(host.children.length, 0, 'a skeleton is never left reading');
});

test('a patch carrying a type the tablet cannot draw draws nothing and breaks nothing', () => {
  const host = deck();
  const out = UI.applyPatches(host, [{ id: 'hologram:x', op: 'add', type: 'hologram', item: { type: 'hologram', data: { html: '<b>x</b>' } } }]);
  assert.deepEqual([out.added, out.changed, out.visual], [0, 0, 0]);
  assert.equal(host.children.length, 0);
});

// --------------------------------------------------------------------- identity

test('render identity is the record, not the position', () => {
  assert.equal(UI.surfaceId({ type: 'order', data: ORDER }), 'order:gid://shopify/Order/1');
  assert.equal(UI.surfaceId({ type: 'order', data: { order_number: '#1938' } }), 'order:#1938');
  assert.equal(UI.surfaceId({ type: 'email_thread', data: { thread_id: 't1' } }), 'email_thread:t1');
  assert.equal(UI.surfaceId({ type: 'assistant', data: { text: 'hi' } }), 'assistant');
  assert.equal(UI.surfaceId({ type: 'inventory', data: { query: 'hoodie', products: [{ product_id: 'p1' }] } }), 'inventory:p1');
  assert.equal(UI.surfaceId(shell('order_list')), 'order_list:~shell');
});

test('every renderable type has an identity rule or is identified by its kind', () => {
  for (const type of UI.TYPES) {
    const id = UI.surfaceId({ type, data: {} });
    assert.equal(id, type, `${type} with no record must fall back to its kind`);
  }
});
