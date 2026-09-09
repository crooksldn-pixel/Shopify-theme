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

test('an order is composed by entity: number and status, then items, money, shipping, customer, email', () => {
  const node = UI.renderItem({ type: 'order', data: {
    order_number: '#1930', fulfillment: 'unfulfilled', payment: 'paid', total: '£60.00', customer_name: 'Sam Fixture',
    placed_at: '2026-09-08T09:42:00Z', detail: true,
    items: [{ title: 'Yard Jeans', variant: 'M', quantity: 1, total: '£60.00', stock: { tracked: true, available: 3 } }], fulfillments: [],
    money: { subtotal: '£55.00', shipping: '£5.00', tax: '£9.17', discounts: '£0.00', refunded: '£0.00', outstanding: '£0.00' },
    shipping_address: { name: 'Sam Fixture', lines: ['12 Somewhere Street', 'Flat 3'], city: 'Windsor', zip: 'SL4 1AA', country: 'United Kingdom' },
    shipping_method: 'Royal Mail Tracked 24',
    history: { orders: 3, spent: '£410.00', since: '2025-01-02T00:00:00Z', standing: 'returning', first_order_at: '2025-01-02T10:00:00Z', other_unfulfilled: ['#1901'],
      recent: [{ order_number: '#1930', placed_at: '2026-09-08T09:42:00Z', total: '£60.00', fulfillment: 'unfulfilled', current: true }, { order_number: '#1901', placed_at: '2026-08-20T10:00:00Z', total: '£200.00', fulfillment: 'unfulfilled', items_brief: 'Convict Hoodie ×2' }] },
    email: { available: true, threads: [{ thread_id: 't1', from: 'Sam Fixture', subject: 'Address for 1930', date: 'Tue, 8 Sep 2026 10:12:00 +0100', snippet: 'Send it to work', verified_sender: true, match: 'both', provenance: 'CUSTOMER_EMAIL' },
      { thread_id: 't2', from: 'Someone', subject: 'Re: #1930', snippet: 'is this mine', verified_sender: false, match: 'order_number', provenance: 'UNKNOWN' }] },
    pending: [],
  } });
  assert.equal(node.dataset.type, 'order');
  assert.equal(node.querySelector('.card-title').textContent, '#1930');
  const badges = node.querySelectorAll('.badges')[0].querySelectorAll('.badge').map((b) => [b.textContent, b.className]);
  assert.deepEqual(badges, [['unfulfilled', 'badge warn'], ['paid', 'badge ok']]);
  assert.equal(node.querySelectorAll('.tab').length, 0, 'nothing is behind a tab');
  const sections = node.querySelectorAll('.sec').map((s) => s.querySelector('.sec-kicker').textContent);
  assert.deepEqual(sections, ['Items · 1', 'Money', 'Shipping', 'Customerreturning', 'Email']);
  const items = node.querySelector('.items');
  assert.ok(textOf(items).includes('Yard Jeans') && textOf(items).includes('3 left'));
  assert.equal(node.querySelectorAll('.thumb-img').length, 0, 'no image without a signed path');
  const money = textOf(node.querySelector('.money'));
  assert.ok(money.includes('Subtotal') && money.includes('£5.00') && money.includes('Total') && !money.includes('Refunded'), 'zero refunds are not a line');
  const addr = node.querySelectorAll('.addr-line').map((l) => l.textContent);
  assert.deepEqual(addr, ['Sam Fixture', '12 Somewhere Street', 'Flat 3', 'Windsor SL4 1AA', 'United Kingdom']);
  const hist = textOf(node.querySelector('.sec-history'));
  assert.ok(hist.includes('Lifetime') && hist.includes('£410.00') && hist.includes('Also waiting to ship: #1901') && hist.includes('First order') && hist.includes('this order'));
  const mail = node.querySelector('.sec-email');
  assert.deepEqual(mail.querySelectorAll('.badge').map((b) => b.textContent), ['From the customer · verified', 'Mentions the order']);
  const matched = UI.renderItem({ type: 'order', data: { detail: true, items: [], pending: [], email: { available: true, threads: [{ thread_id: 't', subject: 'x', sender_match: true, verified_sender: false }] } } });
  assert.equal(matched.querySelector('.sec-email').querySelector('.badge').textContent, 'Sender matches');
  assert.equal(node.dataset.pending, '');
});

test('a summary order has no sections and says how to get more', () => {
  const node = UI.renderItem({ type: 'order', data: { order_number: '#1930', detail: false } });
  assert.equal(node.querySelectorAll('.sec').length, 0);
  assert.ok(textOf(node).includes('items and shipping'));
});

test('an image is drawn only from a path the Mac signed, and never from data in fixture-less rendering', () => {
  const signed = '/media/shopify/0123456789abcdef0123456789abcdef/160?u=https%3A%2F%2Fcdn.shopify.com%2Fa.jpg';
  const good = UI.renderItem({ type: 'order', data: { detail: true, items: [{ title: 'Jeans', image: signed }] } });
  assert.equal(good.querySelector('.thumb-img').getAttribute('src'), signed);
  for (const bad of ['https://cdn.shopify.com/a.jpg', '/media/shopify/x/160?u=<img onerror=1>', 'data:image/svg+xml;base64,AAAA', 'javascript:alert(1)']) {
    const node = UI.renderItem({ type: 'order', data: { detail: true, items: [{ title: 'Jeans', image: bad }] } });
    assert.equal(node.querySelectorAll('.thumb-img').length, 0, bad);
    assert.ok(node.querySelector('.thumb-mono'), 'a monogram stands in');
  }
  const fixture = UI.renderItem({ type: 'order', data: { detail: true, items: [{ title: 'Jeans', image: 'data:image/svg+xml;base64,AAAA' }] } }, { fixture: true });
  assert.equal(fixture.querySelectorAll('.thumb-img').length, 1, 'a fixture may carry an inline SVG');
});

test('what missed the budget says so, and is filled in when it arrives', () => {
  const node = UI.renderItem({ type: 'order', data: { detail: true, order_number: '#1930', items: [], pending: ['history', 'email'] } });
  assert.equal(node.dataset.pending, 'history email');
  assert.ok(textOf(node.querySelector('.sec-history')).includes('Reading their history'));
  assert.ok(textOf(node.querySelector('.sec-email')).includes('Checking the inbox'));
  const still = UI.hydrateOrder(node, { pending: ['email'], history: { orders: 2, spent: '£99.00', standing: 'returning', recent: [] } });
  assert.deepEqual(still, ['email']);
  assert.ok(textOf(node.querySelector('.sec-history')).includes('£99.00') && !textOf(node.querySelector('.sec-history')).includes('Reading'));
  assert.ok(textOf(node.querySelector('.sec-email')).includes('Checking the inbox'));
  assert.deepEqual(UI.hydrateOrder(node, { pending: [], email: { available: true, threads: [] } }), []);
  assert.ok(textOf(node.querySelector('.sec-email')).includes('No recent email'));
  assert.equal(node.dataset.pending, '');
  assert.deepEqual(UI.hydrateOrder(null, {}), []);
  const off = UI.renderItem({ type: 'order', data: { detail: true, items: [], pending: [], email: { available: false, reason: 'Gmail is not configured' } } });
  assert.ok(textOf(off.querySelector('.sec-email')).includes('Email not checked'));
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

test('a draft never has a send control and says nothing was sent; a sent one says sent', () => {
  const node = UI.renderItem({ type: 'email_draft', data: { to: 'x@example.com', subject: 's', body: 'b' } });
  // No buttons at all: the dead "Rewrite / Shorter" controls went with the space they cost.
  assert.equal(node.querySelectorAll('button').length, 0);
  assert.ok(/nothing has been sent/i.test(textOf(node)) && /Draft · saved in Gmail/.test(textOf(node)));
  const sent = UI.renderItem({ type: 'email_draft', data: { state: 'sent', to: 'x@example.com', subject: 's', body: 'b' } });
  assert.equal(sent.querySelectorAll('button').length, 0);
  assert.ok(/^Sent/.test(textOf(sent).trim()) && !/nothing has been sent/i.test(textOf(sent)));
});

test('an email card prints the whole body the gesture would send, as text', () => {
  const { node } = tapHarness({ body: 'Hi Sam,\n\nIt ships tomorrow.\n\n' + HOSTILE, operation: 'gmail_send_reply', risk: 'red' });
  const body = node.querySelector('.action-body');
  assert.ok(body && body.textContent.includes('It ships tomorrow.') && body.textContent.includes(HOSTILE));
  assert.equal(node.querySelector('img'), null);
});

test('a confirmation without a proposal is inert and names its risk', () => {
  const amber = UI.renderItem({ type: 'confirmation', data: { title: 'Fulfil?', risk: 'amber' } });
  const red = UI.renderItem({ type: 'confirmation', data: { title: 'Refund?', risk: 'red' } });
  assert.ok(amber.classList.contains('tier-amber') && red.classList.contains('tier-red'));
  for (const node of [amber, red]) {
    assert.equal(node.querySelectorAll('button').length, 0, 'no generic button that could inherit a click');
    const surface = node.querySelector('.action-surface');
    assert.equal(surface.getAttribute('aria-disabled'), 'true');
    assert.notEqual(surface.dataset.state, 'armed');
    assert.equal(typeof node.settle, 'undefined', 'nothing to commit without a proposal id');
  }
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

test('sales summary lists the days when the Mac breaks the window down', () => {
  const node = UI.renderItem({ type: 'sales_summary', data: { title: 'This week', revenue: '£55.50', orders: 3, by_day: [
    { date: '2026-09-07', orders: 1, revenue: '£40.00' },
    { date: '2026-09-08', orders: 2, revenue: '£15.50' },
    'junk', null,
  ] } });
  const rows = node.querySelectorAll('.row');
  assert.equal(rows.length, 2);
  assert.ok(textOf(rows[0]).includes('£40.00') && textOf(rows[0]).includes('1 order'));
  assert.ok(textOf(rows[1]).includes('2 orders') && textOf(rows[1]).includes('Tue'));
  const plain = UI.renderItem({ type: 'sales_summary', data: { title: 'Today', revenue: '£10.00', orders: 1 } });
  assert.equal(plain.querySelectorAll('.row').length, 0);
});

// ------------------------------------------------------------------ actions

function proposalCard(overrides, opts) {
  const data = Object.assign({
    proposal_id: 'prop_1', status: 'pending', risk: 'amber', operation: 'order_note_append', title: 'Add order note',
    entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/1', summary: HOSTILE, detail: 'The order has no note yet.',
    interaction: { kind: 'tap_commit', label: 'Tap to apply', armed_after_ms: 650 }, ttl_s: 60, reversible: true,
  }, overrides || {});
  return UI.renderItem({ type: 'confirmation', data }, opts);
}

function tapHarness(overrides, extra) {
  let t = 0;
  const commits = [];
  const opts = Object.assign({
    now: () => t, blocked: () => false, onCommit: (id, node) => commits.push(id),
    timers: { set: () => 0, clear: () => {} },
  }, extra || {});
  const node = proposalCard(overrides, opts);
  const surface = node.querySelector('.action-surface');
  return { node, surface, commits, at: (ms) => { t = ms; }, arm: () => { surface.dataset.state = 'armed'; } };
}

test('the action card renders from the proposal, through textContent, with its risk and entity', () => {
  const { node, surface } = tapHarness();
  assert.ok(node.classList.contains('tier-amber'));
  assert.ok(textOf(node).includes('Add order note') && textOf(node).includes('Order #1930') && textOf(node).includes(HOSTILE));
  assert.equal(node.querySelectorAll('button').length, 0);
  assert.equal(surface.dataset.state, 'arming');
  assert.equal(surface.getAttribute('aria-disabled'), 'true');
  assert.equal(node.dataset.proposal, 'prop_1');
});

test('a tap during the dead time does nothing', () => {
  const h = tapHarness();
  h.at(100); h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  assert.deepEqual(h.commits, []);
});

test('a press that began before arming cannot commit when it ends after', () => {
  const h = tapHarness();
  h.at(100); h.surface.dispatch('pointerdown');
  h.at(900); h.arm(); h.surface.dispatch('pointerup');
  assert.deepEqual(h.commits, []);
});

test('a tap after arming commits once, and only once', () => {
  const h = tapHarness();
  h.at(700); h.arm();
  h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  assert.deepEqual(h.commits, ['prop_1']);
  assert.equal(h.surface.dataset.state, 'committing');
});

test('recording or a turn in flight blocks the tap', () => {
  let busy = true;
  const h = tapHarness({}, { blocked: () => busy });
  h.at(700); h.arm();
  h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  assert.deepEqual(h.commits, []);
  busy = false;
  h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  assert.deepEqual(h.commits, ['prop_1']);
});

test('a settled card cannot be tapped', () => {
  for (const state of ['stale', 'expired', 'revoked', 'verified']) {
    const h = tapHarness();
    h.at(700); h.arm();
    h.node.settle(state, 'Not available');
    h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
    assert.deepEqual(h.commits, [], state);
    assert.equal(h.surface.dataset.state, state);
  }
});

test('a proposal that is not pending, or an interaction the tablet does not know, is inert', () => {
  for (const data of [{ status: 'expired' }, { interaction: { kind: 'select_then_commit' } }, { proposal_id: '' }]) {
    const h = tapHarness(data);
    h.at(5000);
    h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
    assert.deepEqual(h.commits, []);
  }
  assert.ok(textOf(tapHarness({ interaction: { kind: 'select_then_commit' } }).node).includes('newer tablet build'));
});

test('a success card offers its undo the same way, and success needs a verified answer to exist at all', () => {
  const commits = [];
  let t = 0;
  const node = UI.renderItem({ type: 'success', data: { title: 'Note added', detail: 'Order #1930', proposal_id: 'prop_1', undo: { proposal_id: 'prop_2', label: 'Undo', ttl_s: 60, armed_after_ms: 650 } } },
    { now: () => t, onCommit: (id) => commits.push(id), timers: { set: () => 0, clear: () => {} } });
  const surface = node.querySelector('.action-surface');
  assert.ok(surface && textOf(surface).includes('Undo'));
  t = 100; surface.dispatch('pointerdown'); surface.dispatch('pointerup');
  assert.deepEqual(commits, []);
  t = 700; surface.dataset.state = 'armed';
  surface.dispatch('pointerdown'); surface.dispatch('pointerup');
  assert.deepEqual(commits, ['prop_2']);
  const plain = UI.renderItem({ type: 'success', data: { title: 'Note added' } });
  assert.equal(plain.querySelector('.action-surface'), null);
});

// ------------------------------------------------------------------ composition

test('an order carries its progress strip and every item, with the quantity where it is more than one', () => {
  const node = UI.renderItem({ type: 'order', data: { order_number: '#1930', payment: 'paid', fulfillment: 'unfulfilled', placed_at: '2026-09-08T09:42:00Z', detail: true,
    items: [{ title: 'Yard Jeans', variant: 'M', total: '£60.00', quantity: 2 }, { title: 'Convict Sweats', variant: 'L', total: '£55.00', quantity: 1 }, { title: 'Cap', total: '£20.00' }, { title: 'Socks', total: '£8.00' }], fulfillments: [], items_truncated: true } });
  const steps = node.querySelectorAll('.tl-step');
  assert.equal(steps.length, 3);
  assert.deepEqual(steps.map((s) => s.classList.contains('is-done')), [true, true, false]);
  assert.ok(textOf(steps[2]).includes('To ship'));
  const items = node.querySelector('.items');
  assert.equal(items.querySelectorAll('.item').length, 5, 'four items and a "more" line');
  assert.ok(textOf(items).includes('Yard Jeans') && textOf(items).includes('× 2') && textOf(items).includes('More items than shown'));
  const cancelled = UI.renderItem({ type: 'order', data: { order_number: '#1', payment: 'refunded', fulfillment: 'unfulfilled', cancelled_at: '2026-09-08T10:00:00Z' } });
  assert.equal(cancelled.querySelectorAll('.is-bad').length, 1);   // the shim reads one class at a time
  assert.ok(textOf(cancelled).includes('Cancelled'));
});

test('a customer card carries the history when the tool returned it', () => {
  const node = UI.renderItem({ type: 'customer', data: { customer_id: 'c1', name: 'Daniel Sear', email: 'd@example.com', orders: 3, spent: '£410.00',
    history: { orders: 3, spent: '£410.00', since: '2025-01-02T00:00:00Z', standing: 'returning', other_unfulfilled: ['#1901', '#1938'], recent: [{ order_number: '#1938', total: '£60.00', fulfillment: 'unfulfilled' }] },
    related_email: { available: true, threads: [{ thread_id: 't1', subject: 'Hello', verified_sender: true }] } } });
  assert.ok(textOf(node).includes('Also waiting to ship: #1901, #1938') && textOf(node).includes('From the customer'));
  const many = UI.renderItem({ type: 'customer', data: { name: 'R', history: { orders: 12, recent_truncated: true, recent: [{ order_number: '#9' }, { order_number: '#8' }] } } });
  assert.ok(textOf(many).includes('Last 2 of 12 orders shown'));
  assert.ok(textOf(node).includes('d@example.com'), 'the address is still the address');
  assert.ok(!textOf(node).includes('Ask for their orders'));
});

test('a customer is a profile: initials, standing, lifetime', () => {
  const node = UI.renderItem({ type: 'customer', data: { customer_id: 'c1', name: 'Daniel Sear', email: 'd@example.com', orders: 4, spent: '£286.00' } });
  assert.equal(textOf(node.querySelector('.avatar')), 'DS');
  assert.ok(textOf(node).includes('Regular') && textOf(node).includes('Lifetime'));
  assert.equal(node.dataset.ref, 'c1');
  assert.equal(textOf(UI.renderItem({ type: 'customer', data: { name: HOSTILE } }).querySelector('.avatar')).length, 2);
  assert.ok(textOf(UI.renderItem({ type: 'customer', data: { name: 'Solo', orders: 1 } })).includes('First order'));
});

test('sales over several days become a strip of bars whose heights are numbers of our own making', () => {
  const node = UI.renderItem({ type: 'sales_summary', data: { title: 'This week', revenue: '£1,000.00', orders: 10, by_day: [
    { date: '2026-09-02', orders: 1, revenue: '£100.00' }, { date: '2026-09-03', orders: 2, revenue: '£400.00' }, { date: '2026-09-04', orders: 0, revenue: '£0.00' } ] } });
  const bars = node.querySelectorAll('.bar');
  assert.equal(bars.length, 3);
  assert.deepEqual(bars.map((b) => Number(b.dataset.pct)), [25, 100, 4]);
  assert.equal(UI.renderItem({ type: 'sales_summary', data: { revenue: '£1', by_day: [{ date: '2026-09-02', revenue: '£1' }] } }).querySelectorAll('.bar').length, 0, 'one day is not a chart');
});

test('an email thread shows a face per message and lights the latest', () => {
  const node = UI.renderItem({ type: 'email_thread', data: { subject: 's', messages: [{ from: 'Ada Lovelace', body: 'one' }, { from: 'Sam Fixture', body: 'two' }] } });
  const msgs = node.querySelectorAll('.msg');
  assert.equal(msgs.length, 2);
  assert.deepEqual(msgs.map((m) => textOf(m.querySelector('.avatar'))), ['AL', 'SF']);
  assert.ok(msgs[0].classList.contains('is-collapsed') && msgs[1].classList.contains('is-latest'));
});

test('the surface stops inviting a tap just before the Mac would say Expired', () => {
  const scheduled = [];
  const h = tapHarness({ ttl_s: 60 }, { timers: { set: (fn, ms) => { scheduled.push({ fn, ms }); return scheduled.length; }, clear: () => {} } });
  const expiry = scheduled.find((t) => t.ms > 1000);
  assert.ok(expiry && expiry.ms === 59000, 'a second early, never late');
  h.at(700); h.arm();
  expiry.fn();
  assert.equal(h.surface.dataset.state, 'expired');
  h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
  assert.deepEqual(h.commits, []);
  assert.ok(textOf(h.surface).includes('Expired'));
});

test('the arming fill lasts exactly as long as the arming', () => {
  const h = tapHarness({ interaction: { kind: 'tap_commit', label: 'Tap to apply', armed_after_ms: 900 } });
  assert.equal(h.surface.style.getPropertyValue('--arm-ms'), '900ms');
});

test('partial payment and partial shipping light the middle of the strip', () => {
  const node = UI.renderItem({ type: 'order', data: { order_number: '#2', payment: 'partially paid', fulfillment: 'partially fulfilled', placed_at: '2026-09-08T09:42:00Z' } });
  assert.equal(node.querySelectorAll('.is-partial').length, 2);
});

test('a blocked card names who is stopping the tap, by code, and never blames the tablet for the Mac', () => {
  const words = {};
  for (const code of ['writes_disabled', 'allow_list_missing', 'not_authorised', 'not_authorised_local', 'scope_missing', 'something_else']) {
    const node = proposalCard({ commit: { allowed: false, code, reason: 'why' } });
    const surface = node.querySelector('.action-surface');
    assert.equal(surface.dataset.state, 'unavailable');
    words[code] = textOf(surface);
  }
  assert.ok(/switched off on the Mac/.test(words.writes_disabled));
  assert.ok(/No allowed logins/.test(words.allow_list_missing));
  assert.ok(/tablet's login/.test(words.not_authorised));
  assert.ok(/Mac itself/.test(words.not_authorised_local) && !/tablet/.test(words.not_authorised_local));
  assert.ok(/Shopify has not granted/.test(words.scope_missing));
  for (const text of Object.values(words)) assert.ok(!/not allowed/i.test(text), text);
});

test('the wait line counts down while the card is live and clears when it settles', () => {
  const scheduled = [];
  let t = 0;
  const timers = { set: (fn, ms) => { scheduled.push({ fn, ms }); return scheduled.length; }, clear: () => {} };
  const node = proposalCard({ ttl_s: 60 }, { now: () => t, blocked: () => false, onCommit: () => {}, timers });
  const meta = node.querySelector('.action-meta');
  assert.ok(textOf(meta).startsWith('Waits 60 s'));
  const tick = scheduled.find((s) => s.ms === 1000);
  t = 12000; tick.fn();
  assert.ok(textOf(meta).startsWith('Waits 48 s'), textOf(meta));
  node.settle('revoked', 'Withdrawn');
  assert.equal(textOf(meta), '');
});

test('a sales window names the last day it covers, not the morning after', () => {
  const node = UI.renderItem({ type: 'sales_summary', data: { title: 'Last 7 days', revenue: '£1,000.00', orders: 12, days: 7, since: '2026-09-01T23:00:00Z', until: '2026-09-08T23:00:00Z' } });
  const meta = textOf(node.querySelector('.card-meta'));
  assert.ok(meta.indexOf('→') !== -1 && /8 Sept/.test(meta) && !/9 Sept/.test(meta), meta);
});

test('the undo counts down too, and stops offering itself when its minute is up', () => {
  const scheduled = [];
  let t = 0;
  const timers = { set: (fn, ms) => { scheduled.push({ fn, ms }); return scheduled.length; }, clear: () => {} };
  const node = UI.renderItem({ type: 'success', data: { title: 'Note added', detail: 'Order #1930', proposal_id: 'p1', undo: { proposal_id: 'p2', label: 'Undo', armed_after_ms: 100, ttl_s: 60 } } },
    { now: () => t, blocked: () => false, onCommit: () => {}, timers });
  const meta = node.querySelectorAll('.action-meta').pop();
  assert.ok(textOf(meta).indexOf('Undo available for') === 0, textOf(meta));
  const tick = scheduled.find((s) => s.ms === 1000);
  t = 20000; tick.fn();
  assert.equal(textOf(meta), 'Undo available for 40 s');
  const expiry = scheduled.find((s) => s.ms > 1000);
  assert.ok(expiry && expiry.ms === 59000);
  expiry.fn();
  assert.equal(node.querySelector('.action-surface').dataset.state, 'expired');
});

test('the rail shows only the Mac\'s chips, primes the words on tap, and a disabled chip says why and does nothing', () => {
  const primed = [];
  const node = UI.renderItem({ type: 'order', data: { detail: true, order_number: '#1938', items: [], pending: [], actions: [
    { id: 'note', label: 'Note', risk: 'amber', enabled: true, instruction: 'Add a note to order 1938', mode: 'ask' },
    { id: 'cancel', label: 'Cancel', risk: 'red', enabled: true, instruction: 'Cancel order 1938', mode: 'ask' },
    { id: 'refund', label: 'Refund', risk: 'red', enabled: false, reason: 'not paid', instruction: 'Refund order 1938', mode: 'ask' },
    { id: 'evil', label: HOSTILE, risk: 'red', enabled: true, instruction: HOSTILE, mode: 'ask' },
  ] } }, { onAction: (a) => primed.push(a.id) });
  const chips = node.querySelectorAll('.rail-chip');
  assert.equal(chips.length, 4);
  assert.deepEqual(chips.map((c) => c.getAttribute('aria-disabled')), ['false', 'false', 'true', 'false']);
  assert.ok(textOf(chips[2]).includes('not paid'));
  chips[0].dispatch('click'); chips[1].dispatch('click'); chips[2].dispatch('click'); chips[3].dispatch('click');
  assert.deepEqual(primed, ['note', 'cancel', 'evil']);
  assert.ok(textOf(chips[3]).includes(HOSTILE) && !node.querySelectorAll('img').length);
  assert.equal(UI.renderItem({ type: 'order', data: { detail: true, items: [], actions: [] } }).querySelectorAll('.rail').length, 0, 'no rail without chips');
});


// ---- the gestures. A timer table stands in for setTimeout so a hold can be "completed" by
// firing the timer the surface armed, and a press can carry coordinates.

function gestureHarness(kind, extra) {
  let t = 0;
  const commits = [];
  const arms = [];
  const timers = [];
  const opts = Object.assign({
    now: () => t, blocked: () => false, trackWidth: 356,
    onCommit: (id, node, nonce) => commits.push([id, nonce || '']),
    onArm: (id) => { arms.push(id); return Promise.resolve('tok-1'); },
    timers: { set: (fn, ms) => { timers.push({ fn, ms, id: timers.length + 1 }); return timers.length; }, clear: (id) => { const x = timers[id - 1]; if (x) x.cleared = true; } },
  }, extra || {});
  const node = proposalCard({ interaction: { kind, label: 'x', armed_after_ms: 650, target: 'Drop to cancel and refund £60.00' }, risk: 'red' }, opts);
  const surface = node.querySelector('.action-surface');
  const fire = (ms) => { for (const x of timers) if (!x.fired && !x.cleared && x.ms === ms) { x.fired = true; x.fn(); } };
  const down = (x, y) => surface.dispatch('pointerdown', { clientX: x || 0, clientY: y || 0, pointerId: 1 });
  const move = (x, y) => surface.dispatch('pointermove', { clientX: x || 0, clientY: y || 0, pointerId: 1 });
  const up = () => surface.dispatch('pointerup', { pointerId: 1 });
  const settle = () => new Promise((r) => setTimeout(r, 0));
  return { node, surface, commits, arms, timers, fire, down, move, up, settle, at: (ms) => { t = ms; }, arm: () => { surface.dataset.state = 'armed'; } };
}
const TRACK = 300;   // 356 minus a 56 px handle

test('a swipe commits only past most of the track, and a vertical wobble is a scroll', () => {
  const h = gestureHarness('swipe_commit');
  assert.equal(h.surface.dataset.kind, 'swipe_commit');
  assert.ok(h.node.querySelector('.action-track') && h.node.querySelector('.action-handle'));
  h.at(700); h.arm();
  h.down(10, 100); h.move(120, 102); h.up();                 // not far enough
  assert.deepEqual(h.commits, []);
  assert.equal(h.surface.dataset.dx, '0', 'the handle springs back');
  h.down(10, 100); h.move(60, 140); h.up();                  // the thumb went down the page
  assert.deepEqual(h.commits, []);
  h.down(10, 100); h.move(100, 101); h.move(240, 103); h.up();
  assert.deepEqual(h.commits, [['prop_1', '']]);
  assert.equal(h.surface.dataset.state, 'committing');
  h.down(10, 100); h.move(300, 100); h.up();
  assert.equal(h.commits.length, 1, 'once');
});

test('a swipe during the dead time, or while busy, moves nothing', () => {
  let busy = false;
  const h = gestureHarness('swipe_commit', { blocked: () => busy });
  h.at(100); h.down(10, 100); h.move(300, 100); h.up();
  assert.deepEqual(h.commits, []);
  h.at(700); h.arm(); busy = true;
  h.down(10, 100); h.move(300, 100); h.up();
  assert.deepEqual(h.commits, []);
});

test('hold to arm: the Mac is told as the hold begins, a wobble aborts it, the tap after the hold commits with the token', async () => {
  const h = gestureHarness('hold_to_arm');
  h.at(700); h.arm();
  h.down(50, 50);
  assert.equal(h.surface.dataset.state, 'holding');
  assert.deepEqual(h.arms, ['prop_1']);
  await h.settle();
  h.move(50 + 20, 50);                                       // a wobble
  assert.equal(h.surface.dataset.state, 'armed');
  assert.ok(textOf(h.surface).includes('Hold still'));
  h.up();
  assert.deepEqual(h.commits, []);
  // A still hold: the timer completes it, the surface says so, and a tap applies it.
  h.down(50, 50); await h.settle();
  h.fire(HOLD_TOTAL);
  assert.equal(h.surface.dataset.state, 'held');
  assert.ok(textOf(h.surface).includes('Armed'));
  h.up();                                                    // the lift that ends the hold: nothing yet
  assert.deepEqual(h.commits, []);
  h.at(1500); h.down(50, 50); h.up();                        // the tap
  assert.deepEqual(h.commits, [['prop_1', 'tok-1']]);
});
const HOLD_TOTAL = 1050;

test('a hold the Mac will not arm never commits, and a lift before the hold completes disarms', async () => {
  const h = gestureHarness('hold_to_arm', { onArm: () => Promise.resolve(null) });
  h.at(700); h.arm();
  h.down(50, 50); await h.settle();
  assert.equal(h.surface.dataset.state, 'armed');
  assert.ok(textOf(h.surface).includes("won't arm"));
  const g = gestureHarness('hold_to_arm');
  g.at(700); g.arm();
  g.down(50, 50); await g.settle(); g.up();
  assert.equal(g.surface.dataset.state, 'armed');
  g.fire(HOLD_TOTAL);
  assert.equal(g.surface.dataset.state, 'armed', 'a timer that outlived its hold changes nothing');
  assert.deepEqual(g.commits, []);
});

test('an armed hold lapses when no tap follows', async () => {
  const h = gestureHarness('hold_to_arm');
  h.at(700); h.arm();
  h.down(50, 50); await h.settle(); h.fire(HOLD_TOTAL); h.up();
  assert.equal(h.surface.dataset.state, 'held');
  h.fire(5000);
  assert.equal(h.surface.dataset.state, 'armed');
  h.at(1500); h.down(50, 50); h.up();
  assert.deepEqual(h.commits, [], 'the tap after the lapse begins a new hold, not a commit');
  assert.equal(h.surface.dataset.state, 'armed');
});

test('hold and drag: the handle unlocks only after the hold, and commits only when released on the target', async () => {
  const h = gestureHarness('hold_drag_target');
  assert.ok(textOf(h.node.querySelector('.action-target')).includes('refund £60.00'));
  h.at(700); h.arm();
  h.down(10, 100); await h.settle();
  h.move(200, 100);                                          // dragging before the hold completed is a wobble
  assert.equal(h.surface.dataset.state, 'armed');
  h.up();
  h.down(10, 100); await h.settle(); h.fire(HOLD_TOTAL);
  assert.equal(h.surface.dataset.state, 'held');
  h.move(120, 101); h.up();                                  // released short of the target
  assert.deepEqual(h.commits, []);
  assert.equal(h.surface.dataset.state, 'armed');
  h.down(10, 100); await h.settle(); h.fire(HOLD_TOTAL);
  h.move(150, 100); h.move(260, 102); h.up();                // onto the target
  assert.deepEqual(h.commits, [['prop_1', 'tok-1']]);
  assert.equal(h.surface.dataset.state, 'committing');
});

test('a settled surface answers to no gesture', async () => {
  for (const kind of ['swipe_commit', 'hold_to_arm', 'hold_drag_target']) {
    const h = gestureHarness(kind);
    h.at(700); h.arm();
    h.node.settle('revoked', 'Withdrawn');
    h.down(10, 100); await h.settle(); h.fire(HOLD_TOTAL); h.move(300, 100); h.up();
    assert.deepEqual(h.commits, [], kind);
    assert.equal(h.surface.dataset.state, 'revoked');
  }
});

test('the card prints the facts the gesture authorises and the footer names the gesture', () => {
  const node = proposalCard({ interaction: { kind: 'hold_drag_target', label: 'Hold, then drag', footer: 'nothing happens until you hold the card and drag', armed_after_ms: 650 },
    facts: [{ label: 'Refund', value: '£60.00 to the original card', tone: 'bad' }, { label: 'Customer emailed', value: 'yes' }, { label: 'Empty', value: '' }], ttl_s: 60 }, { timers: { set: () => 0, clear: () => {} }, now: () => 0 });
  const facts = node.querySelectorAll('dd').map((d) => d.textContent);
  assert.deepEqual(facts, ['£60.00 to the original card', 'yes']);
  assert.ok(textOf(node.querySelector('.action-meta')).includes('nothing happens until you hold the card and drag'));
  assert.ok(node.classList.contains('kind-hold_drag_target'));
});

test('an undo takes the kind the Mac gave it', () => {
  const node = UI.renderItem({ type: 'success', data: { title: 'Done', proposal_id: 'p', undo: { proposal_id: 'u', label: 'Undo', ttl_s: 60, interaction: 'hold_to_arm' } } }, { now: () => 0, timers: { set: () => 0, clear: () => {} } });
  assert.equal(node.querySelector('.action-surface').dataset.kind, 'hold_to_arm');
  assert.ok(textOf(node.querySelector('.action-surface')).toLowerCase().includes('hold'));
});
