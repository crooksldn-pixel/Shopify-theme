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
  // No buttons at all: the dead "Rewrite / Shorter" controls went with the space they cost.
  assert.equal(node.querySelectorAll('button').length, 0);
  assert.ok(!/send\b/i.test(textOf(node).replace(/not sent|nothing has been sent/gi, '')), 'a send control exists');
  assert.ok(/not sent/i.test(textOf(node)));
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
  for (const data of [{ status: 'expired' }, { interaction: { kind: 'hold_drag_target' } }, { proposal_id: '' }]) {
    const h = tapHarness(data);
    h.at(5000);
    h.surface.dispatch('pointerdown'); h.surface.dispatch('pointerup');
    assert.deepEqual(h.commits, []);
  }
  assert.ok(textOf(tapHarness({ interaction: { kind: 'hold_drag_target' } }).node).includes('newer tablet build'));
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

test('an order carries its progress strip and previews what was bought', () => {
  const node = UI.renderItem({ type: 'order', data: { order_number: '#1930', payment: 'paid', fulfillment: 'unfulfilled', placed_at: '2026-09-08T09:42:00Z', detail: true,
    items: [{ title: 'Yard Jeans', variant: 'M', total: '£60.00', quantity: 2 }, { title: 'Convict Sweats', variant: 'L', total: '£55.00', quantity: 1 }, { title: 'Cap', total: '£20.00' }, { title: 'Socks', total: '£8.00' }], fulfillments: [] } });
  const steps = node.querySelectorAll('.tl-step');
  assert.equal(steps.length, 3);
  assert.deepEqual(steps.map((s) => s.classList.contains('is-done')), [true, true, false]);
  assert.ok(textOf(steps[2]).includes('To ship'));
  const preview = node.querySelector('.items-preview');
  assert.equal(preview.querySelectorAll('li').length, 4, 'three items and an "and more" line');
  assert.ok(textOf(preview).includes('Yard Jeans · M') && textOf(preview).includes('× 2') && textOf(preview).includes('and 1 more'));
  const cancelled = UI.renderItem({ type: 'order', data: { order_number: '#1', payment: 'refunded', fulfillment: 'unfulfilled', cancelled_at: '2026-09-08T10:00:00Z' } });
  assert.equal(cancelled.querySelectorAll('.is-bad').length, 1);   // the shim reads one class at a time
  assert.ok(textOf(cancelled).includes('Cancelled'));
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
  assert.ok(/write_orders/.test(words.scope_missing));
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
