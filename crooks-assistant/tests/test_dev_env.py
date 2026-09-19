"""The builder environment script, against the four defects an independent review reproduced.

Candidate `9a27bc4` was rejected as the reproducible Dev Team foundation with four findings,
recorded in product memory as BUILDER_ENVIRONMENT_REVIEW.md:

    BE-01  `bootstrap` crashed on its own committed manifest
    BE-02  `doctor` returned success for wrong versions and failed tools
    BE-03  generated shell exports executed command substitution found in a checkout path
    BE-04  a fresh checkout could not reconstruct the environment

Every test here fails against that candidate and passes against the repair, which is the only
reason any of them is worth running. They are offline: no network, no real tool and no real
browser is touched. The fixtures are shell scripts that answer `--version`, because the defect
being tested is what the script DECIDES about a tool's answer, not whether any tool works.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parent.parent / "scripts" / "dev_env.py"
DEV_ENV_DIR = Path(__file__).resolve().parent.parent / "docs" / "dev-environment"


def _import_at(root: Path):
    """Import the real dev_env.py as though the checkout were `root`.

    dev_env.py derives the repository root from its own __file__, so a copy placed in a
    disposable tree is the exact candidate code reading a disposable environment. This is how
    the review reproduced BE-02 and BE-03 without touching the builder.
    """
    scripts = root / "crooks-assistant" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    copy = scripts / "dev_env.py"
    copy.write_bytes(SOURCE.read_bytes())
    name = f"dev_env_fixture_{abs(hash(str(root)))}"
    spec = importlib.util.spec_from_file_location(name, copy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _script(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _fixture_manifest(*, chromium: str) -> dict:
    return {
        "environment": {
            "PLAYWRIGHT_BROWSERS_PATH": ".tooling/browsers",
            "NODE_PATH": ".tooling/node/node_modules",
            "CROOKS_CHROMIUM": ".tooling/browsers/chromium-1194/chrome",
            "LD_LIBRARY_PATH": ".tooling/sysroot/root/lib",
            "UV_TOOL_DIR": ".tooling/uv-tools",
            "PATH_PREPEND": ".tooling/bin",
        },
        "binaries": {
            "$comment": "prose, not a tool — BE-01 is what happens when this is not filtered",
            "shellcheck": {"version": "0.11.0", "upstream": "https://example.invalid/shellcheck",
                           "verify": "shellcheck --version"},
            "gitleaks": {"version": "8.30.1", "upstream": "https://example.invalid/gitleaks",
                         "verify": "gitleaks version"},
        },
        "node": {"$comment": "prose", "playwright": {"version": "1.56.1"}},
        "browsers": {"chromium": {"chromium_version": chromium}},
        "sysroot": {"scope": ".tooling/sysroot/root"},
        "python": {"interpreter": "3.12.3",
                   "builder_only": {"pytest-xdist": {"version": "3.8.0"}}},
        "uv_tools": {"skillspector": {"version": "2.11.2", "commit": "d162d9b343e559be1",
                                      "upstream": "https://example.invalid/skillspector",
                                      "verify": "skillspector --version"}},
    }


def _checkout(root: Path, *, tools: dict[str, str], node: str, pip: str, python: str,
              chromium: str, skillspector_exit: int = 0, chromium_pin: str = "141.0.7390.37"):
    """A complete disposable checkout: committed inputs, plus a .tooling tree of stand-ins.

    `tools`, `node`, `pip`, `python` and `chromium` are the versions the stand-ins REPORT. The
    manifest always pins the right ones, so passing a wrong value here is how a test says
    "this tool is present and is not the pinned one".
    """
    dev_env = root / "crooks-assistant" / "docs" / "dev-environment"
    dev_env.mkdir(parents=True, exist_ok=True)

    manifest = _fixture_manifest(chromium=chromium_pin)
    (dev_env / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    (dev_env / "node-package.json").write_text(
        json.dumps({"dependencies": {"playwright": "1.56.1"}}), encoding="utf-8")
    (dev_env / "node-package-lock.json").write_text(json.dumps(
        {"packages": {"node_modules/playwright": {"version": "1.56.1", "integrity": "sha512-x"}}}),
        encoding="utf-8")
    (dev_env / "sysroot-packages.txt").write_text("libnss3=2:3.98-1build1\n", encoding="utf-8")
    (dev_env / "sysroot-packages.sha256").write_text("# fixture\n", encoding="utf-8")

    for name, reported in tools.items():
        _script(root / ".tooling" / "bin" / name, f"#!/bin/sh\necho '{name} {reported}'\n")
    _script(root / ".tooling" / "bin" / "skillspector",
            f"#!/bin/sh\necho 'SkillSpector v2.11.2'\nexit {skillspector_exit}\n")
    _script(root / ".tooling" / "browsers" / "chromium-1194" / "chrome",
            f"#!/bin/sh\necho 'Chromium {chromium}'\n")

    lines = []
    for name in sorted(tools):
        path = root / ".tooling" / "bin" / name
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  .tooling/bin/{name}")
    (dev_env / "binaries.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    pkg = root / ".tooling" / "node" / "node_modules" / "playwright"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "package.json").write_text(json.dumps({"version": node}), encoding="utf-8")

    (root / ".tooling" / "sysroot" / "root" / "lib").mkdir(parents=True, exist_ok=True)

    _script(root / "crooks-assistant" / ".venv" / "bin" / "python", f"""#!/bin/sh
case "$*" in
  *--version*)  echo 'Python {python}' ;;
  *"pip show"*) echo 'Name: x'; echo 'Version: {pip}' ;;
  *)            echo 'AVAILABLE' ;;
esac
exit 0
""")
    return _import_at(root)


def _healthy(root: Path, **overrides):
    """A checkout where every stand-in reports exactly what the manifest pins."""
    defaults = dict(tools={"shellcheck": "0.11.0", "gitleaks": "8.30.1"}, node="1.56.1",
                    pip="3.8.0", python="3.12.3", chromium="141.0.7390.37")
    return _checkout(root, **{**defaults, **overrides})


# --------------------------------------------------------------------------------- BE-01


def test_be01_plan_survives_the_repositorys_own_committed_manifest(capsys):
    """The rejected `bootstrap` raised TypeError on the manifest committed beside it.

    `binaries` carries a string-valued `$comment` so the pins stay readable. doctor skipped
    `$`-prefixed keys and the plan generator did not, so it reached `spec['version']` with a
    string and died eighteen printed lines in:

        TypeError: string indices must be integers, not 'str'

    Nothing was wrong with the manifest. The public command simply could not complete with the
    inputs this repository ships, which is why no amount of prose about a working environment
    was worth anything. This runs against the real committed file, not a fixture.
    """
    dev_env = _import_at_source()
    # Whichever name this candidate gives the generator: the defect is that generating the
    # steps at all crashed, and a test that only knew the repaired name would report a missing
    # attribute instead of the TypeError that got the candidate rejected.
    generate = getattr(dev_env, "cmd_plan", None) or dev_env.cmd_bootstrap
    assert generate(dev_env.load()) == 0
    printed = capsys.readouterr().out
    for name in ("shellcheck", "gitleaks", "trivy", "uv"):
        assert name in printed, f"the plan never mentions {name}"
    assert "$comment" not in printed, "manifest prose leaked into the plan as a tool"


def test_be01_prose_is_filtered_and_a_malformed_tool_is_named(tmp_path):
    """One filter, used by doctor and plan alike, and a malformed entry gets a name.

    The fix is not "skip $comment in the plan too" — that is the same bug waiting for the next
    caller. `entries()` is the single place that decides what a tool is, and an entry that
    survives the filter without being a complete object is a manifest error carrying the key
    that is wrong, not a TypeError from four frames down.
    """
    dev_env = _import_at(tmp_path)
    section = {"$comment": "prose", "$note": ["more", "prose"],
               "real": {"version": "1.0.0", "upstream": "u", "verify": "real --version"}}
    kept = dev_env.entries(section, required=("version", "upstream", "verify"), where="binaries")
    assert list(kept) == ["real"]

    with pytest.raises(dev_env.ManifestError) as broken:
        dev_env.entries({"oops": "not an object"}, required=("version",), where="binaries")
    assert "binaries.oops" in str(broken.value)
    assert "str" in str(broken.value)

    with pytest.raises(dev_env.ManifestError) as absent:
        dev_env.entries({"half": {"version": "1.0.0"}},
                        required=("version", "verify"), where="binaries")
    assert "binaries.half" in str(absent.value) and "verify" in str(absent.value)


def test_be01_a_broken_manifest_is_a_message_not_a_traceback(tmp_path):
    """A malformed manifest must report cleanly. `doctor` is used as a precondition."""
    root = tmp_path / "checkout"
    _healthy(root)
    manifest = root / "crooks-assistant" / "docs" / "dev-environment" / "manifest.json"
    broken = json.loads(manifest.read_text())
    broken["binaries"]["gitleaks"] = "this should have been an object"
    manifest.write_text(json.dumps(broken), encoding="utf-8")

    done = subprocess.run(
        ["python3", str(root / "crooks-assistant" / "scripts" / "dev_env.py"), "doctor"],
        capture_output=True, text=True, timeout=120)
    assert done.returncode != 0
    assert "Traceback" not in done.stderr, done.stderr
    assert "binaries.gitleaks" in done.stderr


# --------------------------------------------------------------------------------- BE-02


def test_be02_doctor_fails_closed_when_tools_are_present_but_wrong(tmp_path, capsys):
    """Present is not the same as correct, and the rejected doctor could not tell them apart.

    It counted only MISSING. A binary that ran and printed any version at all was `ok` — the
    pin was displayed beside the output and never compared to it. A node or pip version that
    did not match was `warn`. A tool whose probe failed outright was `warn`. So a fixture with
    nine mismatches and nine failed probes still ended `all present` with exit 0, which is the
    precise shape of a false green: a machine-readable claim that the environment is the
    pinned one, made by code that never checked.

    Here every stand-in is installed and runnable and every one of them is wrong.
    """
    root = tmp_path / "checkout"
    dev_env = _healthy(root, tools={"shellcheck": "0.0.0", "gitleaks": "0.0.0"}, node="0.0.0",
                       pip="0.0.0", python="0.0.0", chromium="0.0.0.0", skillspector_exit=3)
    assert dev_env.cmd_doctor(dev_env.load()) == 1

    printed = capsys.readouterr().out
    assert "all present" not in printed
    assert "FAILED" in printed
    for name in ("shellcheck", "gitleaks", "playwright", "chromium", "venv", "pytest-xdist",
                 "skillspector"):
        line = next(ln for ln in printed.splitlines() if f" {name} " in f" {ln.strip()} ")
        assert line.strip().startswith("FAIL"), f"{name} was not a failure: {line!r}"


def test_be02_doctor_passes_the_same_fixture_when_everything_matches(tmp_path, capsys):
    """The other half of the proof: fail-closed must not mean always-fail.

    Same fixture, same code path, every stand-in reporting exactly what the manifest pins.
    Without this test "doctor now fails" would be satisfied by `return 1`.
    """
    root = tmp_path / "checkout"
    dev_env = _healthy(root)
    assert dev_env.cmd_doctor(dev_env.load()) == 0

    printed = capsys.readouterr().out
    assert "FAIL" not in printed
    assert "the pinned environment" in printed


def test_be02_advisory_findings_are_named_and_never_decide_the_exit_code(tmp_path, capsys):
    """Required health and undecidable provenance are separated, and both are visible.

    The pinned SkillSpector commit is the one thing here that genuinely cannot be checked:
    `uv tool install --from <local clone>` records a path, not a revision. The honest answer is
    to print it as advisory WITH the reason — not to pass it silently, which is BE-02, and not
    to fail the environment for a fact nothing on the machine can settle.
    """
    root = tmp_path / "checkout"
    dev_env = _healthy(root)
    assert dev_env.cmd_doctor(dev_env.load()) == 0

    printed = capsys.readouterr().out
    advisory = [ln for ln in printed.splitlines() if ln.strip().startswith("advisory")]
    assert len(advisory) == 1 and "commit" in advisory[0]
    assert "not re-derivable" in advisory[0], "an advisory line must say why it is advisory"
    assert "1 advisory" in printed


def test_be02_a_tampered_binary_fails_even_at_the_right_version(tmp_path, capsys):
    """A version number is a claim the artifact makes about itself.

    Pinning 0.11.0 does not pin the bytes, so the digests are checked too: a tool that reports
    the pinned version and is not the pinned artifact is a failure.
    """
    root = tmp_path / "checkout"
    dev_env = _healthy(root)
    assert dev_env.cmd_doctor(dev_env.load()) == 0
    capsys.readouterr()

    tampered = root / ".tooling" / "bin" / "gitleaks"
    _script(tampered, "#!/bin/sh\necho 'gitleaks 8.30.1'\n# and then something else\n")

    assert dev_env.cmd_doctor(dev_env.load()) == 1
    printed = capsys.readouterr().out
    assert "not the pinned artifact" in printed


# --------------------------------------------------------------------------------- BE-03


def _eval_in_sh(root: Path, names: list[str]) -> dict[str, str]:
    """Evaluate the generated exports the way DEV_ENVIRONMENT.md documents, and read them back."""
    script = root / "crooks-assistant" / "scripts" / "dev_env.py"
    generated = subprocess.run(["python3", str(script), "env"],
                               capture_output=True, text=True, timeout=120, check=True).stdout
    readback = "; ".join(f'printf "%s\\n" "${n}"' for n in names)
    done = subprocess.run(["/bin/sh", "-c", generated + "\n" + readback],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    # printf leaves a trailing separator, so the read-back is truncated to the names asked for.
    return dict(zip(names, done.stdout.split("\n")[:len(names)], strict=True))


def test_be03_a_command_substitution_in_the_checkout_path_is_not_executed(tmp_path):
    """The reproduction that rejected the candidate, run against the repair.

    `cmd_env` built each line with Python's repr and then replaced the quotes, producing a
    DOUBLE-quoted shell word. Double quotes do not stop the shell: it expands `$(...)`,
    backticks and `$VAR` inside them. A checkout at

        /tmp/crooks-$(printf CROOKS_ENV_PROBE)

    exported NODE_PATH=/tmp/crooks-CROOKS_ENV_PROBE/.tooling/node/node_modules — the wrong
    directory, and a command the generator decided to run. Only a fixed printf ever ran, then
    or here; the point is that the checkout path chose it.

    shlex.quote is the fix, and single quotes are why: nothing inside them expands.
    """
    root = tmp_path / "crooks-$(printf CROOKS_ENV_PROBE)"
    _healthy(root)
    values = _eval_in_sh(root, ["NODE_PATH", "CROOKS_CHROMIUM"])

    assert values["NODE_PATH"] == str(root / ".tooling/node/node_modules")
    assert "$(printf CROOKS_ENV_PROBE)" in values["NODE_PATH"]
    assert "CROOKS_ENV_PROBE/" not in values["NODE_PATH"], "the substitution ran"
    assert values["CROOKS_CHROMIUM"].startswith(str(root))


def test_be03_every_shell_metacharacter_round_trips_including_path(tmp_path):
    """Spaces, apostrophes, quotes, dollars, backticks, semicolons and a newline.

    All of them in one directory name, because a checkout path is whatever the owner's
    filesystem holds and the generator does not get to assume otherwise. PATH is in the
    contract too: it is the one export whose value is partly inherited from the surrounding
    shell, so it is the one most easily left unquoted.
    """
    hostile = "dir with 'quote' \"double\" $DOLLAR `tick` ;semi\nnewline"
    root = tmp_path / hostile
    _healthy(root)
    names = ["PLAYWRIGHT_BROWSERS_PATH", "NODE_PATH", "CROOKS_CHROMIUM", "LD_LIBRARY_PATH",
             "UV_TOOL_DIR", "PATH"]

    script = root / "crooks-assistant" / "scripts" / "dev_env.py"
    generated = subprocess.run(["python3", str(script), "env"],
                               capture_output=True, text=True, timeout=120, check=True).stdout
    # A NUL-separated read-back, because one of the values deliberately contains a newline.
    readback = "; ".join(f'printf "%s\\0" "${n}"' for n in names)
    done = subprocess.run(["/bin/sh", "-c", generated + "\n" + readback],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    values = dict(zip(names, done.stdout.split("\0")[:len(names)], strict=True))

    for name in names[:5]:
        assert values[name].startswith(str(root)), f"{name} lost the checkout path"
        assert hostile in values[name]
    assert values["PATH"].startswith(str(root / ".tooling/bin") + ":")
    assert values["PATH"].endswith(os.environ.get("PATH", ""))
    assert "DOLLAR" in values["NODE_PATH"], "$DOLLAR was expanded away"


# --------------------------------------------------------------------------------- BE-04


def _import_at_source():
    spec = importlib.util.spec_from_file_location("dev_env_real", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_be04_every_input_the_plan_reads_is_committed(tmp_path):
    """The reproducibility defect, stated as the thing that actually broke.

    The rejected plan's first step was `cd .tooling/node && npm install`, and `.tooling/` is
    gitignored — so on a fresh checkout the directory it starts in does not exist and the
    package.json it installs from was never committed anywhere. The environment could only be
    rebuilt on a machine that already had it, which is not a reconstruction.

    This copies ONLY the committed files into an empty tree — no `.tooling`, no `.venv` — and
    asks the plan whether it can still be followed.
    """
    root = tmp_path / "fresh"
    dev_env = _import_at(root)
    target = root / "crooks-assistant" / "docs" / "dev-environment"
    target.mkdir(parents=True, exist_ok=True)
    for committed in DEV_ENV_DIR.iterdir():
        if committed.is_file():
            shutil.copy2(committed, target / committed.name)

    assert not (root / ".tooling").exists()
    # The concrete thing that was missing: the npm project step 1 installs from lived only in
    # gitignored .tooling/, so it was not in any checkout that did not already have it.
    assert (target / "node-package.json").exists(), \
        "the npm project the plan installs from is not committed anywhere"
    assert (target / "node-package-lock.json").exists(), "no committed dependency lock"

    missing = [p for p in dev_env.plan_inputs() if not p.exists()]
    assert missing == [], f"the plan reads files a fresh checkout does not have: {missing}"

    done = subprocess.run(
        ["python3", str(root / "crooks-assistant" / "scripts" / "dev_env.py"), "plan"],
        capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert "Every input the plan reads is committed and present" in done.stdout


def test_be04_the_node_install_builds_its_inputs_from_committed_files(tmp_path, capsys):
    """Step 1 must create `.tooling/node/package.json`, never assume it.

    And it installs from the committed lock with `npm ci`, not `npm install`: a lock that is
    committed and then not used is decoration.
    """
    dev_env = _import_at_source()
    commands = dict(dev_env.plan_steps(dev_env.load()))
    node_step = next(v for k, v in commands.items() if k.startswith("1."))
    joined = "\n".join(node_step)

    copied = next(i for i, c in enumerate(node_step) if "node-package.json" in c)
    installed = next(i for i, c in enumerate(node_step) if "npm ci" in c)
    assert copied < installed, "npm runs before its package.json is created"
    assert "node-package-lock.json" in joined
    assert "npm install" not in joined, "the committed lock must be the thing that is installed"


def test_be04_no_step_leaves_the_repository_root_behind_it(tmp_path):
    """Root-anchored, every line of it.

    The rejected plan printed bare `cd` steps that the following commands silently inherited,
    so following it literally from the repository root put later steps in the wrong place. A
    `cd` is allowed only inside a subshell, which ends at the closing parenthesis.
    """
    dev_env = _import_at_source()
    for heading, commands in dev_env.plan_steps(dev_env.load()):
        for command in commands:
            if command.lstrip().startswith("#"):
                continue
            if "cd " in command:
                assert command.startswith("( cd "), f"{heading}: unscoped cd in {command!r}"
                assert command.rstrip().endswith(")"), f"{heading}: subshell not closed"


def test_be04_the_plan_is_read_only_and_repeats_identically(tmp_path, capsys):
    """Two runs, byte-identical, and nothing written by either.

    `plan` prints; it does not install. That is the honest interface the review asked for, and
    the second-run property is trivially true because of it — which is the point. The rejected
    command claimed idempotent installation and performed neither half.
    """
    root = tmp_path / "checkout"
    dev_env = _healthy(root)
    before = sorted(p.relative_to(root) for p in root.rglob("*"))

    assert dev_env.cmd_plan(dev_env.load()) == 0
    first = capsys.readouterr().out
    assert dev_env.cmd_plan(dev_env.load()) == 0
    second = capsys.readouterr().out

    assert first == second
    assert sorted(p.relative_to(root) for p in root.rglob("*")) == before


def test_be04_the_plan_says_plainly_what_it_cannot_do(tmp_path, capsys):
    """A plan that is not executable end to end must say so where it is read.

    Step 4 cannot be written as commands: the manifest pins each tool's version and upstream
    repository but not its release tag or asset URL, and pinning those needs an approved
    package-fetch policy. Reporting that as BLOCKED is the requirement; guessing eight release
    URLs and committing them untested is how BE-01 happened in the first place.
    """
    dev_env = _import_at_source()
    assert dev_env.cmd_plan(dev_env.load()) == 0
    printed = capsys.readouterr().out
    assert "BLOCKED" in printed
    assert "package-fetch policy" in printed
    assert "NOT EXECUTABLE YET" in printed


def test_be04_bootstrap_is_gone_and_refuses_rather_than_pretending(tmp_path):
    """The old name exits non-zero and points at the new one.

    Keeping `bootstrap` as a silent alias would preserve exactly the thing that was wrong:
    a command called "install" that prints. It refuses, and explains.
    """
    root = tmp_path / "checkout"
    _healthy(root)
    done = subprocess.run(
        ["python3", str(root / "crooks-assistant" / "scripts" / "dev_env.py"), "bootstrap"],
        capture_output=True, text=True, timeout=120)
    assert done.returncode == 2
    assert "plan" in done.stderr
    assert "never installed anything" in done.stderr


def test_be04_the_committed_reconstruction_inputs_are_the_real_ones():
    """The inventories shipped in this repository, checked for shape rather than trusted.

    89 sysroot packages with a digest each, nine pinned binaries with a digest each, and a node
    lock that carries an integrity hash for every dependency the manifest pins. The digests
    themselves are observed, not upstream-attested — recorded in the files that hold them.
    """
    dev_env = _import_at_source()
    manifest = dev_env.load()

    packages = [ln for ln in dev_env.SYSROOT_PACKAGES.read_text().splitlines()
                if ln.strip() and not ln.startswith("#")]
    digests = dev_env.read_checksums(dev_env.SYSROOT_CHECKSUMS)
    assert len(packages) == manifest["sysroot"]["packages_extracted"] == len(digests)
    assert all("=" in line for line in packages), "apt-get download needs name=version"
    for excluded in manifest["sysroot"]["excluded"]:
        assert not any(line.startswith(f"{excluded}=") for line in packages), \
            f"{excluded} would shadow the system C runtime"

    binaries = dev_env.read_checksums(dev_env.BINARY_CHECKSUMS)
    assert len(binaries) == 9
    assert all(len(d) == 64 for d in binaries.values())

    assert dev_env.node_package_findings(manifest) == []
