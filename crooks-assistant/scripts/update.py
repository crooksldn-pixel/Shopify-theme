#!/usr/bin/env python3
"""crooks-update — bring this Mac up to date, in one word, safely.

    crooks-update              fetch, fast-forward, install what changed, restart, verify
    crooks-update --check      say what WOULD happen and change nothing
    crooks-update --branch X   update a branch other than the one checked out

Seven stages, each of which reports itself and any of which stops the run:

    1  find      the checkout this command belongs to
    2  branch    it is the branch you meant, and the tree is clean enough to move
    3  fetch     from the remote
    4  pull      FAST-FORWARD ONLY — never a merge, never a rebase, never a reset
    5  deps      only when the dependency files actually changed
    6  restart   the backend and whisper-server, through launchd
    7  verify    /health, read back, with the build id

What it will not do, by construction:

  * touch .env, or anything in logs/, or any credential (they are not in git, and nothing
    here writes them)
  * discard local work: a dirty tree or a diverged branch STOPS the update and says so.
    There is no --force, and no reset.
  * decide to update itself. This runs when George types it, and not otherwise; nothing in
    CROOKS OS calls it.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

# Files whose change means the dependencies need installing again. Anything else is code.
DEP_FILES = ("pyproject.toml", "uv.lock", "requirements.txt")
# Never written, never checked out over, never mentioned to git by this command.
NEVER_TOUCH = (".env", "logs", "reports", ".venv")

OK, FAIL, SKIP = "  ok   ", "  FAIL ", "  --   "


class Stopped(RuntimeError):
    """A stage said no. The message is what the owner reads; nothing is undone."""


def git(*args: str, cwd: Path | None = None, check: bool = True) -> str:
    # ROOT is looked up at call time, not bound as a default: a default would freeze the
    # checkout at import and make this untestable against any other one.
    out = subprocess.run(["git", *args], cwd=cwd or ROOT, capture_output=True, text=True, timeout=120)
    if check and out.returncode != 0:
        raise Stopped((out.stderr or out.stdout or "git failed").strip().splitlines()[-1][:300])
    return (out.stdout or "").strip()


def stage_find() -> Path:
    top = Path(git("rev-parse", "--show-toplevel"))
    print(f"{OK} repo     {top}")
    return top


def _porcelain_path(line: str) -> str:
    """The path out of a `git status --porcelain` line. Two status characters, a space, then
    the path — or "old -> new" for a rename, where the new name is the one that matters."""
    path = line[3:].strip() if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip('"')


def stage_branch(wanted: str) -> str:
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":
        raise Stopped("This checkout is not on a branch (detached HEAD). `git checkout <branch>` first.")
    if wanted and branch != wanted:
        raise Stopped(f"On {branch}, not {wanted}. `git checkout {wanted}` first — this command does not switch branches for you.")
    dirty = [_porcelain_path(line) for line in git("status", "--porcelain").splitlines() if line.strip()]
    dirty = [d for d in dirty if d]
    blocking = [d for d in dirty if not any(d == p or d.startswith(f"{p}/") or f"/{p}/" in d or d.endswith(f"/{p}") for p in NEVER_TOUCH)]
    if blocking:
        listed = ", ".join(blocking[:5])
        raise Stopped(f"There are local changes here ({listed}{'…' if len(blocking) > 5 else ''}). Commit or stash them; this command will not throw work away.")
    print(f"{OK} branch   {branch}" + (f"  ({len(dirty)} untracked/ignored file(s) left alone)" if dirty else ""))
    return branch


def stage_fetch(branch: str) -> tuple[str, str, int, int]:
    remote = git("config", f"branch.{branch}.remote", check=False) or "origin"
    git("fetch", remote, branch)
    local = git("rev-parse", "HEAD")
    upstream = git("rev-parse", f"{remote}/{branch}")
    behind = int(git("rev-list", "--count", f"HEAD..{remote}/{branch}") or 0)
    ahead = int(git("rev-list", "--count", f"{remote}/{branch}..HEAD") or 0)
    print(f"{OK} fetch    {remote}/{branch}  {behind} to come, {ahead} of yours not pushed")
    return local, upstream, behind, ahead


def stage_pull(branch: str, behind: int, ahead: int, *, check_only: bool) -> tuple[bool, list[str]]:
    if behind == 0:
        print(f"{SKIP} pull     already up to date")
        return False, []
    if ahead:
        raise Stopped(
            f"This branch has {ahead} commit(s) the remote does not, so it cannot fast-forward. "
            "Push or rebase them yourself; this command will not rewrite your history."
        )
    remote = git("config", f"branch.{branch}.remote", check=False) or "origin"
    changed = git("diff", "--name-only", "HEAD", f"{remote}/{branch}", "--").splitlines()
    if check_only:
        print(f"{SKIP} pull     would fast-forward {behind} commit(s), {len(changed)} file(s)")
        return False, changed
    git("merge", "--ff-only", f"{remote}/{branch}")
    print(f"{OK} pull     fast-forwarded {behind} commit(s), {len(changed)} file(s)")
    return True, changed


def stage_deps(changed: list[str], *, check_only: bool) -> bool:
    needed = [f for f in changed if Path(f).name in DEP_FILES]
    if not needed:
        print(f"{SKIP} deps     unchanged")
        return False
    if check_only:
        print(f"{SKIP} deps     would reinstall ({', '.join(needed)})")
        return False
    pip = ROOT / ".venv" / "bin" / "pip"
    if not pip.exists():
        raise Stopped("There is no .venv here. Run `make venv` once, then try again.")
    out = subprocess.run([str(pip), "install", "-q", "-e", ".[dev]"], cwd=ROOT, capture_output=True, text=True, timeout=900)
    if out.returncode != 0:
        raise Stopped("Installing the dependencies failed:\n" + (out.stderr or out.stdout)[-600:])
    print(f"{OK} deps     reinstalled ({', '.join(needed)})")
    return True


def stage_restart(*, check_only: bool, port: int) -> None:
    if check_only:
        print(f"{SKIP} restart  would restart the assistant and whisper-server")
        return
    import launch_common as lc

    domain = f"gui/{lc.uid()}"
    failed = []
    for label in lc.AGENTS:
        out = subprocess.run(["launchctl", "kickstart", "-k", f"{domain}/{label}"], capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            failed.append(f"{label}: {(out.stderr or '').strip() or 'launchctl refused'}")
    if failed:
        raise Stopped(
            "The services would not restart:\n  " + "\n  ".join(failed)
            + "\nIf they were never installed, run `make install` once. Your code IS updated; only the restart failed."
        )
    print(f"{OK} restart  assistant and whisper-server kicked")


def stage_verify(*, check_only: bool, port: int) -> bool:
    import launch_common as lc

    if check_only:
        print(f"{SKIP} verify   would read /health back")
        return True
    health = lc.wait_for_health(f"http://127.0.0.1:{port}/health", timeout_s=90)
    if not health:
        raise Stopped("The backend did not come back healthy within 90 seconds. `make logs` shows why; nothing was undone.")
    print(f"{OK} verify   {lc.summarise_health(health)}")
    return True


def report(port: int) -> None:
    """The concise status the owner reads at the end. Same shape as crooks-status."""
    from scripts.status import show

    print()
    show(port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="say what would happen; change nothing")
    parser.add_argument("--branch", default="", help="the branch this checkout should be on")
    args = parser.parse_args(argv)

    from config.settings import get_settings

    port = get_settings().port
    print("crooks-update" + ("  (check only — nothing will change)" if args.check else ""))
    try:
        stage_find()
        branch = stage_branch(args.branch)
        _, _, behind, ahead = stage_fetch(branch)
        moved, changed = stage_pull(branch, behind, ahead, check_only=args.check)
        stage_deps(changed, check_only=args.check)
        if moved:
            stage_restart(check_only=args.check, port=port)
            stage_verify(check_only=args.check, port=port)
        elif not args.check:
            print(f"{SKIP} restart  nothing changed, so nothing was restarted")
    except Stopped as exc:
        print(f"{FAIL} {exc}")
        print("\nNothing was changed. Fix the line above and run crooks-update again.")
        return 1
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"{FAIL} {type(exc).__name__}: {exc}")
        return 1
    if not args.check:
        report(port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
