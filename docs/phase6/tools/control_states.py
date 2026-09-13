#!/usr/bin/env python3
"""The twelve CROOKS Control states, built from the REAL documents.

§14 asks for twelve visual states and says, in the same breath, not to make twelve disconnected
fake mockups. So none of these is hand-written JSON. Each one bends exactly one thing about a
working Mac — the backend stops answering, an essential goes down, the tablet's WebView crashes,
an update is waiting — and then asks `scripts/control.py` for the document it really produces.
What the harness renders is therefore the bytes CROOKS Control would actually be handed.

The four that a status document cannot express on its own — a test running, an update in flight,
an update that failed — carry an `app` block beside the document, which is the state the Swift
`LifecycleMachine` and `UpdatePanel` hold in memory between presses. That is the honest split:
the document is the Mac, the app block is what this app knows that the Mac does not.

    python3 docs/phase6/tools/control_states.py > docs/phase6/tools/control_states.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3] / "crooks-assistant"
sys.path.insert(0, str(ROOT))

from scripts import control  # noqa: E402


def check(ok: bool, detail: str = "") -> dict:
    return {"ok": ok, "detail": detail}


def health(**over) -> dict:
    """A /health as the running backend answers it, everything well."""
    doc = {
        "status": "ok", "version": "0.6.2", "build": "b-2026-09-12-a3f91c", "uptime_s": 27_360.0,
        "sessions": 1,
        "checks": {
            "speech": check(True, "scribe_v2 (primary)"), "tts": check(True, "Derek"),
            "claude": check(True, "sonnet, CLI"), "shopify": check(True, "5wn03t-nm.myshopify.com"),
            "gmail": check(True, "george@crooksldn.com"), "whisper": check(True, "small.en"),
            "knowledge_base": check(True, "7 file(s)"), "terminology": check(True, "120 term(s)"),
            "writes": check(True, "ready"),
        },
        "speech": {"primary": "scribe", "effective": "scribe_v2"},
        "writes": {"state": "ready", "detail": "ready"},
        "manifest": {"reads": 40, "writes": 12, "batches": 3, "fingerprint": "deadbeefcafe"},
        "observability": {"test_session": None, "name": None},
    }
    doc.update(over)
    return doc


def pad(alive=True, age=3.0, webview="loaded", showing=True, battery=87) -> dict:
    return {"connected": alive, "state": "connected" if alive else "stale",
            "last_seen_s": age, "app_version": "CROOKS Pad 0.6.2", "device_model": "SM-T290",
            "webview": webview, "showing_crooks": showing, "battery_percent": battery,
            "stale_after_s": 95}


def document(health_doc, host="crooks-mini.tail1234.ts.net"):
    """Ask control.py for the real thing, with one fact about the Mac bent."""
    note = "" if host else "Tailscale is not serving port 8000"
    with mock.patch.object(control, "port", lambda: 8000), \
         mock.patch.object(control, "read_health", lambda p, fresh=False: health_doc), \
         mock.patch.object(control, "tablet_route", lambda p: (host, note)):
        return control.status_document()


def state(key, title, why, health_doc, *, host="crooks-mini.tail1234.ts.net", app=None):
    return {"key": key, "title": title, "why": why,
            "status": document(health_doc, host=host), "app": app or {}}


DOWN = "the access token was refused (401)"

STATES = [
    state("ready", "Ready / live",
          "Everything the appliance needs is working and the tablet is showing CROOKS. The state "
          "the owner sees most, so it is the one that must be quietest.",
          health(pad=pad())),

    state("development", "Development-ready",
          "A fixture backend, which is CORRECT for a development Mac. §10: expected absence is "
          "not a failure, so this reads READY with the environment named rather than DEGRADED.",
          health(pad=pad(), environment="development",
                 checks={**health()["checks"],
                         "shopify": check(True, "fixture backend"),
                         "gmail": check(True, "fixture backend")})),

    state("stopped", "Backend stopped",
          "Nothing is answering on the loopback port. One thing to do, and it is the only "
          "control on the screen.",
          None, host=""),

    state("degraded", "Actual failure",
          "CROOKS OS is up and cannot do its job: an essential is genuinely down. This is what "
          "the fixture case must NOT look like.",
          health(pad=pad(), checks={**health()["checks"], "shopify": check(False, DOWN)})),

    state("pad-away", "Pad disconnected",
          "The Mac is well. The tablet has not checked in since this morning — a fact about the "
          "tablet, not about CROOKS OS, so the big word stays READY.",
          health(pad=pad(alive=False, age=20_400.0, webview="", showing=None, battery=None))),

    state("pad-blank", "Pad connected, not showing",
          "The one the old build could not say. The tablet is on and checking in; its WebView "
          "has crashed, so the owner is looking at a white rectangle. CONNECTED would be a lie.",
          health(pad=pad(webview="crashed", showing=False))),

    state("test-ready", "Physical test ready",
          "Healthy, tablet showing, nothing running. The primary action is the test.",
          health(pad=pad())),

    state("test-active", "Physical test active",
          "A session is running. While it is, it is the only thing on the screen worth reading.",
          health(pad=pad(), observability={"test_session": "s-4471", "name": "Saturday counter"}),
          app={"test": {"active": True, "id": "s-4471", "name": "Saturday counter",
                        "elapsed_s": 522, "interactions": 31}}),

    state("test-done", "Physical test complete",
          "It has just stopped. What was learned is the point, not the fact that it finished.",
          health(pad=pad()),
          app={"report": {"id": "s-4471", "name": "Saturday counter", "duration_s": 1_284,
                          "interactions": 47, "issues": 3}}),

    state("update-available", "Update available",
          "A newer CROOKS OS exists. Nothing is wrong, so this is an offer and not an alarm.",
          health(pad=pad()),
          app={"update": {"state": "available", "version": "0.6.3",
                          "candidate": "9c1e77f2b4", "behind": 4}}),

    state("updating", "Updating",
          "In flight. The stages are the content; there is nothing to press and nothing else to "
          "read.",
          health(pad=pad()),
          app={"update": {"state": "running", "version": "0.6.3",
                          "stages": [{"stage": "Preparing", "state": "ok"},
                                     {"stage": "Testing", "state": "ok"},
                                     {"stage": "Restarting", "state": "running"},
                                     {"stage": "Verifying", "state": "pending"}]}}),

    state("update-failed", "Update failure / rollback",
          "The update moved the build and CROOKS OS did not come back. The previous build has "
          "been restored. Unmistakable, and it says what was done.",
          health(pad=pad(), checks={**health()["checks"], "shopify": check(False, DOWN)}),
          app={"update": {"state": "failed", "version": "0.6.3", "restored": "a3f91c2d10",
                          "why": "CROOKS OS did not come back healthy within 90 seconds."}}),
]

if __name__ == "__main__":
    json.dump({"states": STATES}, sys.stdout, indent=1, sort_keys=False)
    sys.stdout.write("\n")
