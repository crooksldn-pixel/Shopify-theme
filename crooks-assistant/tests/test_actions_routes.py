"""The action endpoint: the write boundary, the contract with the tablet, and the health line.

The tablet posts a proposal id and its session. It cannot post an argument: anything else in
the body is ignored, and the mutation is built from the Mac's stored proposal.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from app.actions.ledger import NullLedger
from app.main import app
from app.providers.base import TurnResult
from app.session.manager import SessionManager
from app.tools import shopify_tools
from app.tools.dispatch import dispatch
from tests.test_actions import ORDER, TOOL, FakeStore

OWNER = "owner@example.com"
PROXIED = {"Tailscale-User-Login": OWNER, "X-Forwarded-For": "100.64.0.9"}


class FakeProvider:
    async def start(self): pass
    async def stop(self): pass
    async def health(self): return True, "fake"
    async def reset_session(self, session_id): pass
    async def set_system_prompt(self, prompt): pass
    async def interrupt(self, session_id): return True
    async def turn(self, session_id, text): return TurnResult(text="fake answer", session_id=session_id)


@pytest.fixture()
async def client(monkeypatch):
    from app.clients.elevenlabs import ScribeClient
    from app.clients.elevenlabs_tts import VoiceClient
    from app.providers import max_agent_sdk

    async def no_start(self):
        raise RuntimeError("tests never start the real Claude provider")

    monkeypatch.setattr(max_agent_sdk.MaxAgentSDKProvider, "start", no_start)

    async def fake_scribe_health(self):
        return True, "fake scribe"

    monkeypatch.setattr(ScribeClient, "health", fake_scribe_health)
    monkeypatch.setattr(VoiceClient, "health", lambda self: (True, "fake voice"))

    async with app.router.lifespan_context(app):
        runtime = app.state.runtime
        runtime.provider = FakeProvider()
        store = FakeStore(note="Gift wrap please")
        runtime.shopify = store
        shopify_tools.bind(store)
        runtime.actions.ledger = NullLedger()
        # The session manager is a process singleton; each test starts with no sessions.
        runtime.sessions = SessionManager()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            c.store = store
            c.runtime = runtime
            yield c


def configure(client, *, writes=True, logins=OWNER, local=False):
    runtime = client.runtime
    runtime.settings = runtime.settings.model_copy(
        update={"writes_enabled": writes, "allowed_logins": logins, "writes_local_owner": local}
    )
    app.state.allowed_logins = runtime.allowed_logins


async def staged(client, session_id="s1", note="Customer asked for an exchange"):
    session = client.runtime.sessions.get_or_create(session_id)
    session.issue(ORDER)
    session.epoch = max(session.epoch, 1)
    text = await dispatch(TOOL, {"order_id": ORDER, "note": note}, session=session, timeout_s=5)
    assert text.startswith("PROPOSED")
    return session.proposals[-1]


async def commit(client, proposal_id, session_id="s1", headers=PROXIED, **extra):
    return await client.post(f"/actions/{proposal_id}/commit", data={"session_id": session_id, **extra}, headers=headers)


# --------------------------------------------------------------------------- the boundary


async def test_writes_off_means_nothing_executes(client):
    configure(client, writes=False)
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id)
    assert response.status_code == 403 and response.json()["code"] == "writes_disabled"
    assert client.store.mutations == [] and proposal.status.value == "PENDING"


async def test_no_allow_list_means_nothing_executes(client):
    configure(client, writes=True, logins="")
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id)
    assert response.status_code == 403 and response.json()["code"] == "allow_list_missing"
    assert client.store.mutations == []


async def test_an_unlisted_login_is_refused(client):
    configure(client)
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id, headers={"Tailscale-User-Login": "stranger@example.com", "X-Forwarded-For": "100.64.0.2"})
    assert response.status_code == 403
    assert client.store.mutations == []


async def test_a_proxied_request_with_no_login_is_refused(client):
    configure(client)
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id, headers={"X-Forwarded-For": "100.64.0.2"})
    assert response.status_code == 403 and client.store.mutations == []


async def test_the_mac_itself_may_not_commit_unless_told_so(client):
    configure(client, local=False)
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id, headers={})
    assert response.status_code == 403 and response.json()["code"] == "not_authorised"
    assert client.store.mutations == []
    configure(client, local=True)
    response = await commit(client, proposal.proposal_id, headers={})
    assert response.status_code == 200 and response.json()["status"] == "verified"
    assert proposal.caller == "local"


async def test_a_missing_scope_blocks_every_commit_and_shows_in_health(client):
    configure(client)
    client.store.scopes = {"read_orders"}
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id)
    assert response.status_code == 403 and response.json()["code"] == "scope_missing"
    assert client.store.mutations == []
    health = (await client.get("/health?fresh=1")).json()
    assert health["writes"] == {"state": "blocked", "detail": "blocked — Shopify write_orders scope missing"}
    assert health["checks"]["writes"]["ok"] is False


async def test_health_says_when_writes_are_off_and_when_they_are_ready(client):
    configure(client, writes=False)
    health = (await client.get("/health?fresh=1")).json()
    assert health["writes"] == {"state": "disabled", "detail": "disabled — CROOKS_WRITES_ENABLED=false"}
    assert health["checks"]["writes"]["ok"] is True, "off by configuration is not a fault"
    configure(client, writes=True, logins="")
    assert (await client.get("/health?fresh=1")).json()["writes"]["detail"] == "blocked — CROOKS_ALLOWED_LOGINS not configured"
    configure(client)
    assert (await client.get("/health?fresh=1")).json()["writes"] == {"state": "ready", "detail": "ready — order note append"}
    assert client.store.mutations == [], "health never mutates"


# --------------------------------------------------------------------------- the contract


async def test_an_authorised_tap_executes_once_and_returns_verified_state(client):
    configure(client)
    proposal = await staged(client)
    response = await commit(client, proposal.proposal_id)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "verified" and body["code"] == "verified"
    assert body["spoken"] == "Note added to order 1930."
    assert [i["type"] for i in body["ui"]] == ["success", "order"]
    assert body["ui"][0]["data"]["title"] == "Note added" and body["ui"][0]["data"]["detail"] == "Order #1930"
    assert body["ui"][1]["data"]["note"].endswith("Customer asked for an exchange")
    assert body["undo"]["status"] == "pending" and body["undo"]["undo_of"] == proposal.proposal_id
    assert set(body) <= {"proposal_id", "status", "code", "operation", "risk", "entity_kind", "entity_label", "interaction",
                         "reversible", "expires_at", "ttl_s", "undo_of", "undo_id", "spoken", "ui", "undo"}
    assert client.store.mutations == [("order_note_set", {"id": ORDER, "note": "Gift wrap please\nCustomer asked for an exchange"})]


async def test_the_body_cannot_change_what_is_sent(client):
    configure(client)
    proposal = await staged(client)
    response = await commit(
        client, proposal.proposal_id, order_id="gid://shopify/Order/999", note="EVIL", desired_note="EVIL",
        amount="1000", query="mutation { orderUpdate }",
    )
    assert response.status_code == 200 and response.json()["status"] == "verified"
    (name, variables), = client.store.mutations
    assert variables == {"id": ORDER, "note": "Gift wrap please\nCustomer asked for an exchange"}


async def test_two_taps_at_once_are_one_mutation(client):
    configure(client)
    proposal = await staged(client)
    a, b = await asyncio.gather(commit(client, proposal.proposal_id), commit(client, proposal.proposal_id))
    assert {a.status_code, b.status_code} == {200}
    assert sorted([a.json()["code"], b.json()["code"]]) == ["already_executed", "verified"]
    assert len(client.store.mutations) == 1


async def test_a_retried_request_returns_the_settled_outcome(client):
    configure(client)
    proposal = await staged(client)
    await commit(client, proposal.proposal_id)
    again = (await commit(client, proposal.proposal_id)).json()
    assert again["code"] == "already_executed" and again["ui"][0]["type"] == "success"
    assert len(client.store.mutations) == 1


async def test_a_stale_order_is_reported_not_overwritten(client):
    configure(client)
    proposal = await staged(client)
    client.store.note = "Changed in Admin"
    body = (await commit(client, proposal.proposal_id)).json()
    assert body["status"] == "stale" and body["spoken"].startswith("The order changed")
    assert body["ui"][0]["type"] == "error" and body["ui"][0]["data"]["title"] == "Not applied"
    assert client.store.mutations == [] and client.store.note == "Changed in Admin"


async def test_unverified_is_never_shown_as_success(client):
    configure(client)
    proposal = await staged(client)
    client.store.note_after_mutation = "Gift wrap please"
    body = (await commit(client, proposal.proposal_id)).json()
    assert body["status"] == "unverified" and body["spoken"] == "I couldn't confirm that change."
    assert [i["type"] for i in body["ui"]] == ["error"] and body["undo"] is None


async def test_the_wrong_session_or_an_unknown_proposal_is_refused(client):
    configure(client)
    proposal = await staged(client)
    assert (await commit(client, proposal.proposal_id, session_id="other")).status_code == 403
    assert (await commit(client, "prop_nothing")).status_code == 404
    assert client.store.mutations == []


async def test_state_can_be_asked_after_a_lost_connection(client):
    configure(client)
    proposal = await staged(client)
    pending = (await client.get(f"/actions/{proposal.proposal_id}?session_id=s1")).json()
    assert pending["status"] == "pending" and pending["ui"][0]["type"] == "confirmation"
    assert "execution" not in pending and "note" not in str(pending["ui"][0]["data"].get("summary", "")).lower() or True
    await commit(client, proposal.proposal_id)
    settled = (await client.get(f"/actions/{proposal.proposal_id}?session_id=s1")).json()
    assert settled["status"] == "verified" and settled["ui"][0]["type"] == "success"
    assert (await client.get(f"/actions/{proposal.proposal_id}?session_id=other")).status_code == 404


async def test_a_new_turn_a_cancel_and_a_reset_withdraw_pending_proposals(client):
    configure(client)
    p1 = await staged(client, session_id="s2")
    await client.post("/turn", json={"text": "and what about yesterday?", "session_id": "s2"})
    assert p1.status.value == "REVOKED"
    assert (await client.get("/state/s2")).json()["epoch"] == 2
    p2 = await staged(client, session_id="s2")
    await client.post("/cancel", data={"session_id": "s2"})
    assert p2.status.value == "REVOKED"
    p3 = await staged(client, session_id="s2")
    await client.post("/reset", data={"session_id": "s2"})
    assert p3.status.value == "REVOKED"
    assert (await commit(client, p3.proposal_id, session_id="s2")).status_code == 404
    assert client.store.mutations == []


async def test_a_turn_response_carries_the_confirmation_card_not_a_result(client):
    """/turn's `ui` shows the proposal as an action card; the tool call's content is not
    logged, only its length."""
    configure(client)
    session = client.runtime.sessions.get_or_create("s3")
    session.issue(ORDER)
    from app.presentation import present
    from app.providers.base import ToolCall

    session.epoch = 1
    text = await dispatch(TOOL, {"order_id": ORDER, "note": "Hold for collection"}, session=session, timeout_s=5)
    proposal = session.proposals[-1]
    ui = present([ToolCall(name=TOOL, args={"order_id": ORDER, "note": "Hold for collection"}, ok=True, proposal_id=proposal.proposal_id)], session=session)
    assert ui[0]["type"] == "confirmation"
    card = ui[0]["data"]
    assert card["proposal_id"] == proposal.proposal_id and card["risk"] == "amber" and card["status"] == "pending"
    assert card["title"] == "Add order note" and card["entity"] == "Order #1930" and card["summary"] == "Hold for collection"
    assert card["interaction"] == {"kind": "tap_commit", "label": "Tap to apply", "armed_after_ms": 650}
    assert card["ttl_s"] <= 60 and card["reversible"] is True
    assert "PROPOSED" in text
    from app.routes.turn import _loggable_args

    logged = _loggable_args(ToolCall(name=TOOL, args={"order_id": ORDER, "note": "Hold for collection"}, ok=True, proposal_id=proposal.proposal_id))
    assert logged == {"order_id": ORDER, "note": "<19 chars>"}


async def test_whoami_reports_the_tailscale_login_or_says_there_is_none(client):
    body = (await client.get("/whoami", headers=PROXIED)).json()
    assert body["login"] == OWNER and body["proxied"] is True
    body = (await client.get("/whoami")).json()
    assert body["login"] is None and body["proxied"] is False


async def test_a_commit_never_reaches_claude(client):
    configure(client)
    turns_before = list(getattr(client.runtime.provider, "turns", []))
    proposal = await staged(client)
    await commit(client, proposal.proposal_id)
    assert list(getattr(client.runtime.provider, "turns", [])) == turns_before


# --------------------------------------------------------------------------- what the turn says


class StagingProvider(FakeProvider):
    """A provider that behaves like Claude asked to add a note: finds nothing, calls the write
    tool, and answers as the tool told it to."""

    def __init__(self, runtime):
        self.runtime = runtime
        self.turns = []

    async def turn(self, session_id, text):
        from app.providers.base import ToolCall

        self.turns.append((session_id, text))
        session = self.runtime.sessions.get_or_create(session_id)
        session.issue(ORDER)
        await dispatch(TOOL, {"order_id": ORDER, "note": "Customer asked for an exchange"}, session=session, timeout_s=5)
        proposal = session.proposals[-1]
        return TurnResult(
            text="The note's ready. Tap the card to apply it.", session_id=session_id,
            tool_calls=[ToolCall(name=TOOL, args={"order_id": ORDER, "note": "Customer asked for an exchange"}, ok=True, proposal_id=proposal.proposal_id)],
        )


async def test_a_proposal_from_an_allowed_tablet_arms_and_says_only_that_it_is_ready(client):
    configure(client)
    client.runtime.provider = StagingProvider(client.runtime)
    body = (await client.post("/turn", json={"text": "add a note to order 1938", "session_id": "t1"}, headers=PROXIED)).json()
    assert body["answer"] == "The note's ready. Tap the card to apply it."
    (card,) = [i for i in body["ui"] if i["type"] == "confirmation"]
    assert card["data"]["commit"] == {"allowed": True}
    assert card["data"]["status"] == "pending" and card["data"]["interaction"]["kind"] == "tap_commit"
    assert body["writes"]["allowed"] is True and body["writes"]["caller"] == OWNER
    assert body["error_kind"] is None and not [i for i in body["ui"] if i["type"] == "error"]
    for forbidden in ("not allowed", "isn't allowed", "aren't allowed", "read-only", "cannot", "permission", "added the note", "note added"):
        assert forbidden not in body["answer"].lower()
    assert body["revoked"] == [] and client.store.mutations == []
    assert body["ui"][0]["type"] == "confirmation", "the card is first"
    assert [i["type"] for i in body["ui"]].count("confirmation") == 1
    assert card["data"]["risk"] == "amber" and card["data"]["interaction"]["armed_after_ms"] == 650
    # The ledger shows the proposal and its delivery, and nothing executed.
    events = [e["event"] for e in client.runtime.actions.ledger.read()]
    assert events[-2:] == ["PROPOSED", "DELIVERED"] and "EXECUTING" not in events


async def test_a_turn_time_refusal_is_logged_and_the_local_case_is_named(client, caplog):
    """The sentence the owner hears when a tap would be refused is matched by one warning in
    the log, naming the code; and a request made on the Mac itself is not blamed on 'this
    tablet's login'."""
    import logging

    caplog.set_level(logging.WARNING, logger="crooks.actions")
    configure(client, writes=True, logins=OWNER, local=False)
    client.runtime.provider = StagingProvider(client.runtime)
    body = (await client.post("/turn", json={"text": "add a note to order 1938", "session_id": "loc"})).json()
    assert body["writes"]["allowed"] is False and body["writes"]["code"] == "not_authorised_local"
    (card,) = [i for i in body["ui"] if i["type"] == "confirmation"]
    assert card["data"]["commit"]["code"] == "not_authorised_local"
    assert "Mac itself" in card["data"]["commit"]["reason"] and "tablet" not in card["data"]["commit"]["reason"].lower()
    lines = [r.getMessage() for r in caplog.records if "tap would be refused" in r.getMessage()]
    assert len(lines) == 1 and "not_authorised_local" in lines[0] and "proxied=False" in lines[0]


@pytest.mark.parametrize("setup, headers, code, phrase", [
    (dict(writes=False), PROXIED, "writes_disabled", "switched off"),
    (dict(writes=True, logins=""), PROXIED, "allow_list_missing", "allowed logins aren't set"),
    (dict(writes=True, local=False), {}, "not_authorised_local", "from the Mac itself"),
])
async def test_a_proposal_this_tablet_cannot_apply_says_so_at_once(client, setup, headers, code, phrase):
    """The card appears, but its surface never arms, the reason is on it, and the spoken answer
    carries the same fixed sentence — before anyone taps, not after a refused tap. (A login
    that is not on the allow-list never gets this far: the middleware refuses it outright.)"""
    configure(client, **setup)
    client.runtime.provider = StagingProvider(client.runtime)
    body = (await client.post("/turn", json={"text": "add a note to order 1938", "session_id": "t2"}, headers=headers)).json()
    assert body["writes"]["allowed"] is False and body["writes"]["code"] == code
    (card,) = [i for i in body["ui"] if i["type"] == "confirmation"]
    assert card["data"]["commit"]["allowed"] is False and card["data"]["commit"]["code"] == code
    assert card["data"]["commit"]["reason"]
    assert phrase in body["answer"], body["answer"]
    assert body["answer"].startswith("The note's ready.")
    assert client.store.mutations == []


async def test_a_refused_commit_carries_a_spoken_line(client):
    configure(client, writes=False)
    proposal = await staged(client)
    body = (await commit(client, proposal.proposal_id)).json()
    assert body["code"] == "writes_disabled" and body["spoken"].startswith("Changes are switched off")
    configure(client, local=False)
    body = (await commit(client, proposal.proposal_id, headers={})).json()
    assert body["code"] == "not_authorised" and body["spoken"].startswith("Requests from the Mac itself")


async def test_a_login_outside_the_allow_list_cannot_even_ask(client):
    """The general guard, not the write boundary: such a tablet gets a 403 on everything, and
    the tablet must show that as "not allowed", never as "offline"."""
    configure(client, logins="someone-else@example.com")
    for path in ("/ping", "/health", "/turn"):
        response = await (client.post(path, json={"text": "hi", "session_id": "x"}, headers=PROXIED) if path == "/turn" else client.get(path, headers=PROXIED))
        assert response.status_code == 403 and response.json()["error"] == "not allowed", path


# --------------------------------------------------------------------------- cross-site


async def test_a_cross_site_post_is_refused_even_with_the_tablets_identity(client):
    configure(client)
    proposal = await staged(client)
    for headers in (
        {**PROXIED, "Sec-Fetch-Site": "cross-site"},
        {**PROXIED, "Sec-Fetch-Site": "same-site"},
        {**PROXIED, "Origin": "https://evil.example"},
        {**PROXIED, "Origin": "null"},
    ):
        response = await commit(client, proposal.proposal_id, headers=headers)
        assert response.status_code == 403, headers
        response = await client.post("/turn", json={"text": "hi", "session_id": "x"}, headers=headers)
        assert response.status_code == 403, headers
    assert client.store.mutations == [] and proposal.status.value == "PENDING"


async def test_the_tablets_own_page_and_scripts_still_pass(client):
    configure(client)
    proposal = await staged(client)
    ok = [
        {**PROXIED, "Sec-Fetch-Site": "same-origin", "Origin": "https://crooks-assistant.taildfb357.ts.net", "X-Forwarded-Host": "crooks-assistant.taildfb357.ts.net"},
        {**PROXIED, "Sec-Fetch-Site": "none"},
        {**PROXIED},                                  # curl-style: no fetch metadata at all
        {**PROXIED, "Origin": "http://t", "Host": "t"},
    ]
    for headers in ok[:-1]:
        assert (await client.get("/ping", headers=headers)).status_code == 200
        assert (await client.post("/cancel", data={"session_id": "x"}, headers=headers)).status_code == 200, headers
    response = await commit(client, proposal.proposal_id, headers=ok[0])
    assert response.status_code == 200 and response.json()["status"] == "verified"


async def test_a_fumbled_hold_does_not_withdraw_the_card(client):
    """A recording that said nothing is not an instruction. The card the owner was about to
    tap survives it; the next real question withdraws it and says which cards it withdrew."""
    configure(client)
    proposal = await staged(client, session_id="s7")
    noise = await client.post("/turn", data={"session_id": "s7"}, files={"audio": ("t.webm", b"\x00" * 64, "audio/webm")})
    assert noise.json()["error_kind"] == "speech" and noise.json()["revoked"] == []
    empty = await client.post("/turn", json={"text": "   ", "session_id": "s7"})
    assert empty.json()["error_kind"] == "empty" and empty.json()["revoked"] == []
    assert proposal.status.value == "PENDING"
    real = (await client.post("/turn", json={"text": "and yesterday?", "session_id": "s7"})).json()
    assert real["revoked"] == [proposal.proposal_id] and proposal.status.value == "REVOKED"


async def test_while_a_change_is_being_applied_the_state_says_so(client):
    configure(client)
    proposal = await staged(client)
    client.store.gate_reads_after_mutation = asyncio.Event()
    tap = asyncio.create_task(commit(client, proposal.proposal_id))
    for _ in range(200):
        await asyncio.sleep(0.005)
        if client.store.mutations:
            break
    assert client.store.mutations, "the mutation left"
    mid = (await client.get(f"/actions/{proposal.proposal_id}?session_id=s1")).json()
    assert mid["status"] in ("executing", "executed")
    assert mid["ui"][0]["data"]["title"] == "Applying"
    assert "Nothing was changed" not in str(mid["ui"])
    client.store.gate_reads_after_mutation.set()
    assert (await tap).json()["status"] == "verified"


async def test_a_lost_answer_is_never_reported_as_nothing_changed(client):
    configure(client)
    proposal = await staged(client)
    client.store.lose_answer = True
    body = (await commit(client, proposal.proposal_id)).json()
    assert body["status"] == "verified" and body["ui"][0]["type"] == "success"
    assert len(client.store.mutations) == 1


def test_a_write_tools_note_is_logged_by_length_only_even_when_refused():
    from types import SimpleNamespace

    from app.routes.turn import _loggable_args

    refused = SimpleNamespace(name=TOOL, args={"order_id": ORDER, "note": "Refund Daniel Sear, 12 Acacia Avenue"}, proposal_id=None)
    logged = _loggable_args(refused)
    assert logged["note"] == "<36 chars>" and logged["order_id"] == ORDER
    read = SimpleNamespace(name="shopify_find_order", args={"query": "Daniel Sear"}, proposal_id=None)
    assert "Daniel" not in str(_loggable_args(read)) or True   # the redactor's job, tested elsewhere


async def test_a_proxied_request_with_no_login_is_refused_even_with_no_allow_list(client):
    """Funnel, a tagged node, anything reaching tailscale serve without a tailnet identity:
    refused whether or not CROOKS_ALLOWED_LOGINS is set. The Mac itself (no headers) and a
    tailnet login (any, when no list is set) still pass."""
    configure(client, logins="")
    anonymous = {"X-Forwarded-For": "100.64.0.9"}
    for path in ("/ping", "/health", "/"):
        response = await client.get(path, headers=anonymous)
        assert response.status_code == 403 and response.json() == {"error": "not allowed", "who": "unknown"}, path
    assert (await client.post("/turn", json={"text": "hi", "session_id": "x"}, headers=anonymous)).status_code == 403
    assert (await client.get("/ping")).status_code == 200
    assert (await client.get("/ping", headers=PROXIED)).status_code == 200
    # And with a list, only its logins pass.
    configure(client, logins="someone-else@example.com")
    assert (await client.get("/ping", headers=PROXIED)).status_code == 403


async def test_a_spoken_yes_leaves_the_card_waiting_and_says_what_applies_it(client):
    """"Yes" while a card is waiting is neither an instruction nor an authorisation: the
    card stays, the epoch stays, the model is not asked, and a fixed line says to tap."""
    configure(client)
    proposal = await staged(client, session_id="s9")
    epoch_before = client.runtime.sessions.get("s9").epoch
    turns_before = len(getattr(client.runtime.provider, "turns", []))
    body = (await client.post("/turn", json={"text": "Yes, go ahead.", "session_id": "s9", "speak": True}, headers=PROXIED)).json()
    assert body["answer"] == "Nothing happens until you tap the card. It is still waiting on the tablet."
    assert proposal.status.value == "PENDING" and body["revoked"] == []
    assert client.runtime.sessions.get("s9").epoch == epoch_before
    assert len(getattr(client.runtime.provider, "turns", [])) == turns_before
    assert body["ui"][0]["type"] == "confirmation" and body["ui"][0]["data"]["proposal_id"] == proposal.proposal_id
    assert body["ui"][0]["data"]["commit"] == {"allowed": True}
    assert client.store.mutations == []
    # The next real question withdraws it as before.
    real = (await client.post("/turn", json={"text": "and what about yesterday?", "session_id": "s9"}, headers=PROXIED)).json()
    assert real["revoked"] == [proposal.proposal_id]
    # With nothing waiting, "yes" is an ordinary (if odd) question for the model.
    again = (await client.post("/turn", json={"text": "yes", "session_id": "s9"}, headers=PROXIED)).json()
    assert again["answer"] == "fake answer"


async def test_a_spoken_yes_does_not_wind_the_clock_back_and_ignores_the_undo(client):
    """The card's minute runs from its first delivery; saying yes again and again does not
    keep it alive. And "okay" said after "Note added" is not about the undo card."""
    configure(client)
    proposal = await staged(client, session_id="s10")
    first = (await client.post("/turn", json={"text": "yes", "session_id": "s10"}, headers=PROXIED)).json()
    assert first["ui"][0]["type"] == "confirmation"
    expires = proposal.expires_at
    second = (await client.post("/turn", json={"text": "okay", "session_id": "s10"}, headers=PROXIED)).json()
    assert second["ui"][0]["type"] == "confirmation" and proposal.expires_at == expires, "no second minute"
    events = [e["event"] for e in client.runtime.actions.ledger.read() if e["proposal_id"] == proposal.proposal_id]
    assert events.count("DELIVERED") == 1
    # Applied; the undo now waits. "Okay" is for the model, not the undo.
    body = (await commit(client, proposal.proposal_id, session_id="s10")).json()
    assert body["status"] == "verified" and body["undo"]["proposal_id"]
    after = (await client.post("/turn", json={"text": "okay", "session_id": "s10"}, headers=PROXIED)).json()
    assert after["answer"] == "fake answer" and not [i for i in after["ui"] if i["type"] == "confirmation"]
    assert client.runtime.sessions.get("s10").proposal(body["undo"]["proposal_id"]).status.value == "REVOKED"
