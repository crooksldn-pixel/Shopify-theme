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
# The operator's default tool budget is 8 s; a search is a listing, a batched fetch and, on a
# cold start, a credential refresh. Its own ceiling, still a hard one.
GMAIL_TIMEOUT_S = 15.0
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


def _extract_body(payload: dict, *, limit: int = MAX_BODY_CHARS) -> str:
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
    if len(text) > limit:
        text = text[:limit] + f"… [truncated, {len(text) - limit} more chars]"
    return text


_METADATA_HEADERS = [
    "From", "Subject", "Date", "List-Unsubscribe", "List-Id",
    "Precedence", "Auto-Submitted", "List-Post", "Authentication-Results",
]

_AUTH_PASS = re.compile(r"\b(?:dkim|spf)=pass\b", re.I)


def _authenticated(headers: dict[str, str]) -> bool:
    """Whether the receiving server's own Authentication-Results say the message passed
    DKIM or SPF. A From header is written by the sender; this line is written by Gmail."""
    return bool(_AUTH_PASS.search(headers.get("authentication-results", "")))


async def _list_metadata(client: GmailClient, full_query: str, limit: int) -> list[dict]:
    """The listing and the metadata of every message in it, in one batched round trip.
    Raises ToolError with a readable reason; never a raw client exception."""

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
        def get_request(stub):
            return service.users().messages().get(
                userId="me", id=stub["id"], format="metadata", metadataHeaders=_METADATA_HEADERS,
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
        return await asyncio.to_thread(fetch_all)
    except Exception as exc:  # noqa: BLE001
        if _is_auth_failure(exc):
            client.reset()
            raise ToolError(str(GmailAuthRequired("Gmail authorisation has expired."))) from exc
        raise ToolError(f"Gmail search failed: {_describe(exc)}") from exc


def _one_per_thread(messages: list[dict], include_bulk: bool) -> list[tuple[str, dict[str, str], dict]]:
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
    return candidates


def _summary(thread_id: str, headers: dict[str, str], message: dict) -> dict[str, Any]:
    sender_name, sender_email = parseaddr(headers.get("from", ""))
    return {
        "thread_id": thread_id,
        "message_id": str(message.get("id") or ""),
        "from": sender_name or sender_email,
        "from_email": sender_email,
        "subject": headers.get("subject", "(no subject)"),
        "date": headers.get("date", ""),
        "snippet": (message.get("snippet") or "")[:300],
        "likely_bulk": _is_bulk(headers),
        "authenticated": _authenticated(headers),
    }


# Correlation looks this far back: an order is visible in Shopify for sixty days without the
# read_all_orders scope, and the conversation about it is rarely older than the order.
CORRELATION_DAYS = 60
CORRELATION_LIMIT = 3
_GMAIL_TERM = re.compile(r"[^\w@.+\-]")


async def threads_for(*, sender: str = "", terms: list[str] | tuple[str, ...] = (), days: int = CORRELATION_DAYS, limit: int = CORRELATION_LIMIT) -> dict[str, Any]:
    """Recent inbox threads from one sender, or mentioning one of a few exact terms (an
    order number). For the context layer, not the model: it never raises — an inbox that is
    not configured or not answering is reported as unavailable, and the order card is shown
    without its email. Metadata only; a body is read only when the owner asks for it."""
    if _client is None:
        return {"available": False, "reason": "Gmail is not configured on this backend.", "threads": []}
    clauses: list[str] = []
    sender = _GMAIL_TERM.sub("", (sender or "").strip().lower())
    if sender and "@" in sender:
        clauses.append(f"from:{sender}")
    for term in terms:
        term = _GMAIL_TERM.sub("", str(term or "").strip())
        if term:
            clauses.append(f'"{term}"')
    if not clauses:
        return {"available": True, "threads": []}
    days = max(1, min(int(days), 365))
    limit = max(1, min(int(limit), MAX_RESULTS))
    query = f"newer_than:{days}d -in:trash -in:spam -in:chats ({' OR '.join(clauses)})"
    try:
        messages = await _list_metadata(_c(), query, limit * 2)
    except ToolError as exc:
        log.warning("email correlation unavailable: %s", exc)
        return {"available": False, "reason": str(exc)[:160], "threads": []}
    threads = [_summary(t, h, m) for t, h, m in _one_per_thread(messages, include_bulk=False)]
    return {"available": True, "query": query, "threads": threads[:limit]}


# An email read as evidence for a change is read whole: an address at the foot of a long
# message is still the address.
EVIDENCE_BODY_CHARS = 20_000


async def message_evidence(message_id: str) -> dict[str, Any]:
    """One message, read in full, as evidence for a change the owner asked for: who sent it,
    whether the receiving server vouched for that sender, and its text. For the write tools
    on the Mac — never handed to the model, which cites a message by id and no more."""
    client = _c()
    message_id = str(message_id or "").strip()
    if not message_id:
        raise ToolError("No message id was given.")

    def fetch() -> dict:
        return client.service().users().messages().get(userId="me", id=message_id, format="full").execute()

    try:
        message = await asyncio.to_thread(fetch)
    except Exception as exc:  # noqa: BLE001
        if _is_auth_failure(exc):
            client.reset()
            raise ToolError(str(GmailAuthRequired("Gmail authorisation has expired."))) from exc
        raise ToolError(f"Could not read that email: {_describe(exc)}") from exc
    if not isinstance(message, dict) or not message.get("payload"):
        raise ToolError("That email could not be read.")
    headers = _headers(message)
    sender_name, sender_email = parseaddr(headers.get("from", ""))
    return {
        "message_id": str(message.get("id") or message_id),
        "thread_id": str(message.get("threadId") or ""),
        "from": sender_name or sender_email,
        "from_email": sender_email.strip().lower(),
        "date": headers.get("date", ""),
        "subject": headers.get("subject", ""),
        "authenticated": _authenticated(headers),
        "body": _extract_body(message.get("payload", {}), limit=EVIDENCE_BODY_CHARS),
    }


@tool(
    name="gmail_search",
    description=(
        'Search recent email in the CROOKS inbox: sender, subject, date and a snippet per thread, '
        'bulk mail flagged, senders matching a Shopify customer marked. Call it before reading a '
        'thread — it is what makes a thread available.'
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
    timeout_s=GMAIL_TIMEOUT_S,
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

    messages = await _list_metadata(client, full_query, limit)
    candidates = _one_per_thread(messages, include_bulk)

    # Cross-reference every sender against Shopify concurrently, not one after another.
    senders = [parseaddr(h.get("from", ""))[1] for _, h, _ in candidates]
    known = await asyncio.gather(*(_known_customer(e) for e in senders))

    results: list[dict[str, Any]] = []
    for (thread_id, headers, message), is_known in zip(candidates, known, strict=True):
        results.append({**_summary(thread_id, headers, message), "known_customer": is_known})

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
    timeout_s=GMAIL_TIMEOUT_S,
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
                "message_id": str(message.get("id") or ""),
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
