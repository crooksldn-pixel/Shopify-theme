"""The tool and intent-family audit (§32).

Every registered tool and every routable intent family gets a row, and every column is read
from the thing that decides it rather than from a claim. The two rules this file exists to
keep:

* a tool is not "tested" because a unit test imports it — DIRECTLY TESTED means a test or a
  golden scenario actually calls that tool by name;
* the checked-in document is generated, so it cannot drift from the registries.
"""

from __future__ import annotations

import pathlib

from experience import tool_matrix

DOC = pathlib.Path(__file__).resolve().parents[1] / "docs" / "phase4" / "TOOL_MATRIX.md"


def test_every_registered_tool_has_a_row():
    from app.tools import registry

    tool_matrix.load()
    rows = {row["name"]: row for row in tool_matrix.tools()}
    assert set(rows) == set(registry.names())
    for row in rows.values():
        assert row["registered"] is True
        for column in tool_matrix.COLUMNS:
            assert column in row, f"{row['name']} has no {column!r}"


def test_every_routable_intent_family_has_a_row():
    from app.fastpath.intent import all_families

    tool_matrix.load()
    rows = {row["name"]: row for row in tool_matrix.families()}
    assert set(rows) == {f.name for f in all_families()}


def test_a_write_tool_declares_staging_and_verification():
    tool_matrix.load()
    for row in tool_matrix.tools():
        if row["read_write"] == "write":
            assert row["staging"], f"{row['name']} is a write with no staging"
            assert row["verification"], f"{row['name']} is a write with no verification"
        if row["read_write"] == "read":
            assert not row["staging"] and not row["verification"]


def test_no_tool_is_called_tested_because_a_unit_test_imported_it():
    """The column is derived from the tool's NAME appearing in a test or a scenario, and the
    matrix says which. A tool with no citation is reported as untested, which is honest."""
    tool_matrix.load()
    for row in tool_matrix.tools():
        assert bool(row["directly_tested"]) == bool(row["tested_by"]), row["name"]


def test_the_checked_in_document_is_the_generated_one():
    """Generated in a FRESH interpreter, which is how `make tool-matrix` runs it.

    Not in this one. Several tests register a tool of their own and do not take it away
    again, so by the time the suite reaches here the registry holds four that the shipped
    application does not — and a document compared against that is a document that can never
    be made to match. Spawning the generator also proves it works from a cold start, which is
    the only way anybody actually runs it.
    """
    import subprocess
    import sys

    root = DOC.resolve().parents[2]
    generated = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, '.'); from experience import tool_matrix; "
         "sys.stdout.write(tool_matrix.markdown())"],
        cwd=root, capture_output=True, text=True, timeout=180, check=False,
    )
    assert generated.returncode == 0, generated.stderr[-2000:]
    assert DOC.exists(), f"{DOC} has not been written"
    assert DOC.read_text(encoding="utf-8") == generated.stdout, (
        "docs/phase4/TOOL_MATRIX.md is out of date; regenerate it with `make tool-matrix`"
    )


def test_the_audit_never_mutates_anything():
    """Building the matrix reads registries and files. It must not call a handler."""
    from app.tools import registry

    tool_matrix.load()
    before = registry.names()
    tool_matrix.markdown()
    assert registry.names() == before
