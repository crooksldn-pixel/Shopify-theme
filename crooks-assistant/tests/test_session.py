from __future__ import annotations

import time

import pytest

from app.session.manager import SessionExpired, SessionManager


def test_get_or_create_then_get():
    m = SessionManager(idle_timeout_s=60)
    s = m.get_or_create("a")
    assert m.get("a") is s
    assert m.exists("a")
    assert m.count() == 1


def test_unknown_session_raises_keyerror_subclass():
    m = SessionManager()
    with pytest.raises(SessionExpired):
        m.get("nope")
    with pytest.raises(KeyError):
        m.peek("nope")
    assert not m.exists("nope")


def test_idle_sessions_expire():
    m = SessionManager(idle_timeout_s=0)
    m.get_or_create("a")
    time.sleep(0.01)
    assert not m.exists("a")


def test_peek_does_not_keep_a_session_alive():
    m = SessionManager(idle_timeout_s=60)
    s = m.get_or_create("a")
    before = s.last_seen_at
    time.sleep(0.01)
    m.peek("a")
    assert s.last_seen_at == before
    m.get("a")
    assert s.last_seen_at > before


def test_issue_and_state():
    m = SessionManager()
    s = m.get_or_create("a")
    s.issue("x", "", None)
    assert s.issued_ids == {"x"}
    s.set_state("CHECKING SHOPIFY", "shopify_list_orders")
    assert (s.state, s.state_detail) == ("CHECKING SHOPIFY", "shopify_list_orders")


def test_staged_proposals_get_ids():
    m = SessionManager()
    s = m.get_or_create("a")
    p = s.stage("mock_danger", {}, "no")
    assert p.proposal_id.startswith("prop_")
    assert s.proposals == [p]


def test_drop():
    m = SessionManager()
    m.get_or_create("a")
    m.drop("a")
    assert not m.exists("a")
