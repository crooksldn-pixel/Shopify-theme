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


class ShopifyThrottled(ShopifyError):
    """The query cost bucket was short. Carries how long Shopify said it takes to refill."""

    def __init__(self, message: str, wait_s: float = 0.5) -> None:
        super().__init__(message)
        self.wait_s = wait_s


class ShopifyPreconditionFailed(ShopifyError):
    """Shopify refused a change because the entity was not as the sender assumed — a
    compare-and-swap that found another quantity, an order that cannot be cancelled as it
    stands. Nothing was applied, and the sender's picture of the entity is out of date."""


# The user-error codes that mean "the entity is not as you thought", across payloads.
PRECONDITION_CODES = frozenset({
    "CHANGE_FROM_QUANTITY_STALE", "COMPARE_QUANTITY_STALE", "ORDER_NOT_CANCELLABLE", "ALREADY_CANCELLED",
    "ORDER_ALREADY_CANCELLED", "NOT_CANCELLABLE", "INVALID_FULFILLMENT_ORDER", "FULFILLMENT_ORDER_NOT_FOUND",
})


class ShopifyScopeRefused(ShopifyError):
    """Shopify refused a mutation for want of a scope, and said so in the response. Proof that
    nothing was applied — which is what makes one retry with a freshly minted token safe. No
    other failure means this: a 5xx whose body happens to mention the words does not."""


@dataclass(slots=True)
class _Token:
    value: str
    expires_at: float
    expires_in: int

    @property
    def fresh(self) -> bool:
        return time.time() < self.expires_at - TOKEN_REFRESH_MARGIN_S


# ------------------------------------------------------------ reviewed writes
#
# The assistant sends no mutation it did not ship with. `graphql()` refuses any mutation
# document outright; the only way to change anything is `mutate()`, which takes a NAME from
# this table — a reviewed document with a fixed, bounded variable set — and never a document.
# A future action adds its own entry here, individually, with its own review. Nothing here is
# built from a caller's string.


@dataclass(frozen=True, slots=True)
class ReviewedMutation:
    name: str
    document: str
    # The exact variable names the document takes, and the Python type each must have.
    variables: dict[str, type]
    # The Admin API access scope the shop must have granted for this to work.
    scope: str
    # Longest string any variable may carry. Shopify's own limit on an order note is 5000.
    max_chars: int = 5000
    # Whether sending it twice with the same variables leaves the same state (setting a note
    # to a value: yes; a refund, a cancel, an adjustment by a delta: no). Only an idempotent
    # mutation is ever sent a second time, and then only after a proven scope refusal.
    idempotent: bool = False
    # The payload's root field, so a refusal can be told from a redaction: a root that came
    # back null was refused; a root that came back with a redacted field inside it ran.
    root: str = ""
    # For a mutation that takes a nested input object: validate(variable name, value) walks it
    # against the reviewed shape — known keys, enum values, numeric bounds — and refuses the
    # rest. A nested input is never sent on the strength of the top-level check alone.
    validate: Any = None


REVIEWED_MUTATIONS: dict[str, ReviewedMutation] = {
    # Phase 1: the order note. `orderUpdate` overwrites the note, which is why the desired
    # value is built on the Mac from a fresh read and checked against it again before sending.
    "order_note_set": ReviewedMutation(
        name="order_note_set",
        document="""
            mutation CrooksOrderNoteSet($id: ID!, $note: String!) {
              orderUpdate(input: {id: $id, note: $note}) {
                order { id name note }
                userErrors { field message }
              }
            }
        """,
        variables={"id": str, "note": str},
        scope="write_orders",
        idempotent=True,
        root="orderUpdate",
    ),
    # Tags. tagsAdd and tagsRemove are set operations: sending either twice leaves the same
    # tags, so both may be retried after a proven scope refusal.
    "order_tags_add": ReviewedMutation(
        name="order_tags_add",
        document="""
            mutation CrooksOrderTagsAdd($id: ID!, $tags: [String!]!) {
              tagsAdd(id: $id, tags: $tags) {
                node { id }
                userErrors { field message }
              }
            }
        """,
        variables={"id": str, "tags": list},
        scope="write_orders",
        max_chars=40,
        idempotent=True,
        root="tagsAdd",
    ),
    "order_tags_remove": ReviewedMutation(
        name="order_tags_remove",
        document="""
            mutation CrooksOrderTagsRemove($id: ID!, $tags: [String!]!) {
              tagsRemove(id: $id, tags: $tags) {
                node { id }
                userErrors { field message }
              }
            }
        """,
        variables={"id": str, "tags": list},
        scope="write_orders",
        max_chars=40,
        idempotent=True,
        root="tagsRemove",
    ),
}

KEEPALIVE_CONNECTIONS = 4
KEEPALIVE_EXPIRY_S = 120.0
# When Shopify says the query cost bucket is short, a read waits this long at most for it
# to refill, once, before being reported as throttled.
THROTTLE_WAIT_MAX_S = 1.5

SCOPES_TTL_S = 600.0
# How long a failed scope check is remembered as failed, so a Shopify that is not answering
# is not asked again on every turn and every tap.
SCOPES_FAILED_TTL_S = 30.0


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
        # One HTTPS connection, kept open between calls. A TLS handshake to Shopify costs a
        # few hundred milliseconds; a question that makes two lookups was paying it twice.
        self._http: httpx.AsyncClient | None = None
        self.mutations_sent = 0   # every reviewed mutation this process has sent
        self._scopes: frozenset[str] | None = None
        self._scopes_at = 0.0
        self._scopes_failed_at = 0.0
        # What the last answer said about the query cost bucket: requested, actual, and how
        # much is left. For the timings, and for waiting rather than failing when it is short.
        self.last_cost: dict[str, float] = {}

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            # Kept warm for minutes, not httpx's five seconds: the order, the customer's
            # history and the scope check go out together and must not each open a socket.
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(max_keepalive_connections=KEEPALIVE_CONNECTIONS, keepalive_expiry=KEEPALIVE_EXPIRY_S),
            )
        return self._http

    async def aclose(self) -> None:
        if self._http is not None and not self._http.is_closed:
            await self._http.aclose()
        self._http = None

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
                response = await self._client().post(
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
        # Reads only, enforced HERE and not only by the scope list the owner types into a
        # console. A document whose operation is a mutation never leaves this process by this
        # path; the reviewed writes go through `mutate()`, by name.
        if _is_mutation(query):
            raise ShopifyError("Refused: this path never sends a Shopify mutation.")
        try:
            return await self._post(query, variables)
        except ShopifyThrottled as exc:
            # The bucket was short. A read is safe to send again: wait for the refill Shopify
            # itself described (bounded), then once more. A mutation never takes this path.
            wait = min(max(exc.wait_s, 0.2), THROTTLE_WAIT_MAX_S)
            log.info("Shopify throttled a read; waiting %.1fs once", wait)
            await asyncio.sleep(wait)
            return await self._post(query, variables)

    async def mutate(self, name: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Send one reviewed mutation by name. The document comes from REVIEWED_MUTATIONS,
        the variables must be exactly the set it declares, and every string is bounded. There
        is no way to pass a document in."""
        reviewed = REVIEWED_MUTATIONS.get(name)
        if reviewed is None:
            raise ShopifyError(f"Refused: {name!r} is not a reviewed mutation.")
        if not isinstance(variables, dict) or set(variables) != set(reviewed.variables):
            raise ShopifyError(f"Refused: {name} variables do not match the reviewed set.")
        for key, kind in reviewed.variables.items():
            value = variables[key]
            if not isinstance(value, kind) or isinstance(value, bool) and kind is not bool:
                raise ShopifyError(f"Refused: {name}.{key} has the wrong type.")
            if isinstance(value, str) and (not value.strip() if key == "id" else len(value) > reviewed.max_chars):
                raise ShopifyError(f"Refused: {name}.{key} is out of bounds.")
            if isinstance(value, list):
                # A list carries strings only, each bounded, and not too many of them.
                if not value or len(value) > 20 or any(not isinstance(v, str) or not v.strip() or len(v) > reviewed.max_chars for v in value):
                    raise ShopifyError(f"Refused: {name}.{key} is out of bounds.")
            if isinstance(value, dict) and reviewed.validate is not None and not reviewed.validate(key, value):
                raise ShopifyError(f"Refused: {name}.{key} does not match the reviewed shape.")
        self.mutations_sent += 1
        log.info("mutation %s sent", name)
        try:
            return await self._post(reviewed.document, variables, mutation=True, root=reviewed.root)
        except ShopifyScopeRefused:
            if self.auth_mode == "static_token" or self._token is None or not reviewed.idempotent:
                # Never a second send of a change that could apply twice. The scope refusal
                # is reported; the owner grants the scope and asks again.
                raise
            # A client-credentials token lives a day and carries the scopes granted when it was
            # minted. The store granted write_orders after that: one fresh token, one retry —
            # for a mutation that leaves the same state however many times it is sent, and
            # only after a refusal that proved nothing ran (the root came back null).
            log.warning("mutation %s refused for scope; re-minting the token once", name)
            self._token = None
            self._scopes = None
            self.mutations_sent += 1
            return await self._post(reviewed.document, variables, mutation=True, root=reviewed.root)

    async def access_scopes(self, *, refresh: bool = False) -> frozenset[str]:
        """What the store has granted this app. A read, cached briefly: the write preflight
        asks on every health poll and must not cost a query each time."""
        if self._scopes is not None and not refresh and time.time() - self._scopes_at < SCOPES_TTL_S:
            return self._scopes
        if not refresh and time.time() - self._scopes_failed_at < SCOPES_FAILED_TTL_S:
            # It did not answer a moment ago. Asking again on every turn and every tap would
            # spend the preflight's whole bound each time, and the caller treats a scope check
            # it cannot make as "unknown" — which is applicable, with Shopify deciding the tap.
            raise ShopifyError("the scope check failed a moment ago")
        try:
            payload = await self.graphql(
                "query CrooksScopes { currentAppInstallation { accessScopes { handle } } }"
            )
        except Exception:
            self._scopes_failed_at = time.time()
            raise
        installation = (payload.get("data") or {}).get("currentAppInstallation") or {}
        self._scopes = frozenset(
            str(s.get("handle", "")) for s in installation.get("accessScopes") or [] if isinstance(s, dict)
        )
        self._scopes_at = time.time()
        self._scopes_failed_at = 0.0
        return self._scopes

    async def _post(self, query: str, variables: dict[str, Any] | None = None, *, mutation: bool = False, root: str = "") -> dict[str, Any]:
        token = await self._access_token()
        try:
            response = await self._client().post(
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
            raise ShopifyThrottled("Shopify is rate-limiting us. Try again in a moment.", wait_s=_retry_after(response))
        if response.status_code != 200:
            raise ShopifyError(f"Shopify returned {response.status_code}: {response.text[:200]}")

        payload = response.json()
        self.last_cost = _cost_of(payload)

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
                raise ShopifyThrottled("Shopify is rate-limiting us. Try again in a moment.", wait_s=_refill_wait(self.last_cost))
            if "MAX_COST_EXCEEDED" in codes:
                raise ShopifyError("That query was too expensive for Shopify; narrow it.")
            data = payload.get("data")
            root_value = (data or {}).get(root) if isinstance(data, dict) and root else None
            if mutation and "ACCESS_DENIED" in codes and (data is None or (root and root_value is None)):
                # For a read, ACCESS_DENIED is protected customer data coming back redacted and
                # the rest of the answer stands. For a mutation it is a refusal ONLY when the
                # mutation's own root came back null: a root that came back, with a redacted
                # field inside it, is a change that RAN. This type is raised for the refusal
                # alone — it is what permits a second send, and a second send of a change
                # that ran would be a second change.
                raise ShopifyScopeRefused(f"Shopify refused the change (ACCESS_DENIED): {messages[:160]}")
            if data is None:
                raise ShopifyError(f"Shopify rejected the query: {messages}")
            log.warning("Shopify partial errors (likely protected-data redaction): %s", messages)
            payload.setdefault("_partial_errors", messages)
            self.last_partial_errors = messages

        user_errors = _collect_user_errors(payload.get("data") or {})
        if user_errors:
            codes = {str(e.get("code") or "").upper() for e in user_errors if isinstance(e, dict)}
            messages = "; ".join(str(e.get("message", e)) for e in user_errors)
            if codes & PRECONDITION_CODES:
                raise ShopifyPreconditionFailed(messages)
            raise ShopifyError(messages)

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
    """True if the document holds a mutation operation anywhere in it. Anonymous `{ ... }` and
    `query` documents are reads; `mutation Name(`, `mutation Name {`, `mutation {` and
    `mutation{` — first in the document or after another operation — are all writes, and this
    path never sends one."""
    return bool(_MUTATION_RE.match(document or "")) or bool(
        re.search(r"(?:^|[\s};])mutation\b\s*(?:\w+\s*)?[({]", document or "", re.I)
    )


def _cost_of(payload: dict[str, Any]) -> dict[str, float]:
    """The cost extension, as numbers: requested, actual, available, restore rate."""
    cost = (payload.get("extensions") or {}).get("cost") if isinstance(payload, dict) else None
    if not isinstance(cost, dict):
        return {}
    throttle = cost.get("throttleStatus") or {}
    out: dict[str, float] = {}
    for key, value in (
        ("requested", cost.get("requestedQueryCost")), ("actual", cost.get("actualQueryCost")),
        ("available", throttle.get("currentlyAvailable")), ("restore_rate", throttle.get("restoreRate")),
        ("maximum", throttle.get("maximumAvailable")),
    ):
        try:
            if value is not None:
                out[key] = float(value)
        except (TypeError, ValueError):
            pass
    return out


def _refill_wait(cost: dict[str, float]) -> float:
    """How long until the bucket holds what the last query asked for, by Shopify's own numbers."""
    requested, available, rate = cost.get("requested"), cost.get("available"), cost.get("restore_rate")
    if requested is None or available is None or not rate:
        return 0.5
    return max(0.0, (requested - available) / rate)


def _retry_after(response: httpx.Response) -> float:
    try:
        return float(response.headers.get("retry-after", "0.5"))
    except ValueError:
        return 0.5


def _iso_utc(dt: datetime) -> str:

    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_user_errors(node: Any, found: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Every user error in a payload, whatever the payload calls its list: `userErrors`,
    `orderCancelUserErrors`, `inventoryAdjustQuantitiesUserErrors` — any key ending in
    UserErrors. Each is a dict with at least a message, and a code when Shopify gave one."""
    found = found if found is not None else []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.endswith("UserErrors") or key == "userErrors":
                if isinstance(value, list):
                    found.extend(
                        {"message": str(e.get("message", e)), "code": e.get("code"), "field": e.get("field")}
                        for e in value if isinstance(e, dict)
                    )
            else:
                _collect_user_errors(value, found)
    elif isinstance(node, list):
        for item in node:
            _collect_user_errors(item, found)
    return found
