"""Preparing an answer for a mouth rather than a screen.

Two rules are being defended here. The first is that the known-awkward things sound right:
money, order numbers, markdown, links. The second matters more — nothing in this layer may
change what the answer says. Every test that rewrites a number checks the number survived.
"""

from __future__ import annotations

import pytest

from app.speech.speakable import number_words, order_number_words, to_speakable


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "zero"), (7, "seven"), (13, "thirteen"), (20, "twenty"), (42, "forty-two"),
        (100, "one hundred"), (430, "four hundred and thirty"), (999, "nine hundred and ninety-nine"),
        (1000, "one thousand"), (1030, "one thousand and thirty"),
        (1930, "one thousand nine hundred and thirty"),
        (12_500, "twelve thousand five hundred"),
    ],
)
def test_number_words_are_british(value, expected):
    assert number_words(value) == expected


def test_number_words_refuses_what_it_should_not_spell():
    with pytest.raises(ValueError):
        number_words(1_000_000)


# --------------------------------------------------------------------------- money


@pytest.mark.parametrize(
    "text,expected",
    [
        ("£60", "sixty pounds"),
        ("£1", "one pound"),
        ("£430.50", "four hundred and thirty pounds fifty"),
        ("£430.00", "four hundred and thirty pounds"),
        ("£430.05", "four hundred and thirty pounds oh five"),
        ("£0.99", "ninety-nine pence"),
        ("£1,204.99", "one thousand two hundred and four pounds ninety-nine"),
        ("£ 60", "sixty pounds"),
    ],
)
def test_money_is_spoken_not_symbolised(text, expected):
    assert to_speakable(text) == expected


def test_an_amount_too_large_to_spell_keeps_its_digits():
    # Exactness beats elegance: the figure is still right, the engine reads it.
    assert to_speakable("£1200000") == "1200000 pounds"


def test_money_inside_a_sentence_leaves_the_sentence_alone():
    said = to_speakable("Twelve orders today, £430.50 in total.")
    assert said == "Twelve orders today, four hundred and thirty pounds fifty in total."


# --------------------------------------------------------------------------- order numbers


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Order #1930", "Order nineteen thirty"),
        ("order 1930", "order nineteen thirty"),
        ("order number 1930", "order nineteen thirty"),
        ("invoice no. 1905", "invoice nineteen oh five"),
        ("order 1900", "order nineteen hundred"),
        ("order 2000", "order two thousand"),
        ("#1930", "nineteen thirty"),
    ],
)
def test_order_numbers_are_read_as_pairs(text, expected):
    assert to_speakable(text) == expected


def test_a_hash_is_never_read_as_the_word_hash():
    assert "hash" not in to_speakable("Order #1930 shipped.").lower()
    assert "#" not in to_speakable("Order #1930 shipped.")


def test_five_digit_ids_keep_their_digits():
    # There is no agreed spoken form; inventing one makes the id unrecognisable.
    assert to_speakable("order 12345") == "order 12345"
    assert order_number_words("12345") == "12345"


def test_a_bare_number_is_not_treated_as_an_order():
    assert to_speakable("There are 1930 units in stock.") == "There are 1930 units in stock."


# --------------------------------------------------------------------------- formatting


def test_markdown_never_reaches_the_voice():
    said = to_speakable("## Today\n\n- **Twelve** orders\n- *Four* returns")
    assert said == "Today. Twelve orders. Four returns"
    for symbol in "*_#`":
        assert symbol not in said


def test_urls_become_a_link_and_html_disappears():
    assert to_speakable("See https://crooksldn.com/orders/1") == "See a link"
    assert to_speakable("A <b>bold</b> claim") == "A bold claim"
    assert to_speakable("Read [the policy](https://x.test/p)") == "Read the policy"


def test_code_fences_are_dropped_whole():
    assert to_speakable("Here it is.\n```json\n{\"id\": 1}\n```") == "Here it is."


def test_repeated_punctuation_is_collapsed():
    assert to_speakable("Really?!?  Yes!!!") == "Really? Yes!"
    assert to_speakable("Wait... twelve.") == "Wait. twelve."


def test_symbols_that_are_words_become_words():
    assert to_speakable("Up 20% on stock & returns") == "Up 20 percent on stock and returns"


def test_nothing_worth_saying_returns_nothing():
    assert to_speakable("") == ""
    assert to_speakable("...") == ""
    assert to_speakable("***") == ""


def test_length_is_bounded_at_a_sentence():
    long_answer = "One sentence here. " * 200
    said = to_speakable(long_answer, max_chars=100)
    assert len(said) <= 100
    assert said.endswith(".")


def test_an_already_spoken_answer_is_left_alone():
    # The system prompt asks Claude for exactly this shape; this layer must not second-guess it.
    original = "Twelve orders today, four hundred and thirty pounds. Nothing needs chasing."
    assert to_speakable(original) == original
