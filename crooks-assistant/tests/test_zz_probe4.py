from __future__ import annotations

import pytest

from experience.harness import harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_other_kinds(stage):
    stage.configure(logins="")
    a = await stage.say("what has Mia Jones ordered", session_id="ownerS")
    print("A", a.recipe_id, a.surface_types, a.entity)
    b = await stage.say("what is in my inbox", session_id="ownerS")
    print("B", b.recipe_id, b.surface_types)
    from app.memory import current
    m = current()
    keys = {t: list(v.keys()) for t, v in m._tiers.items() if v}
    print("MEMORY", keys)
    other = {"Tailscale-User-Login": "intruder@example.com", "X-Forwarded-For": "100.64.0.44"}
    await stage.client.post("/turn", json={"text": "what can you do", "session_id": "otherS"}, headers=other)
    for kind, ref in [(k.split(":", 1)[0], k.split(":", 1)[1]) for k in keys.get("entity", [])]:
        r = await stage.client.post("/command", data={
            "session_id": "otherS", "command": "open.entity", "kind": kind, "ref": ref}, headers=other)
        body = r.json()
        ui = body.get("ui") or []
        print(kind, ref[:50], "->", body.get("ok"), body.get("code"), [i.get("type") for i in ui],
              str((ui[0].get("data") if ui else {}))[:200])
