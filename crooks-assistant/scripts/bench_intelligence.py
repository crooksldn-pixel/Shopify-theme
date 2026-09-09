"""Time the read layer, the working sets, the cross-source read and batch staging against a
fake store, so a change to them is measured rather than felt.

Nothing here reaches a network. The store is the test suite's fake with a season of orders
generated on it; Shopify's latency is simulated per request so the numbers say how many
round trips a question costs as well as how long the Mac's own work takes.

    make bench-intelligence            # or: .venv/bin/python scripts/bench_intelligence.py [--orders 400] [--latency-ms 40]

Before / after: "before" is the path the assistant had for the same question before the
read layer existed — a listing tool paged through by the model (shopify_list_orders, twenty
orders a call, the sums done in the model's head), or nothing at all — measured here as the
number of tool calls it would take and the time those calls cost at the same latency.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("CROOKS_ANALYTICS_WARM_DAYS", "0")


def _fmt(ms: float) -> str:
    return f"{ms:,.0f} ms"


async def _timed(fn, *, repeat: int = 3) -> tuple[float, float]:
    """Best and median of `repeat` runs, in ms."""
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        await fn()
        samples.append((time.perf_counter() - t0) * 1000)
    return min(samples), statistics.median(samples)


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--orders", type=int, default=400, help="orders over the last 90 days")
    parser.add_argument("--latency-ms", type=float, default=40.0, help="simulated Shopify / Gmail latency per request")
    args = parser.parse_args(argv)

    from app.actions import batch as batch_module
    from app.actions import engine as engine_module
    from app.actions.engine import ActionEngine
    from app.actions.ledger import NullLedger
    from app.analytics import sets
    from app.analytics.cache import OrderCache
    from app.session.models import Session
    from app.tools import analytics_tools, batch_tools, shopify_tools  # noqa: F401
    from app.tools.dispatch import dispatch
    from tests.test_analytics import HOODIE, JEANS, JOGGERS, node
    from tests.test_analytics_tools import Store, london_now
    from tests.test_batch import ManyStore

    class Patch:
        def setattr(self, obj, name, value):
            setattr(obj, name, value)

    london_now(Patch())
    products = [JOGGERS, JEANS, HOODIE]
    colours = ["Black", "Pink", "Grey", "Blue"]
    sizes = ["S", "M", "L", "XL"]
    nodes = []
    for i in range(args.orders):
        p = products[i % 3]
        nodes.append(node(1000 + i, days_ago=(i * 89.0 / max(1, args.orders)) + 0.1, items=[(*p, colours[i % 4], sizes[i % 4], 1 + i % 3, 45.0 + 15 * (i % 3))],
                         customer=(f"gid://shopify/Customer/{i % 60}", f"Customer {i % 60} Name", 1 + i % 5, 100.0 * (1 + i % 5)), fulfillment="UNFULFILLED" if i % 7 == 0 else "FULFILLED"))
    store = Store(nodes)
    store.delay_s = args.latency_ms / 1000.0
    for n in nodes:
        for e in n["lineItems"]["edges"]:
            store.stock[e["node"]["variant"]["id"]] = 12
    clock = time.time
    cache = OrderCache(lambda: store, clock=clock)
    analytics_tools.bind(cache)
    session = Session(session_id="bench")
    session.epoch = 1
    rows = []

    async def q(name, spec):
        # Every measured call is its own turn: the plan would otherwise hand back the last
        # answer instead of running the query again.
        session.plan = None
        calls: list = []
        text = await dispatch(name, spec, session=session, timeout_s=30, calls=calls)
        assert not text.startswith(("ERROR", "REFUSED")), text
        return calls[-1].result

    # --- best sellers: cold (pages Shopify) and warm (the cache)
    pages_before = store.pages
    cold_best, _ = await _timed(lambda: q("commerce_aggregate", {"period": "this_month", "group_by": ["product"], "metrics": ["units", "revenue"], "view": "ranking"}), repeat=1)
    pages_cold = store.pages - pages_before
    session.plan = None
    warm_best, warm_med = await _timed(lambda: q("commerce_aggregate", {"period": "last_30_days", "group_by": ["product"], "metrics": ["units", "revenue"], "view": "ranking"}))
    listing_calls = -(-min(args.orders, args.orders // 3) // 20)
    rows.append(["Best sellers (month)", f"{listing_calls} × shopify_list_orders calls ≈ {_fmt(listing_calls * args.latency_ms)} + the model summing", f"cold {_fmt(cold_best)} ({pages_cold} Shopify pages)", f"warm {_fmt(warm_best)} (0 pages)"])
    # --- stock cover
    session.plan = None
    cold_stock, _ = await _timed(lambda: q("inventory_query", {"period": "last_7_days", "limit": 10}), repeat=1)
    session.plan = None
    warm_stock, _ = await _timed(lambda: q("inventory_query", {"period": "last_7_days", "limit": 10}))
    rows.append(["Stock cover / restock priority", "not composable (shopify_inventory is one product at a time)", f"cold {_fmt(cold_stock)}", f"warm {_fmt(warm_stock)}"])
    # --- a working set from a listing, and a follow-up on it
    session.plan = None
    made = {}

    async def listing():
        made["set"] = (await q("commerce_query", {"entity": "orders", "period": "last_90_days", "filters": {"fulfillment": "unfulfilled", "older_than_days": 5}}))["set"]

    set_ms, _ = await _timed(listing)
    session.plan = None
    follow_ms, _ = await _timed(lambda: q("commerce_query", {"entity": "orders", "period": "last_90_days", "filters": {"in_set": made["set"]["set_id"], "country_code": "GB"}}))
    rows.append([f"Working set ({made['set']['count']} delayed orders)", "re-run the search and re-read every order", f"{_fmt(set_ms)}", "—"])
    rows.append(["Follow-up on the set (narrow to UK)", "re-run the search", f"{_fmt(follow_ms)}", "—"])
    # --- cross-source
    async def threads_for(**kwargs):
        await asyncio.sleep(args.latency_ms / 1000.0)
        return {"available": True, "threads": [{"thread_id": "18f0000000000001", "subject": "Order?", "date": "", "snippet": ""}] if kwargs.get("sender", "").startswith("customer 1") else []}

    async def replied(thread_id):
        await asyncio.sleep(args.latency_ms / 1000.0)
        return False

    analytics_tools.bind_email(threads_for, replied)
    session.plan = None
    small = sets.create(session, kind="orders", members=list(made["set"]["set_id"] and [n["id"] for n in nodes if n["displayFulfillmentStatus"] == "UNFULFILLED"][:20]), label="twenty delayed")
    cross_ms, _ = await _timed(lambda: q("email_query", {"set_id": small.set_id, "days": 30}), repeat=1)
    rows.append(["Cross-source (20 customers × Gmail)", f"20 × gmail_search calls by the model ≈ {_fmt(20 * args.latency_ms)}", f"{_fmt(cross_ms)} (4 in flight)", "—"])
    # --- batch staging
    engine = ActionEngine(ledger=NullLedger())
    engine_module.install(engine)
    batches = batch_module.install(batch_module.BatchEngine(engine))
    for count in (20, 50):
        many = ManyStore({f"gid://shopify/Order/{9000 + i}": [] for i in range(count)})
        many.delay_s = 0.0

        original = many.graphql

        async def slow_graphql(query, variables=None, _orig=original):
            await asyncio.sleep(args.latency_ms / 1000.0)
            return await _orig(query, variables)

        many.graphql = slow_graphql  # type: ignore[method-assign]
        shopify_tools.bind(many)
        ws = sets.create(session, kind="orders", members=list(many.orders), label=f"{count} orders", labels={k: v["name"] for k, v in many.orders.items()})
        session.epoch += 1

        async def staging(ws=ws):
            calls: list = []
            text = await dispatch("batch_order_tags_add", {"set_id": ws.set_id, "tags": ["bench"]}, session=session, timeout_s=60, calls=calls)
            assert text.startswith("PROPOSED BATCH"), text

        stage_ms, _ = await _timed(staging, repeat=1)
        rows.append([f"Batch staging ({count} orders)", f"{count} separate proposals, {count} gestures", f"{_fmt(stage_ms)} ({batch_module.PREPARE_CONCURRENCY} reads in flight)", "—"])
        batch = list(session.batches.values())[-1]
        batches.arm(batch.batch_id, "bench")
        batch.armed_at -= 1.0

        async def committing(batch=batch):
            from app.tools import registry

            result = await batches.commit(batch.batch_id, "bench", caller="bench", spec_lookup=lambda n: registry.get(n), nonce=batch.arm_nonce)
            assert result.code == "done", result.code

        commit_ms, _ = await _timed(committing, repeat=1)
        rows.append([f"Batch commit ({count} orders, read + write + re-read each)", f"{count} taps ≈ {_fmt(count * 3 * args.latency_ms)} sequential", f"{_fmt(commit_ms)} ({batch_module.COMMIT_CONCURRENCY} in flight)", "—"])

    print(f"\nRead layer, working sets and batches against a fake store: {args.orders} orders, {args.latency_ms:.0f} ms per Shopify/Gmail request\n")
    widths = [max(len(str(r[i])) for r in rows + [["Question", "Before", "After", "After (warm)"]]) for i in range(4)]
    header = ["Question", "Before", "After", "After (warm)"]
    print("| " + " | ".join(h.ljust(w) for h, w in zip(header, widths, strict=True)) + " |")
    print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for r in rows:
        print("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths, strict=True)) + " |")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
