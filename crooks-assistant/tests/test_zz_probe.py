from __future__ import annotations

import pytest

from experience.harness import TABLET_HEADERS, harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_open_entity_across_sessions(stage):
    a = await stage.say("show me order 1938", session_id="leakA")
    print("A entity", a.entity, a.answer[:80])
    b = await stage.touch("open.entity", session_id="leakB", kind="order",
                          ref="gid://shopify/Order/1938", label="pwned")
    print("B status", b.status, "ok", b.raw.get("ok"), "code", b.raw.get("code"))
    print("B ui types", b.surface_types)
    print("B issued", stage.runtime.sessions.get_or_create("leakB").issued_ids)
    import json
    print(json.dumps(b.raw.get("ui"), default=str)[:1200])


async def test_adopt_latest_set_across_branches(stage):
    s = "leakS"
    await stage.say("show me order 1938", session_id=s)
    fork = await stage.client.post("/branches/fork", data={"session_id": s, "label": "right"}, headers=TABLET_HEADERS)
    child = fork.json()["branch_id"]
    print("child", child, "focused", fork.json()["focused"])
    parent = [b for b in fork.json()["branches"] if b["branch_id"] != child][0]["branch_id"]
    # a listing on the child half
    r = await stage.say("which customers are waiting on a reply", session_id=s, branch_id=child)
    print("child listing", r.lane, r.recipe_id, r.answer[:100], r.surface_types)
    session = stage.runtime.sessions.get_or_create(s)
    print("sets", {k: (v.kind, v.count) for k, v in session.sets.items()})
    pb = session.branches[parent]
    cb = session.branches[child]
    print("parent wf", pb.workflow, "set", pb.set_id)
    print("child wf", cb.workflow, "set", cb.set_id)
    # now say "next" on the parent half
    n = await stage.say("next", session_id=s, branch_id=parent)
    print("next on parent:", n.lane, n.recipe_id, n.answer[:120])
    print("parent wf after", session.branches[parent].workflow, "set", session.branches[parent].set_id)
