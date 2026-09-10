"""CROOKS Control: the JSON the app renders, and the refusals behind the buttons.

The app itself is Swift and cannot be compiled here. That is the reason this file exists:
everything the app decides is decided by `scripts/control.py` and `scripts/update.py --json`,
and everything in those two is tested here — the four-colour roll-up, both SHAs, the
fast-forward-only rule, the dirty-tree stop, the rollback decision, and the promise that no
secret reaches the screen. The Swift side reads these documents and draws them; if it drifts
from this shape, the contract test below is what fails.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import control, update

# --------------------------------------------------------------------------- a real repo


@pytest.fixture()
def repo(tmp_path):
    """A tiny git repo with a remote, so the refusals can be tested against real git."""
    origin, work = tmp_path / "origin", tmp_path / "work"
    subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "T")):
        subprocess.run(["git", "config", key, value], cwd=work, check=True)
    (work / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (work / "app.py").write_text("print('one')\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)
    subprocess.run(["git", "commit", "-qm", "first"], cwd=work, check=True)
    subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=work, check=True)
    return work


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD")


def commit_upstream(repo: Path, text: str = "print('two')\n", *, path: str = "app.py") -> str:
    """A commit on the remote and nowhere else: what an update has to fast-forward to."""
    clone = repo.parent / "other"
    if not clone.exists():
        subprocess.run(["git", "clone", "-q", str(repo.parent / "origin"), str(clone)], check=True)
        for key, value in (("user.email", "t@example.com"), ("user.name", "T")):
            subprocess.run(["git", "config", key, value], cwd=clone, check=True)
    else:
        subprocess.run(["git", "pull", "-q"], cwd=clone, check=True)
    (clone / path).write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=clone, check=True)
    subprocess.run(["git", "commit", "-qm", f"upstream {path}"], cwd=clone, check=True)
    subprocess.run(["git", "push", "-q"], cwd=clone, check=True)
    return head(clone)


@pytest.fixture()
def here(repo, monkeypatch, tmp_path):
    """Both scripts pointed at the fixture repo, with a logs/ of its own."""
    monkeypatch.setattr(update, "ROOT", repo)
    monkeypatch.setattr(control, "ROOT", repo)
    monkeypatch.setattr(control, "LOG_DIR", repo / "logs")
    return repo


# --------------------------------------------------------- the path out of a status line


@pytest.mark.parametrize(("line", "expected"), [
    (" M app/routes/turn.py", "app/routes/turn.py"),
    ("M app/routes/turn.py", "app/routes/turn.py"),        # the first line, after git() stripped it
    ("?? .venv", ".venv"),
    (" M .env", ".env"),
    ("M .env", ".env"),
    ("MM Makefile", "Makefile"),
    (" D logs/assistant.out.log", "logs/assistant.out.log"),
    ('R  "old name.py" -> "new name.py"', "new name.py"),
    ("!! reports/x.md", "reports/x.md"),
    ("", ""),
])
def test_the_path_is_read_off_the_status_letters_not_a_fixed_column(line, expected):
    """`git()` strips its output, so an unstaged change on the first line arrives without its
    leading space. Reading from column three ate the first character — and a hand-edited
    `.env` became "env", which is not in NEVER_TOUCH, which stopped an update that should
    have gone ahead."""
    assert update._porcelain_path(line) == expected


def test_a_hand_edited_env_on_the_first_line_does_not_stop_the_update(here):
    """The bug above, end to end: the owner's own `.env`, modified, and nothing else."""
    (here / ".env").write_text("CROOKS_WRITES_ENABLED=true\n", encoding="utf-8")
    subprocess.run(["git", "add", "-f", ".env"], cwd=here, check=True)
    subprocess.run(["git", "commit", "-qm", "env"], cwd=here, check=True)
    (here / ".env").write_text("CROOKS_WRITES_ENABLED=false\n", encoding="utf-8")
    assert update.dirty_paths() == [".env"]
    assert update.blocking_changes([".env"]) == []
    code, doc = update.run(check=True, quiet=True)
    assert code == 0 and doc["stop"] is None
    assert doc["local_work"] == {"dirty": [".env"], "blocking": [], "stops": False}
    assert (here / ".env").read_text(encoding="utf-8") == "CROOKS_WRITES_ENABLED=false\n"


# ------------------------------------------------------------ the update, as one document


def test_the_check_document_carries_both_shas_and_changes_nothing(here):
    before = head(here)
    candidate = commit_upstream(here)
    code, doc = update.run(check=True, quiet=True)
    assert code == 0 and doc["ok"] is True
    assert doc["contract"] == update.CONTRACT and doc["command"] == "crooks-update"
    assert doc["current"]["sha"] == before and doc["candidate"]["sha"] == candidate
    assert doc["current"]["short"] == before[:10] and len(doc["candidate"]["short"]) == 10
    assert doc["behind"] == 1 and doc["ahead"] == 0 and doc["fast_forward"] is True
    assert doc["next"] == "click_to_apply", "a check never applies; the click does"
    assert doc["moved"] is False and doc["restarted"] is False and doc["verified"] is False
    assert head(here) == before, "nothing moved"
    assert [s["stage"] for s in doc["stages"]] == ["repo", "branch", "fetch", "pull", "deps", "tests"]


def test_up_to_date_says_so_rather_than_offering_a_click(here):
    code, doc = update.run(check=True, quiet=True)
    assert code == 0 and doc["behind"] == 0 and doc["next"] == "up_to_date"
    assert doc["current"]["sha"] == doc["candidate"]["sha"]


def test_a_diverged_branch_is_refused_as_not_a_fast_forward(here):
    """The owner has a commit the remote does not. There is no fast-forward, so there is no
    update — and the commit is still there afterwards."""
    commit_upstream(here)
    (here / "mine.py").write_text("mine\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=here, check=True)
    subprocess.run(["git", "commit", "-qm", "mine"], cwd=here, check=True)
    mine = head(here)
    code, doc = update.run(quiet=True)
    assert code == 1 and doc["ok"] is False
    assert doc["fast_forward"] is False and doc["ahead"] == 1 and doc["behind"] == 1
    assert doc["stop"]["stage"] == "pull"
    assert "cannot fast-forward" in doc["stop"]["reason"]
    assert doc["next"] == "blocked"
    assert head(here) == mine, "the owner's commit is untouched"
    assert (here / "mine.py").exists()


def test_a_dirty_tree_stops_the_update_and_says_which_files(here):
    commit_upstream(here)
    (here / "app.py").write_text("print('mine, uncommitted')\n", encoding="utf-8")
    before = head(here)
    code, doc = update.run(quiet=True)
    assert code == 1 and doc["stop"]["stage"] == "branch"
    assert doc["local_work"]["blocking"] == ["app.py"] and doc["local_work"]["stops"] is True
    assert "app.py" in doc["stop"]["reason"] and "will not throw work away" in doc["stop"]["reason"]
    assert head(here) == before
    assert (here / "app.py").read_text(encoding="utf-8") == "print('mine, uncommitted')\n"


def test_the_fast_forward_moves_the_build_and_says_what_moved(here, monkeypatch):
    """The apply path, with the restart and the health read stubbed: launchd and /health are
    the Mac's, not this machine's. What is tested here is that the code moved, by a
    fast-forward, and that the document says so."""
    candidate = commit_upstream(here, path="pyproject.toml", text="[project]\nname='x'\nversion='2'\n")
    kicked: list[str] = []
    monkeypatch.setattr(update, "stage_deps", lambda changed, *, check_only: bool(update.dep_changes(changed)))
    monkeypatch.setattr(update, "stage_restart", lambda *, check_only, port: kicked.append("restart"))
    monkeypatch.setattr(update, "stage_verify", lambda *, check_only, port: {"build": "b-2", "status": "ok"})
    code, doc = update.run(quiet=True)
    assert code == 0 and doc["moved"] is True
    assert head(here) == candidate
    assert doc["current"]["sha"] != candidate, "the document names the build it started from"
    assert doc["deps"] == ["pyproject.toml"] and doc["changed_files"] == 1
    assert doc["restarted"] is True and doc["verified"] is True
    assert doc["current"]["build"] == "b-2" and doc["next"] == "verify_the_tablet"
    assert kicked == ["restart"]


def test_a_failing_suite_stops_before_anything_restarts(here, monkeypatch):
    commit_upstream(here)
    monkeypatch.setattr(update, "stage_restart", lambda **kw: pytest.fail("restarted a build that did not pass"))
    monkeypatch.setattr(update, "stage_verify", lambda **kw: pytest.fail("verified a build that did not pass"))
    (here / ".venv" / "bin").mkdir(parents=True)
    fake = here / ".venv" / "bin" / "pytest"
    fake.write_text("#!/bin/sh\necho '1 failed, 2 passed'\nexit 1\n", encoding="utf-8")
    fake.chmod(0o755)
    code, doc = update.run(test=True, quiet=True)
    assert code == 1 and doc["stop"]["stage"] == "tests"
    assert "did not pass" in doc["stop"]["reason"] and "1 failed" in doc["stop"]["reason"]
    assert doc["moved"] is True, "the code did move; that is what the rollback is for"
    assert doc["tested"] is False and doc["restarted"] is False


def test_the_suite_is_not_run_unless_it_is_asked_for(here):
    commit_upstream(here)
    code, doc = update.run(check=True, quiet=True)
    tests = [s for s in doc["stages"] if s["stage"] == "tests"]
    assert tests and tests[0]["state"] == "skip" and "not asked for" in tests[0]["detail"]
    assert code == 0


def test_the_json_switch_prints_one_document_and_no_lines(here, capsys):
    assert update.main(["--check", "--json"]) == 0
    out = capsys.readouterr().out
    doc = json.loads(out), "the whole of stdout parses as one JSON document"
    assert doc[0]["command"] == "crooks-update"
    assert "crooks-update" not in out.split("\n", 1)[0], "no human header above the JSON"


def test_the_typed_command_still_prints_its_lines(here, capsys):
    assert update.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("crooks-update  (check only")
    assert f"{update.OK} repo    " in out and f"{update.SKIP} pull    " in out
    assert "already up to date" in out, "the same seven lines it always printed"


# ------------------------------------------------------------------- what /health looks like


def check(ok: bool, detail: str = "") -> dict:
    return {"ok": ok, "detail": detail}


def family(state: str, *, label: str, scope: str = "", detail: str = "", operations=("order_note_append",)) -> dict:
    return {"key": label.lower().replace(" ", "_"), "label": label, "area": "orders", "what": "…",
            "state": state, "detail": detail or state.lower(), "scope": scope,
            "operations": list(operations), "tools": [], "offerable": state == "READY", "hide": False}


def health_doc(**over) -> dict:
    """A /health as the running backend answers it, everything well."""
    doc = {
        "status": "ok", "version": "0.1.0", "build": "b-2026-09-10-abc", "uptime_s": 7200.0, "sessions": 1,
        "checks": {
            "speech": check(True, "scribe_v2 (primary)"), "tts": check(True, "Derek"),
            "claude": check(True, "sonnet, CLI"), "shopify": check(True, "5wn03t-nm.myshopify.com"),
            "gmail": check(True, "george@crooksldn.com"), "whisper": check(True, "small.en"),
            "knowledge_base": check(True, "7 file(s)"), "terminology": check(True, "120 term(s)"),
            "writes": check(True, "ready"),
        },
        "speech": {"primary": "scribe", "effective": "scribe_v2"},
        "writes": {"state": "ready", "detail": "ready"},
        "families": {"order_note": family("READY", label="Order notes")},
        "manifest": {"reads": 40, "writes": 12, "batches": 3, "fingerprint": "deadbeefcafe"},
        "orders_cache": {"orders": 312, "age_s": 40, "days": 90},
        "observability": {"test_session": None, "name": None},
    }
    doc.update(over)
    return doc


@pytest.fixture()
def running(here, monkeypatch):
    """The control surface pointed at a well backend on a routed tailnet. Each test bends one
    thing and reads the colour back."""
    state = {"health": health_doc(), "host": "crooks-assistant.taildfb357.ts.net"}
    monkeypatch.setattr(control, "port", lambda: 8000)
    monkeypatch.setattr(control, "read_health", lambda p, fresh=False: state["health"])
    monkeypatch.setattr(control, "tablet_route", lambda p: (state["host"], "" if state["host"] else "Tailscale is not serving port 8000"))
    return state


# ----------------------------------------------------------------------- the four colours


def test_green_is_everything_answering_changes_ready_tablet_routed(running):
    doc = control.status_document()
    assert doc["state"] == "GREEN" and doc["headline"] == "CROOKS — Online"
    assert doc["ok"] is True and doc["degraded"] == [] and doc["issues"] == []
    assert doc["contract"] == control.CONTRACT


def test_blue_is_a_test_session_recording(running):
    running["health"]["observability"] = {"test_session": "ts-20260910-1200-first-hour", "name": "first hour"}
    doc = control.status_document()
    assert doc["state"] == "BLUE" and doc["headline"] == "CROOKS — Testing"
    assert "ts-20260910-1200-first-hour" in doc["why"]
    assert doc["test_session"] == {"active": True, "id": "ts-20260910-1200-first-hour", "name": "first hour"}


def test_amber_is_live_and_read_only(running):
    """The Mac as it normally runs: writes off, so every write family is READ_ONLY. Live, and
    the owner can see at a glance that nothing can be changed from the tablet."""
    running["health"]["writes"] = {"state": "disabled", "detail": "disabled — CROOKS_WRITES_ENABLED=false"}
    running["health"]["families"] = {"order_note": family("READ_ONLY", label="Order notes", detail="changes are off")}
    doc = control.status_document()
    assert doc["state"] == "AMBER" and doc["headline"] == "CROOKS — Read only"
    assert doc["mutation"]["state"] == "read_only" and doc["degraded"] == ["changes"]
    assert "read-only" in doc["why"]


def test_amber_is_also_something_non_essential_being_down(running):
    running["health"]["checks"]["gmail"] = check(False, "the token was revoked")
    doc = control.status_document()
    assert doc["state"] == "AMBER" and doc["headline"] == "CROOKS — Degraded"
    assert "gmail" in doc["degraded"] and "the token was revoked" in doc["why"]
    assert doc["ok"] is True, "degraded is live: the exit code is not an alarm"


def test_amber_is_also_a_tablet_with_no_route(running):
    running["host"] = None
    doc = control.status_document()
    assert doc["state"] == "AMBER" and "tablet route" in doc["degraded"]
    assert doc["tablet"]["host"] == "" and doc["tablet"]["local"] == "http://127.0.0.1:8000/"
    assert "Tailscale is not serving" in doc["why"]


def test_red_is_nothing_answering(running, monkeypatch):
    monkeypatch.setattr(control, "read_health", lambda p, fresh=False: None)
    doc = control.status_document()
    assert doc["state"] == "RED" and doc["headline"] == "CROOKS — Offline"
    assert doc["ok"] is False and "nothing is answering on 127.0.0.1:8000" in doc["why"]
    rows = {r["key"]: r for r in doc["rows"]}
    assert rows["online"]["state"] == "bad" and rows["build"]["value"] == "?"


@pytest.mark.parametrize("name", ["speech", "claude", "shopify"])
def test_red_is_one_of_the_three_it_cannot_work_without(running, name):
    running["health"]["checks"][name] = check(False, "not available")
    doc = control.status_document()
    assert doc["state"] == "RED" and doc["headline"] == "CROOKS — Issue"
    assert doc["issues"] == [name] and doc["ok"] is False


def test_an_issue_is_never_hidden_by_a_test_session(running):
    running["health"]["observability"] = {"test_session": "ts-x", "name": "an hour"}
    running["health"]["checks"]["claude"] = check(False, "the CLI is not on PATH")
    assert control.status_document()["state"] == "RED", "RED beats BLUE"


def test_a_test_session_outranks_something_merely_degraded(running):
    running["health"]["observability"] = {"test_session": "ts-x", "name": "an hour"}
    running["health"]["checks"]["gmail"] = check(False, "revoked")
    doc = control.status_document()
    assert doc["state"] == "BLUE" and "gmail" in doc["degraded"], "BLUE beats AMBER, and still says so"


def test_every_colour_is_reachable_and_no_fifth_one_is(running):
    """The oracle for the roll-up itself: four inputs, four colours, nothing else."""
    seen = set()
    for bend in (lambda: None,
                 lambda: running["health"]["observability"].update({"test_session": "ts-x"}),
                 lambda: running["health"]["checks"].update({"gmail": check(False, "revoked")}),
                 lambda: running["health"]["checks"].update({"claude": check(False, "down")})):
        running["health"] = health_doc()
        bend()
        seen.add(control.status_document()["state"])
    assert seen == set(control.COLOURS)


# ------------------------------------------------------------- mutation readiness, from /health


def test_mutation_readiness_is_read_from_the_capability_families(running):
    """Not from a notion of our own: app/capabilities/families.py states every family with the
    scope named, and /health carries the table."""
    running["health"]["families"] = {
        "order_note": family("READY", label="Order notes"),
        "discount": family("MISSING_SCOPE", label="Discount codes", scope="write_discounts",
                           detail="blocked — Shopify write_discounts scope missing"),
    }
    mutation = control.mutation_readiness(running["health"])
    assert mutation["state"] == "missing_scope" and mutation["source"] == "families"
    assert "write_discounts" in mutation["detail"]
    assert mutation["missing_scope"][0]["label"] == "Discount codes"
    assert mutation["ready"] == ["Order notes"]
    assert control.status_document()["state"] == "AMBER"


def test_a_family_that_is_off_on_this_store_is_not_a_fault(running):
    running["health"]["families"] = {
        "order_note": family("READY", label="Order notes"),
        "credit": family("NOT_SUPPORTED_BY_STORE", label="Store credit", detail="this store does not offer it"),
    }
    mutation = control.mutation_readiness(running["health"])
    assert mutation["state"] == "partial" and mutation["unavailable"][0]["label"] == "Store credit"


def test_readiness_falls_back_to_the_writes_line_on_a_build_with_no_family_table(running):
    running["health"]["families"] = {}
    running["health"]["writes"] = {"state": "ready", "detail": "ready"}
    assert control.mutation_readiness(running["health"])["state"] == "ready"
    assert control.mutation_readiness(running["health"])["source"] == "writes"
    running["health"]["writes"] = {"state": "disabled", "detail": "disabled — CROOKS_WRITES_ENABLED=false"}
    assert control.mutation_readiness(running["health"])["state"] == "read_only"


def test_writes_blocked_by_configuration_is_named_as_blocked(running):
    running["health"]["writes"] = {"state": "blocked", "detail": "blocked — CROOKS_ALLOWED_LOGINS not configured"}
    mutation = control.mutation_readiness(running["health"])
    assert mutation["state"] == "blocked" and "ALLOWED_LOGINS" in mutation["detail"]
    assert control.status_document()["state"] == "AMBER"


# ------------------------------------------------------------------------- the rows


def test_every_row_the_brief_asks_for_is_there_and_in_order(running):
    doc = control.status_document()
    keys = [row["key"] for row in doc["rows"]]
    assert keys == ["online", "build", "backend", "speech", "speaks", "claude", "shopify", "gmail",
                    "orders", "tablet", "mutation", "session", "branch", "known_good"]
    assert all(set(row) == {"key", "label", "state", "value", "detail"} for row in doc["rows"])
    assert all(row["state"] in ("ok", "off", "bad") for row in doc["rows"])
    rows = {row["key"]: row for row in doc["rows"]}
    assert rows["build"]["value"] == "b-2026-09-10-abc"
    assert rows["orders"]["value"] == "312 held, read 40s ago"
    assert rows["tablet"]["value"] == "https://crooks-assistant.taildfb357.ts.net/"
    assert rows["speech"]["value"].startswith("scribe_v2 · ")
    assert rows["branch"]["value"].endswith(control.current_build()["short"])


def test_a_row_the_build_does_not_report_says_so_rather_than_lying(running):
    del running["health"]["checks"]["gmail"]
    del running["health"]["orders_cache"]
    rows = {row["key"]: row for row in control.status_document()["rows"]}
    assert rows["gmail"]["state"] == "off" and "does not report" in rows["gmail"]["detail"]
    assert rows["orders"]["value"] == "cold"


# --------------------------------------------------------------- the last known-good build


def test_there_is_no_known_good_build_until_something_records_one(running):
    doc = control.status_document()
    assert doc["build"]["last_known_good"] is None
    assert doc["rollback"]["available"] is False and doc["rollback"]["safe"] is False
    assert "nothing to go back to" in doc["rollback"]["reason"]
    rows = {row["key"]: row for row in doc["rows"]}
    assert rows["known_good"]["value"] == "none recorded" and "mark-good" in rows["known_good"]["detail"]


def test_marking_the_running_build_good_writes_it_where_only_this_command_writes(running, here):
    doc = control.mark_good_document()
    assert doc["ok"] is True
    record = doc["marked_good"]
    assert record["sha"] == head(here) and record["build"] == "b-2026-09-10-abc"
    assert record["recorded_by"] == "crooks-control mark-good"
    path = control.known_good_path()
    assert path == here / "logs" / "last_known_good.json"
    assert json.loads(path.read_text(encoding="utf-8"))["sha"] == head(here)
    assert path.stat().st_mode & 0o777 == 0o600, "a file about this Mac, read by this Mac"
    assert control.read_known_good()["short"] == head(here)[:10]


def test_a_build_that_is_not_answering_is_never_recorded_as_good(running, monkeypatch):
    monkeypatch.setattr(control, "read_health", lambda p, fresh=False: None)
    doc = control.mark_good_document()
    assert doc["ok"] is False and doc["marked_good"] is None
    assert "not known to be good" in doc["stop"]["reason"]
    assert control.read_known_good() is None


def test_a_build_with_an_essential_down_is_never_recorded_as_good(running):
    running["health"]["checks"]["shopify"] = check(False, "401 from the store")
    doc = control.mark_good_document()
    assert doc["ok"] is False and "shopify is down" in doc["stop"]["reason"]
    assert control.read_known_good() is None


# ------------------------------------------------------------------ the rollback decision


def test_the_rollback_picks_the_last_known_good_build(running, here):
    good = head(here)
    control.mark_good_document()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "a build that turned out badly"], cwd=here, check=True)
    doc = control.status_document()
    assert doc["build"]["current"]["sha"] != good
    assert doc["rollback"]["available"] is True and doc["rollback"]["safe"] is True
    assert doc["rollback"]["sha"] == good and doc["rollback"]["short"] == good[:10]
    assert doc["rollback"]["commands"] == [["git", "checkout", good], ["make", "restart"]]
    assert "detached HEAD" in doc["rollback"]["note"]


def test_the_running_build_being_the_good_one_is_not_a_rollback(running, here):
    control.mark_good_document()
    doc = control.status_document()
    assert doc["rollback"]["available"] is False and "IS the last known-good one" in doc["rollback"]["reason"]


def test_a_known_good_commit_that_is_not_in_this_checkout_is_refused(running, here):
    control.write_known_good({"version": 1, "sha": "0" * 40, "short": "0" * 10, "recorded_at": 1.0})
    decision = control.status_document()["rollback"]
    assert decision["available"] is False and "not in this checkout" in decision["reason"]


def test_a_rollback_refuses_a_dirty_tree_and_leaves_the_work_alone(running, here):
    good = head(here)
    control.mark_good_document()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "later"], cwd=here, check=True)
    (here / "app.py").write_text("half-finished, mine\n", encoding="utf-8")
    doc = control.rollback_document(yes=True)
    assert doc["ok"] is False and doc["next"] == "blocked"
    assert doc["rollback"]["available"] is True and doc["rollback"]["safe"] is False
    assert "app.py" in doc["rollback"]["reason"] and "Nothing has been thrown away" in doc["rollback"]["reason"]
    assert head(here) != good, "it did not move"
    assert (here / "app.py").read_text(encoding="utf-8") == "half-finished, mine\n"


def test_a_rollback_needs_the_click_even_when_it_is_safe(running, here):
    good = head(here)
    control.mark_good_document()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "later"], cwd=here, check=True)
    doc = control.rollback_document(yes=False)
    assert doc["ok"] is False and doc["next"] == "click_to_apply"
    assert doc["rollback"]["safe"] is True and "rollback --yes" in doc["stop"]["reason"]
    assert head(here) != good, "nothing moved without the click"


def test_a_rollback_that_is_clicked_goes_back_and_restarts(running, here, monkeypatch):
    good = head(here)
    control.mark_good_document()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "a build that turned out badly"], cwd=here, check=True)
    (here / ".env").write_text("mine\n", encoding="utf-8")
    kicked = []
    monkeypatch.setattr(control.update_module(), "stage_restart", lambda *, check_only, port: kicked.append(port))
    doc = control.rollback_document(yes=True)
    assert doc["ok"] is True and doc["next"] == "done"
    assert head(here) == good and kicked == [8000]
    assert [s["stage"] for s in doc["stages"]] == ["checkout", "restart", "verify"]
    assert doc["build"]["current"]["detached"] is True
    assert (here / ".env").read_text(encoding="utf-8") == "mine\n", "the owner's own file, untouched"


def test_a_rollback_whose_restart_is_refused_says_so_rather_than_claiming_success(running, here, monkeypatch):
    control.mark_good_document()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "later"], cwd=here, check=True)

    def refuse(**_kw):
        raise update.Stopped("The services would not restart: launchctl refused")

    monkeypatch.setattr(control.update_module(), "stage_restart", refuse)
    doc = control.rollback_document(yes=True)
    assert doc["ok"] is False and doc["next"] == "restart_by_hand"
    assert doc["stages"][-1]["state"] == "fail" and "launchctl refused" in doc["stop"]["reason"]


def test_the_detached_build_a_rollback_leaves_is_never_itself_marked_good(running, here, monkeypatch):
    control.mark_good_document()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "later"], cwd=here, check=True)
    monkeypatch.setattr(control.update_module(), "stage_restart", lambda **kw: None)
    assert control.rollback_document(yes=True)["ok"] is True
    doc = control.mark_good_document()
    assert doc["ok"] is False and "detached HEAD" in doc["stop"]["reason"]
