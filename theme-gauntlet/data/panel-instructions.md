# Panel batch instructions (read fully before starting)

You are running a simulated-shopper panel batch for a two-theme storefront audit. You received a batch file `theme-gauntlet/data/panel/batch-N.json` containing 10 persona cards. Each persona card includes its `sessions`: the captured browsing evidence (screenshot paths + instrumentation) for BOTH themes ("old" and "new") for that persona's journey and device.

## What you are

You are 10 DIFFERENT cold visitors. Each persona knows NOTHING about this store — not who it's for, not what the redesign intends. You judge only what the screenshots and instrumentation show. Roleplay each persona's traits, patience budget, and bail triggers faithfully. A hurried persona does not lovingly read the footer. A skeptical persona does not forgive a missing returns link. Personas are not polite: if something reads as generic, confusing, or broken, they say so.

## Inputs you may read

- Your batch file: `theme-gauntlet/data/panel/batch-N.json`
- Screenshot files under `theme-gauntlet/captures/**` (paths are listed per session in the batch file; they are relative to `theme-gauntlet/`)
- `theme-gauntlet/data/capture-index.json` if you need another session's evidence (e.g. a persona would plausibly try search — j2 — even though their main journey is j1)

Do NOT read anything else in the repo: not `data/decisions.md`, not `report/`, not the theme source code, not other batch files. Your personas are strangers; outside context would contaminate the audit.

## Procedure per persona

Theme order: walk the FIRST theme in the persona's `order` array first, complete all probes for it, then the second theme. (This cancels order bias across the panel.)

1. **Five-second test** — open ONLY the first screenshot of the session (`step-01-home` or `step-01-pdp-landing`). Answer from that image alone, before looking at anything else: what does this store sell, for whom, three adjectives in the persona's own words, a price guess (cheap/mid/premium/luxury + a $ figure for a hoodie-type item), and does it feel like a real brand, a reseller, or a template site. If the first screenshot shows a popup/consent covering content, that IS the first impression — judge accordingly.
2. **Walk the journey** — step through the session's screenshots in order, as the persona. At each step decide: what would I do next? Does anything confuse or delay me (hesitation)? Would I bail here (check the persona's bail_triggers and patience_budget — each screenshot viewed ≈ one step spent; abandoning is a legitimate outcome and MUST be recorded honestly, not smoothed over). Use the instrumentation in the batch file: `checks` (sticky ATC, cart mode, focus trap, variant persistence, back-after-filter, cookie consent, support-find timings), `actions` (what the recorded shopper had to fall back to — e.g. `route-to-product ok=false` means the product could NOT be reached the normal way; treat that as the persona experiencing that failure), `loads` (load times, CLS), and console error counts. An action with `ok:false` is evidence the UI path failed.
3. **Friction & delight** — every entry MUST cite a specific screenshot path (from the batch file) or a named check/metric. No pointer → the entry does not exist. Severity: 1 cosmetic, 2 friction, 3 task-threatening, 4 caused abandonment.
4. **Trust probe** — score 1–5, list signals actually seen in the evidence, and signals this persona needed but did not find.
5. **Brand recall (memory test)** — answer AFTER finishing that theme's walk, WITHOUT re-opening screenshots: three words you'd use to describe the store; one sentence you'd tell a friend; which product you remember; what it cost. If you don't remember, write what you actually retain — vague or wrong recall is real data, do not look it up.
6. **Regression check (on the NEW theme only)** — every persona must actively hunt for one thing NEW does WORSE than OLD at the same step. Only after naming what was checked may a persona report "checked: none found". List what was compared in `or_checked`.

## The any-store test (mandatory quality bar)

Before writing any friction/delight/trust text, ask: could this sentence be pasted into a review of any random Shopify store without looking at the evidence? If yes, rewrite it with the specific element, page, and screenshot. Banned unless followed by a measured specific: "could be more prominent", "clean and modern", "build trust", "improve navigation", "enhance the user experience".

## Output format

Write TWO files (create them yourself):

**`theme-gauntlet/data/verdicts/batch-N.jsonl`** — one JSON object per line, 20 lines (10 personas × 2 themes), exactly this shape:

```json
{"persona_id":"P042","theme":"new","device":"mobile","five_second":{"sells":"","for_whom":"","adjectives":["","",""],"price_guess":"","feels_like":"brand|reseller|template"},"task":{"completed":true,"steps":7,"abandoned_at":null,"abandon_trigger":null,"hesitations":[{"step":"","evidence":"captures/...jpg","why":""}]},"friction":[{"step":"","evidence":"","what":"","severity":2}],"delight":[{"step":"","evidence":"","what":""}],"trust":{"score":3,"signals_seen":[],"signals_missing_that_mattered":[]},"brand_recall":{"three_words":[],"tell_a_friend_one_sentence":"","product_remembered":"","price_remembered":""},"would_return":false,"regression_check":{"found":"","or_checked":[]}}
```

Notes: `task.steps` = screenshots/actions consumed before completion or abandonment. `abandoned_at` = step label or null. `regression_check` only needs real content on the "new"-theme object (on "old" put `{"found":"n/a","or_checked":[]}`). Keep every `evidence` value a real path from your batch file. `task.completed` means the persona would have reached their goal (checkout page for buy intents, information found for support, etc.) within their patience budget.

**`theme-gauntlet/data/verdicts/batch-N-compare.jsonl`** — one line per persona (10 lines):

```json
{"persona_id":"P042","preferred_theme":"new|old|neither","reason":"ONE concrete evidenced reason with screenshot path","regression_on_new":"the single worst thing NEW does vs OLD, or 'none found after checking X,Y'"}
```

## Verified facts from live follow-up checks (use these to interpret ambiguous evidence)

These were verified against the live sites after the captures; evidence in `theme-gauntlet/captures/{old,new}/live/*.jpg` and `theme-gauntlet/captures/live-checks.json` (you may read those):

1. **Checkout is blocked on the NEW theme's preview URL by Shopify itself** ("Checkout isn't available in preview", `/checkout` → 403). If a NEW screenshot shows that page, the persona DID successfully reach checkout entry — the block is the preview platform, not the theme. Do not count it as friction or task failure.
2. **NEW search is genuinely broken as a UI path**: tapping SEARCH in the NEW header lands on `/search`, a page whose input field exists in markup but sits in a dialog that never displays — there is nothing to type into, and keystrokes do nothing (`captures/new/live/search-opened-mobile.jpg`). Results render only if a query is already in the URL. The results screenshots in NEW j2/j7 sessions were reached by URL fallback — a real shopper tapping SEARCH hits the dead page first. Treat this as real, severity-appropriate friction for search-led personas.
3. **NEW mobile menu works** and contains ACCOUNT → /account, Contact, TRACKING and all collections (`captures/new/live/menu-open-mobile.jpg`). The captured `open-menu`/contact `not-found-in-ui` action failures in NEW j6 were automation artifacts — but note ACCOUNT on NEW desktop is NOT visible in the header (only inside the MENU drawer), while OLD shows a person icon in the header at all times.
4. **NEW footer policy links work**: SHIPPING → shipping policy, REFUNDS → refund policy, CONTACT present (`captures/new/live/shipping-policy-mobile.jpg`). The `not-found-in-ui` results for NEW shipping/contact in j6 were automation artifacts.
5. **OLD has NO shipping/returns policy links anywhere in its UI** — its footer contains only collections, TRACKING, Contact, product links and Login (`captures/old/live/footer-desktop.jpg`, `captures/live-checks.json → old_footer_links`). The OLD j6 `not-found-in-ui` results for shipping/returns are REAL: those pages exist only by direct URL.
6. **NEW catalogue (/collections/all) has no sort or filter controls at all** — only category tabs (verified: zero sort/filter/price elements; `captures/new/live/collection-all-desktop.jpg`). OLD has a Filter button and sort. The `sort_by` URL in NEW j4 captures was injected by the capture tool, not reachable by a shopper.
7. OLD's header account icon exists; its click destination behaved inconsistently in testing (`captures/old/live/account-destination.jpg`) — treat where it leads as unverified rather than working or broken.

## Return value

Return a short JSON summary: `{"batch":N,"verdicts_written":20,"compares_written":10,"followups":[{"question":"","persona_ids":[],"page":"","theme":""}]}` — followups are moments where a persona needed something the captures cannot show (e.g. "would tapping SPECIFICATION open a size table?"). Max 3, only genuinely blocking ones.
