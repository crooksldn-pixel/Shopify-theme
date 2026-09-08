"""What the tablet is allowed to know, and what it must do with the voice.

The client is JavaScript and there is no browser in this suite, so these are read as source.
That is weaker than driving Chrome, and it is not nothing: the two things that would be most
expensive to discover on the tablet — a credential in a file served to the browser, and a voice
that talks over the microphone — are both visible here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parent.parent / "web"
APP_JS = (WEB / "app.js").read_text(encoding="utf-8")
INDEX = (WEB / "index.html").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- the credential


@pytest.mark.parametrize("path", sorted(p.name for p in WEB.iterdir() if p.is_file()))
def test_no_credential_is_served_to_the_browser(path):
    """The key is read from the Keychain on the Mac and used in one header there. Anything
    that looks like a key, a key header, or a direct call to ElevenLabs is a leak."""
    source = (WEB / path).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in ("xi-api-key", "elevenlabs.io", "api.elevenlabs", "elevenlabs_api_key"):
        assert forbidden not in lowered, f"{path} names {forbidden}"
    # Key shapes: ElevenLabs keys are sk_ or xi_ followed by a long hex-ish run.
    assert not re.search(r"\b(?:sk|xi)_[A-Za-z0-9]{20,}", source), f"{path} contains a key"


def test_the_tablet_talks_only_to_its_own_backend():
    """Every fetch in the client is a same-origin path. A cross-origin one would be either a
    leak or a dependency the office cannot see."""
    for url in re.findall(r"fetch\(\s*[`'\"]([^`'\"]+)", APP_JS):
        assert url.startswith("/"), f"cross-origin fetch: {url}"


# --------------------------------------------------------------------------- the voice


def test_the_answer_is_spoken_through_the_backend():
    assert "'/speak'" in APP_JS
    assert "speakAnswer(data.answer" in APP_JS


def test_the_answer_text_is_not_made_to_wait_for_the_audio():
    """The text goes on screen, then the voice is asked for — never the other way round."""
    body = APP_JS[APP_JS.index("const data = await response.json();"):]
    assert body.index("el.answer.textContent = data.answer") < body.index("speakAnswer(data.answer")
    # Not awaited: awaiting it would keep the talk button disabled while Derek spoke.
    assert "await speakAnswer(" not in APP_JS


def test_the_browser_voice_is_only_the_fallback():
    """browserSpeak is reachable only from a failure path inside speakAnswer, never directly
    from the turn — otherwise Android would quietly become the normal voice again."""
    assert "browserSpeak(data.answer" not in APP_JS
    for call in re.findall(r"browserSpeak\((.*?)\)", APP_JS, re.S):
        assert "reason:" in call or "text," in call


def test_every_failure_of_the_voice_ends_in_the_fallback():
    speak_answer = APP_JS[APP_JS.index("async function speakAnswer"):APP_JS.index("/* ------------------------------------------------------------------ health */")]
    for failure in ("!response.ok", "!blob.size", "} catch (error) {", "player.onerror"):
        assert failure in speak_answer
    # Four of them: a bad status, an empty body, a dead backend, a player that will not play.
    assert speak_answer.count("browserSpeak(") >= 4


# --------------------------------------------------------------------------- interruption


def test_holding_the_microphone_silences_the_voice_first():
    """The assistant must never be recorded answering itself."""
    handler = APP_JS[APP_JS.index("el.talk.addEventListener('pointerdown'"):]
    handler = handler[: handler.index("});")]
    assert handler.index("stopSpeaking()") < handler.index("startRecording()")
    # And the recorder stops it again on its own path, for the microphone-test route in.
    assert "stopSpeaking();" in APP_JS[APP_JS.index("async function startRecording"):]


def test_a_new_answer_cancels_the_one_before_it():
    speak_answer = APP_JS[APP_JS.index("async function speakAnswer"):]
    assert speak_answer.index("stopSpeaking();") < speak_answer.index("await fetch('/speak'")
    # A generation counter, so a response that arrives after the interruption is dropped
    # rather than played over the next question.
    assert speak_answer.count("generation !== speakGeneration") >= 4


def test_stopping_actually_stops_both_engines_and_the_request():
    stop = APP_JS[APP_JS.index("function stopSpeaking()"):]
    stop = stop[: stop.index("\n}")]
    assert "player.pause()" in stop
    assert "speakAbort.abort()" in stop
    assert "speechSynthesis.cancel()" in stop
    assert "speakGeneration += 1" in stop


# --------------------------------------------------------------------------- resources


def test_one_player_for_the_life_of_the_page():
    """A new Audio element per answer leaks a decoder per question and eventually plays
    nothing at all. The microphone test is the one exception and is a manual diagnostic."""
    assert "const player = new Audio();" in APP_JS
    assert APP_JS.count("new Audio(") == 2  # the shared player, and the mic-test playback


def test_object_urls_are_revoked():
    assert "function releaseAudioUrl()" in APP_JS
    assert "URL.revokeObjectURL(currentAudioUrl)" in APP_JS
    # Revoked when it ends, when it fails, and when it is interrupted.
    assert APP_JS.count("releaseAudioUrl()") >= 5


def test_the_volume_is_normal():
    settings = re.findall(r"player\.volume\s*=\s*([^;]+);", APP_JS)
    assert settings and set(settings) == {"1.0"}


# --------------------------------------------------------------------------- autoplay


def test_the_first_touch_unlocks_both_engines():
    """Android plays neither audio nor speechSynthesis until the page has been touched. The
    talk button is that touch, and it is the only gesture this interface has."""
    unlock = APP_JS[APP_JS.index("function unlockSpeech()"):]
    unlock = unlock[: unlock.index("\n}")]
    assert "player.play()" in unlock
    assert "SpeechSynthesisUtterance" in unlock
    handler = APP_JS[APP_JS.index("el.talk.addEventListener('pointerdown'"):]
    assert "unlockSpeech();" in handler[: handler.index("});")]


# --------------------------------------------------------------------------- the settings page


def test_the_settings_page_says_which_voice_is_which():
    assert "Derek" in INDEX
    assert "Fallback voice" in INDEX
