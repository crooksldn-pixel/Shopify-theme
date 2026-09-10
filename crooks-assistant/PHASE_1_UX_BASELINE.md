# Phase 1 UX baseline

What each surface is meant to do, in the owner's terms. This is the behaviour Phase 2 is
refining — not a style guide, and not a specification of how anything should look.

The tablet is a Galaxy Tab A 8.0 on a workbench, held in portrait, operated by someone with
their other hand full. Everything below follows from that: the answer is spoken so it can be
heard from across the room, and the screen is what you look at when you need the detail.

---

## The rule that governs all of them

**Speech and screen answer different questions.**

Spoken: what a person would say across a workshop. One or two sentences.
Screen: what you would hand them if they came over.

> "Order 1938 is £84 from Mia Jones and is currently unfulfilled. I've opened it."

and then the card, with the items, the address, the money, the customer's history and what can
be done next. The spoken answer never reads the card out, and the card is never a transcript of
the spoken answer.

A turn that answers in words and shows nothing is a failure, however good the words are and
however quickly they arrived. That is what was reported from the tablet, and it is what
`prose_only` exists to catch.

---

## Order detail — "Show me order 1938"

The main surface. Arrives on the fast lane with no model call.

**At once**: the number, the customer and their email, the status badges (unfulfilled / paid),
the timeline (placed → paid → to ship), the money, and the action rail.

**In tabs**, because 7,500 pixels of card against 655 pixels of screen is a scroll, not an
interface: Overview · Items · Shipping · Customer · Email. The selected tab is branch state, so
it survives a reload, a Back, and putting the half aside.

**Then, separately**: the customer's history and any related inbox threads. The order does not
wait for Gmail. Regions that are still coming say so.

**Actions**: what suits *this* order, decided on the Mac from the order's own state and what
the store has granted. An unfulfilled paid order offers Note, Fulfil, Address, Cancel, Refund —
and Refund is shown **disabled with the reason "nothing to refund"** rather than hidden. A rail
that only shows what is possible teaches nothing; one that shows what is not, and why, answers
the question before it is asked.

Nothing on the rail applies anything. A tap stages a proposal; a gesture commits it.

---

## Order list — "Show me today's orders"

Rows, not a paragraph. Compact enough that four or five fit without scrolling, each tappable.

The list **opens a working set**, which is what makes it navigable: "next", "the third one" and
a tap on the third row are then one cursor on one list. A list that is only a list leaves the
owner with nothing to walk.

Spoken: the shape of it, not its contents. "Three orders today; two still to go out." Seven
orders read aloud is a minute nobody listens to.

---

## Capability — "What can you do now?"

The question a new owner asks first and an experienced one asks after an update.

Grouped by the part of the shop it touches, with tabs per group, each entry saying what it is
and whether it could be done *right now*. Counts in the subtitle. When changes are switched
off it says so in one line, and lists no changes at all.

Spoken: one sentence. Thirty capabilities spoken is not a list — by the fourth the first is
gone.

The card and the sentence come from the same manifest, so they cannot disagree, and the
manifest is read when asked rather than at boot.

---

## Customer — "What else has this customer ordered?"

Who they are, how long they have been buying, what they have spent, and their recent orders
with enough of each to recognise it. Tabs: Overview · Orders · Email.

Reached by pronoun — "this customer", "she" — because the person is whoever the open record
belongs to. A question that *names* someone is a different question and takes a different path.

---

## Work queue — "Which customers need replying to?"

The threads waiting on us, with enough of each to decide without opening it: who, what about,
how long. An automated sender is never offered as a customer needing a reply.

This is a set, so it is walkable.

---

## Analytics — "How much have we sold today?"

Figures, with the period named and the completeness stated. When the read layer's coverage is
partial the card says so rather than presenting a partial total as a total.

---

## Navigation

**Back** is deterministic and free. It moves the branch's cursor and redraws the record it
lands on from what the Mac already holds — no model, no read, no reconstruction. At the end of
the trail it says so rather than inventing somewhere to go.

**Next / Previous** move one member of the open set and open it. At the ends they say "that is
the last one" / "that is the first one". A cursor that runs off the end and reports the last
member again is worse than one that stops, because the owner walking a queue of eleven has no
way to tell the eleventh from the end.

**Tabs** are state, not DOM. "Show me the shipping" and a tap on Shipping are the same
operation.

**Linked entities** carry their kind and their id on the card, so a tap opens the record
without asking the model to find it again.

Saying it and tapping it reach the same code. There is one implementation of each.

---

## Touch, then voice

Some controls want words rather than a decision. Tapping one binds what the words will apply
to, shows what it is listening for, and starts listening:

> tap **[Rewrite]** → "make it shorter and more apologetic"

rather than "rewrite Millie's draft to be shorter and more apologetic".

Three properties matter, and all three are about *not* applying:

- **It belongs to one half of the orb.** A binding armed on the left never catches a sentence
  spoken to the right.
- **It lasts one sentence.** Taken or abandoned, it is released.
- **It expires.** Two minutes — long enough to think of the sentence, short enough that a tap
  made and forgotten does not catch the next question.

And a sentence that is an instruction in its own right — "go back", "next", "what can you do" —
**releases the binding rather than being captured by it**. Tapping Note and then saying "go
back" abandons the note; it does not write "go back" into it.

---

## The split orb

Two halves, each with its own current record, set, workflow, cursor, navigation stack, tab,
expanded rows, voice binding and proposals. A half put aside works quietly and says "ready" on
its own chip rather than taking the screen.

Read caches are shared because they are immutable. Nothing else is.

---

## What never happens

- A change applied without the gesture on the card.
- A spoken "yes" authorising anything.
- A card claiming something was done that was not verified by reading it back.
- An action offered that the store has not granted — it is shown disabled, with the reason.
- The screen showing a value no tool returned.
- A question about a record answered with a paragraph and an empty screen.

---

*Baseline recorded at `f517877` on `claude/crooks-assistant-build-lgxlau` for Phase 1.
See `PHASE_1_HANDOFF.md` for the architecture, the scenarios and how to run them.*
