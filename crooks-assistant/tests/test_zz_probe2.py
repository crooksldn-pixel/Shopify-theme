from __future__ import annotations

import pytest

from experience.harness import TABLET_HEADERS, harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_open_entity_from_another_login(stage):
    await stage.say("show me order 1938", session_id="ownerS")
    other = {"Tailscale-User-Login": "intruder@example.com", "X-Forwarded-For": "100.64.0.44"}
    r = await stage.client.post("/turn", json={"text": "what can you do", "session_id": "otherS"}, headers=other)
    print("other turn", r.status_code)
    r2 = await stage.client.post("/command", data={
        "session_id": "otherS", "command": "open.entity", "kind": "order",
        "ref": "gid://shopify/Order/1938"}, headers=other)
    body = r2.json()
    print("other open.entity", r2.status_code, body.get("ok"), body.get("code"))
    ui = body.get("ui") or []
    print("types", [i.get("type") for i in ui])
    d = (ui[0].get("data") if ui else {}) or {}
    print("leaked:", d.get("order_number"), d.get("customer_name"), d.get("customer_email"))


async def test_set_line_on_the_other_half(stage):
    s = "setLeak"
    await stage.say("show me order 1938", session_id=s)
    fork = await stage.client.post("/branches/fork", data={"session_id": s, "label": "right"}, headers=TABLET_HEADERS)
    child = fork.json()["branch_id"]
    parent = [b for b in fork.json()["branches"] if b["branch_id"] != child][0]["branch_id"]
    await stage.say("which customers are waiting on a reply", session_id=s, branch_id=child)
    session = stage.runtime.sessions.get_or_create(s)
    print("focus", session.focus)
    n = await stage.say("tell me what you make of it", session_id=s, branch_id=parent)
    print("lane", n.lane)
    asked = stage.provider.calls[-1] if stage.provider.calls else ""
    print("PROMPT TAIL:", asked[-900:])
