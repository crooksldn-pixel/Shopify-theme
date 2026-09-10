/* The Phase 2 tablet audit: the page driven the way a person drives it, and measured.
 *
 * The difference from scripts/browser/experience.js is what it is for. That one is a
 * regression gate — it asks whether the page can draw what the backend sent and whether a
 * finger can hit it, and it must stay cheap and stable. This one asks the questions a person
 * holding the tablet would ask, and answers them in numbers:
 *
 *   how much of the screen is spent before the answer starts
 *   how far you have to scroll to see everything
 *   what is visible without scrolling at all
 *   which controls are below the fold
 *   how big the things you tap are
 *   what text is repeated on one screen
 *
 * It drives real turns through the page's own `submit()` (the typing field in the diagnostics
 * sheet posts exactly what the microphone posts), so what is measured is the interface the
 * owner gets — chrome, animation, dock and all — rather than a card rendered into a bare div.
 *
 *   node scripts/browser/audit.js http://127.0.0.1:8765 /path/to/screenshots [label]
 *
 * Prints one JSON object: { ok, surfaces: [...], shots: [...] }.
 */
'use strict';

const { chromium } = require('playwright-core');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = process.argv[3] || '';
const LABEL = process.argv[4] || 'after';
// The Galaxy Tab A 8.0 (SM-T290), portrait, which is how it sits on the workbench.
const VIEWPORT = { width: 800, height: 1280 };
const HEADERS = { 'Tailscale-User-Login': 'owner@example.com', 'X-Forwarded-For': '100.64.0.9' };
// Below this a control is a coin toss for a thumb. Material and HIG both land near here.
const MIN_TAP = 44;

const surfaces = [];
const shots = [];

async function main() {
  const browser = await chromium.launch({
    executablePath: process.env.CROOKS_CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  });
  const context = await browser.newContext({
    viewport: VIEWPORT, deviceScaleFactor: 1, isMobile: true, hasTouch: true,
    extraHTTPHeaders: HEADERS,
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    // The 503 is this script's own /speak stub. Counting it would bury a real fault.
    const text = m.text();
    if (m.type() === 'error' && !/503|speak/i.test(text)) errors.push(`console: ${text}`);
  });
  await page.route('**/speak', (r) => r.fulfill({
    status: 503, contentType: 'application/json',
    body: '{"ok":false,"kind":"no_key","reason":"no voice under test"}',
  }));

  // `?dev=1` is what wires the typing field to `submit()`. It also drops a "developer mode"
  // banner into the page, which production never shows — so it goes, before anything is
  // measured. What is left is the interface the owner gets.
  await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('.dev-banner')) b.remove();
  });

  const shot = async (name) => {
    if (!OUT) return '';
    const file = path.join(OUT, `${LABEL}-${name}.png`);
    await page.waitForTimeout(450);
    await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
    shots.push(path.basename(file));
    return path.basename(file);
  };

  /* Ask, the way the microphone asks. The diagnostics field calls the same `submit()` the
   * recogniser calls, so the whole client path runs: busy state, /turn, render, pushContext,
   * setMode, the dock. Injecting into the renderer would skip all of it. */
  const ask = async (text) => {
    await page.evaluate(() => {
      const sheet = document.querySelector('#settings');
      const dev = document.querySelector('#dev');
      if (dev) dev.hidden = false;
      if (sheet && !sheet.open && sheet.showModal) sheet.showModal();
    });
    await page.fill('#dev-text', text);
    await page.press('#dev-text', 'Enter');
    await page.waitForTimeout(900);
    await page.evaluate(() => {
      const sheet = document.querySelector('#settings');
      if (sheet && sheet.open && sheet.close) sheet.close();
    });
    await page.waitForTimeout(350);
  };

  /* What the screen is actually like, in numbers rather than adjectives. */
  const measure = async () => page.evaluate((minTap) => {
    const deck = document.querySelector('#cards');
    const fold = window.innerHeight;
    const out = {
      fold,
      scrollHeight: deck ? deck.scrollHeight : 0,
      viewportHeight: deck ? deck.clientHeight : 0,
      screensToScroll: deck && deck.clientHeight ? +(deck.scrollHeight / deck.clientHeight).toFixed(2) : 0,
      mode: document.body.dataset.mode || '',
    };
    const cards = Array.from(document.querySelectorAll('#cards .card'));
    out.cards = cards.map((c) => {
      const r = c.getBoundingClientRect();
      return {
        type: c.dataset.type || '',
        top: Math.round(r.top),
        height: Math.round(r.height),
      };
    });
    // How much of the screen is spent before the answer begins.
    out.contentStartsAt = cards.length ? Math.round(cards[0].getBoundingClientRect().top) : null;
    // Everything you can tap, and whether it is below the fold when the card first draws.
    const tappables = Array.from(document.querySelectorAll(
      '#cards button, #cards [role="tab"], #cards a, #cards [data-ask], #cards .row, #cards li.item, #cards .rank-row, #cards tbody tr',
    ));
    out.tappable = tappables.map((el) => {
      const r = el.getBoundingClientRect();
      return {
        what: (el.textContent || '').trim().slice(0, 28),
        kind: el.dataset.action ? 'action' : (el.getAttribute('role') === 'tab' ? 'tab' : el.tagName.toLowerCase()),
        w: Math.round(r.width), h: Math.round(r.height),
        top: Math.round(r.top),
        belowFold: r.top > fold - 60,
        small: r.height < minTap || r.width < minTap,
      };
    });
    out.tooSmall = out.tappable.filter((t) => t.small && t.h > 0).length;
    out.smallest = out.tappable.filter((t) => t.small && t.h > 0)
      .map((t) => `${t.what || t.kind}(${t.w}x${t.h})`).slice(0, 6);
    out.belowFold = out.tappable.filter((t) => t.belowFold).length;
    // Text repeated inside one deck. A number the owner reads three times is two too many.
    // Visible only. Tab panels are all in the DOM and only one is shown, so counting the lot
    // reported "£84.00 x4" for a card the owner sees it on twice — a measurement that would
    // have sent me hunting duplication that is not on screen.
    const words = {};
    for (const el of document.querySelectorAll('#cards .card *')) {
      if (el.children.length) continue;
      if (!el.getClientRects().length) continue;
      const t = (el.textContent || '').trim();
      if (t.length < 3 || t.length > 40) continue;
      words[t] = (words[t] || 0) + 1;
    }
    out.repeated = Object.entries(words).filter(([, n]) => n > 1)
      .sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t, n]) => `${t} x${n}`);
    // Where the screen goes before the answer does. Each band, by name, so a saving can be
    // attributed rather than admired.
    out.bands = [];
    for (const sel of ['.topbar', '#orb-dock', '.orb-zone', '#heard', '#answer', '.nav', '#branch-bar', '.stack-chips', '#cards']) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.height < 1) continue;
      out.bands.push({ sel, top: Math.round(r.top), height: Math.round(r.height) });
    }
    // Anything spilling sideways is a layout fault on a narrow screen, always.
    out.overflowX = deck ? deck.scrollWidth > deck.clientWidth + 1 : false;
    // What the assistant said, and how much of it.
    const answer = document.querySelector('#answer');
    out.spoken = answer ? (answer.textContent || '').trim() : '';
    out.spokenChars = out.spoken.length;
    // What the glass costs. Every element with a live backdrop-filter is a separate
    // compositing pass over everything behind it; every element with a running animation
    // is a frame the GPU cannot skip. The reference measured 66 and ~120 on one page.
    const all = Array.from(document.querySelectorAll('body *'));
    out.blurLayers = all.filter((e) => { const b = getComputedStyle(e).backdropFilter; return b && b !== 'none' && e.getClientRects().length; }).length;
    out.animating = all.filter((e) => { const cs = getComputedStyle(e); return cs.animationName !== 'none' && cs.animationIterationCount === 'infinite' && e.getClientRects().length; }).length;
    return out;
  }, MIN_TAP);

  /* Frame time while the deck scrolls and a tab changes: the two things a hand does most.
   * Relative numbers — this is a workstation's Chromium, not the Tab A — but the same probe
   * before and after a styling change says whether the change made frames longer. */
  const jank = async () => page.evaluate(() => new Promise((resolve) => {
    const deck = document.querySelector('#cards');
    const frames = [];
    let last = performance.now();
    let n = 0;
    const tabs = Array.from(document.querySelectorAll('#cards [role="tab"]'));
    const tick = (now) => {
      frames.push(now - last); last = now; n += 1;
      if (deck) deck.scrollTop = (n % 40) * 12;
      if (tabs.length && n % 15 === 0) tabs[(n / 15) % tabs.length].click();
      if (n < 90) requestAnimationFrame(tick);
      else {
        frames.shift();
        const sorted = frames.slice().sort((a, b) => a - b);
        resolve({
          frames: frames.length,
          meanMs: +(frames.reduce((a, b) => a + b, 0) / frames.length).toFixed(1),
          p95Ms: +sorted[Math.floor(sorted.length * 0.95)].toFixed(1),
          worstMs: +sorted[sorted.length - 1].toFixed(1),
          over32ms: frames.filter((f) => f > 32).length,
        });
      }
    };
    requestAnimationFrame(tick);
  }));

  const record = async (name, title, note) => {
    const m = await measure();
    m.name = name;
    m.title = title;
    m.note = note || '';
    m.shot = await shot(name);
    surfaces.push(m);
    return m;
  };

  // The orb screen, before any question: the dock and the atmosphere, on their own. The hold
  // label must sit clear of the dock here — in context mode the two share a band by design.
  const orbScreen = await page.evaluate(() => {
    const label = document.querySelector('#talk-label').getBoundingClientRect();
    const dockTop = Math.min(...Array.from(document.querySelectorAll('.dock-btn')).map((b) => b.getBoundingClientRect().top));
    return { mode: document.body.dataset.mode, lit: document.querySelectorAll('.dock-btn[aria-pressed="true"]').length,
      labelBottom: Math.round(label.bottom), dockTop: Math.round(dockTop), labelClearsDock: label.bottom <= dockTop,
      lite: document.documentElement.dataset.lite === '1' };
  });
  await record('home', 'The orb screen', JSON.stringify(orbScreen));

  // ---------------------------------------------------------------- P0 workflows

  await ask('show me order 1938');
  await record('order-detail', 'Show me order 1938');

  // The items tab: what did they actually buy.
  const tab = async (word) => {
    const found = await page.evaluate((w) => {
      const t = Array.from(document.querySelectorAll('#cards [role="tab"]'))
        .find((el) => (el.textContent || '').toLowerCase().includes(w));
      if (t) t.click();
      return Boolean(t);
    }, word.toLowerCase());
    await page.waitForTimeout(500);
    return found;
  };
  await record('order-items', 'Order 1938, Items tab', (await tab('items')) ? '' : 'no Items tab found');
  await record('order-email', 'Order 1938, Email tab', (await tab('email')) ? '' : 'no Email tab found');

  await ask("show me today's orders");
  await record('order-list', "Show me today's orders");

  await ask('which customers need replying to?');
  await record('needs-reply', 'Which customers need replying to?');

  await ask('what else has this customer ordered?');
  await record('customer', 'What else has this customer ordered?');

  await ask('what can you do now?');
  await record('capability', 'What can you do now?');

  // Tapping a row must open the record it names. `open.entity` existed on the Mac from Phase 1
  // and nothing on the page posted it, so a list was a picture of the orders rather than a way
  // into them.
  await ask("show me today's orders");
  const opened = await page.evaluate(async () => {
    const row = document.querySelector('#cards .row.tappable[data-kind="order"]');
    if (!row) return { tapped: false, why: 'no tappable order row' };
    const was = (document.querySelector('#cards .card') || {}).dataset || {};
    row.click();
    await new Promise((r) => setTimeout(r, 1200));
    const now = document.querySelector('#cards .card');
    return {
      tapped: true,
      wasType: was.type || '',
      nowType: (now && now.dataset.type) || '',
      nowRef: (now && now.dataset.ref) || '',
    };
  });
  await record('row-tap', 'Tapping a row on the order list', JSON.stringify(opened));

  // The graph, walked with a finger only: order -> a prior order of the same customer ->
  // the customer chip in the nav bar. Every hop used to need a spoken sentence.
  await ask('show me order 1938');
  const hops = await page.evaluate(async () => {
    const out = [];
    const tap = async (el, what) => {
      if (!el) { out.push(`${what}: MISSING`); return; }
      el.click();
      await new Promise((r) => setTimeout(r, 1300));
      const card = document.querySelector('#cards .card');
      out.push(`${what}: ${(card && card.dataset.type) || 'none'} ${(card && card.dataset.ref) || ''}`);
    };
    const customerTab = Array.from(document.querySelectorAll('#cards [role="tab"]'))
      .find((t) => (t.textContent || '').toLowerCase().includes('customer'));
    if (customerTab) { customerTab.click(); await new Promise((r) => setTimeout(r, 400)); }
    await tap(document.querySelector('#cards .hist-rows .row.tappable[data-kind="order"]'), 'prior order');
    await tap(document.querySelector('#stack .chip[data-kind="customer"], #stack .chip[data-ref*="Customer"]'), 'customer chip');
    return out;
  });
  await record('graph-hops', 'order to prior order to customer, by finger', JSON.stringify(hops));

  // The dock: a tap on an area lands on that area's surface and lights the icon; the lit icon
  // follows what is on screen (a spoken question that changes area moves it); nothing lights
  // on the orb screen. And its geometry: every icon a finger can hit, none under the pill.
  const dock = await page.evaluate(async () => {
    const out = { steps: [] };
    const lit = () => Array.from(document.querySelectorAll('.dock-btn[aria-pressed="true"]')).map((b) => b.dataset.area).join(',') || 'none';
    const cardType = () => ((document.querySelector('#cards .card') || {}).dataset || {}).type || '';
    const tap = async (area) => {
      const b = document.querySelector(`.dock-btn[data-area="${area}"]`);
      if (!b) { out.steps.push({ area, missing: true }); return; }
      b.click();
      await new Promise((r) => setTimeout(r, 1400));
      out.steps.push({ tapped: area, card: cardType(), lit: lit(), mode: document.body.dataset.mode });
    };
    await tap('orders');
    await tap('email');
    await tap('sales');
    await tap('products');
    const btns = Array.from(document.querySelectorAll('.dock-btn')).map((b) => { const r = b.getBoundingClientRect(); return { area: b.dataset.area, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; });
    const pill = document.querySelector('#talk-label').getBoundingClientRect();
    out.geometry = { buttons: btns, pill: { x: Math.round(pill.x), y: Math.round(pill.y), w: Math.round(pill.width), h: Math.round(pill.height) } };
    out.overlapsPill = btns.some((b) => b.x < pill.x + pill.width && b.x + b.w > pill.x && b.y < pill.y + pill.height && b.y + b.h > pill.y);
    out.small = btns.filter((b) => b.w < 44 || b.h < 44).length;
    const deck = document.querySelector('#cards');
    out.deckClearsDock = deck ? parseInt(getComputedStyle(deck).paddingBottom, 10) >= 112 : false;
    return out;
  });
  await record('dock', 'The dock, tapped through each area', JSON.stringify({ steps: dock.steps, overlapsPill: dock.overlapsPill, small: dock.small, deckClearsDock: dock.deckClearsDock }));
  // Home is the FIRST RECORD of the trail (navigation.home), not the orb screen: the lit icon
  // must follow the record it lands on, which after the walk above is the order list.
  await page.evaluate(() => { const h = document.querySelector('#home-btn'); if (h) h.click(); });
  await page.waitForTimeout(900);
  const home = await page.evaluate(() => ({
    mode: document.body.dataset.mode,
    card: ((document.querySelector('#cards .card') || {}).dataset || {}).type || '',
    lit: Array.from(document.querySelectorAll('.dock-btn[aria-pressed="true"]')).map((b) => b.dataset.area).join(',') || 'none',
  }));
  await record('home-after', 'Home: the lit icon follows the record it lands on', JSON.stringify(home));
  // Frame time, on the order card, as a hand would use it — first as this machine is
  // classed (a Chromium reporting four cores or fewer is lite, as the Tab A is), then with
  // the full design forced on, so the cost of the glass is a number and not a guess.
  await ask('show me order 1938');
  const liteNow = await page.evaluate(() => document.documentElement.dataset.lite === '1');
  const frames = await jank();
  const cost = await measure();
  surfaces.push({ name: liteNow ? 'frames-lite' : 'frames-full', title: `Frame time while scrolling and switching tabs (${liteNow ? 'lite device' : 'full design'})`,
    note: JSON.stringify(frames), blurLayers: cost.blurLayers, animating: cost.animating, ...frames });
  await page.goto(`${BASE}?dev=1&lite=${liteNow ? 0 : 1}`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });
  await ask('show me order 1938');
  const framesOther = await jank();
  const costOther = await measure();
  surfaces.push({ name: liteNow ? 'frames-full' : 'frames-lite', title: `Frame time while scrolling and switching tabs (${liteNow ? 'full design, forced' : 'lite, forced'})`,
    note: JSON.stringify(framesOther), blurLayers: costOther.blurLayers, animating: costOther.animating, ...framesOther });
  await shot(liteNow ? 'order-detail-full' : 'order-detail-lite');

  await browser.close();
  const ok = errors.length === 0;
  process.stdout.write(`${JSON.stringify({ ok, errors: errors.slice(0, 4), surfaces, shots })}\n`);
  return ok ? 0 : 1;
}

main().then((code) => process.exit(code)).catch((e) => {
  process.stdout.write(`${JSON.stringify({ ok: false, error: String(e && e.message).slice(0, 500), surfaces, shots })}\n`);
  process.exit(1);
});
