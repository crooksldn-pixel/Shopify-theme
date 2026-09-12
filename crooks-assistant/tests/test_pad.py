"""The CROOKS PAD heartbeat (§16) and the appliance telemetry (§18).

The test this file exists for is `test_a_reachable_backend_with_no_pad_reports_disconnected`.
Everything before the appliance layer answered "is the tablet connected?" by asking Tailscale
whether a route existed, and a route exists whether the tablet is in the owner's hand or in a
drawer with a flat battery. §26's warning is written about exactly this: "tablet connected vs
backend merely reachable". So the first thing proved here is that a completely healthy Mac —
/ping answering, /health answering, every route up — reports the pad DISCONNECTED until a pad
has actually said something, and reports it disconnected again once the pad stops.

The second thing proved here is that the liveness answer cannot be served out of the /health
cache. /health answers from a ninety-second-old result, and STALE_AFTER_S is ninety-five
seconds; a pad block frozen into that cache would go on saying "connected" for almost the whole
staleness window after the tablet died, which would make the word worthless precisely when it
is being relied upon. `test_the_pad_block_is_never_served_from_the_health_cache` moves the clock
underneath a warm cache and insists the answer changes.

The third is the flood. Appliance events are the ones that arrive in thousands — an access point
flapping, a WebView in a reload loop — and a timeline nobody can read is not observability.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.actions.ledger import NullLedger
from app.main import app
from app.observability import pad as pad_module
from app.observability import timeline as timeline_module
from app.observability.report import reconstruct, render
from app.observability.session import TestSessions
from app.observability.timeline import Timeline, read_events
from app.session.manager import SessionManager
from tests.test_actions_routes import PROXIED, FakeProvider, configure


class Clock:
    """A clock the test moves by hand. Liveness is arithmetic on two timestamps, so every
    assertion below about staleness is exact rather than a sleep and a hope."""

    def __init__(self, now: float = 1_800_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> float:
        self.now += seconds
        return self.now


@pytest.fixture(autouse=True)
def _fresh_pad():
    """A pad nobody has ever heard from, before and after each test. The registry is
    process-wide (like the timeline), so a heartbeat left behind by one test would make the
    next one's "no pad has checked in" a lie that happened to pass."""
    pad_module.reset()
    yield
    pad_module.reset()


@pytest.fixture()
def registry():
    clock = Clock()
    return pad_module.install(pad_module.PadRegistry(clock=clock)), clock


@pytest.fixture()
def recording(tmp_path):
    """A timeline writing to this test's own directory, with a session running, so that what
    reaches disk can be read back. Returns (timeline, path)."""
    sessions = TestSessions(tmp_path / "logs")
    timeline = timeline_module.install(Timeline(sessions))
    session = timeline.start("appliance")
    yield timeline, sessions.timeline_path(session)
    timeline.stop()
    timeline_module.install(timeline_module.NullTimeline())


@pytest.fixture()
async def client(monkeypatch, tmp_path):
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
        runtime.actions.ledger = NullLedger()
        runtime.sessions = SessionManager()
        runtime.tests = TestSessions(tmp_path / "logs")
        runtime.timeline = timeline_module.install(Timeline(runtime.tests))
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            c.runtime = runtime
            c.tmp = tmp_path
            yield c
        runtime.timeline.stop()
        timeline_module.install(timeline_module.NullTimeline())


# ------------------------------------------------------------------- is the pad there at all


async def test_a_reachable_backend_with_no_pad_reports_disconnected(client):
    """§26, the whole reason this file exists.

    Every route on this Mac answers. Nothing is broken anywhere. And the pad is DISCONNECTED,
    because no pad has said anything — which is the only evidence that would mean it is there.
    A Tailscale route, a 200 from /ping and a green /health are all facts about the Mac.
    """
    assert (await client.get("/ping")).json()["ok"] is True, "the backend is genuinely up"
    health = (await client.get("/health")).json()
    assert health["status"] in ("ok", "degraded"), "and genuinely answering"

    pad = health["pad"]
    assert pad["connected"] is False
    assert pad["state"] == "never_seen"
    assert pad["last_seen"] is None and pad["last_seen_s"] is None
    assert pad["heartbeats"] == 0
    assert pad["detail"] == "CROOKS PAD has never checked in with this Mac"
    # And the same answer from the route the Control app can ask directly, without paying for a
    # Shopify query and a Gmail profile to get it.
    assert (await client.get("/pad")).json()["connected"] is False


async def test_a_fresh_heartbeat_reports_connected_with_what_the_pad_said_it_is(client):
    configure(client, logins="owner@example.com")
    answer = await client.post("/pad/heartbeat", headers=PROXIED, json={
        "app_version": "0.4.2", "device_model": "SM-T290", "os_version": "Android 11 (API 30)",
        "boot_id": "b7f1", "at": 1_800_000_000.0,
    })
    assert answer.status_code == 200
    body = answer.json()
    # The appliance reads its own cadence off the backend rather than carrying a constant that
    # can drift away from the staleness window it is meant to satisfy.
    assert body["interval_s"] == pad_module.HEARTBEAT_INTERVAL_S
    assert body["stale_after_s"] == pad_module.STALE_AFTER_S
    assert body["recording"] is False, "no test session is running, so the pad keeps its telemetry off"
    # `showing_crooks` is None because this beat did not say what was on the screen, and an
    # unanswered question is not a yes.
    assert body["pad"] == {"state": "connected", "connected": True, "showing_crooks": None}

    pad = (await client.get("/health")).json()["pad"]
    assert pad["connected"] is True and pad["state"] == "connected"
    assert pad["app_version"] == "0.4.2" and pad["device_model"] == "SM-T290" and pad["os_version"] == "Android 11 (API 30)"
    assert pad["heartbeats"] == 1 and pad["last_seen_s"] is not None and pad["last_seen_s"] < 5
    assert pad["detail"] == "CROOKS PAD connected, last seen now, app 0.4.2, device SM-T290"


def test_a_stale_heartbeat_reports_disconnected(registry):
    """One missed beat is a radio waking up; three is a pad that is not answering. The window is
    written down here so that a change to it has to be a change to this line."""
    reg, clock = registry
    reg.heartbeat(app_version="0.4.2", device_model="SM-T290", os_version="Android 11")
    assert reg.status()["connected"] is True

    clock.advance(pad_module.HEARTBEAT_INTERVAL_S * 2 + 1)
    assert reg.status()["connected"] is True, "two missed beats is not a disconnection"

    clock.advance(pad_module.STALE_AFTER_S)
    status = reg.status()
    assert status["connected"] is False and status["state"] == "stale"
    assert status["detail"].startswith("CROOKS PAD DISCONNECTED, last seen ")
    assert "app 0.4.2, device SM-T290" in status["detail"], "who it was is still worth saying"
    # It comes back the moment it checks in again, and not before.
    reg.heartbeat(app_version="0.4.2")
    assert reg.status()["connected"] is True


async def test_the_pad_block_is_never_served_from_the_health_cache(client):
    """/health answers from a result up to CACHE_TTL_S old. If the pad block were cached with
    it, a pad that died one second after a poll would be reported connected for the next ninety
    — longer than the staleness window itself, so `connected` would have meant nothing at the
    only moment anybody wanted it."""
    from app.routes.health import CACHE_TTL_S

    assert CACHE_TTL_S >= pad_module.STALE_AFTER_S - 30, (
        "the cache is long enough relative to the staleness window that a cached pad block "
        "would be actively misleading; that is why _pad() is computed at answer time"
    )
    clock = Clock()
    pad_module.install(pad_module.PadRegistry(clock=clock))
    configure(client, logins="owner@example.com")
    await client.post("/pad/heartbeat", headers=PROXIED, json={"app_version": "0.4.2", "device_model": "SM-T290"})

    first = (await client.get("/health")).json()
    assert first["cached"] is False and first["pad"]["connected"] is True

    # The pad dies. Nothing else about the Mac changes, and the health cache is still warm.
    clock.advance(pad_module.STALE_AFTER_S + 60)
    second = (await client.get("/health")).json()
    assert second["cached"] is True, "the expensive checks really are being answered from the cache"
    assert second["pad"]["connected"] is False and second["pad"]["state"] == "stale"


async def test_reading_the_pad_directly_is_the_macs_own_business(client):
    """The tablet has no use for this and the route is not its business: the Control app runs on
    the Mac, like every other control route in `app/routes/observe.py`."""
    assert (await client.get("/pad", headers=PROXIED)).status_code == 403
    assert (await client.get("/pad")).status_code == 200


# ------------------------------------------------------------------------ what a pad may say


async def test_a_heartbeat_that_is_not_a_heartbeat_is_refused(client):
    configure(client, logins="owner@example.com")
    assert (await client.post("/pad/heartbeat", headers=PROXIED, content=b"{not json",)).status_code == 400
    assert (await client.post("/pad/heartbeat", headers=PROXIED, json=["nope"])).status_code == 400
    assert (await client.post("/pad/heartbeat", headers=PROXIED, content=b"x" * 20_000)).status_code == 400
    assert pad_module.current().heartbeats == 0, "none of those counted as the pad being alive"
    # An empty object IS a heartbeat: a pad that cannot name itself is still a pad checking in,
    # and the Control app should say connected-but-unidentified rather than disconnected.
    assert (await client.post("/pad/heartbeat", headers=PROXIED, json={})).status_code == 200
    status = pad_module.current().status()
    assert status["connected"] is True and status["detail"].endswith("app ?, device ?")


def test_an_identity_cannot_smuggle_a_secret_or_an_address_onto_health(registry):
    """/health is read by the Control app, pasted into reports and handed to engineers, exactly
    as a timeline is. So an identity string is filtered to a safe character set and then passed
    through the timeline's OWN scrub — the seam from Phase 5 — rather than through a second
    redactor written here."""
    reg, _clock = registry
    reg.heartbeat(
        app_version="shpat_0123456789abcdef",
        device_model="SM-T290 <script>alert(1)</script> george@crooks.example",
        os_version="A" * 500,
    )
    status = reg.status()
    assert status["app_version"] == "[secret]", "a credential shape is replaced by the timeline's scrub"
    assert "@" not in status["device_model"] and "george@crooks.example" not in status["device_model"]
    assert "<" not in status["device_model"] and ">" not in status["device_model"]
    assert status["device_model"].startswith("SM-T290 scriptalert(1)")
    assert len(status["os_version"]) == pad_module.MAX_IDENTITY_CHARS

    # There is no field for a device NAME, and inventing one does not create it: "George's Tab"
    # is the owner, not the appliance.
    reg.heartbeat(device_name="George's Tab")
    assert not hasattr(reg, "device_name") and "George" not in str(reg.status())


async def test_an_app_that_is_alive_around_a_dead_webview_does_not_read_as_fine(client):
    """§26: "app launched vs CROOKS loaded". The heartbeat comes from the NATIVE shell, and the
    native shell is perfectly capable of being alive around a WebView that never loaded, showed
    Chrome's error page, or was killed for memory. A row that said "CROOKS PAD connected" while
    the owner was looking at a white rectangle would be the fake green this layer exists to
    prevent, so the two facts are reported separately and the sentence says both."""
    configure(client, logins="owner@example.com")
    await client.post("/pad/heartbeat", headers=PROXIED, json={
        "app_version": "0.4.2", "device_model": "SM-T290", "webview": "error",
    })
    pad = (await client.get("/health")).json()["pad"]
    # Alive: the process is running and talking to us. That part is true and is still reported.
    assert pad["connected"] is True and pad["state"] == "connected"
    # And not fine.
    assert pad["showing_crooks"] is False and pad["webview"] == "error"
    assert pad["detail"] == "CROOKS PAD connected but NOT SHOWING CROOKS (webview error), last seen now, app 0.4.2, device SM-T290"

    # It clears only when the pad says it has: nothing here guesses.
    await client.post("/pad/heartbeat", headers=PROXIED, json={"app_version": "0.4.2", "webview": "loaded"})
    pad = (await client.get("/health")).json()["pad"]
    assert pad["showing_crooks"] is True
    assert pad["detail"] == "CROOKS PAD connected, last seen now, app 0.4.2, device SM-T290"


def test_a_pad_that_has_not_said_what_is_on_its_screen_is_not_assumed_to_be_fine(registry):
    """`None`, not `True`. A backend that assumed "loaded" because a heartbeat arrived would be
    inventing the one fact it cannot observe, and inventing it in the optimistic direction."""
    reg, _clock = registry
    reg.heartbeat(app_version="0.4.2", device_model="SM-T290")
    status = reg.status()
    assert status["showing_crooks"] is None and status["webview"] == ""
    assert "NOT SHOWING" not in status["detail"], "nor is it assumed broken; it simply has not said"
    # A value outside the vocabulary is not a value.
    reg.heartbeat(webview="probably fine honestly")
    assert reg.status()["showing_crooks"] is None


def test_the_webview_state_arrives_by_either_door(registry, recording):
    """An appliance that emits `pad_webview_error` need not also carry `webview` on every beat.
    One field, set by whichever said so last."""
    _timeline, _path = recording
    reg, clock = registry
    reg.heartbeat(app_version="0.4.2", webview="loaded")
    assert reg.status()["showing_crooks"] is True
    reg.record([{"kind": "pad_renderer_crash", "reason": "oom"}])
    assert reg.status()["showing_crooks"] is False and reg.status()["webview"] == "crashed"
    reg.record([{"kind": "pad_webview_loaded", "url": "https://crooks.example/"}])
    assert reg.status()["showing_crooks"] is True

    # And it stops being an assertion the moment the pad stops talking. What it last said about
    # its screen goes stale exactly as everything else it said does, and a row reading
    # "disconnected, showing CROOKS: yes" would be the fake green with two coats of paint.
    clock.advance(pad_module.STALE_AFTER_S + 1)
    stale = reg.status()
    assert stale["connected"] is False and stale["showing_crooks"] is None
    assert stale["webview"] == "loaded", "the last thing it said is still worth having, labelled as old"


def test_the_pads_own_clock_is_recorded_as_a_skew_and_never_as_liveness(registry):
    """A clock is a number the pad chose. What proves the pad alive is that the call happened."""
    reg, clock = registry
    reg.heartbeat(app_version="0.4.2", at=clock.now + 3600)
    assert reg.last_seen == clock.now, "the server's clock, not the pad's"
    assert reg.status()["clock_skew_s"] == 3600.0, "and the pad's wrong clock is reported, because it is a fault"
    assert reg.status()["connected"] is True


# ------------------------------------------------------------------- appliance telemetry (§18)


def test_only_a_transition_writes_a_heartbeat_event(registry, recording):
    """A beat every thirty seconds for eight hours is 960 events and nothing worth reading. What
    is worth reading is the pad appearing, coming back after an outage, and changing what it
    says it is."""
    timeline, path = recording
    reg, clock = registry

    reg.heartbeat(app_version="0.4.2", device_model="SM-T290")          # first_seen
    for _ in range(10):
        clock.advance(pad_module.HEARTBEAT_INTERVAL_S)
        reg.heartbeat(app_version="0.4.2", device_model="SM-T290")      # nothing: same pad, still here
    clock.advance(600)
    reg.heartbeat(app_version="0.4.2", device_model="SM-T290")          # returned, after ten minutes gone
    reg.heartbeat(app_version="0.5.0", device_model="SM-T290")          # identity_changed

    timeline.flush()
    beats = [e for e in read_events(path) if e["kind"] == "pad_heartbeat"]
    assert [e["state"] for e in beats] == ["first_seen", "returned", "identity_changed"]
    assert beats[1]["gap_s"] == 600.0, "the outage is written down with its length"
    assert beats[2]["changed"] == "app_version"
    assert all(e["source"] == "pad" for e in beats)


def test_a_flood_of_identical_events_is_collapsed_and_counted(registry, recording):
    """An access point flapping emits pad_network_changed a hundred times a minute. One of them
    is information; the other ninety-nine are what makes a timeline unreadable."""
    timeline, path = recording
    reg, _clock = registry

    flood = [{"kind": "pad_network_changed", "to": "wifi"} for _ in range(200)]
    taken = {"accepted": 0, "collapsed": 0, "rejected": 0, "rate_limited": 0}
    for start in range(0, len(flood), pad_module.MAX_EVENTS_PER_POST):
        for key, value in reg.record(flood[start:start + pad_module.MAX_EVENTS_PER_POST]).items():
            taken[key] += value
    assert taken == {"accepted": 1, "collapsed": 199, "rejected": 0, "rate_limited": 0}
    # And folding is NOT rate limiting: a flood of repeats must not eat the per-minute ceiling,
    # or a genuine event arriving after one would be dropped for the flood's sake.
    assert reg.events_rate_limited == 0

    reg.record([{"kind": "pad_network_changed", "to": "cell"}])
    timeline.flush()
    written = [e for e in read_events(path) if e["kind"] == "pad_network_changed"]
    assert len(written) == 2, "two states, two events, whatever arrived in between"
    assert written[0]["to"] == "wifi" and "repeats" not in written[0]
    assert written[1]["to"] == "cell" and written[1]["repeats"] == 199, (
        "nothing is silently lost: the event that replaces a state says how many identical "
        "reports of that state were folded away"
    )
    assert reg.status()["events"] == {"accepted": 2, "collapsed": 199, "rejected": 0, "rate_limited": 0}


def test_a_crash_loop_with_a_new_signature_every_time_hits_the_ceiling(registry, recording):
    """Folding catches repeats. It cannot catch a loop whose signature genuinely changes each
    time — a renderer dying with a new reason, an app flipping foreground/background — and a flat
    ceiling is the only thing that can."""
    timeline, path = recording
    reg, _clock = registry

    flipping = []
    for i in range(80):
        flipping.append({"kind": "pad_app_foreground" if i % 2 == 0 else "pad_app_background"})
    taken = {"accepted": 0, "collapsed": 0, "rejected": 0, "rate_limited": 0}
    for start in range(0, len(flipping), pad_module.MAX_EVENTS_PER_POST):
        for key, value in reg.record(flipping[start:start + pad_module.MAX_EVENTS_PER_POST]).items():
            taken[key] += value
    assert taken["accepted"] == pad_module.MAX_EVENTS_PER_MINUTE
    # The twenty past the ceiling split evenly between refused and folded, and that is not an
    # accident worth papering over: a rate-limited event does NOT become the channel's new
    # state, because nothing was written down for it. So the flood past the ceiling keeps being
    # measured against the last thing actually on the timeline, and every second one of an
    # alternating pair matches it and folds. The alternative — letting a refused event set the
    # state — would mean the timeline's last word on the lifecycle channel disagreed with what
    # the collapser thought the channel was saying.
    assert taken["rate_limited"] + taken["collapsed"] == 80 - pad_module.MAX_EVENTS_PER_MINUTE
    assert taken["rate_limited"] == 10 and taken["collapsed"] == 10

    timeline.flush()
    written = [e for e in read_events(path) if e["kind"].startswith("pad_app_")]
    assert len(written) == pad_module.MAX_EVENTS_PER_MINUTE
    # Silence would be the wrong answer: the count is on /health, so a pad drowning the timeline
    # says so rather than quietly filling it.
    assert reg.status()["events"]["rate_limited"] == 10


def test_a_batch_larger_than_the_ceiling_says_what_it_refused(registry, recording):
    """Slicing the list and returning a number that did not add up would be the quiet kind of
    dropping: the appliance would believe it had reported something it had not."""
    _timeline, _path = recording
    reg, _clock = registry
    sent = [{"kind": "pad_network_changed", "to": f"ap-{i}"} for i in range(70)]
    taken = reg.record(sent)
    assert sum(taken.values()) == len(sent), "every event sent is accounted for in the answer"
    assert taken["accepted"] == pad_module.MAX_EVENTS_PER_POST
    assert taken["rate_limited"] == len(sent) - pad_module.MAX_EVENTS_PER_POST


def test_a_kind_this_backend_does_not_know_is_refused_at_the_door(registry, recording):
    """Unknown fails closed. Forwarding it would put a kind the analyser cannot read onto the
    timeline, which is the very thing section 17 exists to stop happening again."""
    timeline, path = recording
    reg, _clock = registry
    taken = reg.record([
        {"kind": "pad_something_new"}, {"kind": "tablet_render"}, {"kind": ""},
        "not a dict", {"kind": "pad_app_started", "boot_id": "b1"},
    ])
    assert taken == {"accepted": 1, "collapsed": 0, "rejected": 4, "rate_limited": 0}
    timeline.flush()
    kinds = [e["kind"] for e in read_events(path) if e.get("source") == "pad"]
    assert kinds == ["pad_app_started"]
    assert reg.status()["events"]["rejected"] == 4


def test_a_pad_event_obeys_the_existing_pii_scrubbing(registry, recording):
    """Not a second redactor — the same one. Everything a pad reports goes through
    `timeline.emit`, so the shapes Phase 5 learned to redact (D-15: three real customer email
    addresses in a shipped timeline) are redacted here without this file knowing what they are.
    """
    timeline, path = recording
    reg, _clock = registry
    reg.record([{
        "kind": "pad_webview_error", "code": "ERR_FAILED",
        "message": "load failed for george@crooks.example, token shpat_0123456789abcdef, ring 07700 900123",
        "url": "https://crooks.example/?x=1",
        "authorization": "Bearer abcdefghijklmnop", "device_name": "George's Tab",
    }])
    timeline.flush()
    written = [e for e in read_events(path) if e["kind"] == "pad_webview_error"][0]
    assert "george@crooks.example" not in written["message"] and "[email]" in written["message"]
    assert "shpat_0123456789abcdef" not in written["message"] and "[secret]" in written["message"]
    assert "07700 900123" not in written["message"]
    # Fields that are not in the appliance's vocabulary never become fields at all, so there is
    # nothing for the scrub to have to catch.
    assert "authorization" not in written and "device_name" not in written
    assert written["code"] == "ERR_FAILED" and written["url"].startswith("https://crooks.example")


async def test_the_route_takes_events_alongside_a_beat_and_says_what_it_did(client):
    """One call from the appliance rather than two. The pad learns whether a session is running
    from the same answer, so it can turn its own telemetry on within one beat."""
    configure(client, logins="owner@example.com")
    await client.post("/test-session/start", json={"name": "appliance"})
    answer = await client.post("/pad/heartbeat", headers=PROXIED, json={
        "app_version": "0.4.2", "device_model": "SM-T290", "os_version": "Android 11",
        "events": [
            {"kind": "pad_app_started", "boot_id": "b1"},
            {"kind": "pad_webview_loaded", "url": "https://crooks.example/", "ms": 812},
            {"kind": "pad_webview_loaded", "url": "https://crooks.example/", "ms": 900},
            {"kind": "pad_nonsense"},
        ],
    })
    assert answer.status_code == 200
    body = answer.json()
    assert body["recording"] is True, "the pad is told to start reporting, without a second request"
    assert body["events"] == {"accepted": 2, "collapsed": 1, "rejected": 1, "rate_limited": 0}

    stopped = (await client.post("/test-session/stop")).json()
    client.runtime.timeline.flush()
    events = read_events(Path(stopped["path"]))
    pad_events = [e for e in events if e.get("source") == "pad"]
    assert [e["kind"] for e in pad_events] == ["pad_heartbeat", "pad_app_started", "pad_webview_loaded"]
    assert pad_events[0]["state"] == "first_seen" and pad_events[0]["device_model"] == "SM-T290"
    assert pad_events[2]["ms"] == 812, "the first load is the one written; the identical second is folded"


async def test_a_heartbeat_is_taken_when_nothing_is_being_recorded(client):
    """Liveness is not telemetry. The Control app has to be able to say whether the tablet is
    alive at three in the morning with no session running — that is the whole point of it — so a
    heartbeat is taken whatever the timeline is or is not doing."""
    configure(client, logins="owner@example.com")
    assert client.runtime.timeline.active is None
    answer = await client.post("/pad/heartbeat", headers=PROXIED, json={"app_version": "0.4.2", "device_model": "SM-T290"})
    assert answer.status_code == 200 and answer.json()["recording"] is False
    assert (await client.get("/pad")).json()["connected"] is True


# ------------------------------------------------------------------------------ the analyser


def _timeline_with_appliance_events() -> list[dict]:
    """One small session with a turn in it and the appliance talking around the turn."""
    base = 1_800_000_000.0
    return [
        {"ts": base, "seq": 1, "kind": "session_started", "source": "mac", "name": "appliance hour"},
        {"ts": base + 1, "seq": 2, "kind": "pad_heartbeat", "source": "pad", "state": "first_seen",
         "app_version": "0.4.2", "device_model": "SM-T290", "os_version": "Android 11 (API 30)"},
        {"ts": base + 2, "seq": 3, "kind": "pad_app_started", "source": "pad", "boot_id": "b1"},
        {"ts": base + 3, "seq": 4, "kind": "pad_webview_loaded", "source": "pad", "ms": 812},
        {"ts": base + 4, "seq": 5, "kind": "turn_started", "source": "mac", "turn_id": "t1", "session_id": "s1", "input": "voice"},
        {"ts": base + 5, "seq": 6, "kind": "turn_finished", "source": "mac", "turn_id": "t1", "session_id": "s1",
         "question": "how many orders today", "answer": "Eleven.", "ms": 1200, "ui": []},
        {"ts": base + 9, "seq": 7, "kind": "pad_backend_unreachable", "source": "pad", "code": "timeout"},
        {"ts": base + 40, "seq": 8, "kind": "pad_backend_reachable", "source": "pad", "repeats": 12},
        {"ts": base + 60, "seq": 9, "kind": "pad_renderer_crash", "source": "pad", "reason": "oom"},
        {"ts": base + 90, "seq": 10, "kind": "pad_heartbeat", "source": "pad", "state": "returned", "gap_s": 81.0,
         "app_version": "0.4.2", "device_model": "SM-T290", "os_version": "Android 11 (API 30)"},
        {"ts": base + 99, "seq": 11, "kind": "session_stopped", "source": "mac", "duration_s": 99.0},
    ]


def test_the_analyser_reads_a_timeline_with_pad_events_in_it():
    """The §18 requirement, and the one that could have broken something: these kinds did not
    exist when the analyser was written. Before this pass they would have fallen through to
    `unknown_kinds` and into `orphans`, and section 1 of every appliance report would have said
    "event kinds this report does not read" about our own tablet — which is precisely the
    September failure test_e in tests/test_analyser.py was written about."""
    rec = reconstruct(_timeline_with_appliance_events())

    assert not rec.unknown_kinds, dict(rec.unknown_kinds)
    assert len(rec.appliance) == 7
    assert not [e for e in rec.orphans if str(e.get("kind", "")).startswith("pad_")], (
        "an appliance event belongs to no turn by construction, and is filed as such rather "
        "than reported as an event outside a turn"
    )
    # The ordinary reconstruction is untouched by their presence.
    assert len(rec.turns) == 1 and rec.turns[0].turn_id == "t1"
    assert rec.turns[0].answer == "Eleven."

    markdown = render(rec, tools_registered=[])
    assert "## 17. The appliance" in markdown
    assert "**SM-T290**" in markdown and "app **0.4.2**" in markdown
    assert "The pad went quiet and came back 1 time(s)" in markdown
    assert "could not reach this Mac **1** time(s)" in markdown
    assert "The renderer died 1 time(s)" in markdown
    assert "12 identical repeat(s) were folded away" in markdown
    assert "7 appliance event(s)" in markdown


def test_a_pad_kind_from_a_newer_backend_is_read_rather_than_choked_on():
    """A timeline can be written by one build and read by another — `make test-session-report`
    is routinely run against a file from last week. A `pad_` kind this build has never heard of
    must be counted, not treated as unreadable."""
    events = _timeline_with_appliance_events()
    events.append({"ts": 1_800_000_098.0, "seq": 12, "kind": "pad_thermal_throttled", "source": "pad", "state": "hot"})
    rec = reconstruct(events)
    assert not rec.unknown_kinds, "a pad_ kind is the appliance's, whether or not this build knows it"
    markdown = render(rec, tools_registered=[])
    assert "pad_thermal_throttled" in markdown
    assert "does not read line by line" in markdown


def test_a_session_with_no_appliance_events_is_reported_exactly_as_before():
    """Section 17 is conditional. Every session recorded from a browser, and every session
    recorded before the appliance existed, must come out byte for byte as it did — a section
    saying "none" at the bottom of each of those is noise in every report ever written."""
    events = [e for e in _timeline_with_appliance_events() if not str(e.get("kind", "")).startswith("pad_")]
    markdown = render(reconstruct(events), tools_registered=[])
    assert "## 17." not in markdown and "appliance event(s)" not in markdown
    assert "## 16. Two outcomes per turn" in markdown
