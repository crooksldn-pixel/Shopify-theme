# The pad as a dedicated device — a plan, not an implementation

The tablets that run CROOKS Assistant do nothing else. Today the assistant reaches them as a
web page in Chrome, opened from the home screen. This document sets out what a dedicated
application would buy over that page, what it would cost, which route is right for this
product, and what else would make the pad more useful once it is treated as a fixture rather
than a browser tab. Nothing here is built. Everything here is sized so that it can be decided.

## What the page cannot do, and why it matters on a dedicated device

The web page is good at the conversation. It is poor at being a *fixture*:

| Gap | What the owner sees | Root cause |
|---|---|---|
| It can be closed, swiped away, navigated off | A black pad that has to be "opened" | Chrome is a general browser |
| The screen sleeps, or Chrome is backgrounded, and the wake lock and microphone go | First question of the afternoon fails or clips | Web wake locks and media streams end when the page is hidden |
| No wake word | Every question starts with a hand on the orb | A page cannot listen while hidden, and continuous listening in a tab is fragile |
| Nothing arrives unasked | The pad never says "a new order came in" | No push to a page that is not open; no background execution |
| Permission prompts can reappear | Microphone prompt after a Chrome update or cache clear | Web permissions are per-origin and revocable |
| The address has to be typed once per pad | Setting up a second pad means Tailscale, Chrome, the URL, the home-screen shortcut | No provisioning story |
| Audio routing is Chrome's | Voice plays through whatever Android chose | No control over output device or ducking |

Half of these are solved by making the page a *kiosk*; the other half need a real
application. The routes below are ordered by how much of the table they close for how much
work, and the recommendation is to take them in order and stop when the pad is good enough.

## Route 1 — the page, installed properly (done, or one afternoon)

Already shipped: the app installs from Chrome as "CROOKS OS" — a manifest with
`display: standalone`, portrait orientation, the wordmark as its icon (maskable too, so
Samsung's launcher shapes it like the others), a wake lock while the page is showing, and a
service worker that keeps the shell (page, scripts, styles, icons) and nothing else, so the
installed app opens instantly and, when the Mac is away, opens onto a SYSTEM OFFLINE state
of its own that reconnects by itself. A new build installs in the background and is taken
only when nothing is in progress. Cheap additions still on the web side:

- **An "as of 09:12" stamp on every card.** A fixture's enemy is staleness: a count that was
  true this morning must not look true at four o'clock. One line in the renderer.
- **Android's own kiosk mode ("screen pinning")** — Settings → Security → Pin windows — keeps
  Chrome on the page and needs a PIN to leave. Zero code. It does not stop the screen sleeping.
- **Display never sleeps while charging** — Developer options → Stay awake. Zero code.

This closes "can be closed" and "reloads slowly" and nothing else. It is where a single pad
on a desk should stop for now.

## Route 2 — a kiosk browser (a day, no code)

Fully Kiosk Browser (or an equivalent) is a paid Android app that wraps a URL with the fixture
behaviour the page lacks: launch at boot, stay on the URL, keep the screen on, auto-reload on
failure, remote configuration, and a motion-triggered screensaver. It also grants microphone
permission permanently to the configured URL.

What it closes: closing, sleeping, permission prompts, and boot-to-assistant. What it does
not: wake word, unasked arrivals, audio routing. It is the right answer for two or three pads
in one workroom and costs an afternoon per pad. The assistant needs no change; the page is
already built for it.

## Route 3 — a thin Android application (two to three weeks)

A native Android shell (Kotlin) whose only screen is a WebView showing the same page, but
which owns the things a page cannot:

- **Foreground service**: the app keeps running with the screen off; the microphone stream
  and the AudioContext survive; the wake lock is the app's, not Chrome's.
- **Wake word** on the device ("Crooks…") using an on-device engine (Picovoice Porcupine or
  the open-source openWakeWord), which then hands the page a "start listening" event
  through the WebView bridge. This is the single largest change to how the pad feels: no
  hand on the orb for a question across the room.
- **Push from the Mac**: a persistent connection (server-sent events over Tailscale) from
  the app to `/events`, so the Mac can tell the pad "new order #1934, £95, unfulfilled" the
  moment Shopify's webhook arrives, and the pad can say so out loud — read-only stays
  read-only; this is the Mac talking, not acting.
- **Provisioning**: the app carries the Tailscale hostname, installs as a device-owner app
  (Android Enterprise "dedicated device" mode) so it launches at boot and cannot be left,
  and sets up the second and third pad in a minute each.
- **Audio**: choose the output (the pad's speaker, a Bluetooth speaker, a USB DAC), duck the
  voice when the owner starts talking, and keep the microphone's echo cancellation tuned
  for the room.

The page inside it stays exactly the page that exists now: one codebase, one renderer, one
`ui` contract, one voice pipeline. The app is a frame, not a rewrite. That is what makes it
two to three weeks rather than three months, and what keeps the tests meaningful.

What it costs beyond the weeks: an Android Studio install on the Mac, a signing key, a
private distribution route (sideload or an internal Play track), and, for the wake word,
either a Picovoice licence or an evening tuning openWakeWord on the owner's voice.

## Route 4 — a fully native application (months)

Rebuilding the orb, the cards and the voice pipeline in Kotlin (Jetpack Compose, ExoPlayer,
Oboe) would buy lower audio latency on the pad and a smoother orb on the 2019 GPU. It would
also duplicate every renderer, every fixture and every guard in a second language, and put
the tablet on a release cycle of its own. Nothing in the product asks for it. Not
recommended while the page inside a shell can do the job.

## Recommendation

Take Route 1 now (mostly done), Route 2 the day a second pad appears or the first one is
found asleep once too often, and Route 3 when either the wake word or unasked arrivals
become the thing the owner wants next. Skip Route 4. In every case the backend on the Mac
is unchanged: every route here talks to the same `/turn`, `/speak`, `/state` and `/health`,
and the read-only gate is the same gate.

## Greater utility on the pad, whichever route

These are product ideas, each read-only, each sized. They are what a dedicated pad is for.

1. **The morning brief** (backend, three days). One spoken paragraph on the first question of
   the day, or on a tap: overnight orders, anything still to ship, customer email waiting,
   stock at zero. Two of its four parts exist as GREEN tools today (`shopify_list_orders`
   with `unfulfilled_only` over a 60-day window; `gmail_search`); the third,
   `shopify_sales_summary`, exists; the fourth — stock at zero across the whole catalogue
   without naming a product — needs a new GREEN tool and one live-store check of the
   variant search filter. Composed only from GREEN tools, with a gate test that proves no
   AMBER handler runs inside it, and presented as an `attention` card — the component and
   its footer surface already exist and are fed by nothing. This is the highest-value
   unbuilt thing in the product.
2. **Unasked arrivals** (backend two days, pad one day; Route 3 for the pad to hear them
   while idle). Shopify's `orders/create` webhook to the Mac (through `tailscale funnel` or a
   small relay), a server-sent-events stream to the pad, and the orb's SUCCESS state with one
   spoken line. Read-only: the Mac is told, it does not act.
3. **Camera lookups** (pad, three days) — a maybe, not a plan. Point the camera at a barcode
   and hear the stock line. Scribe already hears numbers well; this earns its place only if
   packing slips turn out to be read aloud more often than spoken.
4. **A second pad in the workroom** (Route 2, an afternoon). Same Mac, same conversation
   session per pad, the context stack showing what the other pad last asked about.
5. **Hands-free follow-ups** (pad, two days). After Derek answers, listen for three seconds
   without a hold; a follow-up spoken in that window is sent, silence is not. The warm
   microphone and the level gate make this cheap; the risk is the office's ambient noise,
   which is why it should be a setting, off by default.
6. **The label printer** — is a write, and stays out of scope until the gate has an AMBER
   confirmation path with a real read-back. The `confirmation` component is built for it.

## What to decide

- Whether one pad on the desk is the product (Route 1, stop) or several around the workroom
  are (Route 2 now, Route 3 later).
- Whether a wake word is wanted at all. It is the reason to build the Android shell; without
  it, Route 2 is enough for years.
- Whether unasked arrivals are welcome in a workroom, or whether the pad should only ever
  speak when spoken to. That is a taste decision, and it decides the second half of Route 3.
