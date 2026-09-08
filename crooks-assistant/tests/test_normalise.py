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


# --- ordinary English is not a product name ---------------------------------

# What the live catalogue actually adds on top of the seed file: the store's colour options,
# as one-word terms. Every false positive below was measured against this list.
COLOURS = ["White", "Black", "Grey", "Pink", "Blue", "Red", "Charcoal", "Bone", "Sand"]


@pytest.fixture()
def live():
    """The seed catalogue with the live colour options merged in, as M7 does hourly."""
    return from_terms(COLOURS + REAL, ALIASES)


def test_the_tablet_sentence_that_found_this(live):
    """The live regression, exactly as Scribe v2 heard it and the normaliser wrecked it:
    'what' became 'White' twice, because metaphone codes them both WT."""
    raw = "Order one nine three zero and tell me what they, exactly what they ordered"
    out = live.normalise(raw)
    assert out.text == "Order 1930 and tell me what they, exactly what they ordered"
    assert not out.matches
    assert out.order_numbers == ["1930"], "the order number must still be recovered"


def test_what_never_becomes_white(live):
    for phrase in [
        "what",
        "what did they order",
        "so what happened there",
        "tell me what they ordered",
        "what's the total",
    ]:
        assert "White" not in live.normalise(phrase).text, phrase


@pytest.mark.parametrize(
    "heard",
    [
        "is that back in stock",       # back  ~ Black,  89
        "read me the last email",      # read  ~ Red,    86 and an equal metaphone code
        "and tell me more",            # and   ~ Sand,   86
        "the address on that one",     # one   ~ Bone,   86
        "were there any refunds",
        "who is that from",
        "did he pay for it",
        "how much did we take yesterday",
    ],
)
def test_ordinary_english_is_never_replaced(live, heard):
    """Each of these scored above the old threshold against a one-word colour term."""
    out = live.normalise(heard)
    assert out.text == heard, f"normaliser damaged a correct transcript: {out.matches}"
    assert not out.matches


def test_real_corrections_still_happen_with_colours_in_the_catalogue(live):
    """The protection must be conservative, not inert."""
    assert "Grey Convict Hoodie" in live.normalise("gray convict hoodie").text
    assert "Blue Wash Yard Jeans" in live.normalise("blue wash yard genes").text
    assert "Hydrocuff Windbreaker" in live.normalise("the hydro cuff wind breaker").text
    assert "CRXST★RZ T-Shirt" == live.normalise("cross stars tee").text
    assert "Black Convict Hoodie" in live.normalise("black convict hoodie in medium").text


def test_a_colour_said_plainly_still_reaches_its_display_form(live):
    """An ordinary word may still match a catalogue entry exactly — it just may not be
    corrected towards one."""
    assert live.normalise("in black").text == "in Black"


def test_an_alias_outranks_the_ordinary_english_rule():
    """A hand-written spoken form is a deliberate instruction, even when it is plain English."""
    n = from_terms(["Cellblock Set"], {"the set": "Cellblock Set"})
    assert n.normalise("the set").text == "Cellblock Set"


def test_short_terms_need_more_evidence_than_long_ones():
    from app.speech.normalise import FUZZY_THRESHOLD, SHORT_TERM_THRESHOLD, threshold_for

    assert threshold_for("blue") == SHORT_TERM_THRESHOLD
    assert threshold_for("charcoal") == FUZZY_THRESHOLD          # long enough to be distinctive
    assert threshold_for("blue wash yard jeans") == FUZZY_THRESHOLD


def test_a_phonetic_code_alone_cannot_invent_a_match():
    """'what' and 'white' share the metaphone code WT and look 67% alike; 'gray' and 'grey'
    share theirs and look 75% alike. Only the second is evidence."""
    n = from_terms(["White", "Grey"])
    assert n.normalise("what").text == "what"
    assert n.normalise("gray").text == "Grey"


def test_common_word_detection_ignores_apostrophes():
    from app.speech.normalise import is_common_speech

    assert is_common_speech("what's")
    assert is_common_speech("what they")
    assert not is_common_speech("yard genes")
    assert not is_common_speech("")


def test_customer_names_are_not_matched_more_aggressively():
    """The rule only ever refuses a match. A name that was corrected before still is, and a
    name that was left alone still is."""
    n = from_terms(["Anna Denning", "Blue Wash Yard Jeans"])
    assert "Anna Denning" in n.normalise("anna denning").text
    assert n.normalise("tell me what they ordered").text == "tell me what they ordered"


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
