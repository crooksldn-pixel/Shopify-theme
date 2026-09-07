"""The normaliser is what makes small.en good enough. These are its acceptance criteria."""

from __future__ import annotations

import pytest

from app.speech.normalise import (
    Catalogue,
    extract_order_numbers,
    from_terms,
    load_terms,
    words_to_digits,
)

TERMS = [
    "Blue Wash Yard Jeans",
    "Bone Wash Yard Jeans",
    "Crooks Cargo Pant",
    "Cuffed Beanie",
    "Stash Hoodie",
    "Balaclava Knit",
    "Anna Denning",
]


@pytest.fixture()
def n():
    return from_terms(TERMS)


# --- product terminology ---------------------------------------------------

@pytest.mark.parametrize(
    "heard,expected",
    [
        ("blue wash yard genes", "Blue Wash Yard Jeans"),
        ("blue wash yard jeans", "Blue Wash Yard Jeans"),
        ("bone wash yard genes", "Bone Wash Yard Jeans"),
        ("crooks cargo pants", "Crooks Cargo Pant"),
        ("cuffed beanie", "Cuffed Beanie"),
        ("stash hoody", "Stash Hoodie"),
    ],
)
def test_product_names_are_corrected(n, heard, expected):
    assert expected in n.normalise(heard).text


def test_similar_products_are_not_conflated(n):
    """Blue and Bone differ by one word; collapsing them would be worse than leaving them."""
    assert "Blue Wash Yard Jeans" in n.normalise("blue wash yard genes").text
    assert "Bone Wash Yard Jeans" in n.normalise("bone wash yard genes").text


def test_unrelated_words_are_left_alone(n):
    out = n.normalise("how many orders have we had today")
    assert out.text.lower() == "how many orders have we had today"
    assert not out.matches


def test_empty_input(n):
    assert n.normalise("").text == ""
    assert n.normalise("   ").text == ""


def test_match_provenance_is_recorded(n):
    out = n.normalise("blue wash yard genes")
    assert out.matches
    assert out.matches[0].replaced_with == "Blue Wash Yard Jeans"
    assert out.matches[0].via in {"fuzzy", "phonetic"}


def test_customer_name_corrected(n):
    assert "Anna Denning" in n.normalise("anna denning").text


def test_no_catalogue_is_a_no_op():
    out = from_terms([]).normalise("blue wash yard genes")
    assert out.text == "blue wash yard genes"
    assert not out.matches


# --- spoken numbers --------------------------------------------------------

@pytest.mark.parametrize(
    "spoken,expected",
    [
        (["four", "eight", "three", "two"], ["4832"]),
        (["forty", "eight", "thirty", "two"], ["4832"]),
        (["one", "two", "three"], ["123"]),
        (["hello", "there"], ["hello", "there"]),
    ],
)
def test_words_to_digits(spoken, expected):
    assert words_to_digits(spoken) == expected


def test_single_number_word_is_not_glued():
    assert words_to_digits(["I", "want", "three", "shirts"]) == ["I", "want", "3", "shirts"]


# --- order numbers ---------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("find order 4832", ["4832"]),
        ("find order #4832", ["4832"]),
        ("order number 4832", ["4832"]),
        ("look up #1201", ["1201"]),
        ("we sold 12 units", []),          # no order cue, and too short
        ("that was 2024 last year", []),   # a year with no cue is not an order
    ],
)
def test_order_number_extraction(text, expected):
    assert extract_order_numbers(text) == expected


def test_spoken_order_number_becomes_digits(n):
    out = n.normalise("find order four eight three two")
    assert "4832" in out.text
    assert out.order_numbers == ["4832"]


def test_hash_is_stripped_from_order_numbers(n):
    out = n.normalise("find order #4832")
    assert out.order_numbers == ["4832"]


# --- the five M3 benchmark phrases ----------------------------------------

def test_benchmark_phrases_survive_normalisation(n):
    phrases = [
        "How many orders have we had today?",
        "Find order 4832.",
        "How many Blue Wash Yard Jeans in medium do we have?",
        "Look at my emails from today.",
        "Has that customer replied yet?",
    ]
    for phrase in phrases:
        out = n.normalise(phrase)
        assert out.text.rstrip(".?").lower() == phrase.rstrip(".?").lower(), (
            f"normaliser damaged a correct transcript: {phrase!r} -> {out.text!r}"
        )


# --- catalogue loading -----------------------------------------------------

def test_load_terms_parses_markdown(tmp_path):
    f = tmp_path / "terminology.md"
    f.write_text(
        "# Products\n\n- Blue Wash Yard Jeans\n- Stash Hoodie  # the grey one\n"
        "\n## Customers\n\nAnna Denning\n\n> a note we should ignore\n",
        encoding="utf-8",
    )
    assert load_terms(f) == ["Blue Wash Yard Jeans", "Stash Hoodie", "Anna Denning"]


def test_load_terms_missing_file_is_not_fatal(tmp_path):
    assert load_terms(tmp_path / "nope.md") == []


def test_catalogue_dedupes_case_insensitively():
    assert len(Catalogue(["Stash Hoodie", "stash hoodie", "STASH HOODIE"])) == 1
