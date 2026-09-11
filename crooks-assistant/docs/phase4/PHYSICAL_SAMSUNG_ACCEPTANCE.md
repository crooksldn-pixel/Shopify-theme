# Physical acceptance on the Samsung — Phase 4

**17–27 minutes.** This is not a tour of every feature. It is the highest-risk flows and the
things the last live session got wrong, in the order that would be most embarrassing to have
got wrong again.

Before you start: `make watch` in a Terminal window on the Mac. Every line below that says
*watch shows* is something you should see there while you do it. If you would rather not look
at a Terminal at all, the Control app's status view is the same information.

Say `start test session` (or `make test-session-start NAME="phase 4 acceptance"`) first, so
that everything you say about defects is recorded — see step 9, which is the point.

---

## 1 · The button that lied (3 min) — D-1

The defect: a send that had already gone out left the button saying "Applying…" for ever, and
when you asked, the assistant told you it was just the screen.

1. Open an email thread with a customer waiting.
2. Tap **Reply**, dictate or type a short reply, and approve it.
3. **Watch the button.** The moment the Mac proves the send, it must stop spinning and say it
   is done. Not "Applying…". Not a spinner that fades.
4. **Undo must appear as its own control** — and must NOT make anything say a change is still
   waiting.
5. Ask: *"has that sent?"* The answer must agree with the button.

**Fail if:** any spinner survives the confirmation, or Undo makes something look unfinished.

## 2 · Split, for real (4 min) — D-3

The defect: *"it just shows two of the same thing"*, and six taps between halves found no
difference.

1. Tap the visible **Split** control (not the gesture — that is step 8).
2. Ask the LEFT half: *"show yesterday's orders"*.
3. Tap the RIGHT half. Ask it: *"which customers need replying to?"*
4. Tap between the two halves three times.
   - Each half must show **its own** workspace, and the header must say which is which.
   - They must not be two copies of one thing.
5. While one half is still working, look at the selector: it should say so, and say **READY**
   when it finishes — without throwing anything over the half you are reading.
6. Open the finished half. Its result must be there.
7. Merge. What it says about changes still waiting must be true — an Undo you have not used
   is an offer, not a change waiting — and it must appear **above the cards, in its own
   space**, never floating over the half you are reading.

**Fail if:** the two halves are indistinguishable, or tapping a half redraws nothing.

## 3 · Back, Home, Next (3 min) — D-10

The defect: you pressed Home eight times and Back four times in twenty-two seconds, every one
returned success, and you never got where you were going.

1. Dock → **Orders**. Open an order. Open its **Customer**. Open one of their earlier orders.
2. **Back** → must return to the Customer tab **on the first order**.
3. **Back** again → must return to the Orders list, near where you were.
4. **Home** → must go to the branch landing. **Not** the last email thread you looked at.
5. Open a list of several orders. **Next** three times — it must walk the list and show a
   position ("3 of 10"). It must not behave like Back.

**Fail if:** Home replays an entity, or Back and Next feel like the same thing.

## 4 · Something useful, quickly (2 min) — D-5

The defect: a compound question showed nothing for 7,975 ms, then dumped everything.

1. Ask: *"Look up today's orders and today's emails and see if anything correlates."*
2. Watch the screen, not the clock. A shell should appear almost at once, then facts filling
   in — orders, then inbox, then correlations.
3. While it fills: **scroll**. The page must not jump, and nothing must move under your thumb.

**Fail if:** you stare at nothing and then everything arrives at once.

## 5 · The first screenful (2 min) — D-12

At 601 × 889 the first viewport must answer three questions without scrolling: what am I
looking at, what matters, what can I do.

1. Open an order. Judge the first screen against those three.
2. Open an email thread. Same.
3. Open an order list. Same.

**Fail if:** you must scroll past 1,500 px of anything to find the thing you came for.

## 5b · The bottom of the deck (1 min) — D-12, and the worst thing this pass found

The defect nobody reported because it reads as the tablet ignoring you: the cards were drawn
and scrolled **through** the dock band at the bottom of the screen, so any control that came
to rest in the bottom 112 px was untouchable — the invisible speech target took the tap
instead. It hit nine of fifteen stress screens at your tablet's size.

1. Open a long card — an order with many items, or a thread with several messages.
2. Scroll until a **button** (an Apply, a chip, a "more" control) is sitting in the bottom
   inch of the screen, just above the dock.
3. **Tap it.** It must do its own job.

**Fail if:** the tap starts a recording, or nothing happens at all. That is the bug, and it is
the likeliest explanation for anything in the last session that felt like "it just would not
let me press things".

## 6 · Typing, when the voice is wrong (2 min) — D-9

The defect: you tried to ask how to type and were not understood; four recordings were too
short to use.

1. Open a composer or any card with a field.
2. **Find the typing path without being told where it is.** That is the test.
3. Type an email address. It must validate, keep focus, stay above the keyboard, and not start
   a recording.
4. While typing, let a background enrichment land. Your text must survive it.
5. Ask: *"how do I type instead of speaking?"* — you must get a real answer (step 7).

## 7 · Does it know its own screen? (1 min) — D-6

The defect: *"What does the split button do?"* → *"I don't know what that button is… check with
whoever built the tablet screen."*

Ask all five:
- *"What does Split do?"*
- *"How do I go back?"*
- *"How do I type instead of speaking?"*
- *"What does Applying mean?"*
- *"How do I return to this order?"*

**Fail if:** it disclaims its own interface, or invents a control that does not exist.

## 8 · Gestures (1 min)

1. Hold the dock and speak — normal.
2. Two fingers on the orb, spread. It must divide and must **not** submit an empty speech turn.
3. Pinch to merge.
4. Scroll a long card with one finger — no recording starts.

**Fail if:** any gesture produces "I could not hear that clearly."

## 9 · Tell it what is broken (2 min) — D-7

The defect: you said *"please log that your split function is broken"* twice, and were told
twice there was no tool for it. None of it reached the report.

1. With the test session running, say: *"log that [whatever you just found] is broken."*
2. It must confirm it recorded it — not offer to send an email, not ask for approval.
3. Do it again for anything else you noticed.
4. Stop the session and generate the report.
5. **Your words must be in it, verbatim, under OWNER-REPORTED DEFECTS.**

**Fail if:** you have to remember your own findings after the session.

## 10 · The order that cannot be edited (1 min)

`write_order_edits` is not granted. Ask to add an item to an order.

**It must say exactly that** — the scope, and that it is a permission to grant — and must not
offer an Add flow that cannot work.

---

## What to write down

For each step: **pass**, or what you saw. If anything is wrong, say it out loud during the
session (step 9) rather than writing it here — that is what the recorder is now for, and
whether it captures you is itself part of the test.

## What this does not cover

Real Shopify writes beyond the email flow, the Control app on the Mac, and anything needing a
scope that is not granted. Those are in the report's known-limitations section.
