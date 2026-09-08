"""Two read-only Gmail tools.

There is no send, no draft, no label, no trash and no modify anywhere in this module, and the
scope the client requests cannot perform any of them. The gate refuses those verbs by name as
well, so a write path would have to defeat both to exist.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from email.utils import parseaddr
from typing import Any

from app.clients.gmail import GmailAuthRequired, GmailClient
from app.logging.turnlog import redact_text
from app.tools.gate import Tier
from app.tools.registry import ToolError, tool

log = logging.getLogger("crooks.gmail_tools")

MAX_RESULTS = 25
MAX_BODY_CHARS = 1500
MAX_THREAD_MESSAGES = 12

# Gmail categories are ML heuristics and do misclassify genuine customer replies, so this is a
# base filter, not a verdict. Everything that survives it is flagged rather than hidden.
BASE_QUERY = "category:primary -from:me -in:chats -in:trash -in:spam"

_BULK_HEADERS = ("list-unsubscribe", "list-id", "precedence", "auto-submitted", "list-post")
_BULK_SENDER = re.compile(
    r"(no[-_.]?reply|do[-_.]?not[-_.]?reply|notifications?@|mailer@|bounce|newsletter|marketing@)",
    re.I,
)

_client: GmailClient | None = None
# Set by the runtime once Shopify is up. Optional by design: Gmail must keep working when
# Shopify is down, just with a less useful known_customer flag.
_customer_lookup = None


def bind(client: GmailClient, customer_lookup=None) -> None:
    global _client, _customer_lookup
    _client = client
    _customer_lookup = customer_lookup


def _c() -> GmailClient:
    if _client is None:
        raise ToolError("Gmail is not configured on this backend.")
    return _client


def _describe(exc: Exception) -> str:
    """googleapiclient errors embed the request URL — including the search query, which may
    contain an email address the owner typed. Strip URLs, then redact what is left."""
    text = re.sub(r"https?://\S+", "[url]", str(exc))
    return redact_text(text)[:200]


def _is_auth_failure(exc: Exception) -> bool:
    try:
        from google.auth.exceptions import RefreshError
    except ImportError:  # pragma: no cover
        return False
    return isinstance(exc, (RefreshError, GmailAuthRequired)) or "invalid_grant" in str(exc)


def _headers(message: dict) -> dict[str, str]:
    return {
        h["name"].lower(): h["value"]
        for h in (message.get("payload", {}).get("headers") or [])
    }


def _is_bulk(headers: dict[str, str]) -> bool:
    if any(h in headers for h in _BULK_HEADERS):
        return True
    return bool(_BULK_SENDER.search(headers.get("from", "")))


async def _known_customer(email: str) -> bool | None:
    """True/False if Shopify could be asked, None if it could not. None is not False."""
    if not email or _customer_lookup is None:
        return None
    try:
        return await _customer_lookup(email)
    except Exception as exc:  # noqa: BLE001 — Shopify being down must not break Gmail
        log.warning("customer cross-reference unavailable: %s", exc)
        return None


def _fetch_batched(service, stubs, get_request) -> list[dict] | None:
    """Fetch every message in one batch HTTP request. None when the client cannot batch (a
    test double, an old library), in which case the caller fetches one by one."""
    new_batch = getattr(service, "new_batch_http_request", None)
    if not stubs or new_batch is None or not callable(new_batch):
        return None
    results: dict[str, dict] = {}

    def collect(request_id, response, exception):
        if exception is not None:
            log.warning("could not fetch message %s: %s", request_id, _describe(exception))
        elif isinstance(response, dict):
            results[request_id] = response

    try:
        batch = new_batch(callback=collect)
        for stub in stubs:
            batch.add(get_request(stub), request_id=stub["id"])
        batch.execute()
    except Exception as exc:  # noqa: BLE001 — fall back to the one-by-one path
        log.warning("batched fetch failed (%s); fetching one by one", _describe(exc))
        return None
    return [results[stub["id"]] for stub in stubs if stub["id"] in results]


def _decode_part(part: dict) -> str:
    data = (part.get("body") or {}).get("data")
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def _extract_body(payload: dict) -> str:
    """Walk a multipart MIME tree for text/plain, falling back to stripped HTML."""
    plain: list[str] = []
    html: list[str] = []

    def walk(part: dict) -> None:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            plain.append(_decode_part(part))
        elif mime == "text/html":
            html.append(_decode_part(part))
        for child in part.get("parts") or []:
            walk(child)

    walk(payload)
    text = "\n".join(t for t in plain if t).strip()
    if not text and html:
        text = re.sub(r"<[^>]+>", " ", "\n".join(html))
        text = re.sub(r"\s+", " ", text).strip()
    # Quoted history adds length and no information to a spoken answer.
    text = re.split(r"\nOn .{0,80} wrote:\n|\n-{2,} ?Original Message", text)[0].strip()
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS] + f"… [truncated, {len(text) - MAX_BODY_CHARS} more chars]"
    return text


@tool(
    name="gmail_search",
    description=(
        "Search recent email in the CROOKS inbox. Returns the sender, subject, date and a short "
        "snippet for each thread, with bulk and marketing mail flagged, and senders that match a "
        "Shopify customer marked as known customers. Use this before reading a thread — it is "
        "what makes a thread available to read."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional Gmail search terms, e.g. 'jeans' or 'from:jo@example.com'.",
                "default": "",
            },
            "days": {"type": "integer", "description": "How many days back to look.",
                     "default": 1},
            "limit": {"type": "integer", "description": "Maximum threads (1-25).", "default": 10},
            "include_bulk": {
                "type": "boolean",
                "description": "Include newsletters and automated mail.",
                "default": False,
            },
        },
    },
    tier=Tier.GREEN,
)
async def gmail_search(
    query: str = "", days: int = 1, limit: int = 10, include_bulk: bool = False
) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_RESULTS))
    days = max(1, min(int(days), 365))
    full_query = f"newer_than:{days}d {BASE_QUERY}"
    if query.strip():
        full_query += f" {query.strip()}"

    # googleapiclient is synchronous. Run it in a thread so the event loop stays free and the
    # 8-second tool timeout can actually fire — awaiting blocking I/O directly makes the
    # timeout unenforceable and freezes every other request while Gmail stalls.
    def fetch_all() -> list[dict]:
        service = client.service()
        listing = (
            service.users()
            .messages()
            .list(userId="me", q=full_query, maxResults=limit)
            .execute()
        )
        stubs = listing.get("messages", []) or []
        # metadata format still costs 20 quota units, so the result count is the lever.
        headers = [
            "From", "Subject", "Date", "List-Unsubscribe", "List-Id",
            "Precedence", "Auto-Submitted", "List-Post",
        ]

        def get_request(stub):
            return service.users().messages().get(
                userId="me", id=stub["id"], format="metadata", metadataHeaders=headers,
            )

        # One round trip for all of them, not one each: a batch request carries every get in
        # a single HTTP call, which is most of a second saved on every email question.
        batched = _fetch_batched(service, stubs, get_request)
        if batched is not None:
            return batched
        messages: list[dict] = []
        for stub in stubs:
            try:
                messages.append(get_request(stub).execute())
            except Exception as exc:  # noqa: BLE001
                log.warning("could not fetch message %s: %s", stub["id"], _describe(exc))
        return messages

    try:
        messages = await asyncio.to_thread(fetch_all)
    except Exception as exc:  # noqa: BLE001
        if _is_auth_failure(exc):
            client.reset()
            raise ToolError(str(GmailAuthRequired("Gmail authorisation has expired."))) from exc
        raise ToolError(f"Gmail search failed: {_describe(exc)}") from exc

    candidates: list[tuple[str, dict[str, str], dict]] = []
    seen_threads: set[str] = set()
    for message in messages:
        thread_id = message.get("threadId", "")
        if thread_id in seen_threads:
            continue
        seen_threads.add(thread_id)
        headers = _headers(message)
        if _is_bulk(headers) and not include_bulk:
            continue
        candidates.append((thread_id, headers, message))

    # Cross-reference every sender against Shopify concurrently, not one after another.
    senders = [parseaddr(h.get("from", ""))[1] for _, h, _ in candidates]
    known = await asyncio.gather(*(_known_customer(e) for e in senders))

    results: list[dict[str, Any]] = []
    for (thread_id, headers, message), sender_email, is_known in zip(candidates, senders, known, strict=True):
        sender_name = parseaddr(headers.get("from", ""))[0]
        results.append(
            {
                "thread_id": thread_id,
                "from": sender_name or sender_email,
                "from_email": sender_email,
                "subject": headers.get("subject", "(no subject)"),
                "date": headers.get("date", ""),
                "snippet": (message.get("snippet") or "")[:300],
                "likely_bulk": _is_bulk(headers),
                "known_customer": is_known,
            }
        )

    return {
        "query": full_query,
        "count": len(results),
        "threads": results,
        "note": (
            "Gmail's Primary category is a heuristic and can misfile a genuine customer reply. "
            "Nothing here is guaranteed complete."
        ),
    }


@tool(
    name="gmail_read_thread",
    description=(
        "Read the messages in one email thread. Requires a thread_id from gmail_search — you "
        "cannot guess one. Prefer the snippet from gmail_search when it already answers the "
        "question; only read the thread when the detail matters."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "thread_id": {
                "type": "string",
                "description": "The thread_id returned by gmail_search.",
            }
        },
        "required": ["thread_id"],
    },
    tier=Tier.AMBER,
    issued_id_args=("thread_id",),
)
async def gmail_read_thread(thread_id: str) -> dict:
    client = _c()
    try:
        thread = await asyncio.to_thread(
            lambda: client.service()
            .users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        if _is_auth_failure(exc):
            client.reset()
            raise ToolError(str(GmailAuthRequired("Gmail authorisation has expired."))) from exc
        raise ToolError(f"Could not read thread {thread_id}: {_describe(exc)}") from exc

    # The NEWEST messages are the ones that matter — the customer's latest reply is at the end.
    messages = thread.get("messages", [])[-MAX_THREAD_MESSAGES:]
    out = []
    for message in messages:
        headers = _headers(message)
        sender_name, sender_email = parseaddr(headers.get("from", ""))
        out.append(
            {
                "from": sender_name or sender_email,
                "from_email": sender_email,
                "date": headers.get("date", ""),
                "subject": headers.get("subject", ""),
                "body": _extract_body(message.get("payload", {})),
            }
        )

    return {
        "thread_id": thread_id,
        "message_count": len(thread.get("messages", [])),
        "messages_shown": len(out),
        "truncated": len(thread.get("messages", [])) > MAX_THREAD_MESSAGES,
        "messages": out,
    }
