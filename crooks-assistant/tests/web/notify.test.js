/* The notification architecture (web/notify.js), under Node.
 *
 * Every assertion here is one of the rules the live tablet session earned:
 *
 *   - three classes, and the placement is a consequence of the class, not an offset
 *   - a message about the machine itself is the ONLY thing allowed above every screen, and
 *     asking to be global is not enough to be global
 *   - a message about one half is that half's, and disappears with it rather than being
 *     drawn over the other one — which is what "Merged. 2 changes still waiting over there."
 *     did on 11 September at 00:24:53
 *   - the same thing said twice is one row and a count
 *   - a failure stays until it is dismissed; a low-risk success goes on its own
 *   - a message stacks predictably and is capped, so a run of them cannot take the screen
 *   - a message is never a way to get anywhere: Dismiss is the only control it may carry
 *
 * And the policy the session earned but Phase 4 did not write (D-10 · §10). Sixteen
 * notifications, ELEVEN of them carrying no code at all and five saying `divided`/`merged`:
 *
 *   - a message with no words, or with no letter or digit in it, is refused
 *   - a message with no NAME is refused — that is the eleven
 *   - a state change the screen already shows is refused — that is the five
 *   - a state the control already carries is refused: "Draft saved" belongs on Save draft
 *   - at most MAX_TRANSIENT messages that leave on their own, across all three hosts
 *   - at most MAX_GOOD of those may be a success: one event, one "done"
 *   - every refusal is RECORDED, because a silence is not a policy
 *
 * SOME CODES IN THE TESTS BELOW CHANGED with that policy, and only for that reason: four
 * placement/lifetime tests used `code: 'draft_saved'` and two used `code: 'divided'` or
 * `'merged'` as convenient stand-ins, and those exact codes are now refused by name. The
 * assertion in each is unchanged; the message it is made about is one the policy allows.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
const N = require(path.join(__dirname, '..', '..', 'web', 'notify.js'));

function screen(mode) {
  const doc = shim.document;
  const hosts = {
    global: doc.createElement('div'),
    orbWorkspace: doc.createElement('div'),
    deckWorkspace: doc.createElement('div'),
  };
  hosts.global.id = 'notes-global';
  hosts.orbWorkspace.id = 'notes-orb';
  hosts.deckWorkspace.id = 'notes-deck';
  for (const host of Object.values(hosts)) host.hidden = true;
  const recorded = [];
  N.reset();
  N.init({
    document: doc,
    global: hosts.global, orbWorkspace: hosts.orbWorkspace, deckWorkspace: hosts.deckWorkspace,
    mode: () => mode || 'context',
    record: (kind, fields) => recorded.push({ kind, fields }),
  });
  return { hosts, recorded, doc };
}

const rows = (host) => host.children.filter((n) => n.className.split(' ').indexOf('note') !== -1);
const words = (row) => row.childNodes.filter((n) => n.className === 'note-words').map((n) => n.textContent)[0] || '';
const button = (row) => row.childNodes.find((n) => n.className === 'note-dismiss') || null;

test('a workspace message is drawn in the workspace, and nowhere else', () => {
  const { hosts } = screen('context');
  N.show({ text: 'The refund was proved on the store.', class: 'workspace', tone: 'good', code: 'refund_proved' });
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(rows(hosts.global).length, 0);
  assert.equal(rows(hosts.orbWorkspace).length, 0);
  assert.equal(hosts.deckWorkspace.hidden, false, 'the region shows itself when it has something to say');
  assert.equal(words(rows(hosts.deckWorkspace)[0]), 'The refund was proved on the store.');
});

test('the same message on the orb screen goes under the caption instead', () => {
  const { hosts } = screen('orb');
  N.show({ text: 'This half has nothing yet. Ask it something.', class: 'workspace', code: 'half_empty' });
  assert.equal(rows(hosts.orbWorkspace).length, 1);
  assert.equal(rows(hosts.deckWorkspace).length, 0);
});

test('only the machine\'s own state may be global; anything else that asks becomes workspace', () => {
  const { hosts } = screen('context');
  N.show({ text: 'The Mac cannot be reached.', class: 'global', tone: 'bad', code: 'backend_down', machine: true });
  assert.equal(rows(hosts.global).length, 1);
  // No `machine: true`: a message that merely wants to be seen everywhere does not get to be.
  const demoted = N.show({ text: 'Refund verified.', class: 'global', tone: 'good', code: 'refund_verified' });
  assert.equal(demoted.class, 'workspace');
  assert.equal(rows(hosts.global).length, 1, 'the global region still holds one message');
  assert.equal(rows(hosts.deckWorkspace).length, 1);
});

test('a control-local message is drawn directly after its control, inside the card', () => {
  const { hosts, doc } = screen('context');
  const card = doc.createElement('article');
  const rail = doc.createElement('div');
  const chip = doc.createElement('button');
  const after = doc.createElement('p');
  rail.appendChild(chip);
  rail.appendChild(after);
  card.appendChild(rail);
  N.show({ text: 'That does not look like an email address.', class: 'control', tone: 'bad', code: 'invalid_email', host: rail, after: chip });
  assert.equal(rail.children.length, 3);
  assert.equal(rail.children[0], chip, 'the control stays where it was');
  assert.equal(rail.children[1].className.indexOf('note note-control'), 0, 'the message sits directly after it');
  assert.equal(rail.children[2], after, 'and everything after it keeps its place');
  assert.equal(rows(hosts.deckWorkspace).length, 0, 'nothing went to the workspace');
});

test('a message about one half is hidden while the other half is focused, and comes back', () => {
  const { hosts } = screen('context');
  N.show({ text: '2 changes came back still waiting for you.', class: 'workspace', tone: 'warn', code: 'merge_waiting', branch: 'br_first' });
  N.focusBranch('br_first');
  assert.equal(rows(hosts.deckWorkspace)[0].hidden, false);
  N.focusBranch('br_second');
  assert.equal(rows(hosts.deckWorkspace)[0].hidden, true, 'not drawn over the other half');
  assert.equal(hosts.deckWorkspace.hidden, true, 'and the region goes with it');
  assert.equal(N.list()[0].shown, false, 'it is still there, and says it is not on screen');
  N.focusBranch('br_first');
  assert.equal(rows(hosts.deckWorkspace)[0].hidden, false, 'and it is back when its half is');
});

test('a message with no half is shown whichever half is focused', () => {
  const { hosts } = screen('context');
  N.show({ text: 'Nothing is saved until you tap.', class: 'workspace', code: 'reminder' });
  N.focusBranch('br_second');
  assert.equal(rows(hosts.deckWorkspace)[0].hidden, false);
});

test('the same thing said twice is one row with a count', () => {
  const { hosts, recorded } = screen('context');
  const first = N.show({ text: 'The Mac did not answer.', class: 'workspace', tone: 'bad', code: 'silent' });
  const again = N.show({ text: 'The Mac did not answer.', class: 'workspace', tone: 'bad', code: 'silent' });
  assert.equal(again, first, 'the same entry, refreshed');
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(N.list()[0].repeats, 2);
  const count = rows(hosts.deckWorkspace)[0].childNodes.find((n) => n.className === 'note-count');
  assert.equal(count.textContent, '×2');
  assert.equal(count.hidden, false);
  assert.deepEqual(recorded.map((r) => r.fields.repeat), [undefined, 2]);
  // A different message is a different row.
  N.show({ text: 'That could not be applied.', class: 'workspace', tone: 'bad', code: 'refused' });
  assert.equal(rows(hosts.deckWorkspace).length, 2);
});

test('a failure persists and carries Dismiss; a success goes on its own and carries none', () => {
  const { hosts } = screen('context');
  const bad = N.show({ text: 'Archive failed on the Mac.', class: 'workspace', tone: 'bad', code: 'archive_failed' });
  const good = N.show({ text: 'The refund was proved.', class: 'workspace', tone: 'good', code: 'refund_proved' });
  assert.equal(bad.ttl, 0, 'a failure waits to be read');
  assert.ok(good.ttl > 0 && good.ttl <= 5000, `a low-risk success goes: ${good.ttl}`);
  assert.ok(button(bad.node), 'the failure can be dismissed');
  assert.equal(button(good.node), null, 'the one that leaves on its own needs no button');
  // And Dismiss is the ONLY control a message may carry: a transient line must never become
  // a way to get somewhere, because the screen it would go to may already be gone.
  for (const row of rows(hosts.deckWorkspace)) {
    const controls = row.childNodes.filter((n) => n.tagName === 'BUTTON' || n.tagName === 'A');
    for (const control of controls) assert.equal(control.className, 'note-dismiss', `only Dismiss: ${control.className}`);
  }
  assert.equal(N.dismiss(bad.id), true);
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(N.list().length, 1);
});

test('a warning persists only as long as it is worth, and an explicit persist overrides the tone', () => {
  screen('context');
  const warn = N.show({ text: 'Two changes are still waiting.', class: 'workspace', tone: 'warn', code: 'waiting' });
  assert.ok(warn.ttl > 5000, `a warning is given time to be read: ${warn.ttl}`);
  const kept = N.show({ text: 'The refund was proved.', class: 'workspace', tone: 'good', code: 'refund_proved', persist: true });
  assert.equal(kept.ttl, 0);
  assert.ok(button(kept.node), 'and so it can be dismissed');
});

test('messages stack in the order they arrived, and the region is capped', () => {
  const { hosts } = screen('context');
  for (const n of [1, 2, 3, 4, 5]) N.show({ text: `Message ${n}`, class: 'workspace', tone: 'bad', code: `m${n}` });
  const shown = rows(hosts.deckWorkspace).map(words);
  assert.equal(shown.length, N.MAX_PER_HOST, `capped at ${N.MAX_PER_HOST}`);
  assert.deepEqual(shown, ['Message 3', 'Message 4', 'Message 5'], 'the oldest go, the order holds');
});

test('a mode change moves the workspace messages to the host that is on screen', () => {
  const doc = shim.document;
  const hosts = {
    global: doc.createElement('div'), orbWorkspace: doc.createElement('div'), deckWorkspace: doc.createElement('div'),
  };
  let mode = 'orb';
  N.reset();
  N.init({ document: doc, global: hosts.global, orbWorkspace: hosts.orbWorkspace, deckWorkspace: hosts.deckWorkspace, mode: () => mode });
  N.show({ text: 'This half has nothing yet. Ask it something.', class: 'workspace', tone: 'info', code: 'half_empty' });
  assert.equal(rows(hosts.orbWorkspace).length, 1);
  mode = 'context';
  N.remode();
  assert.equal(rows(hosts.orbWorkspace).length, 0);
  assert.equal(rows(hosts.deckWorkspace).length, 1);
});

test('every message says what it is in a word as well as in a colour', () => {
  const { hosts } = screen('context');
  for (const [tone, word] of [['info', 'Note'], ['good', 'Done'], ['warn', 'Check'], ['bad', 'Failed']]) {
    N.clear({});
    N.show({ text: `A ${tone} message`, class: 'workspace', tone, code: tone });
    const row = rows(hosts.deckWorkspace)[0];
    const mark = row.childNodes.find((n) => n.className === 'note-mark');
    assert.equal(mark.textContent, word, `${tone} says "${word}"`);
    assert.equal(row.dataset.tone, tone);
  }
});

test('an unknown class and an unknown tone fall back rather than throwing', () => {
  const { hosts } = screen('context');
  const odd = N.show({ text: 'Something happened.', class: 'shout', tone: 'magenta', code: 'odd' });
  assert.equal(odd.class, 'workspace');
  assert.equal(odd.tone, 'info');
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(N.show({ text: '   ', code: 'odd' }), null, 'nothing to say is not a message');
  assert.equal(N.show({}), null);
});

test('clear takes what it is asked for and can be told to keep the failures', () => {
  const { hosts } = screen('context');
  N.show({ text: 'The refund was proved.', class: 'workspace', tone: 'good', code: 'refund_proved' });
  N.show({ text: 'Archive failed.', class: 'workspace', tone: 'bad', code: 'archive_failed' });
  N.clear({ keepFailures: true });
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(N.list()[0].code, 'archive_failed');
  N.clear({});
  assert.equal(N.list().length, 0);
  assert.equal(hosts.deckWorkspace.hidden, true);
});

test('with nowhere to draw, a message is not drawn and nothing throws', () => {
  N.reset();
  N.init({ document: shim.document });
  assert.equal(N.show({ text: 'Nowhere to say this.', class: 'workspace', code: 'nowhere' }), null);
  assert.equal(N.list().length, 0);
  N.reset();
  assert.equal(N.show({ text: 'Not started yet.', code: 'not_started' }), null);
});

test('what it records is controlled vocabulary: a class, a code, a tone — never the words', () => {
  const { recorded } = screen('context');
  N.show({ text: 'Alexandra Featherstonehaugh was emailed.', class: 'workspace', tone: 'good', code: 'emailed', branch: 'br_a' });
  assert.equal(recorded.length, 1);
  assert.equal(recorded[0].kind, 'notify');
  assert.deepEqual(recorded[0].fields, { name: 'workspace', code: 'emailed', tone: 'good', branch: 'br_a', persists: false });
  assert.ok(!/Alexandra|Featherstonehaugh/.test(JSON.stringify(recorded)), 'nothing a message said is recorded');
});


/* ======================================================================================
 * D-10 · §10 — THE POLICY. Sixteen notifications in the live tablet session, and every one
 * of them noise. Each test below names the event it makes impossible.
 * ==================================================================================== */

test('a notification with no words is not a notification, and the refusal is recorded', () => {
  const { hosts, recorded } = screen('context');
  // The eleven. Each was a sentence the page had, or thought it had, and nothing else. The
  // ones that arrived with an empty server field arrived with no words at all.
  for (const nothing of [undefined, null, '', '   ', '\n\t ']) {
    assert.equal(N.show({ text: nothing, class: 'workspace', code: 'empty' }), null, JSON.stringify(nothing));
  }
  // And a row whose only content is punctuation is the empty notification with a character
  // in it. A word has a letter or a digit in it or it is not a word.
  for (const notWords of ['—', '.', '…', '?!', '- -', '***']) {
    assert.equal(N.show({ text: notWords, class: 'workspace', code: 'empty' }), null, notWords);
  }
  assert.equal(N.list().length, 0);
  assert.equal(rows(hosts.deckWorkspace).length, 0);
  assert.equal(hosts.deckWorkspace.hidden, true);
  // Eleven of these went unnoticed for a whole evening because dropping a message silently
  // is indistinguishable from not having a policy.
  assert.equal(recorded.length, 11, 'every refusal is an event');
  assert.ok(recorded.every((r) => r.kind === 'notify_refused' && r.fields.reason === 'no_words'), JSON.stringify(recorded));
  assert.ok(!/—|\.\.\.|…/.test(JSON.stringify(recorded)), 'and the refusal does not record the words either');
});

test('a message the system cannot NAME is refused: that is the eleven', () => {
  const { hosts, recorded } = screen('context');
  // Eleven of the sixteen `tablet_notify` events in the session carried no code, so the
  // recorded event was `{name:"workspace", tone:"info"}`. Eleven messages nobody can
  // deduplicate, test, or be held to.
  assert.equal(N.show({ text: 'Something went wrong somewhere.', class: 'workspace' }), null);
  assert.equal(N.show({ text: 'Something went wrong somewhere.', class: 'workspace', code: '' }), null);
  assert.equal(N.show({ text: 'Something went wrong somewhere.', class: 'workspace', code: '  ' }), null);
  assert.deepEqual(recorded.map((r) => r.fields.reason), ['no_code', 'no_code', 'no_code']);
  // A name in the shape every other name on this tablet has. Not a sentence, not SHOUTING,
  // not a path: the code is what telemetry and the policy both match on.
  for (const bad of ['Draft Saved', 'draft saved', 'DRAFT_SAVED', '2_fast', 'a-b', 'a.b', 'a/b']) {
    assert.equal(N.show({ text: 'A message.', class: 'workspace', code: bad }), null, bad);
    assert.equal(N.check({ text: 'A message.', code: bad }).reason, 'bad_code', bad);
  }
  assert.equal(rows(hosts.deckWorkspace).length, 0);
  // And a well-formed name is drawn.
  assert.ok(N.show({ text: 'A message.', class: 'workspace', code: 'a_message' }));
  assert.equal(rows(hosts.deckWorkspace).length, 1);
});

test('divided, merged, opened and a changed tab produce NO notification at all', () => {
  const { hosts, recorded } = screen('context');
  // The five that carried text: divided, merged, divided, merged, divided. The screen had
  // just visibly become two halves, or one orb. §10 — a state change updates THE PLACE THE
  // STATE ALREADY LIVES, and there is nothing left for a message to add.
  const said = [
    ['divided', 'Divided. Tap a half to talk to it; the other keeps working.'],
    ['merged', 'Merged. 2 things it looked at came back.'],
    ['split', 'Split.'],
    ['closed', 'That half is closed.'],
    ['opened', 'Order #1962 is open.'],
    ['order_opened', 'Order #1962 is open.'],
    ['tab', 'Now showing Orders.'],
    ['tab_changed', 'Now showing Orders.'],
    ['navigated', 'Back at the assistant.'],
    ['home', 'Back at the assistant.'],
    ['back', 'Back.'],
    ['next', 'The next one.'],
  ];
  for (const [code, text] of said) {
    assert.equal(N.show({ text, class: 'workspace', tone: 'good', code }), null, code);
    // Nor by asking to be global, which is how a message with no home gets a home.
    assert.equal(N.show({ text, class: 'global', machine: true, tone: 'good', code }), null, code);
    // Nor beside a control.
    assert.equal(N.show({ text, class: 'control', tone: 'good', code, host: hosts.deckWorkspace }), null, code);
  }
  assert.equal(N.list().length, 0);
  assert.equal(rows(hosts.global).length + rows(hosts.orbWorkspace).length + rows(hosts.deckWorkspace).length, 0);
  assert.ok(recorded.every((r) => r.fields.reason === 'screen_shows'), JSON.stringify(recorded.slice(0, 3)));
  assert.equal(recorded.length, said.length * 3);
});

test('a draft save updates the control, not a toast', () => {
  const { hosts, recorded } = screen('context');
  // §10, first example. Save draft is an action surface: it goes to `executed` and its own
  // label becomes the outcome (web/action-state.js). A line in the workspace saying the same
  // thing is a second claim about one event, in the worse of the two places — 788px from the
  // thumb that tapped it, and gone in four seconds.
  assert.equal(N.show({ text: 'Draft saved in Gmail drafts.', class: 'workspace', tone: 'good', code: 'draft_saved' }), null);
  assert.equal(N.show({ text: 'Saved.', class: 'workspace', tone: 'good', code: 'saved' }), null);
  assert.equal(N.show({ text: 'Sent.', class: 'workspace', tone: 'good', code: 'sent' }), null);
  assert.equal(N.show({ text: 'Archived.', class: 'workspace', tone: 'good', code: 'archived' }), null);
  assert.equal(N.show({ text: 'That change is applied.', class: 'workspace', tone: 'good', code: 'applied' }), null);
  assert.equal(N.show({ text: 'Ready.', class: 'workspace', tone: 'good', code: 'ready' }), null);
  assert.equal(rows(hosts.deckWorkspace).length, 0, 'no toast for a thing the control says itself');
  assert.ok(recorded.every((r) => r.fields.reason === 'control_shows'), JSON.stringify(recorded));
  // What is NOT refused: the draft that could not be saved. A failure is not a state the
  // control carries — it is the reason the control did not change — and it belongs beside it.
  const failed = N.show({ text: 'Gmail refused the draft.', class: 'control', tone: 'bad', code: 'draft_refused', host: hosts.deckWorkspace });
  assert.ok(failed, 'a refusal still has somewhere to go');
});

test('two identical notifications in a row produce one', () => {
  const { hosts } = screen('context');
  const spec = { text: 'The Mac did not answer.', class: 'workspace', tone: 'bad', code: 'backend_silent' };
  const first = N.show(spec);
  for (let i = 0; i < 8; i += 1) assert.equal(N.show(spec), first, 'the same entry, refreshed');
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(N.list().length, 1);
  assert.equal(N.list()[0].repeats, 9);
  // AND the same EVENT, whose sentence carries a number that moved. Deduplication used to
  // match on the class, the code, the half AND THE TEXT, so every message that varies by a
  // count, a name or an amount defeated it by definition: "1 change still waiting" and "2
  // changes still waiting" were two rows about one recurring thing. One event is one row,
  // and the newest words are the ones on it.
  N.clear({});
  const one = N.show({ text: '1 change came back still waiting for you.', class: 'workspace', tone: 'warn', code: 'merge_waiting' });
  const two = N.show({ text: '2 changes came back still waiting for you.', class: 'workspace', tone: 'warn', code: 'merge_waiting' });
  assert.equal(two, one, 'one event, one row');
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(words(rows(hosts.deckWorkspace)[0]), '2 changes came back still waiting for you.');
  // The half it is about is still part of what makes it the same message: one half's news
  // must never overwrite the other's.
  N.show({ text: '1 change came back still waiting for you.', class: 'workspace', tone: 'warn', code: 'merge_waiting', branch: 'br_other' });
  assert.equal(N.list().length, 2);
});

test('two controls refused for the same reason are two messages, one beside each', () => {
  /* The other edge of deduplicating by NAME. Two fields the Mac refused are two refusals
     even though both are `field_refused`: collapsing them would put one message beside the
     wrong control and leave the other with none, which is the exact failure CONTROL-LOCAL
     exists to avoid. So the control is part of what makes a control-local message the same
     message — by reference, not by name. */
  const { doc } = screen('context');
  const card = doc.createElement('article');
  const one = doc.createElement('div');
  const two = doc.createElement('div');
  card.appendChild(one);
  card.appendChild(two);
  const said = 'That does not look like an email address.';
  const a = N.show({ text: said, class: 'control', tone: 'bad', code: 'field_refused', host: one });
  const b = N.show({ text: said, class: 'control', tone: 'bad', code: 'field_refused', host: two });
  assert.ok(a && b && a !== b, 'two controls, two messages');
  assert.equal(rows(one).length, 1);
  assert.equal(rows(two).length, 1);
  // And the SAME control, said twice, is still one row with a count.
  const again = N.show({ text: said, class: 'control', tone: 'bad', code: 'field_refused', host: one });
  assert.equal(again, a);
  assert.equal(rows(one).length, 1);
  assert.equal(N.list().length, 2);
});

test('more than MAX_TRANSIENT messages that leave on their own is impossible', () => {
  const { hosts } = screen('context');
  // Two rows is 88px of a ~700px workbench screen. Three is 132px and starts costing a card,
  // and nobody follows three lines that are all disappearing. The newest wins.
  assert.equal(N.MAX_TRANSIENT, 2, 'chosen and justified in web/notify.js and the policy doc');
  for (const n of [1, 2, 3, 4, 5, 6]) {
    N.show({ text: `Something to know, number ${n}.`, class: 'workspace', tone: 'info', code: `k${n}` });
    assert.ok(N.list().filter((e) => !e.persists).length <= N.MAX_TRANSIENT, `after ${n}`);
  }
  const shown = rows(hosts.deckWorkspace).map(words);
  assert.deepEqual(shown, ['Something to know, number 5.', 'Something to know, number 6.']);
  // Across ALL THREE hosts, not per host: three regions of two each is six lines on one
  // screen, which is the stack the cap exists to stop.
  N.show({ text: 'The Mac cannot be reached.', class: 'global', machine: true, tone: 'info', code: 'unreachable' });
  assert.equal(N.list().filter((e) => !e.persists).length, N.MAX_TRANSIENT);
  assert.equal(rows(hosts.global).length + rows(hosts.deckWorkspace).length + rows(hosts.orbWorkspace).length, 2);
  // A FAILURE is not transient: it waits to be read, and neither cap counts it.
  for (const n of [1, 2, 3]) N.show({ text: `A failure, number ${n}.`, class: 'workspace', tone: 'bad', code: `f${n}` });
  assert.equal(N.list().filter((e) => e.persists).length, 3);
});

test('a "done" never stacks on a "done": one event, one line', () => {
  const { hosts } = screen('context');
  assert.equal(N.MAX_GOOD, 1);
  N.show({ text: 'The refund was proved on the store.', class: 'workspace', tone: 'good', code: 'refund_proved' });
  N.show({ text: 'The archive was proved in Gmail.', class: 'workspace', tone: 'good', code: 'archive_proved' });
  N.show({ text: 'The note was proved on the order.', class: 'workspace', tone: 'good', code: 'note_proved' });
  const shown = rows(hosts.deckWorkspace).map(words);
  assert.deepEqual(shown, ['The note was proved on the order.'], `one success, the newest: ${shown}`);
  assert.equal(N.list().filter((e) => e.tone === 'good').length, 1);
  // A success and a warning are two different things to know, and both may be live.
  N.show({ text: '2 changes came back still waiting for you.', class: 'workspace', tone: 'warn', code: 'merge_waiting' });
  assert.deepEqual(rows(hosts.deckWorkspace).map(words),
    ['The note was proved on the order.', '2 changes came back still waiting for you.']);
});

test('check() answers the policy without drawing anything, and is the same answer show gives', () => {
  screen('context');
  assert.deepEqual(N.check({ text: 'A real message.', code: 'a_real_message' }), { ok: true, reason: '' });
  assert.equal(N.check({ text: '', code: 'a' }).reason, 'no_words');
  assert.equal(N.check({ text: '—', code: 'a' }).reason, 'no_words');
  assert.equal(N.check({ text: 'x' }).reason, 'no_code');
  assert.equal(N.check({ text: 'x', code: 'No' }).reason, 'bad_code');
  assert.equal(N.check({ text: 'x', code: 'merged' }).reason, 'screen_shows');
  assert.equal(N.check({ text: 'x', code: 'draft_saved' }).reason, 'control_shows');
  assert.equal(N.list().length, 0, 'asking the policy draws nothing');
  // The two lists are policy and are readable, so a call site can be told which one it hit.
  assert.ok(N.SCREEN_SHOWS.includes('divided') && N.SCREEN_SHOWS.includes('merged'));
  assert.ok(N.CONTROL_SHOWS.includes('draft_saved'));
  assert.equal(N.SCREEN_SHOWS.filter((c) => N.CONTROL_SHOWS.includes(c)).length, 0, 'one reason each');
});

test('the whole live session, replayed: sixteen notifications become none', () => {
  const { hosts, recorded } = screen('orb');
  // The session's own sixteen, in the shape the page produced them: eleven that reached
  // `show()` with a sentence and no name, and five that named a state change the screen had
  // just made. Nothing in this list is allowed to appear on the glass.
  const session = [
    { text: 'That is not possible just now.', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: 'That could not be prepared.', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: 'The Mac did not answer.', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: 'That could not be applied.', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: '', class: 'workspace' },
    { text: 'Divided. Tap a half to talk to it; the other keeps working.', class: 'workspace', tone: 'good', code: 'divided' },
    { text: 'Merged. 2 things it looked at came back.', class: 'workspace', tone: 'good', code: 'merged' },
    { text: 'Divided. Tap a half to talk to it; the other keeps working.', class: 'workspace', tone: 'good', code: 'divided' },
    { text: 'Merged. 2 things it looked at came back.', class: 'workspace', tone: 'good', code: 'merged' },
    { text: 'Divided. Tap a half to talk to it; the other keeps working.', class: 'workspace', tone: 'good', code: 'divided' },
  ];
  assert.equal(session.length, 16);
  for (const message of session) assert.equal(N.show(message), null, JSON.stringify(message).slice(0, 60));
  assert.equal(N.list().length, 0);
  assert.equal(rows(hosts.global).length + rows(hosts.orbWorkspace).length + rows(hosts.deckWorkspace).length, 0);
  assert.equal(hosts.orbWorkspace.hidden, true, 'and the region never appeared');
  // Sixteen refusals, each with a reason, none of them a silence.
  assert.equal(recorded.length, 16);
  const why = {};
  for (const r of recorded) why[r.fields.reason] = (why[r.fields.reason] || 0) + 1;
  // A recorded notify event carries the class, the tone and the CODE, and never the words
  // (see the last test in this file: that is deliberate, and the owner's sentences are not
  // telemetry). So "eleven carry no text at all" is eleven messages with nothing readable in
  // the record: no words, no name, or neither. Both refusals are counted together against
  // the forensic number, and the five that did name something named a state change.
  assert.equal((why.no_words || 0) + (why.no_code || 0), 11,
    `eleven that said nothing the system could read: ${JSON.stringify(why)}`);
  assert.equal(why.screen_shows, 5, `and five that said what the screen had just shown: ${JSON.stringify(why)}`);
});
