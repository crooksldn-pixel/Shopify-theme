/* Which tab a card opens on — D-2, the owner's loudest complaint, under Node.
 *
 * 20:18:12, verbatim: "can you log that I'm not seeing any UI here except email where there's
 * nothing? I want to also be seeing his orders and his history and like an email write box,
 * and there's none of that here".
 *
 * It was all there, one tab away on the same card. `renderOpts().tab` was ONE value per
 * BRANCH, handed to every card that had tabs (web/app.js:1692 → web/ui.js tabs()). He tapped
 * Email once, on one customer, early in the session; from that moment every customer card on
 * that branch opened on Email — including all seven cards of turn_be1b384ca420, freshly drawn
 * for seven customers he had never opened:
 *
 *   {'type':'customer','ref':'…6343','tabs':['Overview','Orders','Email'],'tab_active':'Email'}
 *   … ×7, seven different ids, every one open on Email
 *
 * The Email tab was TAPPED TWICE all session and was active on 23 rendered cards.
 *
 * So tab selection belongs to an ENTITY, and the precedence is fixed here, in the renderer,
 * in one function (`tabFor`):
 *
 *   1. the tab THIS card is open on right now — a patch never moves the owner's reading;
 *   2. the tab the TASK implies, named by the Mac for THIS card (`data.tab`);
 *   3. the tab the owner left THIS record on (`opts.tabOf`, by render identity);
 *   4. nothing: the card's first panel.
 *
 * Never, at any step, a tab tapped on a different record.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
globalThis.document = shim.document;
const UI = require(path.join(__dirname, '..', '..', 'web', 'ui.js'));

// Two customers with orders AND email, so both cards carry the same three tabs the live
// session recorded: Overview, Orders, Email.
function customer(id, name) {
  return {
    type: 'customer',
    data: {
      customer_id: id, name, email: `${name.toLowerCase()}@example.com`, orders: 2, spent: '£120.00',
      history: { orders: 2, spent: '£120.00', standing: 'Returning', recent: [{ order_number: '#1938', total: '£60.00' }] },
      related_email: { threads: [{ thread_id: 't1', subject: 'Where is my order?' }] },
    },
  };
}

function deck() {
  const host = shim.document.createElement('div');
  host.scrollTop = 0;
  return host;
}

function patch(op, item, extra) {
  return Object.assign({ id: UI.surfaceId(item), op, type: item.type, item }, extra || {});
}

// The tab the card is open on, read the way the telemetry reads it: the selected tab button.
function openTab(node) {
  const tabs = node.querySelectorAll('[role="tab"]');
  const active = tabs.filter((t) => t.getAttribute('aria-selected') === 'true')[0];
  return active ? active.textContent.trim() : '';
}

// A per-entity store of the kind web/app.js keeps (`cardTabs`, keyed by render identity).
function store() {
  const held = new Map();
  return {
    tabOf: (id) => held.get(id) || '',
    onTab: (id, name) => held.set(id, name),
    held,
  };
}

// --------------------------------------------------------------------- D-2

test('a tab tapped on one customer does not open the next customer on it', () => {
  const tabs = store();
  const opts = { tabOf: tabs.tabOf, onTab: tabs.onTab };
  const a = customer('gid://shopify/Customer/6343', 'Ada');
  const b = customer('gid://shopify/Customer/4807', 'Bea');

  // He taps Email on customer A. That is the one tap the whole session had.
  const cardA = UI.renderItem(a, opts);
  const emailTab = cardA.querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Email')[0];
  emailTab.dispatch('click');
  assert.equal(openTab(cardA), 'Email', 'his own tap moved the card he tapped');
  assert.equal(tabs.held.get(UI.surfaceId(a)), 'email', 'and it was remembered against THAT customer');

  // Customer B is drawn fresh. Nothing about A may reach it.
  const cardB = UI.renderItem(b, opts);
  assert.notEqual(openTab(cardB), 'Email', 'B opened on the tab tapped on A — this is D-2');
  assert.equal(openTab(cardB), 'Overview');
});

test('a branch-wide tab is not a card\'s tab', () => {
  // The defect in one line. `renderOpts()` handed `tab` — ONE value per BRANCH — to every
  // card with tabs, so a card for a record the owner had never opened took the tab he had
  // tapped on a different one. Nothing in the renderer may open a card on a value that is
  // not about that card's own record, whoever passes it.
  assert.equal(openTab(UI.renderItem(customer('gid://shopify/Customer/4807', 'Bea'), { tab: 'email' })), 'Overview');
});

test('seven freshly rendered customers open on the tab the task implies', () => {
  // turn_be1b384ca420: seven customers he had never opened, every card on Email. The task
  // named their ORDERS ("has anyone bought today that has bought before"), so the Mac names
  // the intended tab on each card (`data.tab`) and every one of them opens on it.
  const tabs = store();
  const opts = { tabOf: tabs.tabOf, onTab: tabs.onTab };
  const first = customer('gid://shopify/Customer/6343', 'Ada');
  const drawn = UI.renderItem(first, opts);
  drawn.querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Email')[0].dispatch('click');
  assert.equal(openTab(drawn), 'Email');

  const ids = ['6343', '4807', '5015', '4055', '7975', '2855', '8887'];
  const opened = ids.map((id, i) => {
    const item = customer(`gid://shopify/Customer/${id}`, `Customer${i}`);
    item.data.tab = 'orders';                       // what the task implies, from the Mac
    return openTab(UI.renderItem(item, opts));
  });
  assert.deepEqual(opened, ids.map(() => 'Orders'), `seven cards opened on ${opened.join(', ')}`);
});

test('returning to a card the owner left on a tab restores THAT card\'s tab', () => {
  const tabs = store();
  const opts = { tabOf: tabs.tabOf, onTab: tabs.onTab };
  const a = customer('gid://shopify/Customer/6343', 'Ada');
  const b = customer('gid://shopify/Customer/4807', 'Bea');
  UI.renderItem(a, opts).querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Email')[0].dispatch('click');
  UI.renderItem(b, opts).querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Orders')[0].dispatch('click');

  // Back to A: his tab, not B's, and not the first panel either.
  assert.equal(openTab(UI.renderItem(a, opts)), 'Email');
  assert.equal(openTab(UI.renderItem(b, opts)), 'Orders');
});

test('the task\'s tab is only the tab of the card the Mac named it on', () => {
  const tabs = store();
  const opts = { tabOf: tabs.tabOf, onTab: tabs.onTab };
  const named = customer('gid://shopify/Customer/6343', 'Ada');
  named.data.tab = 'email';
  assert.equal(openTab(UI.renderItem(named, opts)), 'Email');
  // The card beside it, from the same turn, was not named: it opens on its own first panel.
  assert.equal(openTab(UI.renderItem(customer('gid://shopify/Customer/4807', 'Bea'), opts)), 'Overview');
});

test('an order card and a customer card do not share a tab either', () => {
  // The same defect one type over: five tabs on an order, three on a customer, one value
  // per branch handed to both.
  const tabs = store();
  const opts = { tabOf: tabs.tabOf, onTab: tabs.onTab };
  const order = { type: 'order', data: { order_id: 'g1', order_number: '#1938', detail: true, total: '£84.00', items: [{ title: 'Hoodie', quantity: 1 }] } };
  const drawn = UI.renderItem(order, opts);
  drawn.querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Shipping')[0].dispatch('click');
  assert.equal(openTab(drawn), 'Shipping');
  assert.equal(openTab(UI.renderItem(customer('gid://shopify/Customer/6343', 'Ada'), opts)), 'Overview');
  // And the order itself comes back on Shipping.
  assert.equal(openTab(UI.renderItem(order, opts)), 'Shipping');
});

// --------------------------------------------------------------------- the patch path

test('a patch does not move the tab the owner is reading', () => {
  const tabs = store();
  const opts = { tabOf: tabs.tabOf, onTab: tabs.onTab };
  const host = deck();
  const one = customer('gid://shopify/Customer/6343', 'Ada');
  UI.applyPatches(host, [patch('add', one)], { opts });
  const node = host.children[0];
  node.querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Orders')[0].dispatch('click');
  assert.equal(openTab(node), 'Orders');

  // The inbox landed and the card says something new. It is rebuilt in place — and the owner
  // is still reading Orders, whatever the payload would have opened.
  const enriched = JSON.parse(JSON.stringify(one));
  enriched.data.tab = 'email';
  enriched.data.related_email = { threads: [{ thread_id: 't2', subject: 'Another one' }] };
  const out = UI.applyPatches(host, [patch('data', enriched)], { opts });
  assert.equal(out.changed, 1);
  assert.equal(host.children.length, 1, 'one card, not two');
  assert.equal(openTab(host.children[0]), 'Orders', 'the patch took him off the tab he was on');
});

test('the tab store is told which record a tap was on, by render identity', () => {
  const seen = [];
  const opts = { tabOf: () => '', onTab: (id, name, label, kind) => seen.push([id, name, label, kind]) };
  const one = customer('gid://shopify/Customer/6343', 'Ada');
  const node = UI.renderItem(one, opts);
  node.querySelectorAll('[role="tab"]').filter((t) => t.textContent.trim() === 'Email')[0].dispatch('click');
  assert.deepEqual(seen[seen.length - 1], ['customer:gid://shopify/Customer/6343', 'email', 'Email', 'customer']);
});

// --------------------------------------------------------------------- §15 / §27
//
// The workspace that says what it IS before it says anything else, and the five states every
// section of it can be in. EMPTY IS NOT ERROR: "no Gmail threads found" keeps the workspace.

const PLAN = {
  type: 'workspace_plan',
  data: {
    workspace_id: 'turn_c8eb4cffe077', title: 'Orders · Inbox', state: 'loading',
    sections: [
      { name: 'orders', label: 'Orders', state: 'loading' },
      { name: 'inbox', label: 'Inbox', state: 'waiting' },
    ],
  },
};

test('the workspace names itself and its sections before any fact arrives', () => {
  const node = UI.renderItem(PLAN, {});
  assert.equal(node.dataset.type, 'workspace_plan');
  assert.equal(node.dataset.state, 'loading');
  const words = node.allText();
  assert.match(words, /Orders/);
  assert.match(words, /Inbox/);
  assert.match(words, /loading/);
  assert.match(words, /waiting/);
  // A state is not a value: there is no number on this card that the Mac has not read.
  assert.ok(!/£|\b\d+\b/.test(words), words);
});

test('a section going from loading to a count patches the card in place', () => {
  const host = deck();
  UI.applyPatches(host, [patch('add', PLAN)]);
  host.scrollTop = 320;
  const ready = JSON.parse(JSON.stringify(PLAN));
  ready.data.state = 'partial';
  ready.data.sections[0] = { name: 'orders', label: 'Orders', state: 'ready', value: '7' };
  const out = UI.applyPatches(host, [patch('data', ready)]);
  assert.equal(out.changed, 1);
  assert.equal(host.children.length, 1, 'the workspace was not duplicated');
  assert.equal(host.scrollTop, 320, 'the owner was 320 px down and he still is');
  assert.match(host.children[0].allText(), /7/);
  assert.equal(host.children[0].dataset.state, 'partial');
});

test('an empty section keeps its workspace and is not an error', () => {
  const empty = JSON.parse(JSON.stringify(PLAN));
  empty.data.state = 'partial';
  empty.data.sections = [
    { name: 'orders', label: 'Orders', state: 'ready', value: '7' },
    { name: 'inbox', label: 'Inbox', state: 'empty', note: 'No messages found' },
  ];
  const node = UI.renderItem(empty, {});
  const rows = node.querySelectorAll('.row');
  assert.equal(rows.length, 2, 'the workspace still has both sections');
  const inbox = rows.filter((r) => r.dataset.section === 'inbox')[0];
  assert.equal(inbox.dataset.state, 'empty');
  assert.notEqual(inbox.dataset.state, 'error');
  assert.match(inbox.allText(), /No messages found/);
  assert.match(node.allText(), /Orders/, 'and the section that did land is still on it');
});

test('an errored section does not kill its neighbours', () => {
  const mixed = JSON.parse(JSON.stringify(PLAN));
  mixed.data.state = 'partial';
  mixed.data.sections = [
    { name: 'orders', label: 'Orders', state: 'ready', value: '7' },
    { name: 'inbox', label: 'Inbox', state: 'error', note: 'Gmail did not answer' },
  ];
  const node = UI.renderItem(mixed, {});
  const rows = node.querySelectorAll('.row');
  assert.deepEqual(rows.map((r) => r.dataset.state), ['ready', 'error']);
  assert.match(rows[0].allText(), /7/, 'the section that landed still says what it found');
  assert.match(rows[1].allText(), /Gmail did not answer/);
  // The workspace as a whole is not an error because one section is.
  assert.equal(node.dataset.state, 'partial');
});

test('the same workspace patched seven times is drawn once', () => {
  // D-8. `turn_f0628fcf7be5` drew order_list + working_set + folded SEVEN times, #2..#7 at
  // 0.0 s apart, and each redraw cost the scroll position while he was scrolling.
  const host = deck();
  const one = patch('add', PLAN);
  for (let i = 0; i < 7; i++) UI.applyPatches(host, [one]);
  assert.equal(host.querySelectorAll('[data-type="workspace_plan"]').length, 1);
  assert.equal(host.children.length, 1);
});
