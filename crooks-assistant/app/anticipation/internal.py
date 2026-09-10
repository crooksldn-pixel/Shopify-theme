"""Internal reads: things the Mac can look up that are not model-facing tools.

§18 asks for "shipping/tracking context available internally" among the P1 background reads.
That context does not come from a registered tool — there is no shipping tool, because there is
no shipping provider (§20) — so it cannot travel through the read scheduler, which only knows
registered tools. It travels here instead, through a table of named async functions.

The table is closed and its contents are read-only by construction: each entry is a call into a
package that has no mutation in it. Nothing is dispatched by name from outside this module, and
a name the table does not hold is a skipped prediction rather than an import.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

log = logging.getLogger("crooks.anticipation")


async def _shipping_status(args: dict[str, Any]) -> Any:
    """The order's shipping state from whatever provider is connected — DISCONNECTED here."""
    from app.shipping import context_for

    context = await context_for(str(args.get("order_id") or ""))
    return context.public()


READS: dict[str, Callable[[dict[str, Any]], Awaitable[Any]]] = {
    "shipping_status": _shipping_status,
}


def known(name: str) -> bool:
    return name in READS


async def run(name: str, args: dict[str, Any]) -> Any:
    """One internal read, or None when there is no such read."""
    handler = READS.get(name)
    if handler is None:
        log.debug("no internal read called %s", name)
        return None
    return await handler(dict(args or {}))
