"""§14: no N+1 reads, with the before and the after measured rather than claimed.

D-4's read pattern, from the timeline:

    turn_be1b384ca420   shopify_customer_history x 7 — one per candidate customer
                        to answer "how many of today's buyers have bought before".

Seven reads for a fact the Mac already held: `numberOfOrders` and `amountSpent` are on every
order row the cache stores (app/analytics/cache.py ORDERS_QUERY). The whole session spent
24,567 ms reading against 21,885 ms waiting for prose — the reads dominated, and this is the
shape of most of them.

Every test here counts REQUESTS TO THE SOURCE, not tool calls: a tool that is served from the
Mac's own cache costs the shop nothing, and a tool call is not the unit the owner waits on.
`Counting` below wraps the fixture store, so the count is what actually went out.

The BEFORE numbers are measured the same way, against the same fixture, by running the read
pattern the model actually used that evening — `commerce_query` for the day and then one
`shopify_customer_history` per buyer. They are not estimates: `test_the_audit_table` runs
both halves and prints the table the report carries.
"""

from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime

import pytest

from app.analytics.cache import OrderCache
from app.families import load_all
from app.fastpath import recipe_for, resolve, runner
from app.fastpath.models import Ctx
from app.session.branch import Branch
from app.session.models import Session
from app.tools import analytics_tools, shopify_tools
from app.tools.context import CURRENT_SESSION
from tests.test_analytics import HOODIE, NOW, node
from tests.test_analytics_tools import Store
from tests.test_summaries import NODES, SEVEN

load_all()

# The bound this pass puts on each audited workflow, stated so that a change which quietly
# reintroduces a per-entity read fails here rather than on the tablet.
#
# Two numbers, because two things are being bounded and only one of them is the defect:
#
#   TOOL CALLS      one. A summary question is one read tool, whose whole answer is the
#                   aggregation the Mac does over rows it has.
#   ENTITY READS    ZERO. Not "fewer than seven": the fact D-4 spent seven reads on —
#                   `numberOfOrders`, `amountSpent` — is on every order row already, so the
#                   right number of per-customer reads to answer it is none.
#
# What is NOT bounded to one is requests to Shopify, and pretending otherwise would be the
# kind of number that has to be widened later. The order cache reads its window in PAGES
# (app/analytics/cache.py PAGE = 8 orders, paced against the leaky bucket), so a wider window
# is more pages — that is data volume, it is already bounded by MAX_PAGES and paced, and it
# is the same for every question about the same period. `pages_for` below says what the
# paging alone costs, and the tests assert the workflows spend that and not a request more.
BOUND: dict[str, tuple[int, int]] = {
    "returning_customers": (1, 0),
    "customer_lifetime": (0, 0),
    "orders_attention": (1, 0),
    "order_list": (1, 0),
}


def pages_for(orders: int) -> int:
    """What reading `orders` orders costs the cache in requests, and nothing above it."""
    from app.analytics.cache import PAGE

    return max(1, math.ceil(orders / PAGE))


class Counting(Store):
    """The fixture store, counting what actually left the Mac, by query name.

    `CrooksOrderRows` is a page of the cache's own window; `CrooksCustomerOrders` is one
    customer's history — the read D-4 made seven of. Counting them apart is the whole point:
    a workflow may legitimately page the cache and must not read an entity per row.
    """

    def __init__(self, nodes=NODES) -> None:
        super().__init__(nodes)
        self.by_query: dict[str, int] = {}

    async def graphql(self, query, variables=None):
        for name in ("CrooksOrderRows", "CrooksCustomerOrders", "CrooksVariantStock", "Inventory"):
            if name in query:
                self.by_query[name] = self.by_query.get(name, 0) + 1
                break
        if "CrooksCustomerOrders" in query:
            if self.delay_s:
                await asyncio.sleep(self.delay_s)
            return {"data": {"customer": self._customer((variables or {}).get("id"))}}
        if "query Inventory" in query:
            if self.delay_s:
                await asyncio.sleep(self.delay_s)
            return {"data": {"products": {"pageInfo": {"hasNextPage": False},
                                          "edges": self._products((variables or {}).get("n") or 1)}}}
        return await super().graphql(query, variables)

    def _products(self, n):
        """The catalogue, as `shopify_inventory` shapes it. Built from the same line items, so
        the BEFORE path reads the truth and not a stub."""
        seen: dict[str, dict] = {}
        for order in self.nodes:
            for edge in order["lineItems"]["edges"]:
                item = edge["node"]
                product = item["product"]
                seen.setdefault(product["id"], {
                    "id": product["id"], "title": product["title"], "status": "ACTIVE",
                    "totalInventory": 6, "variants": {"edges": []},
                })
                seen[product["id"]]["variants"]["edges"].append({"node": {
                    "id": item["variant"]["id"], "title": item["variantTitle"],
                    "sku": item["sku"], "inventoryQuantity": 3,
                    "inventoryPolicy": "DENY", "inventoryItem": {"tracked": True},
                }})
        return [{"node": node} for node in list(seen.values())[: max(1, int(n))]]

    def _customer(self, customer_id):
        """One customer's history, as `CUSTOMER_ORDERS_QUERY` shapes it — built from the same
        order nodes, so the BEFORE path reads the truth and not a stub."""
        theirs = [n for n in self.nodes if (n.get("customer") or {}).get("id") == customer_id]
        if not theirs:
            return None
        first = theirs[-1]
        node_of = theirs[0]["customer"]
        return {
            "id": customer_id, "displayName": node_of["displayName"],
            "numberOfOrders": node_of["numberOfOrders"], "createdAt": node_of["createdAt"],
            "tags": [], "amountSpent": node_of["amountSpent"],
            "defaultEmailAddress": node_of["defaultEmailAddress"],
            "lastOrder": {"id": theirs[0]["id"], "name": theirs[0]["name"]},
            "firstOrder": {"edges": [{"node": {"id": first["id"], "name": first["name"],
                                               "processedAt": first["createdAt"],
                                               "createdAt": first["createdAt"]}}]},
            "openOrders": {"edges": []},
            "orders": {"edges": [{"node": {
                "id": n["id"], "name": n["name"], "createdAt": n["createdAt"],
                "processedAt": n["createdAt"], "cancelledAt": None,
                "displayFulfillmentStatus": n["displayFulfillmentStatus"],
                "displayFinancialStatus": n["displayFinancialStatus"],
                "currentTotalPriceSet": n["currentTotalPriceSet"],
                "lineItems": {"edges": [{"node": {"title": e["node"]["title"], "quantity": e["node"]["quantity"]}}
                                        for e in n["lineItems"]["edges"]]},
            }} for n in theirs]},
        }

    @property
    def source_reads(self) -> int:
        return sum(self.by_query.values())

    @property
    def entity_reads(self) -> int:
        """The N+1 itself: one request per record on a list."""
        return self.by_query.get("CrooksCustomerOrders", 0)

    @property
    def product_reads(self) -> int:
        return self.by_query.get("Inventory", 0)


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)


def _bind(store) -> None:
    """The read tools against this store, with no inbox behind them.

    The hydrator is built here rather than through `shopify_tools.bind`, which goes looking
    for Gmail when it is not handed a correlation helper: these measurements are about
    Shopify reads and an inbox in the middle of them would be a second variable.
    """
    from app.context.order import Hydrator

    analytics_tools.bind(OrderCache(lambda: store, clock=lambda: NOW.timestamp()))
    analytics_tools.datetime = FixedDatetime
    shopify_tools._client = store
    shopify_tools._hydrator = Hydrator(lambda: store, threads_for=None, clock=lambda: NOW.timestamp())


@pytest.fixture()
def shop(monkeypatch):
    store = Counting()
    _bind(store)
    monkeypatch.setattr(analytics_tools, "datetime", FixedDatetime)
    try:
        yield store
    finally:
        analytics_tools.bind(None)
        shopify_tools._client = None
        shopify_tools._hydrator = None


async def turn(text: str, *, session: Session | None = None):
    session = session or Session(session_id="n1")
    session.turn_id = "turn_n1"
    branch = Branch(branch_id="br_n1", session_id=session.session_id)
    intent = resolve(text, branch=branch)
    recipe = recipe_for(intent.family) if intent.family else None
    assert recipe is not None, f"{text!r} resolved to {intent.family!r} and has no recipe"
    fast = await runner.run(recipe, Ctx(runtime=None, session=session, branch=branch,
                                        intent=intent, text=text))
    assert not fast.deferred, fast.defer
    return fast, session


# ----------------------------------------------------------- the bound, enforced


async def test_the_returning_customers_answer_reads_the_period_once(shop):
    """The defect, as a number: seven entity reads become none.

    The bound is stated and enforced: one request to the source for the period, and ZERO
    per-customer reads however many buyers there are.
    """
    fast, _session = await turn("any returning customers today")
    calls, entities = BOUND["returning_customers"]
    assert shop.entity_reads == entities, f"{shop.entity_reads} per-customer reads: {shop.by_query}"
    assert len(fast.calls) == calls, [c.name for c in fast.calls]
    # And nothing beyond what paging the period costs: no request per buyer, and none for
    # anything the aggregation worked out for itself.
    assert shop.source_reads <= pages_for(len(NODES)), shop.by_query
    # It answered: one, out of seven buyers.
    assert fast.trace["count"] == 1, fast.trace


async def test_the_answer_does_not_grow_a_read_when_the_shop_does(shop):
    """The N+1 test proper: more buyers must not mean more reads.

    Seven buyers here; the same question over twenty-five buyers reads exactly as much. A
    per-entity read would show up as twenty-five.
    """
    more = list(NODES) + [
        node(3000 + n, days_ago=0.05, items=[(*HOODIE, "Grey", "M", 1, 60.0)],
             customer=(f"gid://shopify/Customer/{7100 + n}", f"Buyer {n}", 4, 400.0))
        for n in range(25)
    ]
    shop.nodes = [dict(x) for x in more]
    fast, _session = await turn("any returning customers today")
    assert shop.entity_reads == 0, shop.by_query
    assert len(fast.calls) == 1, [c.name for c in fast.calls]
    # Thirty-two more rows cost more PAGES and not one read more than that: the paging is the
    # data, and the N+1 — a request per buyer — would be twenty-five of them.
    assert shop.source_reads <= pages_for(len(more)), shop.by_query
    assert shop.source_reads < 25, f"a read per buyer crept back: {shop.by_query}"
    assert fast.trace["count"] >= 25, fast.trace


async def test_two_summary_questions_in_a_row_read_the_shop_once(shop):
    """§36: the second question is answered from the view the first took.

    The cache is the mechanism and this is the assertion that it is actually in the path —
    without it a "one read per question" bound is still one read per question, and the owner
    asking three things in a minute waits three times.
    """
    session = Session(session_id="warm")
    await turn("any returning customers today", session=session)
    after_first = shop.source_reads
    await turn("which orders need attention", session=session)
    await turn("what came in yesterday", session=session)
    assert shop.source_reads == after_first, f"the warm cache was not used: {shop.by_query}"
    assert shop.entity_reads == 0, shop.by_query


async def test_the_attention_and_listing_answers_keep_the_same_bound(shop):
    for text, workflow in (("which orders need attention", "orders_attention"),
                           ("what came in yesterday", "order_list")):
        store = Counting()
        _bind(store)
        fast, _session = await turn(text)
        calls, entities = BOUND[workflow]
        assert store.entity_reads == entities, f"{text!r}: {store.by_query}"
        assert len(fast.calls) == calls, [c.name for c in fast.calls]
        assert store.source_reads <= pages_for(len(NODES)), f"{text!r}: {store.by_query}"


async def test_lifetime_metrics_for_a_whole_set_read_nothing_at_all(shop):
    """§14's second named workflow, measured: the values are already on the rows."""
    from zoneinfo import ZoneInfo

    from app.analytics import summarise

    view = await analytics_tools.cache().view(_ninety_days())
    before = shop.source_reads
    held = summarise.customer_lifetime(view.rows, [c[0] for c in SEVEN], zone=ZoneInfo("Europe/London"))
    assert shop.source_reads == before, "aggregating read the shop"
    assert len([k for k, v in held.items() if v.get("held")]) == len(SEVEN)


def _ninety_days():
    from datetime import timedelta

    from app.analytics.periods import Period

    return Period(NOW - timedelta(days=90), NOW, "held", "days")


# ------------------------------------------------------- the before, measured the same way


async def _before_returning_customers(store) -> tuple[int, float]:
    """The read pattern of turn_be1b384ca420, run against this fixture.

    `commerce_query` for the day, then one `shopify_customer_history` per buyer — which is
    what the model did, and what the seven calls in the timeline are. Measured, so the
    report's "before" column is a number this suite produced rather than one copied out of
    a log.
    """
    session = Session(session_id="before")
    session.turn_id = "turn_before"
    token = CURRENT_SESSION.set(session)
    started = time.perf_counter()
    try:
        listing = await analytics_tools.commerce_query(
            entity="orders", period="today", limit=25, title="Orders",
        )
        buyers = [row["customer_id"] for row in listing["rows"] if row.get("customer_id")]
        # One per buyer, in turn, exactly as the seven calls in the timeline were.
        for customer_id in dict.fromkeys(buyers):
            await shopify_tools.shopify_customer_history(customer_id)
    finally:
        CURRENT_SESSION.reset(token)
    return store.source_reads, (time.perf_counter() - started) * 1000


async def _after_returning_customers(store) -> tuple[int, float]:
    started = time.perf_counter()
    await turn("any returning customers today")
    return store.source_reads, (time.perf_counter() - started) * 1000


async def test_the_before_pattern_really_does_read_once_per_buyer(shop):
    """The BEFORE column, proved to be what the forensics says it is.

    Without this the "after" number means nothing: a bound of one is only an improvement if
    the pattern it replaced was seven, and this is where that is measured rather than
    asserted from the timeline.
    """
    reads, _ms = await _before_returning_customers(shop)
    assert shop.entity_reads == len(SEVEN), f"expected one read per buyer: {shop.by_query}"
    assert reads >= len(SEVEN) + 1, shop.by_query


# What one request to Shopify actually cost the owner that evening: 24,567 ms of reading
# across the session's 40 tool calls. The fixture store has no network in it, so a wall-time
# column measured against it would say "0.4 ms before, 0.2 ms after" and mean nothing. Each
# audited workflow is therefore measured TWICE — once with the store answering instantly, for
# the code's own cost, and once with every request delayed by this, for the number the owner
# would feel. The delay is the session's own average and not a guess.
SESSION_MS_PER_READ = 24_567 / 40


async def _before_customer_lifetime(store) -> tuple[int, float]:
    """Lifetime orders and lifetime spend for the seven buyers, the way it was read: the
    period, then one `shopify_customer_history` each."""
    return await _before_returning_customers(store)


async def _after_customer_lifetime(store) -> tuple[int, float]:
    """The same figures, from the rows the view already returned."""
    from zoneinfo import ZoneInfo

    from app.analytics import summarise

    started = time.perf_counter()
    view = await analytics_tools.cache().view(_ninety_days())
    summarise.customer_lifetime(view.rows, [c[0] for c in SEVEN], zone=ZoneInfo("Europe/London"))
    return store.source_reads, (time.perf_counter() - started) * 1000


async def _before_inventory(store) -> tuple[int, float]:
    """Stock for three products, one `shopify_inventory` call each — which is what a model
    asked "how much of the jeans, the joggers and the hoodie" does."""
    started = time.perf_counter()
    for product in ("Yard Jeans", "Convict Joggers", "Convict Hoodie"):
        await shopify_tools.shopify_inventory(product=product, limit=1)
    return store.product_reads, (time.perf_counter() - started) * 1000


async def _after_inventory(store) -> tuple[int, float]:
    """The same three, in the one query the tool already supports. Nothing about this needed
    building: the audit's finding for this workflow is that the batch read EXISTS and the
    per-product call is a shape the model chooses, which is why it is measured here and told
    to the model in the tool's own description."""
    started = time.perf_counter()
    await shopify_tools.shopify_inventory(product="Convict", limit=3)
    return store.product_reads, (time.perf_counter() - started) * 1000


AUDIT = (
    ("returning customers", _before_returning_customers, _after_returning_customers),
    ("customer lifetime metrics", _before_customer_lifetime, _after_customer_lifetime),
    ("inventory summaries", _before_inventory, _after_inventory),
)


async def test_the_audit_table():
    """The §14 audit, both halves, on one fixture, printed for the report.

    Run with `-s` to read it. It is a test rather than a script so the numbers cannot drift
    from the code that produced them, and every row is asserted as well as printed: fewer
    requests, and zero per-entity reads where the aggregation replaced them.
    """
    rows = []
    for name, before, after in AUDIT:
        measured = {}
        for label, delay in (("fast", 0.0), ("real", SESSION_MS_PER_READ / 1000.0)):
            store = Counting()
            store.delay_s = delay
            _bind(store)
            before_reads, before_ms = await before(store)

            store_after = Counting()
            store_after.delay_s = delay
            _bind(store_after)
            after_reads, after_ms = await after(store_after)
            measured[label] = (before_reads, after_reads, before_ms, after_ms,
                               store.entity_reads, store_after.entity_reads)
        rows.append((name, measured))
    analytics_tools.bind(None)
    shopify_tools._client = None
    shopify_tools._hydrator = None

    print(f"\n§14 N+1 audit — one request to the shop costs {SESSION_MS_PER_READ:.0f} ms "
          f"(the live session's own average: 24,567 ms over 40 calls)\n")
    print(f"{'workflow':26} {'reads':>12}  {'ms (no latency)':>18}  {'ms (measured latency)':>22}  entity reads")
    for name, measured in rows:
        br, ar, bms, ams, be, ae = measured["fast"]
        _rbr, _rar, rbms, rams, _rbe, _rae = measured["real"]
        print(f"{name:26} {br:5} -> {ar:<4}  {bms:8.1f} -> {ams:<7.1f}  {rbms:10.0f} -> {rams:<10.0f}  {be} -> {ae}")
        assert ar < br, f"{name}: {ar} requests is not fewer than {br}"
        assert ae == 0, f"{name}: still {ae} per-entity reads"
        assert rams < rbms, f"{name}: {rams:.0f} ms is not quicker than {rbms:.0f} ms"


async def test_the_inbox_correlation_never_holds_more_of_gmail_than_gmail_has():
    """§14's third named workflow: today's order/email correlation.

    The reads here are irreducible — Gmail has no query that answers "which of these people
    wrote to us" in one — so what this asserts is the BOUND. `email_query` kept a semaphore of
    four beside the call while app/reads/budget.py SOURCE_SLOTS said Gmail was three, so the
    tool could hold four while the read scheduler believed three was the whole of it. One
    table now, read through app/reads/fanout.py.
    """
    from app.reads import budget

    peak = {"now": 0, "max": 0}

    async def threads_for(sender="", terms=(), days=30):
        peak["now"] += 1
        peak["max"] = max(peak["max"], peak["now"])
        await asyncio.sleep(0.01)
        peak["now"] -= 1
        return {"available": True, "threads": []}

    from app.analytics import sets as working_sets
    from app.analytics.cache import CacheView

    class _Cache:
        clock = staticmethod(lambda: NOW.timestamp())

        async def view(self, period, *, timeout_s=0.0):
            return CacheView(
                rows=[{"order_id": f"gid://shopify/Order/{2000 + n}", "order_number": f"CROOKS-{2000 + n}",
                       "ts": NOW.timestamp(),
                       "customer": {"customer_id": f"gid://shopify/Customer/{7200 + n}",
                                    "name": f"Buyer {n}", "email": f"b{n}@example.com"}}
                      for n in range(10)],
                complete=True, covered_days=90, synced_at=NOW.timestamp(), syncing=False)

        def _client(self):
            class _C:
                async def timezone(self):
                    from zoneinfo import ZoneInfo

                    return ZoneInfo("Europe/London")
            return _C()

    session = Session(session_id="corr")
    session.turn_id = "turn_corr"
    ws = working_sets.create(session, kind="customers",
                             members=[f"gid://shopify/Customer/{7200 + n}" for n in range(10)],
                             label="today's buyers")
    analytics_tools._cache = _Cache()
    analytics_tools.bind_email(threads_for=threads_for)
    token = CURRENT_SESSION.set(session)
    try:
        result = await analytics_tools.email_query(set_id=ws.set_id, days=30)
    finally:
        CURRENT_SESSION.reset(token)
        analytics_tools.bind_email(threads_for=None)
        analytics_tools.bind(None)
    assert result["customers"] == 10, result["customers"]
    assert peak["max"] <= budget.SOURCE_SLOTS["gmail"], (
        f"{peak['max']} Gmail reads in flight; SOURCE_SLOTS says {budget.SOURCE_SLOTS['gmail']}"
    )


# ------------------------------------------------- the bounded fan-out, where one is needed


async def test_a_bounded_fan_out_never_exceeds_the_sources_own_slots():
    """Where a read really is per-entity (an inbox check per customer), it is bounded by the
    source's own concurrency and not by a number written beside it.

    app/reads/budget.py SOURCE_SLOTS is the one table; `app/reads/fanout.py` reads it rather
    than keeping a second one, which is what stopped two layers disagreeing about how much of
    Gmail there is.
    """
    from app.reads import budget, fanout

    seen: list[int] = []
    live = {"n": 0}

    async def read(item):
        live["n"] += 1
        seen.append(live["n"])
        await asyncio.sleep(0.005)
        live["n"] -= 1
        return item

    out = await fanout.gather(range(12), read, source="gmail", lane=budget.FOREGROUND)
    assert out == list(range(12))
    assert max(seen) <= budget.SOURCE_SLOTS["gmail"], f"{max(seen)} in flight at once"


async def test_a_bounded_fan_out_reports_what_failed_and_answers_anyway():
    """A fan-out is partial or it is nothing, and a summary that loses one row to a failed
    read must say so rather than quietly counting it out."""
    from app.reads import budget, fanout

    async def read(item):
        if item == 3:
            raise RuntimeError("gmail said no")
        return item * 2

    out, failed = await fanout.gather_with_failures(
        range(5), read, source="gmail", lane=budget.FOREGROUND,
    )
    assert out == [0, 2, 4, None, 8], out
    assert list(failed) == [3] and "gmail said no" in failed[3]
