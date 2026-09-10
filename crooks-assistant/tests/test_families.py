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
    lines = families.words({
        family.key: {"label": "Test family", "state": "MISSING_SCOPE", "detail": "blocked — Shopify write_test scope missing"},
        "other": {"label": "Other", "state": "READY", "detail": "ready"},
    })
    assert any("Test family: MISSING_SCOPE" in line and "Do not attempt it" in line for line in lines)
    assert any(line == "- Other: READY." for line in lines)


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
