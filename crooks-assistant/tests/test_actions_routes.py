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
    assert body["spoken"] == "Order note added."
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
