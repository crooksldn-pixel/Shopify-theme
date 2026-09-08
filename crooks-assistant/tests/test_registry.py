from __future__ import annotations

import pytest

from app.tools import registry
from app.tools.gate import Tier


def test_all_day1_tools_are_registered():
    from app.tools import gmail_tools, mock, shopify_tools  # noqa: F401

    names = registry.names()
    for expected in (
        "mock_echo", "mock_slow", "mock_danger",
        "shopify_find_order", "shopify_order_detail", "shopify_list_orders",
        "shopify_find_customer", "shopify_inventory", "shopify_sales_summary",
        "shopify_product_info", "gmail_search", "gmail_read_thread",
    ):
        assert expected in names


def test_tiers_match_the_gate():
    from app.tools.gate import classify

    for spec in registry.all_specs():
        if spec.issued_id_args:
            continue  # need an issued id to be anything but denied; covered in test_actions.py
        assert classify(spec.name, {"query": "x", "product": "x", "word": "x"}).tier == spec.tier, spec.name


def test_duplicate_registration_is_an_error():
    with pytest.raises(ValueError):
        registry.tool(name="mock_echo", description="d", input_schema={"type": "object"})(lambda: None)


def test_normalise_tool_name():
    assert registry.normalise_tool_name("mcp__crooks__shopify_inventory") == "shopify_inventory"
    assert registry.normalise_tool_name("mcp__other__thing") == "thing"
    assert registry.normalise_tool_name("plain") == "plain"


async def test_invoke_unknown_tool():
    with pytest.raises(KeyError):
        await registry.invoke("nope", {}, timeout_s=1)


async def test_invoke_bad_args_is_a_tool_error():
    from app.tools import mock  # noqa: F401

    with pytest.raises(registry.ToolError):
        await registry.invoke("mock_echo", {"wrong": 1}, timeout_s=1)


def test_mcp_server_builds_from_registry():
    """With the SDK installed, the adapter must produce a server exposing every tool."""
    pytest.importorskip("claude_agent_sdk")
    from app.tools import mock  # noqa: F401

    async def dispatch(name, args):
        return "ok"

    server = registry.build_mcp_server(dispatch)
    assert server["type"] == "sdk"
    assert server["name"] == registry.MCP_SERVER_NAME
    # The SDK stores the tool list on the instance; count it.
    instance = server["instance"]
    tools = getattr(instance, "_tools", None) or getattr(instance, "tools", None)
    if tools is not None:
        assert len(tools) == len(registry.names())


def test_every_spec_has_an_object_schema():
    for spec in registry.all_specs():
        assert spec.input_schema.get("type") == "object", spec.name
        assert isinstance(spec.tier, Tier)


# --------------------------------------------------------------------------- per-tool ceiling

async def _patient(delay: float = 0.05) -> dict:
    import asyncio

    await asyncio.sleep(delay)
    return {"ok": True}


@pytest.fixture()
def patient_tool():
    """Registered for one test only: the gate treats any tool it does not know as RED, and
    the registry-wide tier test must keep seeing only the real ones."""
    registry.tool(
        name="test_patient_tool", description="slow on purpose",
        input_schema={"type": "object", "properties": {"delay": {"type": "number"}}},
        tier=Tier.GREEN, timeout_s=1.0,
    )(_patient)
    try:
        yield "test_patient_tool"
    finally:
        registry._REGISTRY.pop("test_patient_tool", None)


async def test_a_tool_may_declare_its_own_timeout_ceiling(patient_tool):
    """A Gmail search is a listing, a batched fetch and sometimes a credential refresh; the
    operator's 8 s default is the wrong bound for it. A tool's own ceiling replaces the
    default — and is still a hard bound."""
    assert registry.get(patient_tool).timeout_s == 1.0
    # The caller's tighter budget does not apply: the tool's own does.
    result = await registry.invoke(patient_tool, {"delay": 0.05}, timeout_s=0.01)
    assert result["ok"] is True
    # ...and the tool's own ceiling is enforced.
    with pytest.raises(registry.ToolError, match="did not respond within 1 seconds"):
        await registry.invoke(patient_tool, {"delay": 1.5}, timeout_s=30)


def test_gmail_tools_carry_their_own_ceiling():
    from app.tools import gmail_tools  # noqa: F401

    assert registry.get("gmail_search").timeout_s == gmail_tools.GMAIL_TIMEOUT_S
    assert registry.get("gmail_read_thread").timeout_s == gmail_tools.GMAIL_TIMEOUT_S
    assert registry.get("shopify_find_order").timeout_s is None, "the default still applies elsewhere"
