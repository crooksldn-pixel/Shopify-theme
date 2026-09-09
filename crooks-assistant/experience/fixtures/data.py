"""The golden world: five people, seven orders, three garments and an inbox that fits them.

Everything a scenario needs to be interesting is here and nothing else is. The shapes are
Shopify's and Gmail's own — `lineItems.edges[].node`, `payload.headers` — because the fixture
clients hand these straight to the production shaping code. A fixture that were already shaped
would prove only that the presenter can copy a dictionary.

Time is relative to the run. "Today's orders" has to find today's orders in five months' time,
so the stamps are computed from the clock at import and then frozen for the process: two runs
an hour apart see the same world, and a run in a year still has orders placed this morning.

Every name, address, postcode and email here is invented. There is no real customer in this
file and there must never be one: a fixture is committed to the repository and a real address
is not ours to commit.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

# A 1x1 grey PNG. The media proxy only forwards Shopify's own CDN hosts, so a fixture image
# has to be a data: URI or it is dropped on the way to the tablet — correctly, and that
# dropping is itself tested. Nothing here is fetched over the network.
PLACEHOLDER_IMAGE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

SHOP_TIMEZONE = "Europe/London"
SHOP_TZ = ZoneInfo(SHOP_TIMEZONE)
CURRENCY = "GBP"

# The clock the world is built against, fixed once per process — and kept in the SHOP's zone,
# not UTC. A shopkeeper asking for "today's orders" means the shop's day, and the application
# agrees: it asks Shopify for the local day's bounds. Stamping the fixtures in UTC instead put
# every order in the wrong day for the hour either side of midnight UTC, which is a fixture
# that passes all day and fails at eleven at night.
NOW = datetime.now(SHOP_TZ)


def _local(days_ago: float, hour: int, minute: int = 0) -> datetime:
    """The instant `days_ago` shop-local days back, at a shop-local time of day."""
    return (NOW - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=0, microsecond=0)


def _at(days_ago: float, hour: int = 10, minute: int = 0) -> str:
    """A stamp `days_ago` days back, in Shopify's format, which is always UTC."""
    return _local(days_ago, hour, minute).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ms(days_ago: float, hour: int = 10, minute: int = 0) -> str:
    """The same instant as Gmail's internalDate: milliseconds since the epoch, as a string."""
    return str(int(_local(days_ago, hour, minute).timestamp() * 1000))


def _rfc2822(days_ago: float, hour: int = 10, minute: int = 0) -> str:
    return _local(days_ago, hour, minute).strftime("%a, %d %b %Y %H:%M:%S %z")


def _money(amount: str) -> dict[str, Any]:
    return {"shopMoney": {"amount": amount, "currencyCode": CURRENCY}}


# --------------------------------------------------------------------------- the catalogue

PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "gid://shopify/Product/9001",
        "title": "Convict Hoodie",
        "productType": "Hoodies",
        "status": "ACTIVE",
        "totalInventory": 26,
        "featuredImage": {"url": PLACEHOLDER_IMAGE, "width": 320, "height": 320},
        "variants": [
            {"id": "gid://shopify/ProductVariant/9101", "title": "Black / S", "sku": "CRK-HOOD-BLK-S", "price": "60.00",
             "inventoryQuantity": 2, "options": [("Colour", "Black"), ("Size", "S")]},
            {"id": "gid://shopify/ProductVariant/9102", "title": "Black / M", "sku": "CRK-HOOD-BLK-M", "price": "60.00",
             "inventoryQuantity": 4, "options": [("Colour", "Black"), ("Size", "M")]},
            {"id": "gid://shopify/ProductVariant/9103", "title": "Black / L", "sku": "CRK-HOOD-BLK-L", "price": "60.00",
             "inventoryQuantity": 11, "options": [("Colour", "Black"), ("Size", "L")]},
            {"id": "gid://shopify/ProductVariant/9104", "title": "Bone / M", "sku": "CRK-HOOD-BON-M", "price": "60.00",
             "inventoryQuantity": 9, "options": [("Colour", "Bone"), ("Size", "M")]},
        ],
    },
    {
        "id": "gid://shopify/Product/9002",
        "title": "Yard Jeans",
        "productType": "Denim",
        "status": "ACTIVE",
        "totalInventory": 13,
        "featuredImage": {"url": PLACEHOLDER_IMAGE, "width": 320, "height": 320},
        "variants": [
            {"id": "gid://shopify/ProductVariant/9201", "title": "Indigo / 30", "sku": "CRK-JEAN-IND-30", "price": "24.00",
             "inventoryQuantity": 0, "options": [("Colour", "Indigo"), ("Size", "30")]},
            {"id": "gid://shopify/ProductVariant/9202", "title": "Indigo / 32", "sku": "CRK-JEAN-IND-32", "price": "24.00",
             "inventoryQuantity": 9, "options": [("Colour", "Indigo"), ("Size", "32")]},
            {"id": "gid://shopify/ProductVariant/9203", "title": "Blue Wash / 32", "sku": "CRK-JEAN-BLW-32", "price": "26.00",
             "inventoryQuantity": 4, "options": [("Colour", "Blue Wash"), ("Size", "32")]},
        ],
    },
    {
        "id": "gid://shopify/Product/9003",
        "title": "Crooks Cap",
        "productType": "Headwear",
        "status": "ACTIVE",
        "totalInventory": 31,
        "featuredImage": {"url": PLACEHOLDER_IMAGE, "width": 320, "height": 320},
        "variants": [
            {"id": "gid://shopify/ProductVariant/9301", "title": "Black / One size", "sku": "CRK-CAP-BLK", "price": "18.00",
             "inventoryQuantity": 31, "options": [("Colour", "Black"), ("Size", "One size")]},
        ],
    },
]

VARIANTS: dict[str, dict[str, Any]] = {}
for _product in PRODUCTS:
    for _variant in _product["variants"]:
        VARIANTS[_variant["id"]] = {**_variant, "product": _product}


# --------------------------------------------------------------------------- the people

@dataclass(frozen=True)
class Person:
    customer_id: str
    name: str
    email: str
    since_days: int
    orders: int
    spent: str


MIA = Person("gid://shopify/Customer/7001", "Mia Jones", "mia.jones@example.com", 420, 3, "213.00")
DAVID = Person("gid://shopify/Customer/7002", "David Randall", "david.randall@example.com", 200, 2, "104.00")
MILLIE = Person("gid://shopify/Customer/7003", "Millie Fenwick", "millie.fenwick@example.com", 95, 1, "84.00")
# Writes in from an address that is not the one on her order: the cross-thread correlation case.
PRIYA = Person("gid://shopify/Customer/7004", "Priya Raman", "priya.raman@example.com", 60, 1, "18.00")
PEOPLE = {p.customer_id: p for p in (MIA, DAVID, MILLIE, PRIYA)}

# Not a customer. Exists so "who needs replying to" has something it must not offer.
NEWSLETTER_SENDER = "no-reply@shipping-updates.example.net"


def _customer_node(person: Person) -> dict[str, Any]:
    return {
        "id": person.customer_id,
        "displayName": person.name,
        "numberOfOrders": str(person.orders),
        "createdAt": _at(person.since_days),
        "amountSpent": {"amount": person.spent, "currencyCode": CURRENCY},
        "defaultEmailAddress": {"emailAddress": person.email},
    }


# --------------------------------------------------------------------------- the orders

@dataclass
class OrderSpec:
    number: int
    person: Person
    days_ago: float
    hour: int
    total: str
    fulfillment: str                  # UNFULFILLED / FULFILLED / PARTIALLY_FULFILLED
    financial: str                    # PAID / REFUNDED / VOIDED
    items: list[tuple[str, int]]      # (variant id, quantity)
    address: dict[str, Any]
    tracking: str = ""
    carrier: str = ""
    cancelled_days_ago: float | None = None
    cancel_reason: str = ""
    note: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def order_id(self) -> str:
        return f"gid://shopify/Order/{self.number}"

    @property
    def name(self) -> str:
        return f"#{self.number}"


_WINDSOR = {"name": "Mia Jones", "firstName": "Mia", "lastName": "Jones", "address1": "12 Bridge Street", "address2": "", "city": "Windsor",
            "provinceCode": "", "zip": "SL4 1QN", "country": "United Kingdom", "countryCodeV2": "GB",
            "phone": "", "company": ""}
_LEEDS = {"name": "David Randall", "firstName": "David", "lastName": "Randall", "address1": "4 Kirkgate", "address2": "Flat 2", "city": "Leeds",
          "provinceCode": "", "zip": "LS1 6BY", "country": "United Kingdom", "countryCodeV2": "GB",
          "phone": "", "company": ""}
# Deliberately missing its house number: the "did anyone email us their house number" scenario
# turns on the inbox supplying what the order does not.
_BRISTOL_NO_NUMBER = {"name": "Millie Fenwick", "firstName": "Millie", "lastName": "Fenwick", "address1": "Sefton Park Road", "address2": "", "city": "Bristol",
                      "provinceCode": "", "zip": "BS7 9AL", "country": "United Kingdom", "countryCodeV2": "GB",
                      "phone": "", "company": ""}
_MANCHESTER = {"name": "Priya Raman", "firstName": "Priya", "lastName": "Raman", "address1": "88 Oldham Road", "address2": "", "city": "Manchester",
               "provinceCode": "", "zip": "M4 5EG", "country": "United Kingdom", "countryCodeV2": "GB",
               "phone": "", "company": ""}

ORDERS: list[OrderSpec] = [
    # Today. The scenario order: multi-item, unfulfilled, a customer with history.
    OrderSpec(1938, MIA, 0, 9, "84.00", "UNFULFILLED", "PAID",
              [("gid://shopify/ProductVariant/9102", 1), ("gid://shopify/ProductVariant/9202", 1)],
              _WINDSOR, note="", tags=["vip"]),
    # Today. Single item, unfulfilled — the second row of "today's orders".
    OrderSpec(1940, PRIYA, 0, 11, "18.00", "UNFULFILLED", "PAID",
              [("gid://shopify/ProductVariant/9301", 1)], _MANCHESTER),
    # Today. Fulfilled and tracked, so "today's orders" is not uniformly unfulfilled.
    OrderSpec(1939, DAVID, 0, 8, "60.00", "FULFILLED", "PAID",
              [("gid://shopify/ProductVariant/9103", 1)], _LEEDS,
              tracking="AB1234567890GB", carrier="Royal Mail"),
    # Four days ago, fulfilled but never tracked: the untracked case.
    OrderSpec(1936, MILLIE, 4, 14, "84.00", "FULFILLED", "PAID",
              [("gid://shopify/ProductVariant/9104", 1), ("gid://shopify/ProductVariant/9203", 1)],
              _BRISTOL_NO_NUMBER),
    # Twelve days ago, cancelled and refunded.
    OrderSpec(1929, DAVID, 12, 16, "44.00", "UNFULFILLED", "REFUNDED",
              [("gid://shopify/ProductVariant/9201", 1), ("gid://shopify/ProductVariant/9301", 1)],
              _LEEDS, cancelled_days_ago=11, cancel_reason="CUSTOMER"),
    # Mia's history: two older orders, so "what else has she ordered" has an answer.
    OrderSpec(1912, MIA, 45, 12, "60.00", "FULFILLED", "PAID",
              [("gid://shopify/ProductVariant/9101", 1)], _WINDSOR,
              tracking="CD2233445566GB", carrier="Royal Mail"),
    OrderSpec(1876, MIA, 120, 10, "69.00", "FULFILLED", "PAID",
              [("gid://shopify/ProductVariant/9301", 1), ("gid://shopify/ProductVariant/9203", 1)],
              _WINDSOR, tracking="EF3344556677GB", carrier="Royal Mail"),
]

BY_ID = {o.order_id: o for o in ORDERS}
BY_NAME = {o.name: o for o in ORDERS}

# The order every "show me order N" scenario asks for.
SCENARIO_ORDER = BY_NAME["#1938"]


def line_item_node(index: int, variant_id: str, quantity: int, *, fulfilled: bool) -> dict[str, Any]:
    variant = VARIANTS[variant_id]
    product = variant["product"]
    total = f"{float(variant['price']) * quantity:.2f}"
    return {
        "id": f"gid://shopify/LineItem/{index}",
        "title": product["title"],
        "quantity": quantity,
        "currentQuantity": quantity,
        "refundableQuantity": 0 if fulfilled else quantity,
        "unfulfilledQuantity": 0 if fulfilled else quantity,
        "variantTitle": variant["title"],
        "sku": variant["sku"],
        "originalTotalSet": _money(total),
        "discountedTotalSet": _money(total),
        "image": {"url": PLACEHOLDER_IMAGE, "width": 320, "height": 320},
        "variant": {
            "id": variant["id"],
            "inventoryQuantity": variant["inventoryQuantity"],
            "inventoryItem": {"id": variant["id"].replace("ProductVariant", "InventoryItem"), "tracked": True},
            "selectedOptions": [{"name": n, "value": v} for n, v in variant["options"]],
        },
        "product": {"id": product["id"], "title": product["title"], "productType": product["productType"]},
    }


def order_node(spec: OrderSpec) -> dict[str, Any]:
    """One order in Shopify's own shape. Every read in the application is shaped from this."""
    fulfilled = spec.fulfillment == "FULFILLED"
    items = [
        line_item_node(1000 + spec.number * 10 + i, variant_id, quantity, fulfilled=fulfilled)
        for i, (variant_id, quantity) in enumerate(spec.items)
    ]
    subtotal = sum(float(VARIANTS[v]["price"]) * q for v, q in spec.items)
    fulfillments: list[dict[str, Any]] = []
    if fulfilled:
        fulfillments = [{
            "id": f"gid://shopify/Fulfillment/{spec.number}",
            "status": "SUCCESS",
            "createdAt": _at(max(0.0, spec.days_ago - 1), 15),
            "trackingInfo": ([{"number": spec.tracking, "company": spec.carrier,
                               "url": f"https://track.example/{spec.tracking}"}] if spec.tracking else []),
        }]
    return {
        "id": spec.order_id,
        "name": spec.name,
        "createdAt": _at(spec.days_ago, spec.hour),
        "processedAt": _at(spec.days_ago, spec.hour),
        "updatedAt": _at(max(0.0, spec.days_ago - 1), spec.hour),
        "cancelledAt": _at(spec.cancelled_days_ago, 9) if spec.cancelled_days_ago is not None else None,
        "cancelReason": spec.cancel_reason or None,
        "closedAt": None,
        "displayFulfillmentStatus": spec.fulfillment,
        "displayFinancialStatus": spec.financial,
        "tags": list(spec.tags),
        "note": spec.note,
        "email": spec.person.email,
        "currentTotalPriceSet": _money(spec.total),
        "totalPriceSet": _money(spec.total),
        "subtotalPriceSet": _money(f"{subtotal:.2f}"),
        "totalShippingPriceSet": _money("5.00"),
        "totalTaxSet": _money("0.00"),
        "totalRefundedSet": _money(spec.total if spec.financial == "REFUNDED" else "0.00"),
        "totalOutstandingSet": _money("0.00"),
        "customer": _customer_node(spec.person),
        "shippingAddress": dict(spec.address),
        "billingAddress": dict(spec.address),
        "shippingLine": {"title": "Royal Mail Tracked 48"},
        "fulfillments": fulfillments,
        "refunds": ([{"id": f"gid://shopify/Refund/{spec.number}", "createdAt": _at(11, 9),
                      "totalRefundedSet": _money(spec.total)}] if spec.financial == "REFUNDED" else []),
        "lineItems": {"pageInfo": {"hasNextPage": False}, "edges": [{"node": n} for n in items]},
    }


# --------------------------------------------------------------------------- the inbox

MAILBOX = "orders@crooksldn.example"


@dataclass
class Message:
    message_id: str
    thread_id: str
    sender: str                 # "Name <addr>"
    to: str
    subject: str
    body: str
    days_ago: float
    hour: int
    labels: list[str]

    @property
    def outbound(self) -> bool:
        return "SENT" in self.labels


@dataclass
class Thread:
    thread_id: str
    messages: list[Message]
    # The order this thread is really about, when it is about one. The correlation the
    # application derives is checked against this, never seeded from it.
    about_order: str = ""


def _msg(mid: str, tid: str, sender: str, subject: str, body: str, days_ago: float, hour: int,
         labels: list[str] | None = None, to: str = MAILBOX) -> Message:
    return Message(mid, tid, sender, to, subject, body, days_ago, hour, labels or ["INBOX", "UNREAD"])


THREADS: list[Thread] = [
    # 1. Inbound, unanswered, about a live order. The needs-reply case.
    Thread("t_mia_1938", [
        _msg("m1", "t_mia_1938", f"Mia Jones <{MIA.email}>", "Order 1938 — can I add to it?",
             "Hi, I have just placed order 1938. Is it too late to add a cap to it? Thanks, Mia.",
             0, 12),
    ], about_order="#1938"),

    # 2. Inbound then our reply: answered, so it must NOT appear in needs-reply.
    Thread("t_david_1939", [
        _msg("m2", "t_david_1939", f"David Randall <{DAVID.email}>", "Where is 1939?",
             "Morning — any tracking for order 1939 yet?", 1, 9),
        _msg("m3", "t_david_1939", f"CROOKS <{MAILBOX}>", "Re: Where is 1939?",
             "Hi David, 1939 went out with Royal Mail, tracking AB1234567890GB. CROOKS",
             1, 11, labels=["SENT"], to=DAVID.email),
    ], about_order="#1939"),

    # 3. The house number. Millie's order has a street but no number; she sent it by email,
    #    in a thread that never mentions the order number.
    Thread("t_millie_address", [
        _msg("m4", "t_millie_address", f"Millie Fenwick <{MILLIE.email}>", "Delivery address",
             "Sorry — I think I left the house number off. It is 41 Sefton Park Road, Bristol BS7 9AL.",
             3, 16),
    ], about_order=""),

    # 4. A reply that arrived in its own thread rather than on the original: the cross-thread
    #    correlation case. Priya's order is 1940; this thread names it only in the body.
    Thread("t_priya_separate", [
        _msg("m5", "t_priya_separate", f"Priya Raman <{PRIYA.email}>", "Cap",
             "Following up on my order 1940 — is the black cap the adjustable one?", 0, 13),
    ], about_order="#1940"),

    # 5. A notification. Not a customer, must never be offered as needing a reply.
    Thread("t_notification", [
        _msg("m6", "t_notification", f"Shipping Updates <{NEWSLETTER_SENDER}>",
             "Your weekly carrier report is ready",
             "This is an automated message. Do not reply. View your report online.",
             0, 6, labels=["INBOX", "UNREAD", "CATEGORY_UPDATES"]),
    ]),

    # 6. An older answered thread, for a customer's email history.
    Thread("t_mia_1912", [
        _msg("m7", "t_mia_1912", f"Mia Jones <{MIA.email}>", "Order 1912 arrived",
             "Got it, thank you — the hoodie fits perfectly.", 40, 10, labels=["INBOX"]),
        _msg("m8", "t_mia_1912", f"CROOKS <{MAILBOX}>", "Re: Order 1912 arrived",
             "Glad to hear it, Mia. CROOKS", 40, 15, labels=["SENT"], to=MIA.email),
    ], about_order="#1912"),
]

BY_THREAD = {t.thread_id: t for t in THREADS}

# A draft sitting in the mailbox, so the draft surface has something real to open.
DRAFTS = [{
    "draft_id": "d_mia_1938",
    "message_id": "m_draft_1",
    "thread_id": "t_mia_1938",
    "to": MIA.email,
    "subject": "Re: Order 1938 — can I add to it?",
    "body": "Hi Mia, I have added the cap to 1938 and it will go out today. CROOKS",
}]


def gmail_message_payload(message: Message) -> dict[str, Any]:
    """A message as the Gmail API returns it, body included."""
    encoded = base64.urlsafe_b64encode(message.body.encode("utf-8")).decode("ascii").rstrip("=")
    return {
        "id": message.message_id,
        "threadId": message.thread_id,
        "labelIds": list(message.labels),
        "internalDate": _ms(message.days_ago, message.hour),
        "snippet": message.body[:120],
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": message.sender},
                {"name": "To", "value": message.to},
                {"name": "Subject", "value": message.subject},
                {"name": "Date", "value": _rfc2822(message.days_ago, message.hour)},
                {"name": "Message-ID", "value": f"<{message.message_id}@example>"},
            ],
            "body": {"data": encoded, "size": len(message.body)},
        },
    }


# --------------------------------------------------------------------------- the whole thing

@dataclass(frozen=True)
class World:
    """What a scenario asserts against. Read-only, and the same in every process."""

    orders: list[OrderSpec]
    people: dict[str, Person]
    threads: list[Thread]
    products: list[dict[str, Any]]
    mailbox: str = MAILBOX
    timezone: str = SHOP_TIMEZONE
    currency: str = CURRENCY

    def order(self, name: str) -> OrderSpec:
        return BY_NAME[name if name.startswith("#") else f"#{name}"]

    def today(self) -> list[OrderSpec]:
        """The orders a question about today should find, newest first. `days_ago == 0` is the
        shop's current local day by construction, which is the same day the application asks
        Shopify for."""
        return sorted([o for o in self.orders if o.days_ago == 0], key=lambda o: o.hour, reverse=True)

    def orders_of(self, person: Person) -> list[OrderSpec]:
        return sorted([o for o in self.orders if o.person is person], key=lambda o: o.days_ago)

    def threads_of(self, person: Person) -> list[Thread]:
        return [t for t in self.threads if any(person.email in m.sender for m in t.messages)]

    def needs_reply(self) -> list[Thread]:
        """Threads whose last message came in and was never answered, from a real customer."""
        out = []
        for thread in self.threads:
            last = max(thread.messages, key=lambda m: (-m.days_ago, m.hour))
            if last.outbound:
                continue
            if not any(p.email in last.sender for p in self.people.values()):
                continue
            out.append(thread)
        return out


world = World(orders=ORDERS, people=PEOPLE, threads=THREADS, products=PRODUCTS)
