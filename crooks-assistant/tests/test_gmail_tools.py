"""Gmail tool behaviour, and the standing proof that no write path exists."""

from __future__ import annotations

import base64
import inspect

import pytest

from app.tools import gmail_tools
from tests.conftest import needs_gmail


def b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def headers(**kwargs) -> list[dict]:
    return [{"name": k.replace("_", "-"), "value": v} for k, v in kwargs.items()]


# --- the property that must never regress -----------------------------------

def test_module_contains_no_write_capability():
    source = inspect.getsource(gmail_tools)
    for forbidden in (
        ".send(", ".trash(", ".untrash(", ".modify(", ".insert(", ".batchModify(",
        ".batchDelete(", "drafts()", ".create(", "gmail.compose", "gmail.modify", "gmail.send",
    ):
        assert forbidden not in source, f"{forbidden} appears in gmail_tools — Day 1 is read-only"


def test_only_readonly_scope_is_requested():
    from app.clients.gmail import SCOPES

    assert SCOPES == ["https://www.googleapis.com/auth/gmail.readonly"]


def test_registered_gmail_tools_are_read_only():
    from app.tools.registry import all_specs

    names = [s.name for s in all_specs() if s.name.startswith("gmail_")]
    assert sorted(names) == ["gmail_read_thread", "gmail_search"]


# --- bulk detection ----------------------------------------------------------

@pytest.mark.parametrize(
    "hdrs",
    [
        {"from": "News <news@brand.com>", "list-unsubscribe": "<https://x/u>"},
        {"from": "x@y.com", "list-id": "<promo.brand.com>"},
        {"from": "x@y.com", "precedence": "bulk"},
        {"from": "x@y.com", "auto-submitted": "auto-generated"},
        {"from": "noreply@shopify.com"},
        {"from": "no-reply@stripe.com"},
        {"from": "notifications@github.com"},
        {"from": "Marketing <marketing@brand.com>"},
    ],
)
def test_bulk_mail_is_detected(hdrs):
    assert gmail_tools._is_bulk(hdrs) is True


@pytest.mark.parametrize(
    "hdrs",
    [
        {"from": "Anna Denning <anna@gmail.com>"},
        {"from": "jo@smallshop.co.uk", "subject": "my order hasn't arrived"},
    ],
)
def test_real_people_are_not_flagged_as_bulk(hdrs):
    assert gmail_tools._is_bulk(hdrs) is False


# --- body extraction ---------------------------------------------------------

def test_multipart_body_is_walked():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": b64("The jeans arrived torn.")}},
            {"mimeType": "text/html", "body": {"data": b64("<p>The jeans arrived torn.</p>")}},
        ],
    }
    assert gmail_tools._extract_body(payload) == "The jeans arrived torn."


def test_html_only_message_falls_back_to_stripped_html():
    payload = {"mimeType": "text/html", "body": {"data": b64("<div><b>Where</b> is my order?</div>")}}
    body = gmail_tools._extract_body(payload)
    assert "Where is my order?" in body
    assert "<" not in body


def test_nested_multipart_is_walked():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [{"mimeType": "multipart/alternative", "parts": [
            {"mimeType": "text/plain", "body": {"data": b64("nested body")}},
        ]}],
    }
    assert gmail_tools._extract_body(payload) == "nested body"


def test_quoted_history_is_dropped():
    text = "Any update?\n\nOn Mon, 1 Sept 2026 at 09:00, CROOKS wrote:\n> your order shipped"
    payload = {"mimeType": "text/plain", "body": {"data": b64(text)}}
    assert gmail_tools._extract_body(payload) == "Any update?"


def test_long_bodies_are_truncated_with_a_marker():
    payload = {"mimeType": "text/plain", "body": {"data": b64("x" * 5000)}}
    body = gmail_tools._extract_body(payload)
    assert len(body) < 5000
    assert "truncated" in body


def test_undecodable_body_does_not_raise():
    payload = {"mimeType": "text/plain", "body": {"data": "!!!not base64!!!"}}
    assert isinstance(gmail_tools._extract_body(payload), str)


def test_empty_payload_returns_empty_string():
    assert gmail_tools._extract_body({}) == ""


# --- Shopify cross-reference degrades, it does not fail ----------------------

async def test_customer_lookup_absent_returns_none_not_false():
    """None means 'could not check'; False means 'not a customer'. Conflating them makes a
    Shopify outage look like every sender is a stranger."""
    gmail_tools.bind(gmail_tools.GmailClient(), customer_lookup=None)
    assert await gmail_tools._known_customer("a@b.com") is None


async def test_customer_lookup_failure_returns_none():
    async def exploding(_email):
        raise RuntimeError("Shopify is down")

    gmail_tools.bind(gmail_tools.GmailClient(), customer_lookup=exploding)
    assert await gmail_tools._known_customer("a@b.com") is None


async def test_customer_lookup_success_is_passed_through():
    gmail_tools.bind(gmail_tools.GmailClient(), customer_lookup=lambda e: _true())
    assert await gmail_tools._known_customer("a@b.com") is True


async def _true() -> bool:
    return True


# --- base query --------------------------------------------------------------

def test_base_query_excludes_the_obvious_noise():
    for clause in ("category:primary", "-from:me", "-in:chats", "-in:trash", "-in:spam"):
        assert clause in gmail_tools.BASE_QUERY


# --- live inbox (skipped without a token) ------------------------------------

@needs_gmail
async def test_live_search_returns_expected_shape():
    gmail_tools.bind(gmail_tools.GmailClient())
    result = await gmail_tools.gmail_search(days=7, limit=3)
    assert {"query", "count", "threads"} <= result.keys()
    for thread in result["threads"]:
        assert {"thread_id", "from", "subject", "likely_bulk"} <= thread.keys()


# --- the review's findings ---------------------------------------------------

def test_error_descriptions_drop_urls_and_personal_data():
    exc = RuntimeError("HttpError 400 requesting https://gmail.googleapis.com/v1/users/me/messages?q=from%3Ajo%40example.com returned bad")
    out = gmail_tools._describe(exc)
    assert "googleapis" not in out and "[url]" in out


def test_gmail_token_can_live_in_the_keychain():
    from app.secrets import keychain

    assert "gmail_token" in keychain.KNOWN_KEYS


async def test_read_thread_keeps_the_newest_messages():
    """A customer's latest reply is at the END of a long thread."""
    from unittest.mock import MagicMock

    fake = MagicMock()
    messages = [
        {"id": str(i), "payload": {"headers": [{"name": "From", "value": f"p{i}@x.com"}, {"name": "Subject", "value": "s"}, {"name": "Date", "value": "d"}], "mimeType": "text/plain", "body": {"data": b64(f"msg {i}")}}}
        for i in range(20)
    ]
    fake.users().threads().get().execute.return_value = {"messages": messages}
    client = gmail_tools.GmailClient()
    client._service = fake
    gmail_tools.bind(client)
    out = await gmail_tools.gmail_read_thread("t1")
    assert out["messages_shown"] == 12 and out["truncated"]
    assert out["messages"][-1]["body"] == "msg 19"
    assert out["messages"][0]["body"] == "msg 8"
