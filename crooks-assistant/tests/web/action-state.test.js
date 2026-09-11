/* The action state machine, run under Node (node --test tests/web).
 *
 * These are the tests for D-1 of the live session: a send the Mac had proved VERIFIED left the
 * tablet saying "Applying…" for ten minutes, because the correction path settled a card from
 * `arming` and `armed` and from nothing else — and a committed card is in `committing`. The
 * one state that can be stuck was the one state reconcile refused to touch.
 *
 * So: one state machine, named states, explicit terminals; a terminal card is never settled
 * twice; every other state settles from the Mac's terminal status; and a watchdog says out
 * loud when a surface is still in flight after its proposal finished on the Mac.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const shim = require('./dom-shim.js');
globalThis.document = shim.document;
const UI = require(path.join(__dirname, '..', '..', 'web', 'ui.js'));
const AS = require(path.join(__dirname, '..', '..', 'web', 'action-state.js'));

// A real confirmation card, wired as the page wires it, with time and timers in the test's hand.
function card(id, overrides, extra) {
  let t = 0;
  const commits = [];
  const opts = Object.assign({
    now: () => t, blocked: () => false, onCommit: (pid) => commits.push(pid),
    timers: { set: () => 0, clear: () => {} },
  }, extra || {});
  const data = Object.assign({
    proposal_id: id, status: 'pending', risk: 'amber', operation: 'order_note_append',
    title: 'Add order note', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/1',
    interaction: { kind: 'tap_commit', label: 'Tap to apply', armed_after_ms: 650 }, ttl_s: 60, reversible: true,
  }, overrides || {});
  const node = UI.renderItem({ type: 'confirmation', data }, opts);
  const surface = node.querySelector('.action-surface');
  return {
    node, surface, commits,
    label: () => surface.childNodes[0].textContent,
    at: (ms) => { t = ms; },
    // The gesture the owner actually makes: arm, press, release — which is what puts a card
    // into `committing` and says "Applying…".
    commit: () => { t = 700; surface.dataset.state = 'armed'; surface.dispatch('pointerdown'); surface.dispatch('pointerup'); },
  };
}

// A card the renderer drew for a proposal that was NOT pending: no gesture, so no settle()
// on the node at all. This is the surface nothing on the page can talk to — the one a
// watchdog exists for.
function inertCard(id, status) {
  const node = UI.renderItem({ type: 'confirmation', data: {
    proposal_id: id, status, risk: 'amber', operation: 'order_note_append', title: 'Add order note',
    entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/1',
    interaction: { kind: 'tap_commit', label: 'Tap to apply', armed_after_ms: 650 }, ttl_s: 60,
  } });
  return { node, surface: node.querySelector('.action-surface') };
}

// ------------------------------------------------------------------ the machine itself

test('the states are named once, and the terminal ones are named with them', () => {
  assert.deepEqual(AS.STATES, ['READY', 'STAGED', 'ARMING', 'ARMED', 'EXECUTING', 'VERIFYING', 'VERIFIED', 'FAILED', 'EXPIRED', 'UNDONE']);
  assert.deepEqual(AS.TERMINAL, ['VERIFIED', 'FAILED', 'EXPIRED', 'UNDONE']);
  assert.deepEqual(AS.IN_FLIGHT, ['EXECUTING', 'VERIFYING']);
  for (const state of AS.TERMINAL) assert.ok(AS.isTerminal(state) && !AS.isLive(state), state);
  for (const state of AS.STATES.filter((s) => AS.TERMINAL.indexOf(s) === -1)) assert.ok(AS.isLive(state) && !AS.isTerminal(state), state);
});

test('every word the surface has ever carried maps onto one named state', () => {
  // The vocabulary the renderer, the page and the Mac's codes have all put in dataset.state.
  const expected = {
    '': 'READY', unavailable: 'READY', unsupported: 'READY',
    pending: 'STAGED', staged: 'STAGED', proposed: 'STAGED', batch_member: 'STAGED',
    arming: 'ARMING', holding: 'ARMING',
    armed: 'ARMED', held: 'ARMED', not_armed: 'ARMED',
    committing: 'EXECUTING', executing: 'EXECUTING', in_progress: 'EXECUTING',
    verifying: 'VERIFYING', executed: 'VERIFYING', unknown: 'VERIFYING',
    verified: 'VERIFIED', done: 'VERIFIED', already_executed: 'VERIFIED',
    undone: 'UNDONE',
    failed: 'FAILED', unverified: 'FAILED', stale: 'FAILED', refused: 'FAILED', blocked: 'FAILED', service_unavailable: 'FAILED',
    expired: 'EXPIRED', settled: 'EXPIRED', revoked: 'EXPIRED',
  };
  for (const token of Object.keys(expected)) assert.equal(AS.stateOf(token), expected[token], token);
  // The tokens the page writes back into dataset.state stay what the tablet has always used.
  assert.equal(AS.tokenFor('EXECUTING'), 'committing');
  assert.equal(AS.tokenFor('VERIFIED'), 'verified');
  // A word from a build that is newer than this one is live, never terminal: an unknown
  // state must be correctable, and must never be mistaken for a finished change.
  assert.equal(AS.stateOf('something_new'), 'STAGED');
  assert.ok(AS.isLive('something_new'));
});

// ------------------------------------------------------------------ D-1: the stuck card

test('a committed card settles from EXECUTING — the state that was stuck', () => {
  const c = card('prop_037e20c6ea04');
  c.commit();
  assert.equal(c.surface.dataset.state, 'committing', 'the gesture puts it in committing');
  assert.equal(AS.stateOf(c.surface.dataset.state), 'EXECUTING');
  assert.equal(c.label(), 'Applying…');

  const out = AS.settleProposals(['prop_037e20c6ea04'], 'done', 'Done', [c.node]);
  assert.deepEqual(out.settled, ['prop_037e20c6ea04']);
  assert.equal(AS.stateOf(c.surface.dataset.state), 'VERIFIED');
  assert.notEqual(c.label(), 'Applying…');
});

test('every non-terminal state settles from the Mac; a terminal one never does', () => {
  for (const token of ['arming', 'armed', 'holding', 'held', 'committing', 'verifying', 'executed', 'unknown', 'pending']) {
    const c = card('prop_1');
    c.surface.dataset.state = token;
    assert.deepEqual(AS.settleProposals(['prop_1'], 'done', 'Done', [c.node]).settled, ['prop_1'], token);
    assert.equal(AS.stateOf(c.surface.dataset.state), 'VERIFIED', token);
  }
  for (const token of ['verified', 'done', 'failed', 'unverified', 'stale', 'expired', 'settled', 'revoked', 'undone']) {
    const c = card('prop_1');
    c.node.settle(token, 'Settled');
    const label = c.label();
    const out = AS.settleProposals(['prop_1'], 'failed', 'Failed', [c.node]);
    assert.deepEqual(out.settled, [], token);
    assert.deepEqual(out.refused, ['prop_1'], token);
    assert.equal(c.surface.dataset.state, token, 'a settled card is left exactly as it is');
    assert.equal(c.label(), label);
  }
});

test('a terminal card is never re-settled and never re-animated', () => {
  const c = card('prop_1');
  let settles = 0;
  const real = c.node.settle;
  c.node.settle = (s, l) => { settles += 1; real(s, l); };
  c.commit();
  AS.settleProposals(['prop_1'], 'done', 'Done', [c.node]);
  AS.settleProposals(['prop_1'], 'done', 'Done', [c.node]);       // a duplicate packet
  AS.settleProposals(['prop_1'], 'failed', 'Failed', [c.node]);   // and a late, contrary one
  assert.equal(settles, 1, 'settled exactly once');
  assert.equal(AS.stateOf(c.surface.dataset.state), 'VERIFIED');
  assert.equal(c.label(), 'Done');
  // And it cannot be tapped back into flight.
  c.surface.dispatch('pointerdown'); c.surface.dispatch('pointerup');
  assert.deepEqual(c.commits, ['prop_1'], 'the one commit the gesture made, and no other');
});

// ------------------------------------------------------------------ reconciliation

test("the Mac's statuses become states, and only the terminal ones settle a card", () => {
  const settled = {
    verified: ['VERIFIED', 'done'], unverified: ['FAILED', 'failed'], failed: ['FAILED', 'failed'],
    stale: ['FAILED', 'failed'], expired: ['EXPIRED', 'settled'], revoked: ['EXPIRED', 'revoked'],
  };
  for (const status of Object.keys(settled)) {
    const answer = AS.settledFor(status);
    assert.ok(answer, status);
    assert.equal(answer.state, settled[status][0], status);
    assert.equal(answer.token, settled[status][1], status);
    assert.ok(answer.label, status);
  }
  // Claimed, sent, still being proven: NOT an outcome, and never shown as one. "Success means
  // VERIFIED" — an EXECUTED proposal has not been verified.
  for (const status of ['pending', 'executing', 'executed']) assert.equal(AS.settledFor(status), null, status);
});

test('a dropped commit response is repaired by the next reconcile', () => {
  const c = card('prop_a');
  c.commit();                                   // the POST left; nothing came back
  const states = { prop_a: { proposal_id: 'prop_a', status: 'verified', kind: 'action' } };
  const out = AS.reconcile([c.node], states);
  assert.deepEqual(out.corrected, ['prop_a']);
  assert.deepEqual(out.stuck, []);
  assert.equal(AS.stateOf(c.surface.dataset.state), 'VERIFIED');
});

test('a delayed response leaves the card in flight, and the outcome settles it when it comes', () => {
  const c = card('prop_b');
  c.commit();
  const inFlight = AS.reconcile([c.node], { prop_b: { proposal_id: 'prop_b', status: 'executing', kind: 'action' } });
  assert.deepEqual(inFlight.corrected, []);
  assert.deepEqual(inFlight.stuck, [], 'a proposal still running on the Mac is not a stuck surface');
  assert.equal(AS.stateOf(c.surface.dataset.state), 'EXECUTING');
  assert.equal(c.label(), 'Applying…', 'and it still says what it is doing');
  const later = AS.reconcile([c.node], { prop_b: { proposal_id: 'prop_b', status: 'verified', kind: 'action' } });
  assert.deepEqual(later.corrected, ['prop_b']);
  assert.equal(AS.stateOf(c.surface.dataset.state), 'VERIFIED');
});

test('a duplicate packet corrects nothing the second time', () => {
  const c = card('prop_c');
  c.commit();
  const states = { prop_c: { proposal_id: 'prop_c', status: 'verified', kind: 'action' } };
  assert.deepEqual(AS.reconcile([c.node], states).corrected, ['prop_c']);
  const again = AS.reconcile([c.node], states);
  assert.deepEqual(again.corrected, [], 'the same answer twice settles one card once');
  assert.deepEqual(again.stuck, []);
});

test('a reconnect that finds the action already terminal stops the animation at once', () => {
  // The tablet came back to itself — a wake, a restored workspace — and the change it left in
  // flight finished while it was away.
  const c = card('prop_d');
  c.commit();
  const out = AS.reconcile([c.node], { prop_d: { proposal_id: 'prop_d', status: 'unverified', kind: 'action' } });
  assert.deepEqual(out.corrected, ['prop_d']);
  assert.equal(AS.stateOf(c.surface.dataset.state), 'FAILED');
  assert.equal(c.label(), 'Not confirmed', 'and it says which failure it was, never success');
});

test('a card the Mac has settled is not asked about again', () => {
  const live = card('prop_live');
  const committed = card('prop_committing');
  committed.commit();
  const finished = card('prop_done');
  finished.node.settle('done', 'Done');
  const nodes = [live.node, committed.node, finished.node];
  // The live session's own bug: six reconciles of two proposals that were settled on the Mac,
  // every one changing nothing. A card in flight is asked about; a settled one never is.
  assert.deepEqual(AS.liveProposalIds(nodes).sort(), ['prop_committing', 'prop_live']);
  AS.settleProposals(['prop_committing'], 'done', 'Done', nodes);
  assert.deepEqual(AS.liveProposalIds(nodes), ['prop_live']);
});

// ------------------------------------------------------------------ the watchdog

test('the watchdog corrects a surface left in flight after the Mac finished, and says so', () => {
  // A card drawn for a proposal that was already executing has no gesture and therefore no
  // settle() at all: nothing on the page can talk to it. It is exactly the surface that spins
  // for ever, so the watchdog writes the state itself rather than asking politely.
  const stuck = inertCard('prop_stuck', 'executing');
  assert.equal(AS.stateOf(stuck.surface.dataset.state), 'EXECUTING');
  const out = AS.reconcile([stuck.node], { prop_stuck: { proposal_id: 'prop_stuck', status: 'verified', kind: 'action' } });
  assert.deepEqual(out.stuck.map((s) => s.proposal_id), ['prop_stuck']);
  assert.equal(out.stuck[0].was, 'EXECUTING');
  assert.equal(out.stuck[0].status, 'verified');
  assert.equal(AS.stateOf(stuck.surface.dataset.state), 'VERIFIED', 'corrected in place');
  assert.equal(stuck.surface.getAttribute('aria-disabled'), 'true');
  assert.notEqual(stuck.surface.childNodes[0].textContent, 'Applying…');
});

test('the watchdog fires for VERIFYING as well, and for nothing that is not in flight', () => {
  const verifying = inertCard('prop_v', 'executed');
  assert.equal(AS.stateOf(verifying.surface.dataset.state), 'VERIFYING');
  const out = AS.reconcile([verifying.node], { prop_v: { proposal_id: 'prop_v', status: 'failed', kind: 'action' } });
  assert.deepEqual(out.stuck.map((s) => s.proposal_id), ['prop_v']);
  assert.equal(AS.stateOf(verifying.surface.dataset.state), 'FAILED');

  // A waiting card whose proposal expired is corrected by the ordinary path, not by the
  // watchdog: the watchdog is a defect signal and must not cry about routine settling.
  const waiting = card('prop_w');
  const ordinary = AS.reconcile([waiting.node], { prop_w: { proposal_id: 'prop_w', status: 'expired', kind: 'action' } });
  assert.deepEqual(ordinary.corrected, ['prop_w']);
  assert.deepEqual(ordinary.stuck, []);
});

// ------------------------------------------------------------------ D-2: undo is not waiting

test('a pending undo is undoable, never a change still waiting', () => {
  const states = {
    prop_change: { proposal_id: 'prop_change', status: 'pending', undo_of: null, kind: 'action' },
    prop_undo: { proposal_id: 'prop_undo', status: 'pending', undo_of: 'prop_done', kind: 'action' },
    prop_done: { proposal_id: 'prop_done', status: 'verified', undo_id: 'prop_undo', kind: 'action' },
  };
  const split = AS.waiting(states);
  assert.deepEqual(split.pending, ['prop_change']);
  assert.deepEqual(split.undoable, ['prop_undo']);
  // The live session's merge toast said "2 changes still waiting over there" when both were
  // undo offers for changes that had already been made.
  assert.equal(AS.waiting({ prop_undo: states.prop_undo }).pending.length, 0);
});
