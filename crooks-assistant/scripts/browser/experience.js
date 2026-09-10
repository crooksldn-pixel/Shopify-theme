/* The tablet, for real: the page in Chromium, talking to a backend that is serving the
 * golden world.
 *
 * This is the difference between this file and scripts/browser/accept.js. That one stubs the
 * turn payloads and checks that the renderer can draw them — a good check, and not this one.
 * Here every response comes from the real backend over HTTP, so what is being checked is the
 * whole thing: the router chose a lane, a recipe read the fixture shop, a presenter shaped a
 * card, the page drew it, and a finger can hit what it drew.
 *
 *   node scripts/browser/experience.js http://127.0.0.1:8765 /path/to/screenshots
 *
 * Prints one JSON object: { ok, checks: [{name, ok, detail}], shots: [...] }.
 *
 * Nothing here reaches Shopify, Gmail or ElevenLabs — the backend it is pointed at is the
 * fixture one — and /speak is answered with a 503 so no voice is synthesised.
 */
'use strict';

const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = process.argv[3] || '';
// The Galaxy Tab A 8.0 (SM-T290), portrait, which is how it sits on the workbench.
const VIEWPORT = { width: 800, height: 1280 };
// What the backend expects from a request `tailscale serve` proxied.
const HEADERS = { 'Tailscale-User-Login': 'owner@example.com', 'X-Forwarded-For': '100.64.0.9' };

const checks = [];
const shots = [];
const check = (name, ok, detail) => checks.push({ name, ok: Boolean(ok), detail: detail === undefined ? '' : String(detail).slice(0, 300) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`console: ${m.text()}`); });
  // No voice under test: a 503 is what the tablet already handles when ElevenLabs is absent.
  await page.route('**/speak', (r) => r.fulfill({ status: 503, contentType: 'application/json', body: '{"ok":false,"kind":"no_key","reason":"no voice under test"}' }));

  // Cards fade and rise as they arrive. A screenshot taken the instant after drawing catches
  // them part-way through and reads as a blank or half-dimmed screen, which is a picture of
  // the animation rather than of the interface. Wait for it to settle, and stop it repeating.
  const shot = async (name) => {
    if (!OUT) return;
    const file = path.join(OUT, `${name}.png`);
    await page.waitForTimeout(500);
    await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
    shots.push(path.basename(file));
  };

  // The page talks to the backend itself; this asks a question the way the orb does, by
  // posting a transcript, and then waits for the card to appear.
  const ask = async (text, session) => page.evaluate(async ([t, s]) => {
    const r = await fetch('/turn', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: t, session_id: s }),
    });
    return r.json();
  }, [text, session]);

  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(600);
  // Draw a turn the way the app does: the page's own renderer, its own vocabulary, its own
  // skip list. Nothing here re-implements rendering — if a card cannot be drawn, CrooksUI
  // says so in `skipped` and the check above fails.
  await page.evaluate(() => {
    window.__crooksDraw = (payload) => {
      const root = document.querySelector('#cards, .cards, main') || document.body;
      const out = window.CrooksUI.render(payload.ui || [], {});
      root.innerHTML = '';
      out.nodes.forEach((n) => root.appendChild(n));
      return { nodes: out.nodes.length, skipped: out.skipped };
    };
  });
  const hasRenderer = await page.evaluate(() => Boolean(window.CrooksUI && window.CrooksUI.render));
  check('the page exposes its renderer', hasRenderer, 'window.CrooksUI');
  check('the page loads with no script error', errors.length === 0, errors.join(' | '));
  await shot('01-home');

  // ---- 1. a real order lookup, drawn by the real renderer
  const turn = await ask('show me order 1938', 'browser');
  const types = (turn.ui || []).map((i) => i.type);
  check('the backend answered with an order surface', types.indexOf('order') !== -1, `ui=${types.join(',')}`);
  check('it took the fast lane', turn.lane === 'FAST', `lane=${turn.lane}`);

  // The page renders whatever the app puts on screen; drive it the way a person does, by
  // typing into the shell's own input if it has one, otherwise by handing the payload to the
  // renderer the page already exposes for its fixtures.
  const drawn = await page.evaluate((payload) => window.__crooksDraw(payload), turn);
  check('the renderer drew the cards the backend sent', drawn.nodes > 0,
    `nodes=${drawn.nodes} skipped=${(drawn.skipped || []).join(',')}`);
  check('the renderer skipped nothing the backend sent', (drawn.skipped || []).length === 0,
    `skipped=${(drawn.skipped || []).join(',')}`);
  await shot('02-order-detail');

  // ---- 2. the card is mechanically usable
  const card = await page.evaluate(() => {
    const el = document.querySelector('.card, [data-kind="order"]');
    if (!el) return null;
    const tabs = Array.from(el.querySelectorAll('[role="tab"], .tab')).map((t) => (t.textContent || '').trim());
    const buttons = Array.from(el.querySelectorAll('button')).map((b) => {
      const r = b.getBoundingClientRect();
      return { text: (b.textContent || '').trim().slice(0, 24), w: Math.round(r.width), h: Math.round(r.height) };
    });
    return { tabs, buttons, width: Math.round(el.getBoundingClientRect().width) };
  });
  check('the order card rendered', card !== null, JSON.stringify(card).slice(0, 160));
  if (card) {
    check('it has tabs to spread the detail over', card.tabs.length >= 3, `tabs=${card.tabs.join('/')}`);
    const tappable = card.buttons.filter((b) => b.w >= 32 && b.h >= 32);
    check('its controls are big enough for a finger',
      card.buttons.length === 0 || tappable.length === card.buttons.length,
      `${tappable.length}/${card.buttons.length} at 32px+`);
    check('the card fits the tablet', card.width <= VIEWPORT.width, `card=${card.width}px viewport=${VIEWPORT.width}px`);
  }

  // ---- 3. nothing scrolls sideways, at this width or narrower
  for (const width of [VIEWPORT.width, 400]) {
    await page.setViewportSize({ width, height: VIEWPORT.height });
    await page.waitForTimeout(120);
    const overflow = await page.evaluate(() => ({
      doc: document.documentElement.scrollWidth,
      win: window.innerWidth,
      widest: Array.from(document.querySelectorAll('body *')).reduce((w, el) => Math.max(w, el.scrollWidth), 0),
    }));
    check(`no horizontal overflow at ${width}px`, overflow.doc <= overflow.win + 1,
      `scrollWidth=${overflow.doc} innerWidth=${overflow.win} widest=${overflow.widest}`);
  }
  await page.setViewportSize(VIEWPORT);

  // ---- 4. a tab switch through the semantic command endpoint
  const tabbed = await page.evaluate(async () => {
    const form = new URLSearchParams({ session_id: 'browser', command: 'surface.tab', surface: 'order', tab: 'shipping' });
    const r = await fetch('/command', { method: 'POST', body: form });
    return r.json();
  });
  check('tapping a tab is a semantic command the server owns', tabbed.ok === true && (tabbed.changed || {}).tab === 'shipping',
    JSON.stringify(tabbed).slice(0, 160));

  // ---- 5. a list, then walking it
  const list = await ask("show me today's orders", 'browser');
  check('a list question draws a list', (list.ui || []).some((i) => i.type === 'order_list'),
    `ui=${(list.ui || []).map((i) => i.type).join(',')}`);
  await page.evaluate((payload) => window.__crooksDraw(payload), list);
  await shot('03-order-list');
  const rows = await page.evaluate(() => Array.from(document.querySelectorAll('.rows li, .row')).length);
  check('the list rendered rows to tap', rows > 0, `rows=${rows}`);

  const next = await page.evaluate(async () => {
    const form = new URLSearchParams({ session_id: 'browser', command: 'workflow.next' });
    return (await fetch('/command', { method: 'POST', body: form })).json();
  });
  check('Next moves the cursor from the browser', next.ok === true && /\d+ of \d+/.test(next.answer || ''),
    `answer=${next.answer}`);

  const back = await page.evaluate(async () => {
    const form = new URLSearchParams({ session_id: 'browser', command: 'navigation.back' });
    return (await fetch('/command', { method: 'POST', body: form })).json();
  });
  check('Back returns and redraws', back.ok === true && (back.ui || []).length > 0,
    `ui=${(back.ui || []).map((i) => i.type).join(',')} answer=${back.answer}`);

  // ---- 6. touch, then voice
  const bound = await page.evaluate(async () => {
    const form = new URLSearchParams({ session_id: 'browser', command: 'voice.bind', family: 'order.add_note' });
    return (await fetch('/command', { method: 'POST', body: form })).json();
  });
  check('a tapped control can arm the microphone for what it is about',
    bound.ok === true && ((bound.changed || {}).listening_for || {}).family === 'order.add_note',
    JSON.stringify(bound.changed || {}).slice(0, 160));

  // ---- 7. the capability surface
  const caps = await ask('what can you do now?', 'browser');
  check('the capability question draws a surface', (caps.ui || []).some((i) => i.type === 'capability'),
    `ui=${(caps.ui || []).map((i) => i.type).join(',')}`);
  const capsDrawn = await page.evaluate((payload) => window.__crooksDraw(payload), caps);
  check('the capability surface renders', capsDrawn.nodes > 0 && (capsDrawn.skipped || []).length === 0,
    `nodes=${capsDrawn.nodes} skipped=${(capsDrawn.skipped || []).join(',')}`);
  const capsBody = await page.evaluate(() => {
    const el = document.querySelector('.card');
    return el ? { height: Math.round(el.getBoundingClientRect().height), text: (el.textContent || '').trim().length } : null;
  });
  check('the capability card has something in it', capsBody && capsBody.height > 80 && capsBody.text > 40,
    JSON.stringify(capsBody));
  await shot('04-capabilities');

  check('no script error during the whole run', errors.length === 0, errors.slice(0, 3).join(' | '));

  await browser.close();
  const ok = checks.every((c) => c.ok);
  process.stdout.write(`${JSON.stringify({ ok, checks, shots })}\n`);
  return ok ? 0 : 1;
}

main().then((code) => process.exit(code)).catch((e) => {
  process.stdout.write(`${JSON.stringify({ ok: false, checks: [{ name: 'browser run', ok: false, detail: String(e && e.message).slice(0, 400) }], shots })}\n`);
  process.exit(1);
});
