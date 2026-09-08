from __future__ import annotations

import pytest

from app.clients.shopify import ShopifyClient
from app.secrets import keychain


def shopify_configured() -> bool:
    try:
        return keychain.present("shopify_client_id") or keychain.present("shopify_static_token")
    except Exception:  # noqa: BLE001 — no keyring backend at all
        return False


def gmail_configured() -> bool:
    from app.clients.gmail import TOKEN_PATH

    if TOKEN_PATH.exists():
        return True
    try:
        return keychain.present("gmail_token")
    except Exception:  # noqa: BLE001
        return False


needs_shopify = pytest.mark.skipif(
    not shopify_configured(), reason="no Shopify credentials in the Keychain (M6 not done)"
)
needs_gmail = pytest.mark.skipif(
    not gmail_configured(), reason="no Gmail token.json (M8 not done)"
)


class FakeShopify(ShopifyClient):
    """A ShopifyClient that returns canned GraphQL payloads. Lets the tools' shaping logic —
    which is where the bugs live — be tested without a network or a store."""

    def __init__(self, responses: list[dict], timezone: str = "Europe/London") -> None:
        super().__init__("fake.myshopify.com", "2025-07")
        self._responses = list(responses)
        self.queries: list[tuple[str, dict]] = []
        self._shop = {
            "name": "CROOKS LDN", "myshopifyDomain": "fake.myshopify.com",
            "ianaTimezone": timezone, "currencyCode": "GBP",
        }
        from zoneinfo import ZoneInfo

        self._tz = ZoneInfo(timezone)

    async def graphql(self, query: str, variables: dict | None = None) -> dict:
        self.queries.append((query, variables or {}))
        if not self._responses:
            raise AssertionError("FakeShopify ran out of canned responses")
        return self._responses.pop(0)


@pytest.fixture()
def fake_shopify():
    return FakeShopify
