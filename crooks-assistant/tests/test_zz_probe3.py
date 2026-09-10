from __future__ import annotations

import pytest

from experience.harness import harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_open_entity_other_login_open_allowlist(stage):
    stage.configure(logins="")
    await stage.say("show me order 1938", session_id="ownerS")
    other = {"Tailscale-User-Login": "intruder@example.com", "X-Forwarded-For": "100.64.0.44"}
    r = await stage.client.post("/turn", json={"text": "what can you do", "session_id": "otherS"}, headers=other)
    print("other turn", r.status_code, (r.json() or {}).get("code"), str((r.json() or {}).get("detail"))[:120])
    r2 = await stage.client.post("/command", data={
        "session_id": "otherS", "command": "open.entity", "kind": "order",
        "ref": "gid://shopify/Order/1938"}, headers=other)
    body = r2.json()
    print("open.entity", r2.status_code, body.get("ok"), body.get("code"))
    ui = body.get("ui") or []
    d = (ui[0].get("data") if ui else {}) or {}
    print("leaked:", d.get("order_number"), d.get("customer_name"), d.get("customer_email"), (d.get("shipping") or {}))
