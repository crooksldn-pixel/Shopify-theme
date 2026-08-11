# CROOKSLDN theme gauntlet — 100-shopper audit: NEW redesign vs OLD live theme

**Method.** 100 deterministic simulated shoppers (seed 42), the same roster walking BOTH themes across 7 journey scripts × 2 devices, over 246 real Playwright screenshots with per-step timing, console-error, failed-request and theme-ID-assertion instrumentation. 200 structured verdicts + 100 paired comparisons. **n=100 simulated shoppers is directional evidence, not a live A/B test** — every preference count below is simulation-internal. Personas never saw the brand brief (information firewall held: intended adjectives appear 0× as quoted-back language in persona output).

- **OLD** = live published theme `202044309847` (CROOKSLDN — Dev), Horizon 3.5.0.
- **NEW** = unpublished staging theme `202053779799` (CROOKSLDN — Staging), Horizon 3.5.0 — a genuinely different custom build (`crk-*` markup, own header/drawer/cart), not a re-skin. Homepage HTML is 5× smaller and structurally distinct. The panel was justified; this is not a colors-only change.

## Verdict: SHIP WITH FIXES

**The redesign did what it set out to do on identity — and it did not just restyle the furniture.** It measurably moved perception from "reseller/template, plainly mid-priced" to "a real brand, plausibly premium," gave the store a name shoppers actually remember, and sharpened the audience read toward young streetwear buyers. On the evidence, that is expansion, not a re-skin. NEW also wins trust (2.73 vs 2.25 / 5), would-return (51% vs 32%), and the whole mobile experience (mobile preference 41–15, mobile completion 50% vs 40%).

**But it shipped with a P0 hole in the money path: search is broken.** Tapping SEARCH on NEW lands on a dead page with no usable input — verified live, not an artifact — and search-led and returning shoppers hit a wall. That, not "the whole funnel," is the real conversion regression. The scary-looking buy-now number (43% complete vs OLD's 80%) is **mostly a measurement artifact**: OLD was captured on the live domain where checkout works, NEW on the preview link where Shopify blocks checkout. Correct for that and NEW's buy-now completion is ~57%; the durable, theme-caused loss is concentrated in search plus a few smaller regressions below.

**Net:** publish the redesign — the identity gain is real and OLD is genuinely weak (research/support shoppers complete 0% on OLD because it has no findable returns policy). But **do not publish until search works**, and clear the four smaller regressions. Full fix list in Section G.

Confirmed by the adversarial skeptic pass (5 of 10 top findings CONFIRMED, 5 WEAKENED with caveats attached, 0 fabricated). Only confirmed findings drive this summary; weakened ones carry their caveat inline below.

---

## A. Funnel table (OLD vs NEW)

All percentages are of the personas in that cell. "Shopping intents" = buy-now + research + gift + returning (personas who could add to cart). "Checkout-reach" is among buy-intent personas only.

| Metric | OLD | NEW | Read |
|---|---|---|---|
| Task completion (all 100) | 47% | **52%** | NEW slightly ahead overall |
| Add-to-cart rate (shopping intents) | 58% | **62%** | ~even, NEW nudge |
| **Checkout-reach (buy-intent)** | 72% | 48%* | *OLD wins, but see S3 — confounded by live-vs-preview checkout block |
| Buy-now completion | 80% | 43%* | *artifact-inflated; ~57% after correcting for the preview block (S3) |
| Median steps to task end | 6 | 6 | identical |
| Search success | 57% | 50% | OLD ahead; NEW desktop search 27% |
| Mean trust (1–5) | 2.25 | **2.73** | NEW +0.48 |
| Would-return | 32% | **51%** | NEW +19pts |
| Severity-4 (abandonment) frictions | 38 | 39 | even |

**By device.** Mobile: NEW completion 50% vs OLD 40%, trust 2.85 vs 2.17, would-return 57% vs 25% — **NEW clearly better on mobile.** Desktop: OLD completion 58% vs NEW 55%, and OLD desktop search success 91% vs NEW 27% — **desktop is where NEW's regressions bite.**

**By intent (completion, NEW vs OLD).**

| Intent | NEW | OLD | Note |
|---|---|---|---|
| buy-now | 43% | **80%** | NEW's core conversion regression |
| research-compare | **60%** | 0% | OLD has no shipping/returns info at all → nobody completes |
| lookup-support | **30%** | 0% | same cause; NEW at least has policies |
| returning | **60%** | 47% | NEW ahead |
| gift-hunt | **60%** | 50% | NEW ahead |
| browse-graze | 60% | **73%** | OLD ahead (NEW lost filters/sort) |

**Abandonment stages.** OLD: after-atc (9), pdp (9), pdp-compare (5), returns (3), account-login (3). NEW: home (8), search (6), size-guide (5), account-login (5), checkout-click (4, partly preview artifact). NEW loses people earlier (home/search); OLD loses them later (pdp/cart) and to missing returns info.

**Paired preference (simulation-internal).** NEW **59**, OLD **36**, neither 5. Two-sided sign test on the 95 decided pairs: **p ≈ 0.023**. By device: mobile **41–15 NEW**, desktop **21–18 OLD**. By intent: research-compare **14–4 NEW**, lookup-support **9–0 NEW**, buy-now **18–11 OLD**.

---

## B. Identity & branding — "has it expanded, or just restyled?"

**Answer: it expanded.** The redesign moved perception decisively toward the brief on every identity axis measured, while introducing legibility costs (Section C, F10).

- **Brand vs reseller vs template** (bluntest identity metric, and it moved a lot): OLD reads **brand 49% / reseller 31% / template 20%**; NEW reads **brand 81% / template 19% / reseller 0%**. NEW **eliminated the "reseller" read entirely** and cut "template" by a point while nearly doubling "real brand."
- **Intended-adjective coverage.** The brief's adjectives (confident, new, exciting/exiting, cool, bold). In aggregated recall + five-second adjectives, **OLD scores 0 on every one of them.** NEW surfaces all five clusters (bold/dark dominant, plus confident, new, exciting, cool). Perception moved *toward* the intent, from a standing start of zero.
- **Price-position alignment.** Brief = mid/premium. OLD: **98% "mid"**, 0% premium — shoppers read it as ordinary. NEW: **44% "premium" + 45% "mid"** — half the panel now reads a premium price, which is the reposition the brief asked for. (Caveat: a premium *look* that shoppers still can't buy from easily is a conversion problem wearing a branding costume — see F1.)
- **Audience match.** Brief = 14–18 into baggy streetwear. OLD's "for whom": generic — "young people / teens / young adults." NEW's: specific and on-target — "streetwear kids into the heist/case-file concept," "lore and drops," "gamer teens." NEW sharpened the audience read toward the target, though a few older/international personas felt *excluded* ("UK street kids, not overseas buyers like me") — consistent with the currency regression (F6).
- **Coherence.** OLD's recall scatters into vague negatives: plain (16), basic, grey (35), empty, "no-returns." NEW's recall converges on a **specific concept** — case-file (27), terminal, maze, short-runs, pixel — and **shoppers recall the brand name unprompted 11× on NEW vs 0× on OLD.** The identity is sharper, not just prettier. The cost: "maze" (9) and "broken-search" (6) show the concept sometimes reads as *confusing*, a usability cost rather than an identity one.
- **Off-brand contamination.** OLD's contaminants are identity-fatal: "plain/basic/generic/empty." NEW's are usability, not identity: "maze/broken-search/popup," plus 19% still "template." Different, more fixable failure mode.

**Verdict on the thesis ("brand authenticity + coherence + conversion"):** authenticity and coherence — **achieved and measurable.** Conversion — **not yet;** the identity win is partly undercut by broken utilities (search, filters, currency switch) that cost the buy-now funnel (Section C).

---

## C. Findings (ranked by conversion impact)

Each finding carries its skeptic verdict. **CONFIRMED** = survived adversarial refutation; **WEAKENED** = core holds, caveat attached. Killed findings are not shown (none were). Evidence paths are relative to `theme-gauntlet/`.

### Surprises (things you likely don't already know)

**S1 — The identity reposition genuinely worked, and it's measurable. [F4 · CONFIRMED · severity 1, no fix]**
"Feels like a reseller" went **31% → 0%**; "feels like a real brand" **49% → 81%**; price read **98% "mid" → 44% "premium"** (identical $69/$83 prices — pure perception). Shoppers recalled the brand name **unprompted 15× on NEW, 0× on OLD**. The skeptic's preview-artifact theory failed: OLD's header shows the CROOKSLDN wordmark yet earned zero name recall, so the shift is the concept working, not the preview chrome. This is the thesis ("brand authenticity + coherence") delivered. *Evidence: `data/aggregate.json` identity block; `data/verdicts/*.jsonl` brand_recall.*

**S2 — Your OLD theme, not the redesign, is the real trust liability — and NEW already fixes it. [F3 · WEAKENED · severity 3]**
On OLD, research-compare and lookup-support personas complete **0%**: the OLD PDP shows delivery timeframes and a free-shipping banner but **no findable returns policy anywhere in the UI**, and its policy pages aren't linked from any menu or footer. NEW puts a complete, specific policy on every PDP — 14-day returns, free UK shipping over £20 (Tracked 24 over £70), UK 1–2 / intl 7–14 day delivery — inside the "Chain of custody — shipping & returns" accordion. *Skeptic caveat: the original claim overstated OLD ("no shipping info at all") — OLD does show delivery timeframes; the true gap is the missing returns policy and unlinked policy pages. Also, NEW's accordion is collapsed by default, so cold shoppers still had to hunt (66 flagged) — the win is real but under-advertised.* *Evidence: `data/followup-accordions.json`; `captures/new/live/fu-crewneck-expanded.jpg`; `captures/old/j6/mobile/meta.jsonl`.*

**S3 — The buy-now "regression" is mostly a measurement artifact; the real loss is search. [F1 · WEAKENED · severity 4→re-scored]**
The raw numbers (buy-now completion 43% vs 80%, checkout-reach 48% vs 72%) are **not like-for-like**: OLD was captured on the live domain and reached a working `/checkouts/cn/…` page; NEW ran on the preview link where Shopify blocks checkout entirely. The 4 checkout-blocked personas alone are ~13 of the 37-point gap; crediting them lifts NEW buy-now to ~57%. Of 17 "affected" personas, 3 actually completed on NEW and 6 also failed on OLD. *Skeptic caveat: NEW's buy-now is plausibly somewhat worse, but the durable, theme-caused core is ~a third of the headline gap and traces to R1 (broken search), a missing above-fold price on some landings, and currency — not a broad funnel collapse.* *Evidence: `captures/{old,new}/j1/*/meta.jsonl`; `data/aggregate.json`.*

---

## D. What the new theme broke (mandatory regression section)

Every persona was required to hunt for one thing NEW does worse. Five survived scrutiny; ranked by conversion impact.

**R1 — Search is a dead end on NEW. [F2 · CONFIRMED · severity 4] — this is the ship blocker.**
Tapping SEARCH in the NEW header lands on `/search` whose input sits in a `display:none` dialog that never opens; there is nothing to type into and keystrokes do nothing. Results render only if a query is already in the URL. OLD's search works — a predictive dropdown with product thumbnails on keystroke. **12 personas abandoned at search on NEW; 41 flagged it.** Verified on the live preview site, so not an automation artifact. Search-led buy (J2) and returning-customer (J7) intents depend on it, and NEW desktop search-success is 27% vs OLD's 91%. *Evidence: `captures/new/live/search-opened-mobile.jpg`, `captures/new/live/search-after-typing.jpg`, `captures/old/j2/mobile/step-02-search-suggest.jpg`, `data/followup-resolutions.json` (new_search).*

**R2 — NEW dropped collection filtering and sorting entirely. [F5 · CONFIRMED · severity 2]**
`/collections/all` on NEW shows only category tabs — zero sort or price-filter controls. OLD has an Availability filter and a Sort dropdown. Browse and gift personas trying to narrow by price or newness have no tool (14 flagged). Bounded by the small 14-product catalogue, but it's a capability OLD has and NEW removed. *Evidence: `captures/new/live/collection-all-desktop.jpg`, `captures/old/j4/desktop/step-03-filter-open.jpg`, `data/followup-resolutions.json` (new_collection_controls = []).*

**R3 — "FILED [date]" labels read as sold-out on buyable products. [F9 · CONFIRMED · severity 2]**
NEW's product cards alternate "AVAILABLE" and "FILED 13.07 / 03.08" with no legend. Shoppers read FILED as sold-out or archived — in their own words: "is FILED sold out?", "if that means sold out, say sold out", "archived?". The items are fully in stock (v2-baggies shows "FILED 13.07" yet Add-to-bag is enabled). The evidence-locker motif manufactures false unavailability signals (~30 flagged). *Evidence: `data/followup-resolutions.json` (new_filed_cards, new_filed_pdp_buyable atc enabled), `captures/new/live/collection-all-desktop.jpg`.*

**R4 — The concept costs legibility for hurried, low-tech and low-vision shoppers. [F10 · CONFIRMED · severity 2]**
The same heist/terminal concept that wins identity (S1) also generates the recall words "maze" (9), "broken-search" (6) and "popup" (4); 19% still say "template"; and ~11 personas couldn't guess a price because none was visible above the fold on some landings. OLD's failure mode is the opposite — legible but generic ("plain/basic/grey/empty"). **Do not fix this by reverting the identity; fix it by adding legibility** (visible price, working search, a FILED legend). *Evidence: `data/aggregate.json` identity.new.recall_words; `data/verdicts/*.jsonl` five_second.price_guess.*

**R5 — Two smaller, real-but-narrower regressions (both WEAKENED on impact, not on existence):**
- **Currency switcher removed. [F6 · WEAKENED · severity 3]** OLD's header carries a USD/GBP region selector; NEW has none anywhere. Combined with the "FREE UK SHIPPING OVER £20" banner over USD prices, international personas can't switch or reconcile the clash. *Caveat: the £/$ confusion itself is shared (both themes render USD — see E); the NEW-specific regression is the removed ability to switch, affecting the 14 listed personas, not the full 43.*
- **Desktop account entry hidden. [F8 · WEAKENED · severity 2]** NEW puts ACCOUNT only inside the MENU drawer; OLD shows a persistent header person-icon. *Caveat: verified on desktop, but both themes reach the same working login by direct URL, and the affected set is mostly the few desktop returning personas, not the 19 originally listed.*
- **CRACK THE CUFFS discount popup. [F7 · WEAKENED · severity 2]** A timed discount-puzzle modal covers content on NEW. *Caveat: desktop-only (did not reproduce on mobile within 20s), and the defensible count is ~20 personas, not 35 — the original number conflated it with cookie-consent reactions.*

---

## E. Shared store problems (theme-independent — both failed)

- **F-SHARED1 — USD shown under a "FREE UK SHIPPING" banner.** The storefront geo-renders USD to non-UK visitors while all copy promises UK shipping in £. Confused international/price-sensitive personas on **both** themes (NEW 43, OLD 42). This is a Markets/currency-settings issue, not a theme issue. *(The NEW-specific part — the removed currency switcher — is F6.)* Evidence: `captures/old/j1/desktop/step-01-home.jpg`, `captures/new/j1/mobile/step-01-home.jpg`.
- **F-SHARED2 — account login is a shared hosted flow with an intermittent Cloudflare wall.** Both themes route `/account/login` to `friendsof.crooksldn.com`; login works (email field, "Sign in or create an account"), but a Cloudflare "verify you are human" interstitial intermittently blocks it and flipped several returning-customer outcomes on both themes. Evidence: `data/followup-resolutions.json` (`old_account_login`, `new_account_login`).
- **F-SHARED3 — `/pages/tracking` is an empty stub.** "Tracking", no form, no widget — linked by both themes. No real order-tracking tool exists. Evidence: `data/followup-resolutions.json` (`old_tracking_page`).

---

## F. Do-nothing list (looks like an issue, isn't — don't redesign these)

- **F-DN1 — cookie-consent banner on NEW but not OLD (86 vs 0).** Almost certainly a preview-domain consent-storage artifact (the ephemeral `shopifypreview.com` session stores no prior consent; the live domain does). **Verify on the published domain before treating it as a theme problem.** Evidence: `data/followup-resolutions.json` (`new_consent_persistence`).
- **F-DN2 — NEW cart PayPal express button renders disabled** (`shopify-paypal-button[disabled]`). Accelerated-checkout buttons are routinely disabled in preview mode; likely not a live bug. Verify post-publish.
- **F-DN3 — "Checkout isn't available in preview" (403).** Shopify preview-link platform limitation. The theme's cart→checkout action fires and navigates correctly; checkout is theme-independent. Evidence: `captures/new/j1/mobile/step-07-checkout-click-failed.jpg`.
- **F-DN4 — USD prices in every capture.** Geo-detection of the audit's egress IP. Real UK shoppers see GBP. Don't treat the currency symbol as a theme choice.

---

## G. Verdict & fix list

**SHIP WITH FIXES.** The redesign delivers the identity/authenticity/coherence half of its thesis (S1, confirmed) and beats a genuinely weak OLD theme on trust, would-return and mobile. It does **not** yet deliver the conversion half — but the block is a small set of fixable utilities, not the concept. Publish after R1; the rest can follow fast.

Every fix below traces to a confirmed or structurally-verified finding. Effort is a rough guess (S/M/L).

| # | Fix | Finding | Funnel stage | % of panel affected | Effort | Evidence |
|---|---|---|---|---|---|---|
| **P0** | **Make search work** — the `/search` input is in a `display:none` dialog; wire the SEARCH control to a functioning search field/overlay | R1 / F2 (CONFIRMED) | discovery | 41% flagged, 12 abandoned | **M** | `captures/new/live/search-opened-mobile.jpg` |
| P1 | Add a legend or change "FILED [date]" so buyable ≠ reads-as-sold-out (e.g. keep FILED as a date stamp but show explicit stock/"AVAILABLE" state prominently) | R3 / F9 (CONFIRMED) | browse/PDP | ~30% flagged | S | `data/followup-resolutions.json` (new_filed_*) |
| P1 | Restore collection sort + price filter on `/collections/all` | R2 / F5 (CONFIRMED) | browse | 14 flagged | M | `captures/new/live/collection-all-desktop.jpg` |
| P1 | Surface a price above the fold on PDP/landing and open (or preview) the "Chain of custody" returns line by default — the policy is great, just hidden | R4/S2 (F10 CONFIRMED / F3) | first-impression + trust | ~11 no-price, 66 hunted returns | S | `data/followup-accordions.json` |
| P2 | Re-add a currency/region switcher (OLD has one; NEW dropped it) | R5 / F6 (WEAKENED) | pricing/trust | 14 clean, up to 43 incl. shared | S | `data/followup-resolutions.json` (new_currency_ui) |
| P2 | Add an ACCOUNT entry to the NEW desktop header (not only the MENU drawer) | R5 / F8 (WEAKENED) | returning | few desktop returning | S | `captures/live-checks.json` (new_account_desktop) |
| P2 | Make the CRACK THE CUFFS popup dismissible-before-content / delay it / suppress on repeat visits | R5 / F7 (WEAKENED) | home | ~20 (desktop) | S | `captures/new/edge-zoom/desktop/step-01-zoom-home-200pct.jpg` |
| P3 (store, not theme) | Fix Markets so UK copy and currency agree; build a real order-tracking page; smooth the Cloudflare wall on account login | E / F-SHARED1–3 | trust/support | both themes | M | Section E |

**Before treating any of these as live bugs, confirm the do-nothing items (F-DN1–4) on the published theme** — the consent banner, disabled PayPal button, checkout block and USD pricing are preview/geo artifacts, not theme defects, and "fixing" them would be wasted work.

---

## Appendix — known / obvious items (surfaced but you likely already know)

- Catalogue is small (14 products), so filter/sort and "walls of products" findings are bounded in impact.
- Gift budget (£60–100 ≈ $76–127) clears the entire catalogue (max price ~$83), so the gift-hunt "filter by price" task is trivially satisfiable regardless of theme.
- "HERO_COLLECTION: Charcoal" is not a real collection; the charcoal cellblock line lives in `sweats` and `new`. J4 used `/collections/all`. (Logged in `data/decisions.md`.)
- Both themes share the same Horizon 3.5.0 base and the same product data, checkout, and hosted account system — differences are in the theme layer only.
- Full method, currency/IP/TLS-proxy notes, and every judgment call are in `data/decisions.md`. Side-by-side screenshots per journey step are in `report/contact-sheet.html`. Reusable persona roster for the next redesign is `data/personas.json`.
