"""The phone: the size DESIGN.md §13 names and no gate had ever rendered a pixel at.

Three kinds of check, and they are deliberately different kinds — the same division
`tests/test_touch.py` makes, for the same reason.

1. THE STYLESHEET, read as text. That the four safe-area insets are read through tokens rather
   than through bare `env()`; that the hold pill's width is BOUGHT from its slot rather than
   asserted over it; that the band's height and the room reserved for it are one number. A
   string test cannot prove a layout; it CAN prove that the three lines that produced the
   phone's defects are gone and have not come back, which is what a regression test is for.

2. THE GATE, guarded by name. `scripts/browser/mobile.js` is in `run_checks`' default sweep, so
   `tests/test_browser.py` drives it — and a gate that quietly stopped measuring a viewport
   must be a FAILURE, not a smaller green number. The names are asserted here so a run that
   loses one cannot pass.

3. THE GLASS, in Chromium. Not run a second time from here: the gate is in the default tuple
   and a second browser run of the same script would add minutes to every suite run to prove
   the same thing twice.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
STYLE = (WEB / "style.css").read_text(encoding="utf-8")
GATE = (ROOT / "scripts" / "browser" / "mobile.js").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- the stylesheet


def test_the_safe_areas_are_tokens_so_a_gate_can_set_them():
    """`env(safe-area-inset-*)` cannot be written from a test, which is why nothing in this
    repo had ever checked what a notch and a home indicator do to the layout. Read through four
    custom properties, it can be set — `scripts/browser/mobile.js` gives the page an iPhone's
    real insets and measures the result. The tokens are only worth having if every band that
    has to clear the hardware actually uses them, so no bare `env()` may survive."""
    assert "--safe-t:env(safe-area-inset-top,0px)" in STYLE
    assert "--safe-b:env(safe-area-inset-bottom,0px)" in STYLE
    assert "--safe-l:env(safe-area-inset-left,0px)" in STYLE
    assert "--safe-r:env(safe-area-inset-right,0px)" in STYLE
    # Exactly four: the declarations of the tokens themselves, and nowhere else.
    assert STYLE.count("env(safe-area-inset") == 4, (
        "a band is reading env() directly again, so the gate cannot set its inset"
    )
    assert "padding:var(--safe-t) var(--safe-r) var(--safe-b) var(--safe-l);" in STYLE


def test_the_dock_band_and_the_room_reserved_for_it_are_one_number():
    """`.app` reserved `--dock + inset` while `.dock` was `--dock` tall with the inset taken
    OUT of it. On a notched phone the band was therefore 34px shorter than its own reservation:
    the four areas and the hold pill were squeezed into 78px of a 112px band, with a strip of
    empty ground above them and the deck stopping 34px higher than it needed to."""
    assert 'body[data-mode="context"] .app{padding-bottom:calc(var(--dock) + var(--safe-b))}' in STYLE
    dock = STYLE[STYLE.index("\n.dock{"):]
    dock = dock[:dock.index("}")]
    assert "height:calc(var(--dock) + var(--safe-b))" in dock
    assert "padding:0 14px var(--safe-b)" in dock
    talk = STYLE[STYLE.index('body[data-mode="context"] .talk{'):]
    talk = talk[:talk.index("}")]
    assert "height:calc(var(--dock) + var(--safe-b))" in talk


def test_the_hold_pill_is_bought_from_its_slot_and_never_asserted_over_it():
    """D-1's rule, as arithmetic rather than as a z-index.

    `body[data-mode="context"] .talk-label` was `min-width:240px`, and the phone media query
    narrowed `--hold-w` — the slot it sits in — to 200px. So at 390 CSS px the voice layer was
    painted 10px over the Inbox icon at one end and 10px over the Sales icon at the other, and
    the page's own collision engine reported `button_over_navigation` on every surface: layer 5
    covering layer 3, five rows apart in the §8 table and touching anyway.

    A width taken FROM the slot cannot exceed the slot, whatever the slot becomes. So the rule
    is that no pill rule anywhere declares a `min-width`.
    """
    label = STYLE[STYLE.index('body[data-mode="context"] .talk-label{'):]
    label = label[:label.index("}")]
    assert "min-width:0" in label and "width:100%" in label and "max-width:240px" in label
    # And no other rule may re-introduce a floor. The keyboard query had one too.
    for chunk in STYLE.split(".talk-label{")[1:]:
        rule = chunk[:chunk.index("}")]
        assert "min-width:" not in rule or "min-width:0" in rule, (
            f"a .talk-label rule declares a min-width, which can exceed --hold-w: {rule!r}"
        )


def test_the_phone_band_stacks_instead_of_running_off_the_side():
    """Measured, before this block existed: the band asked for 476px on a 390px screen — four
    52px areas, a 200px hold slot, four 10px gaps and 28px of padding. Orders sat at x=-29 and
    Products ended at x=419, and the collision gate said so in its own words ("29px off the
    side — fixed furniture must fit the screen").

    The band does not get wider, so the arrangement changes: the same 112px becomes two rows,
    the four areas above and the hold along the whole of the bottom. The separation §8 requires
    between NAVIGATION and VOICE is then vertical instead of horizontal — geometry either way.

    `--hold-w` must still be the ONE token the hold region and the hole the dock leaves for it
    share, or they can drift apart again; what changed is that the hole is a row.
    """
    phone = STYLE[STYLE.index("@media (max-width:560px){"):]
    phone = phone[:phone.index("\n}")]
    assert "--hold-w:100%" in phone
    assert "flex-wrap:wrap" in phone
    assert '.dock-gap{order:1;flex:0 0 100%;width:var(--hold-w)' in phone, (
        "the hole the dock leaves for the hold is no longer measured in --hold-w"
    )
    # In CONTEXT MODE only. On the idle screen there is no pill in this band — the whole stage
    # is the hold — so stacking there reserved a row for nothing and lifted the four icons 28px
    # into the hold label's own line, which the gate measured as a 58 x 4px collision.
    assert 'body[data-mode="context"] .dock{flex-wrap:wrap' in phone
    assert 'body[data-mode="orb"] .dock-gap{display:none}' in phone
    assert "width:var(--hold-w)" in phone, "the hold region is no longer measured in --hold-w"
    # The labels come back with the space stacking supplies: a cube and a luggage tag are not
    # self-evident, and they were only dropped to buy width.
    assert ".dock-label{display:block}" in phone
    # And the base rules the phone block overrides are still there for the tablet.
    assert ".dock-gap{flex:none;width:var(--hold-w)}" in STYLE


def test_the_phone_navigation_rail_wraps_rather_than_hiding_a_control():
    """At 390 the rail wanted 468px of chips in 354px of container and the last two — Split and
    the open set — were off the screen entirely. `control_clipped_by_container` counts a
    navigation chip as fixed furniture on purpose: "nothing on the glass says a navigation strip
    continues past the edge of the screen."

    Wrapping is conditional by construction, so a rail whose chips fit is one row and 601 and
    800 never reach this block. The fade must go with the scroll — a mask that says "there is
    more this way" over a row that has already wrapped is a lie."""
    assert ".context-nav{flex-wrap:wrap;overflow-x:visible;row-gap:6px}" in STYLE
    assert '.context-nav[data-overflow="1"]{-webkit-mask-image:none;mask-image:none}' in STYLE
    # The tablet keeps the scrolling rail and its fade.
    assert ".context-nav{" in STYLE and "overflow-x:auto" in STYLE


def test_the_card_header_reads_down_the_phone_rather_than_across_it():
    """At 390 the identity column is ~250px of a 358px card, because the money and the state
    badges hold the other 110px beside it: "Alexandra Featherstonehaugh-Wallingford" came out
    on four lines, broken mid-word twice. Stacked, it wraps to two.

    The ORDER of the answer is unchanged — who and which record, then how much and what state.
    Only the axis changes, because down is the direction a phone has room in."""
    phone = STYLE[STYLE.index("@media (max-width:560px){\n  .context-nav"):]
    phone = phone[:phone.index("\n}")]
    assert ".card-head{flex-direction:column;align-items:stretch;gap:10px}" in phone
    assert ".head-side{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}" in phone
    # The tablet's own header is untouched: identity left, money and state right.
    assert ".card-head{display:flex;align-items:flex-start;gap:12px;margin-bottom:12px}" in STYLE
    assert ".head-side{display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex:0 0 auto}" in STYLE


def test_the_row_chevron_no_longer_lands_on_the_timestamp():
    """`.rows.tight .row{padding:9px 0}` is a SHORTHAND: it reset the 26px right-hand padding
    `.row.tappable` reserves for the chevron at `right:2px`. The chevron was therefore drawn 9px
    into the row's own right-hand column on every tight list in the product — "1h ago" read
    "1h ag›" on the inbox, the work queue and every order list.

    Measured at 390, 375, 601 and 800: an identical 9 x 18px overlap at all four. So it is NOT a
    phone defect, it is not a regression introduced here, and the fix is not scoped to phones.
    The collision gate cannot see it and is right not to — the chevron is `aria-hidden`, which
    makes it decorative, and a decorative mark beside text is what a chevron is for."""
    assert ".rows.tight .row{padding-top:9px;padding-bottom:9px}" in STYLE
    assert ".rows.tight .row{padding:9px 0}" not in STYLE
    assert ".row.tappable{position:relative;padding-right:26px}" in STYLE


def test_the_rails_disclosure_is_a_finger_target():
    """§6: every control is at least `--tap` high, and the collision gate enforces 44 with no
    tolerance. `.rail-more` was 32 and had never been measured: collision.js's fixtures are
    rendered payloads, and the disclosure only exists on a rail with more chips than fit, which
    takes a real order from a real backend to produce. `scripts/browser/mobile.js` opens one."""
    rule = STYLE[STYLE.index("\n.rail-more{"):]
    rule = rule[:rule.index("}")]
    assert "min-height:44px" in rule
    assert "min-height:32px" not in rule


def test_the_deck_may_shrink_when_the_keyboard_takes_the_screen():
    """`.deck{min-height:72px}` is right on a full screen and wrong behind a keyboard. A floor
    the column cannot honour is not a short deck: it is a deck that OVERFLOWS, painted out
    through the bottom of the layout and under the fixed band. Measured on a 375 x 313 phone,
    the compose card's subject field came out at y 232-278 with the hold band starting at 237,
    so `#talk-label` was drawn 27px across the field being typed into. The deck scrolls; a
    short deck is an interaction, and a card under the furniture is a defect."""
    assert ".deck{position:relative;flex:1;min-height:72px}" in STYLE
    keyboard = STYLE[STYLE.index("@media (max-height:520px){"):]
    keyboard = keyboard[:keyboard.index("\n}")]
    assert ".deck{min-height:0}" in keyboard


def test_metadata_grey_is_legible_on_a_raised_tile():
    """axe-core measured `--ink-3` at **4.26:1** against `#1f1f23` — the page ground plus the
    card's `.075` glass plus a stat tile's own `.05` — on `.stat-k`, which is 10px. AA wants
    4.5. It missed by 0.24, at every viewport, on the order list, the work queue and the open
    set: this is not a phone defect either.

    `#8a8983` is 4.68:1 on that tile and 5.74:1 on the ground. Moved on the TOKEN rather than on
    `.stat-k`, because every metadata label on every raised tile failed for the same reason —
    §3.2's rule is that a change to the ladder moves all of them together — and seven steps of
    255 is invisible beside the old value and decisive for the ratio. The ladder's ORDER is what
    must not change, and it does not: ink > ink-2 > ink-3 > ink-4.
    """
    assert "--ink-3:#8a8983" in STYLE
    # Over the DECLARATIONS, not the comments: the comment above the token names the value it
    # replaced, which is the point of it, and a search over the whole sheet would be satisfied
    # by the explanation of the change.
    code = "\n".join(line for line in STYLE.split("\n") if not line.lstrip().startswith(("/*", "*", "//")))
    assert "#83827c" not in code, "the old metadata grey is still declared somewhere"

    def luminance(value: str) -> float:
        value = value.lstrip("#")
        parts = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        parts = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in parts]
        return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]

    def contrast(a: str, b: str) -> float:
        la, lb = luminance(a), luminance(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    tile = "#1f1f23"   # what axe measured the stat tile's composite ground to be
    assert contrast("#8a8983", tile) >= 4.5, "metadata grey is under AA on a raised tile again"
    # And the ladder still reads as a ladder.
    rungs = [contrast(c, tile) for c in ("#ebe8e0", "#b9b6ae", "#8a8983", "#7a7a74")]
    assert rungs == sorted(rungs, reverse=True), f"the ink ladder is out of order: {rungs}"


def test_the_keyboard_on_a_phone_yields_the_areas_and_not_the_hold():
    """390 x 844 becomes 390 x ~508 with the keyboard up, where both small-screen blocks apply
    and their arithmetic does not survive the meeting: a 76px band split into two rows is 34px
    of areas over 42px of hold, and this product has never let a control be under 44px.

    So on a phone, while the keyboard is open, the four areas stand down and the hold has the
    band to itself. Same trade the same query already makes with the halves, for the same
    reason: the owner is typing into a field, and the dock is the way to somewhere else.
    It is phone-only — at 601 x 418 the tablet keeps all four, as it does today.
    """
    combined = STYLE[STYLE.index("@media (max-width:560px) and (max-height:520px){"):]
    combined = combined[:combined.index("\n}")]
    assert ".dock-btn{display:none}" in combined
    assert "--hold-w:100%" in combined
    assert "height:48px" in combined, "the hold is not left at a finger's size"
    # And the rest of the room the field needs, which was measured rather than guessed: the
    # rail stops wrapping and sheds the two chips that are not steps, and the orb's band gives
    # up the 44px dot but keeps the Mac's last line.
    assert ".context-nav{flex-wrap:nowrap;overflow-x:auto}" in combined
    assert "#branch-rail{display:none}" in combined
    assert "#stack{display:none}" in combined
    assert 'body[data-mode="context"] .orb-frame{display:none}' in combined
    assert "The deck behind an open keyboard at 375 x 313 measured 63px" in combined, (
        "the measurement this block exists for is no longer written down beside it"
    )
    # The tablet's own keyboard query is untouched and still keeps its four areas.
    keyboard = STYLE[STYLE.index("@media (max-height:520px){"):]
    keyboard = keyboard[:keyboard.index("\n}")]
    assert ".dock-btn{height:48px}" in keyboard
    assert ".dock-btn{display:none}" not in keyboard


def test_the_sheet_is_measured_in_the_viewport_the_phone_actually_has():
    """`vh` is the LARGE viewport — it ignores a collapsing browser address bar — so an 88vh
    sheet in a tab is taller than the screen is and its Done button ends up underneath the
    browser's own chrome. In the installed PWA the two units are identical, so the tablet pays
    nothing for this."""
    assert "max-height:88dvh" in STYLE
    assert "max-height:calc(88dvh - 14px)" in STYLE
    assert "max-height:88vh" not in STYLE
    # And the notification region, which is only ever sized in the media query whose whole
    # subject is the keyboard being open. `vh` there measures the screen the phone would have
    # had if the keyboard were not on it, which is the one thing that query knows is false.
    assert ".notes{max-height:26dvh}" in STYLE
    assert "26vh" not in STYLE


# --------------------------------------------------------------------------- the gate


def test_the_phone_gate_is_in_the_default_browser_sweep():
    """A gate left out of the default tuple proves nothing between releases — which is exactly
    how accept.js came to be the only check that had ever seen the duplicate `replaceCard`."""
    from experience import browser

    source = Path(browser.__file__).read_text(encoding="utf-8")
    default = source[source.index("for script in (scripts if scripts is not None else"):]
    default = default[:default.index("):")]
    assert "MOBILE_SCRIPT" in default, "the phone gate is not in run_checks' default sweep"
    capture = source[source.index("for extra in (TABLET_SCRIPT"):]
    capture = capture[:capture.index("):")]
    assert "MOBILE_SCRIPT" in capture, "the phone gate takes no screenshots"
    assert browser.MOBILE_SCRIPT.exists()


def test_the_phone_gate_measures_both_phones_with_real_touches():
    """`element.click()` dispatches straight at the node and cannot be swallowed by anything
    painted over it, so a gate that used it could not see the defect class this one exists for.

    375 is in the matrix as well as 390 because the failure being measured is ARITHMETIC: a
    band that fits 390 by four pixels does not fit 375 at all."""
    assert "width: 390, height: 844" in GATE
    assert "width: 375, height: 667" in GATE
    assert "Input.dispatchTouchEvent" in GATE
    assert "const PRESS_MS = 95" in GATE
    # The insets are SET, which is the whole reason the tokens exist.
    assert "--safe-t:${INSETS.top}px" in GATE and "--safe-b:${INSETS.bottom}px" in GATE
    # And the authority is the page's own engine, not a new opinion about phones.
    assert "window.CrooksCollide.scan({})" in GATE


def test_the_phone_gates_names_are_guarded():
    """The same guard tests/test_touch.py asks for its own gate: a run that stopped measuring
    a viewport must FAIL, not report a smaller green number."""
    guard = (ROOT / "tests" / "test_browser.py").read_text(encoding="utf-8")
    for name in ("no interactive collision",
                 "the voice layer touches no navigation control",
                 "every fixed navigation control fits the screen",
                 "the dock band and the room reserved for it are the same number",
                 "nothing a finger presses sits in the home indicator's strip",
                 "with the keyboard open the hold is still a whole control on the screen",
                 "the chevron sits beside what a row says, never on it",
                 "prefers-reduced-motion stops the motion"):
        assert name in guard, f"tests/test_browser.py does not guard the phone gate's {name!r}"
