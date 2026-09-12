"""The controls, the words on them and the motion around them — §25, §26, §28.

Workstream F of Phase 5 is subtraction: "if a control does not earn its space, remove it. If
an animation does not communicate state, remove it. If a notification is not necessary, do
not show it." The third of those is `tests/test_notification_policy.py`. These are the first
two, and each test is anchored to a number from the live tablet session of 11 September
(`docs/phase5/LIVE_SESSION_FORENSICS.md`) rather than to a preference.

§25 · THE RAIL, AND THE SESSION'S OWN COUNT
    Four enabled actions on every order card — fulfil, address, cancel, note — four exposures
    each, sixteen chip-exposures in one evening, and ONE tap on any of them (`address`, once).
    "Exposed but never used: cancel, fulfil, note."

    THE OBVIOUS ANSWER WAS TRIED AND IS WRONG, and the record of that is the most useful part
    of this audit. Cutting the rail to two chips with one at full weight, and deleting `note`
    and the thread's `dictate` outright, breaks three things the product needs and the gates
    already assert:

      * `note` is the only chip on an order carrying a `family`, so tapping it is the ONLY
        touch path to binding the microphone to that order (§20, D-11,
        `scripts/browser/experience.js`). Its numbers justify its weight, not its deletion.
      * `dictate` is the same door on a thread, and the composer's own Dictate only exists
        once a composer is open (`scripts/browser/tablet.js`).
      * a real order — unfulfilled, paid, the customer has written, the address needs fixing
        — owes four things, and two slots dropped `address`, which is the one chip the owner
        DID tap (`scripts/browser/email.js`).

    So the count is not the defect; the weight and the relevance are. What this pass removes
    from the rail is `cancel` on any order whose own context does not ask for it — the
    reddest, least reversible chip, two renders and nought taps — and everything the renderer
    was drawing that was not a control at all. §25 has five questions and "remove it" is one
    of five answers.

§26 · HUMAN LANGUAGE, ALWAYS
    "Order #1962", never `gid://shopify/Order/…`, and never a control primed with a sentence
    that names nothing ("Fulfil order ").

§28 · MOTION THAT COMMUNICATES, AND NOTHING ELSE
    The old Samsung runs `html[data-lite]`, where at most ONE continuous animation may
    survive, and only if it is state rather than decoration.

-------------------------------------------------------------------------------------------
THE AUDIT ITSELF. Every persistent control, against §25's five questions — does the owner use
it, does it explain itself, is it in the right place, is there a better contextual location,
does it visually compete with something more important. Usage is the live session's own count
of renders and taps. This table is the record; the tests below are the parts of it that can be
enforced.

  CONTROL            USED          VERDICT        WHERE IT WENT / WHY IT STAYED
  ─────────────────  ────────────  ─────────────  ──────────────────────────────────────────
  Cancel             2 / 0         REMOVED from   ranked last unless the customer's own
                                   the enabled    email asks for it (`context_rank`), and on
                                   set            an order with anything else to offer, last
                                                  means off the card. Still reachable by
                                                  voice, and still shown with its one reason
                                                  when it CANNOT be done (§19).
  Note (order rail)  5 / 0         KEPT, last     removal was tried and reverted: it is the
                                   and never      only chip on an order carrying a `family`,
                                   loud           so it is the one touch path to binding the
                                                  microphone to that order (§20, D-11).
  Dictate (thread)   n/a (Phase 4) KEPT, behind   removal was tried and reverted: the
                                   the            composer's own Dictate exists only once a
                                   disclosure     composer is open; this is the only way to
                                                  bind the microphone to a thread before it.
  Fulfil             2 / 0         KEPT · leads   what an unfulfilled paid order needs, and
                                   by context     the gate asserts it leads on order 1938
  Address            2 / 1 ← the   KEPT           `mode=open`, so a tap reaches the address
                     only tap on                  screen rather than a microphone. Cutting
                     the rail all                 the rail to two chips dropped it, which is
                     evening                      why the rail holds three plus the note.
  Refund             3 / 0         KEPT           leads when the customer's own email asks
                                                  for one; takes the place cancel had
  Email              3 / 0         KEPT           `mode=open` → the composer
  Reply (thread)     24 / 0        KEPT · leads   Phase 4 made it open a composer instead of
                                                  arming a microphone
  Archive (thread)   24 / 0        KEPT           stage → gesture, at full weight beside it
  a chip with no     —             REMOVED        not drawn (it rendered as an em dash)
  label
  a chip the page    —             REMOVED        not drawn (D-6: a control offered before
  cannot wire                                     its destination was known to exist)
  a chip disabled    —             REMOVED        not drawn (§19: a disabled control says
  with no reason                                  why, or it is not a control)
  a rail of only     —             FIXED          behind the disclosure; it used to be
  disabled chips                                  promoted to full weight wholesale
  composer button    —             REMOVED        not drawn (two builders, same em dash)
  with no label
  row button with    —             REMOVED        not drawn (it said "Do")
  no label
  toast(words)       11 of the 16  REMOVED        `notify(words, { code })`; a message that
                     notifications                cannot be named cannot be governed
  "Divided…"         3 of 5        REMOVED        the orb visibly dividing, and two named
                                                  chips under it
  "Merged. N came    2 of 5        REMOVED        one orb, one chip, and the deck has them
  back."

THE LESSON, since it cost a gate run: a control that nobody taps is not the same thing as a
control that nobody needs. Ask what is the ONLY WAY to reach a capability before removing the
thing that reaches it — "exposed but never used" is an argument about weight and placement,
and only sometimes an argument about existence.

AUDITED AND KEPT, with the reason, so the next pass does not re-litigate them:

  #conn (the header's reachability pill) — not a control and never tapped, but it is the only
  always-visible statement of tablet→Mac reachability, and `wentOffline()` already defers to a
  turn's own error copy rather than stacking on it (`if (quiet())`). Not redundant.
  .services (Shopify / Gmail / Voice / Changes) — a different fact from #conn: those are the
  MAC's reachability of each service, not the tablet's of the Mac.
  familyRow's fallback to a raw key or a SCREAMING_SNAKE state — the settings sheet is a
  debug surface, where §26 permits a technical name.

THE LOUDEST §25 FINDING IN THE WHOLE PASS, AND IT IS NOT THIS WORKSTREAM'S TO FIX. The gate
workstream measured the branch strip on the tablet's own 601px screen: **Merge is drawn at
x=590 and Close at x=664** — a 571px strip asked to hold 807px of controls, with two of its
four substantially OFF THE GLASS. That is not clutter to be rearranged; it is a strip whose
contents do not fit by design, and §25's answer to a control that does not fit is to remove
one, not to shrink four. It is `web/app.js drawBranchBar` and the `#branch-bar` / `#branch-rail`
layout, which workstream A owns this pass (D-1 is the P0 there). Recorded here with the
number so it is not lost, and cross-referenced from
`docs/phase5/NOTIFICATION_POLICY.md` — a control that is off the screen shows no state, which
is the premise every muted notification code depends on.

Related, same owner: the gate's shot 22 ("split branch ready") is MISSING — the other half
answered while the owner was elsewhere and nothing on the selector said so. This workstream
MUTES the `ready` notification on the strength of §10 ("the branch chip says READY"), so that
chip owes the state. The policy document lists it as the one row that is not yet proved.

NOT FIXED, AND OWNED ELSEWHERE (recorded so they are not lost):
  `.rail-why` is 11px — that is kicker size for text §19 makes essential. Typography in
  web/style.css, which this workstream owns only for animation.
  `.action-target` is 9px uppercase for a hold-drag instruction (gesture surfaces, workstream A).
  `app/tools/shopify_writes.py` and `app/tools/gmail_writes.py` raise "No order with id
  gid://shopify/Order/…" — a raw id in a sentence, in files this workstream does not own.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.actions.available import (
    MAX_ENABLED,
    MAX_PRIMARY,
    available_actions,
    available_email_actions,
    context_rank,
    order_phrase,
    order_words,
)

ROOT = Path(__file__).resolve().parent.parent
STYLE = (ROOT / "web" / "style.css").read_text()
UI_JS = (ROOT / "web" / "ui.js").read_text()


def _code(source: str) -> str:
    """The source with its comments taken out.

    Every removal in this pass is explained in a comment that NAMES the thing removed, which
    is the point — a deletion nobody can find the reason for comes back. So "it is gone" has
    to be asked of the code and not of the prose about it.
    """
    out = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"^\s*//.*$", "", out, flags=re.M)


STYLE_CODE = _code(STYLE)
UI_CODE = _code(UI_JS)

READY = {"state": "ready", "detail": "ready", "scope": "write_orders"}
CAPS = {op: READY for op in ("order_note_append", "order_cancel", "order_shipping_address_set",
                             "refund_create", "fulfillment_create", "gmail_draft_new")}
EMAIL_CAPS = {"gmail_draft_reply": READY, "gmail_thread_archive": READY}
ARCHIVE_ROW = [{"id": "email_archive", "label": "Archive", "operation": "gmail_thread_archive",
                "risk": "amber", "enabled": True, "reason": "", "detail": "Out of the inbox.",
                "mode": "stage", "command": "", "args": "", "priority": "primary"}]

OPEN = {
    "order_id": "gid://shopify/Order/1938", "order_number": "CROOKS-1938",
    "fulfillment": "UNFULFILLED", "payment": "PAID", "total": "60.00 GBP", "refundable": True,
    "money": {"refunded": "0.00 GBP", "total": "60.00 GBP"}, "customer_email": "d@example.com",
    "shipping_address": {"lines": ["12 Somewhere Street"], "city": "Windsor"},
    "items": [{"unfulfilled_quantity": 1}], "fulfillments": [],
}
SHIPPED = dict(OPEN, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}],
               fulfillments=[{"status": "SUCCESS"}])
CANCELLED = dict(OPEN, cancelled_at="2026-09-08T10:00:00Z", payment="REFUNDED", refundable=False,
                 money={"refunded": "60.00 GBP", "total": "60.00 GBP"})
UNPAID = dict(OPEN, payment="PENDING", refundable=False)
ASKING = dict(SHIPPED, email={"threads": [{"thread_id": "t1", "sender_match": True,
                                           "subject": "Refund please", "snippet": "I want a refund."}]})
EVERY_STATE = [OPEN, SHIPPED, CANCELLED, UNPAID, ASKING]


# =========================================================== §25 · the rail is not a menu


# The chips whose own numbers say they must never be loud. §25's brief names five and says
# "do not give Fulfil / Refund / Cancel / Address / Note equal visual weight on every order";
# these are the two of the five that no order's state can justify shouting.
#
#   note    five renders, nought taps, and it is what is left to offer when the order needs
#           nothing — so it is loudest exactly where it is least use.
#   cancel  two renders, nought taps, red, and irreversible. An order needs cancelling
#           because a PERSON said so, which `context_rank` reads out of the customer's own
#           email; nothing about an order's own state asks for it.
NEVER_LOUD_UNASKED = ("note", "cancel")


@pytest.mark.parametrize("order", EVERY_STATE)
def test_an_order_card_does_not_expose_four_equally_weighted_enabled_actions(order):
    """The defect, stated as the session measured it, in the two forms that were still real.

    Four enabled chips at four exposures each, sixteen chip-exposures, one tap. Phase 4 had
    already stopped drawing all four at one weight in the ordinary case — and left two ways
    for it to happen anyway, both of which this asserts against:

      * `note` was appended to the enabled list and weighed BY POSITION, so on an order with
        only one other thing to offer — cancelled, fully refunded — it landed at index 1 and
        was drawn at FULL WEIGHT. The quietest version of "Note first on every card",
        surviving on exactly the orders that need nothing.
      * `cancel` took a full-weight slot on any order whose state left few enabled chips —
        an unpaid one, for instance — with nobody having asked to cancel anything.

    The rest of the shape: at most two at full weight, whatever is left behind one
    disclosure, and every disabled chip carrying its one short reason (§19).
    """
    actions = available_actions(order, CAPS)
    enabled = [a for a in actions if a["enabled"]]
    primary = [a for a in enabled if a["priority"] == "primary"]
    asked = context_rank(order)
    assert len(primary) <= MAX_PRIMARY == 2, f"not a menu: {[a['id'] for a in primary]}"
    # Three changes the order might need, plus the note, which is always offered and never
    # counted (and never loud — see below).
    assert len([a for a in enabled if a['id'] != 'note']) <= MAX_ENABLED == 3, \
        f"{[a['id'] for a in enabled]}"
    assert len(enabled) - len(primary) >= 1 or len(enabled) <= MAX_PRIMARY, \
        f"if there are more than two, the rest are disclosed: {[(a['id'], a['priority']) for a in enabled]}"
    for action in primary:
        assert not (action["id"] in NEVER_LOUD_UNASKED and action["id"] not in asked), \
            f"{action['id']} is loud and nothing asked for it: {[(a['id'], a['priority']) for a in enabled]}"
    # A disabled chip never sits beside a live one, and never leads.
    for action in actions:
        if not action["enabled"]:
            assert action["priority"] == "secondary", action
            # §19: a control that is disabled says WHY, in the owner's words, short enough to
            # read on an eight-inch screen beside the thing it is about.
            assert action["reason"], action
            assert len(action["reason"]) <= 40, action["reason"]


def test_cancel_is_not_on_an_order_that_nobody_asked_to_cancel():
    """THE REMOVAL §25's evidence supports. Two renders, nought taps, and it is the reddest
    and least reversible thing on the rail. An order needs cancelling because a PERSON said
    so — which `context_rank` reads out of the customer's own email — and nothing about an
    order's own state asks for it.

    §19 · a control that is removed must not leave a spoken claim that it exists, and it must
    not go silent where the owner would ask. Both hold: "cancel order 1938" is a sentence the
    Mac still answers, and a cancel that CANNOT be done still appears with its one reason."""
    # A paid order with real work to do does not carry it at all.
    assert "cancel" not in [a["id"] for a in available_actions(OPEN, CAPS) if a["enabled"]]
    # And nowhere, in any state, is it ever drawn at full weight unless the order asks:
    # an unpaid order that has not shipped is one you MIGHT cancel, so it stays reachable —
    # behind the disclosure, after the things that are not irreversible.
    for order in EVERY_STATE:
        for action in available_actions(order, CAPS):
            if action["id"] == "cancel" and action["priority"] == "primary":
                raise AssertionError(f"a red irreversible chip, loud, unasked: {order.get('payment')}")
    # The customer asked, in writing. Now it leads.
    asked = dict(OPEN, email={"threads": [{"thread_id": "t1", "sender_match": True,
                                           "subject": "please cancel", "snippet": "I ordered the wrong size."}]})
    cancel = next(a for a in available_actions(asked, CAPS) if a["id"] == "cancel")
    assert (cancel["enabled"], cancel["priority"]) == (True, "primary")
    # And where it cannot be done, it still says so rather than vanishing.
    off = {a["id"]: a["reason"] for a in available_actions(SHIPPED, CAPS) if not a["enabled"]}
    assert off.get("cancel") == "already shipped"
    # Ranked, not filtered: a Mac whose only granted write is the cancel still offers it,
    # because there is nothing else to offer.
    assert [a["id"] for a in available_actions(OPEN, {"order_cancel": READY})] == ["cancel"]


def test_note_stays_and_is_the_only_door_it_is_the_only_one_to():
    """Removal was TRIED and reverted, which is the useful half of this audit.

    Five renders and nought taps justify its weight — last, and never at full weight, which
    Phase 4 already did — but not its deletion: it is the only chip on an order carrying a
    `family`, so tapping it is the one way to bind the microphone to THIS order with a thumb
    (§20 — voice is intent, touch is precision, and they are two controls). A chip nobody taps
    is not the same thing as a chip nobody needs."""
    for order in EVERY_STATE:
        by_id = {a["id"]: a for a in available_actions(order, CAPS)}
        assert "note" in by_id, [a["id"] for a in available_actions(order, CAPS)]
        assert by_id["note"]["priority"] == "secondary", "never at full weight"
        assert by_id["note"]["family"] == "order.add_note"
        assert by_id["note"]["mode"] == "ask", "it primes a sentence, which is what arms the family"
    # It is last, always: it is what is left to offer, not what the order needs.
    ids = [a["id"] for a in available_actions(OPEN, CAPS) if a["enabled"]]
    assert ids[-1] == "note", ids


def test_dictate_stays_because_the_composers_own_dictate_is_not_reachable_yet():
    """§25 · "is there a better contextual location?" — asked, and the answer was no.

    The composer that Reply opens does carry a Dictate with this thread's own family and ref
    (tests/test_email_workspace.py), so this chip looks like a duplicate. It is not: that one
    exists only once a composer is open, and this is the only way to bind the microphone to a
    thread before then. Removing it closed the only door, which the browser gate caught by
    tapping `.rail-chip[data-mode="ask"][data-family="email.reply"]`."""
    rail = available_email_actions({"thread_id": "t1"}, EMAIL_CAPS, row_actions=list(ARCHIVE_ROW))
    ids = [a["id"] for a in rail]
    assert ids == ["reply", "email_archive", "dictate"]
    assert [a["priority"] for a in rail] == ["primary", "primary", "secondary"]
    dictate = rail[-1]
    assert (dictate["mode"], dictate["family"]) == ("ask", "email.reply")
    # And the one that leads reaches a screen rather than a microphone (Phase 4, D-11).
    assert (rail[0]["mode"], rail[0]["command"]) == ("open", "compose.reply")


def test_a_rail_is_weighed_in_exactly_one_place():
    """`priority` is decided by `available.py` and by nothing else. A weight decided in two
    files is a weight decided in neither — and the renderer used to overturn it (see below)."""
    rows = (ROOT / "app" / "actions" / "rows.py").read_text()
    assert "MAX_PRIMARY" not in rows, "rows.py must not decide loudness"
    assert "h('div', { class: 'rail-primary' }, front)" in UI_CODE


def test_the_renderer_does_not_promote_a_dead_chip_when_there_is_no_live_one():
    """It did. `primary.length ? primary : list_` drew EVERY chip at full weight whenever
    nothing was marked primary — which is exactly the case a rail of disabled chips is — so
    "a dead chip must not sit beside a live one" held in the payload and failed on the glass.
    A weighed payload is now drawn as it was weighed."""
    assert "primary.length ? primary : list_" not in UI_CODE
    assert "const weighed = list_.some((a) => text(a.priority));" in UI_CODE


def test_a_chip_that_is_not_a_control_is_not_drawn():
    """§25/§19, in the renderer. Three of these looked like controls and were not: one with
    no label (it drew an em dash), one the page could not wire at all (D-6 — a control drawn
    before its destination was known to exist, and dimmed with NO reason on it because
    `reason` is empty exactly when the Mac thinks it is enabled), and one disabled with
    nothing to say."""
    for guard in ("if (!text(a.label)) return null;",
                  "if (a.enabled === true && !enabled) return null;",
                  "if (!enabled && !text(a.reason)) return null;"):
        assert guard in UI_CODE, guard
    # And nowhere else either: the two composer button builders drew the same em dash, and a
    # row button the Mac had not named was drawn saying "Do".
    assert "text(a.label, '—')" not in UI_CODE, "a chip saying an em dash does not explain itself"
    assert "'Do'" not in UI_CODE, "a row button saying \"Do\" does not say what it does"


# ======================================================== §26 · human language, always


def test_no_raw_gid_reaches_a_normal_surface():
    """§26 · "Order #1962", never `gid://shopify/Order/…`. Technical ids only on debug or test
    surfaces.

    The hole was the FALLBACK behind `order_digits`: `order_number` was passed through raw, so
    a read model carrying only the Shopify id produced "Fulfil order gid://shopify/Order/1938"
    — and an `ask` chip's instruction is the sentence the owner is primed to SAY out loud.
    """
    gid = "gid://shopify/Order/1938"
    for order in (dict(OPEN, order_number=gid), dict(OPEN, order_number=f"#{gid}"),
                  dict(OPEN, order_number="gid://shopify/Order/1938 "), OPEN, SHIPPED, CANCELLED):
        for action in available_actions(order, CAPS):
            for field in ("label", "reason", "instruction", "detail"):
                value = str(action.get(field) or "")
                assert "gid://" not in value, f"{action['id']}.{field} = {value!r}"
                assert "://" not in value, f"{action['id']}.{field} = {value!r}"
    # An identity may still travel — in `args`, which is a query string the Mac built and the
    # tablet forwards into a `data-` attribute. It is never drawn as words (web/ui.js puts
    # every id in `data:`), and that is the one place §26 allows one.
    address = next(a for a in available_actions(OPEN, CAPS) if a["id"] == "address")
    assert address["args"] == f"order_id={OPEN['order_id']}" and address["mode"] == "open"


def test_a_control_is_never_primed_with_a_sentence_that_names_nothing():
    """"Fulfil order " — a chip that primes the owner to say a sentence with no record in it.
    An `ask` chip IS its instruction, so with no human name for the order there is no control
    to draw (§18). An `open` chip carries the id itself and still works."""
    nameless = {k: v for k, v in OPEN.items() if k != "order_number"}
    for action in available_actions(nameless, CAPS):
        said = action["instruction"]
        # A whole sentence, naming a record: "order 1938" when the Mac has read the number,
        # "this order" when it has not. Never "order" with nothing after it, and never two
        # spaces where a number was meant to go.
        assert said == said.strip() and "  " not in said, f"{action['id']}: {said!r}"
        assert re.search(r"(order \d|this order)\b", said), f"{action['id']}: {said!r}"
        assert action["mode"] == "open", f"{action['id']} primes words it cannot complete"
    assert order_words(nameless) == ""
    assert order_phrase(nameless) == "this order"
    assert order_words(OPEN) == "1938" and order_phrase(OPEN) == "order 1938"
    assert order_words({"order_number": "gid://shopify/Order/1938"}) == ""


def test_no_technical_capability_name_reaches_a_chip_the_owner_reads():
    """§26 forbids a technical capability name on a normal surface. Each chip carries its
    `operation` — the ledger's own name for the write — because the tablet posts it; none of
    it may appear in anything drawn as words."""
    for order in EVERY_STATE:
        for action in available_actions(order, CAPS):
            operation = action["operation"]
            assert "_" in operation, "the operation is the technical name, and it stays one"
            for field in ("label", "reason", "instruction"):
                assert operation not in str(action.get(field) or ""), f"{action['id']}.{field}"
            assert action["label"] == action["label"].strip() and action["label"]
            assert len(action["label"]) <= 12, f"a word on a chip, not a sentence: {action['label']!r}"


# ============================================ §28 · motion that communicates, and no other

# A declaration that runs for ever. `animation-iteration-count:infinite`, or the shorthand
# carrying it.
_CONTINUOUS = re.compile(r"\binfinite\b")
_NAME = re.compile(r"animation\s*:\s*([A-Za-z_-][\w-]*)")


def _rules(css: str) -> list[tuple[str, str, str]]:
    """(at-rule context, selector, declarations) for every rule in the sheet.

    A deliberately small parser: this stylesheet has no nested selectors and no `{` inside a
    value, which the last assertion in `test_the_parser_sees_the_whole_sheet` checks.
    """
    out: list[tuple[str, str, str]] = []
    context: list[str] = []
    i = 0
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    while i < len(body):
        brace = body.find("{", i)
        if brace == -1:
            break
        head = body[i:brace].strip()
        if head.startswith("@") and not head.startswith("@keyframes"):
            context.append(head)
            i = brace + 1
            continue
        close = body.find("}", brace)
        if head.startswith("@keyframes"):           # skip the frames themselves
            depth, j = 1, brace + 1
            while depth and j < len(body):
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            i = j
            continue
        out.append((" ".join(context), head, body[brace + 1:close]))
        i = close + 1
        while context and body[i:].lstrip().startswith("}"):
            i = body.index("}", i) + 1
            context.pop()
    return out


def _targets(selector: str) -> set[str]:
    """The last compound selector of each comma-separated part — the element the rule is
    about, with any ancestor (`html[data-lite] `, `.cards `) dropped."""
    return {part.strip().split()[-1] for part in selector.split(",") if part.strip()}


def test_the_parser_sees_the_whole_sheet():
    rules = _rules(STYLE)
    assert len(rules) > 200, len(rules)
    assert any(r[1] == ".card" for r in rules)
    assert any("prefers-reduced-motion" in r[0] for r in rules)
    assert any(r[1].startswith("html[data-lite]") for r in rules)


def test_under_data_lite_at_most_one_continuous_animation_and_it_is_state():
    """§28 · the old Samsung. It used to run TWO: a 1.2s opacity-and-scale `sys-pulse` on four
    of the five in-flight action states, because `html[data-lite]` overrode only the fifth —
    and `lite-working` on that fifth. One is allowed, and only because it is STATE: the Mac
    has this change and has not come back yet, which is the one thing on the glass the owner
    cannot work out from anything else on it.
    """
    rules = _rules(STYLE)
    lite_off: set[str] = set()
    for context, selector, decls in rules:
        if not selector.startswith("html[data-lite]") or "prefers-reduced-motion" in context:
            continue
        if re.search(r"animation\s*:\s*none", decls):
            lite_off |= _targets(selector)

    surviving: dict[str, str] = {}
    for context, selector, decls in rules:
        if not _CONTINUOUS.search(decls) or "prefers-reduced-motion" in context:
            continue
        name = _NAME.search(decls)
        assert name, (selector, decls)
        if selector.startswith("html[data-lite]"):
            surviving[name.group(1)] = selector          # it is the lite build's own
        elif not (_targets(selector) <= lite_off):
            surviving[name.group(1)] = selector          # data-lite never switched it off

    assert len(surviving) <= 1, f"the old Samsung would run {len(surviving)}: {surviving}"
    assert set(surviving) == {"lite-working"}, surviving
    # And it is opacity only. A transform or a shadow is what the 2019 panel drops frames on.
    frames = re.search(r"@keyframes\s+lite-working\s*\{(.*?)\}\s*\n", STYLE, re.S)
    assert frames and "transform" not in frames.group(1) and "box-shadow" not in frames.group(1)


def test_nothing_continuous_survives_prefers_reduced_motion():
    """One blanket rule, and it has to actually blanket: an `!important` iteration count of 1
    beats every shorthand in the sheet, whatever its specificity."""
    blanket = [decls for context, selector, decls in _rules(STYLE)
               if "prefers-reduced-motion" in context and selector.replace(" ", "").startswith("*,")]
    assert blanket, "the sheet must turn motion off for somebody who asked for that"
    assert "animation-iteration-count:1!important" in blanket[0].replace(" ", "")
    assert "animation-duration:1ms!important" in blanket[0].replace(" ", "")


def test_the_animations_that_were_deleted_stay_deleted():
    """§28's own list, and the report's WHAT WAS REMOVED. Each of these was motion that did
    not communicate a state:

      sk-breathe   constant shimmer on three to five skeleton rows, on every progressive
                   render — and already switched off, statically, for `data-lite` and for
                   reduced motion, with nobody the wiser. If the honest version of a surface
                   is a static grey bar, the pulse was never carrying the information.
      settle       the success card scaled .97 -> 1.012 -> 1 over 520ms: the largest movement
                   on the tablet, saying what the green edge and the state's own word already
                   said twice.
      the stagger  50/100/140ms of `animation-delay` on the 2nd, 3rd and 4th card. The cards
                   arrive together, so it did not say they arrived in an order; it kept the
                   deck moving for another 140ms after the answer landed, on a screen the
                   owner was already scrolling.
    """
    for gone in ("sk-breathe", "@keyframes settle", "animation-delay:50ms",
                 "animation-delay:100ms", "animation-delay:140ms"):
        assert gone not in STYLE_CODE, gone
    assert "animation:card-in" in STYLE_CODE, "arrival still says it is an arrival"
    assert ".card.success{animation:card-in var(--t-3) var(--ease-spring) both}" in STYLE_CODE


def test_an_enrichment_never_replays_an_entry_animation():
    """§28 · "animations restarting on every patch". The card was covered; the tabbed panel
    inside it was not, and it fades its content in on every draw — right when the owner
    changed the tab, wrong when the Mac enriched the card underneath him."""
    assert ".card[data-patched]{animation:none}" in STYLE_CODE
    assert ".card[data-patched] .panel{animation:none}" in STYLE_CODE


def test_every_continuous_animation_left_in_the_sheet_is_justified_and_switchable():
    """The whole §28 audit, as one assertion. Every animation that runs for ever must be a
    STATE the owner cannot read anywhere else, and must be switchable off for both the old
    panel and for somebody who asked for less motion."""
    allowed = {
        # the microphone is armed and bound to a record, right now
        "armed-pulse": ".armed-dot",
        # the tablet is trying to reach the Mac, right now
        "sys-pulse": ".system-pulse",
        # the Mac has this change and has not come back
        "lite-working": "html[data-lite] .action-surface",
    }
    found: dict[str, list[str]] = {}
    for context, selector, decls in _rules(STYLE):
        if not _CONTINUOUS.search(decls) or "prefers-reduced-motion" in context:
            continue
        name = _NAME.search(decls).group(1)
        found.setdefault(name, []).append(selector)
    assert set(found) <= set(allowed), f"an unjustified continuous animation: {set(found) - set(allowed)}"
    for name, where in allowed.items():
        assert name in found, f"{name} was expected on {where}"
