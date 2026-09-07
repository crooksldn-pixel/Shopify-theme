"""The HTTP surface, driven through ASGI.

The real Claude provider is swapped for a fake before any request is made. On a machine where
the claude CLI is logged in, the real provider WOULD answer — and a test suite that spends the
Max allowance on every run is exactly the mistake the build plan warns about.
"""

from __future__ import annotations

import httpx
import pytest

from app.main import app
from app.providers.base import ClaudeProvider, TurnResult


class FakeProvider(ClaudeProvider):
    def __init__(self) -> None:
        self.turns: list[tuple[str, str]] = []

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def turn(self, session_id: str, text: str) -> TurnResult:
        self.turns.append((session_id, text))
        return TurnResult(text=f"fake answer to {len(text)} chars", session_id=session_id)

    async def health(self) -> tuple[bool, str]:
        return True, "fake"

    async def reset_session(self, session_id: str) -> None:
        pass


@pytest.fixture()
async def client(monkeypatch):
    # Stop the lifespan from starting the real provider at all.
    from app.providers import max_agent_sdk

    async def no_start(self):
        raise RuntimeError("tests never start the real Claude provider")

    monkeypatch.setattr(max_agent_sdk.MaxAgentSDKProvider, "start", no_start)
    async with app.router.lifespan_context(app):
        app.state.runtime.provider = FakeProvider()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            yield c


async def test_health_names_each_subsystem(client):
    body = (await client.get("/health")).json()
    assert body["status"] in {"ok", "degraded"}
    assert {"claude", "whisper", "shopify", "gmail", "knowledge_base", "terminology"} <= body["checks"].keys()
    for check in body["checks"].values():
        assert set(check) == {"ok", "detail"}
    assert "version" in body and "uptime_s" in body


async def test_tools_endpoint_lists_tiers(client):
    tools = (await client.get("/tools")).json()["tools"]
    tiers = {t["name"]: t["tier"] for t in tools}
    assert tiers["mock_danger"] == "RED"
    assert tiers["shopify_order_detail"] == "AMBER"
    assert tiers["shopify_list_orders"] == "GREEN"


async def test_empty_text_is_handled(client):
    body = (await client.post("/turn", json={"text": "  ", "session_id": "e"})).json()
    assert body["error_kind"] == "empty"


async def test_lost_thread_when_tablet_expects_a_session(client):
    body = (await client.post("/turn", json={"text": "and that?", "session_id": "ghost", "turns": 2})).json()
    assert body["error_kind"] == "lost_thread"
    assert body["lost_thread"] is True
    assert "lost the thread" in body["answer"]


async def test_new_session_with_zero_turns_is_not_lost(client):
    body = (await client.post("/turn", json={"text": "hello", "session_id": "fresh", "turns": 0})).json()
    assert body["error_kind"] != "lost_thread"


async def test_state_endpoint_for_unknown_session(client):
    body = (await client.get("/state/nobody")).json()
    assert body == {"session_id": "nobody", "known": False, "state": "READY", "detail": ""}


async def test_undecodable_audio_is_a_named_speech_error(client):
    files = {"audio": ("t.webm", b"\x00" * 64, "audio/webm")}
    body = (await client.post("/turn", data={"session_id": "a", "turns": "0"}, files=files)).json()
    assert body["error_kind"] == "speech"
    assert body["answer"]


async def test_audio_test_reports_decode_failure(client):
    files = {"audio": ("t.webm", b"junk", "audio/webm")}
    body = (await client.post("/audio-test", files=files)).json()
    assert body["ok"] is False and "error" in body


async def test_text_is_capped(client):
    body = (await client.post("/turn", json={"text": "x" * 10_000, "session_id": "cap"})).json()
    assert body["error_kind"] is None
    assert body["answer"] == "fake answer to 2000 chars"
    assert body["turns"] == 0  # the fake provider does not bump the session's turn count


async def test_turn_goes_through_the_provider_once(client):
    body = (await client.post("/turn", json={"text": "hello", "session_id": "once"})).json()
    assert body["answer"].startswith("fake answer")
    assert app.state.runtime.provider.turns == [("once", "hello")]


async def test_real_provider_is_never_started_by_tests(client):
    from app.providers.max_agent_sdk import MaxAgentSDKProvider

    assert not isinstance(app.state.runtime.provider, MaxAgentSDKProvider)


async def test_reload_kb(client):
    body = (await client.post("/reload-kb")).json()
    assert body["reloaded"] is True


async def test_reset(client):
    body = (await client.post("/reset", data={"session_id": "x"})).json()
    assert body == {"reset": True}


async def test_index_serves_the_tablet_page(client):
    r = await client.get("/")
    assert r.status_code == 200 and "CROOKS" in r.text


async def test_reload_kb_resets_the_provider_prompt(client):
    provider = app.state.runtime.provider
    provider.prompts = []

    async def set_system_prompt(prompt):
        provider.prompts.append(prompt)

    provider.set_system_prompt = set_system_prompt
    body = (await client.post("/reload-kb")).json()
    assert body["reloaded"] and provider.prompts and "CROOKS" in provider.prompts[0]


async def test_audio_test_returns_playable_wav(client):
    pytest.importorskip("av")
    from tests.test_decode import tone_pcm, webm_opus

    files = {"audio": ("t.webm", webm_opus(tone_pcm(0.5)), "audio/webm")}
    body = (await client.post("/audio-test", files=files)).json()
    assert body["ok"] and body["wav_base64"].startswith("UklGR")  # "RIFF" in base64


async def test_tool_calls_carry_redacted_args(client):
    from app.providers.base import ToolCall, TurnResult

    async def turn(session_id, text):
        return TurnResult(text="ok", session_id=session_id, tool_calls=[
            ToolCall(name="gmail_search", args={"query": "from:jo@example.com", "days": 1})
        ])

    app.state.runtime.provider.turn = turn
    body = (await client.post("/turn", json={"text": "hi", "session_id": "args"})).json()
    call = body["tool_calls"][0]
    assert call["args"]["days"] == "1"
    assert "jo@example.com" not in call["args"]["query"]
