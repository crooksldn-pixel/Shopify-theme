from __future__ import annotations

from app.kb.loader import MAX_KB_CHARS, build_system_prompt, load


def test_loads_markdown_files_in_order(tmp_path):
    (tmp_path / "b-shipping.md").write_text("Ships in 2 days.", encoding="utf-8")
    (tmp_path / "a-returns.md").write_text("14 days.", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")
    kb = load(tmp_path)
    assert kb.files == ["a-returns.md", "b-shipping.md"]
    assert kb.text.index("Returns") < kb.text.index("Shipping")
    assert "nope" not in kb.text


def test_empty_files_are_skipped(tmp_path):
    (tmp_path / "empty.md").write_text("   \n", encoding="utf-8")
    assert load(tmp_path).empty


def test_missing_dir_is_empty(tmp_path):
    assert load(tmp_path / "nope").empty


def test_budget_is_enforced(tmp_path):
    (tmp_path / "a.md").write_text("x" * (MAX_KB_CHARS - 10), encoding="utf-8")
    (tmp_path / "b.md").write_text("y" * 100, encoding="utf-8")
    kb = load(tmp_path)
    assert kb.files == ["a.md"]


def test_system_prompt_carries_the_rules(tmp_path):
    (tmp_path / "returns-policy.md").write_text("Returns within 14 days.", encoding="utf-8")
    prompt = build_system_prompt(load(tmp_path))
    for phrase in (
        "read aloud", "No markdown", "ask which one", "cannot change anything",
        "Returns within 14 days.", "REFUSED", "AMBER", "no tool call",
    ):
        assert phrase in prompt, phrase


def test_empty_kb_tells_the_model_to_say_so(tmp_path):
    prompt = build_system_prompt(load(tmp_path))
    assert "knowledge base is empty" in prompt
