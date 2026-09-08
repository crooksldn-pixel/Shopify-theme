"""What the tablet is allowed to know, and what it must do with the voice.

The client is JavaScript and there is no browser in this suite, so these are read as source
(the renderer itself is exercised under Node — see test_web_js.py). That is weaker than driving
Chrome, and it is not nothing: the things that would be most expensive to discover on the
tablet — a credential in a file served to the browser, a voice that talks over the microphone,
a second microphone stream, markup built from a customer's email — are all visible here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parent.parent / "web"
APP_JS = (WEB / "app.js").read_text(encoding="utf-8")
UI_JS = (WEB / "ui.js").read_text(encoding="utf-8")
INDEX = (WEB / "index.html").read_text(encoding="utf-8")
JS_FILES = sorted(p.name for p in WEB.glob("*.js"))


def section(source: str, start: str, end: str | None = None) -> str:
    body = source[source.index(start):]
    return body[: body.index(end)] if end else body


def function_body(source: str, signature: str) -> str:
    """The text of one top-level function, up to its closing brace at column 0."""
    body = source[source.index(signature):]
    return body[: body.index("\n}")]


# --------------------------------------------------------------------------- the credential


@pytest.mark.parametrize("path", sorted(p.name for p in WEB.iterdir() if p.is_file()))
def test_no_credential_is_served_to_the_browser(path):
    """The key is read from the Keychain on the Mac and used in one header there. Anything
    that looks like a key, a key header, or a direct call to ElevenLabs is a leak."""
    source = (WEB / path).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in ("xi-api-key", "elevenlabs.io", "api.elevenlabs", "elevenlabs_api_key", "shpat_", "myshopify.com"):
        assert forbidden not in lowered, f"{path} names {forbidden}"
    # Key shapes: ElevenLabs keys are sk_ or xi_ followed by a long hex-ish run.
    assert not re.search(r"\b(?:sk|xi)_[A-Za-z0-9]{20,}", source), f"{path} contains a key"


def test_the_tablet_talks_only_to_its_own_backend():
    """Every fetch in the client is a same-origin path. A cross-origin one would be either a
    leak or a dependency the office cannot see."""
    for name in JS_FILES:
        source = (WEB / name).read_text(encoding="utf-8")
        for url in re.findall(r"fetch\(\s*[`'\"]([^`'\"]+)", source):
            assert url.startswith("/"), f"{name}: cross-origin fetch: {url}"
    for src in re.findall(r"<script[^>]+src=\"([^\"]+)\"", INDEX):
        assert src.startswith("/static/"), f"index.html loads {src}"
    for href in re.findall(r"href=\"([^\"]+)\"", INDEX):
        assert href.startswith("/static/"), f"index.html links {href}"


# --------------------------------------------------------------------------- the renderer


@pytest.mark.parametrize("name", JS_FILES)
def test_no_markup_is_built_from_strings(name):
    """External data reaches the page through textContent and safe DOM construction only."""
    source = (WEB / name).read_text(encoding="utf-8")
    for forbidden in (".innerHTML", ".outerHTML", "insertAdjacentHTML(", "document.write(", "eval(", "new Function(", "srcdoc"):
        assert forbidden not in source, f"{name} uses {forbidden}"


def test_the_renderer_owns_the_vocabulary_and_matches_the_backend():
    from app.presentation import UI_TYPES

    renderers = set(re.findall(r"^\s{4}(\w+): render\w+,$", UI_JS, re.M))
    assert renderers | {"context_stack"} == set(UI_TYPES)
    # Unknown types draw nothing; there is no generic "render whatever arrived" path.
    assert "if (!isValid(item) || !RENDERERS[item.type]) return null;" in UI_JS


def test_the_frontend_never_chooses_a_component_from_the_prose():
    """The cards come from data.ui, never from answer.includes('order')."""
    assert "CrooksUI.render(data.ui" in APP_JS
    assert not re.search(r"answer\s*\.\s*(includes|match|indexOf|search)\(", APP_JS)
    assert not re.search(r"question\s*\.\s*(includes|match|indexOf)\(", APP_JS)


def test_fixtures_are_behind_the_developer_gate():
    """index.html never loads fixtures.js; app.js injects it only when the gate is on, and
    everything it renders is marked as a fixture."""
    assert "fixtures.js" not in INDEX
    dev = section(APP_JS, "if (DEV) {")
    assert "script.src = '/static/fixtures.js'" in dev
    assert "'/static/fixtures.js'" not in APP_JS[: APP_JS.index("if (DEV) {")]
    assert "{ fixture: true }" in dev
    assert "crooks.dev" in APP_JS and "params.has('dev')" in APP_JS
    fixtures = (WEB / "fixtures.js").read_text(encoding="utf-8")
    assert "@example.com" in fixtures and not re.search(r"@(?!example\.com)[\w.-]+\.\w+", fixtures)


def test_no_write_action_is_wired():
    """Read-only: no card can send, fulfil, refund or cancel anything."""
    for name in JS_FILES:
        source = (WEB / name).read_text(encoding="utf-8")
        assert "/send" not in source and "/fulfil" not in source and "/refund" not in source and "/cancel" not in source, name
    for endpoint in re.findall(r"fetch\(\s*[`'\"]([^`'\"]+)", APP_JS):
        assert endpoint.split("?")[0].rstrip("/") in {"/speak", "/health", "/turn", "/audio-test", "/reset"} or endpoint.startswith("/state/"), endpoint


# --------------------------------------------------------------------------- the voice


def test_the_answer_is_spoken_through_the_backend():
    assert "'/speak'" in APP_JS
    assert "speakAnswer(data.answer" in APP_JS


def test_the_answer_text_is_not_made_to_wait_for_the_audio():
    """The text goes on screen, then the cards, then the voice is asked for."""
    body = APP_JS[APP_JS.index("const response = await fetch('/turn', options);"):]
    assert body.index("el.answer.textContent = data.answer") < body.index("renderTurn(data)") < body.index("speakAnswer(data.answer")
    # Not awaited: awaiting it would keep the hold region busy while the voice spoke.
    assert "await speakAnswer(" not in APP_JS


def test_the_browser_voice_is_only_the_fallback():
    """browserSpeak is reachable only from a failure path inside speakAnswer, never directly
    from the turn — otherwise Android would quietly become the normal voice again."""
    assert "browserSpeak(data.answer" not in APP_JS
    for call in re.findall(r"browserSpeak\((.*?)\)", APP_JS, re.S):
        assert "reason:" in call or "text," in call


def test_every_failure_of_the_voice_ends_in_the_fallback():
    speak_answer = section(APP_JS, "async function speakAnswer", "/* ------------------------------------------------------------------ health */")
    for failure in ("!response.ok", "!blob.size", "} catch (error) {", "player.onerror", "audio context suspended"):
        assert failure in speak_answer
    # Five of them: a bad status, an empty body, a dead backend, a player that will not play,
    # and a player bound to an AudioContext that Android will not run.
    assert speak_answer.count("browserSpeak(") >= 5


# --------------------------------------------------------------------------- interruption


def test_holding_the_orb_silences_the_voice_first():
    """The assistant must never be recorded answering itself, and the orb must go straight to
    LISTENING on the touch — no READY flash between SPEAKING and the next question."""
    handler = function_body(APP_JS, "function onHoldStart(event)")
    assert handler.index("unlockSpeech();") < handler.index("stopSpeaking();") < handler.index("setState('LISTENING')") < handler.index("startRecording();")
    # Both hold surfaces use the same handler: the transparent region and the orb itself.
    assert "for (const target of [el.talk, el.orbFrame])" in APP_JS
    assert "target.addEventListener('pointerdown', onHoldStart);" in APP_JS
    # And the recorder stops it again on its own path, for the microphone-test route in.
    assert "stopSpeaking();" in section(APP_JS, "async function startRecording")


def test_a_new_answer_cancels_the_one_before_it():
    speak_answer = section(APP_JS, "async function speakAnswer")
    assert speak_answer.index("stopSpeaking();") < speak_answer.index("await fetch('/speak'")
    # A generation counter, so a response that arrives after the interruption is dropped
    # rather than played over the next question.
    assert speak_answer.count("generation !== speakGeneration") >= 4


def test_stopping_actually_stops_both_engines_and_the_request():
    stop = function_body(APP_JS, "function stopSpeaking()")
    assert "player.pause()" in stop
    assert "speakAbort.abort()" in stop
    assert "speechSynthesis.cancel()" in stop
    assert "speakGeneration += 1" in stop


# --------------------------------------------------------------------------- the microphone


def test_the_microphone_is_opened_once_and_kept_warm():
    """getUserMedia is called in exactly one place, behind a shared promise, and the recorder
    is built from that stream. Stopping tracks after a recording is the first-word clip."""
    assert APP_JS.count("getUserMedia(") == 1
    ensure = function_body(APP_JS, "async function ensureMicStream()")
    assert "if (micIsLive()) return micStream;" in ensure
    assert "if (micOpening) return micOpening;" in ensure
    start = function_body(APP_JS, "async function startRecording()")
    assert "micIsLive() ? micStream : await ensureMicStream()" in start
    assert "new MediaRecorder(stream" in start
    assert "track.stop()" not in start
    # The only place tracks are stopped is the deliberate release, used when the page hides.
    assert APP_JS.count("track.stop()") == 1
    assert "track.stop()" in function_body(APP_JS, "function releaseMicStream()")
    # The microphone test reuses the warm stream rather than opening a second one.
    assert "const stream = await ensureMicStream();" in section(APP_JS, "el.micTest.addEventListener")


def test_the_analysers_hang_off_the_existing_streams():
    """One AudioContext; the mic analyser is attached to the warm stream and the player
    analyser is created once and reconnected to the destination."""
    viz = (WEB / "audio-viz.js").read_text(encoding="utf-8")
    assert viz.count("new AC()") == 1
    assert "createMediaElementSource(player)" in viz
    assert "if (!ctx || playerSource || ctx.state !== 'running') return" in viz
    assert "analyser.connect(ctx.destination)" in viz
    assert "createMediaStreamSource(stream)" in viz
    assert "getUserMedia" not in viz
    assert "audio.attachMic(stream)" in function_body(APP_JS, "async function ensureMicStream()")
    assert "audio.attachPlayer(player)" in APP_JS


# --------------------------------------------------------------------------- resources


def test_one_player_for_the_life_of_the_page():
    """A new Audio element per answer leaks a decoder per question and eventually plays
    nothing at all. The microphone test is the one exception and is a manual diagnostic."""
    assert "const player = new Audio();" in APP_JS
    assert APP_JS.count("new Audio(") == 2  # the shared player, and the mic-test playback


def test_object_urls_are_revoked():
    assert "function releaseAudioUrl()" in APP_JS
    assert "URL.revokeObjectURL(currentAudioUrl)" in APP_JS
    # Revoked when it ends, when it fails, when it is interrupted, and when the context stalls.
    assert APP_JS.count("releaseAudioUrl()") >= 6


def test_the_volume_is_normal():
    settings = re.findall(r"player\.volume\s*=\s*([^;]+);", APP_JS)
    assert settings and set(settings) == {"1.0"}


def test_nothing_runs_while_the_page_is_hidden():
    hidden = section(APP_JS, "document.addEventListener('visibilitychange'", "});")
    assert "orb.stop()" in hidden and "stopSpeaking()" in hidden and "releaseMicStream()" in hidden
    assert "if (document.hidden) return;" in function_body(APP_JS, "async function pollHealth(")
    orb = (WEB / "orb.js").read_text(encoding="utf-8")
    assert "cancelAnimationFrame" in orb
    assert "prefers-reduced-motion" in APP_JS and "reducedMotion" in orb


def test_the_voice_streams_and_every_streaming_failure_plays_whole():
    """MSE playback starts on the first chunk; anything that goes wrong mid-stream replays the
    bytes already received rather than asking ElevenLabs again or going silent."""
    assert "MediaSource.isTypeSupported('audio/mpeg')" in APP_JS
    stream = function_body(APP_JS, "async function playStream(")
    assert "received.push(value)" in stream
    assert "playAudio(new Blob(received, { type: 'audio/mpeg' })" in stream
    assert "generation !== speakGeneration" in stream
    assert "reader.cancel()" in stream
    # The whole-file path and the Android voice remain behind it, untouched.
    assert "function playAudio(blob, text, generation, isError)" in APP_JS


def test_the_turn_says_whether_the_voice_will_be_asked_for():
    assert "form.append('speak', el.speakToggle.checked ? '1' : '0');" in APP_JS
    assert "speak: el.speakToggle.checked" in APP_JS


def test_the_context_deck_is_bounded():
    assert "const MAX_HISTORY = 6;" in APP_JS
    assert "while (history.length > MAX_HISTORY) history.shift();" in APP_JS


# --------------------------------------------------------------------------- autoplay


def test_the_first_touch_unlocks_all_three_engines():
    """Android plays neither audio nor speechSynthesis until the page has been touched, and
    an AudioContext will not start anywhere else. The hold is that touch."""
    unlock = function_body(APP_JS, "function unlockSpeech()")
    assert "player.play()" in unlock
    assert "SpeechSynthesisUtterance" in unlock
    assert "audio.ensure()" in unlock
    assert "unlockSpeech();" in function_body(APP_JS, "function onHoldStart(event)")


# --------------------------------------------------------------------------- the settings sheet


def test_the_settings_sheet_says_which_voice_is_which():
    assert "Fallback voice" in INDEX
    assert "Speak answers aloud" in INDEX and "Show timings" in INDEX
    assert "Microphone test" in INDEX and "New conversation" in INDEX
    assert 'id="health-detail"' in INDEX
    # The real voice's name comes from the backend, never hard-coded here.
    assert "data.voice" in APP_JS and "voice.voice" in APP_JS


def test_the_shell_is_the_orb_not_a_dashboard():
    assert 'id="orb"' in INDEX and "<canvas" in INDEX
    assert 'id="talk"' in INDEX and "Hold to speak" in INDEX
    assert "System ready." in INDEX and "What do you need?" in INDEX
    assert "How can I help" not in INDEX
    assert INDEX.count("<nav") <= 1
