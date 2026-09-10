from __future__ import annotations

import json

import pytest

from experience.harness import TABLET_HEADERS, harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_open_entity_across_sessions(stage):
    a = await stage.say("show me order 1938", session_id="leakA")
    print("A entity", a.entity)
    await stage.say("what can you do", session_id="leakB")
    sb = stage.runtime.sessions.get_or_create("leakB")
    print("B issued before:", sb.issued_ids)
    b = await stage.touch("open.entity", session_id="leakB", kind="order",
                          ref="gid://shopify/Order/1938", label="pwned")
    print("B status", b.status, "ok", b.raw.get("ok"), "code", b.raw.get("code"))
    print("B ui types", b.surface_types)
    print("B answer", b.answer)
    print(json.dumps(b.raw.get("ui"), default=str)[:900])
    print("B branch entity", stage.branch("leakB").entity)


async def test_command_on_a_cancelled_branch(stage):
    s = "leakC"
    await stage.say("show me order 1938", session_id=s)
    fork = await stage.client.post("/branches/fork", data={"session_id": s, "label": "right"}, headers=TABLET_HEADERS)
    child = fork.json()["branch_id"]
    r = await stage.client.post(f"/branches/{child}/cancel", data={"session_id": s}, headers=TABLET_HEADERS)
    print("cancel", r.status_code, r.json().get("focused"))
    session = stage.runtime.sessions.get_or_create(s)
    print("statuses", {b.branch_id: b.status for b in session.branches.values()})
    t = await stage.touch("voice.bind", session_id=s, branch_id=child, family="order.add_note")
    print("bind on cancelled:", t.status, t.raw.get("ok"), t.raw.get("code"), (t.raw.get("changed") or {}))
    print("branch in reply", (t.raw.get("branch") or {}).get("branch_id"), (t.raw.get("branch") or {}).get("status"))
    n = await stage.touch("surface.expand", session_id=s, branch_id=child, ref="row-1")
    print("expand on cancelled:", n.raw.get("ok"), (n.raw.get("changed") or {}))


async def test_expanded_survives_navigation(stage):
    s = "leakE"
    await stage.say("show me order 1938", session_id=s)
    await stage.touch("surface.expand", session_id=s, ref="line-item-7")
    await stage.say("show me order 1940", session_id=s)
    br = stage.branch(s)
    print("entity", br.entity, "expanded", br.expanded)
    print("public", br.public().get("expanded"))
