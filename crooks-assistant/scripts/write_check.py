#!/usr/bin/env python3
"""Rehearse one change against the live store or inbox, from the Mac's keyboard, through the
same engine the tablet uses: stage it, print the card the tablet would show, and — only with
--commit and a typed confirmation — arm and commit it, then print what the proof saw.

    python scripts/write_check.py shopify_order_note_append '{"order_id": "gid://shopify/Order/…", "note": "rehearsal"}'
    python scripts/write_check.py shopify_order_tags_add '{"order_id": "…", "tags": ["rehearsal"]}' --commit

The ids in the arguments are issued to the rehearsal's own session first, as a search would
have issued them. Nothing here bypasses the engine: the tool prepares, the engine re-reads,
sends once, proves. Use it on the designated safe order, in the order the live test plan
gives; never on a real customer's order for a cancel or a refund.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tool", help="the write tool's name, e.g. shopify_order_note_append")
    parser.add_argument("args", help="the tool's arguments as JSON")
    parser.add_argument("--commit", action="store_true", help="after staging, arm and commit (asks for a typed confirmation)")
    options = parser.parse_args()
    try:
        args = json.loads(options.args)
    except ValueError as exc:
        print(f"arguments are not JSON: {exc}")
        return 2

    from app.actions.grammar import HOLD_MS, dwell_ms
    from app.runtime import build
    from app.tools import registry
    from app.tools.dispatch import dispatch

    runtime = build()
    # The keyboard is the owner's: this process may commit, and there is no tablet to confirm.
    runtime.settings = runtime.settings.model_copy(update={"writes_enabled": True, "writes_local_owner": True, "tailscale_verify": False})
    from app.tools import gmail_writes, shopify_writes

    shopify_writes.bind_policy(lambda: runtime.settings)
    gmail_writes.bind(runtime.gmail, policy=lambda: runtime.settings)

    session = runtime.sessions.get_or_create("write-check")
    session.epoch = max(session.epoch, 1)
    for key, value in args.items():
        if key.endswith("_id") and isinstance(value, str):
            session.issue(value)
    status = await runtime.write_status(registry.get(options.tool).write.operation if registry.get(options.tool).write else None)
    print(f"preflight     : {status.state} — {status.detail}")
    text = await dispatch(options.tool, args, session=session, timeout_s=15)
    print(f"tool answered : {text[:400]}")
    if not session.proposals:
        return 1
    proposal = session.proposals[-1]
    spec = registry.get(options.tool)
    words = spec.write.present(proposal)
    print(f"card          : {words.get('title')} · {proposal.risk} · {proposal.interaction}")
    for fact in words.get("facts") or []:
        print(f"  {fact.get('label'):<18} {fact.get('value')}")
    if words.get("body"):
        print("  body:\n    " + str(words["body"]).replace("\n", "\n    "))
    print(f"read-back     : {proposal.summary.get('read_back')}")
    print(f"before        : {proposal.before}")
    if not options.commit:
        print("staged only; add --commit to apply it (the proposal expires with its TTL)")
        return 0
    if not status.ready:
        print("not committing: the preflight is not ready")
        return 1
    typed = input(f'type "apply" to {proposal.summary.get("read_back") or "apply this"}: ').strip()
    if typed != "apply":
        print("not applied")
        return 1
    armed, code = runtime.actions.arm(proposal.proposal_id, session.session_id)
    if code:
        print(f"could not arm: {code}")
        return 1
    dwell = max(dwell_ms(proposal.interaction), HOLD_MS) / 1000.0
    print(f"holding {dwell:.1f}s …")
    await asyncio.sleep(dwell + 0.2)
    started = time.perf_counter()
    result = await runtime.actions.commit(proposal.proposal_id, session.session_id, caller="local", spec_lookup=lambda n: registry.get(n), nonce=proposal.arm_nonce)
    print(f"outcome       : {result.code} in {time.perf_counter() - started:.2f}s — {result.spoken}")
    print(f"after         : {proposal.after}")
    if proposal.note:
        print(f"note          : {proposal.note}")
    if proposal.undo_id:
        print(f"undo staged   : {proposal.undo_id} (expires with its TTL; commit it the same way to reverse)")
    for line in runtime.actions.ledger.read()[-4:]:
        print(f"ledger        : {line.get('event')} {line.get('code') or ''} {line.get('reason') or ''}".rstrip())
    return 0 if result.code == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
