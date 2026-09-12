"""The broken states the owner actually held, lifted off the physical timeline (§30).

Phase 4's browser gate was nineteen invented fixtures and it was green all the way through an
evening in which the tablet swallowed sixty-three taps, drew seven profile pages for a one-line
answer, and answered a request for a customer's orders with an empty inbox. The brief's own
verdict: *"A screenshot suite that never reaches the broken state is not sufficient."* The
fixtures in this module are the broken states, and nothing in them was imagined — every shape,
height, tab, tab selection, collision count, refusal code and tap duration here was read out of
`logs/test-sessions/ts-20260911-201129-phase-4-live-tablet-test.jsonl` (1,365 events), by
`derive()` below, at the sequence numbers each state names.

THE RAW FILE HAS REAL CUSTOMERS IN IT. Nothing from it reaches this module or the JSON beside
it except numbers and type names:

  * a customer/order/product id becomes `cust-6343` — its last four digits and nothing else,
    which is the same truncation the forensics document uses to prove two records differ;
  * a name becomes an invented one from `INVENTED`, chosen by that truncated id so the same
    record is the same invented person in every fixture and across runs;
  * an email address is never carried at all — the addresses in the fixtures are
    `@example.com` and were typed here.

`assert_clean()` is the enforcement, and `tests/test_live_replay.py` runs it over every
committed fixture file: an `@` outside `example.com`, or any of the real ids, fails the suite.

Two halves, like `web/collide.js`:

  * `derive(rows)` is arithmetic over parsed events. It produces the `observed` block of every
    state — the measurements. It needs the raw file, which is gitignored, so it runs only where
    the file is (the owner's Mac, and any machine the session is copied to).
  * `live_states.json` beside this file is the committed fixture: the derived `observed` blocks,
    plus the `ui` payloads and `expect` clauses that make each state replayable in a browser.
    `scripts/browser/replay.js` reads that JSON and nothing else.

When both are present the test re-derives and compares, so a fixture that has drifted away from
what the tablet recorded is a failure rather than a comfortable green.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_SESSION = "ts-20260911-201129-phase-4-live-tablet-test"
#: The committed fixture. Read by Python and by `scripts/browser/replay.js`.
STATES_JSON = Path(__file__).resolve().parent / "live_states.json"
#: The raw timeline. Gitignored on purpose: it has real customers in it.
RAW_DEFAULT = ROOT / "logs" / "test-sessions" / f"{SOURCE_SESSION}.jsonl"

#: The tablet's own viewport, from every `tablet_render` in the session.
VIEWPORT = {"w": 601, "h": 889, "dpr": 1.33}

#: Invented people, in a fixed order. An id's last four digits pick one, so the same record is
#: the same invented person in every fixture and in every run. None of these is a real customer.
INVENTED = (
    "Rowan Pike", "Marta Vasquez", "Dev Achari", "Nina Okafor", "Casper Lund",
    "Priya Raman", "Tobias Frei", "Esme Calloway", "Yusuf Demir", "Greta Lindqvist",
    "Ines Moreau", "Bartek Nowak",
)


class TimelineMissing(RuntimeError):
    """The raw timeline is not on this machine. Derivation is skipped, never faked."""


def raw_path() -> Path:
    """Where the timeline is. `CROOKS_LIVE_TIMELINE` overrides, for a copy kept elsewhere."""
    override = os.environ.get("CROOKS_LIVE_TIMELINE", "").strip()
    return Path(override) if override else RAW_DEFAULT


def read_rows(path: Path | None = None) -> list[dict[str, Any]]:
    where = path or raw_path()
    if not where.exists():
        raise TimelineMissing(f"no timeline at {where}")
    rows: list[dict[str, Any]] = []
    with where.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---- scrubbing ---------------------------------------------------------------------------

_ID_TAIL = re.compile(r"(\d{4})$")
_KIND_PREFIX = {"Customer": "cust", "Order": "order", "Product": "prod", "ProductVariant": "var"}


def scrub_ref(ref: str) -> str:
    """`gid://shopify/Customer/11410640896343` -> `cust-6343`. Last four digits, nothing else.

    Four digits is what the forensics document uses to prove the seven cards were seven
    different customers, and four digits of a Shopify id identify nobody.
    """
    text = str(ref or "")
    if not text:
        return ""
    kind = ""
    for word, short in _KIND_PREFIX.items():
        if f"/{word}/" in text:
            kind = short
            break
    tail = _ID_TAIL.search(text)
    return f"{kind or 'ref'}-{tail.group(1) if tail else '0000'}"


def invented_name(scrubbed_ref: str) -> str:
    """An invented person for a scrubbed id, stable across runs."""
    digits = "".join(ch for ch in str(scrubbed_ref) if ch.isdigit()) or "0"
    return INVENTED[int(digits) % len(INVENTED)]


def invented_email(scrubbed_ref: str) -> str:
    name = invented_name(scrubbed_ref).lower().replace(" ", ".")
    return f"{name}@example.com"


#: Ids from the raw file that must never appear in a committed fixture. Full ids, not fragments:
#: the four-digit tails are exactly what the fixtures are allowed to carry.
_FORBIDDEN = re.compile(r"\b\d{13,}\b")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")


def assert_clean(text: str, where: str = "fixture") -> None:
    """No real ids and no addresses outside the reserved example domains. Raises if either."""
    long_id = _FORBIDDEN.search(text)
    if long_id:
        raise AssertionError(f"{where}: a full id reached a committed fixture: {long_id.group(0)}")
    for found in _EMAIL.findall(text):
        domain = found.rsplit("@", 1)[-1].lower()
        if not any(domain == allowed or domain.endswith("." + allowed) for allowed in _ALLOWED_EMAIL_DOMAINS):
            raise AssertionError(f"{where}: an email address reached a committed fixture: {found}")


# ---- derivation --------------------------------------------------------------------------

def _by_seq(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(r["seq"]): r for r in rows if "seq" in r}


def _cards(render: dict[str, Any]) -> list[dict[str, Any]]:
    """A render's cards, as shapes: type, height, tabs, which tab is open, a truncated ref."""
    out = []
    for card in render.get("cards") or []:
        shape = {"type": card.get("type", ""), "height": card.get("height")}
        if card.get("ref"):
            shape["ref"] = scrub_ref(card["ref"])
        if card.get("tabs"):
            shape["tabs"] = list(card["tabs"])
        if card.get("tab_active"):
            shape["tab_active"] = card["tab_active"]
        if card.get("sections"):
            shape["sections"] = list(card["sections"])
        if card.get("actions"):
            shape["actions"] = [a.get("id", "") for a in card["actions"]]
        out.append(shape)
    return out


def _render(render: dict[str, Any]) -> dict[str, Any]:
    doc = render.get("document") or {}
    over = render.get("overflow") or {}
    return {
        "seq": int(render["seq"]),
        "at": render.get("iso", "")[-8:],
        "screen": render.get("screen", "") or render.get("name", ""),
        "cards": _cards(render),
        "cards_height": doc.get("cards_height"),
        "cards_visible": doc.get("cards_visible"),
        "collisions": over.get("collisions"),
        "long_scroll": over.get("long_scroll"),
        "viewport": {
            "w": (render.get("viewport") or {}).get("w"),
            "h": (render.get("viewport") or {}).get("h"),
            "dpr": round(float((render.get("viewport") or {}).get("dpr") or 0), 2),
        } if render.get("viewport") else None,
    }


def derive(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The `observed` block of every live state, measured off the timeline.

    Keyed by the fixture id used in `live_states.json`. Every number in here came out of the
    file; every string that could name a person has been through `scrub_ref`.
    """
    seqs = _by_seq(rows)
    holds = [r for r in rows if r.get("kind") == "tablet_hold"]
    navs = [r for r in rows if r.get("kind") == "tablet_navigate"]
    commands = [r for r in rows if r.get("kind") == "command"]
    renders = [r for r in rows if r.get("kind") == "tablet_render" and r.get("cards") is not None]

    out: dict[str, dict[str, Any]] = {}

    # --- D-4: a list question answered with seven full profile pages -----------------------
    out["returning_customers_seven_cards"] = _render(seqs[236]) | {
        "distinct_refs": len({c.get("ref") for c in _cards(seqs[236]) if c.get("ref")}),
        "customer_history_calls": sum(
            1 for r in rows
            if r.get("kind") == "tool_requested" and r.get("turn_id") == seqs[236].get("turn_id")
            and r.get("tool") == "shopify_customer_history"
        ),
    }

    # --- "you just pulled up two in the same UI": one customer, two cards ------------------
    dup = _render(seqs[647])
    refs = [c.get("ref") for c in dup["cards"] if c.get("ref")]
    dup["same_ref_twice"] = len(refs) == 2 and refs[0] == refs[1]
    out["duplicate_customer_surface"] = dup

    # --- D-3: a customer workspace request that rendered only an email list ----------------
    out["customer_history_gmail_email_list_only"] = _render(seqs[723]) | {
        "tools": sorted({
            r.get("tool") for r in rows
            if r.get("kind") == "tool_requested" and r.get("turn_id") == seqs[723].get("turn_id")
        }),
    }

    # --- D-5: "can you expand his customer page?" -> a 1,014px capability card -------------
    out["customer_page_expansion_capability"] = _render(seqs[270])

    # --- D-2: every customer card in the session opened on Email ---------------------------
    tab_actives: dict[str, int] = {}
    for render in renders:
        for card in render.get("cards") or []:
            if card.get("type") == "customer" and card.get("tab_active"):
                tab_actives[card["tab_active"]] = tab_actives.get(card["tab_active"], 0) + 1
    email_tab_taps = sum(
        1 for r in rows
        if r.get("kind") == "tablet_tab" and r.get("label") == "Email" and r.get("name") == "customer"
    )
    out["empty_email_section"] = _render(seqs[237]) | {
        "customer_cards_by_active_tab": dict(sorted(tab_actives.items())),
        "email_tab_taps_on_a_customer": email_tab_taps,
    }

    # --- D-1: the branch bar under the full-viewport voice target -------------------------
    # The two-branch window of the second sitting: forked 23:10:55, merged 23:11:46. Inside it
    # the branch bar carried Split/Merge/Close and the orb screen measured collisions.
    forked = next(r for r in rows if r.get("kind") == "branch_forked" and int(r["seq"]) == 1217)
    merged = next(r for r in rows if r.get("kind") == "branch_merged" and int(r["seq"]) == 1287)
    orb_hits = [
        {"seq": int(r["seq"]), "at": r.get("iso", "")[-8:], "collisions": (r.get("overflow") or {}).get("collisions")}
        for r in renders
        if r.get("screen") == "orb" and ((r.get("overflow") or {}).get("collisions") or 0) > 0
    ]
    out["split_overlap_branch_under_voice"] = _render(seqs[1272]) | {
        "two_halves_from": forked.get("iso", "")[-8:],
        "two_halves_until": merged.get("iso", "")[-8:],
        "orb_renders_with_collisions": len(orb_hits),
        "worst_collision_count": max((h["collisions"] or 0) for h in orb_hits) if orb_hits else 0,
        "hold_targets": sorted({r.get("target") for r in holds if r.get("target")}),
    }

    # --- the merge/close tap: every one in the session was a GESTURE, never a control ------
    branch_navs = [r for r in navs if r.get("nav") in ("merge", "split")]
    out["merge_close_tap"] = {
        "seq": 1293,
        "at": seqs[1293].get("iso", "")[-8:],
        "branch_navigations": [{"nav": r.get("nav"), "by": r.get("name")} for r in branch_navs],
        "by_gesture": sum(1 for r in branch_navs if r.get("name") == "gesture"),
        "by_control": sum(1 for r in branch_navs if r.get("name") not in ("gesture", None)),
        "merge_status": seqs[1294].get("status"),
        "render_before": _render(seqs[1292]),
    }

    # --- D-1's evidence: the dock touch burst ---------------------------------------------
    releases = [r for r in holds if r.get("phase") == "release" and r.get("outcome") == "sent"]
    burst = [r for r in releases if "23:08:3" in r.get("iso", "") or "23:08:41" in r.get("iso", "")]
    burst = [r for r in burst if (r.get("ms") or 0) <= 140]
    out["dock_touch_burst"] = {
        "from": burst[0].get("iso", "")[-8:] if burst else "",
        "until": burst[-1].get("iso", "")[-8:] if burst else "",
        "taps": len(burst),
        "ms": [int(r.get("ms") or 0) for r in burst],
        "every_one_sent_a_recording": all(r.get("outcome") == "sent" for r in burst),
        "hold_starts": sum(1 for r in holds if r.get("phase") == "start"),
        "hold_starts_on_dock": sum(1 for r in holds if r.get("phase") == "start" and r.get("target") == "dock"),
        "sent_under_200ms": sum(1 for r in releases if (r.get("ms") or 0) < 200),
        "recordings_too_short": sum(1 for r in rows if r.get("kind") == "tablet_recording_too_short"),
    }

    # --- D-6: a control offered with nothing behind it ------------------------------------
    refusal = next(r for r in commands if r.get("command") == "open.entity" and r.get("ok") is False)
    out["refused_open_entity_half_empty"] = {
        "seq": int(refusal["seq"]),
        "at": refusal.get("iso", "")[-8:],
        "command": refusal.get("command"),
        "ok": refusal.get("ok"),
        "code": refusal.get("code"),
        "then_rendered": (seqs[1359].get("items") or []),
        "then_named": seqs[1359].get("name"),
        "entity_kind": (seqs[1357].get("name") or ""),
        "entity_ref": scrub_ref(seqs[1357].get("entity") or ""),
    }

    # --- D-7: Home accepted every time and arrived nowhere --------------------------------
    home_navs = [r for r in navs if r.get("nav") == "home"]
    window = [r for r in home_navs if r.get("iso", "").endswith(("20:15:17", "20:15:18", "20:15:19", "20:15:20"))]
    home_cmds = [r for r in commands if r.get("command") == "navigation.home"]
    out["home_back_no_arrival"] = {
        "seq": int(window[0]["seq"]) if window else 0,
        "from": window[0].get("iso", "")[-8:] if window else "",
        "until": window[-1].get("iso", "")[-8:] if window else "",
        "presses_in_window": len(window),
        "presses_in_session": len(home_navs),
        "commands_posted": len(home_cmds),
        "commands_accepted": sum(1 for r in home_cmds if r.get("ok") is True),
        "commands_refused": sum(1 for r in home_cmds if r.get("ok") is False),
        "render_after": _render(seqs[477]),
    }
    return out


# ---- the committed fixture ----------------------------------------------------------------

def load() -> dict[str, Any]:
    """The committed fixture, as `scripts/browser/replay.js` reads it."""
    return json.loads(STATES_JSON.read_text(encoding="utf-8"))


def states() -> list[dict[str, Any]]:
    return list(load().get("states") or [])


def state(fixture_id: str) -> dict[str, Any]:
    for entry in states():
        if entry.get("id") == fixture_id:
            return entry
    raise KeyError(fixture_id)


# ---- the authored half --------------------------------------------------------------------
#
# `derive()` above produces the MEASUREMENTS. It cannot produce card content, because the
# timeline records shapes and never text — which is why the raw file can be read at all
# without a customer's name leaving it.
#
# So each state below carries three things beside its derived `observed` block:
#
#   `replay`  the payload that puts the page back INTO the broken state, handed to the page's
#             own renderer, with the shape the timeline recorded as the acceptance condition.
#             If a fixture no longer reaches the state, the fixture is broken and says so.
#   `ask`     the sentence the owner actually said, with the real name swapped for a customer
#             the fixture shop has, posted to the REAL backend. Its `require`/`forbid` clauses
#             are the proof of another workstream's fix, so most of them fail on this tree.
#   `drive`   for the states that are not a payload at all — a tap, a burst, a refusal, seven
#             presses of Home. Steps `scripts/browser/replay.js` knows how to perform.
#
# Every person in here is invented and every id is four digits. See `assert_clean`.

def _history(ref: str, orders: int, spent: str) -> dict[str, Any]:
    return {
        "available": True, "orders": orders, "spent": spent, "standing": "returning",
        "since": "2026-03-04T10:00:00Z", "first_order_at": "2026-03-04T10:00:00Z",
        "recent": [
            {"order_id": f"order-{ref[-4:]}", "order_number": f"#{1900 + int(ref[-2:]) % 90}",
             "total": spent, "placed_at": "2026-09-11T09:14:00Z", "fulfillment": "fulfilled"},
        ],
        "recent_truncated": False, "other_unfulfilled": [],
    }


def _customer(ref: str, *, orders: int = 1, spent: str = "£60.00",
              email_threads: list[Any] | None = None, with_history: bool = True) -> dict[str, Any]:
    """A customer card payload for a scrubbed ref: invented name, invented address, four digits.

    `email_threads=[]` with `available: True` is the EMPTY GMAIL SECTION — the exact state
    behind "I'm not seeing any UI here except email where there's nothing".
    """
    data: dict[str, Any] = {
        "customer_id": ref, "name": invented_name(ref), "email": invented_email(ref),
        "orders": orders, "spent": spent, "standing": "returning",
    }
    if with_history:
        data["history"] = _history(ref, orders, spent)
        data["related_email"] = {"available": True, "threads": email_threads if email_threads is not None else []}
    return data


#: The seven different customers of turn_be1b384ca420, by the last four digits of their ids.
SEVEN = ("cust-6343", "cust-4807", "cust-5015", "cust-4055", "cust-7975", "cust-2855", "cust-8887")

AUTHORED: dict[str, dict[str, Any]] = {
    # ---------------------------------------------------------------- D-4 -----------------
    "returning_customers_seven_cards": {
        "reproduces": "a one-line question answered with seven full customer profiles, 265 px "
                      "each, 1,949 px of deck, seven different ids, every one open on Email",
        "forensics": "D-4 (and D-2: the tab)",
        "owner_words": "Has anyone bought today that has bought before, a returning customer?",
        "gate": "§13 · a summary question is answered with a summary, not with entity profiles",
        "owned_by": "workstream C — families and presentation",
        "replay": {
            "mode": "context", "tab": "email",
            "ui": [{"type": "customer", "data": _customer(ref)} for ref in SEVEN],
            "expect": {
                "card_count": 7, "types": ["customer"] * 7, "distinct_refs": 7,
                "deck_height_min": 1700, "every_card_open_on": "Email",
            },
        },
        "ask": {
            "text": "has anyone bought today that has bought before, a returning customer?",
            "require_any_type": ["customer_list", "table", "metric_group", "assistant", "customer"],
            "max_cards_of_type": {"customer": 1},
            "max_deck_height": 1200,
        },
    },
    # ------------------------------------------------- "two in the same UI" ---------------
    "duplicate_customer_surface": {
        "reproduces": "two customer cards for the SAME customer in one deck, 232 px and 283 px, "
                      "one of them without the tabs the other has",
        "forensics": "owner, 20:17:05 — \"Log your error there. You just pulled up two in the same UI\"",
        "owner_words": "You just pulled up two in the same UI",
        "gate": "§13 · one entity is one surface in a deck",
        "owned_by": "workstream C — families and presentation",
        "replay": {
            "mode": "context", "tab": "",
            "ui": [
                {"type": "customer", "data": _customer("cust-5015", with_history=False)},
                {"type": "customer", "data": _customer("cust-5015")},
            ],
            "expect": {"card_count": 2, "types": ["customer", "customer"], "distinct_refs": 1},
        },
        "ask": {
            "text": "show me Mia Jones's orders in her lifetime",
            "one_card_per_entity": True,
        },
    },
    # ---------------------------------------------------------------- D-3 -----------------
    "customer_history_gmail_email_list_only": {
        "reproduces": "a request for a customer's history, orders, spend AND their email, "
                      "answered with one 187 px email_list and nothing else",
        "forensics": "D-3 · the turn's only new read was gmail_search; renders were "
                     "[['email_list'],['email_list']]",
        "owner_words": "Pull up the history of [a customer] and his orders. See how many times "
                       "he's ordered, see how much he spent in total, and see if he's in the "
                       "inbox or for Gmail anywhere",
        "gate": "§3/§6 · a new read ENRICHES the workspace it belongs to; the last tool is not the screen",
        "owned_by": "workstream D — workspace and progressive hydration",
        "replay": {
            "mode": "context", "tab": "",
            "ui": [{"type": "email_list", "data": {
                "title": "Email", "count": 0, "threads": [], "empty": True,
                "note": "Nothing from them in the inbox.",
            }}],
            "expect": {"card_count": 1, "types": ["email_list"], "deck_height_max": 400},
        },
        "ask": {
            "text": "pull up the history of Mia Jones and her orders, see how many times she has "
                    "ordered, see how much she spent in total, and see if she is in Gmail anywhere",
            "require_any_type": ["customer"],
        },
    },
    # ---------------------------------------------------------------- D-5 -----------------
    "customer_page_expansion_capability": {
        "reproduces": "\"can you expand [a customer]'s customer page?\" answered with a 1,014 px "
                      "capability card of four tabs listing what the system can do",
        "forensics": "D-5 · family capability_summary at 0.70; the two further attempts drew nothing at all",
        "owner_words": "Can you expand [a customer]'s customer page?",
        "gate": "§4/§5 · \"can you\" is not a capability question when an entity and an operation follow it",
        "owned_by": "workstream C — families and presentation",
        "replay": {
            "mode": "context", "tab": "shop",   # the panel NAME behind the label the telemetry recorded
            "ui": [{"type": "capability", "data": {
                "title": "What this can do",
                "counts": {"reads": 23, "changes": 9, "bulk": 5},
                "writes_enabled": True,
                # The four tabs the telemetry names, and enough behind the open one to reach the
                # 1,014 px the tablet measured. The height is the whole point of this fixture:
                # a thousand pixels of "what I can do" on an 889 px screen, in answer to a
                # question about one customer.
                "groups": [
                    {"area": "shop", "label": "The shop", "items": [
                        {"name": "orders", "label": "Look up an order", "state": "ready", "detail": "by number, by customer, or today's"},
                        {"name": "customers", "label": "Look up a customer", "state": "ready", "detail": "their orders, their spend, their email"},
                        {"name": "address", "label": "Change a delivery address", "state": "ready", "detail": "staged for you to apply"},
                        {"name": "fulfil", "label": "Mark an order as shipped", "state": "ready", "detail": "with or without tracking"},
                        {"name": "cancel", "label": "Cancel and refund an order", "state": "ready", "detail": "staged for you to apply"},
                        {"name": "note", "label": "Add a note to an order", "state": "ready", "detail": "appended, never replaced"},
                        {"name": "discount", "label": "Create a discount code", "state": "ready", "detail": "percentage, fixed or free delivery"},
                        {"name": "draft", "label": "Start a draft order", "state": "ready", "detail": "nothing is charged"},
                        {"name": "inventory", "label": "Set a stock level", "state": "ready", "detail": "per variant, per location"},
                        {"name": "refund", "label": "Refund an order", "state": "ready", "detail": "staged for you to apply"},
                    ]},
                    {"area": "inbox", "label": "The inbox", "items": [
                        {"name": "search", "label": "Search the inbox", "state": "ready"},
                        {"name": "reply", "label": "Reply to a thread", "state": "ready"},
                        {"name": "archive", "label": "Archive a thread", "state": "ready"},
                    ]},
                    {"area": "sales", "label": "Sales and stock", "items": [
                        {"name": "sales", "label": "Sales for a period", "state": "ready"},
                        {"name": "stock", "label": "What is running out", "state": "ready"},
                    ]},
                    {"area": "bulk", "label": "Bulk changes", "items": [
                        {"name": "tags", "label": "Tag a whole set", "state": "ready"},
                    ]},
                ],
                "examples": [
                    "show me today's orders", "what is running out?", "who has not replied?",
                    "how are sales this week?", "tag everything unfulfilled",
                    "what did we sell most of last month?",
                ],
                "note": "Every capability, and where it stands on this Mac right now.",
            }}],
            "expect": {"card_count": 1, "types": ["capability"], "deck_height_min": 900},
        },
        "ask": {
            "text": "can you expand Mia Jones's customer page?",
            "require_any_type": ["customer"],
            "forbid_types": ["capability"],
        },
    },
    # ---------------------------------------------------------------- D-2 -----------------
    "empty_email_section": {
        "reproduces": "a customer card opened on Email with nothing behind the tab — the state "
                      "behind \"I'm not seeing any UI here except email where there's nothing\". "
                      "14 of the session's 19 tabbed customer cards were drawn like this, and the "
                      "Email tab was never once tapped on a customer",
        "forensics": "D-2 · renderOpts().tab is one value per BRANCH, handed to every card that has tabs",
        "owner_words": "I'm not seeing any UI here except email where there's nothing. I want to "
                       "also be seeing his orders and his history and like an email write box",
        "gate": "§3/§12 · a tab belongs to an ENTITY; a freshly-drawn card opens on the tab the task implies",
        "owned_by": "workstream B — the renderer's tab ownership",
        "replay": {
            "mode": "context", "tab": "email",
            "ui": [
                {"type": "customer", "data": _customer("cust-6343")},
                {"type": "customer", "data": _customer("cust-4807")},
            ],
            "expect": {"card_count": 2, "types": ["customer", "customer"], "distinct_refs": 2},
            "verdict": {"max_cards_open_on": {"Email": 1}},
        },
    },
    # ---------------------------------------------------------------- D-1 -----------------
    "split_overlap_branch_under_voice": {
        "reproduces": "the idle screen with two halves: the branch bar's Split/Merge/Close chips "
                      "painted and hit-tested UNDER a full-viewport voice target. The tablet "
                      "measured collisions on 20 orb-screen renders, worst 4, while the gate was green",
        "forensics": "D-1 · #branch-bar is a child of .orb-zone (position:relative, z-index:1), "
                     "which caps it under #talk at z-index:3 with inset:0",
        "owner_words": "the split button is actually rendering over the release to send button, "
                       "and there's no actual way to click the split button",
        "gate": "§9 · zero collisions involving interactive elements, and every branch control hit-testable",
        "owned_by": "workstream A — DOM layering and z-index",
        "drive": {"steps": [
            {"do": "idle"},
            {"do": "hit_test", "selector": "#branch-bar [data-action=\"split\"]"},
            {"do": "tap_selector", "selector": "#branch-bar [data-action=\"split\"]", "expect_no_post": "/turn"},
            {"do": "hit_test", "selector": "#branch-bar .branch-chip"},
            {"do": "hit_test", "selector": "#branch-bar [data-action=\"merge\"]"},
            {"do": "hit_test", "selector": "#branch-bar [data-action=\"cancel\"]"},
            {"do": "collide", "interactive_must_be": 0},
        ]},
    },
    # ------------------------------------------------- the merge/close tap ----------------
    "merge_close_tap": {
        "reproduces": "the merge the owner could only ever reach with a gesture. All four branch "
                      "navigations in the session were `by: gesture`; not one was by a control, "
                      "and the orb screen he was tapping measured 4 collisions",
        "forensics": "D-1 · owner: \"I cannot click the merge or close button or any of the other "
                     "buttons for the two blobs\"",
        "owner_words": "I cannot click the merge or close button or any of the other buttons for "
                       "the two blobs, because wherever I press just leads to you listening",
        "gate": "§7/§8 · Merge and Close are reachable by tap, and a tap on them is never a recording",
        "owned_by": "workstream A — touch ownership and layering",
        "drive": {"steps": [
            {"do": "idle"},
            {"do": "tap_selector", "selector": "#branch-bar [data-action=\"split\"]", "expect_no_post": "/turn"},
            {"do": "expect_branches", "count": 2},
            {"do": "tap_selector", "selector": "#branch-bar [data-action=\"merge\"]", "expect_no_post": "/turn"},
            {"do": "expect_branches", "count": 1},
        ]},
    },
    # --------------------------------------------------------- D-1's evidence -------------
    "dock_touch_burst": {
        "reproduces": "26 consecutive taps beside the dock in ten seconds, the exact durations the "
                      "tablet recorded (39-140 ms), every one of which the voice layer turned into "
                      "a recording",
        "forensics": "D-1 · 63 sub-200 ms holds `sent` in 19 bursts; 63 `tablet_recording_too_short`; "
                     "131 of 132 hold starts report target `dock`",
        "owner_words": "wherever I press just leads to you listening",
        "gate": "§7 · zero ordinary control taps may emit a recording event",
        "owned_by": "workstream A — the touch-ownership state machine",
        "drive": {"steps": [
            {"do": "idle"},
            # Aimed at the control he was aiming at. The touch layer reported `target: dock`
            # for 131 of the session's 132 hold starts because `#talk` IS the dock/hold
            # region and it covers the whole idle screen — so a tap on the Split chip is
            # recorded as a tap on the dock, which is the entire defect.
            {"do": "tap_burst", "durations_from": "observed.ms",
             "near": "#branch-bar [data-action=\"split\"]",
             "expect_no_post": "/turn", "expect_no_recording": True},
            # And the dock's own buttons, which must go on working: the fix is ownership, not
            # a bigger dead zone.
            {"do": "tap_burst", "durations_from": "observed.ms", "near": ".dock-btn",
             "expect_no_post": "/turn", "expect_no_recording": True},
        ]},
    },
    # ---------------------------------------------------------------- D-6 -----------------
    "refused_open_entity_half_empty": {
        "reproduces": "a control that posted `open.entity` for something the Mac was not holding: "
                      "refused `not_held`, and the half then drew `half_empty` with no word about why",
        "forensics": "D-6 · command open.entity ok=false code=not_held, then render items "
                     "['half_empty'] named offer_beside",
        "owner_words": "(no words — he tapped it and nothing arrived)",
        "gate": "§18 · a control is not drawn before its destination is known to exist, and a "
                "refusal is visible rather than an empty half",
        "owned_by": "workstream D — offers and held facts",
        "drive": {"steps": [
            # The products landing, which is the surface the live refusal came off: he tapped
            # a row in it and `open.entity` came back `not_held`.
            {"do": "ask", "text": "what are the best sellers this month?"},
            {"do": "post_command", "command": "open.entity",
             "args": {"ref": "gid://shopify/Product/0", "kind": "product"},
             "expect_ok": False, "expect_code": "not_held"},
            {"do": "refusal_carries_words"},
            {"do": "no_control_carries_unheld_ref"},
        ]},
    },
    # ---------------------------------------------------------------- D-7 -----------------
    "home_back_no_arrival": {
        "reproduces": "seven presses of Home in four seconds, every one accepted (8 posted, 8 "
                      "accepted, 0 refused all session) and the deck still showing the order card",
        "forensics": "D-7 · navigation.home 8 posted / 8 accepted / 0 refused; the render after the "
                     "seventh press is the same 580 px order card and a 146 px attention card",
        "owner_words": "(no words — he pressed it seven times)",
        "gate": "§16 · navigation success is a VISIBLE workspace, not an accepted HTTP code",
        "owned_by": "workstream D — navigation destinations",
        "drive": {"steps": [
            {"do": "ask", "text": "show me order 1938"},
            {"do": "press_home_repeatedly", "times": 7, "within_ms": 4000},
        ]},
    },
}


def build(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The committed fixture: authored states with their derived measurements stamped in."""
    observed = derive(rows)
    missing = set(AUTHORED) - set(observed)
    if missing:
        raise AssertionError(f"authored states with nothing derived for them: {sorted(missing)}")
    orphan = set(observed) - set(AUTHORED)
    if orphan:
        raise AssertionError(f"derived states nobody authored: {sorted(orphan)}")
    entries = []
    for fixture_id, authored in AUTHORED.items():
        entry: dict[str, Any] = {"id": fixture_id}
        entry.update(authored)
        entry["observed"] = observed[fixture_id]
        entries.append(entry)
    payload = {
        "source": SOURCE_SESSION,
        "events": len(rows),
        "viewport": VIEWPORT,
        "derived_by": "experience/fixtures/live_states.py :: derive()",
        "pii": "no customer names and no email addresses. ids are four digits; people are invented.",
        "states": entries,
    }
    assert_clean(json.dumps(payload), "live_states.json")
    return payload


def write(path: Path | None = None) -> Path:
    where = path or STATES_JSON
    payload = build(read_rows())
    where.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return where


if __name__ == "__main__":  # pragma: no cover — a build step, run where the timeline is
    import sys
    try:
        print(write())
    except TimelineMissing as missing:
        print(f"cannot build: {missing}", file=sys.stderr)
        raise SystemExit(2) from missing
