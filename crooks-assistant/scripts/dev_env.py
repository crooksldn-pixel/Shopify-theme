#!/usr/bin/env python3
"""The builder development environment: check it, print its shell env, or print its build plan.

This exists so the environment survives losing the chat that built it. Everything it knows comes
from `docs/dev-environment/manifest.json` and the reconstruction inputs committed beside it; this
file is only the thing that reads them.

    python3 scripts/dev_env.py doctor      is this environment the pinned one  (READ-ONLY)
    python3 scripts/dev_env.py env         the exports a browser/tool run needs (READ-ONLY)
    python3 scripts/dev_env.py plan        the steps that rebuild it from a clean checkout

All three are read-only. `plan` PRINTS a build plan and does not execute it; that separation is
deliberate and is why the command is no longer called `bootstrap`. Nothing here installs anything.

`doctor` FAILS CLOSED. A tool that is missing, that will not run, or that reports a version other
than the pinned one is a failure and exits non-zero. Only findings that are genuinely not
decidable here are advisory, and each one says why on its own line. Advisory findings never
change the exit code, and nothing that is merely inconvenient is advisory.

THIS IS BUILDER TOOLING. It reads `.tooling/` inside this worktree and the worktree's own
`.venv`. It does not touch /usr, it does not install or start a service, it does not open a
listening socket, and it needs no secret. `/usr` is read-only in the watcher sandbox on purpose
and this script never tries to change that.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# crooks-assistant/scripts/dev_env.py -> crooks-assistant -> the repository root, which is where
# .tooling lives (it is shared by the theme side of the repo, not only the assistant).
ASSISTANT = Path(__file__).resolve().parent.parent
REPO = ASSISTANT.parent
DEV_ENV = ASSISTANT / "docs" / "dev-environment"
MANIFEST = DEV_ENV / "manifest.json"
TOOLING = REPO / ".tooling"

# Reconstruction inputs. Every one of these is COMMITTED, because `.tooling/` is gitignored and a
# plan whose first step reads a gitignored file is a plan that cannot run on a fresh checkout.
NODE_PACKAGE = DEV_ENV / "node-package.json"
NODE_LOCK = DEV_ENV / "node-package-lock.json"
SYSROOT_PACKAGES = DEV_ENV / "sysroot-packages.txt"
SYSROOT_CHECKSUMS = DEV_ENV / "sysroot-packages.sha256"
BINARY_CHECKSUMS = DEV_ENV / "binaries.sha256"

OK, FAIL, ADVISORY = "ok", "FAIL", "advisory"

# Two or more dot-separated numbers. One number is not a version: `shellcheck --version` prints
# "license: GNU General Public License, version 3", and matching that would be how a wrong
# shellcheck passes.
_VERSION = re.compile(r"\d+(?:\.\d+)+")


class ManifestError(Exception):
    """The manifest is not usable. Reported as a message, never as a traceback."""


def load() -> dict:
    if not MANIFEST.exists():
        raise ManifestError(f"no manifest at {MANIFEST}")
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{MANIFEST} is not valid JSON: {exc}") from exc


def entries(section: dict, *, required: tuple[str, ...], where: str) -> dict[str, dict]:
    """The real tools in a manifest section, with the manifest's own prose filtered out.

    `$comment` keys carry the prose that makes the manifest readable, and they are the reason
    the rejected candidate's plan generator crashed: doctor skipped them and the plan did not,
    so `spec['version']` ran against a string. One filter, used by both, is the fix.

    A key that survives the filter must be an object carrying every `required` field. A
    half-written tool entry is a manifest error with a name and a reason attached, not a
    TypeError from four frames down.
    """
    out: dict[str, dict] = {}
    for name, spec in section.items():
        if name.startswith("$"):
            continue
        if not isinstance(spec, dict):
            raise ManifestError(
                f"{where}.{name} is a {type(spec).__name__}, expected an object. "
                f"Manifest prose belongs under a $-prefixed key.")
        absent = [field for field in required if field not in spec]
        if absent:
            raise ManifestError(f"{where}.{name} is missing {', '.join(absent)}")
        out[name] = spec
    return out


def _abs(rel: str) -> Path:
    """Manifest paths are written relative to the repository root."""
    return REPO / rel


# ----------------------------------------------------------------------------- env


def shell_env(m: dict) -> dict[str, str]:
    e = m["environment"]
    out = {
        "PLAYWRIGHT_BROWSERS_PATH": str(_abs(e["PLAYWRIGHT_BROWSERS_PATH"])),
        "NODE_PATH": str(_abs(e["NODE_PATH"])),
        "CROOKS_CHROMIUM": str(_abs(e["CROOKS_CHROMIUM"])),
        "LD_LIBRARY_PATH": ":".join(str(_abs(p)) for p in e["LD_LIBRARY_PATH"].split(":")),
        "UV_TOOL_DIR": str(_abs(e["UV_TOOL_DIR"])),
    }
    out["PATH"] = f"{_abs(e['PATH_PREPEND'])}:{os.environ.get('PATH', '')}"
    return out


def cmd_env(m: dict) -> int:
    """Print exports for `eval "$(python3 scripts/dev_env.py env)"`.

    Every value goes through shlex.quote, which is the only correct answer here. The rejected
    candidate used Python's repr and then replaced the quotes, which produces a DOUBLE-quoted
    shell word: the shell then expands `$(...)`, `` `...` `` and `$VAR` inside it. A checkout at
    /tmp/crooks-$(printf CROOKS_ENV_PROBE) exported NODE_PATH=/tmp/crooks-CROOKS_ENV_PROBE/...,
    which is both the wrong directory and a command the generator chose to run. shlex.quote
    single-quotes, and single quotes in the value are escaped rather than ended, so a path
    round-trips literally whatever is in it.

    NODE_PATH is the non-obvious one: crooks-assistant/scripts/browser/*.js do
    `require('playwright')`, and node resolves that from the SCRIPT's directory, not the cwd.
    Without NODE_PATH the existing CROOKS browser gate reports itself unavailable even though
    playwright is installed.
    """
    for k, v in shell_env(m).items():
        print(f"export {k}={shlex.quote(v)}")
    return 0


# ----------------------------------------------------------------------------- doctor


def _probe(argv: list[str], env: dict | None = None) -> tuple[bool, str]:
    """Run a check command with a timeout. Returns (exited zero, all of its output).

    All of it, not the first line: `shellcheck --version` puts the number on line two, and
    reading only line one is how the rejected candidate displayed a version beside a pin
    without ever comparing the two.
    """
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=120,
                           env={**os.environ, **(env or {})})
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    return p.returncode == 0, ((p.stdout or "") + (p.stderr or "")).strip()


def _verify_argv(verify: str, exe: Path) -> list[str]:
    """The manifest's own verify command, with argv[0] bound to the pinned executable.

    shlex.split and never a shell: the manifest is data, and data that becomes a command line
    is the same defect as BE-03 wearing a different hat.
    """
    argv = shlex.split(verify)
    if not argv:
        raise ManifestError(f"empty verify command for {exe.name}")
    return [str(exe), *argv[1:]]


def _versions(text: str) -> set[str]:
    return set(_VERSION.findall(text))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_checksums(path: Path) -> dict[str, str]:
    """sha256sum(1) format: `<hex>  <path>`, comments and blank lines ignored."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        out[name.strip()] = digest.strip()
    return out


def node_package_findings(m: dict) -> list[str]:
    """Why the committed node inputs and the manifest might disagree. Empty means they agree.

    The manifest is the source of truth for the pins; `node-package.json` is what npm actually
    consumes and `node-package-lock.json` is what `npm ci` installs byte for byte. Three files
    is three chances to drift, so the drift is checked rather than trusted — and it is checked
    from committed files, so it works on a fresh checkout with no `.tooling/` at all.
    """
    found: list[str] = []
    for path in (NODE_PACKAGE, NODE_LOCK):
        if not path.exists():
            found.append(f"{path.relative_to(REPO)} is missing")
    if found:
        return found

    want = {n: s["version"]
            for n, s in entries(m["node"], required=("version",), where="node").items()}
    declared = json.loads(NODE_PACKAGE.read_text(encoding="utf-8")).get("dependencies", {})
    for name, version in sorted(want.items()):
        if name not in declared:
            found.append(f"node-package.json does not declare {name}")
        elif declared[name] != version:
            found.append(f"node-package.json pins {name} {declared[name]}, manifest says {version}")
    for name in sorted(set(declared) - set(want)):
        found.append(f"node-package.json declares {name}, which the manifest does not pin")

    locked = json.loads(NODE_LOCK.read_text(encoding="utf-8")).get("packages", {})
    for name, version in sorted(want.items()):
        entry = locked.get(f"node_modules/{name}")
        if entry is None:
            found.append(f"node-package-lock.json has no entry for {name}")
        elif entry.get("version") != version:
            found.append(
                f"node-package-lock.json locks {name} {entry.get('version')}, "
                f"manifest says {version}")
        elif not entry.get("integrity"):
            found.append(f"node-package-lock.json has no integrity hash for {name}")
    return found


def cmd_doctor(m: dict) -> int:
    """Is this worktree the pinned environment? Non-zero if it is not, for any reason.

    The rejected candidate counted only MISSING, so a tool that was present and broken, or
    present at the wrong version, printed `warn` and the run still ended `all present` with
    exit 0. Every check below is now either a required fact (ok/FAIL) or an explicitly
    undecidable one (advisory, with the reason printed).
    """
    env = shell_env(m)
    bad = 0
    advisories = 0

    def say(state: str, name: str, detail: str = "") -> None:
        nonlocal bad, advisories
        if state == FAIL:
            bad += 1
        elif state == ADVISORY:
            advisories += 1
        print(f"  {state:<8} {name:<28} {detail}")

    def version_of(exe: Path, spec: dict, name: str, want: str, env: dict | None = None) -> None:
        """Run the pinned tool's own verify command and require the pinned version in its output."""
        ok, out = _probe(_verify_argv(spec["verify"], exe), env)
        if not ok:
            say(FAIL, name, f"`{spec['verify']}` failed: {out.splitlines()[0][:60] if out else ''}")
            return
        found = _versions(out)
        if want in found:
            say(OK, name, want)
        else:
            say(FAIL, name, f"want {want}, reported {', '.join(sorted(found)) or 'no version'}")

    print("\nbinaries (.tooling/bin)")
    for name, spec in entries(m["binaries"],
                              required=("version", "upstream", "verify"),
                              where="binaries").items():
        exe = TOOLING / "bin" / name
        if not exe.exists():
            say(FAIL, name, f"missing — expected {exe}")
            continue
        version_of(exe, spec, name, spec["version"])

    print("\nbinary integrity (sha256, pinned in docs/dev-environment/binaries.sha256)")
    if not BINARY_CHECKSUMS.exists():
        say(FAIL, "binaries.sha256", f"missing — expected {BINARY_CHECKSUMS}")
    else:
        recorded = read_checksums(BINARY_CHECKSUMS)
        mismatched = []
        for rel, digest in sorted(recorded.items()):
            path = REPO / rel
            if not path.exists():
                mismatched.append(f"{rel} is absent")
            elif _sha256(path) != digest:
                mismatched.append(f"{rel} is not the pinned artifact")
        if mismatched:
            for problem in mismatched:
                say(FAIL, "sha256", problem)
        else:
            say(OK, "sha256", f"{len(recorded)} artifacts match")

    print("\nnode packages (.tooling/node)")
    nm = TOOLING / "node" / "node_modules"
    for name, spec in entries(m["node"], required=("version",), where="node").items():
        pkg = nm / name / "package.json"
        if not pkg.exists():
            say(FAIL, name, f"missing — expected {pkg}")
            continue
        got = json.loads(pkg.read_text(encoding="utf-8")).get("version")
        say(OK if got == spec["version"] else FAIL, name,
            spec["version"] if got == spec["version"] else f"{got} (want {spec['version']})")

    print("\nnode reconstruction inputs (committed, readable without .tooling)")
    problems = node_package_findings(m)
    for problem in problems:
        say(FAIL, "node inputs", problem)
    if not problems:
        say(OK, "node inputs", "package.json and lock agree with the manifest")

    print("\nbrowser")
    chrome = Path(env["CROOKS_CHROMIUM"])
    want_chrome = m["browsers"]["chromium"]["chromium_version"]
    if not chrome.exists():
        say(FAIL, "chromium", f"missing — expected {chrome}")
    else:
        # A Chromium that is present but cannot link is the failure this whole sysroot exists
        # for, and it must not be reported as present.
        ok, out = _probe([str(chrome), "--version"], env)
        if not ok:
            say(FAIL, "chromium", out.splitlines()[0][:70] if out else "will not start")
        elif want_chrome in _versions(out):
            say(OK, "chromium", want_chrome)
        else:
            say(FAIL, "chromium", f"want {want_chrome}, reported {out.splitlines()[0][:50]}")

    print("\nsysroot (Chromium's shared libraries, extracted locally)")
    root = _abs(m["sysroot"]["scope"])
    say(OK if root.exists() else FAIL, "sysroot", str(root))
    for path in (SYSROOT_PACKAGES, SYSROOT_CHECKSUMS):
        say(OK if path.exists() else FAIL, path.name,
            "committed" if path.exists() else f"missing — expected {path}")
    if chrome.exists() and shutil.which("ldd"):
        try:
            p = subprocess.run(["ldd", str(chrome)], capture_output=True, text=True, timeout=120,
                               env={**os.environ, **env})
            n = p.stdout.count("not found")
            say(OK if n == 0 else FAIL, "shared libs", f"{n} not found")
        except (OSError, subprocess.SubprocessError) as exc:
            say(FAIL, "shared libs", f"ldd failed: {exc}")

    print("\npython (crooks-assistant/.venv)")
    py = ASSISTANT / ".venv" / "bin" / "python"
    if not py.exists():
        say(FAIL, "venv", "missing — run: make venv")
    else:
        ok, out = _probe([str(py), "--version"])
        want_py = m["python"]["interpreter"]
        if not ok:
            say(FAIL, "venv", f"will not start: {out[:60]}")
        else:
            say(OK if want_py in _versions(out) else FAIL, "venv",
                out.strip()[:40] if want_py in _versions(out) else
                f"want {want_py}, reported {out.strip()[:40]}")
        for name, spec in entries(m["python"]["builder_only"], required=("version",),
                                  where="python.builder_only").items():
            # `pip show` prints several lines and exits 0 for a package it did not find, so the
            # Version: line is what decides, not the return code.
            ok, out = _probe([str(py), "-m", "pip", "show", name])
            got = next((ln.split(": ", 1)[1].strip() for ln in out.splitlines()
                        if ln.startswith("Version:")), "")
            if not got:
                say(FAIL, name, f"not installed (want {spec['version']})")
            else:
                say(OK if got == spec["version"] else FAIL, name,
                    spec["version"] if got == spec["version"]
                    else f"{got} (want {spec['version']})")

    print("\nuv tools")
    for name, spec in entries(m["uv_tools"],
                              required=("version", "commit", "verify"),
                              where="uv_tools").items():
        exe = TOOLING / "bin" / name
        if not exe.exists():
            say(FAIL, name, f"missing — expected {exe}")
            continue
        version_of(exe, spec, name, spec["version"])
        # The one genuinely undecidable check in this file, and it says so rather than passing
        # quietly. `uv tool install --from <local clone>` records a path, not a revision, so the
        # installed artifact carries no commit to compare the pin against. Advisory means "this
        # was not verified", and the remedy is in docs/DEV_ENVIRONMENT.md §9.
        say(ADVISORY, f"{name} commit", f"{spec['commit'][:12]} pinned at install; the installed "
                                        "artifact records no revision, so it is not re-derivable")

    print("\nthe CROOKS browser gate, as the suite sees it")
    if py.exists():
        p = subprocess.run(
            [str(py), "-c",
             "from experience.browser import available; ok,why=available(); "
             "print('AVAILABLE' if ok else 'UNAVAILABLE: '+why)"],
            cwd=ASSISTANT, capture_output=True, text=True, timeout=120,
            env={**os.environ, **env})
        out = (p.stdout or p.stderr).strip().splitlines()
        line = out[-1] if out else "no output"
        say(OK if line.startswith("AVAILABLE") else FAIL, "experience.browser", line)
    else:
        say(FAIL, "experience.browser", "no venv")

    summary = "the pinned environment" if not bad else f"{bad} FAILED"
    if advisories:
        summary += f" · {advisories} advisory (printed above, not counted)"
    print(f"\n{summary} — rebuild steps: python3 scripts/dev_env.py plan\n")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- plan


def plan_inputs() -> tuple[Path, ...]:
    """The committed files the plan consumes. A fresh checkout must contain all of them."""
    return (MANIFEST, NODE_PACKAGE, NODE_LOCK, SYSROOT_PACKAGES, SYSROOT_CHECKSUMS,
            BINARY_CHECKSUMS, Path(__file__).resolve())


def plan_steps(m: dict) -> list[tuple[str, list[str]]]:
    """(heading, commands) for rebuilding this environment from a clean checkout.

    Every command runs FROM THE REPOSITORY ROOT and never leaves it: a bare `cd` that the next
    command silently inherits was one of the reasons the rejected plan could not be followed.
    Where a step genuinely needs a working directory it uses a subshell, which ends at the
    closing parenthesis. Every path is shlex.quote'd for the same reason `env` is.
    """
    q = shlex.quote
    e = m["environment"]
    steps: list[tuple[str, list[str]]] = []

    rel = lambda p: q(str(Path(p).relative_to(REPO)))  # noqa: E731 - a name for one expression

    steps.append(("1. node tooling, installed from the committed lock", [
        "mkdir -p .tooling/node",
        f"cp {rel(NODE_PACKAGE)} .tooling/node/package.json",
        f"cp {rel(NODE_LOCK)} .tooling/node/package-lock.json",
        "( cd .tooling/node && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 "
        "npm ci --no-audit --no-fund )",
    ]))

    steps.append((f"2. the browser Playwright {m['node']['playwright']['version']} expects", [
        f"( cd .tooling/node && PLAYWRIGHT_BROWSERS_PATH={q(str(_abs(e['PLAYWRIGHT_BROWSERS_PATH'])))} "
        "npx --no-install playwright install chromium )",
    ]))

    steps.append((
        "3. Chromium's shared libraries, extracted LOCALLY (/usr is read-only and stays so)", [
            "mkdir -p .tooling/sysroot/debs .tooling/sysroot/root",
            # The inventory carries a prose header, so the pins are read out of it rather than
            # fed to xargs whole — a '#' reaching apt-get is BE-01's mistake in another file.
            f"( cd .tooling/sysroot/debs && awk 'NF && $1 !~ /^#/ {{print $1}}' "
            f"{q(str(SYSROOT_PACKAGES))} | xargs -r apt-get download )",
            f"( cd .tooling/sysroot/debs && sha256sum -c {q(str(SYSROOT_CHECKSUMS))} )",
            "for d in .tooling/sysroot/debs/*.deb; do dpkg-deb -x \"$d\" .tooling/sysroot/root; done",
        ]))

    binaries = entries(m["binaries"], required=("version", "upstream", "verify"), where="binaries")
    fetch = [f"#   {name:<12} {spec['version']:<8} {spec['upstream']}"
             + (f"  asset: {spec['asset']}" if "asset" in spec else "")
             for name, spec in binaries.items()]
    steps.append(("4. single-binary tools -> .tooling/bin", [
        "# NOT EXECUTABLE YET — see 'reconstruction status' below. The pins are exact and the",
        "# integrity check is committed; the release asset URL and tag for each tool are not",
        "# recorded in the manifest, and recording them needs an approved package-fetch policy.",
        *fetch,
        f"sha256sum -c {rel(BINARY_CHECKSUMS)}",
    ]))

    builder_only = entries(m["python"]["builder_only"], required=("version",),
                           where="python.builder_only")
    steps.append((f"5. the project venv (python {m['python']['interpreter']}) "
                  "plus builder-only test tooling", [
        "( cd crooks-assistant && make venv )",
        "crooks-assistant/.venv/bin/pip install " + " ".join(
            q(f"{n}=={s['version']}") for n, s in builder_only.items()),
    ]))

    ss = m["uv_tools"]["skillspector"]
    steps.append(("6. the skill security gate, in its own isolated environment", [
        f"git clone {q(ss['upstream'])} /tmp/skillspector",
        f"git -C /tmp/skillspector checkout {q(ss['commit'])}",
        f"UV_TOOL_DIR={q(str(_abs(e['UV_TOOL_DIR'])))} "
        f"UV_TOOL_BIN_DIR={q(str(_abs(e['PATH_PREPEND'])))} "
        "uv tool install --from /tmp/skillspector skillspector",
    ]))

    steps.append(("7. the env every shell that runs a browser check needs, then the check", [
        'eval "$(python3 crooks-assistant/scripts/dev_env.py env)"',
        "python3 crooks-assistant/scripts/dev_env.py doctor",
    ]))
    return steps


def cmd_plan(m: dict) -> int:
    """Print the rebuild plan. This command installs nothing; step 7 checks what did.

    It is a generator, not an installer, and it is named for what it is. The rejected candidate
    called this `bootstrap`, documented it as "install whatever doctor says is missing" and as
    idempotent, and then printed instructions — so `bootstrap` reporting success proved only
    that text had been printed.
    """
    print("A plan, not an installer: nothing below runs until you run it.")
    print("Every command is written to be run FROM THE REPOSITORY ROOT:")
    print(f"  {REPO}\n")
    print("Steps are individually idempotent; skip any whose `doctor` line already says ok.")

    for heading, commands in plan_steps(m):
        print(f"\n# {heading}")
        for command in commands:
            print(command)

    missing = [str(p.relative_to(REPO)) for p in plan_inputs() if not p.exists()]
    print("\n# reconstruction status — read this before trusting the plan above")
    if missing:
        print("# INPUTS MISSING from this checkout, so the plan cannot be followed here:")
        for path in missing:
            print(f"#   {path}")
    else:
        print("# Every input the plan reads is committed and present in this checkout.")
    print("# BLOCKED: steps 1-3 and 6 fetch from the network (npm, Playwright's CDN, apt and")
    print("#   GitHub) and step 4 cannot be written as commands at all until each tool's release")
    print("#   tag and asset URL are pinned in the manifest. Both need an approved package-fetch")
    print("#   policy. Until one exists this plan has NOT been executed end to end, and no claim")
    print("#   that this environment has been rebuilt from scratch should be made. See")
    print("#   docs/DEV_ENVIRONMENT.md section 9.")
    return 0


def cmd_bootstrap(_: dict) -> int:
    """`bootstrap` is gone on purpose, and says so instead of quietly doing something else."""
    print("`bootstrap` never installed anything — it printed instructions and described itself\n"
          "as an idempotent installer, so its exit code meant only that text had been printed.\n"
          "It is now named for what it does:\n\n"
          "    python3 scripts/dev_env.py plan\n\n"
          "Executing that plan needs an approved package-fetch policy; see\n"
          "crooks-assistant/docs/DEV_ENVIRONMENT.md section 9.", file=sys.stderr)
    return 2


def main() -> int:
    what = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    commands = {"doctor": cmd_doctor, "env": cmd_env, "plan": cmd_plan,
                "bootstrap": cmd_bootstrap}
    if what not in commands:
        sys.exit(f"usage: {sys.argv[0]} [doctor|env|plan]")
    try:
        return commands[what](load())
    except ManifestError as exc:
        sys.exit(f"{MANIFEST.name}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
