"""Shopify Admin GraphQL client.

Two auth modes. `client_credentials` exchanges the Dev Dashboard app's Client ID and secret for
a 24-hour token, forever, with no human in the loop — the intended path. `static_token` uses a
legacy `shpat_` Admin API token, which is the documented fallback for the one failure that has
no config fix: an app and a store in different Shopify organisations.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.secrets import keychain

log = logging.getLogger("crooks.shopify")

# Refresh a little before the hour is up rather than racing the expiry.
TOKEN_REFRESH_MARGIN_S = 300


class ShopifyAuthError(RuntimeError):
    """Authentication failed in a way that needs a human, not a retry."""


class ShopifyError(RuntimeError):
    """A query failed. Carries the message the assistant should read out."""


@dataclass(slots=True)
class _Token:
    value: str
    expires_at: float
    expires_in: int

    @property
    def fresh(self) -> bool:
        return time.time() < self.expires_at - TOKEN_REFRESH_MARGIN_S


class ShopifyClient:
    def __init__(
        self,
        shop_domain: str,
        api_version: str,
        *,
        auth_mode: str = "client_credentials",
        timeout_s: float = 15.0,
    ) -> None:
        self.shop_domain = shop_domain
        self.api_version = api_version
        self.auth_mode = auth_mode
        self._timeout = timeout_s
        self._token: _Token | None = None
        self._lock = asyncio.Lock()
        self._tz: ZoneInfo | None = None
        self._shop: dict[str, Any] | None = None
        self.token_requests = 0  # M6 asserts the second run reuses the cache
        self.last_partial_errors: str | None = None

    # ---------------------------------------------------------------- auth

    @property
    def graphql_url(self) -> str:
        return f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"

    async def _access_token(self) -> str:
        if self.auth_mode == "static_token":
            token = keychain.get_optional("shopify_static_token")
            if not token:
                raise ShopifyAuthError(
                    "auth_mode is static_token but no shopify_static_token is stored. "
                    "Run: python scripts/set_secrets.py shopify_static_token"
                )
            return token

        async with self._lock:
            if self._token and self._token.fresh:
                return self._token.value

            client_id = keychain.get("shopify_client_id")
            client_secret = keychain.get("shopify_client_secret")
            self.token_requests += 1

            url = f"https://{self.shop_domain}/admin/oauth/access_token"
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as http:
                    response = await http.post(
                        url,
                        json={
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "grant_type": "client_credentials",
                        },
                    )
            except httpx.HTTPError as exc:
                raise ShopifyAuthError(f"Could not reach Shopify to mint a token: {exc}") from exc

            if response.status_code != 200:
                body = response.text[:300]
                if "shop_not_permitted" in body:
                    raise ShopifyAuthError(
                        "shop_not_permitted — the app and the store are in different Shopify "
                        "organisations. This cannot be fixed in config and apps cannot be moved. "
                        "Either recreate the app in the store's organisation, or set "
                        "CROOKS_SHOPIFY_AUTH_MODE=static_token and store a legacy shpat_ token."
                    )
                raise ShopifyAuthError(
                    f"Token request failed ({response.status_code}): {body}. "
                    "Check the app version was released and installed on the store."
                )

            payload = response.json()
            expires_in = int(payload.get("expires_in", 86399))
            self._token = _Token(
                value=payload["access_token"],
                expires_at=time.time() + expires_in,
                expires_in=expires_in,
            )
            log.info("minted Shopify token, expires_in=%s", expires_in)
            return self._token.value

    @property
    def token_expires_in(self) -> int | None:
        return self._token.expires_in if self._token else None

    # ------------------------------------------------------------- graphql

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        # Read-only is enforced HERE, not only by the scope list the owner types into a console.
        # A document whose operation is a mutation never leaves this process.
        if _is_mutation(query):
            raise ShopifyError("Refused: this assistant never sends a Shopify mutation.")
        token = await self._access_token()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as http:
                response = await http.post(
                    self.graphql_url,
                    headers={
                        "X-Shopify-Access-Token": token,
                        "Content-Type": "application/json",
                    },
                    json={"query": query, "variables": variables or {}},
                )
        except httpx.HTTPError as exc:
            raise ShopifyError(f"Could not reach Shopify: {exc}") from exc

        if response.status_code == 401:
            self._token = None
            raise ShopifyAuthError("Shopify rejected the token (401). It may have been revoked.")
        if response.status_code == 429:
            raise ShopifyError("Shopify is rate-limiting us. Try again in a moment.")
        if response.status_code != 200:
            raise ShopifyError(f"Shopify returned {response.status_code}: {response.text[:200]}")

        payload = response.json()

        # A 200 with an `errors` array is normal for protected customer data: fields come back
        # null and the reason is in `errors`. Reading only `data` makes that look like an outage.
        errors = payload.get("errors")
        self.last_partial_errors = None
        if errors:
            messages = "; ".join(
                str(e.get("message", e)) for e in errors if isinstance(e, dict)
            ) or str(errors)
            codes = {
                str((e.get("extensions") or {}).get("code", "")).upper()
                for e in errors if isinstance(e, dict)
            }
            # Throttling and cost overruns come back as HTTP 200 with an errors array, not 429.
            if "THROTTLED" in codes:
                raise ShopifyError("Shopify is rate-limiting us. Try again in a moment.")
            if "MAX_COST_EXCEEDED" in codes:
                raise ShopifyError("That query was too expensive for Shopify; narrow it.")
            if payload.get("data") is None:
                raise ShopifyError(f"Shopify rejected the query: {messages}")
            log.warning("Shopify partial errors (likely protected-data redaction): %s", messages)
            payload.setdefault("_partial_errors", messages)
            self.last_partial_errors = messages

        user_errors = _collect_user_errors(payload.get("data") or {})
        if user_errors:
            raise ShopifyError("; ".join(user_errors))

        return payload

    # ---------------------------------------------------------------- shop

    async def shop(self, *, refresh: bool = False) -> dict[str, Any]:
        if self._shop is not None and not refresh:
            return self._shop
        payload = await self.graphql(
            """
            query Shop {
              shop {
                name
                myshopifyDomain
                ianaTimezone
                currencyCode
                plan { publicDisplayName }
              }
            }
            """
        )
        self._shop = payload["data"]["shop"]
        self._tz = ZoneInfo(self._shop["ianaTimezone"])
        return self._shop

    async def timezone(self) -> ZoneInfo:
        """The shop's timezone, read from Shopify. Never hardcode the offset: it is correct all
        winter and an hour wrong all summer, which is the worst possible failure shape."""
        if self._tz is None:
            await self.shop()
        assert self._tz is not None
        return self._tz

    async def local_day_bounds(self, days_back: int = 0) -> tuple[str, str]:
        """UTC instants bracketing a shop-local day, as ISO-8601 for a Shopify search query."""
        tz = await self.timezone()
        now_local = datetime.now(tz)
        start_local = (now_local - timedelta(days=days_back)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_local = start_local + timedelta(days=1)
        return _iso_utc(start_local), _iso_utc(end_local)

    async def health(self) -> tuple[bool, str]:
        try:
            shop = await self.shop(refresh=True)
            return True, f"{shop['name']} ({shop['ianaTimezone']})"
        except (ShopifyAuthError, ShopifyError) as exc:
            return False, str(exc)
        except Exception as exc:  # noqa: BLE001
            return False, f"Shopify check failed: {exc}"


_MUTATION_RE = re.compile(r"^\s*(?:#[^\n]*\n\s*)*mutation\b", re.I)


def _is_mutation(document: str) -> bool:
    """True if the GraphQL document's operation is a mutation. Anonymous `{ ... }` and
    `query` documents are reads; anything starting with `mutation` is a write."""
    return bool(_MUTATION_RE.match(document or "")) or bool(
        re.search(r"\bmutation\s+\w*\s*[({]", document or "", re.I)
    )


def _iso_utc(dt: datetime) -> str:

    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_user_errors(node: Any, found: list[str] | None = None) -> list[str]:
    found = found if found is not None else []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "userErrors" and isinstance(value, list):
                found.extend(str(e.get("message", e)) for e in value if isinstance(e, dict))
            else:
                _collect_user_errors(value, found)
    elif isinstance(node, list):
        for item in node:
            _collect_user_errors(item, found)
    return found
