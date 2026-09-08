"""Provider logic that does not need a live Claude: result classification, error mapping, the
billing guard, and — with the SDK installed — that the options object actually constructs."""

from __future__ import annotations

import pytest

from app.providers.anthropic_api import AnthropicAPIProvider
from app.providers.max_agent_sdk import (
    BillingGuardError,
    MaxAgentSDKProvider,
    assert_no_payg_credentials,
    classify_claude_error,
    result_kind,
    usage_limit_line,
)


class R:
    def __init__(self, **kw):
        self.subtype, self.is_error, self.result, self.errors, self.api_error_status = "success", False, "", [], None
        self.__dict__.update(kw)


def test_success_result_is_none():
    assert result_kind(R()) is None
    assert result_kind(None) is None


@pytest.mark.parametrize(
    "msg,kind",
    [
        (R(subtype="error_max_turns", is_error=True), "max_turns"),
        (R(is_error=True, api_error_status=429), "usage_limit"),
        (R(is_error=True, result="You've hit your usage limit"), "usage_limit"),
        (R(is_error=True, api_error_status=401), "auth"),
        (R(is_error=True, api_error_status=500), "api_error"),
        (R(is_error=True, subtype="error_during_execution"), "unknown"),
    ],
)
def test_result_kinds(msg, kind):
    assert result_kind(msg) == kind


@pytest.mark.parametrize(
    "detail,expect",
    [
        ("Resets at 3pm (UTC)", "resets at 3pm UTC"),
        ("try again in 45 minutes", "resets in 45 minutes"),
        ("resets at 15:00 UTC", "resets at 15:00 UTC"),
        ("limit reached", "rolling five-hour window"),
    ],
)
def test_usage_limit_line_reads_back_reset_time(detail, expect):
    assert expect in usage_limit_line(detail)
    assert "retry" in usage_limit_line(detail).lower() or "try again" in usage_limit_line(detail)


def test_billing_guard(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with pytest.raises(BillingGuardError):
        assert_no_payg_credentials()
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "x")
    with pytest.raises(BillingGuardError):
        assert_no_payg_credentials()


def test_billing_guard_passes_when_clean(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    assert_no_payg_credentials()


def test_typed_sdk_errors_are_classified():
    sdk = pytest.importorskip("claude_agent_sdk")
    assert classify_claude_error(sdk.CLINotFoundError("x"))[0] == "cli_missing"
    assert classify_claude_error(RuntimeError("usage limit reached"))[0] == "usage_limit"
    assert classify_claude_error(RuntimeError("401 unauthorized"))[0] == "auth"
    assert classify_claude_error(ValueError("???"))[0] == "unknown"


async def test_stub_provider_never_works():
    p = AnthropicAPIProvider()
    for coro in (p.start(), p.turn("s", "hi"), p.health(), p.stop(), p.reset_session("s")):
        with pytest.raises(NotImplementedError):
            await coro


def test_stub_provider_imports_no_sdk_and_reads_no_key():
    import inspect

    from app.providers import anthropic_api

    src = inspect.getsource(anthropic_api)
    assert "import anthropic" not in src
    assert "ANTHROPIC_API_KEY" not in src
    assert "keychain" not in src


def test_options_construct_with_no_builtin_tools(monkeypatch):
    """With the SDK installed, prove the options object we build removes every built-in."""
    pytest.importorskip("claude_agent_sdk")
    from app.tools import mock  # noqa: F401 — registers tools

    p = MaxAgentSDKProvider(system_prompt="sys", model="sonnet", cli_path="/usr/bin/true")
    p._auth_mode = "cli"
    opts = p._options()
    assert opts.tools == []
    assert opts.permission_mode == "dontAsk"
    assert opts.setting_sources == []
    assert "crooks" in opts.mcp_servers
    assert all(name.startswith("mcp__crooks__") for name in opts.allowed_tools)
    # RED tools are disallowed at the SDK layer too, not only denied by the hook.
    assert "mcp__crooks__mock_danger" in opts.disallowed_tools
    assert "mcp__crooks__mock_danger" not in opts.allowed_tools
    assert "mcp__crooks__mock_echo" in opts.allowed_tools
    assert "PreToolUse" in opts.hooks
    assert opts.env == {}  # CLI mode injects nothing
    assert opts.system_prompt == "sys"


async def test_turn_before_start_is_honest():
    p = MaxAgentSDKProvider(system_prompt="sys")
    res = await p.turn("s", "hi")
    assert res.error_kind == "not_started"


async def test_health_reports_cli_auth_caveat():
    p = MaxAgentSDKProvider(system_prompt="sys", cli_path="/usr/bin/true")
    p._started, p._auth_mode = True, "cli"
    ok, detail = await p.health()
    assert ok and "launchd" in detail


def test_red_hook_events_are_recorded_as_tool_calls():
    from app.session.models import Session

    p = MaxAgentSDKProvider(system_prompt="sys")
    session = Session(session_id="s")
    session.stage("mock_danger", {}, "refused by gate")
    p._current = session
    p._on_tool_event("mock_danger", "RED")
    assert p._calls and p._calls[0].name == "mock_danger" and not p._calls[0].ok
    assert session.state == "THINKING" and "refused" in session.state_detail


def test_tool_events_drive_live_state():
    from app.session.models import Session

    p = MaxAgentSDKProvider(system_prompt="sys")
    p._current = Session(session_id="s")
    p._on_tool_event("shopify_list_orders", "GREEN")
    assert p._current.state == "CHECKING SHOPIFY"
    p._on_tool_event("gmail_search", "GREEN")
    assert p._current.state == "CHECKING EMAIL"


async def test_set_system_prompt_drops_open_clients():
    class FakeClient:
        def __init__(self): self.closed = False
        async def disconnect(self): self.closed = True

    p = MaxAgentSDKProvider(system_prompt="old")
    fake = FakeClient()
    p._clients["s"] = fake
    p._client_last_used["s"] = 0
    await p.set_system_prompt("new")
    assert p._system_prompt == "new"
    assert fake.closed and not p._clients


def test_broader_billing_guard(monkeypatch):
    for name in ("ANTHROPIC_API_KEY_HELPER", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX"):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv(name, "1")
        with pytest.raises(BillingGuardError):
            assert_no_payg_credentials()
        monkeypatch.delenv(name)
