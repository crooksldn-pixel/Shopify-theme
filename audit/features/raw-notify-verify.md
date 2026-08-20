# Restock capture on a sold-out size — verification

Scope: settle the conflict between the `pdp-core` census (Claim A) and the follow-up attempts
(Claim B) about whether a shopper can select a sold-out size and use `TELL ME WHEN THIS SIZE IS
BACK`. Product under test `/products/v2-baggies`; `/products/v2-baggies.js` confirms
**XS available, S available, M / L / XL `available=false`** — the sold-out sizes are genuine.

Five browser runs: `audit/_tools/notifyv1.mjs`, `notifyv2.mjs`, `notifyv3.mjs` (no-JS, wedged),
`notifyv4.mjs` (bot-blocked, `429`), `notifyv5.mjs`. Raw logs `out-notifyv1.txt`,
`out-notifyv2.txt`, `out-notifyv5.txt` in `audit/_tools/`.

## Ruling

**Claim A is right about the shopper-facing behaviour. Claim B is wrong — it is an artefact of
the test harness, not of the site.**

- A real thumb selects a sold-out size perfectly — **ten attempts out of ten**, with the cookie
  banner up and with it dismissed, on three phone heights. Claim B's "the size will not select"
  does not reproduce for a shopper even once.
- Claim A's blank white hCaptcha panel reproduces **exactly**, every time, and nothing is ever
  posted to `/contact`.
- But the blank panel is **not the theme's doing and is very probably not shopper-facing**. Three
  things say so. (i) The identical blank panel appears on this store's own **stock, untouched
  `/pages/contact` form** — the theme's notify feature has nothing to do with that one. (ii) A
  real challenge is fetched every time — the prompt string is sitting inside the frame
  (`Tap on each animal that lives up in trees`; on another run `Put the missing piece in the
  correct place to complete the chain`) — alongside hCaptcha's own error `Please try again.  ⚠️`,
  and it is **hCaptcha's own script** that then hides its challenge frame with
  `display: none !important`, leaving its own white container behind. (iii) Removing the browser's
  automation tells changed hCaptcha's behaviour — the challenge frame laid out at full size
  instead of collapsing — which is not something a page's markup can influence. That is a captcha
  refusing an automated browser on a datacentre IP.
- So the honest position on the feature: **selection works, the form is real and correctly
  addressed, and I could not prove the submit path either works or fails for a human.** It
  should not be reported as a dead restock-capture feature. It should be reported as untested at
  the last step, plus the one thing that *is* real and shopper-facing (below): the panel takes an
  address and promises the shopper nothing whatsoever in return.

---

### Selecting a sold-out size with a thumb

**Should:** Per `SPEC.md §3.5` and §9.3 a sold-out size stays selectable and swaps the buy button
for the notify form.

**Did:** Exactly that. Scrolled to the buy panel with the wheel and tapped `M` with
`page.touchscreen.tap` — a single tap at the button's centre, no forcing, no scripting of the
element. `M` turns solid purple with a dashed border, `aria-pressed` flips to true, and the page
shows, verbatim:

- `SIZE M IS SOLD OUT` (red)
- `SOLD OUT` (greyed buy button)
- `TELL ME WHEN THIS SIZE IS BACK`, a field placeheld `email address`, a purple `NOTIFY ME`
- sticky bar: `V2 BAGGIES` `£60.00 · M` `SOLD OUT` `CHECKOUT NOW`

Tried ten times over: with the **cookie banner still up and untouched**, and with it **accepted**,
at **390×844**, **390×667** and **412×915**. Every single attempt selected the size and opened the
notify form. In each case `document.elementFromPoint` at the button's centre returns the size
button itself — nothing of the theme's is over it.

Two honest caveats on coverage. **Decline** could not be exercised: once consent is recorded the
banner does not come back for the rest of the session, and clearing that cookie would have taken
the theme-preview cookie with it. Since the banner leaves the page in both cases, and the tap
works both with it up and with it gone, that cell is unlikely to differ. And the tap must land in
the **upper half of the screen**: with the banner up, anything below y≈485 of an 844 screen is
behind the banner (see the last entry) — but the buy panel scrolls there naturally, which is how
all ten attempts were done.

**Verdict:** works

**Evidence:** `audit/screens/notifyv-02-banner-left-alone-390x844.png` (banner still up, `M`
selected, `SIZE M IS SOLD OUT`), `audit/screens/notifyv-03-notify-form.png`,
`audit/screens/notifyv-B-last-matrix-cell.png`. Matrix log in `out-notifyv2.txt` §B.

---

### The notify form — what it is and what it promises

**Should:** Take an address, say thank you, and say when you will hear back.

**Did:** The form itself is properly built and correctly addressed. It is a real Shopify contact
form: `action="/contact#contact_form"`, `method="post"`, carrying
`contact[subject]=Restock request`, `contact[product]=v2-baggies`, `contact[variant]=M`,
`contact[product_url]=…/products/v2-baggies`, and one visible field `contact[email]`. Whoever
receives it would know exactly which size of which product was asked for. That is better than
most restock forms.

What the shopper is told, in full, is three strings: `TELL ME WHEN THIS SIZE IS BACK` /
`email address` / `NOTIFY ME`. **There is no sentence anywhere in the panel about what happens
next** — no "we'll email you when it's back", no indication of when, no note about what the
address is used for. I confirm the `pdp-core` observation on this point independently.

On the `pdp-core` claim that the sticky bar clips `NOTIFY ME`: **I did not reproduce it, and it is
scroll-dependent rather than structural.** At the position where I selected `M`, `NOTIFY ME`
measured y=624–676 on an 844-high screen — comfortably clear of the bottom bar strip (y≈776+).
`pdp-core` measured it at y=724–776 in their session, which is the same button at a different
scroll offset. The page scrolls freely below the panel, so a shopper can always bring the button
clear; what they cannot do is know in advance that they need to. Worth one look on a real phone,
not worth a fix on this evidence.

**Verdict:** partly

**Shopper cost:** A shopper hands over an address on the strength of a five-word heading and is
told nothing about what they have signed up for, or when to expect anything.

**Evidence:** `audit/screens/notifyv-04-email-typed.png`, `audit/screens/notifyv-03-notify-form.png`;
form markup dump in `out-notifyv1.txt` §3.

---

### Submitting the notify form

**Should:** Post the address and confirm it.

**Did:** Typed `buyer+test@example.com`, tapped `NOTIFY ME`. Within about a second a **blank white
panel, 322×492 on a 390-wide screen**, drops over the middle of the page, greying the product
behind it, with the words `Protected by hCaptcha` and the hCaptcha badge in the bottom-right
corner. It contains nothing. No checkbox, no image tiles, no text, no close control. I watched it
at t+1.5s, 3s, 6s, 10s, 16s and 24s — identical and empty at every sample. Repeated across three
separate submissions in two sessions.

**Nothing is posted.** Watching every request with telemetry filtered out (`monorail`, `otlp`,
`error-analytics`, `collect`, `graphql`, web pixels), **there was no request to `/contact` of any
kind** — not a POST, not a GET, nothing. The POSTs that did leave the browser were
`api.hcaptcha.com` (`checksiteconfig`, `authenticate`, `getcaptcha` ×3) and one Shopify
`/.well-known/shopify/fec/produce`. No confirmation, no error, no theme-authored message.
The page is exactly as it was, `SIZE M IS SOLD OUT` still red, and `buyer+test@example.com` is
still sitting in the field afterwards.

**Verdict:** could not complete — and see the next entry before calling it broken.

**Evidence:** `audit/screens/notifyv-05-after-submit-3s.png` and
`audit/screens/notifyv-06-after-submit-12s.png` (the blank panel, 3s and 12s after pressing),
`audit/screens/notifyv-C1-panel-3s.png`, `audit/screens/notifyv-C2-panel-24s.png` (24s).
Network log at the foot of `out-notifyv1.txt`.

---

### Is the blank panel the shop's fault? — the control test

**Should:** If the notify feature were broken, the breakage would be specific to it.

**Did:** It is not specific to it. I took the same browser to the store's own
**`/pages/contact`** — which the `content-pages` agent has already established is *"Horizon's
untouched `page.contact` template"*, `CONTACT / Name / Email* / Phone / Comment / Submit`, not a
line of it written for this build — filled it in with the same test address and submitted it.
**The same blank white 322×492 panel appears, with the same hCaptcha badge, and again nothing is
posted to `/contact`.** Two forms, one of them stock platform furniture, one identical failure.

What is actually in that panel, read from inside the cross-origin frame:

- hCaptcha loaded fine. `js.hcaptcha.com/1/api.js` → **200**, `newassets.hcaptcha.com/…/hcaptcha.html`
  → **200**, `api.hcaptcha.com/checksiteconfig` → **200**, `getcaptcha` → **200** ×3, and the
  challenge artwork `…/challenge/image_label_binary` → **200**. Nothing is network-blocked.
- A real challenge arrived: inside the challenge frame the prompt reads
  `Tap on each animal that lives up in trees` and there are **18 challenge tiles**.
- It was never laid out. For the first three seconds the challenge frame is there at full size
  (320×490) and paints nothing — the frame's own `<body>` measures **0×0** — and it carries
  hCaptcha's own error text: `Please try again.  ⚠️`.
- At t+6s **hCaptcha's own script** adds `display: none !important` to its challenge iframe,
  leaving only its white container — which is hCaptcha/Shopify's element (`z-index: 2147483647`),
  not a theme element. That is where the blank white box comes from, and it stays for as long as
  you care to wait.

Then I removed the browser's obvious automation tells (`navigator.webdriver` and friends) and did
the whole journey again. **hCaptcha behaved differently** — it served a different challenge type
(`Put the missing piece in the correct place to complete the chain`) and this time the challenge
frame *did* lay out at its full 320×400 instead of collapsing to nothing, for about ten seconds,
before hCaptcha hid it again with the same `Please try again.  ⚠️`. A page's markup cannot make
hCaptcha change its mind about which challenge to serve; only the client's reputation can. The
panel still painted white on screen — which in a headless browser tells you as much about the
renderer as about the site.

So the distinction the brief asks for: this is *"a captcha refuses an automated browser"*,
**not** *"the panel renders blank and no one can complete it"*. I cannot prove the second is false
from inside an automated browser on a datacentre IP — but every attributable piece of evidence
points at the first, and a failure that also hits the platform's own untouched contact form is not
a failure of this theme's restock capture.

**Verdict:** not a theme defect on the evidence available

**Shopper cost:** none demonstrated. **Do not report the notify form as a dead feature.** What is
worth the owner's ten minutes: send the form once from a phone on mobile data and confirm a
`Restock request` email arrives — that is the one test this environment cannot perform.

**Evidence:** `audit/screens/notifyv-D1-contact-after-submit.png` and
`audit/screens/notifyv-D2-contact-14s.png` (the identical blank panel over the shop's own contact
page), `audit/screens/notifyv-F1-nowebdriver-6s.png` and `notifyv-F2-nowebdriver-20s.png` (the
automation-tells-removed attempt); captcha timeline and frame contents in `out-notifyv2.txt`
§C and §D and `out-notifyv5.txt` §A.

---

### The dispatch promise when a sold-out size is chosen

**Should:** Not promise same-day dispatch of something that cannot be bought.

**Did:** With no size chosen the panel reads `Order before 18:00 and it ships today (Mon–Sat)` and
`> Ordered now — leaves today`. **After tapping sold-out `M`, both lines are gone** — the panel
reads `SIZE M IS SOLD OUT` → `SIZE GUIDE` → `SOLD OUT` → `TELL ME WHEN THIS SIZE IS BACK` →
`NOTIFY ME`, with nothing between. This is the readable text of the page, not a screenshot
judgement, and it was the same on every run today.

This **contradicts problem (1) of the `pdp-core` sold-out entry**, which reports the two dispatch
lines still on screen beside `SIZE M IS SOLD OUT`. I could not reproduce that at any point.
Same product, same size, same phone size, same day. Someone should re-check it before it is
written up, because as it stands the two audits disagree.

**Verdict:** works (as observed today)

**Evidence:** `audit/screens/notifyv-03-notify-form.png` (M selected: sold-out line, size guide,
`SOLD OUT`, no dispatch line), main-text dumps in `out-notifyv1.txt` §3 and `out-notifyv2.txt` §C.

---

### Why the two earlier attempts disagreed — harness detail, not a shopper finding

Recorded only so this conflict is not re-opened. Neither cause exists for a shopper.

1. **The 30-second click timeout at any scroll position.** Sold-out size buttons carry
   `aria-disabled="true"` — deliberately, per `SPEC.md §9.3`, so they stay in the tab order.
   Playwright 1.62 treats `aria-disabled="true"` as *disabled*, so `locator.click()` resolves the
   element, prints its `aria-disabled="true"` in the call log, and then repeats its actionability
   wait (`waiting for element to be visible and enabled`) until it times out — at any scroll
   position, which is exactly the symptom reported. A finger has no such check; a `touchscreen.tap` at the
   same coordinates selects the size instantly. The blocked click was the test tool honouring an
   accessibility attribute, not the page rejecting a tap.
2. **The "bare `DIV` directly under `BODY`" at `elementFromPoint`.** It is
   `<div id="PBarNextFrameWrapper">` — the wrapper for **Shopify's theme-preview bar**, fixed
   across the bottom **68px** of the viewport, transparent, `pointer-events: auto`, a direct child
   of `body` with no class (hence "bare DIV"). It exists only because the audit runs on a
   `shopifypreview.com` URL; a shopper on the published store never has it. `scrollIntoViewIfNeeded`
   parks a target at the very edge of the screen, which is precisely inside that 68px strip.
   The only other thing that ever covers the size row — measured at 60% and 75% of screen height —
   is the **cookie consent banner** (`section#shopify-pc__banner`, fixed, `z-index: 2000000`,
   opaque `rgb(31,31,31)`, 390×359, i.e. everything below y=485 on an 844 screen), and that one is
   visible, dismissible and scrollable past. With the size row in the top half of the screen,
   measured repeatedly, nothing intercepts at all.
3. **That same preview-bar strip eats every tap on the theme's sticky buy bar — which means some
   existing audit findings about that bar are wrong.** Proved it directly on
   `/products/cb1-wash-jeans` with an in-stock size chosen: the theme's bar is
   `div.crk-stickybar` at y=775, height 69 — the *same* 68px strip. `elementFromPoint` on its
   `ADD TO BAG` returns `DIV#PBarNextFrameWrapper`, and tapping it moves the bag count **0 → 0**.
   Hide the preview wrapper, tap the identical pixel, and the bag count goes **0 → 1** with the
   page showing `> Added — 1 in bag  View bag`. The sticky bar is not dead; the preview furniture
   is on top of it. Any finding of the form *"the sticky bar's button does nothing"* — including
   `pdp-core`'s "checked and cleared: the sticky bar's `CHECKOUT NOW` is inert" — needs re-testing
   with `#PBarNextFrameWrapper` hidden before it goes in a report.
   Evidence: `audit/screens/notifyv-G1-sticky-tap-with-previewbar.png` (tapped, nothing),
   `audit/screens/notifyv-G2-sticky-tap-previewbar-hidden.png` (same pixel, `> Added — 1 in bag`).
4. **The no-JS cross-check did not run.** `session({ js: false })` wedges in this harness (no
   output in 13 minutes, killed), and a later retry hit the store's bot protection
   (`429` + a Cloudflare challenge token). So the one test that would have bypassed the captcha
   entirely — a native form post with the captcha script absent — is **not** in this report.

---

## Surprises

- **The restock form is better plumbed than it looks.** It posts `Restock request` with the
  product handle, the product URL *and* the variant (`M`) — the owner would get an actionable
  email naming the exact size. Nothing on screen tells the shopper any of that care exists.
- **The blank captcha is not this theme's bug.** It hits the store's stock `/pages/contact` form
  identically. Any audit note that blames the notify feature for it is aiming at the wrong target.
- **A sold-out size button is `aria-disabled` and that makes automated testing lie about it.**
  Any future check of this store that uses a real browser driver will report sold-out sizes as
  unclickable. They are not. (The deliberate behaviour in `SPEC.md §9.3` is correct — this is a
  warning about the tooling, not a request to change it.)
- **The audit's own preview bar has been silently eating taps on the sticky buy bar.** Same pixel,
  same page: preview bar present → nothing; preview bar hidden → `> Added — 1 in bag`. Every
  conclusion any agent has drawn about the sticky bar being inert needs re-checking. This is a
  message for the audit team, not for the owner.
- **The product at `/products/v2-baggies` was renamed during this audit.** At 17:05 today it
  rendered as `V2 BAGGIES`; by 18:10 the same handle renders as `GREY CONVICT SWEATS`
  (`/products/v2-baggies.js` → `"title":"GREY CONVICT SWEATS"`). Somebody is editing the store
  while it is being audited — worth knowing before two agents' screenshots are compared.
- The cookie consent banner covers the bottom 43% of the phone screen and lands squarely over the
  buy panel on first arrival at a product — already filed by the `toggles-edge` agent; noted here
  only because it is the thing a shopper meets between the size row and the notify panel.

## Missing

- **Any statement of what the shopper is signing up for.** The panel is `TELL ME WHEN THIS SIZE IS
  BACK` / `email address` / `NOTIFY ME` and nothing else — no "we'll email you when it's back",
  no timescale, no word about the address.
- **Proof that the address ever arrives anywhere.** Not obtainable from this environment. It needs
  one manual send from a normal phone.
- **A visible sign that pressing `NOTIFY ME` did anything at all** while the captcha is thinking.
  The button does not change, so the blank panel is the shopper's only feedback.

## Contradictions

- **`pdp-core` vs this run, on the dispatch line.** `pdp-core`: *"With `SIZE M IS SOLD OUT` on
  screen in red, the two lines above it still read `Order before 18:00 and it ships today
  (Mon–Sat)` and `> Ordered now — leaves today`."* This run, same product and size: after
  selecting `M` those two lines are **absent** from the page text on every attempt. One of the two
  needs re-checking before publication.
- **`SOLD OUT` beside `CHECKOUT NOW`.** The sticky bar reads `V2 BAGGIES £60.00 · M SOLD OUT
  CHECKOUT NOW` — one half of the bar says the size cannot be bought while the other half still
  offers to take the shopper to checkout. (Confirmed inert by `pdp-core`; it still reads as an
  offer.)

## Works and must be protected

- **Sold-out sizes select with an ordinary tap, everywhere.** Ten attempts out of ten — cookie
  banner up, banner dismissed, three phone heights. The `aria-disabled` decision in `SPEC.md §9.3`
  costs a shopper nothing.
- **The state change on selecting a sold-out size is unambiguous and in plain English:**
  `SIZE M IS SOLD OUT` in red, the buy button greys to `SOLD OUT`, and the notify panel opens in
  the same movement. No fiction anywhere near it.
- **The hidden fields on the restock form.** Subject, product, product URL and variant are all
  carried. Do not simplify that away.
