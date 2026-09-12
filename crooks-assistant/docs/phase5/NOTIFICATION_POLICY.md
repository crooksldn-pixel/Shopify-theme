# CROOKS OS — the notification policy

**Status:** enforced. `web/notify.js` refuses what this document forbids, `tests/web/notify.test.js`
proves the behaviour under Node, and `tests/test_notification_policy.py` holds every call site on the
tablet to it. Nothing here is advice.

**Why it exists.** Phase 4 built the three homes a message can have. It did not build a policy, so the
live tablet session of 11 September (`docs/phase5/LIVE_SESSION_FORENSICS.md`, **D-10**) emitted
**sixteen** notifications and every single one was noise.

---

## THE EVIDENCE, AND THE ONE SENTENCE THE POLICY IS FOR

> Sixteen `tablet_notify` events; eleven carry no text at all, and the five with text are
> `divided`, `merged`, `divided`, `merged`, `divided` — state changes the screen itself shows.

**The five.** Every one of them announced a state change that the screen had *just visibly made*.
The orb divided in front of him; two named chips appeared under it; and then a bubble told him it had.
The orb visibly dividing **is** the notification.

**The eleven.** These carried nothing the system could read back. They reached `show()` through
`toast(words)` — a wrapper whose whole job was to say something without naming it — so the recorded
event was `{name:"workspace", tone:"info"}` and nothing else. Some also carried no *words*: a call
site passed a server field straight through (`toast(data.answer, 'bad')`) and an empty `detail` or an
empty `answer` produced an empty message, silently.

Both halves reduce to one rule:

> **A notification with no words is not a notification. Neither is one with no name.**

Under this policy, all sixteen are impossible. `tests/web/notify.test.js` replays them and asserts
zero appear on the glass — with sixteen recorded refusals, each carrying its reason.

---

## §10 · THE FIRST QUESTION IS NEVER "WHERE DOES THIS TOAST GO"

> A state change should usually update **THE PLACE THE STATE ALREADY LIVES.**

| The event | What used to happen | What happens |
|---|---|---|
| Draft saved | a bubble said "Draft saved" | the **Draft control** becomes `Saved` (`web/action-state.js`) |
| A branch result finishing | a bubble over unrelated work | the **branch chip** says `READY` (`.branch-chip.is-ready`) |
| Order opened | a bubble | **nothing** — the order is on the screen |
| Tab changed | a bubble | **nothing** — the tab is the selected tab |
| Split completed | "Divided. Tap a half to talk to it…" | **nothing** — the UI is visibly split |
| Merged | "Merged. 2 things it looked at came back." | **nothing** — one orb, one chip, and the deck has them |

Ask, in this order:

1. **Is there a place this state already lives?** A control, a chip, a card, a label. If yes, update
   it, and stop. This is the answer most of the time.
2. **Is the change visible on the screen the owner is looking at?** If yes, stop.
3. **Only then**: which of the three homes below does it belong to?

---

## THE THREE HOMES, AND ONLY THREE

Every message declares its class, and the class decides where it is drawn. All three hosts are normal
blocks in the document: a message **takes** space rather than borrowing it. Nothing floats over the
dock, the orb, the halves, Back, Next, Split, the composer or an approval surface — not as a style
choice but as the mechanism, and `web/collide.js` measures it in Chromium so it stays true.

### CONTROL-LOCAL — `class: 'control'`
Field and action feedback, drawn directly **after the control it is about**, inside that control's own
card, so it scrolls with the thing it concerns and can cover nothing.

Use it for: an invalid email, a quantity the Mac changed, a typed value the Mac refused, a chip the Mac
would not prepare, a command that got no answer.

*Three messages moved here this pass.* A rejected typed value was a workspace line — a message about
the screen, printed 788px from the thumb that typed it, for something that happened inside one field.

### WORKSPACE-LOCAL — `class: 'workspace'`
Meaningful task outcomes, in **its own space above the cards** (or under the orb's caption when the orb
is the screen). This is the default class, and a message about one half carries its `branch` and is
hidden while the other half is focused — still there when the owner comes back to it.

Use it for: a refund that was proved, an archive that came back, a half that hit a problem, a change
that came back from a merge still waiting for a gesture.

### GLOBAL — `class: 'global', machine: true`
**Genuinely global system problems ONLY**, and there are three: *Disconnected*, *Backend unavailable*,
*Update required*. These are states of the machine itself. In flow, at the top, above the wordmark,
pushing the screen down.

Asking to be global is not enough to be global: without `machine: true` the class is silently demoted
to `workspace`, because anything else that asks to be seen everywhere is a workspace message that has
not been told where it belongs.

---

## THE FOUR REFUSALS

Applied by `check(spec)` in `web/notify.js` to **every** message before it is built. `check` is exported
as a pure function, so a call site or a test can ask the policy without drawing anything.

| reason | what is refused | why |
|---|---|---|
| `no_words` | nothing to read, or nothing with a letter or a digit in it | a row holding a dash is the empty notification with a character in it |
| `no_code` / `bad_code` | no name, or a name that is not `lower_snake_case` | the name is what makes the other three enforceable, and what telemetry and deduplication both match on |
| `screen_shows` | `divided`, `merged`, `split`, `closed`, `opened`, `tab`, `tab_changed`, `navigated`, `home`, `back`, `next`, `focused`, … | §10 — the screen has already changed |
| `control_shows` | `draft_saved`, `saved`, `sent`, `archived`, `applied`, `staged`, `armed`, `done`, `ready`, `success`, `verified`, `committed` | the control carries its own outcome |

The two muted lists are `SCREEN_SHOWS` and `CONTROL_SHOWS`, exported so a call site can be told which
one it hit. They are policy, not implementation, and the reason a code is in one of them is written
beside it in the source.

**A refusal is an event, never a silence.** Every one records `notify_refused` with its reason and the
code, and never the words. The eleven went unnoticed for a whole evening because dropping a message
silently is indistinguishable from not having a policy at all.

---

## THE CAPS

| name | value | the reasoning |
|---|---|---|
| `MAX_TRANSIENT` | **2** | Across **all three hosts**, not per host. A message row is ~44px; two is 88px of a ~700px workbench screen (12%), three is 132px (19%) and starts costing a card. And a person with one hand on an order does not follow three lines that are all disappearing. The newest wins; the oldest transient goes. |
| `MAX_GOOD` | **1** | **Never stack "done"/"ready"/"success"/"opened" for one event.** One event, one line. A second success replaces the first, because the newest is the current truth and two lines both saying a thing worked is one thing the owner has to read twice. |
| `MAX_PER_HOST` | **3** | Failures are not transient — a failure waits to be dismissed — so neither cap above counts them. This is the ceiling that stops a run of failures pushing the deck off the screen. |

## DEDUPLICATION

Two messages are **the same message** when their class, their **name** and their half match. Not their
sentence. The sentence used to be part of the key, so every message carrying a count, a name or an
amount defeated deduplication by definition: *"1 change still waiting"* and *"2 changes still waiting"*
were two rows about one recurring event. One event is one row, with a count, and the newest words are
the ones on it. The half stays part of the key, so one half's news never overwrites the other's.

## LIFETIME, AND THE ONE CONTROL A MESSAGE MAY CARRY

* A failure (`tone: 'bad'`) **persists until dismissed** and carries `Dismiss`.
* A warning gets 9s; an info or a success gets 4s, and carries no button because it leaves on its own.
* `Dismiss` is the **only** control a message may ever carry. A transient line must never become a way
  to get somewhere: the screen it would go to may already be gone.
* Every message says what it is in a **word** as well as in a colour — `Note` / `Done` / `Check` /
  `Failed` — because a workbench light and a cheap panel take the colour out of a border long before
  they take a word out of a line.

---

## HOW TO ADD ONE

```js
notify('The refund was proved on the store.', { tone: 'good', code: 'refund_proved' });
notifyControl('That does not look like an email address.', field, { tone: 'bad', code: 'invalid_email' });
notify('The Mac did not answer.', { class: 'global', machine: true, tone: 'bad', code: 'backend_silent' });
```

Before you write it, answer these in order. If you stop at 1, 2 or 3, there is no notification.

1. Is there a control, chip, card or label where this state already lives? → update that.
2. Did the screen just visibly change in the way this message describes? → stop.
3. Is this a *success* the owner can see for himself? → stop.
4. Which home? Beside a control, in the workspace, or — only for the machine's own three states — global.
5. What is its **name**? `lower_snake_case`, stable, not shared with a different event.
6. What does it say when the Mac sent no words? Every call site carries its own sentence, behind `||` if
   the Mac's words are preferred, because a field that can be empty is how the eleven happened.

## WHERE IT IS ENFORCED

| file | what it holds |
|---|---|
| `web/notify.js` | the policy itself — `check`, `refuse`, `makeRoom`, the two muted lists, the three caps, deduplication |
| `web/app.js` | the call sites, each carrying a literal `code:` and words of its own |
| `tests/web/notify.test.js` | the behaviour, under Node: every refusal, both caps, the dedupe, and the whole live session replayed to zero |
| `tests/test_notification_policy.py` | the source: `toast()` is gone, every call site is named, none of them announces a muted state, and the numbers here match the code |
| `web/collide.js`, `scripts/browser/collision.js` | that no host ever overlaps anything, measured in Chromium |
