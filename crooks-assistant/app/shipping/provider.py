"""The shipping boundary: what any future provider answers, and what "not connected" means.

Easyship is NOT integrated (§20). There are no credentials on this machine and no client, and
this package does not pretend otherwise. What it does is fix the seven questions the tablet and
the anticipation layer want answered about an order's shipping, so that connecting a provider
later is writing one adapter rather than threading tracking state through the application:

    label exists?          `label_exists`
    shipment created?      `shipment_created`
    carrier                `carrier`
    tracking               `tracking`, `tracking_url`
    latest status          `status`, `status_at`
    shipping exception     `exception`
    label / document        `documents`, retrieved by reference through `document()`

One field carries the honesty rule and everything else in here defers to it: `checked` is True
ONLY when a provider was genuinely asked and genuinely answered. A context that was never asked
says so, names what is missing, and cannot be turned into a sentence that claims otherwise —
`said()` is the only way to render one, and it reads the flag. Nothing in the application may
say "checked Easyship" unless `checked` is True and `provider` names it, and that is a test
(tests/test_shipping.py), not a convention.

No mutation lives here, now or later. A label is BOUGHT through the action engine like any
other change — proposed, gestured, verified — and a provider adapter is a read interface plus a
document fetch. That is why this package has no `create_label`: the day one exists it will be a
`WriteSpec` in app/tools, not a method here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# What a provider's answer can be.
OK = "OK"                        # a provider answered about this order
NO_SHIPMENT = "NO_SHIPMENT"      # a provider answered: nothing has been created yet
DISCONNECTED = "DISCONNECTED"    # no provider is connected — nothing was checked
UNAVAILABLE = "UNAVAILABLE"      # a provider is connected and did not answer
STATES = (OK, NO_SHIPMENT, DISCONNECTED, UNAVAILABLE)


class ShippingNotConnected(RuntimeError):
    """Asked of a provider that has no credentials. Carries what is missing, by name."""

    def __init__(self, provider: str, missing: tuple[str, ...]) -> None:
        super().__init__(f"{provider} is not connected: {', '.join(missing) or 'no credentials'}")
        self.provider = provider
        self.missing = tuple(missing)


@dataclass(frozen=True)
class ShippingContext:
    """One order's shipping state, as some provider sees it — or as nobody does."""

    order_ref: str = ""
    state: str = DISCONNECTED
    # True only when a provider was asked AND answered. The whole honesty rule of §20.
    checked: bool = False
    provider: str = ""
    label_exists: bool | None = None
    shipment_created: bool | None = None
    carrier: str = ""
    tracking: str = ""
    tracking_url: str = ""
    status: str = ""
    status_at: float | None = None
    exception: str = ""
    # References only. A document is fetched through `document()` when the owner asks for it;
    # a speculative read never pulls a PDF.
    documents: tuple[str, ...] = ()
    # What would have to exist for this to be answerable, by name. Empty when it was answered.
    missing: tuple[str, ...] = ()
    detail: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def said(self) -> str:
        """The one sentence this context may be rendered as.

        A context that was never checked says that, and names what is missing. There is no
        branch here that can produce "checked Easyship" from `checked=False`, which is the
        point: the string and the flag cannot drift apart because there is only one string.
        """
        if not self.checked:
            missing = ", ".join(self.missing) or "no shipping provider is connected"
            return f"Shipping was not checked: {missing}."
        if self.state == NO_SHIPMENT:
            return f"{self.provider}: no shipment has been created for this order."
        if self.state == UNAVAILABLE:
            return f"{self.provider} did not answer{': ' + self.detail if self.detail else ''}."
        parts = [f"{self.provider}:"]
        parts.append(f"{self.carrier or 'a carrier'}" if self.shipment_created else "no shipment")
        if self.tracking:
            parts.append(f"tracking {self.tracking}")
        if self.status:
            parts.append(self.status)
        if self.exception:
            parts.append(f"exception: {self.exception}")
        return " ".join(parts).strip() + "."

    def public(self) -> dict[str, Any]:
        """For the tablet and the timeline. `checked` first, because it qualifies the rest."""
        return {
            "checked": self.checked, "provider": self.provider or None, "state": self.state,
            "label_exists": self.label_exists, "shipment_created": self.shipment_created,
            "carrier": self.carrier or None, "tracking": self.tracking or None,
            "tracking_url": self.tracking_url or None, "status": self.status or None,
            "status_at": self.status_at, "exception": self.exception or None,
            "documents": list(self.documents) or None,
            "missing": list(self.missing) or None, "detail": self.detail or None,
            "said": self.said(),
        }


def not_connected(order_ref: str, *, provider: str = "", missing: tuple[str, ...] = (), detail: str = "") -> ShippingContext:
    """The answer when nothing was asked. The only way to build a DISCONNECTED context, so
    `checked` cannot be set true on one by accident."""
    return ShippingContext(
        order_ref=str(order_ref or ""), state=DISCONNECTED, checked=False, provider="",
        missing=tuple(missing) or ("no shipping provider is connected",),
        detail=detail or (f"{provider} is not connected" if provider else "no shipping provider is connected"),
    )


@runtime_checkable
class ShippingProvider(Protocol):
    """What a shipping provider has to answer. Reads and one document fetch; no mutations."""

    name: str

    def connected(self) -> bool:
        """Whether this provider has everything it needs to be asked at all."""

    def missing(self) -> tuple[str, ...]:
        """What is missing, by name, when it is not connected."""

    async def shipment_for(self, order_ref: str) -> ShippingContext:
        """That order's shipping state. Raises ShippingNotConnected when it cannot be asked."""

    async def document(self, reference: str) -> bytes | None:
        """One label or customs document, by the reference a context carried. None when there
        is nothing to fetch."""


_current: ShippingProvider | None = None


def install(provider: ShippingProvider | None) -> ShippingProvider | None:
    global _current
    _current = provider
    return provider


def current() -> ShippingProvider | None:
    """The provider, or None. None is the state this build ships in."""
    return _current


async def context_for(order_ref: str) -> ShippingContext:
    """One order's shipping state from whatever is installed — never raising, never inventing.

    This is what the anticipation layer's internal shipping read calls. With no provider (the
    state of this build) it is a DISCONNECTED context and one dictionary; with a provider that
    fails it is UNAVAILABLE with the failure's type, which is still not a claim about the
    shipment.
    """
    provider = current()
    if provider is None:
        return not_connected(order_ref)
    if not provider.connected():
        return not_connected(order_ref, provider=getattr(provider, "name", "the shipping provider"), missing=tuple(provider.missing()))
    started = time.perf_counter()
    try:
        answered = await provider.shipment_for(order_ref)
    except ShippingNotConnected as exc:
        return not_connected(order_ref, provider=exc.provider, missing=exc.missing)
    except Exception as exc:  # noqa: BLE001 — a provider failing is a state, not a crash
        return ShippingContext(
            order_ref=str(order_ref or ""), state=UNAVAILABLE, checked=False,
            provider=getattr(provider, "name", ""), detail=type(exc).__name__,
            missing=("an answer from the shipping provider",),
        )
    if not isinstance(answered, ShippingContext):
        return not_connected(order_ref, provider=getattr(provider, "name", ""), missing=("a well-formed answer",))
    ms = (time.perf_counter() - started) * 1000
    return ShippingContext(**{**answered.__dict__, "extra": {**answered.extra, "ms": round(ms, 1)}})
