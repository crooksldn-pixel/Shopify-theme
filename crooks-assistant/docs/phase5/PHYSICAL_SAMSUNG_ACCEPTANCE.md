# Physical acceptance on the Samsung — Phase 5

**20–30 minutes.** Phase 4's script tested whether things *worked*. This one tests whether the
product **feels finished**, because that is what the pass was for. Several steps ask you a
question about how it felt rather than whether a value was right; those answers matter as much
as the pass/fail ones.

Before you start: `make watch` in a Terminal on the Mac, and say `start test session` so that
anything you say out loud is recorded. **Say defects out loud as you hit them** — you should not
need the word "log" any more (step 9 tests exactly that).

One instruction that applies throughout: **do not be careful with it.** Tap the wrong things.
Tap twice. Tap while it is talking. Put two fingers down. Phase 4 was tested carefully and
passed; you tested it normally, fourteen hours later, and it fell over.

---

## 1 · The one that ruined the last session (3 min) — D-1

Last time: 63 of your taps became recordings. You said *"wherever I press just leads to you
listening"*, and later *"the split button is actually rendering over the release to send
button"*.

1. From the **idle screen** (no cards), tap **Split**. It must divide. It must NOT start
   listening.
2. Tap the **left** chip, then the **right** chip, then the left again. Each tap must switch
   halves and must NOT start listening.
3. Tap **Merge**. Then split again and tap **Close**. Neither may start listening.
4. Now do it badly: tap Split **five times fast**. Then tap a chip while it is speaking. Then
   put **two fingers** on the orb.
5. Now hold the voice target properly and ask something real: *"how many orders today?"* It must
   record and answer.

**FAIL IF:** any tap in 1–4 produces "I could not hear that clearly", "that was too short", or a
turn you did not ask for. The bar is **zero**, not "better".

**Feel check:** did you ever have to think about *where* to tap to avoid the microphone?

## 2 · The bottom inch (1 min) — carried over from Phase 4

1. Open a long card. Scroll until a button sits in the bottom inch, just above the dock.
2. Tap it.

**FAIL IF:** the tap starts a recording or does nothing.

## 3 · A customer, properly (4 min) — D-2, D-3

Last time: you asked for a customer's orders and history and got an empty email panel, three
times, and finally said *"bring up a UI for the customer's page"*.

1. Say: *"pull up [a real customer]'s history and his orders — how many times has he ordered,
   how much has he spent, and is he in Gmail anywhere?"*
2. A **customer workspace** must appear. On the **first screen**, without scrolling, you should
   see: who he is, whether he is returning, lifetime spend, order count, last order.
3. His **orders** must be visible or one obvious tap away — and the card must NOT open on an
   empty Email tab.
4. Watch the Inbox section fill in when Gmail answers. If he has no email, it must say
   *"no messages found"* **and the rest of the workspace must still be there**.
5. Now tap **Email** on this customer. Then ask for a **different** customer.

**FAIL IF:** the second customer opens on Email. That is last session's defect exactly.

**Feel check:** did the first screen answer what you asked, or did you have to hunt?

## 4 · Ask it three different ways (2 min) — D-5, §4, §5

All three must open the customer workspace. None may answer with a list of capabilities, and
none may answer with speech alone.

1. *"Can you expand [customer]'s customer page?"*
2. *"Show me [customer]'s orders"*
3. *"Bring up a UI for the customer's page"*

Then, for contrast, ask: *"Can you access refunds?"* — **this** one should talk about
capability, because it is genuinely a capability question.

**FAIL IF:** any of 1–3 produces a capability card, or speaks without showing.

## 5 · A list question gets a list answer (2 min) — D-4

Last time: *"has anyone bought today that has bought before?"* answered "one" and drew **seven
full customer pages**, 1,949 px of scrolling.

1. Ask: *"has anyone bought today who has bought before?"*
2. You must get a **compact summary** — a count and a row or two, not a stack of profiles.
3. Tap a row. **Now** you get the full customer workspace.

**Feel check:** did the answer fit on the screen?

## 6 · Something useful, quickly (2 min) — §15

1. Ask: *"have a look at today's orders and today's emails and see if anything correlates."*
2. Watch the screen, not the clock. You should immediately see a workspace **with a name on it**
   and its sections marked as loading — then each one filling in.
3. While it fills: **scroll**. Nothing may jump, and nothing may move under your thumb.

**FAIL IF:** you stare at an empty screen and then everything lands at once. Last time this took
11 seconds and drew a 1,393 px card.

## 7 · The empty screen (2 min) — D-11

Last time, with nothing on screen, you asked why there was "bullshit on the screen" and it told
you *"no card's up on my end"* — while you were looking at it.

1. Get to an empty screen (Home, or after a Stop).
2. Ask: *"what is on this screen?"*
3. Ask: *"what is this?"*

**FAIL IF:** it claims nothing is on screen while you are looking at the orb, the dock and the
branch chips. It should be able to tell you what is actually in front of you.

## 8 · Quiet (2 min) — D-10, §10

Last time: 16 notifications, **11 of them with no text at all**.

1. Split. Merge. Open an order. Change a tab. Save a draft.
2. Count the floating messages.

**FAIL IF:** anything floats to tell you something the screen already shows — "divided",
"merged", "opened" — or a message appears with no words in it.

**Feel check:** did it ever interrupt you to say something you already knew?

## 9 · Say it is broken, without saying "log" (2 min) — D-12

Last time you said *"Logical error here, you just pulled up two screens for no reason"* and it
was **not recorded**. You had to repeat it sixteen seconds later starting with "log".

1. Find something you do not like. Say it **plainly**, as you would to a person:
   *"that's wrong, it's showing me two of the same thing"*.
2. It must confirm it recorded that — without you using the word log, record or note.
3. Then say something conversational that is **not** a defect: *"that's quite good actually"*.
   That must NOT be filed as a defect.
4. Stop the session, generate the report, and check your words are in it verbatim.

## 10 · Back, Home, Next (2 min) — D-7

1. Orders → an order → its Customer → one of their earlier orders.
2. **Back** → the Customer tab on the first order. **Back** again → the Orders list, near where
   you were.
3. **Home** → the branch landing. Press **Home again**. And again.
4. Open a list. **Next** three times — it must walk and show "3 of 10".

**FAIL IF:** you press Home twice because the first press did not visibly land. Last session you
pressed it seven times in four seconds.

## 11 · Long and ugly (1 min) — §9

Find, or ask for, a customer with a long name and a long address.

**FAIL IF:** anything overlaps, anything is clipped, or any control is under anything else.

## 12 · The subjective pass (3 min) — §31, §42

Put the tablet down, pick it up, and use it for two minutes as though you had never seen it.

- Does this feel **obvious**?
- Does anything look visually **sloppy**?
- Did anything **move** unexpectedly?
- Did it **notify** you unnecessarily?
- Did you ever wonder **where to tap**?
- Did the interface ever **fight** your gesture?
- Did the first screenful answer the **task**?
- Does a screen look like **one designed workspace**, or like stacked tool output?
- **Could you hand this to somebody with no explanation?**

That last one is the standard for the whole pass.

---

## What to write down

Nothing, ideally — say it out loud during the session (step 9) and let the recorder take it.
Whether it captures you is itself part of the test.

## What this does not cover

Real Shopify or Gmail writes (nothing was staged in the last session either, so the action
engine is untested by this script and unchanged by this pass), the Control app on the Mac, and
anything needing a scope that is not granted.
