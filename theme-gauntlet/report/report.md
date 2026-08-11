<!-- REPORT BODY DRAFT — executive summary, confirmed findings, and verdict are finalized after the skeptic pass. -->
# CROOKSLDN theme gauntlet — 100-shopper audit: NEW redesign vs OLD live theme

**Method.** 100 deterministic simulated shoppers (seed 42), the same roster walking BOTH themes across 7 journey scripts × 2 devices, over 246 real Playwright screenshots with per-step timing, console-error, failed-request and theme-ID-assertion instrumentation. 200 structured verdicts + 100 paired comparisons. **n=100 simulated shoppers is directional evidence, not a live A/B test** — every preference count below is simulation-internal. Personas never saw the brand brief (information firewall held: intended adjectives appear 0× as quoted-back language in persona output).

- **OLD** = live published theme `202044309847` (CROOKSLDN — Dev), Horizon 3.5.0.
- **NEW** = unpublished staging theme `202053779799` (CROOKSLDN — Staging), Horizon 3.5.0 — a genuinely different custom build (`crk-*` markup, own header/drawer/cart), not a re-skin. Homepage HTML is 5× smaller and structurally distinct. The panel was justified; this is not a colors-only change.

<!-- EXEC-SUMMARY-PLACEHOLDER -->

---

## A. Funnel table (OLD vs NEW)

All percentages are of the personas in that cell. "Shopping intents" = buy-now + research + gift + returning (personas who could add to cart). "Checkout-reach" is among buy-intent personas only.

| Metric | OLD | NEW | Read |
|---|---|---|---|
| Task completion (all 100) | 47% | **52%** | NEW slightly ahead overall |
| Add-to-cart rate (shopping intents) | 58% | **62%** | ~even, NEW nudge |
| **Checkout-reach (buy-intent)** | **72%** | 48% | **OLD wins — NEW's money path regressed** |
| Buy-now completion | **80%** | 43% | **OLD wins decisively** |
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

<!-- CONFIRMED-FINDINGS-PLACEHOLDER -->

---

## D. What the new theme broke (mandatory regression section)

<!-- REGRESSIONS-PLACEHOLDER -->

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

<!-- VERDICT-PLACEHOLDER -->

---

## Appendix — known / obvious items (surfaced but you likely already know)

- Catalogue is small (14 products), so filter/sort and "walls of products" findings are bounded in impact.
- Gift budget (£60–100 ≈ $76–127) clears the entire catalogue (max price ~$83), so the gift-hunt "filter by price" task is trivially satisfiable regardless of theme.
- "HERO_COLLECTION: Charcoal" is not a real collection; the charcoal cellblock line lives in `sweats` and `new`. J4 used `/collections/all`. (Logged in `data/decisions.md`.)
- Both themes share the same Horizon 3.5.0 base and the same product data, checkout, and hosted account system — differences are in the theme layer only.
- Full method, currency/IP/TLS-proxy notes, and every judgment call are in `data/decisions.md`. Side-by-side screenshots per journey step are in `report/contact-sheet.html`. Reusable persona roster for the next redesign is `data/personas.json`.
