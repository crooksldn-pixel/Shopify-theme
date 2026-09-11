"""The workspace that arrives in pieces.

`turn_c8eb4cffe077` — "look up today's orders and today's emails and see if anything
correlates" — took **7,975 ms to first cards**. Not to the answer: to the first pixel of
content. `shopify_list_orders`, then `gmail_search`, then `gmail_read_thread`, and only when
the last of them came back was anything drawn at all. Session-wide the Mac spent 17,302 ms
reading and the owner spent 13,388 ms waiting, and he said what it felt like: the system
"waits and then dumps a large chunk".

The read graph is not the problem. Running it in one wave is already what `app/reads/
scheduler.py` does. The problem is that the SCREEN waited for the graph, because `present()`
is called once, at the end, over the whole list of calls — so the first fact and the last fact
arrive together however fast the reads were.

This module is the other half: a workspace that exists from the first moment and fills in.

    shell            the frame and a skeleton of each card that is coming     ~0 ms
    first fact       the first read lands; its card takes the skeleton's place
    next section     the second read lands; its card is patched in beside it
    complete         the turn returns; what changed is patched, what did not is NOT redrawn

Four numbers, and they are the point of the exercise (§7, §25):

    time_to_shell                    when there was a working screen
    time_to_first_fact               when the first real value was on it
    time_to_first_useful_workspace   when it could be used — a record, not a spinner
    time_to_complete_workspace       when nothing more was coming

They live beside `facts_ms` / `workspace_ms` / `prose_wait_ms` in the turn's performance
record rather than replacing them: those three measure the MAC (when it held the data, when
it had built the cards, how long the prose took afterwards), and these four measure the GLASS.

What this module may not do, and structurally cannot:

* It never reads. `observe` is handed a result a read already returned.
* It never mutates a session, issues an id, or stages a change. The cards it stages are built
  by `present()` with no session at all, so nothing is remembered twice and no id is issued
  before the turn's own presentation issues it.
* It never invents a value. A skeleton carries a count and a word; every other field on every
  card comes from `app/presentation.py`, key by key, as it always has.
* A failure here is never a failed turn. Every public entry point is called inside a guard at
  its caller, and everything here is pure bookkeeping over payloads that already exist.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.render import ADDED, DATA, Patch, RenderLedger, render_id

log = logging.getLogger("crooks.progressive")

# What each read is going to put on the screen, so a skeleton can stand there while it runs.
# Read alongside `presentation._from_result`, which is the code that decides for real: the
# test `test_every_shell_promises_a_card_the_renderer_can_draw` holds the two together, so a
# read that changes its card cannot leave a skeleton promising the old one.
SHELL_OF_TOOL: dict[str, str] = {
    "shopify_list_orders": "order_list",
    "shopify_find_order": "order",
    "shopify_order_detail": "order",
    "shopify_customer_history": "customer",
    "shopify_find_customer": "customer",
    "shopify_inventory": "inventory",
    "shopify_sales_summary": "sales_summary",
    "shopify_product_info": "product",
    "gmail_search": "email_list",
    "gmail_read_thread": "email_thread",
}

# The words on a skeleton. Never a value, never a count of anything that has not been read —
# the kind of thing that is coming, and that is all it is allowed to say.
SHELL_WORDS: dict[str, tuple[str, int]] = {
    "order": ("Order", 4),
    "order_list": ("Orders", 4),
    "customer": ("Customer", 3),
    "customer_list": ("Customers", 3),
    "product": ("Product", 3),
    "inventory": ("Stock", 4),
    "sales_summary": ("Sales", 3),
    "email_list": ("Email", 4),
    "email_thread": ("Email thread", 3),
}

# Which of the fast lane's families already knows what it is about to draw, so the shell can
# be up before the first read has even been issued. A family that is not here gets its
# skeleton when its first read starts, which is still far short of 7,975 ms.
SHELL_OF_FAMILY: dict[str, tuple[str, ...]] = {
    "order_lookup": ("order",),
    "order_reopen": ("order",),
    "order_list_period": ("order_list",),
    "order_status_lookup": ("order",),
    "order_address_lookup": ("order",),
    "delayed_orders": ("order_list",),
    "customer_history_lookup": ("customer",),
    "customer_purchase_lookup": ("customer",),
    "sales_breakdown_period": ("sales_summary",),
    "inbox_state": ("email_list",),
    "needs_reply": ("email_list",),
    "stock_cover_analysis": ("inventory",),
}

# A card that is worth looking at: it is about a record, or it carries rows. An error, the
# assistant's own sentence and the context stack are none of those, which is why a turn that
# drew only those is the failure §8 is about rather than a workspace.
NOT_USEFUL = frozenset({"assistant", "error", "context_stack"})
ROW_KEYS = ("orders", "threads", "messages", "customers", "products", "rows", "items", "metrics", "points", "cells")

# Bounds. The patch log is read by a tablet that polls every 400 ms and may miss a poll; it is
# not a transcript, and a turn that produced sixty patches has a bug upstream.
MAX_PATCHES = 60
MAX_LIVE = 24


def _useful(item: dict[str, Any]) -> bool:
    kind = str(item.get("type") or "")
    data = item.get("data")
    if kind in NOT_USEFUL or not isinstance(data, dict):
        return False
    if data.get("shell") is True:
        return False
    if any(isinstance(data.get(key), list) and data[key] for key in ROW_KEYS):
        return True
    from app.render import key_of

    return bool(key_of(item))


def shell_item(kind: str, *, title: str = "", rows: int = 0) -> dict[str, Any]:
    """One skeleton card, in the same `{type, data}` shape as every other card.

    `shell` is the whole of what makes it one. The tablet draws a bounded placeholder for any
    card whose data says so (web/ui.js `skeletonCard`), which is why this adds nothing to the
    vocabulary: there is no skeleton type to keep in step with anything.
    """
    words, count = SHELL_WORDS.get(kind, ("Reading", 3))
    return {
        "type": kind,
        "data": {"shell": True, "loading": True, "title": str(title or words)[:40], "placeholder": int(rows or count)},
    }


@dataclass(slots=True)
class Workspace:
    """One turn's screen, as it fills in. Owned by the session that asked."""

    session_id: str
    turn_id: str = ""
    branch_id: str = ""
    clock: Callable[[], float] = time.perf_counter
    started: float = 0.0
    ledger: RenderLedger = field(default_factory=RenderLedger)
    patches: list[Patch] = field(default_factory=list)
    revision: int = 0
    shell_ms: float | None = None
    first_fact_ms: float | None = None
    first_useful_ms: float | None = None
    complete_ms: float | None = None
    finished: bool = False

    def __post_init__(self) -> None:
        if not self.started:
            self.started = self.clock()

    # ----------------------------------------------------------------- the phases

    def at_ms(self) -> float:
        return max(0.0, (self.clock() - self.started) * 1000.0)

    def shell(self, kinds: tuple[str, ...] | list[str]) -> list[Patch]:
        """The frame, and a skeleton for each card the Mac already knows is coming."""
        now = self.at_ms()
        if self.shell_ms is None:
            self.shell_ms = now
        items = [shell_item(kind) for kind in list(kinds)[:4] if kind in SHELL_WORDS]
        return self._record(self.ledger.stage(items, at_ms=now))

    def starting(self, tool: str) -> list[Patch]:
        """A read has begun. Where its card is known, its skeleton goes up now.

        Not when a real card of that kind is already on the glass: an order found and then
        read in full is one card being filled in, and a skeleton under it would be exactly
        the duplicate this pass exists to remove.
        """
        kind = SHELL_OF_TOOL.get(str(tool or ""))
        if not kind or self.ledger.has_real(kind):
            return []
        now = self.at_ms()
        if self.shell_ms is None:
            self.shell_ms = now
        return self._record(self.ledger.stage([shell_item(kind)], at_ms=now))

    def facts(self, items: list[dict[str, Any]]) -> list[Patch]:
        """A read has landed. Its cards take their skeletons' places, or are added."""
        now = self.at_ms()
        patches = self._record(self.ledger.stage(list(items), at_ms=now))
        for patch in patches:
            if patch.op not in (ADDED, DATA) or patch.item is None:
                continue
            if self.first_fact_ms is None:
                self.first_fact_ms = now
            if self.first_useful_ms is None and _useful(patch.item):
                self.first_useful_ms = now
        return patches

    def complete(self, items: list[dict[str, Any]]) -> list[Patch]:
        """The turn's own presentation, reconciled against what is already on the glass.

        This is the moment the old code redrew everything. What it does now is compare: the
        cards that are unchanged produce nothing at all, the ones that gained a rail or an
        enrichment are patched in place, and any skeleton whose read never landed is taken
        down rather than left saying "reading…".
        """
        now = self.at_ms()
        patches = self._record(self.ledger.stage(list(items), at_ms=now))
        for patch in patches:
            if patch.op in (ADDED, DATA) and patch.item is not None:
                if self.first_fact_ms is None:
                    self.first_fact_ms = now
                if self.first_useful_ms is None and _useful(patch.item):
                    self.first_useful_ms = now
        patches += self._record(self.ledger.drop_shells(at_ms=now))
        self.complete_ms = now
        self.finished = True
        return patches

    # ----------------------------------------------------------------- what the glass reads

    def _record(self, patches: list[Patch]) -> list[Patch]:
        if not patches:
            return []
        self.patches.extend(patches)
        if len(self.patches) > MAX_PATCHES:
            del self.patches[: len(self.patches) - MAX_PATCHES]
        self.revision = self.patches[-1].seq
        return patches

    def public(self, since: int = 0) -> dict[str, Any]:
        """The patches the tablet has not seen, and where the workspace now stands.

        `since` is the last `seq` it applied. A tablet that missed a poll catches up; one that
        has seen everything is told so and draws nothing, which is the same rule as §25's:
        no visible change means no work.
        """
        try:
            cursor = int(since)
        except (TypeError, ValueError):
            cursor = 0
        pending = [p.public() for p in self.patches if p.seq > cursor]
        return {
            "revision": self.revision,
            "turn_id": self.turn_id,
            "branch_id": self.branch_id,
            "complete": bool(self.finished),
            "patches": pending,
            # A tablet that fell far enough behind that the log no longer reaches its cursor
            # must redraw from the turn's payload rather than apply half a sequence.
            "gap": bool(pending and self.patches and pending[0]["seq"] > cursor + 1 and cursor > 0),
            "timings_ms": self.timings(),
            "renders": self.ledger.report(),
        }

    def timings(self) -> dict[str, float | None]:
        return {
            "time_to_shell": _ms(self.shell_ms),
            "time_to_first_fact": _ms(self.first_fact_ms),
            "time_to_first_useful_workspace": _ms(self.first_useful_ms),
            "time_to_complete_workspace": _ms(self.complete_ms),
        }


def _ms(value: float | None) -> float | None:
    return None if value is None else round(float(value), 1)


# --------------------------------------------------------------------------- the live ones

# One workspace per half of one conversation, bounded, oldest evicted. Held here rather than
# on the Session because it is about a TURN: it is built when the turn starts and read by
# /state while that turn runs, and a session that is asleep should not be holding one.
_LIVE: OrderedDict[str, Workspace] = OrderedDict()


def _key(session_id: str, branch_id: str = "") -> str:
    return f"{str(session_id or '')}/{str(branch_id or '')}"


def begin(session_id: str, *, turn_id: str = "", branch_id: str = "", family: str = "",
          clock: Callable[[], float] | None = None) -> Workspace:
    """A turn has started: a working shell, now, before anything has been read."""
    workspace = Workspace(
        session_id=str(session_id or ""), turn_id=str(turn_id or ""), branch_id=str(branch_id or ""),
        clock=clock or time.perf_counter,
    )
    _LIVE[_key(session_id, branch_id)] = workspace
    while len(_LIVE) > MAX_LIVE:
        _LIVE.popitem(last=False)
    workspace.shell(SHELL_OF_FAMILY.get(str(family or ""), ()))
    return workspace


def current(session_id: str, branch_id: str = "") -> Workspace | None:
    """The workspace a poll should read: this half's, or the session's only one."""
    found = _LIVE.get(_key(session_id, branch_id))
    if found is not None:
        return found
    prefix = f"{str(session_id or '')}/"
    mine = [w for k, w in _LIVE.items() if k.startswith(prefix)]
    return mine[-1] if len(mine) == 1 else None


def forget(session_id: str, branch_id: str = "") -> None:
    _LIVE.pop(_key(session_id, branch_id), None)


def reset() -> None:
    """For tests, and for a Mac that has just been restarted."""
    _LIVE.clear()


def _workspace_for(session: Any, branch_id: str = "") -> Workspace | None:
    session_id = str(getattr(session, "session_id", "") or "")
    if not session_id:
        return None
    return current(session_id, branch_id or str(getattr(session, "focused_branch", "") or ""))


def starting(session: Any, tool: str) -> None:
    """A read has been issued. Never raises: a skeleton is not worth a failed turn."""
    try:
        workspace = _workspace_for(session)
        if workspace is not None and not workspace.finished:
            workspace.starting(tool)
    except Exception as exc:  # noqa: BLE001 — bookkeeping must not break a read
        log.debug("progressive shell for %s failed: %s", tool, type(exc).__name__)


def observe(session: Any, name: str, result: Any) -> None:
    """A read has landed: its cards, staged now, patched in place on the glass.

    `present()` is called with NO session, deliberately. It shapes the payload and nothing
    else — nothing is remembered onto the context stack and no id is issued, because the
    turn's own presentation does both when the turn ends and doing them twice would put a
    record on the stack the owner never saw and issue an id nobody was shown.
    """
    try:
        workspace = _workspace_for(session)
        if workspace is None or workspace.finished or not isinstance(result, dict):
            return
        from app.presentation import present
        from app.providers.base import ToolCall

        items = present([ToolCall(name=str(name), args={}, ok=True, result=result)])
        if items:
            workspace.facts(items)
    except Exception as exc:  # noqa: BLE001 — a card that could not be staged early still arrives late
        log.debug("progressive facts for %s failed: %s", name, type(exc).__name__)


def complete(session: Any, items: list[dict[str, Any]], *, branch_id: str = "") -> dict[str, Any]:
    """The turn's final cards, reconciled. Returns the numbers for the performance record."""
    try:
        workspace = _workspace_for(session, branch_id)
        if workspace is None:
            return {}
        patches = workspace.complete(list(items or []))
        return {
            **workspace.timings(),
            "renders": workspace.ledger.report(),
            "revision": workspace.revision,
            "turn_id": workspace.turn_id,
            # The reconciliation itself, so the turn's own response can carry it: the tablet
            # stops polling the moment the turn answers, and these are the patches that would
            # otherwise never be collected.
            "patches": [p.public() for p in patches],
        }
    except Exception as exc:  # noqa: BLE001
        log.debug("progressive reconciliation failed: %s", type(exc).__name__)
        return {}


def suppressed_of(patches: list[Patch]) -> int:
    return sum(1 for p in patches if p.op == DATA)


def identities(items: list[dict[str, Any]]) -> list[str]:
    """The render identities of a list of cards, in order. Used by the tablet's own tests and
    by the turn payload, so the glass and the Mac name the same cards the same way."""
    out: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            found = render_id(item)
            if found:
                out.append(found)
    return out
