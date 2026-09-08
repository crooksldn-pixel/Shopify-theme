"""The JavaScript, checked by Node: syntax for every file, and the renderer's behaviour.

Node is not a dependency of the assistant; it is a development tool. When it is absent these
tests skip rather than fail, so `make test` on a Mac without Node still proves everything
else. When it is present (it is on the build Mac), the renderer is run against a small DOM
stand-in and its two rules — vocabulary only, text only — are checked for real.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node")

needs_node = pytest.mark.skipif(NODE is None, reason="node is not installed here")


@needs_node
@pytest.mark.parametrize("name", sorted(p.name for p in WEB.glob("*.js")))
def test_javascript_parses(name):
    result = subprocess.run([NODE, "--check", str(WEB / name)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


@needs_node
def test_the_renderer_under_node():
    result = subprocess.run(
        [NODE, "--test", str(ROOT / "tests" / "web" / "ui.test.js")],
        capture_output=True, text=True, timeout=120, cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
    assert "# fail 0" in result.stdout
