"""Derek: the ElevenLabs voice, and the Android voice that catches him when he falls.

Nothing here touches the network, the Keychain or a paid API: the HTTP layer is a transport
double and the credential is injected. The rules these tests exist to hold are that the tablet
is never left silent — every way ElevenLabs can fail ends in a 503 the tablet reads as "use
your own voice" — and that the API key never reaches the tablet, a log line, an exception or a
health string.
"""

from __future__ import annotations

import logging

import httpx
import pytest

from app.clients.elevenlabs_tts import VoiceClient, VoiceUnavailable

SECRET = "sk_elevenlabs_test_key_0123456789abcdef"
VOICE_ID = "Q0Et7LOU7VpeoeCRQAVS"
MODEL = "eleven_flash_v2_5"
OUTPUT_FORMAT = "mp3_44100_128"

# Enough of an MP3 frame header to be recognisably audio; nothing decodes it here.
MP3 = b"\xff\xfb\x90\x00" + b"\x00" * 512


@pytest.fixture()
def mock_http(monkeypatch):
    """Route every httpx.AsyncClient created inside the client at a handler we control."""
    holder: dict[str, object] = {"handler": None, "requests": []}
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        def handler(request: httpx.Request) -> httpx.Response:
            holder["requests"].append(request)
            return holder["handler"](request)

        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)

    def install(handler):
        holder["handler"] = handler
        return holder

    return install


def make(**kwargs) -> VoiceClient:
    client = VoiceClient(
        voice_id=VOICE_ID, voice_name="Derek", model=MODEL, output_format=OUTPUT_FORMAT,
        **kwargs,
    )
    client._key = SECRET  # injected: the Keychain is never read in a test
    return client


def audio(status: int = 200, body: bytes = MP3):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=body, headers={"content-type": "audio/mpeg"})

    return handler


def error(status: int, body: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=body)

    return handler


# --------------------------------------------------------------------------- the request


async def test_the_request_is_the_one_the_owner_approved(mock_http):
    """Voice, model and format are the settings that were auditioned. If any of them drifts,
    the tablet speaks with a voice nobody chose."""
    holder = mock_http(audio())
    assert await make().synthesise("Twelve orders today.") == MP3

    request = holder["requests"][0]
    assert request.method == "POST"
    assert request.url.path == f"/v1/text-to-speech/{VOICE_ID}/stream"
    assert request.url.params["output_format"] == OUTPUT_FORMAT
    import json

    body = json.loads(request.content)
    assert body == {"text": "Twelve orders today.", "model_id": MODEL}
    # Voice settings are deliberately absent: the voice's own defaults are what was approved.
    assert "voice_settings" not in body


async def test_the_key_travels_in_the_header_and_nowhere_else(mock_http):
    holder = mock_http(audio())
    await make().synthesise("hello")
    request = holder["requests"][0]
    assert request.headers["xi-api-key"] == SECRET
    assert SECRET not in request.content.decode()
    assert SECRET not in str(request.url)


async def test_the_key_is_read_from_the_keychain_server_side(monkeypatch, mock_http):
    reads: list[str] = []

    def fake_get_optional(key: str):
        reads.append(key)
        return SECRET

    from app.secrets import keychain

    monkeypatch.setattr(keychain, "get_optional", fake_get_optional)
    holder = mock_http(audio())
    client = VoiceClient(voice_id=VOICE_ID, model=MODEL, output_format=OUTPUT_FORMAT)
    await client.synthesise("hello")
    assert reads == ["elevenlabs_api_key"]
    assert holder["requests"][0].headers["xi-api-key"] == SECRET


async def test_text_is_bounded_before_it_is_billed(mock_http):
    holder = mock_http(audio())
    await make(max_chars=20).synthesise("x" * 500)
    import json

    assert len(json.loads(holder["requests"][0].content)["text"]) == 20


async def test_a_successful_mp3_arrives_whole(mock_http):
    mock_http(audio(body=MP3 * 3))
    client = make()
    assert await client.synthesise("hello") == MP3 * 3
    assert client.successes == 1 and client.failures == 0
    assert client.last_bytes == len(MP3) * 3


async def test_the_stream_yields_before_it_ends(mock_http):
    """The point of streaming: bytes leave the Mac as they arrive, not after the last one."""
    mock_http(audio(body=MP3))
    stream = await make().open_stream("hello")
    chunks = [chunk async for chunk in stream.chunks()]
    assert chunks and b"".join(chunks) == MP3


# --------------------------------------------------------------------------- failure


@pytest.mark.parametrize(
    "status,body,kind",
    [
        (401, '{"detail":{"status":"invalid_api_key"}}', "rejected"),
        (403, "missing_permissions", "forbidden"),
        (429, "quota exceeded", "credit"),
        (402, "payment required", "credit"),
        (404, '{"detail":{"status":"voice_not_found"}}', "no_voice"),
        (500, "upstream exploded", "server_error"),
        (418, "teapot", "http_418"),
    ],
)
async def test_every_http_failure_has_a_name(mock_http, status, body, kind):
    mock_http(error(status, body))
    client = make()
    with pytest.raises(VoiceUnavailable) as caught:
        await client.synthesise("hello")
    assert caught.value.kind == kind
    assert client.failures == 1 and client.successes == 0


async def test_a_timeout_is_a_named_failure_not_a_hang(monkeypatch):
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("too slow", request=request)

        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    with pytest.raises(VoiceUnavailable) as caught:
        await make(timeout_s=1.0).synthesise("hello")
    assert caught.value.kind == "timeout"


async def test_no_key_is_a_failure_the_owner_can_act_on(monkeypatch):
    from app.secrets import keychain

    monkeypatch.setattr(keychain, "get_optional", lambda key: None)
    client = VoiceClient(voice_id=VOICE_ID)
    with pytest.raises(VoiceUnavailable) as caught:
        await client.synthesise("hello")
    assert caught.value.kind == "no_key"
    assert "set_secrets.py" in str(caught.value)


async def test_an_empty_response_is_a_failure_not_a_silence(mock_http):
    mock_http(audio(body=b""))
    client = make()
    with pytest.raises(VoiceUnavailable) as caught:
        await client.synthesise("hello")
    assert caught.value.kind == "empty_audio"


async def test_a_dead_account_stops_being_asked(mock_http):
    """A rejected key does not recover between two sentences. Asking anyway costs the owner a
    pause before the Android voice starts."""
    mock_http(error(401, "invalid_api_key"))
    client = make(cooldown_s=300.0)
    with pytest.raises(VoiceUnavailable):
        await client.synthesise("hello")
    assert client.cooling_down
    with pytest.raises(VoiceUnavailable) as caught:
        await client.synthesise("hello again")
    assert caught.value.kind == "cooldown"
    assert client.attempts == 1  # the second answer never reached ElevenLabs


async def test_a_recoverable_failure_is_retried_next_time(mock_http):
    mock_http(error(500, "upstream exploded"))
    client = make(cooldown_s=300.0)
    with pytest.raises(VoiceUnavailable):
        await client.synthesise("hello")
    assert not client.cooling_down


async def test_switching_the_voice_off_costs_nothing(mock_http):
    holder = mock_http(audio())
    client = make(enabled=False)
    with pytest.raises(VoiceUnavailable) as caught:
        await client.synthesise("hello")
    assert caught.value.kind == "off"
    assert not holder["requests"]


async def test_nothing_to_say_is_not_a_request(mock_http):
    holder = mock_http(audio())
    with pytest.raises(VoiceUnavailable) as caught:
        await make().synthesise("   ")
    assert caught.value.kind == "empty_text"
    assert not holder["requests"]


# --------------------------------------------------------------------------- the credential


async def test_the_key_never_reaches_a_log_line_or_an_exception(mock_http, caplog):
    """ElevenLabs echoing the key back in an error body is the realistic way it would leak."""
    mock_http(error(401, f'{{"detail":"key {SECRET} is invalid"}}'))
    client = make()
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(VoiceUnavailable) as caught:
            await client.synthesise("hello")
    assert SECRET not in str(caught.value)
    assert SECRET not in client.last_error
    assert SECRET not in caplog.text
    assert "[redacted]" in str(caught.value)


async def test_health_never_names_the_key(monkeypatch):
    client = make()
    ok, detail = client.health()
    assert ok
    assert SECRET not in detail
    assert "Derek" in detail and MODEL in detail and OUTPUT_FORMAT in detail


def test_health_without_a_key_says_how_to_fix_it(monkeypatch):
    from app.secrets import keychain

    monkeypatch.setattr(keychain, "get_optional", lambda key: None)
    ok, detail = VoiceClient(voice_id=VOICE_ID, voice_name="Derek").health()
    assert not ok
    assert "set_secrets.py" in detail


def test_health_costs_nothing(monkeypatch):
    """A health check that synthesises a sentence on every poll is a bill, not a check."""
    def explode(*args, **kwargs):
        raise AssertionError("/health must not call ElevenLabs")

    monkeypatch.setattr(httpx, "AsyncClient", explode)
    assert make().health()[0]


async def test_health_reports_a_cooldown_rather_than_pretending(mock_http):
    mock_http(error(429, "quota exceeded"))
    client = make(cooldown_s=300.0)
    with pytest.raises(VoiceUnavailable):
        await client.synthesise("hello")
    ok, detail = client.health()
    assert not ok
    assert "credit" in detail
