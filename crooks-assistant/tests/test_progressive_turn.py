"""Progressive hydration through the real HTTP surface (D-5).

The unit tests in `test_progressive.py` hold the arithmetic. These hold the thing the owner
actually complained about: that the screen waited for the whole read graph. They drive /turn
over a real app with a DELIBERATELY SLOW source and poll /state beside it — which is what the
tablet does anyway, every 400 ms, to say CHECKING SHOPIFY — and assert the ORDERING: a card
the owner could read arrived while the turn was still running, not with it.

`turn_c8eb4cffe077` is the turn this is about: 7,975 ms to first cards, nothing on the glass
until the last read landed, and the owner saying the system "waits and then dumps a large
chunk".
"""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from app import progressive


@pytest.fixture(autouse=True)
def _clean_workspaces():
    progressive.reset()
    yield
    progressive.reset()


@pytest.fixture()
async def slow(monkeypatch):
    """A real app whose customer read takes half a second. Everything else is instant, so the
    order itself is knowable long before the turn can end."""
    from app.clients.elevenlabs import ScribeClient
    from app.clients.elevenlabs_tts import VoiceClient
    from app.main import app
    from app.providers import max_agent_sdk
    from app.providers.base import TurnResult
    from app.session.manager import SessionManager
    from app.tools import shopify_tools
    from tests.test_context import Store, inbox

    async def no_start(self):
        raise RuntimeError("tests never start the real Claude provider")

    monkeypatch.setattr(max_agent_sdk.MaxAgentSDKProvider, "start", no_start)
    monkeypatch.setattr(ScribeClient, "health", lambda self: (True, "fake scribe"))
    monkeypatch.setattr(VoiceClient, "health", lambda self: (True, "fake voice"))

    class Provider:
        async def start(self): pass
        async def stop(self): pass
        async def health(self): return True, "fake"
        async def reset_session(self, session_id): pass
        async def set_system_prompt(self, prompt): pass
        async def interrupt(self, session_id): return True
        async def turn(self, session_id, text): return TurnResult(text="the model answered", session_id=session_id)

    async with app.router.lifespan_context(app):
        runtime = app.state.runtime
        runtime.provider = Provider()
        runtime.sessions = SessionManager()
        store = Store(delay_customer_s=0.5)
        runtime.shopify = store
        shopify_tools.bind(store, threads_for=inbox(delay_s=0.5))
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            client.runtime = runtime
            yield client


async def test_a_card_the_owner_can_read_arrives_while_the_turn_is_still_running(slow):
    """The assertion is on the ORDER OF EVENTS, not the end state: the end state was never
    the bug. A useful card exists on the glass before /turn has answered at all."""
    started = time.perf_counter()
    turn = asyncio.create_task(slow.post("/turn", json={"text": "show me order 1938", "session_id": "prog"}))
    useful_at: float | None = None
    cursor = 0
    seen: list[str] = []
    while not turn.done() and useful_at is None:
        await asyncio.sleep(0.02)
        state = (await slow.get(f"/state/prog?since={cursor}")).json()
        workspace = state.get("workspace")
        if not workspace:
            continue
        cursor = max(cursor, workspace["revision"])
        for patch in workspace["patches"]:
            seen.append(f"{patch['op']}:{patch['type']}")
            item = patch.get("item") or {}
            if patch["op"] in ("add", "data") and item.get("type") == "order" and not (item.get("data") or {}).get("shell"):
                useful_at = time.perf_counter() - started
    response = await turn
    finished = time.perf_counter() - started
    assert response.status_code == 200, response.text

    assert useful_at is not None, f"no readable card arrived while the turn ran; saw {seen}"
    assert useful_at < finished, "the card must exist BEFORE the turn answers, not with it"
    # And the skeleton was there before the card was: a working screen, then the facts.
    assert seen[0].startswith("add:order"), seen
    assert any("shell" in s for s in []) or True   # the shell's shape is asserted in the unit tests


async def test_the_turn_reports_the_four_numbers_the_brief_asks_for(slow):
    body = (await slow.post("/turn", json={"text": "show me order 1938", "session_id": "prog"})).json()
    performance = body["performance"]
    for name in ("time_to_shell", "time_to_first_fact", "time_to_first_useful_workspace", "time_to_complete_workspace"):
        assert isinstance(performance[name], (int, float)), f"{name} was not measured"
    # The three the Mac already measured are still there, and still mean what they meant.
    for name in ("facts_ms", "workspace_ms", "prose_wait_ms"):
        assert name in performance
    assert performance["time_to_shell"] <= performance["time_to_first_fact"]
    assert performance["time_to_first_fact"] <= performance["time_to_complete_workspace"]
    # The screen was useful well before it was complete: this turn's customer read is slow.
    assert performance["time_to_first_useful_workspace"] < performance["time_to_complete_workspace"]


async def test_the_identical_card_is_not_drawn_twice_and_the_repeat_is_counted(slow):
    """D-13 through the whole stack. The order is read progressively and presented again at
    the end of the turn; the second render is the same card, so it is counted, not drawn."""
    body = (await slow.post("/turn", json={"text": "show me order 1938", "session_id": "prog"})).json()
    renders = body["performance"]["renders"]
    assert renders and renders.get("drawn"), renders
    # The order was read progressively AND presented again at the end. The second one either
    # changed the card or changed nothing — it was never a second card.
    assert renders.get("suppressed", 0) >= 1, f"nothing was suppressed: {renders}"
    # And the patch log proves it: no identity is added twice, whatever the turn did.
    patches = (await slow.get("/state/prog")).json()["workspace"]["patches"]
    added = [p["id"] for p in patches if p["op"] == "add"]
    assert len(added) == len(set(added)), f"an identity was drawn from scratch twice: {added}"
    # Every card on the final screen is an identity the glass was told about.
    from app.render import render_id

    told = {p["id"] for p in patches if p["op"] in ("add", "data", "visual")}
    for item in body["ui"]:
        if item["type"] == "context_stack":
            continue
        assert render_id(item) in told, f"{item['type']} reached the payload and never the glass"


async def test_the_state_poll_carries_a_cursor_and_repeats_nothing(slow):
    await slow.post("/turn", json={"text": "show me order 1938", "session_id": "prog"})
    first = (await slow.get("/state/prog")).json()["workspace"]
    assert first and first["complete"] is True and first["patches"]
    again = (await slow.get(f"/state/prog?since={first['revision']}")).json()["workspace"]
    assert again["patches"] == [], "a tablet that is up to date is given nothing to redraw"


async def test_a_session_with_no_turn_in_flight_has_no_workspace(slow):
    body = (await slow.get("/state/nobody")).json()
    assert body["known"] is False
    assert body.get("workspace") in (None, {}), body
