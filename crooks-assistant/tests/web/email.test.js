/* The email workspace, the rail that leads into it, and the typing path — in the renderer.
 *
 * These are the tablet's half of D-9 and D-11. Run with the rest: node --test tests/web/*.js
 *
 *   D-11  Eight rail actions rendered enabled and none was ever used. A chip that only puts
 *         words in the owner's mouth is not a control, and a disabled chip beside an enabled
 *         one at the same weight is noise. So: a rail has at most two chips at full weight,
 *         the rest are behind a disclosure, an "open" chip carries the command it posts, and
 *         a disabled chip shows its reason.
 *   D-9   The composer had fields and nothing said so. Every field now carries a visible
 *         affordance, a reply shows who it is to before a word is typed, and what the thumb
 *         has typed survives a redraw the owner did not ask for.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
globalThis.document = shim.document;
const UI = require(path.join(__dirname, '..', '..', 'web', 'ui.js'));

const THREAD = 'aa70d3f83dbef06e';
const textOf = (node) => node.allText();

// The rail as the Mac now sends it (app/actions/available.py).
const REPLY = {
  id: 'reply', label: 'Reply', operation: 'gmail_draft_reply', risk: 'amber', enabled: true,
  reason: '', instruction: 'Reply to this email', mode: 'open', family: 'email.reply',
  command: 'compose.reply', args: `thread_id=${THREAD}`, priority: 'primary', detail: '',
};
const ARCHIVE = {
  id: 'email_archive', label: 'Archive', operation: 'gmail_thread_archive', risk: 'amber',
  enabled: true, reason: '', instruction: '', mode: 'stage', family: '', command: '', args: '',
  priority: 'primary', detail: 'Takes the thread out of the inbox.',
};
const NOTE = {
  id: 'note', label: 'Note', operation: 'order_note_append', risk: 'amber', enabled: true,
  reason: '', instruction: 'Add a note to 1938', mode: 'ask', family: 'order.add_note',
  command: '', args: '', priority: 'secondary', detail: '',
};
const DEAD_FULFIL = {
  id: 'fulfil', label: 'Fulfil', operation: 'fulfillment_create', risk: 'red', enabled: false,
  reason: 'already shipped', instruction: 'Fulfil order 1938', mode: 'ask', family: '',
  command: '', args: '', priority: 'secondary', detail: '',
};

function thread(patch) {
  return UI.renderItem({
    type: 'email_thread',
    data: Object.assign({
      thread_id: THREAD, subject: 'Order 1938 — can I change the size?', message_count: 2,
      messages: [
        { from: 'Crooks', from_email: 'orders@crooksldn.com', body: 'Thanks for your order.', date: '' },
        { from: 'Mia Fenwick', from_email: 'mia@example.com', body: 'Can I change the size?', date: '' },
      ],
      actions: [REPLY, ARCHIVE],
      link_confidence: 'confident',
      linked_order: { order_id: 'gid://shopify/Order/1938', order_number: '#1938', total: '£84.00', fulfillment: 'unfulfilled' },
      link_provenance: ['the number is in the subject'],
    }, patch || {}),
  }, {});
}

/* ------------------------------------------------------------------ §22 the rail */

test('a rail keeps two chips at full weight and puts the rest behind a disclosure', () => {
  const node = thread({ actions: [REPLY, ARCHIVE, NOTE, DEAD_FULFIL] });
  const rail = node.querySelectorAll('.rail')[0];
  assert.ok(rail, 'the thread has a rail');
  const primary = rail.querySelectorAll('.rail-primary')[0];
  assert.deepEqual(primary.querySelectorAll('.rail-chip').map((c) => c.dataset.action), ['reply', 'email_archive']);
  const more = rail.querySelectorAll('.rail-more')[0];
  assert.ok(more, 'the rest are disclosed, not dumped');
  assert.equal(more.getAttribute('aria-expanded'), 'false');
  const rest = rail.querySelectorAll('.rail-rest')[0];
  assert.equal(rest.hidden, true, 'closed until asked for');
  assert.deepEqual(rest.querySelectorAll('.rail-chip').map((c) => c.dataset.action), ['note', 'fulfil']);
  assert.match(textOf(more), /2 more/);
  more.dispatch('click');
  assert.equal(rest.hidden, false);
  assert.equal(more.getAttribute('aria-expanded'), 'true');
});

test('a rail of two or fewer draws no disclosure at all', () => {
  const rail = thread().querySelectorAll('.rail')[0];
  assert.equal(rail.querySelectorAll('.rail-more').length, 0);
  assert.equal(rail.querySelectorAll('.rail-chip').length, 2);
});

test('an open chip posts the command the Mac put on it and nothing else', () => {
  const chip = thread().querySelectorAll('.rail-chip')[0];
  assert.equal(chip.dataset.action, 'reply');
  assert.equal(chip.dataset.mode, 'open');
  assert.equal(chip.dataset.command, 'compose.reply');
  assert.equal(chip.dataset.args, `thread_id=${THREAD}`);
  // Not an argument of a change anywhere on it.
  for (const forbidden of ['body=', 'to=', 'subject=', 'mia@example.com']) {
    assert.ok(String(chip.dataset.args).indexOf(forbidden) === -1, forbidden);
  }
});

test('a disabled chip says why, and is never at the same weight as a live one', () => {
  const node = thread({ actions: [REPLY, ARCHIVE, DEAD_FULFIL] });
  const rest = node.querySelectorAll('.rail-rest')[0];
  const dead = rest.querySelectorAll('.rail-chip')[0];
  assert.equal(dead.dataset.action, 'fulfil');
  assert.equal(dead.getAttribute('aria-disabled'), 'true');
  assert.equal(textOf(dead.querySelectorAll('.rail-why')[0]), 'already shipped');
  assert.ok(dead.classList.contains('is-off'));
  // And it does nothing at all when pressed.
  let asked = 0;
  const again = UI.renderItem({ type: 'email_thread', data: { thread_id: THREAD, messages: [], actions: [DEAD_FULFIL] } },
                              { onAction: () => { asked += 1; } });
  again.querySelectorAll('.rail-chip')[0].dispatch('click');
  assert.equal(asked, 0);
});

test('an ask chip still primes the words, so nothing that worked stopped working', () => {
  const asked = [];
  const node = UI.renderItem({ type: 'email_thread', data: { thread_id: THREAD, messages: [], actions: [NOTE] } },
                             { onAction: (a) => asked.push(a.id) });
  node.querySelectorAll('.rail-chip')[0].dispatch('click');
  assert.deepEqual(asked, ['note']);
});

test('a stage chip prepares the change and says it is preparing', () => {
  const staged = [];
  const node = UI.renderItem({ type: 'email_thread', data: { thread_id: THREAD, messages: [], actions: [ARCHIVE] } },
                             { onRowAction: (id, ref) => staged.push([id, ref]) });
  node.querySelectorAll('.rail-chip')[0].dispatch('click', { stopPropagation() {} });
  assert.deepEqual(staged, [['email_archive', THREAD]]);
});

/* ------------------------------------------------------- §19 the relations, both ways */

test('a thread says which order it is about, tappably', () => {
  const strip = thread().querySelectorAll('.link-strip')[0];
  assert.equal(strip.dataset.kind, 'order');
  assert.equal(strip.dataset.ref, 'gid://shopify/Order/1938');
  assert.equal(strip.getAttribute('role'), 'button');
});

test('an order says which email is about it, tappably — the other direction', () => {
  const order = UI.renderItem({
    type: 'order',
    data: {
      order_id: 'gid://shopify/Order/1938', order_number: '#1938', detail: true, items: [],
      email: { threads: [{ thread_id: THREAD, subject: 'Can I change the size?', from: 'Mia', snippet: 'a size', date: '', sender_match: true }] },
    },
  }, {});
  const row = order.querySelectorAll('.mail')[0].querySelectorAll('.row')[0];
  assert.equal(row.dataset.kind, 'email_thread', 'the order card could not be tapped into the thread');
  assert.equal(row.dataset.ref, THREAD);
  assert.ok(row.classList.contains('tappable'));
  assert.ok(row.querySelectorAll('.row-go').length, 'and it looks tappable');
});

/* -------------------------------------------------- §19 the reply, as a card with fields */

const REPLY_COMPOSER = {
  compose_id: 'cmp_ab12cd34ef', kind: 'reply', thread_id: THREAD,
  to: { value: 'mia@example.com', status: 'ok', hint: '', editable: false },
  to_name: 'Mia Fenwick',
  subject: { value: 'Re: Order 1938', status: 'ok', editable: false },
  body: { value: '', status: 'uncertain', placeholder: 'type the reply', editable: true },
  about: 'a reply to Mia', how: 'Tap the box to type, or hold the dock and say it.',
  actions: [
    { id: 'dictate', label: 'Dictate', command: 'voice.bind', args: `family=email.reply&kind=email_thread&ref=${THREAD}` },
    { id: 'save_draft', label: 'Save draft', mode: 'stage', command: 'compose.stage', args: 'compose_id=cmp_ab12cd34ef&mode=draft' },
    { id: 'send', label: 'Send', mode: 'stage', risk: 'red', command: 'compose.stage', args: 'compose_id=cmp_ab12cd34ef&mode=send' },
    { id: 'discard', label: 'Cancel', command: 'compose.discard', args: 'compose_id=cmp_ab12cd34ef' },
  ],
};

function replyComposer(patch) {
  return UI.renderItem({ type: 'email_compose', data: Object.assign({}, REPLY_COMPOSER, patch || {}) }, {});
}

test('the reply card says who it is to and what it is about before a word is typed', () => {
  const node = replyComposer();
  assert.match(textOf(node), /Mia Fenwick/);
  assert.match(textOf(node), /mia@example\.com/);
  assert.match(textOf(node), /Re: Order 1938/);
  // Shown, and not editable: a reply's recipient is the thread's and the Mac reads it there.
  const statics = node.querySelectorAll('.field-static');
  assert.deepEqual(statics.map((s) => s.dataset.field), ['to', 'subject']);
  assert.deepEqual(node.querySelectorAll('.field-input').map((f) => f.dataset.field), ['body']);
});

test('the reply card says how to put words in it, which nothing did', () => {
  assert.match(textOf(replyComposer()), /Tap the box to type/);
});

test('every button on the composer carries the command the Mac chose for it', () => {
  const buttons = replyComposer().querySelectorAll('.compose-btn');
  assert.deepEqual(buttons.map((b) => [b.dataset.action, b.dataset.command]), [
    ['dictate', 'voice.bind'],
    ['save_draft', 'compose.stage'],
    ['send', 'compose.stage'],
    ['discard', 'compose.discard'],
  ]);
  assert.equal(buttons[0].dataset.args, `family=email.reply&kind=email_thread&ref=${THREAD}`);
  assert.equal(buttons[2].dataset.args, 'compose_id=cmp_ab12cd34ef&mode=send');
  assert.ok(buttons[2].classList.contains('risk-red'));
  for (const b of buttons) {
    assert.ok(!/body=|subject=|to=/.test(String(b.dataset.args)), `${b.dataset.action} carries the email`);
  }
});

test('a composer with no command on its buttons still stages, so an older card works', () => {
  const node = replyComposer({ actions: [{ id: 'send', label: 'Send', mode: 'stage' }, { id: 'discard', label: 'Discard' }] });
  const buttons = node.querySelectorAll('.compose-btn');
  assert.deepEqual(buttons.map((b) => [b.dataset.command, b.dataset.args]), [
    ['compose.stage', 'compose_id=cmp_ab12cd34ef&mode=send'],
    ['compose.discard', 'compose_id=cmp_ab12cd34ef'],
  ]);
});

/* --------------------------------------------------------- §20 finding the keyboard */

test('every field says it can be typed into, in a word a finger can see', () => {
  for (const kind of ['email', 'address', 'sku', 'tracking', 'quantity', 'code', 'money', 'text']) {
    const wrap = UI.field({ kind, name: 'x', label: 'X', compose_id: 'cmp_1' }, {});
    assert.equal(wrap.dataset.typable, 'true', kind);
    const mark = wrap.querySelectorAll('.field-type')[0];
    assert.ok(mark, `${kind} has no typing affordance`);
    assert.match(textOf(mark), /type/i, kind);
  }
});

test('a field nobody has typed in yet says what to do, once, and not twice', () => {
  const empty = UI.field({ kind: 'sku', name: 'sku', label: 'SKU', value: '', compose_id: 'cmp_1' }, {});
  assert.equal(empty.querySelectorAll('.field-type').length, 1);
  const full = UI.field({ kind: 'sku', name: 'sku', label: 'SKU', value: 'CRK-001', compose_id: 'cmp_1' }, {});
  assert.equal(full.querySelectorAll('.field-type').length, 1, 'the affordance is on the label, always');
});

/* ------------------------------------------- §20 what was typed survives a redraw */

test('a redraw the owner did not ask for keeps what the thumb has typed', () => {
  UI.clearFieldDrafts();
  const spec = { kind: 'address', name: 'address', label: 'Ships to', value: 'old line', compose_id: 'cmp_9' };
  const first = UI.field(spec, { onField: () => {} });
  const input = first.querySelectorAll('.field-input')[0];
  input.value = '12 Somewhere Street, Windsor';
  input.dispatch('input');
  // A background enrichment lands and the card is drawn again from the Mac's OLDER copy.
  const again = UI.field(spec, {});
  assert.equal(again.querySelectorAll('.field-input')[0].value, '12 Somewhere Street, Windsor');
  assert.equal(again.dataset.unsaved, 'true', 'and it says the Mac has not got it yet');
});

test('once the Mac has the value, the draft is gone and the Mac is the authority again', () => {
  UI.clearFieldDrafts();
  const input = UI.field({ kind: 'sku', name: 'sku', value: '', compose_id: 'cmp_9' }, {}).querySelectorAll('.field-input')[0];
  input.value = 'CRK-001';
  input.dispatch('input');
  const confirmed = UI.field({ kind: 'sku', name: 'sku', value: 'CRK-001', compose_id: 'cmp_9' }, {});
  assert.equal(confirmed.dataset.unsaved, undefined);
  // And a later value from the Mac — a rewrite it did itself — is now shown, not suppressed.
  const rewritten = UI.field({ kind: 'sku', name: 'sku', value: 'CRK-002', compose_id: 'cmp_9' }, {});
  assert.equal(rewritten.querySelectorAll('.field-input')[0].value, 'CRK-002');
});

test('one field\'s draft is never another field\'s, or another card\'s', () => {
  UI.clearFieldDrafts();
  const a = UI.field({ kind: 'sku', name: 'sku', value: '', compose_id: 'cmp_a' }, {}).querySelectorAll('.field-input')[0];
  a.value = 'AAA';
  a.dispatch('input');
  assert.equal(UI.field({ kind: 'sku', name: 'sku', value: '', compose_id: 'cmp_b' }, {}).querySelectorAll('.field-input')[0].value, '');
  assert.equal(UI.field({ kind: 'sku', name: 'other', value: '', compose_id: 'cmp_a' }, {}).querySelectorAll('.field-input')[0].value, '');
});

test('a draft older than a round trip is not resurrected onto a card hours later', () => {
  UI.clearFieldDrafts();
  const input = UI.field({ kind: 'sku', name: 'sku', value: '', compose_id: 'cmp_9' }, {}).querySelectorAll('.field-input')[0];
  input.value = 'CRK-001';
  input.dispatch('input');
  UI.ageFieldDrafts(UI.FIELD_DRAFT_TTL_MS + 1000);
  assert.equal(UI.field({ kind: 'sku', name: 'sku', value: '', compose_id: 'cmp_9' }, {}).querySelectorAll('.field-input')[0].value, '');
});

/* -------------------------------------- §19 a proven archive leaves the active queue */

test('a proven archive marks the thread and takes it out of the queue on screen', () => {
  const deck = UI.h('div', {});
  const queue = UI.renderItem({
    type: 'email_list',
    data: { title: 'Waiting on a reply', count: 2, threads: [
      { thread_id: THREAD, from: 'Mia', subject: 'Can I change the size?', snippet: '', date: '' },
      { thread_id: 'bbbb', from: 'Sam', subject: 'Where is it?', snippet: '', date: '' },
    ] },
  }, {});
  const open = thread();
  deck.appendChild(queue);
  deck.appendChild(open);
  assert.equal(queue.querySelectorAll('.row').length, 2);

  UI.settleThread(deck, { archived: { kind: 'email_thread', ref: THREAD } });

  assert.deepEqual(queue.querySelectorAll('.row').map((r) => r.dataset.ref), ['bbbb'],
                   'the archived thread stayed in the queue');
  assert.match(textOf(queue.querySelectorAll('.queue-note')[0]), /1 archived/);
  assert.ok(open.classList.contains('is-archived'));
  assert.match(textOf(open.querySelectorAll('.card-head')[0]), /Archived/);
  // Archiving is reversible, and the undo has to be able to undo the screen too.
  UI.settleThread(deck, { restored: { kind: 'email_thread', ref: THREAD } });
  assert.ok(!open.classList.contains('is-archived'));
});

test('a success card that names an archived thread settles the deck it lands in', () => {
  const node = UI.renderItem({
    type: 'success',
    data: { title: 'Archived', detail: 'thread', proposal_id: 'prop_1',
            archived: { kind: 'email_thread', ref: THREAD } },
  }, {});
  assert.ok(node, 'the success card still renders');
  assert.equal(node.dataset.archived, THREAD, 'and says which thread, for the deck to settle');
});

test('settling a thread nobody drew changes nothing and throws nothing', () => {
  const deck = UI.h('div', {});
  UI.settleThread(deck, { archived: { kind: 'email_thread', ref: 'nothing' } });
  UI.settleThread(null, { archived: { kind: 'email_thread', ref: THREAD } });
  UI.settleThread(deck, {});
  assert.equal(deck.querySelectorAll('.row').length, 0);
});
