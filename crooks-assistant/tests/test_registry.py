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


def test_the_tool_block_offered_to_the_model_stays_within_its_budget():
    """Every description is read by the model on every turn. A budget, held here: the shared
    staging rules live in the system prompt once, not in each description."""
    import json

    from app.providers.max_agent_sdk import withheld_tools
    from app.tools import (  # noqa: F401
        analytics_tools,
        batch_tools,
        gmail_tools,
        gmail_writes,
        shopify_tools,
        shopify_writes,
    )

    specs = registry.all_specs()
    offered = [s for s in specs if s.name not in withheld_tools(specs, writes_enabled=True)]
    assert offered, "nothing offered"
    for spec in offered:
        assert len(spec.description) <= 600, f"{spec.name}: {len(spec.description)} chars of description"
        assert "spoken yes" not in spec.description, f"{spec.name}: the staging rules belong in the prompt"
    total = sum(len(json.dumps({"name": s.name, "description": s.description, "input_schema": s.input_schema})) for s in offered)
    # 16,000 held the narrow tools. The read layer (commerce_aggregate, commerce_query,
    # inventory_query, commerce_capabilities) is four tools for the questions that used to
    # need one each; its schemas are terse and the language's detail lives in
    # commerce_capabilities, called on demand. The four cost about 4.5 KB together. The
    # four batch tools (tags on and off a set of orders, a set of threads archived, a draft
    # to each customer) are the bulk versions of changes already offered singly; together
    # they cost about 1.7 KB and are withheld, like every write, while changes are off.
    #
    # 24,300 covers what the September session showed missing and nothing else:
    # shopify_order_address (the street address the owner asked for and was told did not
    # exist), gmail_find_in_email (a term checked across every thread, with coverage
    # reported) and batch_email_send (the bulk send, which shares batch_email_drafts's
    # schema object). About 1.7 KB together, half of it paid back by tightening the address
    # tool's per-field descriptions. The block is what every turn ON THE MODEL PATH pays —
    # a fast-lane turn pays none of it — and a tool added here has to earn its bytes.
    assert total <= 24_300, f"the tool block is {total} bytes"
    batch = sum(len(json.dumps({"name": s.name, "description": s.description, "input_schema": s.input_schema})) for s in offered if s.name.startswith("batch_"))
    # 2,300 covers the fifth batch tool — the same campaign as batch_email_drafts, sent
    # rather than saved — which shares its schema object and adds two lines of description.
    assert batch <= 2_300, f"the batch tools' schemas are {batch} bytes; the rules belong in the prompt"
    analytic = sum(len(json.dumps({"name": s.name, "description": s.description, "input_schema": s.input_schema})) for s in offered if s.name.startswith(("commerce_", "inventory_query")))
    assert analytic <= 5_000, f"the read layer's schemas are {analytic} bytes; the detail belongs in commerce_capabilities"
