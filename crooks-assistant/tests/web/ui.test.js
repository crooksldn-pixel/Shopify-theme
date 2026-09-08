/* Renderer tests, run under Node's built-in test runner (node --test tests/web).
 *
 * The renderer is the one place external strings become DOM. These tests hold: only the
 * vocabulary renders; everything else is skipped; every string arrives as text, never markup;
 * and the shapes the backend promises produce the cards the tablet expects.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
globalThis.document = shim.document;
const UI = require(path.join(__dirname, '..', '..', 'web', 'ui.js'));

const HOSTILE = '<img src=x onerror="alert(1)"><script>alert(2)</script>&lt;b&gt;';

function textOf(node) { return node.allText(); }

test('the vocabulary is exactly the presentation layer\'s', () => {
  assert.deepEqual(new Set(UI.TYPES), new Set([
    'assistant', 'order', 'order_list', 'customer', 'customer_list', 'product', 'inventory',
    'sales_summary', 'email_list', 'email_thread', 'email_draft', 'attention', 'confirmation',
    'success', 'error', 'context_stack',
  ]));
});

test('unknown types and malformed items are skipped, and nothing is drawn for them', () => {
  const out = UI.render([
    { type: 'hologram', data: { html: '<b>x</b>' } },
    { type: 'order' },                       // no data
    { type: 'order', data: 'not an object' },
    { type: 'order', data: [1, 2] },
    null, 42, 'order',
    { type: 'assistant', data: { text: 'hello' } },
  ]);
  assert.equal(out.nodes.length, 1);
  assert.equal(out.nodes[0].dataset.type, 'assistant');
  assert.deepEqual(out.skipped, ['hologram', 'order', 'order', 'order', 'invalid', 'invalid', 'invalid']);
  assert.equal(UI.renderItem({ type: 'hologram', data: {} }), null);
  assert.equal(UI.renderItem({ type: 'context_stack', data: {} }), null);
});

test('every string from outside becomes text, never markup', () => {
  const items = [
    { type: 'assistant', data: { text: HOSTILE } },
    { type: 'order', data: { order_number: HOSTILE, customer_name: HOSTILE, customer_email: HOSTILE, fulfillment: HOSTILE, payment: HOSTILE, total: HOSTILE, note: HOSTILE, ships_to: HOSTILE, detail: true, items: [{ title: HOSTILE, variant: HOSTILE, sku: HOSTILE, quantity: 1, total: HOSTILE }], fulfillments: [{ status: HOSTILE, carrier: HOSTILE, number: HOSTILE }] } },
    { type: 'customer', data: { name: HOSTILE, email: HOSTILE, orders: 1, spent: HOSTILE } },
    { type: 'product', data: { products: [{ title: HOSTILE, subtitle: HOSTILE, description: HOSTILE, fabric: HOSTILE, measurements: [{ [HOSTILE]: HOSTILE }] }] } },
    { type: 'inventory', data: { query: HOSTILE, exceptions: [{ product: HOSTILE, variant: HOSTILE, level: HOSTILE, available: 1 }], products: [{ title: HOSTILE, variants: [{ variant: HOSTILE, sku: HOSTILE, level: 'ok', available: 9 }] }] } },
    { type: 'sales_summary', data: { title: HOSTILE, revenue: HOSTILE, aov: HOSTILE, orders: 3, basis: HOSTILE, since: HOSTILE } },
    { type: 'email_list', data: { threads: [{ from: HOSTILE, subject: HOSTILE, snippet: HOSTILE, date: HOSTILE }] } },
    { type: 'email_thread', data: { subject: HOSTILE, messages: [{ from: HOSTILE, from_email: HOSTILE, body: HOSTILE, date: HOSTILE }] } },
    { type: 'email_draft', data: { to: HOSTILE, subject: HOSTILE, body: HOSTILE } },
    { type: 'attention', data: { items: [{ title: HOSTILE, detail: HOSTILE, kind: HOSTILE }] } },
    { type: 'confirmation', data: { title: HOSTILE, detail: HOSTILE, confirm_label: HOSTILE, tier: HOSTILE } },
    { type: 'success', data: { title: HOSTILE, detail: HOSTILE } },
    { type: 'error', data: { title: HOSTILE, recovery: HOSTILE, service: HOSTILE } },
  ];
  const out = UI.render(items);
  assert.equal(out.nodes.length, items.length);
  for (const node of out.nodes) {
    // The hostile string is present verbatim as text...
    assert.ok(textOf(node).includes(HOSTILE), `${node.dataset.type} lost the text`);
    // ...and no element was ever created from it.
    const tags = new Set();
    (function walk(el) { for (const c of el.children) { tags.add(c.tagName); walk(c); } })(node);
    assert.ok(!tags.has('IMG') && !tags.has('SCRIPT'), `${node.dataset.type} created markup`);
  }
  // Attributes are never built from data either: no attribute value carries the payload.
  (function walk(el) {
    for (const [k, v] of Object.entries(el.attributes)) assert.ok(!v.includes('<'), `${el.tagName}[${k}] carries markup`);
    for (const c of el.children) walk(c);
  })(out.nodes[1]);
});

test('an order renders its hierarchy: number, status, customer, then items behind a tab', () => {
  const node = UI.renderItem({ type: 'order', data: {
    order_number: '#1930', fulfillment: 'unfulfilled', payment: 'paid', total: '£60.00', customer_name: 'Sam Fixture',
    placed_at: '2026-09-08T09:42:00Z', detail: true,
    items: [{ title: 'Yard Jeans', variant: 'M', quantity: 1, total: '£60.00' }], fulfillments: [],
  } });
  assert.equal(node.dataset.type, 'order');
  assert.equal(node.querySelector('.card-title').textContent, '#1930');
  const badges = node.querySelectorAll('.badge').map((b) => [b.textContent, b.className]);
  assert.deepEqual(badges, [['unfulfilled', 'badge warn'], ['paid', 'badge ok']]);
  const tabs = node.querySelectorAll('.tab').map((t) => t.textContent);
  assert.deepEqual(tabs, ['Overview', 'Items · 1', 'Shipping', 'Customer']);
  const panels = node.querySelectorAll('.panel');
  assert.deepEqual(panels.map((p) => p.hidden), [false, true, true, true]);
  node.querySelectorAll('.tab')[1].dispatch('click');
  assert.deepEqual(panels.map((p) => p.hidden), [true, false, true, true]);
  assert.ok(textOf(panels[1]).includes('Yard Jeans'));
});

test('a summary order has no tabs and says how to get more', () => {
  const node = UI.renderItem({ type: 'order', data: { order_number: '#1930', detail: false } });
  assert.equal(node.querySelectorAll('.tab').length, 0);
  assert.ok(textOf(node).includes('items and shipping'));
});

test('inventory leads with the exceptions', () => {
  const node = UI.renderItem({ type: 'inventory', data: {
    query: 'Yard Jeans', low_stock_at: 5,
    exceptions: [{ product: 'Yard Jeans', variant: 'M', available: 3, level: 'low' }, { product: 'Yard Jeans', variant: 'S', available: 0, level: 'out' }],
    products: [{ title: 'Yard Jeans', variants: [{ variant: 'M', available: 3, level: 'low' }, { variant: 'L', available: 20, level: 'ok' }] }],
  } });
  const rows = node.querySelectorAll('.row');
  assert.ok(rows.length >= 2);
  assert.ok(textOf(rows[0]).includes('3 left') && textOf(rows[0]).includes('Low stock'));
  assert.ok(textOf(rows[1]).includes('Out of stock'));
});

test('sales summary shows real figures and no invented comparison', () => {
  const node = UI.renderItem({ type: 'sales_summary', data: { title: 'Today', revenue: '£430.50', orders: 12, aov: '£35.88', complete: true } });
  assert.equal(node.querySelector('.big').textContent, '£430.50');
  const stats = node.querySelectorAll('.stat-v').map((s) => s.textContent);
  assert.deepEqual(stats, ['12', '£35.88']);
  assert.ok(!textOf(node).toLowerCase().includes('vs'));
});

test('email thread: last message open, earlier ones collapsed and openable', () => {
  const node = UI.renderItem({ type: 'email_thread', data: { subject: 'Re: order', messages: [
    { from: 'A', body: 'first' }, { from: 'B', body: 'second' },
  ] } });
  const msgs = node.querySelectorAll('.msg');
  assert.deepEqual(msgs.map((m) => m.classList.contains('is-collapsed')), [true, false]);
  msgs[0].dispatch('click');
  assert.equal(msgs[0].classList.contains('is-collapsed'), false);
});

test('a draft never has a send control and says nothing was sent', () => {
  const node = UI.renderItem({ type: 'email_draft', data: { to: 'x@example.com', subject: 's', body: 'b' } });
  const buttons = node.querySelectorAll('button');
  assert.ok(buttons.length > 0);
  for (const b of buttons) {
    assert.equal(b.getAttribute('disabled'), 'disabled');
    assert.ok(!/send/i.test(b.textContent), 'a send button exists');
  }
  assert.ok(/not sent/i.test(textOf(node)));
});

test('a confirmation has only disabled controls and names the tier', () => {
  const amber = UI.renderItem({ type: 'confirmation', data: { title: 'Fulfil?', tier: 'amber' } });
  const red = UI.renderItem({ type: 'confirmation', data: { title: 'Refund?', tier: 'red' } });
  for (const node of [amber, red]) for (const b of node.querySelectorAll('button')) assert.equal(b.getAttribute('aria-disabled'), 'true');
  assert.ok(amber.querySelector('.tier-amber') && red.querySelector('.tier-red'));
  assert.ok(/read-only/i.test(textOf(red)));
});

test('the context stack comes back as entries and chips, not as a card', () => {
  const out = UI.render([
    { type: 'order', data: { order_number: '#1' } },
    { type: 'context_stack', data: { entries: [{ kind: 'order', label: '#1', ref: 'o1' }, { kind: 'customer', label: HOSTILE, ref: 'c1' }] } },
  ]);
  assert.equal(out.nodes.length, 1);
  assert.equal(out.stack.length, 2);
  let picked = null;
  const chips = UI.renderStack(out.stack, { active: 'c1', onSelect: (e) => { picked = e; } });
  assert.deepEqual(chips.map((c) => c.getAttribute('aria-pressed')), ['false', 'true']);
  assert.ok(textOf(chips[1]).includes(HOSTILE));
  chips[1].dispatch('click');
  assert.equal(picked.ref, 'c1');
});

test('fixtures are marked as such', () => {
  const node = UI.renderItem({ type: 'customer', data: { name: 'Sam' } }, { fixture: true });
  assert.ok(node.classList.contains('is-fixture'));
  assert.ok(/not live/i.test(textOf(node)));
  const live = UI.renderItem({ type: 'customer', data: { name: 'Sam' } });
  assert.ok(!live.classList.contains('is-fixture'));
});

test('lists are bounded even when the payload is not', () => {
  const orders = Array.from({ length: 200 }, (_, i) => ({ order_number: `#${i}` }));
  const node = UI.renderItem({ type: 'order_list', data: { orders } });
  assert.ok(node.querySelectorAll('.row').length <= 10);
  const threads = Array.from({ length: 200 }, (_, i) => ({ subject: `s${i}` }));
  assert.ok(UI.renderItem({ type: 'email_list', data: { threads } }).querySelectorAll('.row').length <= 10);
  const many = Array.from({ length: 100 }, () => ({ type: 'assistant', data: { text: 'x' } }));
  assert.ok(UI.render(many).nodes.length <= 16);
});

test('dates are formatted for reading, and left alone when unparseable', () => {
  assert.match(UI.formatDate('2026-09-08T09:42:00Z'), /8 Sept|8 Sep/);
  assert.equal(UI.formatDate('not a date'), 'not a date');
  assert.equal(UI.formatDate(''), '');
});
