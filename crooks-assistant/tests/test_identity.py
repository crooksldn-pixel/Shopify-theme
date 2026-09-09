"""The tablet's identity, confirmed with Tailscale itself: a login header is a claim; the
forwarded address is put to `tailscale whois`, and the login must be the one it names."""

from __future__ import annotations

import json

import pytest

from app import identity

ADDRESS = "100.101.102.103"
LOGIN = "owner@example.com"


class Whois:
    """A fake `tailscale whois --json`: who holds which address, and a count of calls."""

    def __init__(self, holders: dict[str, str] | None = None, *, fail: bool = False) -> None:
        self.holders = dict(holders or {ADDRESS: LOGIN})
        self.fail = fail
        self.calls: list[str] = []

    def __call__(self, cli: str, address: str) -> str:
        self.calls.append(address)
        if self.fail:
            raise RuntimeError("tailscale: not running")
        login = self.holders.get(address)
        if login is None:
            raise RuntimeError("no such peer")
        return json.dumps({"Node": {"Name": "tablet"}, "UserProfile": {"LoginName": login, "DisplayName": "Owner"}})


@pytest.fixture()
def whois():
    w = Whois()
    identity.bind_runner(w)
    yield w
    identity.bind_runner(None)


def test_the_forwarded_address_is_the_first_one_and_only_tailnet_addresses_count():
    assert identity.forwarded_address("100.101.102.103, 127.0.0.1") == ADDRESS
    assert identity.forwarded_address(" [fd7a:115c:a1e0::1] ") == "fd7a:115c:a1e0::1"
    assert identity.on_tailnet(ADDRESS) and identity.on_tailnet("fd7a:115c:a1e0::1")
    assert not identity.on_tailnet("127.0.0.1") and not identity.on_tailnet("192.168.1.9") and not identity.on_tailnet("nonsense")


def test_the_login_on_the_header_must_be_the_one_tailscale_names(whois):
    assert identity.verify(ADDRESS, "Owner@Example.com", cli="/usr/bin/tailscale", now=100.0) == (True, "confirmed by tailscale whois")
    assert identity.verify(ADDRESS, "someone-else@example.com", cli="/usr/bin/tailscale", now=100.0) == (False, "the address belongs to a different login")
    assert whois.calls == [ADDRESS, ADDRESS]


def test_a_confirmed_pairing_is_cached_and_a_refusal_only_briefly(whois):
    assert identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=100.0)[0]
    assert identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=100.0 + identity.CACHE_S - 1)[0]
    assert whois.calls == [ADDRESS], "within the window, whois is not asked again"
    identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=100.0 + identity.CACHE_S + 1)
    assert whois.calls == [ADDRESS, ADDRESS], "after it, it is"
    whois.holders[ADDRESS] = "intruder@example.com"
    ok, why = identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=100.0 + identity.CACHE_S + 1)
    assert ok, "the fresh answer was cached a moment ago; the pairing stands until the window closes"
    identity.bind_runner(whois)   # clears the cache
    assert not identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=200.0)[0]
    assert not identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=200.0 + identity.NEGATIVE_S - 1)[0]
    assert len(whois.calls) == 3, "a refusal is remembered, so a busy tablet is not a whois storm"
    whois.holders[ADDRESS] = LOGIN
    assert identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=200.0 + identity.NEGATIVE_S + 1)[0]


def test_no_cli_no_answer_or_no_address_means_no(whois):
    assert identity.verify(ADDRESS, LOGIN, cli=None, now=1.0) == (False, "the tailscale CLI was not found (set CROOKS_TAILSCALE_CLI)")
    assert identity.verify("", LOGIN, cli="/usr/bin/tailscale", now=1.0) == (False, "no login or address to check")
    assert identity.verify(ADDRESS, "", cli="/usr/bin/tailscale", now=1.0) == (False, "no login or address to check")
    assert identity.verify("10.0.0.5", LOGIN, cli="/usr/bin/tailscale", now=1.0) == (False, "10.0.0.5 is not a tailnet address")
    assert whois.calls == [], "nothing was asked for any of those"
    whois.fail = True
    assert identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=1.0) == (False, "tailscale did not say who holds that address")
    identity.bind_runner(whois)
    whois.fail = False
    whois.holders = {}
    assert identity.verify(ADDRESS, LOGIN, cli="/usr/bin/tailscale", now=1.0) == (False, "tailscale did not say who holds that address")


def test_whois_output_is_read_defensively():
    identity.bind_runner(lambda cli, address: "not json")
    assert identity.whois_login(ADDRESS, cli="x") is None
    identity.bind_runner(lambda cli, address: json.dumps({"UserProfile": {}}))
    assert identity.whois_login(ADDRESS, cli="x") is None
    identity.bind_runner(lambda cli, address: {"UserProfile": {"LoginName": " Owner@Example.com "}})
    assert identity.whois_login(ADDRESS, cli="x") == LOGIN
    identity.bind_runner(None)


def test_the_cli_is_found_where_the_mac_app_keeps_it_or_not_at_all(tmp_path, monkeypatch):
    monkeypatch.setattr(identity.shutil, "which", lambda name: None)
    monkeypatch.setattr(identity, "MAC_APP_CLI", str(tmp_path / "missing"))
    assert identity.cli_path("") is None
    configured = tmp_path / "tailscale"
    configured.write_text("")
    assert identity.cli_path(str(configured)) == str(configured)
    assert identity.cli_path(str(tmp_path / "nope")) is None, "a configured path that does not exist is not used"
    monkeypatch.setattr(identity.shutil, "which", lambda name: "/opt/homebrew/bin/tailscale")
    assert identity.cli_path("") == "/opt/homebrew/bin/tailscale"
