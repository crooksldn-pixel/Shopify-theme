# CROOKS OS — Phase 2 · Physical-tablet UX audit, interaction polish, Fable experience pass

Branch `claude/crooks-assistant-build-lgxlau`. Everything below was measured, not read: the
page in Chromium at the Galaxy Tab A 8.0's 800 × 1280, driven through its own `submit()`
and its own buttons, against the fixture world. Nothing was deployed and nothing was
written; the live read-only run refused itself for want of a credential (§10).

## Commits and final SHA

| # | SHA | Commit |
|---|---|---|
| 1 | `9608cf5` | Measure the tablet, then give five surfaces back their screen |
| 2 | `5174cb4` | A list becomes a way into its records, and the set chip stops lying |
| 3 | `181864a` | The email leg of the graph, which had no destination |
| 4 | `23ad3fb` | Back and Next stop fighting each other, and say where you are |
| 5 | `1fa4156` | The tablet tells the Mac what the next sentence is about |
| 6 | `f360aa3` | An email gets the rail the order always had |
| 7 | `d03e630` | The glass language, natively, and a dock in the band the thumb already rests in |
| 8 | `7ef14b6` | A read that failed is drawn as a read that failed |
| 9 | `e4e9c76` | This report |
| 10 | HEAD | This report, with the SHAs above filled in — the final SHA of Phase 2 |

**Last behavioural SHA: `7ef14b6`.** Phase 1 ended at `6a1b8e1`; `git log --oneline
6a1b8e1..HEAD` lists everything above, 22 files, +1,900 / −180 lines.

---

## 1. Verdict

Phase 1 built the right machinery and the tablet could not reach most of it. Every P0 the
audit found was a **control that existed on the Mac and had no caller on the glass**, or a
control that moved under the thumb. Nine P0s were confirmed by finger; eight are fixed and
gated by finger; one is named rather than half-built. The glass reference was rendered,
measured, and translated into a twelve-principle token system applied natively, with a dock
that costs the deck nothing — and with the reference's cost (66 blur layers, ~120 animations
running forever) deliberately not copied.

| Area (your priority order) | Before | After |
|---|---|---|
| 1 · Order detail | 254px of chrome before the card; tabs a hairline; five surfaces re-listing | 220px; lit tab pill; one composed card; a failed inbox read says so |
| 2 · Today's orders / lists | rows were pictures, not doors; the set chip lied | rows open records (`open.entity`); chip says `2 of 3` |
| 3 · Email + draft | no email could be opened offline; no Reply/Rewrite/Archive anywhere | threads open by tap; rail with Reply (arms the mic) and Archive (staged) |
| 4 · Linked navigation | nothing in the deck was tappable | order → prior order → customer chip, by finger only |
| 5 · Back / Next / tabs | Next slid 68px under the thumb; end of list killed Next for good; no position on screen | fixed slots; Back is the inverse of Next; `#1938. 2 of 3.` |
| 6 · Touch → voice | `voice.bind` posted 0 times from `web/`; 0 pixels changed on the card | bound, annotated, a band names the target, the chip lights, Cancel exists |
| 7 · Loading / action rails | a failed read drawn as "Checking the inbox…" forever | settles in words, tab marked |
| 8 · Density, scroll, hierarchy, touch | 5/8/4 targets under 44px; 4/3 tappables below the fold; 1.47 screens | 0 / 0 / 1.0 screens on every P0 surface |

---

## 2. What I found, ranked

Every finding was driven, not inferred. "Fixed" means fixed **and** covered by a check that
drives the page's own control.

### P0

| # | Finding | Evidence | Status |
|---|---|---|---|
| 1 | **Touch → voice was unreachable from the tablet.** Tapping Note set two labels and returned; `GET /branches` read `listening_for: null`; the tap fired zero requests; the sentence reached the model bare. Every test posted the bind through the harness, so every test was green. | `grep -c voice.bind web/*.js` → 0 | Fixed `1fa4156` — gate §9 |
| 2 | **No armed state on screen.** 9,961 px changed on the tap, 0 on the card, 0 on the chip; all 9,925 meaningful ones in a dock pill 788px (106mm) below the finger, wiped by "Release to send" the instant the thumb went down. | pixel diff | Fixed `1fa4156` — band above the deck, drawn from `branch.listening_for` |
| 3 | **Next and Back swapped places under the thumb.** Back was `hidden` until the first Next; the first tap made it appear and Next slid 68px (9.1mm). Two real taps at (158,176): forward, then *backward*. | touchscreen taps | Fixed `23ad3fb` — reserved slots, `disabled` at the ends; gate §8 |
| 4 | **Reaching the end of a list killed Next for good.** `at_end` is sticky; Next hid on it; Back posted `navigation.back`; `workflow.previous` had no caller in `web/`. Three Nexts, two Backs: standing on 1 of 3 with Next gone. | probe3 | Fixed `23ad3fb` — Back steps the cursor while a list is open |
| 5 | **The screen never said where you were.** `_member_words` returned "Priya Raman. 1 of 3."; goNext passed it to `pushContext` as a *label* and wrote `#answer` only on failure. Three orders, one stale sentence; in reverse it read "That is the last one." over member 1. | answerChanged=false ×3 | Fixed `23ad3fb` — answer written on success; set chip carries `2 of 3` |
| 6 | **An email thread had no controls.** `rail()` was called from `renderOrder` and nowhere else. Reply, Rewrite, Archive registered on the Mac, reachable by sentence only. | `grep -n "rail(" web/ui.js` → one call | Fixed `f360aa3` — Reply (`email.reply`, arms the mic) + Archive (staged row action); gate §10 |
| 7 | **"Which customers need replying to?" drew five cards and none said who.** A revenue ranking, a working set, a metric group, a table, a second working set — three titled "Recent customers". 1,886px. | before-needs-reply.png | Fixed `9608cf5` — one queue card, 1,070px |
| 8 | **Nothing in the deck was tappable, and the email leg was unreachable offline.** `open.entity` had no caller; fixture thread ids were not hex and `_ID_KIND` refused every one. | `grep open.entity web/app.js` → 0 | Fixed `5174cb4`, `181864a` — rows, prior orders, entity chips open records |
| 9 | **A failed inbox read was drawn as work in progress, forever.** "Checking the inbox…" byte-identical 34.8s later; with the tab closed, indistinguishable from an all-clear. | error/partial audit | Fixed (`7ef14b6`) — region settles in words with the sentence to retry; tab marked |
| 10 | **An email thread does not show the order it is about** (§10, "especially important"). The correlation runs order → threads; the reverse needs a read the presenter must not invent. | thread card text: no money, no status, no link | **Not fixed — named.** §9 |

### P1

| # | Finding | Status |
|---|---|---|
| 11 | Back at the floor was a live-looking button that did nothing; the list was not on the trail | Partly: Back greys at the true floor (`canGoBack`); the set chip returns to the list; the trail still does not hold the list |
| 12 | The nav rail ran 701px off the right edge with dead chips taking room, nothing saying more existed | Fixed: chips are live (`181864a`); the edge fades **only when the rail overflows** (`d03e630`) |
| 13 | The armed hint expired at 8s while the binding lived 120s | Fixed: the band follows the Mac's binding and its deadline |
| 14 | Refusals written to `#state-sub`, which is `display:none` in the only mode they can occur | Fixed: toast |
| 15 | The chip's words contained no note ("Add a note to order 1938" said back staged nothing) | Fixed by 1: the record is bound, the sentence is the note |
| 16 | Split orb: tapping the other half changes who is listening but not what you see; an aside half finishes in silence and its answer can never be read | **Not fixed — named.** §9 |
| 17 | A failed customer read printed "No customer on this order." under a header naming the customer | Not fixed — same shape as 9, the Mac must say *failed* not *empty* |
| 18 | Rewrite on the draft card | Not fixed: the draft surface carries no thread id to bind to |

### P2

| # | Finding | Status |
|---|---|---|
| 19 | Selected tab fill measured 1.02:1 against the card — selection carried by a 1px hairline | Fixed `d03e630`: fill + border + halo everywhere |
| 20 | Deck depth indicator saturates at 2 | Not fixed |
| 21 | A reload leaves the deck empty though the Mac holds the position and the tab | Not fixed — named |

---

## 3. What I changed

Eight behavioural commits, 21 files, and nothing in the foundations §2 protects: the fast
path, the typed presentation, the semantic commands, the action engine, branch isolation,
the order cache, the integrations, live-read-only, the harness and the assertions are as
Phase 1 left them. Two contracts were *extended*, neither rebuilt:

- `FastAnswer.drawn` — which of a recipe's reads become cards (`None` all, `[]` none). The
  reads still reach the turn log and the timeline; only presentation is narrowed.
- `commands.may_open(ctx, kind, ref)` — the permission question separated from cache
  presence, so `open.entity` can refuse before any read and read when the Mac lacks the
  record. (`replay()` used to return `[]` for both "not cached" and "not yours".)

| Commit | What |
|---|---|
| `9608cf5` | The measuring tape: `scripts/audit.py` + `scripts/browser/audit.js` (chrome, scroll, screens, tap-target size, below-fold, repeated text, bands, spoken chars). Five surfaces given back their screen: chrome 254 → 212, needs-reply 1,886 → 1,070px, customer 1.47 → 1.0 screens. |
| `5174cb4` | Rows open records; the set chip follows `branch.workflow`; the order head restructured. |
| `181864a` | Fixture ids made hex so the gate accepts them; `_open_waiting_threads`; prior orders and entity chips live. |
| `23ad3fb` | Back/Next: reserved slots, one cursor, spoken position; gate §8. |
| `1fa4156` | Touch → voice: `family` on `AvailableAction`, `voice.bind` from `primeAction`, the armed band from the branch, Cancel; gate §9. |
| `f360aa3` | The email rail: `available_email_actions`, `rail()` learns "stage" mode; gate §10. |
| `d03e630` | The glass language as tokens, tactile states, the dock; audit gains blur/animation/frame probes and both device classes. |
| `7ef14b6` | A read that failed is drawn as a read that failed. |

---

## 4. Experience results

Fixture world, `python scripts/experience.py --ui`, 15/15 scenarios, 99/99 checks, plus 40
browser checks driven by finger. **Card** is the Mac's own time to a drawable answer; **round
trip** adds ASGI transport. No run calls `/speak`.

| Scenario | Result | First useful UI (card) | Round trip | Surface | Interaction observed |
|---|---|---|---|---|---|
| What can you do now? | PASS | 3 ms | 22 ms | capability | six chips, each a sentence, each posts `/turn` |
| Show me order 1938 | PASS | 7 ms | 10 ms | order + attention | head: number, who, money, state in the first second; rail of 5 |
| Show me 1938 again | PASS | 2–3 ms | 4–6 ms | order | served from the order cache |
| Show me today's orders | PASS | 4 ms | 7 ms | order_list + set strip | rows tappable, chevron, 44px+ |
| Next, said and tapped | PASS | 1–3 ms | 4–36 ms | order | same pixel twice → 1 of 3, 2 of 3; Next greys at 3 of 3 in its slot; Back brings it back |
| Back, more than once | PASS | 1–4 ms | 2–8 ms | order | Back is the inverse of Next in a list, the trail otherwise |
| Shipping, said and tapped | PASS | — | 2 ms | tab | `surface.tab` on the Mac; the tab survives Back |
| Read me the full shipping address | PASS | 2 ms | 6 ms | order (shipping) | |
| What else has this customer ordered? | PASS | 3 ms | 6 ms | customer | one card, 1.0 screens (was 1.47) |
| Which customers need replying to? | PASS | 6 ms | 9 ms | email_list (work queue) | one card naming who and how long; row opens the thread |
| Did any of these customers email their house number? | PASS | — (model) | — | — | NORMAL lane, one model call, stays on the queue |
| From the order to the customer | PASS | 1–3 ms | 2–5 ms | order → customer | `open.entity` by row, prior order, chip |
| Add a hoodie to this order | PASS | — (model) | — | — | refused honestly, nothing staged |
| Two halves, two records | PASS | 3 ms | 5 ms | order | the Mac keeps the halves apart — the tablet does not show it (§9) |
| The card first, the inbox after | PASS | 4 ms | 7 ms | order, then enrichment | the inbox lands after; a failed inbox now settles in words |

Finger-driven gate (40 checks): thumb-swap, end-of-list, position; bind, band, chip, thumb-
down persistence, cancel; thread open, rail, target size; plus the 22 Phase 1 checks. Full
list: `python scripts/experience.py --ui`.

---

## 5. Screenshots

All under `reports/` (generated; not committed — the commands in §13 recreate them).

| Pair | Before | After |
|---|---|---|
| Order detail | `reports/audit/before/before-order-detail.png` | `reports/audit/after-glass/after-glass-order-detail-full.png` |
| Today's orders | `reports/audit/before/before-order-list.png` | `reports/audit/after-glass/after-glass-order-list.png` |
| Needs reply (5 cards → 1) | `reports/audit/before/before-needs-reply.png` | `reports/audit/after-glass/after-glass-needs-reply.png` |
| Customer | `reports/audit/before/before-customer.png` | `reports/audit/after-glass/after-glass-customer.png` |
| Orb screen + dock | `reports/audit/before/before-capability.png` | `reports/audit/after-glass/after-glass-home.png` |
| List walk (same pixel twice) | — | `reports/experience/run-*/screenshots/05-list-walk.png` |
| Touch → voice armed | — | `reports/experience/run-*/screenshots/06-armed.png` |
| Email thread with rail | — | `reports/experience/run-*/screenshots/07-email-thread.png` |
| Side by side, reference vs CROOKS | `reports/audit/compare/reference-vs-crooks-order.png`, `…-tablet.png` | |
| Side by side, CROOKS before/after | `reports/audit/compare/crooks-before-after-order.png`, `…-home.png` | |
| The reference itself | `reports/audit/reference/ref-{desktop,tablet}-{rest,dock-hover,card-hover,sidebar-open}.png`, `ref-styles.json` | |

---

## 6. Voice + touch equivalence

Confirmed by the scenarios `next_previous`, `back`, `tabs`, `linked_entities` and by the
gate: every touch control posts the **same command or the same sentence** the voice reaches,
and the branch replies with the state that decides what is lit.

| Touch | Posts | Voice equivalent |
|---|---|---|
| Next / Back chips | `workflow.next` / `workflow.previous` (in a list), `navigation.back` (otherwise) | "next" / "back" |
| A row, a prior order, an entity chip | `open.entity {kind, ref}` | "open the third one" |
| A tab | `surface.tab` | "shipping" |
| Note / Address / Reply chip | `voice.bind {family, kind, ref}` — the *next sentence* is the instruction | (the sentence itself, addressed by the binding) |
| Archive chip | `/actions/row {action, ref}` — the Mac prepares; a gesture applies | "archive this" |
| Dock: Orders / Inbox / Sales / Products | `/turn` with "show me today's orders" etc. | the same words |

The lit dock icon and the `2 of 3` on the chip come from the branch the Mac returns, never
from the tap.

---

## 7. Tablet findings (800 × 1280, DPR 1 — 1 CSS px = 0.134 mm)

| Metric | Phase 1 end | After P0 fixes | After glass pass |
|---|---|---|---|
| Chrome before the first card | 254px | 212px | **220px** (a real container for the nav costs 8px) |
| Needs-reply deck height | 1,886px (5 cards) | 1,070px (1 card) | 1,062px |
| Customer deck | 1,516px / 1.47 screens | 1,070 / 1.0 | 1,062 / 1.0 |
| Tap targets under 44px (order / list / customer) | 5 / 8 / 4 | 0 / 0 / 0 | 0 / 0 / 0 |
| Tappables below the fold | 4 / 3 | 0 | 0 |
| Anything scrolling sideways | no | no | no |
| Next's x while walking a list | 129 → 197 → 129 | 197 / 197 / 197 | 197 / 197 / 197 |
| Live backdrop-filter layers | 1 (sheet) | 1 | **2** full design · **0** lite (the Tab A is lite) |
| Elements animating forever | 0 | 0 | 1 · 0 |
| Frame time, scroll + tab switch (Chromium) | — | — | mean 16.7ms, p95 16.8, 0 over 32ms, both classes |

The frame numbers are a workstation's Chromium at vsync; they cannot show a GPU cost below
one frame. What they do show is that the glass pass added no frame over 32ms in either
class. `?lite=0|1` forces the class so both can be measured on the tablet itself.

---

## 8. The reference (§7)

`crooksldn-pixel/glass-sidebar-crooksos-tocopy` — the whole design is inline Tailwind in
`src/pages/Champions.jsx`. It was **built and rendered** through an untracked harness (the
Base44 `AuthProvider` would otherwise block on a login), driven at 1280 × 800 and 800 × 1280,
hovered and tapped, and its **computed** styles read off the DOM (`ref-styles.json`).

Measured: dock 92 × 409, fill `.10`, `blur(64px)`, border `.20`, radius 24, shadow
`0 25px 50px -12px rgba(0,0,0,.25)`, 500ms; selected button fill `.15` + border `.30` +
halo `0 0 20px rgba(255,255,255,.4)`; idle button transparent; hover fill `.20` and scale
1.10 at 300ms on `cubic-bezier(.4,0,.2,1)`; cards fill `.10` → `.15` and border `.20` →
`.39` on hover; controls blur 24 / radius 16. One surprise: `bg-white/8` is not a Tailwind
opacity step, so the "8%" panels compute to **transparent** — their look is the 64px blur over
the gradient plus the 1px border and the shadow. Cost on one page: **66 backdrop-filter
layers, ~120 elements animating forever** (80 `pulse-stagger`, 16 `stagger-in`, 8 `bounce-
soft`, 8 atmosphere drifts). On the tablet layout the sidebar overlays the grid and the header
text collides with the sidebar's ("Champions / Discover your next main" under "RIOT GAMES").

### The twelve principles taken

1. **Two blur tiers, not five** — 24px controls, 64px panels. CROOKS: 18 / 26, on two elements.
2. **One white, one fill ladder** — 0 / .05 / .10 / .15 / .20; every state is a step. CROOKS: .05 / .075 / .12 / .16 (half, on a near-black warm ground; the ratio is what was borrowed).
3. **A border ladder** — .10 dividers, .20 rest, .30 selected, .40 strongest. CROOKS: .10 / .18 / .34.
4. **Selected = fill + border + halo, all three.** Applied to tabs, chips, branch chips, dock, the draft card, the open row.
5. **Idle controls sit transparent inside a glass container**; the container carries the glass. Applied to the nav rail and the dock.
6. **Press = scale + one fill step, together**, 120ms. Applied everywhere a finger lands.
7. **Radius pairs with layer** — 24 panels, 16 controls. CROOKS: 20 / 14, nested tiles a step lighter.
8. **One floating shadow** for anything over the atmosphere, deepening when lit.
9. **An atmosphere beneath, not black** — a diagonal with large soft glows. CROOKS: two *static* glows, warm top-left, cool bottom-right.
10. **Staggered entrances** say the layering order. CROOKS: cards 50ms apart, the band from above, the panel on a tab switch.
11. **The selected thing breathes** — one continuous animation, on one element. CROOKS: the armed dot, only while armed.
12. **An opacity ladder for type** — 1 / .9 / .6 / .5. CROOKS already had it (`--ink` … `--ink-4`).

### Not taken, deliberately

Hover as the carrier of state (touch-first: everything reads without it); the purple
gradient and Inter (CROOKS's identity is warm ink on near-black); the desktop sidebar; the
eight drifting glows; `pulse-stagger` on 80 dots; blur on every card. Nothing from the
reference runs at runtime and nothing depends on it.

### §7E — the dock decision

| Option | Width cost at 800px | Height cost | Verdict |
|---|---|---|---|
| A · compact left column (as the reference) | 64–92px = 8–12% of every screen, forever | 0 | rejected: the deck is the product |
| B · collapsible rail | 0 collapsed, then a gesture to open | 0 | rejected: a second gesture before every area |
| C · contextual dock | 0 | 0 | already what the rail (`Assistant / Back / Next / set / entities`) is |
| **D · hybrid** — persistent areas in the band the thumb rests in, contextual actions on the surface | **0** | **0** (the 112px hold band already existed) | **chosen** |

Four areas — Orders, Inbox, Sales, Products — each a sentence the fast lane answers
(`order_list_period`, `inbox_state`, `sales_breakdown_period`, `best_sellers_period`, all
verified FAST). Customers is not on the dock: "who are my best customers?" goes to the model
and draws no card, so a tap would be slow and empty — a customers recipe is a Phase 3 item.
Measured: the four land and light; the lit one follows the record (Home lights what it lands
on; the orb screen lights nothing); no icon overlaps the pill; all 64 × 56; the deck clears
the band.

### §7I / §7J — readability and cost

Text on glass: ink `#ebe8e0` on the card ground measures 15.1:1; `--ink-3` metadata 4.3:1;
the warn line 4.29:1. Selected states are three signals, not one. Blur is on two elements in
the full design and none on a lite device, which the Tab A is (`hardwareConcurrency ≤ 4`).
Animations that run forever: one, only while the microphone is armed. Cards use gradients and
borders for their glass, as the stylesheet's header has always required.

### §7M — does each surface belong in the same family?

| Surface | Before | After | Why |
|---|---|---|---|
| Nav rail | no — outlined words on black | yes | glass container, lit spot, edge fade on overflow |
| Order detail | partly — flat, hairline tab | yes | one floating panel, nested tiles a step lighter, lit tab pill, rail with tactile press |
| Order list | no — table rows | yes | rows raise on press, the open one lifts, chevrons |
| Email queue / thread | no — no controls | yes | same rail, same press |
| Draft | — | yes | the active object: strong border and halo |
| Dock | did not exist | yes | the reference's dock, laid along the bottom |
| Orb screen | yes | yes | untouched but for the dock and the atmosphere |

---

## 9. Remaining limitations (ranked)

1. **The linked order on an email thread** (P0, §10). The thread card shows the words and
   hides the order. The honest shape is a second wave on an `email_thread` recipe that reads
   the correlation order → threads in reverse and carries `linked_order = {number, total,
   fulfillment, order_id}` on the surface; the tablet then draws one tappable strip. Not
   half-built because the presenter must not invent a read.
2. **Split orb on the tablet** (P0 in its area, P1 in §19). The Mac keeps two halves; the
   tablet has one deck, one answer line. Tapping the other half changes who is listening and
   nothing visible; a half put aside finishes in silence and its answer is unreachable.
   Proposed: `/branches/{id}/focus` replies with `ui` (a `replay()` of the branch's entity,
   exactly as `/command` does), and "ready" on a chip draws the result on tap.
3. **The Mac does not distinguish "failed" from "pending"** on `/context/order`. The tablet
   settles on its own clock (`7ef14b6`). A `failed: [...]` field beside `pending` would let it
   settle the moment the Mac knows, and would fix P1 #17 ("No customer on this order.").
4. **Rewrite** needs the draft surface to carry the thread it replies to.
5. **A reload leaves the deck empty** although the branch holds the record, the tab and the
   cursor. One `navigation.home`-shaped call at boot would redraw it.
6. **The list is not on the trail**: Back from member 1 says there is nowhere further back
   while the list is one chip away. The set chip is the way back today.
7. **Customers has no instant landing** and so no dock icon.
8. Deck depth saturates at 2. Frame timing was measured on a workstation, not the Tab A.

---

## 10. Exact final test counts

| Suite | Command | Result |
|---|---|---|
| Offline suite | `make test` | **1407 passed, 2 deselected** (the deselected two are `live`) |
| Golden scenarios + browser | `python scripts/experience.py --ui` | **15/15 scenarios, 99/99 checks, 40/40 browser checks**, 7 screenshots |
| Browser gate alone | `pytest tests/test_browser.py` | 1 passed (40 checks inside) |
| Renderer (Node) | `node --test tests/web/ui.test.js` | **66 passed** |
| Service worker / telemetry (Node) | `node --test tests/web/sw.test.js tests/web/telemetry.test.js` | 12 + 6 passed |
| Source checks | `pytest tests/test_web.py` | 58 passed |
| Lint | `ruff check app config scripts tests` | clean |
| Live read-only | `python scripts/experience.py --live` | **refused, exit 2**: "no Shopify credential in the Keychain (make secrets)" — the correct outcome on this machine |

---

## 11. Safety

- **No deploy.** Nothing was started, installed or pushed to the Mac or the tablet.
- **No writes, no production mutation.** Every run was the fixture world. The one live
  invocation refused itself before opening a client.
- **Live-read-only enforcement untouched** (`app/readonly.py`); `_ID_KIND` untouched — the
  fixture was changed to satisfy it, not the other way round.
- **Branch isolation held under attack**: the Phase 1 test that a record is replayed only to
  the conversation it was shown to passed throughout; `may_open` refuses *before* any read.
- **The tablet still posts names and references only**: `voice.bind` carries a family and a
  ref; a dock icon carries a sentence; a staged chip carries an action id and a ref. The
  source check that no argument of a change ever leaves the tablet still passes.
- **Nothing from the reference repository runs at runtime.** Its clone and harness live
  outside this repository.

---

## 12. Commits and final SHA

Listed at the top of this file.

---

## 13. Commands to run after review

Read-only. No deploy, no writes, no live credential needed for any but the last.

```sh
git fetch origin claude/crooks-assistant-build-lgxlau
git checkout claude/crooks-assistant-build-lgxlau
cd crooks-assistant

make venv                                   # once
make test                                   # 1407 passed, 2 deselected
node --test tests/web/ui.test.js tests/web/sw.test.js tests/web/telemetry.test.js
python scripts/experience.py --ui           # 15/15, 40 browser checks, screenshots under reports/experience/
python scripts/audit.py --label review      # the tablet measured: chrome, scroll, targets, blur, frames
python scripts/audit.py --compare           # against the previous run

# On the Mac only, with the Keychain populated — reads, never writes:
python scripts/experience.py --live
```
