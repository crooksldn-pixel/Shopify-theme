"""M13's rule is that logs contain no personal data. This is how that stays true."""

from __future__ import annotations

import json

from app.logging.turnlog import TurnLog, redact, redact_text


def test_emails_are_redacted():
    assert "jo@example.com" not in redact_text("write to jo@example.com today")


def test_uk_postcodes_are_redacted():
    assert "SW1A 1AA" not in redact_text("ships to SW1A 1AA")
    assert "E8 3RL" not in redact_text("address is E8 3RL")


def test_phone_numbers_are_redacted():
    assert "07700 900123" not in redact_text("call 07700 900123")
    assert "+44 7700 900123" not in redact_text("call +44 7700 900123")


def test_card_numbers_are_redacted():
    assert "4111 1111 1111 1111" not in redact_text("card 4111 1111 1111 1111")


def test_address_keys_are_redacted_whatever_the_value():
    out = redact({"shippingAddress": {"street": "12 Rivington St"}, "city": "London"})
    assert out["shippingAddress"] == "[redacted]"
    assert out["city"] == "London", "non-identifying fields should survive"


def test_message_bodies_are_redacted():
    assert redact({"body": "anything at all"})["body"] == "[redacted]"


def test_empty_values_are_not_replaced_with_the_marker():
    assert redact({"phone": None})["phone"] is None


def test_nested_structures_are_walked():
    out = redact({"threads": [{"from_email": "a@b.com", "subject": "hi jo@example.com"}]})
    assert out["threads"][0]["from_email"] == "[redacted]"
    assert "jo@example.com" not in out["threads"][0]["subject"]


def test_order_numbers_survive_redaction():
    """Over-redacting is a real risk: an order number must still be readable in the log."""
    assert "4832" in redact_text("found order 4832")


def test_written_log_line_contains_no_personal_data(tmp_path):
    TurnLog(tmp_path).write(
        {
            "text": "email jo@example.com about order 4832",
            "result": {"shippingAddress": {"street": "12 Rivington St"}, "phone": "07700900123"},
        }
    )
    written = (tmp_path / "turns.jsonl").read_text()
    for leak in ("jo@example.com", "Rivington", "07700900123"):
        assert leak not in written, f"{leak!r} reached the log file"
    assert json.loads(written)["text"].startswith("email [email]")
