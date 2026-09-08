"""`make up` and `make install`: what they would run, and what they would write.

Neither launches anything here. The supervisor's commands and the rendered launchd agents are
checked as data, because the failure that matters — a plist with a placeholder left in it, or
a backend started on the wrong port — is one launchd turns into a silent restart loop.
"""

from __future__ import annotations

import importlib.util
import json
import plistlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lc = load("launch_common")
whisper_server = load("whisper_server")
up = load("up")
installer = load("install_launchd")


# --------------------------------------------------------------------------- tailscale


def test_serve_status_finds_the_host_proxying_our_port():
    status = json.dumps({
        "TCP": {"443": {"HTTPS": True}},
        "Web": {"crooks-assistant.taildfb357.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8000"}}}},
    })
    assert lc.parse_serve_status(status, 8000) == "crooks-assistant.taildfb357.ts.net"
    assert lc.parse_serve_status(status, 8910) is None


@pytest.mark.parametrize("text", ["", "{}", "not json", '{"Web": null}', "[]", '{"Web": {"h:443": {}}}'])
def test_serve_status_is_none_when_nothing_is_served(text):
    assert lc.parse_serve_status(text, 8000) is None


# --------------------------------------------------------------------------- the supervisor


class FakeSettings:
    host = "127.0.0.1"
    port = 8000
    whisper_url = "http://127.0.0.1:8910"
    whisper_model = "large-v3-turbo"
    whisper_vad_pad_ms = 200

    def __init__(self, whisper_bin_dir: Path) -> None:
        self.whisper_bin_dir = whisper_bin_dir


def test_backend_command_uses_the_configured_address_and_no_reload_by_default(tmp_path):
    settings = FakeSettings(tmp_path)
    cmd = up.backend_command(settings)
    assert cmd[1:4] == ["-m", "uvicorn", "app.main:app"]
    assert "--host" in cmd and cmd[cmd.index("--host") + 1] == "127.0.0.1"
    assert "--port" in cmd and cmd[cmd.index("--port") + 1] == "8000"
    assert "--reload" not in cmd
    assert "--reload" in up.backend_command(settings, reload=True)


def test_up_runs_without_whisper_when_it_is_not_built_and_says_so(tmp_path):
    children, notes = up.commands(FakeSettings(tmp_path / "nowhere"))
    assert [name for name, _ in children] == ["backend"]
    assert any("whisper-server is NOT starting" in n for n in notes)
    assert any("ElevenLabs still hears you" in n for n in notes)


def test_up_runs_whisper_first_when_it_is_built(tmp_path):
    root = tmp_path / "whisper.cpp"
    (root / "build" / "bin").mkdir(parents=True)
    (root / "models").mkdir()
    (root / "build" / "bin" / "whisper-server").write_text("")
    (root / "models" / "ggml-large-v3-turbo.bin").write_text("")
    (root / "models" / "ggml-silero-v5.1.2.bin").write_text("")
    children, notes = up.commands(FakeSettings(root))
    assert [name for name, _ in children] == ["whisper", "backend"]
    whisper_cmd = children[0][1]
    assert whisper_cmd[0].endswith("whisper-server")
    assert "--vad" in whisper_cmd and "--port" in whisper_cmd and whisper_cmd[whisper_cmd.index("--port") + 1] == "8910"
    # No Core ML encoder: a note, not a refusal.
    assert any("Metal" in n for n in notes)


def test_up_does_not_start_what_is_already_running(tmp_path):
    """The login-time agents may already hold both ports; `make up` must not fight them."""
    children, notes = up.commands(FakeSettings(tmp_path / "nowhere"), port_open=lambda host, port: True)
    assert children == []
    assert any("already running on port 8000" in n for n in notes)
    assert any("already running on port 8910" in n for n in notes)


def test_port_open_sees_a_real_listener():
    import socket

    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        assert lc.port_open("127.0.0.1", port)
    assert not lc.port_open("127.0.0.1", port)


def test_whisper_refuses_without_a_vad_model(tmp_path):
    root = tmp_path / "whisper.cpp"
    (root / "build" / "bin").mkdir(parents=True)
    (root / "models").mkdir()
    (root / "build" / "bin" / "whisper-server").write_text("")
    (root / "models" / "ggml-large-v3-turbo.bin").write_text("")
    resolved = whisper_server.resolve(FakeSettings(root))
    assert resolved.cmd is None and "Silero" in resolved.problem


# --------------------------------------------------------------------------- launchd agents


def values(tmp_path: Path) -> dict[str, str]:
    return lc.plist_values(root=tmp_path / "checkout", python=tmp_path / ".venv" / "bin" / "python", home=tmp_path)


def test_every_template_renders_to_a_valid_plist_with_no_placeholder_left(tmp_path):
    rendered = installer.rendered_plists(values(tmp_path))
    assert set(rendered) == {"com.crooks.assistant", "com.crooks.whisper"}
    for label, body in rendered.items():
        assert "{{" not in body and "USERNAME" not in body
        plist = plistlib.loads(body.encode("utf-8"))
        assert plist["Label"] == label
        assert plist["ProgramArguments"][0] == str(tmp_path / ".venv" / "bin" / "python")
        assert plist["WorkingDirectory"] == str(tmp_path / "checkout")
        assert plist["KeepAlive"] == {"SuccessfulExit": False, "Crashed": True}
        assert plist["ThrottleInterval"] >= 10
        assert plist["StandardOutPath"].startswith(str(tmp_path / "checkout" / "logs"))
        env = plist["EnvironmentVariables"]
        assert env["HOME"] == str(tmp_path)
        assert "/usr/bin" in env["PATH"].split(":")
        # Nothing that would bill per token, and no credential, is ever written into a plist.
        for forbidden in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "xi-api-key", "shpat_"):
            assert forbidden not in body


def test_the_backend_agent_names_the_cli_and_the_port(tmp_path):
    body = installer.rendered_plists(values(tmp_path))["com.crooks.assistant"]
    plist = plistlib.loads(body.encode("utf-8"))
    args = plist["ProgramArguments"]
    assert args[1:4] == ["-m", "uvicorn", "app.main:app"]
    assert args[args.index("--host") + 1] == "127.0.0.1" and args[args.index("--port") + 1] == "8000"
    assert "CROOKS_CLAUDE_CLI_PATH" in plist["EnvironmentVariables"]


def test_render_refuses_a_missing_placeholder():
    with pytest.raises(ValueError):
        lc.render("<string>{{ROOT}}</string>", {"PYTHON": "x"})


def test_launchd_path_starts_with_the_interpreter_that_will_run_it():
    path = lc.launchd_path([sys.executable]).split(":")
    assert str(Path(sys.executable).resolve().parent) in path
    assert "/usr/bin" in path and "/bin" in path


def test_health_summary_names_what_is_down():
    data = {"status": "degraded", "checks": {"claude": {"ok": True}, "shopify": {"ok": False}, "gmail": {"ok": True}}}
    line = lc.summarise_health(data)
    assert line.startswith("partly down") and "working: Claude, Gmail" in line and "NOT working: Shopify" in line
    assert lc.summarise_health(None) == "the assistant is not answering"
    assert lc.summarise_health({"status": "ok", "checks": {"claude": {"ok": True}}}) == "all good · Claude"


def test_the_makefile_has_the_targets_the_readme_promises():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("up:", "install:", "uninstall:", "status:", "restart:", "logs:"):
        assert f"\n{target}" in makefile
    assert "scripts/up.py" in makefile and "scripts/install_launchd.py" in makefile
