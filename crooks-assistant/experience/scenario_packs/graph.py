"""The customer / order / email graph, driven the way the tablet drives it (brief §16).

Three things that were broken on the bench, in the order they happen on the workbench:

    a thread showed its words and hid its order      → the linked_order strip, and a tap on it
    an order hid the email about it                   → the order's Email tab
    "have they emailed … and draft the reply"          → 35 seconds, almost all Claude, and two
                                                         gmail_read_thread calls REFUSED for
                                                         ids nobody had issued

The last one is the whole point of the pack: the same sentence has to come back on the FAST
lane with the order, the thread and the reply state on screen, both ids issued, and the draft
offered rather than claimed. Nothing here may write — the assertions include that nothing was
staged, because a read family that quietly proposed a draft would still pass every other check
in this file.
"""

from __future__ import annotations

from typing import Any

from experience.harness import Harness

# `Result`, `check` and the shared assertions live in experience/scenarios.py, which collects
# the packs at the END of its own module body, so these names are bound by the time this is
# imported. Importing them keeps one definition of what a check is.
from experience.scenarios import Result, a_surface, check, compound, deterministic, grounded

MIA_THREAD = "aa70d3f83dbef06e"
MIA_ORDER = "gid://shopify/Order/1938"
# David has written — about #1939 — and #1929 is another of his orders. "No email about this
# order" has to be said about #1929 without the thread about #1939 being mistaken for it.
DAVID_ORDER = "1929"
COMPOUND = "Check whether they've emailed us about this, tell me what they're waiting for, and draft the reply"


def _ok(c) -> bool:
    return bool(c.raw.get("ok", True))


def _detail(c) -> str:
    return f"code={c.raw.get('code')!r} detail={c.raw.get('detail')!r}"


def _issued(h: Harness, session_id: str) -> set[str]:
    """The ids this conversation has been shown. The gate refuses every id that is not in here
    (app/tools/gate.py), which is exactly what happened to the bench turn's two thread reads."""
    return set(getattr(h.runtime.sessions.get(session_id), "issued_ids", ()) or ())


def _tools(c) -> list[dict[str, Any]]:
    return [t for t in (c.raw.get("tool_calls") or []) if isinstance(t, dict)]


def _staged(h: Harness, session_id: str) -> list[Any]:
    return list(getattr(h.runtime.sessions.get(session_id), "proposals", ()) or [])


async def graph_thread_to_order(h: Harness) -> Result:
    r = Result("graph_thread_to_order", "Open Mia's thread from the queue, then its order")
    q = await h.say("which customers need replying to", scenario="graph_thread_to_order", session_id="graph1")
    r.captures.append(q)
    r.checks.append(check("the queue answers deterministically", q.lane == "FAST" and q.model_calls == 0, f"lane={q.lane} model_calls={q.model_calls}"))
    r.checks.append(check("Mia's thread is a row on it, so the conversation has been shown that id",
                          MIA_THREAD in _issued(h, "graph1"), f"issued={sorted(_issued(h, 'graph1'))[:6]}"))

    c = await h.touch("open.entity", scenario="graph_thread_to_order", session_id="graph1",
                      kind="email_thread", ref=MIA_THREAD, label="Order 1938")
    r.captures.append(c)
    r.checks.append(check("a row on the queue opens", c.status == 200 and _ok(c), _detail(c)))
    r.checks += a_surface(c, "email_thread", what="draws the thread")
    r.checks.append(deterministic(c))
    card = c.data("email_thread")
    linked = card.get("linked_order") if isinstance(card.get("linked_order"), dict) else {}
    r.checks.append(check("the thread says which order it is about", bool(linked.get("order_id")),
                          f"link_confidence={card.get('link_confidence')!r} linked_order={linked}"))
    r.checks.append(check("and how sure that is, in words", card.get("link_confidence") == "confident" and bool(card.get("link_provenance")),
                          f"confidence={card.get('link_confidence')!r} why={card.get('link_provenance')}"))
    if grounded(h):
        r.checks.append(check("the money and the status are on the strip, so the owner need not open it",
                              linked.get("order_number") == "#1938" and linked.get("total") == "£89.00" and linked.get("fulfillment") == "unfulfilled",
                              f"linked_order={linked}"))
    # Tappable is not a claim about the DOM: it is that the ref the strip carries was issued to
    # this conversation, so the tap the renderer wires up is a tap the gate will honour.
    r.checks.append(check("the strip's order was issued, so the tap on it is not refused",
                          str(linked.get("order_id") or "") in _issued(h, "graph1"), f"order_id={linked.get('order_id')!r}"))

    o = await h.touch("open.entity", scenario="graph_thread_to_order", session_id="graph1",
                      kind="order", ref=str(linked.get("order_id") or MIA_ORDER), label="#1938")
    r.captures.append(o)
    r.checks.append(check("tapping it opens the order", o.status == 200 and _ok(o), _detail(o)))
    r.checks += a_surface(o, "order", what="draws the order")
    r.checks.append(deterministic(o))
    r.checks.append(check("the order is now what the conversation is on", (o.entity or {}).get("ref") == MIA_ORDER, f"entity={o.entity}"))
    return r


async def graph_order_to_email(h: Harness) -> Result:
    r = Result("graph_order_to_email", "Order 1938, and the email about it")
    c = await h.say("show me order 1938", scenario="graph_order_to_email", session_id="graph2")
    r.captures.append(c)
    r.checks += a_surface(c, "order", what="draws the order")
    r.checks.append(deterministic(c))
    email = c.data("order").get("email") if isinstance(c.data("order").get("email"), dict) else {}
    threads = [t for t in (email.get("threads") or []) if isinstance(t, dict)]
    r.checks.append(check("the order card carries the inbox around it", bool(email.get("available")) and bool(threads),
                          f"email={ {k: email.get(k) for k in ('available', 'reason')} } threads={len(threads)}"))
    r.checks.append(check("Mia's thread about it is one of them",
                          MIA_THREAD in [str(t.get("thread_id")) for t in threads],
                          f"threads={[str(t.get('subject')) for t in threads]}"))
    if grounded(h):
        mine = next((t for t in threads if str(t.get("thread_id")) == MIA_THREAD), {})
        r.checks.append(check("and it says why it is on this order — her address and the number, not her name",
                              mine.get("match") == "both" and mine.get("sender_match") is True,
                              f"match={mine.get('match')!r} sender_match={mine.get('sender_match')!r}"))
    tab = await h.touch("surface.tab", scenario="graph_order_to_email", session_id="graph2", surface="order", tab="email")
    r.captures.append(tab)
    r.checks.append(check("the Email tab is a place on the order, not a new question",
                          tab.status == 200 and _ok(tab) and (tab.raw.get("changed") or {}).get("tab") == "email", _detail(tab)))
    return r


async def graph_compound_reply(h: Harness) -> Result:
    """The bench's worst turn, asked exactly as it was asked."""
    r = Result("graph_compound_reply", "“…emailed us about this … and draft the reply”")
    opened = await h.say("show me order 1938", scenario="graph_compound_reply", session_id="graph3")
    r.captures.append(opened)
    c = await h.say(COMPOUND, scenario="graph_compound_reply", session_id="graph3")
    r.captures.append(c)
    # The mechanics are the Mac's and the synthesis is Claude's, in ONE turn (§16). The recipe
    # is named on the turn even though the lane became NORMAL, because it ran: it chose the
    # reads, drew the cards, and handed the words on. ONE model call — the failure this
    # replaces is the owner asking a second time, which was a second turn.
    r.checks += compound(c, "order_email_reply")
    perf = c.raw.get("performance") or {}
    r.checks.append(check("the facts were in hand before the turn ended, not at the end of it",
                          float(perf.get("facts_ms") or 0.0) < float(perf.get("turn_total_ms") or 1e9),
                          f"facts_ms={perf.get('facts_ms')} total={perf.get('turn_total_ms')}"))
    r.checks.append(check("the answer leads with what was READ, not with what was written",
                          c.answer.startswith("Mia"), c.answer[:160]))
    r.checks += a_surface(c, "order", what="draws the order")
    r.checks += a_surface(c, "email_thread", what="draws the thread")
    r.checks += a_surface(c, "reply_state", what="draws the reply state")
    thread_card = c.data("email_thread")
    r.checks.append(check("the thread carries its linked order",
                          (thread_card.get("linked_order") or {}).get("order_id") == MIA_ORDER,
                          f"linked_order={thread_card.get('linked_order')}"))
    state = c.data("reply_state")
    r.checks.append(check("the reply state is who is waiting, since when, and on whom",
                          state.get("latest_direction") == "inbound" and state.get("replied") is False
                          and bool(state.get("waiting_since")) and state.get("confidence") == "confident",
                          f"reply_state={state}"))
    if grounded(h):
        r.checks.append(check("the customer is named from the thread, not guessed",
                              state.get("last_from") == "Mia" and state.get("order_number") == "#1938", f"reply_state={state}"))
    names = [str(t.get("name") or "") for t in _tools(c)]
    refused = [t for t in _tools(c) if str(t.get("name")) == "gmail_read_thread" and not t.get("ok")]
    r.checks.append(check("the thread was read, and the read was not refused for an unissued id",
                          "gmail_read_thread" in names and not refused, f"tools={names} refused={refused}"))
    issued = _issued(h, "graph3")
    r.checks.append(check("both ids the model is handed are issued to the conversation",
                          MIA_THREAD in issued and MIA_ORDER in issued,
                          f"thread={MIA_THREAD in issued} order={MIA_ORDER in issued}"))
    # The handover itself. `email.reply` is the spoken control this build already has for
    # drafting a reply to a thread (app/commands.py:SPOKEN_CONTROLS), so whatever is said next
    # reaches Claude with this thread named and applied to nothing else. What the prompt itself
    # contains — the thread text, both ids, and the gmail_draft_reply instruction, bounded — is
    # asserted in tests/test_graph.py, where it can be read without a customer's words going
    # through the timeline.
    listening = h.branch("graph3", c.branch_id).voice_target() or {}
    r.checks.append(check("the reply is armed on that thread for the next thing the owner says",
                          listening.get("family") == "email.reply" and listening.get("ref") == MIA_THREAD,
                          f"listening_for={ {k: listening.get(k) for k in ('family', 'kind', 'ref')} }"))
    # The recipe's half of the sentence no longer offers to draft — the owner asked for the
    # draft and it is being written in the same breath, so offering would be asking twice. What
    # it must still never do is claim the reply went out; the model's half is the fixture
    # provider's fixed sentence here, so this is the Mac's half being checked.
    lead = c.answer.split("[model answer]")[0]
    r.checks.append(check("the Mac's half states the position and never claims the reply went out",
                          "#1938" in lead and "not replied" in lead.lower()
                          and "say the word" not in lead.lower() and "sent" not in lead.lower(),
                          lead[:200]))
    r.checks.append(check("and nothing was staged: this family reads", not _staged(h, "graph3"),
                          f"proposals={[getattr(p, 'operation', p) for p in _staged(h, 'graph3')]}"))
    # Every tool this turn ran, held against the four reads the recipe declares. A write would
    # be caught by `assert_read_only` before the plan ran; this catches the turn as a whole
    # reaching for anything the recipe did not say it would.
    r.checks.append(check("only the recipe's own reads ran",
                          bool(names) and set(names) <= {"shopify_find_order", "shopify_order_detail", "gmail_search", "gmail_read_thread"},
                          f"tools={names}"))
    return r


async def graph_no_email_about_this_order(h: Harness) -> Result:
    """The other half of never guessing: David HAS written, about a different order."""
    r = Result("graph_no_email_about_this_order", "Nothing about #1929, and it says so without the model")
    opened = await h.say(f"show me order {DAVID_ORDER}", scenario="graph_no_email_about_this_order", session_id="graph4")
    r.captures.append(opened)
    r.checks.append(check("the order opens on the fast lane", opened.lane == "FAST" and opened.surface("order") is not None,
                          f"lane={opened.lane} surfaces={opened.surface_types}"))
    c = await h.say(COMPOUND, scenario="graph_no_email_about_this_order", session_id="graph4")
    r.captures.append(c)
    r.checks.append(check("answered by the Mac alone", c.lane == "FAST" and c.model_calls == 0,
                          f"lane={c.lane} recipe={c.recipe_id!r} model_calls={c.model_calls}"))
    r.checks.append(check("the answer is the plain one, with the window it actually looked at",
                          c.answer.startswith(f"No email from David about #{DAVID_ORDER} in the last 30 days."), c.answer[:200]))
    r.checks.append(check("it does not pretend he has written nothing at all",
                          "not about this order" in c.answer and "#1939" in c.answer, c.answer[:240]))
    r.checks.append(check("no thread is drawn and no reply state is invented",
                          c.surface("email_thread") is None and c.surface("reply_state") is None, f"surfaces={c.surface_types}"))
    r.checks += a_surface(c, "order", what="still draws the order that was asked about")
    r.checks.append(check("the whole answer is given, so nothing is left outstanding",
                          c.raw.get("partial") is not True, f"partial={c.raw.get('partial')!r}"))
    r.checks.append(check("no thread was opened", "gmail_read_thread" not in [str(t.get("name")) for t in _tools(c)],
                          f"tools={[str(t.get('name')) for t in _tools(c)]}"))
    r.checks.append(check("and nothing is listening for a reply that has nothing to reply to",
                          not (h.branch("graph4", c.branch_id).voice_target() or {}),
                          f"listening_for={h.branch('graph4', c.branch_id).voice_target()}"))
    return r


SCENARIOS = (
    ("graph_thread_to_order", graph_thread_to_order),
    ("graph_order_to_email", graph_order_to_email),
    ("graph_compound_reply", graph_compound_reply),
    ("graph_no_email_about_this_order", graph_no_email_about_this_order),
)
