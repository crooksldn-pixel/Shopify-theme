/* The phone, measured — 390 × 844 and 375 × 667, with a finger.
 *
 *   node scripts/browser/mobile.js http://127.0.0.1:8765 [/path/to/screenshots]
 *
 * WHY THIS FILE EXISTS, and it is the same answer as collision.js's.
 *
 * Every browser gate in this repo runs at 601 × 889 and 800 × 1280. Those are the tablet, and
 * they are the right two sizes for the device that exists. But `DESIGN.md` §13 names 390 × 844
 * as part of the verification matrix and nothing in the suite had ever rendered a pixel at it,
 * so what the product did on a phone was an opinion. It was wrong:
 *
 *   the dock asked for 476px on a 390px screen — four 52px areas, a 200px hold slot, four 10px
 *   gaps, 28px of padding. Orders sat at x = -29 and Products ended at x = 419: two of the four
 *   ways into the shop were half a control each, on every surface. And `--hold-w` narrowed to
 *   200px while `.talk-label` kept `min-width:240px`, so the hold pill was painted 10px over
 *   the Inbox icon and 10px over the Sales icon — VOICE over NAVIGATION, which is D-1's rule
 *   and D-1's shape, five layers apart in the §8 table and touching anyway.
 *
 * The page's own collision engine reported all of it the moment it was asked at 390. It had
 * never been asked. That is the whole argument for this file: not a new opinion about phones,
 * a new SIZE for the instruments that already exist.
 *
 * Three things here that the tablet gates do not do:
 *
 *   SAFE AREAS ARE SET, NOT ASSUMED. `env(safe-area-inset-*)` cannot be written from a test,
 *   which is why nothing had ever checked it. web/style.css reads the four insets through
 *   `--safe-t/r/b/l` instead, so this gate can give the page an iPhone's real notch and home
 *   indicator and measure what the layout does with them.
 *
 *   THE KEYBOARD IS OPENED. `interactive-widget=resizes-content` shrinks the viewport rather
 *   than overlaying it, so a phone typing a reply is 390 × ~508 — a size at which the dock,
 *   the rail and the halves all have to give way to the field.
 *
 *   THE PRESSES ARE REAL. CDP touch events at measured pixels, 95 ms — the live session's
 *   median tap — because `element.click()` cannot be swallowed by anything painted over it and
 *   therefore cannot see the defect class this file is here for.
 *
 * Prints one JSON object: { ok, checks: [{name, ok, detail}], shots }.
 */
'use strict';

const { chromium } = require('playwright-core');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = process.argv[3] || '';
const HEADERS = { 'Tailscale-User-Login': 'owner@example.com', 'X-Forwarded-For': '100.64.0.9' };

/* The two phones. 390 × 844 is `DESIGN.md` §13's representative iPhone; 375 × 667 is the
   narrowest screen still in service, and it is in the matrix because a band that fits 390 by
   four pixels does not fit 375 at all — the failure mode being measured here is arithmetic. */
const PHONES = [
  { name: '390x844@3', width: 390, height: 844, dpr: 3 },
  { name: '375x667@2', width: 375, height: 667, dpr: 2 },
];
/* An iPhone held in portrait with a notch and a home indicator. Real numbers, not round ones:
   these are what Safari reports for the 390 × 844 class of device. */
const INSETS = { top: 59, bottom: 34 };
const PRESS_MS = 95;
const TAP_MIN = 44;   // what web/style.css actually gives a chip; --tap (48) is the target

const checks = [];
const shots = [];
const check = (name, ok, detail) => checks.push({ name, ok: Boolean(ok), detail: detail === undefined ? '' : String(detail).slice(0, 460) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const browser = await chromium.launch({
    executablePath: process.env.CROOKS_CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  });
  try {
    for (const phone of PHONES) await sweep(browser, phone);
  } finally {
    await browser.close();
  }
  const ok = checks.every((c) => c.ok);
  process.stdout.write(`${JSON.stringify({ ok, checks, shots, viewports: PHONES.map((p) => p.name) })}\n`);
  return ok ? 0 : 1;
}

async function sweep(browser, vp) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dpr,
    isMobile: true, hasTouch: true, extraHTTPHeaders: HEADERS,
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    if (m.type() !== 'error') return;
    const from = (m.location && m.location() && m.location().url) || '';
    if (from.includes('/speak')) return;
    errors.push(`console: ${m.text()}${from ? ` <- ${from}` : ''}`);
  });
  const posts = [];
  page.on('request', (r) => { if (r.method() === 'POST') posts.push(r.url().replace(BASE, '')); });
  await page.route('**/speak', (r) => r.fulfill({ status: 503, contentType: 'application/json', body: '{"ok":false,"kind":"no_key","reason":"no voice under test"}' }));
  // A microphone that makes noise, so a recording that ends by mistake is shown NOT to be
  // sent rather than being too short to send. Same reason as tablet.js.
  await page.addInitScript(() => {
    const AC = window.AudioContext || window.webkitAudioContext;
    const ac = new AC();
    const dest = ac.createMediaStreamDestination();
    const osc = ac.createOscillator(); const gain = ac.createGain(); gain.gain.value = 0.2;
    osc.frequency.value = 220; osc.connect(gain); gain.connect(dest); osc.start();
    navigator.mediaDevices.getUserMedia = async () => { await ac.resume(); return dest.stream; };
  });
  const cdp = await context.newCDPSession(page);
  const at = (what) => `${vp.name} · ${what}`;
  const shot = async (name) => {
    if (!OUT) return;
    const file = path.join(OUT, `mobile-${vp.name.replace(/[@.]/g, '')}-${name}.png`);
    await page.waitForTimeout(320);
    await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
    shots.push(path.basename(file));
  };

  const arrive = async () => {
    await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1100);
    await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });
  };
  await arrive();

  // ---------------------------------------------------------------- 1. the idle screen
  await geometry(page, at, 'the idle screen');
  await shot('01-idle');

  // ---------------------------------------------------------------- 2. every area is reachable
  // with a finger, and it is the LANDING command that goes — not a sentence. The dock is the
  // only navigation a phone has while the cards are up, and two of its four were off the side.
  for (const area of ['orders', 'email', 'sales', 'products']) {
    const box = await page.evaluate((a) => {
      const b = document.querySelector(`.dock-btn[data-area="${a}"]`);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width), h: Math.round(r.height) };
    }, area);
    check(at(`the ${area} area is wholly on the screen`),
      Boolean(box) && box.left >= -1 && box.right <= vp.width + 1 && box.h >= TAP_MIN,
      JSON.stringify(box) + ` · viewport ${vp.width}px`);
    if (!box) continue;
    // And nothing is painted between the thumb and it.
    const under = await page.evaluate((p) => {
      const el = document.elementFromPoint(p.x, p.y);
      return el ? `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}.${String(el.className || '').split(' ')[0]}` : 'none';
    }, box);
    check(at(`nothing sits between the thumb and the ${area} area`),
      /dock-btn|dock-label|svg|path/i.test(under), `under it: ${under}`);
    posts.length = 0;
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: box.x, y: box.y }] });
    await sleep(PRESS_MS);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    for (let i = 0; i < 30 && !posts.length; i++) await sleep(200);
    await sleep(1800);
    check(at(`a ${PRESS_MS}ms press on ${area} lands, as a landing and not as a sentence`),
      posts.includes('/command') && !posts.includes('/turn'), `posted: ${posts.join(', ') || 'nothing'}`);
  }
  await shot('02-products');

  // ---------------------------------------------------------------- 3. a list, and a record
  await page.evaluate(() => { const b = document.querySelector('.dock-btn[data-area="orders"]'); if (b) b.click(); });
  await sleep(4000);
  await geometry(page, at, 'an order list');
  // The chevron that says a row opens something must sit BESIDE the row's right-hand column,
  // not on it. `.rows.tight .row{padding:9px 0}` was a shorthand and reset the 26px
  // `.row.tappable` reserves for it, so "1h ago" was drawn as "1h ag›" on every tight list at
  // every viewport. The collision gate cannot see it — the chevron is `aria-hidden`, so it is
  // `decorative` — which is why the check is written out here.
  const chevrons = await page.evaluate(() => Array.from(document.querySelectorAll('#cards .row.tappable')).map((row) => {
    const side = row.querySelector('.row-side'); const go = row.querySelector('.row-go');
    if (!side || !go) return null;
    const s = side.getBoundingClientRect(); const g = go.getBoundingClientRect();
    const w = Math.min(s.right, g.right) - Math.max(s.left, g.left);
    const h = Math.min(s.bottom, g.bottom) - Math.max(s.top, g.top);
    return w > 1 && h > 1 ? { over: `${Math.round(w)}x${Math.round(h)}`, text: side.textContent.trim().slice(0, 18) } : null;
  }).filter(Boolean));
  check(at('the chevron sits beside what a row says, never on it'), chevrons.length === 0,
    JSON.stringify(chevrons.slice(0, 4)));
  await shot('03-orders-list');

  const opened = await page.evaluate(() => {
    const cards = new Set(Array.from(document.querySelectorAll('#cards .card')).map((c) => c.dataset.ref || ''));
    const row = Array.from(document.querySelectorAll('#cards [data-ref][data-kind="order"]'))
      .find((el) => !el.classList.contains('card') && !cards.has(el.dataset.ref) && el.getBoundingClientRect().width > 2);
    if (!row) return false;
    row.click();
    return true;
  });
  if (opened) await sleep(4000);
  check(at('an order row on a phone opens the order'),
    opened && (await page.evaluate(() => Array.from(document.querySelectorAll('#cards .card')).some((c) => c.dataset.type === 'order'))),
    `opened=${opened}`);
  await geometry(page, at, 'an order');
  await shot('04-order');

  // ---------------------------------------------------------------- 4. the tabs are the density
  // answer on the tablet and they are more so here. Each one has to be a finger target and each
  // one has to be on the screen.
  const tabs = await page.evaluate(() => Array.from(document.querySelectorAll('#cards [role="tab"]')).map((t) => {
    const b = t.getBoundingClientRect();
    return { tab: t.dataset.tab || '', left: Math.round(b.left), right: Math.round(b.right), h: Math.round(b.height) };
  }));
  check(at('every tab on a card is a finger target'), tabs.length > 0 && tabs.every((t) => t.h >= TAP_MIN),
    JSON.stringify(tabs.filter((t) => t.h < TAP_MIN)) || `${tabs.length} tabs`);

  // ---------------------------------------------------------------- 5. a proposal, which is the
  // one surface where a mis-tap costs money. Nothing may be drawn over it and nothing under.
  await page.evaluate(() => {
    const root = document.querySelector('#cards');
    const out = window.CrooksUI.render([{
      type: 'confirmation',
      data: {
        title: 'Refund £40.00 to the card', family: 'order.refund', tier: 'amber',
        summary: 'Refunds £40.00 of £84.00 to the card ending 4242 on order #1938.',
        lines: [{ label: 'Order', value: '#1938' }, { label: 'Amount', value: '£40.00' }],
        proposal_id: 'p-mobile-gate',
      },
    }], {});
    root.replaceChildren();
    out.nodes.forEach((n) => root.appendChild(n));
    document.body.dataset.mode = 'context';
  });
  await sleep(600);
  await geometry(page, at, 'a proposal');
  const approval = await page.evaluate(() => {
    const sel = (window.CrooksTouch && window.CrooksTouch.APPROVAL_SELECTOR) || '.approve, [data-approve]';
    return Array.from(document.querySelectorAll(sel)).map((el) => {
      const b = el.getBoundingClientRect();
      return { sel: `${el.tagName.toLowerCase()}.${String(el.className || '').split(' ')[0]}`, left: Math.round(b.left), right: Math.round(b.right), h: Math.round(b.height), onScreen: b.left >= -1 && b.right <= innerWidth + 1 && b.bottom <= innerHeight + 1 };
    });
  });
  check(at('the approval surface is wholly on a phone screen and finger-sized'),
    approval.length === 0 || approval.every((a) => a.onScreen && a.h >= TAP_MIN), JSON.stringify(approval));
  await shot('05-proposal');

  // ---------------------------------------------------------------- 5b. two halves, which is
  // the most crowded the furniture ever gets: a rule, two named chips, Merge and Close, in a
  // band 390px wide. §17's grid is `minmax(0,1fr) auto minmax(0,1fr)` precisely so a long task
  // label cannot push its neighbour off the edge; this is that claim, at the width where it is
  // hardest to keep.
  const divided = await page.evaluate(() => {
    const c = document.querySelector('#branch-rail [data-action="split"], #branch-bar [data-action="split"]');
    if (!c) return false;
    c.click();
    return true;
  });
  if (divided) await sleep(3200);
  const halves = await page.evaluate(() => Array.from(document.querySelectorAll('.branch-chip')).map((c) => {
    const b = c.getBoundingClientRect();
    return { left: Math.round(b.left), right: Math.round(b.right), h: Math.round(b.height), words: (c.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
  }));
  check(at('a phone can divide the orb, and both halves are whole controls on it'),
    divided && halves.length === 2 && halves.every((c) => c.left >= -1 && c.right <= vp.width + 1 && c.h >= TAP_MIN),
    JSON.stringify(halves) + ` · viewport ${vp.width}px`);
  await geometry(page, at, 'two halves');
  await shot('05b-halves');
  await page.evaluate(() => {
    const m = document.querySelector('#branch-bar [data-action="merge"], #branch-rail [data-action="merge"]')
      || document.querySelector('#branch-bar [data-action="cancel"], [data-action="cancel"]');
    if (m) m.click();
  });
  await sleep(2600);

  // ---------------------------------------------------------------- 6. the notch and the home
  // indicator, SET rather than assumed. `env()` cannot be written from a test; the four tokens
  // can, which is the only reason this check can exist at all.
  await page.addStyleTag({ content: `:root{--safe-t:${INSETS.top}px;--safe-b:${INSETS.bottom}px}` });
  await sleep(420);
  const safe = await page.evaluate((ins) => {
    const dock = document.querySelector('#dock');
    const talk = document.querySelector('#talk');
    const app = document.querySelector('#app');
    const top = document.querySelector('.top');
    const d = dock.getBoundingClientRect(); const t = talk.getBoundingClientRect();
    const cs = getComputedStyle(app);
    return {
      dockHeight: Math.round(d.height),
      talkHeight: Math.round(t.height),
      reserved: Math.round(parseFloat(cs.paddingBottom) || 0),
      appPadTop: Math.round(parseFloat(cs.paddingTop) || 0),
      wordmarkTop: Math.round(top.getBoundingClientRect().top),
      // What the band gives its contents once the indicator has taken its share.
      dockContent: Math.round(d.height - ins.bottom),
      // Nothing that takes a touch may sit in the home indicator's strip — measured on the
      // CONTENT box, not the border box. A band may reach the bottom edge of the screen and
      // pay the inset back as padding; that is how `.dock` and `.talk` are built, and it is
      // the correct shape. What must clear the indicator is the thing the thumb aims at.
      inIndicator: Array.from(document.querySelectorAll('button, [role="button"], a[href], input'))
        .filter((el) => {
          const b = el.getBoundingClientRect();
          if (b.width < 2 || b.height < 2) return false;
          const st = getComputedStyle(el);
          if (st.visibility === 'hidden' || st.display === 'none' || st.opacity === '0') return false;
          const padBottom = parseFloat(st.paddingBottom) || 0;
          return (b.bottom - padBottom) > innerHeight - ins.bottom + 1;
        })
        .map((el) => `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}`),
    };
  }, INSETS);
  check(at('the wordmark clears the notch'), safe.appPadTop === INSETS.top && safe.wordmarkTop >= INSETS.top,
    JSON.stringify({ padTop: safe.appPadTop, wordmarkTop: safe.wordmarkTop, notch: INSETS.top }));
  check(at('the dock band and the room reserved for it are the same number'),
    safe.dockHeight === safe.reserved && safe.dockContent >= 100,
    JSON.stringify({ band: safe.dockHeight, reserved: safe.reserved, contentAfterIndicator: safe.dockContent }));
  check(at('the hold band carries the home indicator too'), safe.talkHeight <= safe.dockHeight && safe.talkHeight > 0,
    JSON.stringify({ talk: safe.talkHeight, dock: safe.dockHeight }));
  check(at('nothing a finger presses sits in the home indicator\'s strip'), safe.inIndicator.length === 0,
    safe.inIndicator.join(', '));
  await geometry(page, at, 'a phone with a notch and a home indicator');
  await shot('06-safe-areas');
  await page.evaluate(() => { for (const s of document.querySelectorAll('style')) { if (s.textContent.includes('--safe-t')) s.remove(); } });
  await sleep(320);

  // ---------------------------------------------------------------- 7. the keyboard. The
  // viewport shrinks rather than being overlaid, so this is a SIZE, and the band, the rail and
  // the halves all have to give way to the field the owner is typing into.
  await page.evaluate(() => {
    const root = document.querySelector('#cards');
    const out = window.CrooksUI.render([{
      type: 'email_compose',
      data: {
        compose_id: 'c-mobile-gate', thread_id: 't-1', about: 'Mia Jones',
        to: { value: 'mia@example.com' }, subject: { value: 'Your order #1938' },
        body: { value: 'Hello Mia,' },
      },
    }], {});
    root.replaceChildren();
    out.nodes.forEach((n) => root.appendChild(n));
    document.body.dataset.mode = 'context';
  }).catch(() => {});
  await sleep(500);
  await page.setViewportSize({ width: vp.width, height: Math.round(vp.height * 0.47) });
  await sleep(500);
  await page.evaluate(() => { const f = document.querySelector('#cards .field-input, #cards textarea, #cards input[type="text"]'); if (f && f.focus) f.focus(); });
  await sleep(520);
  // Focus alone, first — and it is asked as its own question. A field the owner has tapped
  // that is still below the fold of a 63px deck is a defect whatever the geometry says about
  // it afterwards, and rolling it into the sweep below would hide it behind a rectangle.
  const focused = await page.evaluate(() => {
    const f = document.activeElement;
    if (!f || !f.closest || !f.closest('#cards')) return { focused: false };
    const b = f.getBoundingClientRect();
    const deck = document.querySelector('#cards').getBoundingClientRect();
    const scroller = document.querySelector('#cards');
    const card = f.closest('.card');
    return {
      focused: true, sel: `${f.tagName.toLowerCase()}.${String(f.className || '').split(' ')[0]}`,
      visible: Math.round(Math.min(b.bottom, deck.bottom) - Math.max(b.top, deck.top)),
      height: Math.round(b.height), deck: Math.round(deck.height),
      scrollTop: Math.round(scroller.scrollTop), scrollH: scroller.scrollHeight, clientH: scroller.clientHeight,
      cardTop: card ? Math.round(card.getBoundingClientRect().top) : null,
      cardH: card ? Math.round(card.getBoundingClientRect().height) : null,
      cardOverflow: card ? getComputedStyle(card).overflow : '',
      fieldTop: Math.round(b.top), fieldBottom: Math.round(b.bottom),
      deckTop: Math.round(deck.top), deckBottom: Math.round(deck.bottom),
    };
  });
  check(at('tapping into a field brings the whole of it above the fixed band'),
    focused.focused && focused.visible >= Math.min(focused.height, focused.deck) - 1,
    JSON.stringify(focused));
  // Then the page is put where the owner would put it — the field in the middle of what is
  // left — and the geometry is measured there. `scrollIntoView` is what a browser does for a
  // focused field and what a thumb does by dragging; measuring only the un-scrolled position
  // would report the deck's own scroll as a collision.
  await page.evaluate(() => { const f = document.activeElement; if (f && f.scrollIntoView) f.scrollIntoView({ block: 'center' }); });
  await sleep(420);
  const keyboard = await page.evaluate(() => {
    const talk = document.querySelector('#talk-label');
    const t = talk ? talk.getBoundingClientRect() : null;
    const areas = Array.from(document.querySelectorAll('.dock-btn')).filter((b) => {
      const st = getComputedStyle(b);
      return st.display !== 'none' && b.getBoundingClientRect().width > 1;
    }).map((b) => { const r = b.getBoundingClientRect(); return { left: Math.round(r.left), right: Math.round(r.right) }; });
    return {
      height: innerHeight,
      hold: t ? { left: Math.round(t.left), right: Math.round(t.right), h: Math.round(t.height), onScreen: t.left >= -1 && t.right <= innerWidth + 1 && t.bottom <= innerHeight + 1 } : null,
      areasShown: areas,
      halves: (() => { const z = document.querySelector('#branch-zone'); return z ? getComputedStyle(z).display : 'missing'; })(),
    };
  });
  check(at('with the keyboard open the hold is still a whole control on the screen'),
    Boolean(keyboard.hold) && keyboard.hold.onScreen && keyboard.hold.h >= TAP_MIN, JSON.stringify(keyboard.hold));
  check(at('and whatever furniture is still drawn fits the screen'),
    keyboard.areasShown.every((a) => a.left >= -1 && a.right <= vp.width + 1),
    JSON.stringify(keyboard.areasShown));
  await geometry(page, at, 'the keyboard open');
  await shot('07-keyboard');
  await page.setViewportSize({ width: vp.width, height: vp.height });
  await sleep(420);

  // ---------------------------------------------------------------- 8. reduced motion, which
  // is a product rule (§10) and not a preference. Eight blocks in the sheet honour it; a phone
  // is where a new transition is most likely to be added and least likely to be checked.
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await arrive();
  const still = await page.evaluate(() => {
    const sample = ['#talk-label', '.dock-btn', '.chip', '.orb-frame', '.system-pulse'];
    const out = {};
    for (const sel of sample) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const st = getComputedStyle(el);
      out[sel] = { transition: st.transitionDuration, animation: st.animationDuration };
    }
    return out;
  });
  const longest = Object.values(still).flatMap((s) => [s.transition, s.animation])
    .flatMap((v) => String(v).split(',')).map((v) => parseFloat(v) || 0);
  check(at('prefers-reduced-motion stops the motion'), longest.every((s) => s <= 0.02),
    JSON.stringify(still));
  await page.emulateMedia({ reducedMotion: null });

  check(at('no script error during the whole run'), errors.length === 0, errors.slice(0, 3).join(' | '));
  await context.close();
}

/* The geometry every surface has to satisfy, asked the same way each time. Four questions, and
   the first of them is the page's own collision engine — the same instrument collision.js runs
   at 601 and 800, run here at 390 and 375. It is the authority; the other three name the
   specific shapes this file was written for, so a failure says which. */
async function geometry(page, at, where) {
  const g = await page.evaluate(() => {
    const vw = innerWidth; const vh = innerHeight;
    const shown = (el) => {
      const st = getComputedStyle(el);
      const b = el.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && st.visibility !== 'hidden' && st.display !== 'none' && st.opacity !== '0';
    };
    const nameOf = (el) => `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : ''}`;
    const rect = (el) => { const b = el.getBoundingClientRect(); return { left: Math.round(b.left), right: Math.round(b.right), top: Math.round(b.top), bottom: Math.round(b.bottom), w: Math.round(b.width), h: Math.round(b.height) }; };

    // Voice over navigation, measured directly rather than inferred from a z-index.
    const talk = document.querySelector('#talk-label');
    const over = [];
    if (talk && shown(talk)) {
      const t = talk.getBoundingClientRect();
      for (const nav of document.querySelectorAll('.dock-btn, #context-nav .chip, .branch-chip')) {
        if (!shown(nav)) continue;
        const n = nav.getBoundingClientRect();
        const w = Math.min(t.right, n.right) - Math.max(t.left, n.left);
        const h = Math.min(t.bottom, n.bottom) - Math.max(t.top, n.top);
        if (w > 1 && h > 1) over.push({ nav: nameOf(nav), w: Math.round(w), h: Math.round(h) });
      }
    }

    // Fixed navigation furniture that is not wholly on the screen. The same claim
    // `control_clipped_by_container` makes, restated per element so the detail names it.
    const off = [];
    for (const el of document.querySelectorAll('.dock-btn, #context-nav .chip, .branch-chip, #branch-bar button')) {
      if (!shown(el)) continue;
      const b = el.getBoundingClientRect();
      if (b.left < -1 || b.right > vw + 1) off.push({ el: nameOf(el), ...rect(el), text: (el.textContent || '').trim().slice(0, 18) });
    }

    // And every control a finger has to find.
    const small = [];
    for (const el of document.querySelectorAll('button, [role="button"], [role="tab"], .row.tappable, .chip, .rail-chip, .branch-chip, .dock-btn')) {
      if (!shown(el)) continue;
      if (el.disabled || el.getAttribute('aria-disabled') === 'true') continue;
      const b = el.getBoundingClientRect();
      if (b.height < 44) small.push({ el: nameOf(el), h: Math.round(b.height), text: (el.textContent || '').trim().slice(0, 18) });
    }

    return {
      vw, vh,
      overflowX: document.documentElement.scrollWidth > vw + 1,
      docWidth: document.documentElement.scrollWidth,
      voiceOverNavigation: over, offScreen: off, small,
      collide: window.CrooksCollide ? (() => {
        const s = window.CrooksCollide.scan({});
        return { interactive: s.interactive, worst: (s.interactive_hits || []).slice(0, 3) };
      })() : null,
    };
  });
  check(at(`${where}: no interactive collision`), Boolean(g.collide) && g.collide.interactive === 0,
    g.collide ? JSON.stringify(g.collide.worst) : 'the page has no collision engine');
  check(at(`${where}: the voice layer touches no navigation control`), g.voiceOverNavigation.length === 0,
    JSON.stringify(g.voiceOverNavigation));
  check(at(`${where}: every fixed navigation control fits the screen`), g.offScreen.length === 0,
    JSON.stringify(g.offScreen) + ` · viewport ${g.vw}px`);
  check(at(`${where}: every control a finger finds is at least ${TAP_MIN}px`), g.small.length === 0,
    JSON.stringify(g.small.slice(0, 6)));
  check(at(`${where}: the page is not wider than the phone`), !g.overflowX,
    `document ${g.docWidth}px in ${g.vw}px`);
}

main().then((code) => process.exit(code)).catch((e) => {
  process.stdout.write(`${JSON.stringify({ ok: false, checks: checks.concat([{ name: 'mobile run', ok: false, detail: String((e && e.stack) || e).slice(0, 600) }]), shots })}\n`);
  process.exit(1);
});
