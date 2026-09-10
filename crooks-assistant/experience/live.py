"""Live read-only mode: the real shop and the real inbox, and no way to change either.

The fixture world proves the code is right. This proves the code is right about the shop the
owner actually has — real orders with real shapes, real threads that really do or do not
correlate, a catalogue with the sizes that really sell out. Those are the things a fixture
quietly gets wrong, and the things a screenshot is worth taking of.

The safety is not in this file being careful. It is in `app/readonly.py`, which latches the
process before a single client is built, and in the three places that latch is checked:

    ShopifyClient.mutate            every reviewed Shopify mutation
    GmailClient send/draft/modify   every Gmail change
    ActionEngine.commit             one layer up, so a refusal is a card and a ledger line

Those are a complete set rather than a remembered list: every write in the application goes
through one of them. On top of that the clients built here refuse a mutation on their own
account, so the latch would have to fail AND the wrapper would have to fail AND the engine
would have to fail before anything could be sent.

What this mode may do: read orders, read customers, read products and stock, read threads,
correlate them, build surfaces, and stage a proposal so the card can be looked at. What it
must never do is execute one — and staging is not executing: a proposal is an object on the
Mac until a gesture commits it, and commit is latched.
"""

from __future__ import annotations

import logging
from typing import Any

from app import readonly
from app.clients.gmail import GmailClient
from app.clients.shopify import ShopifyClient

log = logging.getLogger("crooks.experience.live")

REASON = "live read-only acceptance run"


class LiveWriteAttempted(AssertionError):
    """A live run reached a write. The latch refused it; this says so loudly enough to fail
    the run rather than be a line in a log nobody reads."""


class ReadOnlyShopify(ShopifyClient):
    """The real store, readable. `mutate` is gone rather than guarded — the method that could
    change the shop does not exist on this object in a usable form."""

    async def mutate(self, name: str, variables: dict[str, Any]) -> dict[str, Any]:
        raise LiveWriteAttempted(
            f"a live read-only run tried to execute the Shopify mutation {name!r}. "
            "Live scenarios read and propose; they never execute."
        )


class ReadOnlyGmail(GmailClient):
    """The real mailbox, readable. Every method that could change it refuses."""

    def create_draft(self, raw: str, thread_id: str | None) -> dict:
        raise LiveWriteAttempted("a live read-only run tried to create a Gmail draft")

    def delete_draft(self, draft_id: str) -> None:
        raise LiveWriteAttempted("a live read-only run tried to delete a Gmail draft")

    def send_message(self, raw: str, thread_id: str | None) -> dict:
        raise LiveWriteAttempted("a live read-only run tried to send a Gmail message")

    def send_draft(self, draft_id: str) -> dict:
        raise LiveWriteAttempted("a live read-only run tried to send a Gmail draft")

    def modify_thread(self, thread_id: str, *, add: list[str], remove: list[str]) -> None:
        raise LiveWriteAttempted("a live read-only run tried to relabel a Gmail thread")

    def store_token(self, payload: str) -> str:
        raise LiveWriteAttempted("a live read-only run tried to write the Gmail credential")


def credentials_available() -> tuple[bool, str]:
    """Whether this machine has what a live run needs.

    Checked before the run rather than discovered during it: without a Shopify credential
    every scenario fails for the same reason, and eleven red lines that all mean "there is no
    shop here" tell the reader less than one line saying so.
    """
    from app.secrets import keychain

    try:
        shopify = keychain.present("shopify_client_id") or keychain.present("shopify_static_token")
    except Exception as exc:  # noqa: BLE001 — no keyring backend at all
        return False, f"the Keychain is not available to this process ({type(exc).__name__})"
    if not shopify:
        return False, "no Shopify credential in the Keychain (make secrets)"
    return True, ""


def arm_read_only(runtime: Any) -> tuple[ReadOnlyShopify, ReadOnlyGmail]:
    """Latch the process, then hand the runtime clients that cannot write either.

    Called by the harness before any request is served. The order matters: the latch goes down
    first, so that even the construction of these clients happens in a process that has already
    lost the ability to change anything.
    """
    from app.tools import gmail_tools, shopify_tools

    readonly.engage(REASON)
    if not readonly.active():   # pragma: no cover — belt and braces on a safety device
        raise LiveWriteAttempted("the read-only latch did not engage; refusing to run live")

    settings = runtime.settings
    store = ReadOnlyShopify(
        settings.shopify_shop_domain, settings.shopify_api_version,
        auth_mode=settings.shopify_auth_mode,
    )
    gmail = ReadOnlyGmail()
    runtime.shopify = store
    runtime.gmail = gmail
    shopify_tools.bind(store)
    gmail_tools.bind(gmail, getattr(runtime, "customer_lookup", None))
    log.warning(
        "%s — reading %s and the shop's inbox. No change can be executed by this process.",
        readonly.banner(), settings.shopify_shop_domain,
    )
    return store, gmail


def guarantees() -> list[str]:
    """What the report prints under the run's heading, so a live run is never mistaken for a
    rehearsal of one — or for a run that could have written."""
    return [
        readonly.banner() or "read-only latch NOT engaged",
        "ShopifyClient.mutate refuses: every reviewed Shopify mutation",
        "GmailClient send/draft/modify refuse: every Gmail change",
        "ActionEngine.commit refuses before claiming a proposal",
        "the clients bound to the runtime have no working mutate/send at all",
    ]
