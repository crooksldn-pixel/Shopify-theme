"""Three tools that exist only to prove the gate works before anything real sits behind it.

Registered at M5 and kept afterwards: `make test` re-proves on every run that a RED tool cannot
execute, which is the one property that must never silently regress.
"""

from __future__ import annotations

import asyncio

from app.tools.gate import Tier
from app.tools.registry import tool

# Module-level counters. tests/test_gate.py asserts DANGER_CALLS never moves.
ECHO_CALLS = 0
SLOW_CALLS = 0
DANGER_CALLS = 0


def reset_counters() -> None:
    global ECHO_CALLS, SLOW_CALLS, DANGER_CALLS
    ECHO_CALLS = SLOW_CALLS = DANGER_CALLS = 0


@tool(
    name="mock_echo",
    description="Echo a word back. Diagnostic only.",
    input_schema={
        "type": "object",
        "properties": {"word": {"type": "string", "description": "The word to echo."}},
        "required": ["word"],
    },
    tier=Tier.GREEN,
)
async def mock_echo(word: str) -> dict:
    global ECHO_CALLS
    ECHO_CALLS += 1
    return {"echo": word}


@tool(
    name="mock_slow",
    description="Sleep for 12 seconds. Diagnostic only — exercises the tool timeout.",
    input_schema={"type": "object", "properties": {}},
    tier=Tier.GREEN,
)
async def mock_slow() -> dict:
    global SLOW_CALLS
    SLOW_CALLS += 1
    await asyncio.sleep(12)
    return {"slept": 12}


@tool(
    name="mock_danger",
    # Deliberately bland. If the description said "destructive", Claude would decline to call
    # it and the gate would never be exercised — and the point of this tool is to prove the
    # GATE blocks it, not that the model is polite.
    description="Run the mock danger diagnostic. Diagnostic only.",
    input_schema={"type": "object", "properties": {}},
    tier=Tier.RED,
)
async def mock_danger() -> dict:
    global DANGER_CALLS
    DANGER_CALLS += 1  # If this ever increments, the gate has failed and the build stops.
    return {"detonated": True}
