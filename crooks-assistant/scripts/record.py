#!/usr/bin/env python3
"""The production experience recorder, from the Mac's terminal.

    make record-start [NAME="thursday afternoon"]   begin a recording; prints its id
    make record-status                              what is recording, and how many events
    make record-stop                                end it
    make record-list [RECORDING=rec-…]              the interactions in a recording
    make record-save-test [RECORDING=… TURN=turn_…] save one interaction as a fixture

This is NOT `make test-session-*`. A test session is a session somebody started to test with;
a recording is the shop open and the owner working. They write to different directories and
nothing reads one as the other.

The recorder is off unless `CROOKS_RECORD_EXPERIENCE=true` is in `.env`, so `start` here says
so rather than pretending: with the setting off, the backend has no recorder installed and a
file marked active would collect nothing. `record-save-test` needs no backend at all — it
reads the JSONL and writes the fixture.

Nothing here can apply a change. There is no arm, no commit and no nonce anywhere in it, and
the fixture it writes holds names, counts and milliseconds.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _settings():
    from config.settings import get_settings

    return get_settings()


def _recordings(settings):
    from app.observability.recorder import Recordings

    return Recordings(settings.log_dir)


def _health(port: int) -> dict | None:
    request = urllib.request.Request(f"http://127.0.0.1:{port}/health", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310 — loopback only
            return json.loads(response.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        return None


def cmd_start(args) -> int:
    from app.observability.session import AlreadyActive

    settings = _settings()
    if not settings.record_experience:
        print("recording is off. Put CROOKS_RECORD_EXPERIENCE=true in .env and restart the backend "
              "(make restart) before starting a recording; otherwise nothing would be written.", file=sys.stderr)
        return 2
    store = _recordings(settings)
    try:
        session = store.start((args.name or "recording").strip())
    except AlreadyActive as exc:
        print(f"already recording: {exc}. Stop it first (make record-stop).", file=sys.stderr)
        return 1
    print(session.test_session_id)
    print(f"recording to {store.timeline_path(session)}", file=sys.stderr)
    if _health(settings.port) is None:
        print("the backend is not running; it will pick the recording up within a second of starting.", file=sys.stderr)
    return 0


def cmd_status(args) -> int:  # noqa: ARG001
    from app.observability.timeline import count_events

    settings = _settings()
    store = _recordings(settings)
    session = store.active()
    if session is None:
        last = store.last()
        print("not recording" + (f"; the last one was {last.test_session_id}" if last else ""))
        return 0
    path = store.timeline_path(session)
    print(session.test_session_id)
    print(f"{count_events(path)} events in {path}", file=sys.stderr)
    print(f"transcripts: {'kept' if settings.record_transcripts else 'shape only'}; "
          f"recording enabled in settings: {settings.record_experience}", file=sys.stderr)
    return 0


def cmd_stop(args) -> int:  # noqa: ARG001
    settings = _settings()
    session = _recordings(settings).stop()
    if session is None:
        print("nothing was recording.", file=sys.stderr)
        return 0
    print(session.test_session_id)
    return 0


def _find(settings, ref: str) -> Path | None:
    store = _recordings(settings)
    if ref and ref.endswith(".jsonl") and Path(ref).exists():
        return Path(ref)
    return store.find(ref or "")


def cmd_list(args) -> int:
    from app.observability.recorder import interactions

    settings = _settings()
    path = _find(settings, args.recording)
    if path is None:
        print("no recording found" + (f" for {args.recording!r}" if args.recording else ": start and stop one first"), file=sys.stderr)
        return 1
    rows = interactions(path)
    if not rows:
        print(f"{path.name} holds no interaction yet.", file=sys.stderr)
        return 0
    for row in rows:
        tools = ", ".join(row["tools"]) or "—"
        cards = ", ".join(row["cards"]) or "—"
        ms = f"{row['ms']:,.0f} ms" if row["ms"] is not None else "—"
        print(f"{row['turn_id']}  {row['lane'] or '—':7} {row['family'] or '—':24} {ms:>10}  "
              f"{row['outcome']:10} tools[{tools}] cards[{cards}] {', '.join(row['classes'])}")
    print(f"\nnext: make record-save-test RECORDING={path.stem} TURN=<turn id>", file=sys.stderr)
    return 0


def cmd_save_test(args) -> int:
    from app.observability.recorder import save_as_test

    settings = _settings()
    path = _find(settings, args.recording)
    if path is None:
        print("no recording found" + (f" for {args.recording!r}" if args.recording else ""), file=sys.stderr)
        return 1
    out_dir = Path(args.out) if args.out else ROOT / "experience" / "fixtures" / "recorded"
    try:
        written = save_as_test(path, out_dir, turn_id=args.turn or "")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(written["timeline"])
    print(written["manifest"])
    print("assert the manifest against `reconstruct` over the .jsonl beside it "
          "(tests/test_recorder.py shows the shape).", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start", help="begin a named recording")
    start.add_argument("--name", default="recording")
    sub.add_parser("status", help="what is recording")
    sub.add_parser("stop", help="end the recording in progress")
    listing = sub.add_parser("list", help="the interactions in a recording")
    listing.add_argument("recording", nargs="?", default="", help="a recording id, its prefix, or a .jsonl path")
    save = sub.add_parser("save-test", help="save one interaction as a fixture and a manifest")
    save.add_argument("recording", nargs="?", default="", help="a recording id, its prefix, or a .jsonl path")
    save.add_argument("--turn", default="", help="which interaction (default: the last one in the recording)")
    save.add_argument("--out", default="", help="directory for the fixture (default: experience/fixtures/recorded/)")
    args = parser.parse_args(argv)
    return {"start": cmd_start, "status": cmd_status, "stop": cmd_stop,
            "list": cmd_list, "save-test": cmd_save_test}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
