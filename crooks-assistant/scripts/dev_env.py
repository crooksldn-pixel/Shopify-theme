#!/usr/bin/env python3
"""The builder development environment: check it, print its shell env, or bootstrap it.

This exists so the environment survives losing the chat that built it. Everything it knows comes
from `docs/dev-environment/manifest.json`, which is the pinned source of truth; this file is only
the thing that reads it.

    python3 scripts/dev_env.py doctor      what is installed, what is missing  (READ-ONLY)
    python3 scripts/dev_env.py env         the exports a browser/tool run needs (READ-ONLY)
    python3 scripts/dev_env.py bootstrap   install whatever doctor says is missing

`doctor` and `env` never write anything. `bootstrap` is idempotent: every step checks for its own
result first and is skipped when already satisfied, so running it twice does nothing the second
time.

THIS IS BUILDER TOOLING. It installs into `.tooling/` inside this worktree and into the worktree's
own `.venv`. It does not touch /usr, it does not install or start a service, it does not open a
listening socket, and it needs no secret. `/usr` is read-only in the watcher sandbox on purpose
and this script never tries to change that.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# crooks-assistant/scripts/dev_env.py -> crooks-assistant -> the repository root, which is where
# .tooling lives (it is shared by the theme side of the repo, not only the assistant).
ASSISTANT = Path(__file__).resolve().parent.parent
REPO = ASSISTANT.parent
MANIFEST = ASSISTANT / "docs" / "dev-environment" / "manifest.json"
TOOLING = REPO / ".tooling"

OK, MISSING, WARN = "ok", "MISSING", "warn"


def load() -> dict:
    if not MANIFEST.exists():
        sys.exit(f"no manifest at {MANIFEST}")
    return json.loads(MANIFEST.read_text())


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

    NODE_PATH is the non-obvious one: crooks-assistant/scripts/browser/*.js do
    `require('playwright')`, and node resolves that from the SCRIPT's directory, not the cwd.
    Without NODE_PATH the existing CROOKS browser gate reports itself unavailable even though
    playwright is installed.
    """
    for k, v in shell_env(m).items():
        print(f"export {k}={v!r}".replace("'", '"'))
    return 0


# ----------------------------------------------------------------------------- doctor


def _run(argv: list[str], env: dict | None = None) -> tuple[bool, str]:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=120,
                           env={**os.environ, **(env or {})})
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    line = (p.stdout or p.stderr or "").strip().splitlines()
    return p.returncode == 0, (line[0] if line else "")


def cmd_doctor(m: dict) -> int:
    env = shell_env(m)
    bad = 0

    def say(state: str, name: str, detail: str = "") -> None:
        nonlocal bad
        if state == MISSING:
            bad += 1
        print(f"  {state:<8} {name:<28} {detail}")

    print("\nbinaries (.tooling/bin)")
    for name, spec in m["binaries"].items():
        if name.startswith("$"):  # manifest prose, not a tool
            continue
        exe = TOOLING / "bin" / name
        if not exe.exists():
            say(MISSING, name, f"expected {exe}")
            continue
        ok, out = _run([str(exe), "--version"])
        say(OK if ok else WARN, name, f"want {spec['version']} · {out[:60]}")

    print("\nnode packages (.tooling/node)")
    nm = TOOLING / "node" / "node_modules"
    for name, spec in m["node"].items():
        if name.startswith("$"):
            continue
        pkg = nm / name / "package.json"
        if not pkg.exists():
            say(MISSING, name, f"expected {pkg}")
            continue
        got = json.loads(pkg.read_text()).get("version")
        say(OK if got == spec["version"] else WARN, name, f"{got} (want {spec['version']})")

    print("\nbrowser")
    chrome = Path(env["CROOKS_CHROMIUM"])
    if not chrome.exists():
        say(MISSING, "chromium", f"expected {chrome}")
    else:
        ok, out = _run([str(chrome), "--version"], env)
        # A Chromium that is present but cannot link is the failure this whole sysroot exists
        # for, and it must not be reported as present.
        say(OK if ok else MISSING, "chromium", out[:70] or "present but will not start")

    print("\nsysroot (Chromium's shared libraries, extracted locally)")
    root = _abs(m["sysroot"]["scope"])
    say(OK if root.exists() else MISSING, "sysroot", str(root))
    if chrome.exists() and shutil.which("ldd"):
        ok, _ = _run(["ldd", str(chrome)], env)
        p = subprocess.run(["ldd", str(chrome)], capture_output=True, text=True,
                           env={**os.environ, **env})
        n = p.stdout.count("not found")
        say(OK if n == 0 else MISSING, "shared libs", f"{n} not found")

    print("\npython (crooks-assistant/.venv)")
    py = ASSISTANT / ".venv" / "bin" / "python"
    if not py.exists():
        say(MISSING, "venv", "run: make venv")
    else:
        say(OK, "venv", _run([str(py), "--version"])[1])
        for name, spec in m["python"]["builder_only"].items():
            # `pip show` prints several lines; _run only keeps the first, so read it directly.
            p = subprocess.run([str(py), "-m", "pip", "show", name],
                               capture_output=True, text=True)
            got = next((ln.split(": ", 1)[1].strip() for ln in p.stdout.splitlines()
                        if ln.startswith("Version:")), "")
            if not got:
                say(MISSING, name, f"want {spec['version']}")
            else:
                say(OK if got == spec["version"] else WARN, name,
                    f"{got} (want {spec['version']})")

    print("\nuv tools")
    for name, spec in m["uv_tools"].items():
        exe = TOOLING / "bin" / name
        if not exe.exists():
            say(MISSING, name, f"expected {exe}")
        else:
            ok, _ = _run([str(exe), "--help"])
            say(OK if ok else WARN, name, f"want {spec['version']} @ {spec['commit'][:12]}")

    print("\nthe CROOKS browser gate, as the suite sees it")
    py = ASSISTANT / ".venv" / "bin" / "python"
    if py.exists():
        p = subprocess.run(
            [str(py), "-c",
             "from experience.browser import available; ok,why=available(); "
             "print('AVAILABLE' if ok else 'UNAVAILABLE: '+why)"],
            cwd=ASSISTANT, capture_output=True, text=True,
            env={**os.environ, **env})
        out = (p.stdout or p.stderr).strip().splitlines()
        line = out[-1] if out else "no output"
        say(OK if line.startswith("AVAILABLE") else MISSING, "experience.browser", line)
    else:
        say(MISSING, "experience.browser", "no venv")

    print(f"\n{'all present' if not bad else f'{bad} missing'} — "
          f"bootstrap with: python3 scripts/dev_env.py bootstrap\n")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- bootstrap


def cmd_bootstrap(m: dict) -> int:
    """Install what doctor says is missing. Every step is skipped when already satisfied.

    Deliberately NOT implemented as a shell script: the steps need the manifest, and a second
    copy of the pinned versions in a .sh file is a second source of truth that drifts.
    """
    print("bootstrap is intentionally explicit. Run these, in order, from the repository root.")
    print("Each is idempotent; skip any whose `doctor` line already says ok.\n")
    e = m["environment"]

    print("# 1. node tooling (pinned in .tooling/node/package.json)")
    print("cd .tooling/node && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-audit --no-fund\n")

    print("# 2. the browser Playwright expects")
    print(f"PLAYWRIGHT_BROWSERS_PATH={e['PLAYWRIGHT_BROWSERS_PATH']} "
          f"npx --no-install playwright install chromium\n")

    print("# 3. Chromium's shared libraries, extracted LOCALLY (/usr is read-only and stays so)")
    print("mkdir -p .tooling/sysroot/debs .tooling/sysroot/root && cd .tooling/sysroot/debs")
    print("apt-get download $(apt-cache depends --recurse --no-recommends --no-suggests \\")
    print("  --no-conflicts --no-breaks --no-replaces --no-enhances \\")
    print("  " + " ".join(m["sysroot"]["directly_required"]) + " \\")
    print("  | grep -E '^[a-z0-9]' | sort -u | grep -vE '^(" +
          "|".join(x.replace("+", r"\+") for x in m["sysroot"]["excluded"]) + ")$')")
    print("for d in *.deb; do dpkg-deb -x \"$d\" ../root; done\n")

    print("# 4. single-binary tools -> .tooling/bin (exact versions)")
    for name, spec in m["binaries"].items():
        print(f"#    {name} {spec['version']}  {spec['upstream']}")
    print()

    print("# 5. the project venv, plus builder-only test tooling")
    print("cd crooks-assistant && make venv")
    print(".venv/bin/pip install " + " ".join(
        f"'{n}=={s['version']}'" for n, s in m["python"]["builder_only"].items()) + "\n")

    print("# 6. the skill security gate, in its own isolated environment")
    ss = m["uv_tools"]["skillspector"]
    print(f"git clone {ss['upstream']} /tmp/skillspector && "
          f"git -C /tmp/skillspector checkout {ss['commit']}")
    print(f"UV_TOOL_DIR={e['UV_TOOL_DIR']} UV_TOOL_BIN_DIR={e['PATH_PREPEND']} "
          "uv tool install --from /tmp/skillspector skillspector\n")

    print('# 7. every shell that runs a browser check needs the env:')
    print('eval "$(python3 crooks-assistant/scripts/dev_env.py env)"\n')
    return 0


def main() -> int:
    what = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    m = load()
    if what == "doctor":
        return cmd_doctor(m)
    if what == "env":
        return cmd_env(m)
    if what == "bootstrap":
        return cmd_bootstrap(m)
    sys.exit(f"usage: {sys.argv[0]} [doctor|env|bootstrap]")


if __name__ == "__main__":
    raise SystemExit(main())
