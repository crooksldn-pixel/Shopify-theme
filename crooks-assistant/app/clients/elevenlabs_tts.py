"""HTTP client for ElevenLabs text-to-speech — the assistant's voice.

The sibling module (elevenlabs.py) turns the owner's speech into text; this one turns the
answer back into speech. Same account, same credential, same two rules:

- Nothing here may leak the credential. The key is read through the Keychain wrapper, held in
  memory only, sent in one header, and every message this module produces goes through
  _scrub(). It is never handed to the tablet, so web/app.js has no way to leak it either.
- Nothing here may cost the owner an answer. Speech is an output layer: every failure is one
  named VoiceUnavailable, /speak turns that into a 503, and the tablet falls back to the
  Android voice it used before. A silent tablet is a bug; a broken turn is a worse one.

The MP3 is streamed out of ElevenLabs and through FastAPI as it arrives rather than being
buffered here, so the first bytes leave the Mac before the last ones have been generated.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator

import httpx

from app.secrets import keychain

log = logging.getLogger("crooks.voice")

API_BASE = "https://api.elevenlabs.io/v1"

# The same shapes of failure that make Scribe stand down: a key that will not be accepted and
# an account with nothing left in it do not recover between two sentences, and retrying them
# on every answer costs the owner a pause before the Android voice starts.
STICKY_KINDS = frozenset({"no_key", "rejected", "forbidden", "credit"})


class VoiceUnavailable(RuntimeError):
    """ElevenLabs cannot speak this answer. The tablet falls back to its own voice.

    `kind` is the machine-readable shape of the failure (timeout, rejected, credit, …); it is
    what gets logged and reported. str(exc) is the human detail, already scrubbed."""

    def __init__(self, detail: str, *, kind: str) -> None:
        super().__init__(detail)
        self.kind = kind


class VoiceStream:
    """An MP3 arriving from ElevenLabs, forwarded chunk by chunk.

    Constructed only after the response headers have come back 200, so the caller already knows
    the request succeeded before it commits to an audio/mpeg response with no way back."""

    def __init__(self, client: VoiceClient, http: httpx.AsyncClient, response: httpx.Response,
                 started: float) -> None:
        self._client = client
        self._http = http
        self._response = response
        self._started = started
        self.bytes_out = 0

    async def chunks(self) -> AsyncIterator[bytes]:
        truncated = ""
        try:
            async for chunk in self._response.aiter_bytes():
                if chunk:
                    self.bytes_out += len(chunk)
                    yield chunk
        except httpx.HTTPError as exc:
            # The tablet already has the opening of the sentence and is playing it; there is
            # no status code left to change. Say so in the log, which is where it is findable.
            truncated = f" TRUNCATED after {type(exc).__name__}"
        finally:
            await self.aclose()
            self._client._finish(self, truncated)

    async def aclose(self) -> None:
        try:
            await self._response.aclose()
        finally:
            await self._http.aclose()

    @property
    def ms(self) -> float:
        return (time.perf_counter() - self._started) * 1000


class VoiceClient:
    def __init__(
        self,
        *,
        voice_id: str,
        voice_name: str = "",
        model: str = "eleven_flash_v2_5",
        output_format: str = "mp3_44100_128",
        timeout_s: float = 20.0,
        base_url: str = API_BASE,
        max_chars: int = 1200,
        cooldown_s: float = 300.0,
        enabled: bool = True,
    ) -> None:
        self.voice_id = voice_id
        self.voice_name = voice_name or voice_id
        self.model = model
        self.output_format = output_format
        self.base_url = base_url.rstrip("/")
        self.max_chars = max_chars
        self.enabled = enabled
        self._timeout = timeout_s
        self._cooldown_s = cooldown_s
        self._key: str | None = None
        self._cooldown_until = 0.0
        # Non-sensitive diagnostics for /health. Never the text that was spoken.
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.last_error: str = ""
        self.last_error_kind: str = ""
        self.last_ms: float = 0.0
        self.last_bytes: int = 0

    # ------------------------------------------------------------------ credential

    def _api_key(self) -> str:
        """The key, from the Keychain, cached in memory once found. A *missing* key is not
        cached, so storing it later starts working without a restart."""
        if not self._key:
            self._key = keychain.get_optional("elevenlabs_api_key") or ""
        if not self._key:
            raise VoiceUnavailable(
                "no elevenlabs_api_key in the Keychain "
                "(store it with: python scripts/set_secrets.py elevenlabs_api_key)",
                kind="no_key",
            )
        return self._key

    def _scrub(self, text: str) -> str:
        """Last line of defence: no message this module emits may contain the credential."""
        key = self._key
        if key and len(key) >= 8 and key in text:
            text = text.replace(key, "[redacted]")
        return text

    def forget_key(self) -> None:
        self._key = None

    # ------------------------------------------------------------------ cooldown

    @property
    def cooling_down(self) -> bool:
        return time.time() < self._cooldown_until

    @property
    def cooldown_remaining_s(self) -> float:
        return max(0.0, self._cooldown_until - time.time())

    def clear_cooldown(self) -> None:
        self._cooldown_until = 0.0

    def _record_failure(self, exc: VoiceUnavailable) -> VoiceUnavailable:
        self.failures += 1
        self.last_error_kind = exc.kind
        self.last_error = self._scrub(str(exc))[:200]
        if exc.kind in STICKY_KINDS and self._cooldown_s > 0:
            self._cooldown_until = time.time() + self._cooldown_s
            if exc.kind in {"rejected", "forbidden"}:
                self.forget_key()  # the stored key may have been replaced since we read it
        log.warning(
            "tts unavailable (%s): %s — the tablet will use its own voice", exc.kind,
            self.last_error,
        )
        return exc

    def _finish(self, stream: VoiceStream, truncated: str) -> None:
        self.last_ms = stream.ms
        self.last_bytes = stream.bytes_out
        if truncated or not stream.bytes_out:
            self.failures += 1
            self.last_error_kind = "truncated" if truncated else "empty"
            self.last_error = (truncated or "ElevenLabs sent no audio").strip()
            log.warning(
                "tts %s · %s · %s · %.0fms · %d bytes%s", self.last_error_kind, self.voice_name,
                self.model, stream.ms, stream.bytes_out, truncated,
            )
            return
        self.successes += 1
        self.clear_cooldown()
        log.info(
            "tts ok · %s · %s · %s · %.0fms · %d bytes", self.voice_name, self.model,
            self.output_format, stream.ms, stream.bytes_out,
        )

    # ------------------------------------------------------------------ request

    def _payload(self, text: str) -> dict:
        """The request body. Voice settings are deliberately absent: the voice's own defaults
        are what was auditioned and approved, and the API applies them when we say nothing."""
        return {"text": text, "model_id": self.model}

    def _url(self, *, stream: bool) -> str:
        path = f"/text-to-speech/{self.voice_id}" + ("/stream" if stream else "")
        return f"{self.base_url}{path}?output_format={self.output_format}"

    def _guard(self, text: str) -> str:
        if not self.enabled:
            raise VoiceUnavailable("ElevenLabs speech is switched off in settings", kind="off")
        text = (text or "").strip()
        if not text:
            raise VoiceUnavailable("nothing to say", kind="empty_text")
        if self.cooling_down:
            raise VoiceUnavailable(
                f"skipped: cooling down for {self.cooldown_remaining_s:.0f}s after "
                f"{self.last_error_kind or 'a failure'}",
                kind="cooldown",
            )
        return text[: self.max_chars]

    async def open_stream(self, text: str) -> VoiceStream:
        """Start the request and return once the headers say it worked.

        Splitting the handshake from the body is the whole point: a 401 or an exhausted account
        is discovered here, while a JSON error response is still possible, rather than halfway
        through an audio/mpeg body the tablet is already playing."""
        text = self._guard(text)
        key = self._api_key()
        self.attempts += 1
        started = time.perf_counter()
        http = httpx.AsyncClient(timeout=self._timeout)
        request = http.build_request(
            "POST",
            self._url(stream=True),
            headers={"xi-api-key": key, "accept": "audio/mpeg"},
            json=self._payload(text),
        )
        try:
            response = await http.send(request, stream=True)
        except httpx.TimeoutException as exc:
            await http.aclose()
            raise self._record_failure(
                VoiceUnavailable(f"no response in {self._timeout:.0f}s", kind="timeout")
            ) from exc
        except httpx.HTTPError as exc:
            await http.aclose()
            raise self._record_failure(
                VoiceUnavailable(f"request failed: {type(exc).__name__}", kind="network")
            ) from exc

        if response.status_code != 200:
            body = ""
            try:
                body = (await response.aread()).decode("utf-8", "replace")
            except httpx.HTTPError:
                pass
            finally:
                await response.aclose()
                await http.aclose()
            raise self._record_failure(self._http_failure(response.status_code, body))
        return VoiceStream(self, http, response, started)

    async def synthesise(self, text: str) -> bytes:
        """The whole MP3, for scripts and tests. The tablet uses open_stream()."""
        stream = await self.open_stream(text)
        audio = b"".join([chunk async for chunk in stream.chunks()])
        if not audio:
            raise self._record_failure(
                VoiceUnavailable("ElevenLabs returned no audio", kind="empty_audio")
            )
        return audio

    def _http_failure(self, code: int, body: str) -> VoiceUnavailable:
        """Name the failure by its shape. The body is included because it is what makes an
        account problem diagnosable — scrubbed, and truncated, because it is not ours."""
        body = self._scrub(body[:200])
        lowered = body.lower()
        if code in (401, 403) or "invalid_api_key" in lowered:
            kind = "rejected" if code == 401 else "forbidden"
        elif code in (402, 429) or "quota" in lowered or "credit" in lowered:
            kind = "credit"
        elif code == 404 or "voice_not_found" in lowered:
            kind = "no_voice"
        elif code >= 500:
            kind = "server_error"
        else:
            kind = f"http_{code}"
        return VoiceUnavailable(f"ElevenLabs returned {code}: {body}", kind=kind)

    # ------------------------------------------------------------------ health

    def health(self) -> tuple[bool, str]:
        """Is the voice usable? Answered from configuration and the Keychain, with no request:
        a health check that synthesises a sentence on every poll is a bill, not a check. The
        account itself is already probed once, by the Scribe check, on the same credential."""
        note = f"ElevenLabs {self.voice_name} · {self.model} · {self.output_format}"
        if not self.enabled:
            return True, f"not in use (CROOKS_TTS_ENABLED=false) · {note}"
        try:
            self._api_key()
        except VoiceUnavailable as exc:
            return False, f"{self._scrub(str(exc))} · {note}"
        if self.attempts:
            note += (
                f" · {self.successes}/{self.attempts} ok, last {self.last_ms:.0f}ms, "
                f"{self.last_bytes} bytes"
            )
        if self.cooling_down:
            return False, (
                f"{note} · SKIPPING ElevenLabs for {self.cooldown_remaining_s:.0f}s after "
                f"{self.last_error_kind}: {self.last_error}"
            )
        return True, f"key ok · {note}"
