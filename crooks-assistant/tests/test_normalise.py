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


def test_single_number_word_is_left_alone():
    """A lone number word is conversation, not an order number. Rewriting it gains nothing."""
    assert words_to_digits(["I", "want", "three", "shirts"]) == ["I", "want", "three", "shirts"]
    assert words_to_digits(["oh", ",", "how", "many"]) == ["oh", ",", "how", "many"]


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
        ("call 07700 900123", []),         # phone fragments are not orders
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


# --- lessons from the real CROOKSLDN catalogue -------------------------------

REAL = [
    "Grey Convict Sweats", "Grey Convict Hoodie", "Black Convict Hoodie", "Crooks Express Tee",
    "CRX Garms T-Shirt", "CRXST★RZ T-Shirt", "OG Jeans", "Hydrocuff Windbreaker",
    "Grey Wash Yard Jeans", "Blue Wash Yard Jeans", "Blue Wash Yard Jorts",
    "Charcoal Cellblock Crewneck", "Black/Blue Motiontec Socks", "White/Red Motiontec Socks",
    "Pink Set", "Grey Set",
]
ALIASES = {"cross stars tee": "CRXST★RZ T-Shirt", "motion tech socks": "Motiontec Socks"}


@pytest.fixture()
def real():
    return from_terms(REAL, ALIASES)


def test_alias_maps_unpronounceable_name(real):
    assert real.normalise("cross stars tee").text == "CRXST★RZ T-Shirt"
    assert real.normalise("cross stars tee").matches[0].via == "alias"


def test_alias_does_not_false_match_a_similar_real_product(real):
    """'cross stars tee' scored above the old threshold against 'Crooks Express Tee'."""
    assert "Crooks Express Tee" not in real.normalise("cross stars tee").text


def test_compound_word_splits_are_repaired(real):
    assert "Hydrocuff Windbreaker" in real.normalise("the hydro cuff wind breaker").text
    assert "Charcoal Cellblock Crewneck" in real.normalise("charcoal cell block crew neck").text


def test_colour_variants_are_not_conflated(real):
    out = real.normalise("black blue motion tech socks")
    assert "Black/Blue Motiontec Socks" in out.text
    assert "White/Red" not in out.text


def test_partial_name_below_threshold_is_left_alone():
    """'motiontec socks' matches neither colour well enough to replace — so it is not replaced,
    and Claude's Shopify search on the partial name will return both for it to ask about."""
    n = from_terms(["Black/Blue Motiontec Socks", "White/Red Motiontec Socks"])
    out = n.normalise("motiontec socks")
    assert out.text == "motiontec socks"
    assert not out.matches


def test_tie_between_two_products_is_left_alone_and_reported():
    """Two names one similar word apart, heard as something between them: a tie is not a
    decision, so the words stay as heard and the candidates are reported."""
    n = from_terms(["Black Motiontec Socks", "Blank Motiontec Socks"])
    out = n.normalise("blanc motiontec socks")
    assert out.text == "blanc motiontec socks", "a tie must not be broken by guessing"
    assert out.ambiguities
    assert set(out.ambiguities[0].candidates) >= {"Black Motiontec Socks", "Blank Motiontec Socks"}


def test_synonyms_bridge_tee_and_t_shirt(real):
    assert "CRX Garms T-Shirt" in real.normalise("crx garms tee").text


def test_case_is_not_an_obstacle():
    n = from_terms(["BLUE WASH YARD JEANS"])
    assert n.normalise("blue wash yard genes").text == "BLUE WASH YARD JEANS"


def test_shopify_title_case_and_seed_dedupe_keeps_the_seed():
    n = from_terms(["Blue Wash Yard Jeans", "BLUE WASH YARD JEANS"])
    assert n.catalogue.terms == ["Blue Wash Yard Jeans"]


def test_prompt_terms_are_display_case_with_aliases_last(real):
    terms = real.catalogue.prompt_terms()
    assert "CRXST RZ T-Shirt".replace("-", " ") in [t.replace("-", " ") for t in terms]
    assert terms[-1] == "Motion Tech Socks"
    assert all("★" not in t for t in terms)


def test_repoint_swaps_the_catalogue(real):
    real.repoint(["Cuffed Beanie"], {"the beanie": "Cuffed Beanie"})
    assert real.normalise("the beanie").text == "Cuffed Beanie"
    assert real.normalise("cross stars tee").text == "cross stars tee"


@pytest.mark.parametrize(
    "text,expected",
    [("find order CROOKS-1928", ["1928"]), ("crooks 1928", ["1928"]), ("order crooks 1928", ["1928"])],
)
def test_crooks_prefixed_order_numbers(real, text, expected):
    assert real.normalise(text).order_numbers == expected


def test_nineteen_twenty_eight_is_an_order_number(real):
    out = real.normalise("find order nineteen twenty eight")
    assert out.order_numbers == ["1928"]


def test_prose_lines_in_terminology_are_not_terms(tmp_path):
    from app.speech.normalise import load_terminology

    f = tmp_path / "t.md"
    f.write_text(
        "# Terminology\n\nProduct names written the way they are said, one per line please.\n\n"
        "## Products\n\nOG Jeans\ncross stars tee => CRXST★RZ T-Shirt\n",
        encoding="utf-8",
    )
    terms, aliases = load_terminology(f)
    assert terms == ["OG Jeans"]
    assert aliases == {"cross stars tee": "CRXST★RZ T-Shirt"}


def test_shipped_terminology_seed_loads_cleanly():
    from pathlib import Path

    from app.speech.normalise import from_file

    n = from_file(Path(__file__).resolve().parent.parent / "kb" / "terminology.md")
    assert len(n.catalogue) >= 20
    assert n.catalogue.max_words <= 6, "a prose line has leaked into the term list"
    assert "cross stars tee" in n.catalogue.aliases
