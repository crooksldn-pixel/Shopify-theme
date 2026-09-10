from __future__ import annotations

import pytest

from experience.harness import harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_customer_kind(stage):
    stage.configure(logins="")
    await stage.say("which customers are waiting on a reply", session_id="ownerS")
    await stage.say("next", session_id="ownerS")
    from app.memory import current
    print("MEMORY entity", list(current()._tiers.get("entity", {}).keys()))
    other = {"Tailscale-User-Login": "intruder@example.com", "X-Forwarded-For": "100.64.0.44"}
    await stage.client.post("/turn", json={"text": "hello", "session_id": "otherS"}, headers=other)
    for key in list(current()._tiers.get("entity", {}).keys()):
        kind, ref = key.split(":", 1)
        r = await stage.client.post("/command", data={
            "session_id": "otherS", "command": "open.entity", "kind": kind, "ref": ref}, headers=other)
        b = r.json()
        ui = b.get("ui") or []
        print(kind, ref[:44], b.get("ok"), b.get("code"), [i.get("type") for i in ui], str(ui[0].get("data") if ui else "")[:180])
