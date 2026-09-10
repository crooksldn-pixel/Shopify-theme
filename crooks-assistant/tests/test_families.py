"""The capability families: one table, three readers.

A family's state has more shapes than ready/blocked — written but the scope is missing, not
offered by the store, no provider connected, not built. These assert that a registered family
reaches /health and the manifest with its state, that the model is told the ones it must not
attempt, and that the state derivation from the per-operation table is right.
"""

from __future__ import annotations

import pytest

from app.capabilities import families


@pytest.fixture
def family():
    key = "test_family_zz"
    fam = families.register(families.CapabilityFamily(
        key=key, label="Test family", area="orders", what="a thing the tests can do",
        operations=("test_op",), scopes=("write_test",), state="READY",
    ))
    try:
        yield fam
    finally:
        families.REGISTRY.pop(key, None)


def test_a_state_must_be_one_of_the_seven():
    with pytest.raises(ValueError):
        families.register(families.CapabilityFamily(key="bad_zz", label="x", area="orders", what="x", state="MAYBE"))
    families.REGISTRY.pop("bad_zz", None)


@pytest.mark.asyncio
async def test_the_state_follows_the_operation_table(family):
    ready = await families.states(None, operations={"test_op": {"state": "ready", "detail": "ready", "scope": "write_test"}})
    assert ready[family.key]["state"] == "READY" and ready[family.key]["offerable"] is True
    missing = await families.states(None, operations={"test_op": {"state": "blocked", "detail": "blocked — Shopify write_test scope missing", "scope": "write_test"}})
    assert missing[family.key]["state"] == "MISSING_SCOPE" and missing[family.key]["scope"] == "write_test" and not missing[family.key]["offerable"]
    off = await families.states(None, operations={"test_op": {"state": "disabled", "detail": "disabled — CROOKS_WRITES_ENABLED=false", "scope": "write_test"}})
    assert off[family.key]["state"] == "READ_ONLY"


@pytest.mark.asyncio
async def test_a_probe_has_the_last_word_and_a_failing_probe_is_a_state():
    async def not_offered(_runtime):
        return {"state": "NOT_SUPPORTED_BY_STORE", "detail": "the store has no store credit"}

    async def broken(_runtime):
        raise RuntimeError("no network")

    for key, probe in (("probe_zz", not_offered), ("broken_zz", broken)):
        families.register(families.CapabilityFamily(key=key, label=key, area="customers", what="x", state="READY", probe=probe))
    try:
        table = await families.states(None, operations={})
        assert table["probe_zz"]["state"] == "NOT_SUPPORTED_BY_STORE"
        assert table["broken_zz"]["state"] == "TEMPORARILY_UNAVAILABLE" and "RuntimeError" in table["broken_zz"]["detail"]
    finally:
        families.REGISTRY.pop("probe_zz", None)
        families.REGISTRY.pop("broken_zz", None)


def test_the_model_is_told_what_not_to_attempt(family):
    table = {
        family.key: {"label": "Test family", "state": "MISSING_SCOPE", "detail": "blocked — Shopify write_test scope missing"},
        "other": {"label": "Other", "state": "READY", "detail": "ready"},
    }
    lines = families.words(table)
    assert any("Test family: MISSING_SCOPE" in line and "Do not attempt it" in line for line in lines)
    # The ready ones are NOT on the prompt: they are the tools the model is offered, and
    # `runtime.withheld_by_family` has taken the rest away, so a line saying "READY" is model
    # context spent to say nothing — fifteen of them, every turn (brief section 25).
    assert not any("Other" in line for line in lines)
    # The surfaces the OWNER reads want the whole list, and ask for it.
    everything = families.words(table, only_unavailable=False)
    assert any(line == "- Other: READY." for line in everything)


def test_the_scope_to_grant_is_named_even_when_the_reason_does_not_say_it(family):
    """The scope is the one thing the owner cannot work out from the tablet; it has to be in
    the words whether or not Shopify's own message mentions it."""
    lines = families.words({family.key: {"label": "Test family", "state": "MISSING_SCOPE",
                                         "detail": "the shop has not granted it", "scope": "write_test"}})
    assert any("write_test" in line for line in lines)
    # And never twice when it does.
    once = families.words({family.key: {"label": "Test family", "state": "MISSING_SCOPE",
                                        "detail": "missing the write_test scope", "scope": "write_test"}})
    assert once and once[0].count("write_test") == 1


def test_the_manifest_carries_the_families(family):
    from app.capabilities import manifest

    built = manifest.build(build_id="t", writes_enabled=True)
    rows = {f["key"]: f for f in built["families"]}
    assert family.key in rows and rows[family.key]["state"] == "READY" and rows[family.key]["scopes"] == ["write_test"]
    # A family changing state is a build change the delta can see.
    a = manifest.fingerprint(built)
    built["families"] = [dict(f, state="NOT_IMPLEMENTED") if f["key"] == family.key else f for f in built["families"]]
    assert manifest.fingerprint(built) != a


def test_every_family_module_loads():
    from app.families import load_all

    loaded = load_all()
    assert isinstance(loaded, list)


# ------------------------------------------------- the capabilities that already existed


def _core_table():
    """Every family, with every tool module imported — the registry only holds what has been
    imported, and app/runtime.py imports the tools before the families."""
    import app.tools.analytics_tools  # noqa: F401
    import app.tools.gmail_tools  # noqa: F401
    import app.tools.gmail_writes  # noqa: F401
    import app.tools.shopify_tools  # noqa: F401
    import app.tools.shopify_writes  # noqa: F401
    from app.capabilities import families
    from app.families import load_all

    load_all()
    return {f.key: f for f in families.all_families()}


def test_every_existing_write_operation_belongs_to_a_named_family():
    """The family table was built for Phase 3's additions and started empty, so /health
    listed nothing and the settings sheet could say nothing about the fourteen write
    operations that already worked. A manifest that lists only the new things is not one."""
    from app.tools import registry

    families = _core_table()
    claimed = {op for f in families.values() for op in f.operations}
    registered = {s.write.operation for s in registry.all_specs() if s.write is not None}
    assert registered, "no write tools are registered at all — the check would pass vacuously"
    assert registered <= claimed, f"no family names these operations: {sorted(registered - claimed)}"


def test_every_read_tool_the_model_is_offered_belongs_to_a_named_family():
    from app.tools import registry

    families = _core_table()
    claimed = {tool for f in families.values() for tool in f.tools}
    reads = {
        s.name for s in registry.all_specs()
        if s.write is None and s.batch is None and not s.name.startswith("mock_")
    }
    assert reads <= claimed, f"no family names these read tools: {sorted(reads - claimed)}"


async def test_a_write_family_reads_read_only_when_changes_are_off():
    """Derived, not declared: the family says READY, and the per-operation table — which knows
    the store, the scopes and whether writes are switched on — is what turns it into
    READ_ONLY or MISSING_SCOPE. This is what the settings sheet shows the owner."""
    from app.capabilities import families

    class Runtime:
        pass

    off = {op: {"state": "disabled", "detail": "changes are switched off on this Mac"}
           for op in ("order_cancel", "refund_create", "gmail_send_reply")}
    table = await families.states(Runtime(), operations=off)
    assert table["order_cancel"]["state"] == "READ_ONLY"
    assert "switched off" in table["order_cancel"]["detail"]
    assert table["email_sends"]["state"] == "READ_ONLY"
    assert table["order_cancel"]["offerable"] is False
    # A read family has no operations to derive from and is unaffected.
    assert table["order_reads"]["state"] == "READY" and table["order_reads"]["offerable"] is True


async def test_a_missing_scope_names_the_scope_to_grant():
    from app.capabilities import families

    class Runtime:
        pass

    blocked = {"inventory_set": {"state": "blocked", "detail": "the app is missing the write_inventory scope",
                                 "scope": "write_inventory"}}
    table = await families.states(Runtime(), operations=blocked)
    assert table["inventory_set"]["state"] == "MISSING_SCOPE"
    assert table["inventory_set"]["scope"] == "write_inventory"


def test_the_families_that_already_worked_never_withhold_a_tool_from_the_model():
    """`withheld_by_family` exists to stop the model attempting what the store cannot do. It
    must not take away anything that worked before this table existed: a family with no tools
    of its own withholds nothing, and a READY one withholds nothing either."""
    from app.capabilities.families import OFFERABLE

    families = _core_table()
    for key, family in families.items():
        if family.state in OFFERABLE:
            continue
        assert not family.tools, f"{key} is not READY and names tools that would be withheld: {family.tools}"
