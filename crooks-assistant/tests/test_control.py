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
