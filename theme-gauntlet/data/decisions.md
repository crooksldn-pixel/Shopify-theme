# Decisions log — Theme Gauntlet v2, annadenning.com run (2026-08-19)

Every deviation from the gauntlet spec, and why. Logged per the spec's "make the
reasonable call and log it" rule.

## D1 — Single-site run, not OLD vs NEW
The fill-in block arrived blank except for one URL in the request itself
(https://www.annadenning.com). Preflight established that annadenning.com is a
**Kajabi** site (all assets from kajabi-cdn.com; Shopify paths /cart,
/products.json, /collections/all all 404). There is no Shopify OLD/NEW theme
pair, no preview link, and no redesign to test. The user's instruction was
"audit this site", so the gauntlet runs as a **single-site Buyer's Cut**:
n=20 cold buyers × 1 site (20 sessions, not 40).
Dropped as inapplicable: parity diff, "what the new theme broke" regression
hunt, paired preference, SHIP/HOLD-on-redesign verdict. Kept: feature census,
20 live agent-driven buyer sessions, buyer's-eye rule, evidence rule,
information firewall, full 5-seat council incl. skeptic, peer review,
feature scorecard with UNTESTED honesty. Verdict reframed as a site verdict
with a prioritized, evidence-pinned fix list.

## D2 — Session-repo mismatch noted
This session's workspace repo is an unrelated Shopify theme for a different
store (CROOKSLDN). It plays no part in this audit; gauntlet artifacts live in
theme-gauntlet/ only. If the intended target was actually the CROOKSLDN
live-vs-staging comparison, that is a different run — flagged to the user in
the final summary.

## D3 — Run-integrity assertion adapted
window.Shopify.theme.id does not exist on Kajabi. Replaced with a host+URL
assertion logged on every page load to sessions/{id}-nav.log. Any session that
navigated off *.annadenning.com (other than an external link a buyer knowingly
followed) is flagged. This is plumbing and appears nowhere in findings.

## D4 — Brand intent source (firewall preserved)
BRAND_INTENT and REDESIGN_THESIS were blank. The council (Phase 4 only) will
judge buyer perception against the site's **own public positioning** — its
meta description and homepage promises — captured verbatim at synthesis time,
not against user-supplied intent. Buyers and the census never see this framing;
buyer materials contain zero positioning language. Firewall intact.

## D5 — Errand inputs derived from the store itself
KEY_PRODUCTS / HERO_COLLECTION / GIFT_BUDGET were blank. Derived after census
from what the store actually sells (courses, membership, certification, book),
with the gift cap set from the observed price ladder. Logged in
data/feature-assignments.json.

## D6 — Commerce-flow rules translated to Kajabi
No Shopify cart. Kajabi sells via per-offer checkout pages. Buyers stop at the
checkout page, never submit payment, never create accounts, never subscribe to
email forms, never send contact forms. If a checkout exposes a coupon field, a
buyer tries an obviously fake code and records the error verbatim. Popups get
real-buyer treatment: close, or leave if it won't close.

## D7 — Intent mix retranslated for a course/coaching store
buy-now (6) → ready to buy a specific course/book today;
research/compare (4) → weighing this school against alternatives kept mentally
open in another tab; browse/graze (3) → curious wanderers from social;
gift hunters (3) → buying for someone else within a budget;
returning customers (2) → existing students trying to reach their content;
lookup/support (2) → find a certified facilitator / verify credentials /
find contact or policy answers. Device split stays 12 mobile / 8 desktop.

## D8 — Plumbing: sandbox TLS
The sandbox's egress proxy cannot pass Chromium's TLS 1.3 handshake; harness
caps the browser at TLS 1.2 (verification still on, proxy CA trusted). Zero
bearing on findings; logged for reproducibility.

## D9 — Cart isolation → profile isolation
Fresh Chromium user-data-dir per buyer (cookies, localStorage isolated), one
persistent browser per buyer, ≤5 concurrent. Politeness pacing ~0.9–1.9s per
step plus human-scale think time between agent decisions.

## D10 — Panel determinism
The 20-persona roster was authored once against the census and committed as
data/personas.json (panel_version v1-seed42). The committed file itself is the
stable panel future runs reuse — rerunning the gauntlet must load this file,
not regenerate it. Intent mix, device split, and trait sprinkling follow the
spec exactly (see D7).

## D11 — Third-party pages and our probe environment
Three buyer moments hinge on how NON-annadenning properties responded to our
cloud environment: B18's Cloudflare "Attention Required" block on the login
path, B08's Instagram error page, and B05's Amazon bot-check interstitial.
A datacenter IP can be treated more harshly than a home buyer's connection, so
the synthesis must not present third-party blocks as site defects. What stands
regardless: the on-site facts (the members' area requires login; the book has
no on-site purchase path; the Instagram link's destination is what it is).
The skeptic seat and chairman weigh these accordingly.

## D12 — Census correction (found in peer review)
The census recorded the facilitators directory as having "no search box, no
filters". Buyer B19's live session falsified this: the directory has a working
search box and country chips (shots/b19-02-directory-found.png). The census
note is superseded; the scorecard and report carry the corrected fact. Root
cause: the census probe read the page before its widgets finished appearing.

## D13 — Peer standings applied to synthesis
Reviewer rankings (lower=better, summed): Seat 5 skeptic 4 (ranked 1st by all
four reviewers), Seat 4 UX 7, Seat 1 CRO 11, Seat 3 operator 13, Seat 2 brand
15. Claims killed in review were removed from the report body; the report's
"Peer-review standings" section lists them for transparency.
