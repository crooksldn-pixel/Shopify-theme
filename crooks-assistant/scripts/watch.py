#!/usr/bin/env python3
"""crooks-watch — what CROOKS OS is doing, live, in one line per thing.

    make watch                 follow the active test session
    make watch SESSION=ts-…    follow (or replay) a named one
    crooks-watch --once        print what has happened and stop

Reads the test session's timeline as it grows and prints the SEMANTIC state: the turn, the
branch, the lane it took, which recipe, what the cache did, which source was read, whether
the model was called at all, what was staged and what the screen showed.

What it will never print, whatever is on the timeline:

  * model reasoning of any kind — the timeline does not carry it and this does not ask for it
  * secrets, tokens or headers — the writer withholds them; this also refuses them by key
  * an email body, a subject, a customer's name, an address or an order's contents

Everything below is an id, a count, a millisecond or a controlled word.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

POLL_S = 0.25
# Fields that may be printed. An event field not named here is not shown, so a field added
# to the timeline later cannot start leaking into a terminal on somebody's bench.
SAFE = frozenset({
    "kind", "turn_id", "session_id", "branch_id", "parent_branch_id", "lane", "why", "family",
    "confidence", "recipe_id", "hit", "defer", "ms", "target_ms", "partial", "tool", "ok",
    "outcome", "error", "tool_call_id", "proposal_id", "batch_id", "operation", "risk",
    "interaction", "status", "code", "count", "set_id", "set_kind", "label", "engine",
    "fallback", "audio_s", "steps", "error_kind", "stopped_early", "ui", "model_calls",
    "fast_path_hit", "cache", "coalesced", "prefetch", "critical_path_ms", "serial_ms",
    "saved_ms", "groups", "fanout", "spent", "skipped", "state", "nav", "depth", "index",
    "chars", "via", "source", "input", "turns_before", "epoch", "missing_capability",
    "model_input_chars", "tool_schema_bytes", "turn_total_ms", "stt_ms", "model_ms",
    "source_ms", "tool_calls", "backgrounded", "cancelled", "threads_checked", "threads_found",
})

DIM, BOLD, RESET = "\033[2m", "\033[1m", "\033[0m"
COLOUR = {"FAST": "\033[32m", "NORMAL": "\033[36m", "DEEP": "\033[35m",
          "error": "\033[31m", "warn": "\033[33m", "ok": "\033[32m"}


def _tint(text: str, key: str, colour: bool) -> str:
    return f"{COLOUR.get(key, '')}{text}{RESET}" if colour and COLOUR.get(key) else text


def _ms(value) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{value / 1000:.1f}s" if value >= 1000 else f"{value:.0f}ms"


def line(event: dict, *, colour: bool = True) -> str | None:
    """One event as one line, or None for an event with nothing to say."""
    event = {k: v for k, v in event.items() if k in SAFE or k in ("ts", "iso")}
    kind = str(event.get("kind") or "")
    when = str(event.get("iso") or "")[11:19]
    turn = str(event.get("turn_id") or "")[-6:]
    head = f"{_tint(when, 'dim', False)} {DIM if colour else ''}{turn or '······'}{RESET if colour else ''}"

    if kind == "session_started":
        return f"{head} {BOLD if colour else ''}session started{RESET if colour else ''}"
    if kind == "session_stopped":
        return f"{head} {BOLD if colour else ''}session stopped{RESET if colour else ''}"
    if kind == "turn_started":
        return f"{head} ── heard ({event.get('input')})"
    if kind == "stt":
        ok = "ok" if event.get("ok") else "no speech"
        return f"{head}    stt {ok} via {event.get('engine') or '?'}" + (" (fallback)" if event.get("fallback") else "")
    if kind == "lane":
        lane = str(event.get("lane") or "")
        why = str(event.get("why") or "")
        recipe = f" {event.get('recipe_id')}" if event.get("recipe_id") else ""
        return f"{head}    lane {_tint(lane, lane, colour)}{recipe}  {DIM if colour else ''}{why}{RESET if colour else ''}"
    if kind == "fast_path":
        state = "hit" if event.get("hit") else f"deferred: {event.get('defer')}"
        late = "  ⟵ over target" if _over(event) else ""
        return f"{head}    recipe {event.get('recipe_id')} {state} in {_ms(event.get('ms'))}{late}"
    if kind == "read_plan":
        groups = event.get("groups") or []
        saved = _ms(event.get("saved_ms"))
        return f"{head}    reads {' | '.join(','.join(g) for g in groups)}  {_ms(event.get('critical_path_ms'))}" + (f" (saved {saved})" if saved else "")
    if kind == "prefetch" and event.get("hit"):
        return f"{head}    looked the order up ahead of the model in {_ms(event.get('ms'))}"
    if kind == "tool_finished":
        outcome = str(event.get("outcome") or "")
        key = "ok" if outcome == "ok" else ("warn" if outcome in ("not_yet", "staged") else "error")
        tail = f"  {event.get('error')}" if outcome not in ("ok", "staged") and event.get("error") else ""
        return f"{head}    {event.get('tool')} {_tint(outcome, key, colour)} {_ms(event.get('ms'))}{str(tail)[:80]}"
    if kind == "model":
        steps = len(event.get("steps") or [])
        calls = len(event.get("tool_calls") or [])
        return f"{head}    claude {_ms(event.get('ms'))}  {steps} step(s), {calls} tool call(s)"
    if kind == "action_proposed" or kind == "batch_proposed":
        return f"{head}    staged {event.get('operation')} ({event.get('risk')}, {event.get('interaction')})"
    if kind in ("action_commit", "batch_commit", "action_settled"):
        return f"{head}    {kind.split('_')[-1]} {event.get('operation') or ''} → {_tint(str(event.get('code') or event.get('status') or ''), 'ok' if str(event.get('code')) == 'verified' else 'error', colour)}"
    if kind == "row_action":
        return f"{head}    row action {event.get('action')} {'staged' if event.get('ok') else 'refused'}"
    if kind == "working_set":
        return f"{head}    set {event.get('set_id')} {event.get('count')} {event.get('set_kind')}"
    if kind == "unsupported_claim":
        return f"{head}    {_tint('said it cannot, though it can', 'warn', colour)}"
    if kind == "turn_performance":
        bits = [f"lane={event.get('lane')}", f"model={event.get('model_calls')}"]
        if event.get("model_ms"):
            bits.append(f"claude={_ms(event.get('model_ms'))}")
        cache = event.get("cache") or {}
        if isinstance(cache, dict) and (cache.get("hits") or cache.get("misses")):
            bits.append(f"cache={cache.get('hits')}/{cache.get('hits', 0) + cache.get('misses', 0)}")
        if event.get("model_input_chars"):
            bits.append(f"prompt={event['model_input_chars']}c")
        return f"{head}    {DIM if colour else ''}{'  '.join(bits)}{RESET if colour else ''}"
    if kind == "turn_finished":
        cards = ",".join(str(u) for u in (event.get("ui") or [])) or "no card"
        bad = event.get("error_kind")
        return f"{head} ══ {_ms(event.get('ms'))}  {cards}" + (f"  {_tint(str(bad), 'error', colour)}" if bad else "")
    if kind.startswith("tablet_"):
        return _tablet(head, kind, event, colour)
    return None


def _over(event: dict) -> bool:
    try:
        return float(event.get("ms") or 0) > float(event.get("target_ms") or 0) > 0
    except (TypeError, ValueError):
        return False


def _tablet(head: str, kind: str, event: dict, colour: bool) -> str | None:
    what = kind[len("tablet_"):]
    if what == "render":
        return f"{head}    tablet drew {event.get('count') or ''} card(s)" + (f", skipped {event.get('skipped')}" if event.get("skipped") else "")
    if what == "exception":
        return f"{head}    {_tint('tablet exception', 'error', colour)}"
    if what in ("navigate", "tab", "scroll"):
        return f"{head}    tablet {what} {event.get('nav') or event.get('label') or event.get('depth') or ''}"
    if what == "gesture":
        return f"{head}    tablet gesture {event.get('gesture')} {event.get('state') or ''}"
    return None


def follow(path: Path, *, once: bool, colour: bool, out=None) -> int:
    """Print what is there, then what arrives. Ends on Ctrl-C, or at once with --once."""
    out = out if out is not None else sys.stdout
    offset = 0
    seen_stop = False
    while True:
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                handle.seek(offset)
                for raw in handle:
                    if not raw.endswith("\n"):
                        break        # a partial line: leave the offset before it
                    offset += len(raw.encode("utf-8"))
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        event = json.loads(raw)
                    except ValueError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    rendered = line(event, colour=colour)
                    if rendered:
                        print(rendered, file=out, flush=True)
                    seen_stop = seen_stop or event.get("kind") == "session_stopped"
        except OSError:
            pass
        if once or seen_stop:
            return 0
        try:
            time.sleep(POLL_S)
        except KeyboardInterrupt:
            return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("session", nargs="?", default="", help="a session id or its prefix; default: the one running")
    parser.add_argument("--once", action="store_true", help="print what has happened and stop")
    parser.add_argument("--no-colour", action="store_true")
    args = parser.parse_args(argv)

    from app.observability.session import TestSessions
    from config.settings import get_settings

    store = TestSessions(get_settings().log_dir)
    path = store.find(args.session)
    if path is None:
        active = store.active()
        if active is not None:
            path = store.timeline_path(active)     # started, nothing written yet
        else:
            print("No test session is running. Start one: make test-session-start NAME=\"an hour\"", file=sys.stderr)
            return 1
    print(f"watching {path.name} — Ctrl-C to stop\n", file=sys.stderr)
    return follow(path, once=args.once, colour=not args.no_colour and sys.stdout.isatty())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
