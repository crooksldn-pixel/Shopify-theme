"""The external shipping boundary (§20). Not integrated, and not pretending to be.

    app/shipping/provider.py   the seven questions, the context, and `checked`
    app/shipping/easyship.py   the Easyship adapter: DISCONNECTED, and says what is missing
    app/shipping/fixture.py    a provider made of fixture data, for tests and scenarios

Read `provider.py` first: one field there — `checked` — is the whole contract. The capability
state the owner sees is registered in app/families/shipping.py.
"""

from app.shipping.provider import (
    DISCONNECTED,
    NO_SHIPMENT,
    OK,
    UNAVAILABLE,
    ShippingContext,
    ShippingNotConnected,
    ShippingProvider,
    context_for,
    current,
    install,
    not_connected,
)

__all__ = [
    "DISCONNECTED", "NO_SHIPMENT", "OK", "UNAVAILABLE", "ShippingContext",
    "ShippingNotConnected", "ShippingProvider", "context_for", "current", "install",
    "not_connected",
]
