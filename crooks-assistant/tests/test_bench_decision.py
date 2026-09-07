"""The M3 model decision must be arithmetic, not a preference. This pins the rule."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "bench", Path(__file__).resolve().parent.parent / "scripts" / "bench_whisper.py"
)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)

EXPECTED = {f"p{i}": f"phrase {i}" for i in range(1, 6)}


def rows(correct: int, ms: float) -> list[dict]:
    return [
        {
            "stem": f"p{i}", "median_ms": ms,
            "raw": f"phrase {i}" if i <= correct else "wrong",
            "normalised": f"phrase {i}" if i <= correct else "wrong",
        }
        for i in range(1, 6)
    ]


def test_small_perfect_keeps_small_regardless_of_medium():
    decision = bench.decide({"small.en": rows(5, 120), "medium.en": rows(5, 350)}, EXPECTED)
    assert decision["model"] == "small.en"
    assert "all 5" in decision["why"]


def test_medium_wins_when_it_fixes_two_within_budget():
    decision = bench.decide({"small.en": rows(3, 120), "medium.en": rows(5, 380)}, EXPECTED)
    assert decision["model"] == "medium.en"


def test_medium_loses_when_it_only_fixes_one():
    decision = bench.decide({"small.en": rows(4, 120), "medium.en": rows(5, 380)}, EXPECTED)
    assert decision["model"] == "small.en"


def test_medium_loses_when_it_blows_the_latency_budget():
    decision = bench.decide({"small.en": rows(3, 120), "medium.en": rows(5, 900)}, EXPECTED)
    assert decision["model"] == "small.en"
    assert "700" in decision["why"]


def test_missing_medium_keeps_small():
    assert bench.decide({"small.en": rows(3, 120)}, EXPECTED)["model"] == "small.en"


def test_missing_small_is_not_a_decision():
    assert bench.decide({"medium.en": rows(5, 300)}, EXPECTED)["model"] == "unknown"


@pytest.mark.parametrize(
    "a,b",
    [("Find order 4832.", "find order 4832"), ("How many?", "how many"), ("a  b", "a b")],
)
def test_scoring_ignores_case_and_punctuation(a, b):
    assert bench.similar(a, b)


def test_scoring_does_not_ignore_wrong_words():
    assert not bench.similar("blue wash yard genes", "blue wash yard jeans")


def test_phrases_file_parses(tmp_path):
    f = tmp_path / "phrases.txt"
    f.write_text("# comment\nstem-a | Hello there.\n\nstem-b | Second phrase\n", encoding="utf-8")
    assert bench.load_expected(f) == {"stem-a": "Hello there.", "stem-b": "Second phrase"}


def test_shipped_phrases_file_has_the_five_benchmark_phrases():
    parsed = bench.load_expected(Path(__file__).resolve().parent.parent / "bench" / "phrases.txt")
    assert len(parsed) == 5
    assert "How many orders have we had today?" in parsed.values()
