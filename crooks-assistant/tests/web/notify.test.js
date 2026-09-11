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
  N.show({ text: 'Draft saved in Gmail drafts.', class: 'workspace', tone: 'good', code: 'draft_saved' });
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(rows(hosts.global).length, 0);
  assert.equal(rows(hosts.orbWorkspace).length, 0);
  assert.equal(hosts.deckWorkspace.hidden, false, 'the region shows itself when it has something to say');
  assert.equal(words(rows(hosts.deckWorkspace)[0]), 'Draft saved in Gmail drafts.');
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
  N.show({ text: 'Merged. 2 changes still waiting over there.', class: 'workspace', tone: 'warn', code: 'merged', branch: 'br_first' });
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
  const good = N.show({ text: 'Draft saved.', class: 'workspace', tone: 'good', code: 'draft_saved' });
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
  const kept = N.show({ text: 'Draft saved.', class: 'workspace', tone: 'good', code: 'draft_saved', persist: true });
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
  N.show({ text: 'Divided. Tap a half to talk to it.', class: 'workspace', tone: 'good', code: 'divided' });
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
  const odd = N.show({ text: 'Something happened.', class: 'shout', tone: 'magenta' });
  assert.equal(odd.class, 'workspace');
  assert.equal(odd.tone, 'info');
  assert.equal(rows(hosts.deckWorkspace).length, 1);
  assert.equal(N.show({ text: '   ' }), null, 'nothing to say is not a message');
  assert.equal(N.show({}), null);
});

test('clear takes what it is asked for and can be told to keep the failures', () => {
  const { hosts } = screen('context');
  N.show({ text: 'Draft saved.', class: 'workspace', tone: 'good', code: 'draft_saved' });
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
  assert.equal(N.show({ text: 'Nowhere to say this.', class: 'workspace' }), null);
  assert.equal(N.list().length, 0);
  N.reset();
  assert.equal(N.show({ text: 'Not started yet.' }), null);
});

test('what it records is controlled vocabulary: a class, a code, a tone — never the words', () => {
  const { recorded } = screen('context');
  N.show({ text: 'Alexandra Featherstonehaugh was emailed.', class: 'workspace', tone: 'good', code: 'emailed', branch: 'br_a' });
  assert.equal(recorded.length, 1);
  assert.equal(recorded[0].kind, 'notify');
  assert.deepEqual(recorded[0].fields, { name: 'workspace', code: 'emailed', tone: 'good', branch: 'br_a', persists: false });
  assert.ok(!/Alexandra|Featherstonehaugh/.test(JSON.stringify(recorded)), 'nothing a message said is recorded');
});
