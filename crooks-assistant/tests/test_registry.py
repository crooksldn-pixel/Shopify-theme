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
        if spec.name in ("shopify_order_detail", "gmail_read_thread"):
            continue  # need an issued id to be anything but RED
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
