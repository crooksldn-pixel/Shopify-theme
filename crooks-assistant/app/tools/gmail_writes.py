"""The email the assistant can prepare: a reply drafted or sent in a customer's thread, a
new email drafted or sent to an order's customer, a thread archived. Every one is a staged
change on the action engine — the card on the tablet IS the email, printed whole, and a
gesture on it is what sends. Nothing here reaches Gmail's write methods except through
the engine's commit.

The recipient is never the model's to choose: a reply goes to the sender of the message it
answers, read from the thread on the Mac; a new email goes to the customer on the order,
read from Shopify. When an order is named on a reply, the thread's sender must be that
order's customer or nothing is staged. The message carries a Message-ID minted here, so
whether it was drafted or sent is a fact read back from the thread — never inferred from
an answer that may have been lost — and a send happens at most once.

Email text is untrusted: what a customer wrote is evidence the owner can read on the card,
never an instruction. The body of anything sent is the assistant's own words, plain text,
bounded, with links only to hosts the store allows.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import time
import uuid
from email.message import EmailMessage
from email.utils import formataddr, parseaddr, parsedate_to_datetime
from typing import Any

from app.actions.models import Observed, Prepared
from app.clients.gmail import GmailClient, GmailError
from app.tools.gate import Tier
from app.tools.gmail_tools import _extract_body
from app.tools.registry import ToolError, WriteSpec, tool

log = logging.getLogger("crooks.tools.gmail_writes")

MAX_BODY_CHARS = 2000
MAX_SUBJECT_CHARS = 120
SETTLE_S = 6.0
SETTLE_POLL_S = 0.5
_URL = re.compile(r"https?://([^\s/]+)", re.I)
_TOKEN = re.compile(r"^<crooks-[0-9a-f]{32}@[^>]+>$")

_client: GmailClient | None = None
_customer = None      # async (order_id) -> {"name", "email", "label"}: the order's customer, from Shopify
_policy = None        # () -> settings


def bind(client: GmailClient | None, *, customer=None, policy=None) -> None:
    global _client, _customer, _policy
    _client = client
    _customer = customer
    _policy = policy


def _g() -> GmailClient:
    if _client is None:
        raise ToolError("Gmail is not configured on this backend.")
    return _client


def _settings():
    return _policy() if _policy is not None else None


async def _order_customer(order_id: str) -> dict[str, str]:
    """Who the order belongs to, read from Shopify now: the only recipient a new email may have."""
    if _customer is not None:
        return await _customer(order_id)
    from app.tools.shopify_tools import hydrator

    order = await hydrator().order(str(order_id), budget_s=0.0)
    return {
        "name": str(order.get("customer_name") or ""), "email": str(order.get("customer_email") or "").strip().lower(),
        "label": str(order.get("order_number") or ""),
    }


# ------------------------------------------------------------------- the message


def clean_body(body: object) -> str:
    """The assistant's words as they will be sent: plain text, bounded, links only to hosts
    the store allows, the store's sign-off on the end."""
    settings = _settings()
    text = str(body or "").replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    if not text:
        raise ToolError("The email has no text.")
    if "<" in text or any(ord(ch) < 32 and ch not in "\n\t" for ch in text):
        raise ToolError("The email must be plain text.")
    if len(text) > MAX_BODY_CHARS:
        raise ToolError(f"The email is longer than {MAX_BODY_CHARS} characters; shorten it.")
    allowed = [h.strip().lower() for h in str(getattr(settings, "gmail_link_hosts", "") or "").split(",") if h.strip()]
    for host in _URL.findall(text):
        host = host.lower().split(":")[0]
        if not any(host == a or host.endswith("." + a) for a in allowed):
            raise ToolError(f"The email links to {host}, which is not a site the store links to. Leave the link out.")
    signature = str(getattr(settings, "gmail_signature", "") or "").strip()
    if signature and not text.rstrip().endswith(signature):
        text = f"{text}\n\n{signature}"
    return text


def clean_subject(subject: object) -> str:
    text = " ".join(str(subject or "").split())
    if not text:
        raise ToolError("The email needs a subject.")
    if len(text) > MAX_SUBJECT_CHARS or "<" in text:
        raise ToolError("The subject must be one plain line.")
    return text


def reply_subject(subject: str) -> str:
    text = " ".join(str(subject or "").split())
    return text if re.match(r"^re\s*:", text, re.I) else f"Re: {text}" if text else "Re: your order"


def new_token(address: str) -> str:
    """A Message-ID minted here: how the message is found again in the thread, whatever
    happened to the answer that was meant to say it had gone."""
    domain = address.split("@", 1)[1] if "@" in address else "crooks.local"
    return f"<crooks-{uuid.uuid4().hex}@{domain}>"


def build_raw(*, sender: str, sender_name: str, to: str, to_name: str, subject: str, body: str, token: str, in_reply_to: str = "", references: str = "") -> str:
    """The exact bytes Gmail will be handed, base64url as its API wants them."""
    message = EmailMessage()
    message["From"] = formataddr((sender_name, sender)) if sender_name else sender
    message["To"] = formataddr((to_name, to)) if to_name else to
    message["Subject"] = subject
    message["Message-ID"] = token
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = " ".join(x for x in (references, in_reply_to) if x).strip()
    message.set_content(body)
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def _when(date_header: str) -> str:
    try:
        return parsedate_to_datetime(date_header).strftime("%-d %b %H:%M")
    except (TypeError, ValueError, IndexError):
        return str(date_header or "")[:16]


def _first_name(name: str, email: str) -> str:
    return (name.split() or [email.split("@", 1)[0] or "them"])[0]


# ----------------------------------------------------------------------- the thread


async def thread_context(thread_id: str) -> dict[str, Any]:
    """The thread as it is: who to answer, how to address the reply, what was sent from
    here already (by the tokens minted here), and the drafts waiting in it."""
    client = _g()
    messages = await asyncio.to_thread(client.thread_messages, thread_id)
    if not messages:
        raise ToolError("That thread is empty or could not be read.")
    me = (await asyncio.to_thread(client.address)) or ""
    inbound = [m for m in messages if "DRAFT" not in m["labels"] and "SENT" not in m["labels"] and parseaddr(m["headers"].get("from", ""))[1].strip().lower() != me]
    real = [m for m in messages if "DRAFT" not in m["labels"]]
    tokens_sent = {m["headers"].get("message-id", "").strip() for m in messages if "SENT" in m["labels"] and _TOKEN.match(m["headers"].get("message-id", "").strip())}
    drafts = [
        {"message_id": m["id"], "token": m["headers"].get("message-id", "").strip()}
        for m in messages if "DRAFT" in m["labels"] and _TOKEN.match(m["headers"].get("message-id", "").strip())
    ]
    last_in = inbound[-1] if inbound else None
    head = (last_in or real[-1] if real else messages[-1])["headers"]
    name, email = parseaddr(head.get("from", ""))
    return {
        "thread_id": thread_id, "subject": head.get("subject", ""), "last": (real[-1]["id"] if real else ""),
        "to_name": name.strip(), "to_email": email.strip().lower(), "date": head.get("date", ""),
        "in_reply_to": head.get("message-id", "").strip(), "references": head.get("references", "").strip(),
        "authenticated": bool(re.search(r"\b(?:dkim|spf)=pass\b", head.get("authentication-results", ""), re.I)),
        "has_inbound": last_in is not None, "tokens_sent": tokens_sent, "drafts": drafts,
    }


def _thread_fingerprint(ctx: dict[str, Any], token: str) -> dict[str, Any]:
    return {
        "last": ctx["last"], "drafts": sum(1 for d in ctx["drafts"] if d["token"] == token), "sent": 1 if token in ctx["tokens_sent"] else 0,
    }


async def _observe_thread(execution: dict) -> Observed:
    ctx = await thread_context(str(execution["thread_id"]))
    return Observed(fingerprint=_thread_fingerprint(ctx, str(execution["token"])), entity=None)


async def _token_state(token: str) -> dict[str, int]:
    """For a message outside any thread: how many drafts and how many sent messages carry
    this token, by Gmail's own search on the Message-ID."""
    client = _g()
    drafts, sent = await asyncio.gather(
        asyncio.to_thread(client.list_drafts, f"rfc822msgid:{token.strip('<>')}"),
        asyncio.to_thread(client.find_messages, f"rfc822msgid:{token.strip('<>')} in:sent"),
    )
    return {"drafts": len(drafts), "sent": len(sent)}


async def _observe_token(execution: dict) -> Observed:
    return Observed(fingerprint=await _token_state(str(execution["token"])), entity=None)


async def _check_order(order_id: str, ctx: dict[str, Any]) -> dict[str, str]:
    """A reply named with an order must be to that order's customer, or it is not staged."""
    customer = await _order_customer(order_id)
    if not customer.get("email") or customer["email"] != ctx["to_email"]:
        raise ToolError(
            f"That thread is from {ctx['to_email'] or 'an unknown sender'}, not the customer on order {customer.get('label') or order_id}. Nothing was prepared."
        )
    return customer


def _provenance(ctx: dict[str, Any]) -> str:
    return f"{ctx['to_email']}, {_when(ctx['date'])} · {'verified sender' if ctx['authenticated'] else 'sender not verified'}"


async def _draft_body(draft_id: str) -> str:
    draft = await asyncio.to_thread(_g().get_draft, draft_id)
    return _extract_body((draft.get("message") or {}).get("payload") or {}, limit=MAX_BODY_CHARS * 2)


async def _the_one_draft(drafts: list[dict[str, Any]], where: str) -> dict[str, Any]:
    """Exactly one draft prepared here, or a refusal: a send never guesses between two."""
    if not drafts:
        raise ToolError(f"There is no draft prepared here {where}. Say what the email should say.")
    if len(drafts) > 1:
        raise ToolError(f"There are {len(drafts)} drafts prepared here {where}; delete the extra ones in Gmail first.")
    token = drafts[0]["token"]
    listed = await asyncio.to_thread(_g().list_drafts, f"rfc822msgid:{token.strip('<>')}")
    if len(listed) != 1:
        raise ToolError("That draft could not be found in Gmail.")
    body = await _draft_body(listed[0]["draft_id"])
    return {"draft_id": listed[0]["draft_id"], "token": token, "body": body}


# ----------------------------------------------------------------------- executing


async def _execute_draft(execution: dict) -> dict:
    client = _g()
    if execution.get("delete"):
        drafts = await asyncio.to_thread(client.list_drafts, f"rfc822msgid:{str(execution['token']).strip('<>')}")
        for draft in drafts:
            await asyncio.to_thread(client.delete_draft, draft["draft_id"])
        return {"deleted": len(drafts)}
    return await asyncio.to_thread(client.create_draft, str(execution["raw"]), execution.get("thread_id") or None)


async def _execute_send(execution: dict) -> dict:
    client = _g()
    if execution.get("draft_id"):
        return await asyncio.to_thread(client.send_draft, str(execution["draft_id"]))
    return await asyncio.to_thread(client.send_message, str(execution["raw"]), execution.get("thread_id") or None)


async def _settle_send(execution: dict, sent: dict) -> None:
    """Gmail lists a sent message a moment after the answer; wait for the thread (or the
    search) to show the token, bounded, so the proof reads what is there."""
    deadline = time.monotonic() + SETTLE_S
    while time.monotonic() < deadline:
        try:
            if execution.get("thread_id"):
                ctx = await thread_context(str(execution["thread_id"]))
                if str(execution["token"]) in ctx["tokens_sent"]:
                    return
            elif (await _token_state(str(execution["token"])))["sent"]:
                return
        except (ToolError, GmailError) as exc:
            log.info("settle: %s", exc)
        await asyncio.sleep(SETTLE_POLL_S)


def _verify_drafted(before: dict, observed: dict, execution: dict) -> tuple[bool, str]:
    return observed.get("drafts") == 1 and not observed.get("sent"), ""


def _verify_sent(before: dict, observed: dict, execution: dict) -> tuple[bool, str]:
    return bool(observed.get("sent")), ""


def _undo_draft(execution: dict) -> dict:
    return {"thread_id": execution.get("thread_id", ""), "token": execution["token"], "delete": True}


async def _entity_email(execution: dict) -> dict:
    return {"kind": "email", "to": str(execution.get("to") or ""), "subject": str(execution.get("subject") or ""), "body": str(execution.get("body") or ""), "state": str(execution.get("state") or "")}


def _present_email(proposal) -> dict:
    s = proposal.summary
    sending = s.get("sending")
    if proposal.undo_of:
        return {"title": "Delete the draft", "summary": "", "detail": "Removes the draft from Gmail.", "confirm_label": "Tap to delete", "undone_title": "Draft deleted"}
    facts = [{"label": "To", "value": str(s.get("to_line") or "")}, {"label": "Subject", "value": str(s.get("subject") or "")}]
    if s.get("in_reply_to"):
        facts.append({"label": "Replying to", "value": str(s["in_reply_to"]), "tone": "" if s.get("verified_sender") else "warn"})
    if s.get("order_line"):
        facts.append({"label": "Order", "value": str(s["order_line"])})
    if sending:
        facts.append({"label": "From", "value": str(s.get("from_line") or "")})
    return {
        "title": str(s.get("title") or ("Send the email" if sending else "Save a draft")),
        "summary": "", "body": str(s.get("body") or ""), "facts": facts,
        "detail": "Sends now. It cannot be unsent." if sending else "Saved in Gmail drafts; nothing is sent until you say so.",
        "done_title": str(s.get("done_title") or ("Email sent" if sending else "Draft saved")),
    }


def _prepared_email(*, execution: dict, before: dict, expected_after: dict, entity_ref: str, ctx: dict | None, customer: dict | None, sending: bool, title: str, sender: str, kind: str) -> Prepared:
    to_email, to_name = execution["to"], execution.get("to_name", "")
    first = _first_name(to_name, to_email)
    to_line = f"{to_name} <{to_email}>" if to_name else to_email
    read_back = f"{'send' if sending else 'draft'} {'a reply' if ctx else 'an email'} to {first}" + (f" about order {customer['label'].lstrip('#')}" if customer and customer.get("label") else "")
    label = f"#{customer['label'].lstrip('#')}" if customer and customer.get("label") else "thread"
    return Prepared(
        execution=execution, before=before, expected_after=expected_after, entity_ref=entity_ref, entity_label=label,
        summary={
            "title": title, "sending": sending, "done_title": ("Reply sent" if ctx else "Email sent") if sending else "Draft saved",
            "to_line": to_line, "spoken_to": first, "subject": execution["subject"], "body": execution["body"],
            "in_reply_to": _provenance(ctx) if ctx else "", "verified_sender": bool(ctx and ctx["authenticated"]),
            "order_line": f"#{customer['label'].lstrip('#')} · the customer on the order" if customer and customer.get("label") else "",
            "from_line": sender, "read_back": read_back, "pii": [v for v in (to_email, to_name, execution["subject"]) if v],
            "ledger": {
                "kind": kind, "reply": bool(ctx), "draft_used": bool(execution.get("draft_id")), "chars": len(execution["body"]),
                "verified_sender": bool(ctx and ctx["authenticated"]), "order": bool(customer),
            },
        },
    )


# --------------------------------------------------------------------------- the tools

_REPLY_SCHEMA = {
    "thread_id": {"type": "string", "description": "From gmail_search or the order's email."},
    "body": {"type": "string", "maxLength": MAX_BODY_CHARS, "description": "The reply, plainly. The sign-off is added."},
    "order_id": {"type": "string", "description": "The order it is about, if any; the sender must be its customer."},
}


@tool(
    name="gmail_draft_reply",
    description=(
        "Save a reply in a customer's thread as a Gmail draft, addressed to the sender of the message "
        "it answers. Write it yourself, plainly. Nothing is sent: the draft is saved when the owner "
        "taps the card."
    ),
    input_schema={"type": "object", "properties": dict(_REPLY_SCHEMA), "required": ["thread_id", "body"]},
    tier=Tier.AMBER,
    issued_id_args=("thread_id", "order_id"),
    write=WriteSpec(
        operation="gmail_draft_reply", entity_kind="email", entity_arg="thread_id", mutation="gmail:draft",
        observe=_observe_thread, execute=_execute_draft, present=_present_email, entity=_entity_email, verify=_verify_drafted,
        reversible=True, undo=_undo_draft, op_class="reversible",
        spoken_success="Draft saved to {to}. It's in Gmail, not sent.", spoken_undo_success="Draft deleted.",
        spoken_failure="I couldn't confirm the draft was saved. Check Gmail's drafts.",
        spoken_stale="A new message arrived in that thread since this was prepared. Nothing was saved.",
    ),
)
async def gmail_draft_reply(thread_id: str, body: str, order_id: str = "") -> Prepared:
    client = _g()
    ctx = await thread_context(str(thread_id))
    if not ctx["has_inbound"]:
        raise ToolError("There is no message from the customer in that thread to reply to.")
    customer = await _check_order(order_id, ctx) if order_id else None
    text = clean_body(body)
    sender = await asyncio.to_thread(client.address)
    token = new_token(sender)
    subject = reply_subject(ctx["subject"])
    raw = build_raw(sender=sender, sender_name=str(getattr(_settings(), "gmail_from_name", "") or ""), to=ctx["to_email"], to_name=ctx["to_name"],
                    subject=subject, body=text, token=token, in_reply_to=ctx["in_reply_to"], references=ctx["references"])
    execution = {"thread_id": str(thread_id), "token": token, "raw": raw, "to": ctx["to_email"], "to_name": ctx["to_name"], "subject": subject, "body": text, "state": "draft"}
    before = _thread_fingerprint(ctx, token)
    return _prepared_email(execution=execution, before=before, expected_after={**before, "drafts": 1}, entity_ref=str(thread_id), ctx=ctx, customer=customer,
                           sending=False, title="Save a draft reply", sender=sender, kind="draft_reply")


@tool(
    name="gmail_send_reply",
    description=(
        "Send a reply in a customer's thread to the sender of the message it answers. Give the reply "
        "in your own plain words, or leave body empty to send the one draft prepared here in that "
        "thread. Sent only when the owner holds the card."
    ),
    input_schema={"type": "object", "properties": dict(_REPLY_SCHEMA), "required": ["thread_id"]},
    tier=Tier.RED,
    issued_id_args=("thread_id", "order_id"),
    write=WriteSpec(
        operation="gmail_send_reply", entity_kind="email", entity_arg="thread_id", mutation="gmail:send",
        observe=_observe_thread, execute=_execute_send, present=_present_email, entity=_entity_email, verify=_verify_sent, settle=_settle_send,
        reversible=False, op_class="irreversible",
        spoken_success="Reply sent to {to}.",
        spoken_failure="I couldn't confirm the reply went. Check Sent in Gmail before sending again.",
        spoken_stale="A new message arrived in that thread since this was prepared. Nothing was sent.",
    ),
)
async def gmail_send_reply(thread_id: str, body: str = "", order_id: str = "") -> Prepared:
    client = _g()
    ctx = await thread_context(str(thread_id))
    if not ctx["has_inbound"]:
        raise ToolError("There is no message from the customer in that thread to reply to.")
    customer = await _check_order(order_id, ctx) if order_id else None
    sender = await asyncio.to_thread(client.address)
    subject = reply_subject(ctx["subject"])
    if str(body or "").strip():
        text = clean_body(body)
        token = new_token(sender)
        raw = build_raw(sender=sender, sender_name=str(getattr(_settings(), "gmail_from_name", "") or ""), to=ctx["to_email"], to_name=ctx["to_name"],
                        subject=subject, body=text, token=token, in_reply_to=ctx["in_reply_to"], references=ctx["references"])
        execution = {"thread_id": str(thread_id), "token": token, "raw": raw, "draft_id": "", "to": ctx["to_email"], "to_name": ctx["to_name"], "subject": subject, "body": text, "state": "sent"}
    else:
        draft = await _the_one_draft(ctx["drafts"], "in that thread")
        execution = {"thread_id": str(thread_id), "token": draft["token"], "raw": "", "draft_id": draft["draft_id"], "to": ctx["to_email"], "to_name": ctx["to_name"], "subject": subject, "body": draft["body"], "state": "sent"}
    before = _thread_fingerprint(ctx, execution["token"])
    if before["sent"]:
        raise ToolError("That was already sent.")
    return _prepared_email(execution=execution, before=before, expected_after={**before, "drafts": 0, "sent": 1}, entity_ref=str(thread_id), ctx=ctx, customer=customer,
                           sending=True, title="Send the reply", sender=sender, kind="send_reply")


_NEW_SCHEMA = {
    "order_id": {"type": "string", "description": "The order whose customer this goes to."},
    "subject": {"type": "string", "maxLength": MAX_SUBJECT_CHARS, "description": "One plain line."},
    "body": {"type": "string", "maxLength": MAX_BODY_CHARS, "description": "The email, plainly. The sign-off is added."},
}


@tool(
    name="gmail_draft_new",
    description=(
        "Save a new email to an order's customer as a Gmail draft; the address comes from the order. "
        "Write it yourself, plainly. Saved when the owner taps the card; nothing is sent."
    ),
    input_schema={"type": "object", "properties": dict(_NEW_SCHEMA), "required": ["order_id", "subject", "body"]},
    tier=Tier.AMBER,
    issued_id_args=("order_id",),
    write=WriteSpec(
        operation="gmail_draft_new", entity_kind="email", entity_arg="order_id", mutation="gmail:draft",
        observe=_observe_token, execute=_execute_draft, present=_present_email, entity=_entity_email, verify=_verify_drafted,
        reversible=True, undo=_undo_draft, op_class="reversible",
        spoken_success="Draft saved to {to}. It's in Gmail, not sent.", spoken_undo_success="Draft deleted.",
        spoken_failure="I couldn't confirm the draft was saved. Check Gmail's drafts.",
        spoken_stale="That changed since it was prepared. Nothing was saved.",
    ),
)
async def gmail_draft_new(order_id: str, subject: str, body: str) -> Prepared:
    client = _g()
    customer = await _order_customer(str(order_id))
    if not customer.get("email"):
        raise ToolError(f"Order {customer.get('label') or order_id} has no email address.")
    text = clean_body(body)
    line = clean_subject(subject)
    sender = await asyncio.to_thread(client.address)
    token = new_token(sender)
    raw = build_raw(sender=sender, sender_name=str(getattr(_settings(), "gmail_from_name", "") or ""), to=customer["email"], to_name=customer.get("name", ""), subject=line, body=text, token=token)
    execution = {"thread_id": "", "token": token, "raw": raw, "to": customer["email"], "to_name": customer.get("name", ""), "subject": line, "body": text, "state": "draft"}
    before = {"drafts": 0, "sent": 0}
    return _prepared_email(execution=execution, before=before, expected_after={"drafts": 1, "sent": 0}, entity_ref=str(order_id), ctx=None, customer=customer,
                           sending=False, title="Save a draft", sender=sender, kind="draft_new")


@tool(
    name="gmail_send_new",
    description=(
        "Send a new email to an order's customer; the address comes from the order. Give subject and "
        "body in your own plain words, or leave both empty to send the one draft prepared here for "
        "that customer. Sent only when the owner holds the card."
    ),
    input_schema={"type": "object", "properties": dict(_NEW_SCHEMA), "required": ["order_id"]},
    tier=Tier.RED,
    issued_id_args=("order_id",),
    write=WriteSpec(
        operation="gmail_send_new", entity_kind="email", entity_arg="order_id", mutation="gmail:send",
        observe=_observe_token, execute=_execute_send, present=_present_email, entity=_entity_email, verify=_verify_sent, settle=_settle_send,
        reversible=False, op_class="irreversible",
        spoken_success="Email sent to {to}.",
        spoken_failure="I couldn't confirm the email went. Check Sent in Gmail before sending again.",
        spoken_stale="That changed since it was prepared. Nothing was sent.",
    ),
)
async def gmail_send_new(order_id: str, subject: str = "", body: str = "") -> Prepared:
    client = _g()
    customer = await _order_customer(str(order_id))
    if not customer.get("email"):
        raise ToolError(f"Order {customer.get('label') or order_id} has no email address.")
    sender = await asyncio.to_thread(client.address)
    if str(body or "").strip() or str(subject or "").strip():
        text = clean_body(body)
        line = clean_subject(subject)
        token = new_token(sender)
        raw = build_raw(sender=sender, sender_name=str(getattr(_settings(), "gmail_from_name", "") or ""), to=customer["email"], to_name=customer.get("name", ""), subject=line, body=text, token=token)
        execution = {"thread_id": "", "token": token, "raw": raw, "draft_id": "", "to": customer["email"], "to_name": customer.get("name", ""), "subject": line, "body": text, "state": "sent"}
    else:
        listed = await asyncio.to_thread(client.list_drafts, f"in:draft to:{customer['email']}")
        ours = []
        for d in listed:
            draft = await asyncio.to_thread(client.get_draft, d["draft_id"])
            headers = {h["name"].lower(): h["value"] for h in ((draft.get("message") or {}).get("payload") or {}).get("headers") or []}
            token = headers.get("message-id", "").strip()
            if _TOKEN.match(token) and not headers.get("in-reply-to"):
                ours.append({"draft_id": d["draft_id"], "token": token, "subject": headers.get("subject", ""), "body": _extract_body((draft.get("message") or {}).get("payload") or {}, limit=MAX_BODY_CHARS * 2)})
        if not ours:
            raise ToolError(f"There is no draft prepared here for {customer.get('name') or customer['email']}. Say what the email should say.")
        if len(ours) > 1:
            raise ToolError(f"There are {len(ours)} drafts prepared here for {customer.get('name') or customer['email']}; delete the extra ones in Gmail first.")
        draft = ours[0]
        execution = {"thread_id": "", "token": draft["token"], "raw": "", "draft_id": draft["draft_id"], "to": customer["email"], "to_name": customer.get("name", ""), "subject": draft["subject"], "body": draft["body"], "state": "sent"}
    before = await _token_state(execution["token"])
    if before["sent"]:
        raise ToolError("That was already sent.")
    return _prepared_email(execution=execution, before=before, expected_after={"drafts": 0, "sent": 1}, entity_ref=str(order_id), ctx=None, customer=customer,
                           sending=True, title="Send the email", sender=sender, kind="send_new")


# ------------------------------------------------------------------------ the inbox


async def _observe_inbox(execution: dict) -> Observed:
    labels = await asyncio.to_thread(_g().thread_labels, str(execution["thread_id"]))
    return Observed(fingerprint={"inbox": "INBOX" in labels}, entity=None)


async def _execute_archive(execution: dict) -> dict:
    await asyncio.to_thread(_g().modify_thread, str(execution["thread_id"]), add=list(execution.get("add") or []), remove=list(execution.get("remove") or []))
    return {"thread_id": str(execution["thread_id"])}


def _present_archive(proposal) -> dict:
    s = proposal.summary
    if proposal.undo_of:
        return {"title": "Put it back in the inbox", "summary": "", "detail": "", "confirm_label": "Tap to undo", "undone_title": "Back in the inbox"}
    return {
        "title": "Archive the thread", "summary": "", "detail": "Leaves the inbox; still there in All Mail and in search. Undo puts it back.",
        "facts": [{"label": "Thread", "value": str(s.get("subject") or "")}, {"label": "From", "value": str(s.get("from_line") or "")}],
        "done_title": "Archived",
    }


@tool(
    name="gmail_thread_archive",
    description="Archive an email thread: it leaves the inbox and stays in All Mail. Applied when the owner taps the card; undo puts it back.",
    input_schema={"type": "object", "properties": {"thread_id": {"type": "string", "description": "From gmail_search or the order's email."}}, "required": ["thread_id"]},
    tier=Tier.AMBER,
    issued_id_args=("thread_id",),
    write=WriteSpec(
        operation="gmail_thread_archive", entity_kind="thread", entity_arg="thread_id", mutation="gmail:labels",
        observe=_observe_inbox, execute=_execute_archive, present=_present_archive,
        reversible=True, undo=lambda execution: {"thread_id": execution["thread_id"], "add": ["INBOX"], "remove": []}, op_class="reversible",
        spoken_success="Archived.", spoken_undo_success="It's back in the inbox.",
        spoken_failure="I couldn't confirm the thread was archived.", spoken_stale="That thread isn't in the inbox any more.",
    ),
)
async def gmail_thread_archive(thread_id: str) -> Prepared:
    client = _g()
    labels = await asyncio.to_thread(client.thread_labels, str(thread_id))
    if "INBOX" not in labels:
        raise ToolError("That thread is not in the inbox.")
    messages = await asyncio.to_thread(client.thread_messages, str(thread_id))
    head = messages[-1]["headers"] if messages else {}
    name, email = parseaddr(head.get("from", ""))
    subject = head.get("subject", "")
    return Prepared(
        execution={"thread_id": str(thread_id), "add": [], "remove": ["INBOX"]},
        before={"inbox": True}, expected_after={"inbox": False}, entity_ref=str(thread_id), entity_label=subject[:60] or "the thread",
        summary={"subject": subject, "from_line": f"{name} <{email}>" if name else email, "read_back": f"archive the thread {subject[:60]}".strip(), "pii": [v for v in (name, email) if v], "ledger": {"kind": "archive"}},
    )
