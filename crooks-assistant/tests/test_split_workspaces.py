"""The halves as workspaces, on the Mac's side.

The Phase 2 live test found two things on the physical tablet: tapping the other half changed
who was listening and nothing visible, and a half put aside finished a ten-second turn with
an answer nobody could ever read. Both are properties of what the Mac keeps per branch and
hands back, which is what these assert. The gesture itself — two fingers that must never
become a sentence — is asserted in the browser (scripts/browser/tablet.js), where fingers are.
"""

from __future__ import annotations

from app import commands
from app.session.branch import Branch


class _Session:
    def __init__(self, *branches: Branch) -> None:
        self.session_id = "s1"
        self.branches = {b.branch_id: b for b in branches}
        self.focused_branch = branches[0].branch_id if branches else ""
        self.issued_ids = set()


def _ctx(session, branch, **args):
    return commands.Ctx(runtime=None, session=session, branch=branch, args=args)


def test_a_half_keeps_what_it_last_showed_and_hands_it_back():
    branch = Branch(branch_id="br_a", session_id="s1")
    branch.shown([{"type": "order", "data": {"order_number": "#1938"}}, {"type": "context_stack", "data": {}}], "1938 is Mia's.", "show me order 1938")
    assert branch.public()["has_workspace"] is True
    assert branch.public()["last_question"] == "show me order 1938"
    out = commands.run("branch.show", _ctx(_Session(branch), branch))
    assert out.ok and out.answer == "1938 is Mia's."
    ui = [s.as_ui() for s in out.surfaces]
    assert [u["type"] for u in ui] == ["order"], "the context stack is the tablet's, not the Mac's, and is not handed back"
    assert out.changed["question"] == "show me order 1938"


def test_showing_the_other_half_shows_that_half_not_this_one():
    first = Branch(branch_id="br_a", session_id="s1")
    second = Branch(branch_id="br_b", session_id="s1", parent_id="br_a")
    first.shown([{"type": "order_list", "data": {}}], "3 orders today.", "today's orders")
    second.shown([{"type": "order", "data": {"order_number": "#1938"}}], "1938 is Mia's.", "show me order 1938")
    session = _Session(first, second)
    out = commands.run("branch.show", _ctx(session, first, branch_id="br_b"))
    assert [s.as_ui()["type"] for s in out.surfaces] == ["order"] and out.answer == "1938 is Mia's."
    out = commands.run("branch.show", _ctx(session, second, branch_id="br_a"))
    assert [s.as_ui()["type"] for s in out.surfaces] == ["order_list"] and out.answer == "3 orders today."


def test_a_fresh_half_says_it_is_empty_rather_than_drawing_its_parent():
    first = Branch(branch_id="br_a", session_id="s1")
    first.shown([{"type": "order_list", "data": {}}], "3 orders today.", "today's orders")
    second = Branch(branch_id="br_b", session_id="s1", parent_id="br_a")
    out = commands.run("branch.show", _ctx(_Session(first, second), second))
    assert out.ok and out.surfaces == [] and out.changed.get("empty") is True


def test_a_closed_half_cannot_be_shown():
    gone = Branch(branch_id="br_x", session_id="s1", status="MERGED")
    out = commands.run("branch.show", _ctx(_Session(gone), gone))
    assert not out.ok and out.code == "branch_closed"


def test_an_error_card_does_not_replace_a_record_the_half_still_holds():
    branch = Branch(branch_id="br_a", session_id="s1")
    branch.shown([{"type": "order", "data": {}}], "1938.", "show me 1938")
    branch.shown([], "Something went wrong.", "next")
    assert [u["type"] for u in branch.last_ui] == ["order"], "an empty presentation keeps the last screen"
    assert branch.last_answer == "Something went wrong."


def test_branch_show_is_touch_only():
    spec = commands.get("branch.show")
    assert spec is not None and spec.touch and not spec.voice
