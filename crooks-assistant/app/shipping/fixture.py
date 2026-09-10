"""A shipping provider made of fixture data, so the boundary can be proven without a provider.

This is how the interface is tested and how a scenario exercises the shipping context: a
dictionary of order reference to shipment, answered from memory. It is `connected()` because it
genuinely is — it has everything it needs — and its answers carry `checked=True` and
`provider="fixture"`, which is the truth: a fixture was checked, not Easyship. Nothing in the
application may read a fixture answer as a live one, and nothing can: the provider's name
travels on the context.

The state it is bound in is chosen by the caller (experience/fixtures, a test). It is never
installed by the runtime — production installs nothing, and `context_for` answers DISCONNECTED.
"""

from __future__ import annotations

import time

from app.shipping.provider import NO_SHIPMENT, OK, ShippingContext


class FixtureShipping:
    """A provider whose world is a dict. Reads only."""

    name = "fixture"

    def __init__(self, shipments: dict[str, dict] | None = None, *, documents: dict[str, bytes] | None = None) -> None:
        self.shipments = dict(shipments or {})
        self.documents = dict(documents or {})
        self.asked: list[str] = []

    def connected(self) -> bool:
        return True

    def missing(self) -> tuple[str, ...]:
        return ()

    async def shipment_for(self, order_ref: str) -> ShippingContext:
        ref = str(order_ref or "")
        self.asked.append(ref)
        row = self.shipments.get(ref)
        if not row:
            return ShippingContext(
                order_ref=ref, state=NO_SHIPMENT, checked=True, provider=self.name,
                label_exists=False, shipment_created=False,
                detail="no shipment for this order in the fixture world",
            )
        return ShippingContext(
            order_ref=ref, state=OK, checked=True, provider=self.name,
            label_exists=bool(row.get("label_exists", bool(row.get("documents")))),
            shipment_created=bool(row.get("shipment_created", True)),
            carrier=str(row.get("carrier") or ""),
            tracking=str(row.get("tracking") or ""),
            tracking_url=str(row.get("tracking_url") or ""),
            status=str(row.get("status") or ""),
            status_at=float(row.get("status_at") or time.time()),
            exception=str(row.get("exception") or ""),
            documents=tuple(str(d) for d in (row.get("documents") or ())),
        )

    async def document(self, reference: str) -> bytes | None:
        return self.documents.get(str(reference))
