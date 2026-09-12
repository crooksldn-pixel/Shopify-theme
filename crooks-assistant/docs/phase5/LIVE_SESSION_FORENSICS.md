# Phase 5 — what actually happened on the tablet

Reconstructed from `ts-20260911-201129-phase-4-live-tablet-test.jsonl` (1,365 events) before any
code changed. Evidence priority as the brief sets it: **the raw timeline first, the owner's own
words second, the generated report fourth.** Where this document and the generated report
disagree, the report is wrong and the disagreement is stated.

No customer names and no email addresses appear here. Customer ids are truncated to their last
four digits where one is needed to prove two records are different.

The session is two sittings: **20:11–20:18** and **23:01–23:12**. 44 turns, 40 tool calls, zero
proposals — no change was attempted all evening, so nothing here is about the action engine.

---

## THE HEADLINE: the analyser misdiagnosed three of its own top findings

| The report said | What the timeline says |
|---|---|
| "A value had to be exact and a voice could not make it so" — **62 occurrences**, the #1 improvement candidate, component *"the precision-input path"* | 63 of those events are **ordinary taps on controls**, 39–140 ms, every one swallowed by the voice layer. Nothing to do with precision input. **D-1.** |
| `DUPLICATE_RENDER` on turn_be1b384ca420 — "the same customer card drawn 7 times" | Seven cards for **seven different customers** (ids …6343, …4807, …5015, …4055, …7975, …2855, …8887). Not a duplicate render: a list question answered with seven full profile pages. **D-4.** |
| `UNFULFILLED_ACTION` × 3, severity 5/5, component *"the write tools"* | All three are owner feedback being recorded successfully. The classifier matched on mutation words and ignored that `owner_feedback` had already handled it. **D-9.** |

Had this pass followed the proposals, it would have tuned speech recognition, de-duplicated a
renderer that was not duplicating, and gone looking for a missing write tool. All three are
dead ends.

---

## D-1 · P0 · The voice layer owned every touch on the idle screen

**What he said, 20:15:01, verbatim:**

> Uh, can you also log, I cannot click the merge or close button or any of the other buttons
> for the two blobs, um, because wherever I press just leads to you listening

**And 20:17:20:**

> Also log the current screen I'm on where the split button is actually rendering over the
> release to send button, and there's no actual way to click the split button

**Evidence.** 132 hold-starts in the session. **131 report `target: "dock"`. One reports
`orb`. No other target exists in the entire file** — the tablet has no record of a touch ever
reaching anything else, because nothing else ever got one.

106 holds ended `outcome: "sent"`, median 114 ms. **63 of them were under 200 ms**, in 19
bursts. The two biggest sit exactly where he was complaining:

```
20:14:48–20:14:50    8 taps   68, 46, 83, 68, 71, 94, 81, 67 ms
                              ↓ 11 seconds later
20:15:01             "I cannot click the merge or close button ... wherever I
                       press just leads to you listening"

23:08:31–23:08:41   26 taps   104, 88, 81, 118, 88, 82, 97, 92, 101, 89, 119, 89,
                              81, 39, 90, 118, 58, 79, 103, 55, 79, 96, 81, 115,
                              140, 114 ms
23:09:06–23:09:10    7 taps   87, 82, 70, 89, 68, 106, 56 ms
```

Twenty-six consecutive attempts to press something, in ten seconds, every one of them sent to
the speech recogniser as a recording.

**ROOT CAUSE — a CSS stacking context, and it is one line.**

```
web/style.css:65    --z-orb:1; --z-context:2; --z-talk:3; --z-chrome:4;
web/style.css:132   .orb-zone{ position:relative; z-index:var(--z-orb); ... }   /* 1 */
web/style.css:515   .talk{ position:absolute; z-index:var(--z-talk); ... }      /* 3 */
web/style.css:525   body[data-mode="orb"] .talk{ inset:0 }                      /* the whole screen */
web/index.html:68   <div id="branch-bar" ...>   ← INSIDE <section id="orb-zone"> (52–69)
```

`#branch-bar` — the Split / Merge / Close chips, his "two blobs" — is a child of `.orb-zone`,
which is a positioned element with `z-index: 1`. That makes it a **stacking context**: no
`z-index` on the branch bar or on any chip inside it can lift it above 1. `#talk` is a sibling
at `z-index: 3` and, in orb mode, `inset: 0` — a transparent button the size of the viewport.

So on the idle screen the voice target is painted, and hit-tested, **over every branch control
on the page**. `--z-chrome: 4` looks like it should save them; it cannot, because their parent
caps them.

**This exact bug class was found and fixed once already, one element away.** The comment above
`.bottom` at `web/style.css:474`:

> Orders from the idle screen landed on FOOTER.bottom and did nothing, which is what the owner
> reported: "why can't I click orders unless you're already thinking".

The footer was given `z-index: var(--z-chrome)` and `pointer-events` discipline. The branch bar,
twenty lines up the HTML, was left inside the orb's stacking context.

**Visible consequence.** Every tap on Split, Merge or Close starts a recording. 63 of them
in one evening. He reported it twice and hammered it 26 times.

**System consequence.** 63 junk recordings reached the speech pipeline, which dutifully
reported them as "too short", which the analyser dutifully reported as 62 precision-input
failures — and made speech the top improvement candidate in a session where speech was not the
problem. One HCI defect produced a false engineering priority.

**Fix.** §7/§8: an explicit touch-ownership state machine, and voice activation only from a
deliberate voice target that is never an ancestor of, and never painted over, an interactive
control. Not a bigger hit region with more exceptions.

**Regression test.** Physical-style pointer tests: tap Split, Merge, Close, Back, Home, Next, a
card, a chip, a field, a notification; scroll from a card and from beside the dock; two-finger
split; a real voice hold. **Zero ordinary control taps may emit a recording event.** Must fail
on the current tree.

---

## D-2 · P0 · A per-branch tab was applied to every card, so everything opened on Email

**What he said, 20:18:12, verbatim:**

> Uh, can you log that I'm not seeing any UI here except email where there's nothing? I want to
> also be seeing his orders and his history and like an email write box, and there's none of
> that here

The generated report read this as being about an `email_list` card. It is about something
sharper, and it is visible in the render telemetry.

**Evidence.** Every customer card in the session rendered with `tab_active: "Email"` — including
all seven cards of turn_be1b384ca420, freshly drawn for seven customers he had never opened:

```
{'type': 'customer', 'ref': '…6343', 'tabs': ['Overview','Orders','Email'], 'tab_active': 'Email', …}
{'type': 'customer', 'ref': '…4807', 'tabs': ['Overview','Orders','Email'], 'tab_active': 'Email', …}
… ×7, seven different customer ids, every one open on Email
```

The report's own count: the Email tab was **tapped twice** all session, and was the active tab
on **23** rendered cards.

**ROOT CAUSE.**

```
web/app.js:1692   tab: branchState && branchState.tab ? branchState.tab : '',
web/ui.js         tabs(panels, { initial: opts && opts.tab, … })
```

`renderOpts().tab` is a single value **per branch**, handed to every card that has tabs. He
tapped Email once, on one customer, early on. From that moment every customer card on that
branch — every entity, every turn — opened on Email. The Email panel was usually empty, so a
request for a customer's *orders and history* produced a card showing an empty inbox.

**Visible consequence.** He asked for orders and history and got an empty email panel, on a
card that did contain his orders and history one tab away. His words: *"there's none of that
here."* It was there; it was hidden by a tab the system had chosen for him.

**Fix.** Tab selection belongs to an **entity**, not to a branch. A freshly-drawn card for an
entity the owner has not opened starts on the tab the TASK implies (§3/§12: a request naming
orders opens Orders), never on the last tab tapped on a different record.

**Regression test.** Tap Email on customer A, then render customer B: B opens on its
task-appropriate tab, not Email. Seven fresh cards open on Overview, not on the tab a different
customer was left on.

---

## D-3 · P0 · Held facts never became a surface

**Turn `turn_1e7f630eae7e`** — *"Pull up the history of [name] and his orders. See how many
times he's ordered, see how much he's spent, and see if he's in Gmail anywhere."*

```
tools:   ['gmail_search']          ← the only NEW read
renders: [['email_list'], ['email_list']]
```

The spoken answer was correct and complete — two orders, sixty pounds each, £120 lifetime. The
Mac held all of it. The screen showed an email list, because the presentation layer drew the
most recent tool result and nothing else.

This is §3 exactly: `TOOL RETURNS X → DRAW X CARD`. The task was a customer workspace; the last
tool was Gmail; the screen became Gmail.

**Fix.** §3/§6: intent → workspace → data requirements → progressive hydration, over a canonical
entity. A new read ENRICHES the workspace it belongs to.

---

## D-4 · P1 · A list question answered with seven full profile pages

**Turn `turn_be1b384ca420`** — *"Has anyone bought today that has bought before, a returning
customer?"*

Answer, correctly: **one.** Rendered: **seven full customer cards**, 265 px each, one per
customer read, 1,949 px of deck. Seven `shopify_customer_history` calls to answer a one-line
question (§14's N+1).

The report filed this as DUPLICATE_RENDER. The seven ids are all different. The defect is that a
summary question was answered with entity profiles — §13.

---

## D-5 · P1 · "Can you expand his customer page?" became a capability summary

```
turn_0cce1678e014  "Can you expand [name]'s customer page?"
   → family: capability_summary
   → rendered: one 'capability' card, 1,014 px, tabs: The shop / The inbox / Sales and stock
turn_ddb733d15472  "Expand [name]'s customer page"      (said again, 87% the same words)
   → no tools, no cards at all
turn_9d59579ab03e  "No, bring up a UI for the customer's page"      ("No," — he is correcting it)
   → no tools, no cards at all
```

Three attempts at the same thing. The first produced a thousand-pixel list of what the system
can do; the next two produced nothing visible. §4 and §5: "can you" is not a capability
question when an entity and an operation follow it, and *expand / bring up / show* require a
visible workspace or the turn has not succeeded.

---

## D-6 · P1 · A control was offered with nothing behind it

`turn_dd093f86b92d`: `open.entity` posted, refused `not_held`; the half then drew `half_empty`.
The branch `br_c605ab3fdc` records the same refusal. §18: the control was drawn before its
destination was known to exist.

---

## D-7 · P2 · Home accepted eight times and arrived nowhere

```
20:12:41  home
20:15:17  home   home   home
20:15:20  home   home   home   home
```

Seven presses in four seconds, every one `ok=true` (report §14: `navigation.home` 8 posted, 8
accepted, 0 refused). Phase 4 rebuilt Home as a branch landing; this session shows the landing
being reached and the owner pressing again anyway, four times in three seconds. Either it did
not visibly arrive or it arrived somewhere he did not recognise. §16: navigation success is a
visible workspace, and this needs a replay fixture from this timeline rather than another
assertion about the HTTP code.

---

## D-8 · P2 · One tap, seven redraws

`turn_f0628fcf7be5` drew `order_list + working_set + folded` **seven times** — #2 through #7 at
0.0 s apart, one at 2.5 s. Nine of the twenty-one long-scroll surfaces in the session are this
one turn. Each redraw costs the scroll position, and he was scrolling: 26 scroll reports,
deepest 971 px.

---

## D-9 · P2 · The analyser punished the feature that worked

All eight owner-feedback events recorded correctly — the one unambiguous Phase 4 success of the
evening. Three of them are nonetheless filed `UNFULFILLED_ACTION` at severity 5/5, the report's
third-highest priority, because the classifier saw mutation words ("make a note", "log", "tag")
and did not check that `owner_feedback` had already answered. §20/§21: OWNER_FEEDBACK precedes
generic mutation matching.

---

## D-10 · P3 · Sixteen notifications, eleven of them empty

Sixteen `tablet_notify` events; eleven carry no text at all, and the five with text are
`divided`, `merged`, `divided`, `merged`, `divided` — state changes the screen itself shows. §10:
a state change updates the place the state lives; the orb visibly dividing is sufficient.

---

## What the timeline exonerates

Worth stating, so this pass does not fix what is not broken:

- **Speech.** 38 of 44 recordings transcribed, median 715 ms. Nine STT failures, of which the
  timeline attributes at least two to a gesture ending the recording. Once the 63 tap-recordings
  are removed there is no evidence of a speech-quality problem. §22 is correct to wait.
- **The tools.** 40 calls, **100% success on every one of nine tools.** No tool failed all
  evening.
- **The action engine.** Zero proposals, zero mutations, nothing staged. Untouched, and out of
  scope for this pass.
- **The read layer's correctness.** Context hydration never missed customer history, never
  missed email correlation, never left an order incomplete. It was SLOW (24,567 ms reading) but
  it was right.

The whole of this evening's failure is presentation and interaction. The engine underneath it
did its job.

---

# THE NINETY SECONDS THAT EXPLAIN THE PRODUCT

The generated report has this window as five `STT_ERROR` rows and one unrouted "other" request.
Reconstructed from the raw events it is the entire failure of the product in sequence.

```
23:07:41   RENDER []  mode=orb                ← the deck is EMPTY. Chrome only.

23:08:27   HE SAID: "What is it? What... There is just bullshit Yo, uh, what,
                     why is there bullshit on the screen right now?"

23:08:28   hold 4526 ms → sent                ← a PROPER four-and-a-half-second hold
23:08:28   hold  257 ms → sent
23:08:28   tablet_notify {}                    ← a notification with no words

23:08:30   IT ANSWERED: "Nothing's come from me — I haven't run anything yet,
                         no card's up on my end. What do you want me to..."

23:08:31   hold 104 88 81 118 88 82 97 92 ms   ← eight taps in ONE second
23:08:34   hold 101 89 ms
23:08:36   hold 119 89 81 39 90 118 ms
23:08:37   IT ANSWERED: "I could not hear that clearly — a bit closer to the microphone."
23:08:39   hold 1237 ms, then 58 79 103 55 79 96 81 115 ms
23:08:39   tablet_notify {}                    ← another with no words
23:08:41   hold 140 114 ms                     ← twenty-six taps, ten seconds
23:08:46   IT ANSWERED: "I could not hear that clearly — a bit closer to the microphone."
23:08:47   tablet_notify {}                    ← a third with no words

23:08:56   HE SAID: "What is, what is it doing? Oh"
23:08:58   IT ANSWERED: "Nothing running here, nothing pending on a card.
                         Just say the request when you're ready."
23:09:00   RENDER []  mode=orb                 ← still empty

23:09:04   tablet_notify {}                    ← a fourth
23:09:06   hold 87 82 70 ms
23:09:10   hold 89 68 106 56 ms                ← seven more

23:09:12   HE SAID: "Hi"                       ← checking whether it is alive at all
23:09:14   IT ANSWERED: "Hi. What do you need?"
```

Every answer in that sequence is **technically correct and completely useless.** No card WAS up.
Nothing WAS running. And he was looking at a screen he called bullshit, tapping it thirty-three
times, and being told to speak closer to the microphone.

Three defects fall out of this that appear nowhere in the generated report.

## D-11 · P0 · The assistant has no model of what is on the glass

Asked "why is there bullshit on the screen", it said **"no card's up on my end."** It was right
about cards and wrong about the screen. With the deck empty and the orb divided, what he was
looking at was chrome: the orb, the dock, two branch chips he could not press, and a
"hold to speak" label over all of it.

The assistant can enumerate the cards it sent. It cannot see the interface it is sitting in. So
when the owner asks about the screen, it answers about its own outbox. §19 and §23: it must know
its own UI — including that the screen can be *empty of cards and full of furniture*, which is
its own reportable state.

**Fix:** the UI-semantics manifest must answer "what is on this screen right now" from the
tablet's actual render state, chrome included. "Nothing is on screen" is only true if nothing
is on screen.

## D-12 · P1 · A complaint only counted if he said the word "log"

```
20:16:48  "Logical error here. You just pulled up two [name] screens for no reason"
              → NOT captured. Filed as an unrouted 'orders' request.
20:17:04  "Log your error there. You just pulled up two in the same UI"
              → captured.
```

He stated the defect plainly, was not recorded, and had to repeat it sixteen seconds later with
the magic word in front. The feedback family keys on "log / record / note / broken". A tester
saying *"logical error here, you just pulled up two screens for no reason"* is reporting a
defect by any human standard.

**Fix (§20):** recognise a defect report by its shape — a statement that the system did
something wrong — not only by an imperative to log it. Conservative enough not to swallow
ordinary conversation, and the test must include the negatives.

## D-13 · P1 · A legitimate 4.5-second hold produced no audio, inside a tap burst

At 23:08:28 he held for **4,526 ms** — a real, deliberate, properly-held question. The
transcript came back empty and the answer was "I could not hear that clearly." Two more real
holds in the same window (1,237 ms and 1,186 ms) went the same way.

The report attributes this to speech quality and makes STT its #2 improvement candidate. These
long holds sit *inside* the twenty-six-tap burst: his other finger was hitting the screen
throughout, each tap starting and ending a competing recording on the same element.

**This is gesture arbitration destroying real speech, not a recogniser failing to hear it.** It
is the strongest argument for §22's ordering: fix touch ownership first, because until then
every speech measurement is contaminated.

---

# THE ESCALATION, 20:14:02 → 20:14:35

§4 proving itself:

```
20:14:02  "Can you expand [name]'s customer page?"      → a 1,014 px capability card
20:14:09  "Expand [name]'s customer page"               → nothing visible        (7 s later)
20:14:22  "No, bring up a UI for the customer's page"    → nothing visible       (13 s later)
20:14:35  "Okay, can you make a note of what you just failed to do, please?"
```

Three attempts in twenty seconds. He drops the polite form, corrects it outright ("No,"), then
abandons the request and asks it to record its own failure. By the third attempt he is
**explicitly asking for a user interface** — *"bring up a UI"* — because the first two answered
him with speech.

A product does not get a clearer signal than a user escalating to the words "bring up a UI".

---

# THE TWO SITTINGS ARE DIFFERENT SESSIONS

Worth separating, because averaging them hides both.

**20:11–20:18, seven minutes.** Dense, competent, productive testing. Real business questions,
correct spoken answers, six defects found and reported. Every owner-feedback record comes from
here. This is a man using a tool.

**23:00–23:12, twelve minutes.** A large ambitious request that errored ("Something went wrong
while I was thinking") and was abandoned five seconds later — *"ignore all of that, ignore all
of that"*. Then: "Are you, are you working right now?" · fragments from swallowed taps ("I
actually like", "Broad", "White") · "Stop" · "why is there bullshit on the screen" · 33 taps ·
"what is it doing?" · "Hi" · "Crooks OS". Not one business question in twelve minutes.

The report's headline is "successful 24 · partial 6 · failed 14" over both. Sitting one earns
most of the successes; sitting two is a man who cannot tell whether the thing is alive. **The
second sitting is the one this pass has to answer**, and §42 is its standard: *the owner should
be able to hand the tablet to somebody with no explanation.*
