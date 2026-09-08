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

    # /health asks ElevenLabs whether the account is alive. On the owner's Mac the key is in
    # the Keychain and that would be a real call to a paid API on every test run.
    from app.clients.elevenlabs import ScribeClient

    async def fake_scribe_health(self):
        return True, "fake scribe"

    monkeypatch.setattr(ScribeClient, "health", fake_scribe_health)

    # And the voice must not read the owner's real Keychain entry to report itself healthy.
    from app.clients.elevenlabs_tts import VoiceClient

    monkeypatch.setattr(
        VoiceClient, "health", lambda self: (True, f"key ok · ElevenLabs {self.voice_name}")
    )
    async with app.router.lifespan_context(app):
        app.state.runtime.provider = FakeProvider()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            yield c


async def test_health_names_each_subsystem(client):
    body = (await client.get("/health")).json()
    assert body["status"] in {"ok", "degraded"}
    assert {
        "claude", "scribe", "whisper", "speech", "tts", "shopify", "gmail", "knowledge_base",
        "terminology",
    } <= body["checks"].keys()
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


# --------------------------------------------------------------------------- POST /speak
#
# The voice is an output layer. Every test below is a way it can fail, and in all of them the
# answer still exists: /turn is untouched, and the tablet is told plainly enough to fall back.


class FakeVoiceStream:
    def __init__(self, body: bytes) -> None:
        self.body = body

    async def chunks(self):
        # Two chunks, because the tablet must survive a body arriving in pieces.
        yield self.body[: len(self.body) // 2]
        yield self.body[len(self.body) // 2 :]


def stub_voice(client_app, *, audio: bytes | None = None, fail: str | None = None):
    """Replace the runtime's ElevenLabs client. No test may spend a credit."""
    from app.clients.elevenlabs_tts import VoiceUnavailable

    voice = client_app.state.runtime.voice
    calls: list[str] = []

    async def open_stream(text: str):
        calls.append(text)
        if fail:
            raise VoiceUnavailable("stubbed failure", kind=fail)
        return FakeVoiceStream(audio or b"\xff\xfb\x90\x00mp3")

    voice.open_stream = open_stream  # type: ignore[method-assign]
    return calls


async def test_speak_returns_vikram_as_mp3(client):
    calls = stub_voice(app, audio=b"\xff\xfb\x90\x00" + b"\x00" * 64)
    response = await client.post("/speak", json={"text": "Twelve orders today."})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.content.startswith(b"\xff\xfb")
    assert response.headers["x-crooks-model"] == app.state.runtime.voice.model
    assert calls == ["Twelve orders today."]


async def test_speak_says_the_prepared_text_not_the_written_one(client):
    calls = stub_voice(app)
    await client.post("/speak", json={"text": "**Order #1930** came to £60."})
    assert calls == ["Order nineteen thirty came to sixty pounds."]


async def test_speak_never_returns_the_key_or_the_account_detail(client):
    stub_voice(app, fail="rejected")
    response = await client.post("/speak", json={"text": "Twelve orders today."})
    assert response.status_code == 503
    body = response.json()
    assert body["ok"] is False and body["kind"] == "rejected"
    # A reason the owner can act on, with nothing from ElevenLabs' own error in it.
    assert "key" in body["reason"]
    assert "xi-api-key" not in response.text and "sk_" not in response.text


async def test_speak_failure_is_a_503_the_tablet_can_fall_back_from(client):
    for kind in ("no_key", "credit", "timeout", "network", "cooldown", "off"):
        stub_voice(app, fail=kind)
        response = await client.post("/speak", json={"text": "Twelve orders today."})
        assert response.status_code == 503, kind
        assert response.json()["kind"] == kind


async def test_speak_says_nothing_rather_than_paying_to_say_nothing(client):
    calls = stub_voice(app)
    for text in ("", "   ", "...", "***"):
        response = await client.post("/speak", json={"text": text})
        assert response.status_code == 204
    assert calls == []


async def test_speak_never_logs_the_answer(client, caplog):
    import logging

    stub_voice(app)
    with caplog.at_level(logging.DEBUG, logger="crooks.speak"):
        await client.post("/speak", json={"text": "Jane Smith's order 1930 is late."})
    assert "Jane" not in caplog.text


async def test_a_turn_still_answers_when_the_voice_is_broken(client):
    """The point of the whole design: TTS is not a dependency of Shopify, Gmail or Claude."""
    stub_voice(app, fail="credit")
    turn = (await client.post("/turn", json={"text": "how many orders today"})).json()
    assert turn["answer"]
    assert turn["error_kind"] is None
    assert (await client.post("/speak", json={"text": turn["answer"]})).status_code == 503


async def test_health_names_the_voice(client):
    body = (await client.get("/health")).json()
    assert body["voice"]["voice"] == app.state.runtime.settings.tts_voice_name
    assert body["voice"]["model"] == "eleven_flash_v2_5"
    assert body["voice"]["provider"] == "elevenlabs"
    assert "Derek" in body["checks"]["tts"]["detail"]


async def test_the_configured_voice_is_the_one_that_was_approved(client):
    settings = app.state.runtime.settings
    assert settings.tts_voice_id == "Q0Et7LOU7VpeoeCRQAVS"
    assert settings.tts_model == "eleven_flash_v2_5"
    assert settings.tts_output_format == "mp3_44100_128"


# --------------------------------------------------------------------------- the ui contract


async def test_turn_returns_structured_ui_chosen_from_tool_results(client):
    """The cards come from the tool payloads, and the payloads themselves stay on the Mac."""
    from app.providers.base import ToolCall, TurnResult

    async def turn(session_id, text):
        app.state.runtime.sessions.get_or_create(session_id)   # as the real provider does
        return TurnResult(text="Order 1930 is unfulfilled.", session_id=session_id, tool_calls=[
            ToolCall(name="shopify_find_order", args={"query": "1930"}, result={"orders": [{
                "order_id": "gid://shopify/Order/1", "order_number": "CROOKS-1930", "total": "60.00 GBP",
                "fulfillment": "UNFULFILLED", "payment": "PAID", "customer_name": "Jo Bloggs",
                "customer_id": "gid://shopify/Customer/2", "placed_at": "2026-09-08T10:00:00Z",
            }]}),
        ])

    app.state.runtime.provider.turn = turn
    body = (await client.post("/turn", json={"text": "show me order 1930", "session_id": "ui1"})).json()
    assert [item["type"] for item in body["ui"]] == ["order", "context_stack"]
    assert body["ui"][0]["data"]["order_number"] == "#1930"
    assert body["ui"][0]["data"]["total"] == "£60.00"
    assert "result" not in body["tool_calls"][0]


async def test_error_turns_carry_an_error_card(client):
    body = (await client.post("/turn", json={"text": "  ", "session_id": "ui2"})).json()
    assert body["ui"] == [{"type": "error", "data": {
        "service": "speech", "kind": "empty", "title": "Didn't catch that", "recovery": "Hold the orb while you speak.",
    }}]


async def test_ui_is_always_present_and_a_list(client):
    body = (await client.post("/turn", json={"text": "hello", "session_id": "ui3"})).json()
    assert isinstance(body["ui"], list)
