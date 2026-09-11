/* D-3, in the browser: the split, at both sizes the tablet is ever measured at.
 *
 * The Phase 3 live session, 00:23:57 to 00:24:04 — six `branch_focused` events in nine
 * seconds, and the report's own branch table saying "focus changed with nothing redrawn" four
 * times. The owner: "it just so shows two of the same thing", "the split function doesn't work
 * at all". That is a claim about pixels, so it is checked where the pixels are.
 *
 * Both viewports, in one run, because the 800 x 1280 gate could not see what the physical
 * 601 x 889 tablet did:
 *
 *   node scripts/browser/split.js http://127.0.0.1:8765 /path/to/screenshots
 *
 * Prints one JSON object: { ok, checks: [{name, ok, detail}], shots: [...] }.
 */
'use strict';

const { chromium } = require('playwright-core');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = process.argv[3] || '';
// The gate's size, and the size of the tablet in the owner's hand. A check that passes on one
// and not the other is the class of defect this file exists for.
const SIZES = [
  { name: '601x889', viewport: { width: 601, height: 889 }, dpr: 1.33 },
  { name: '800x1280', viewport: { width: 800, height: 1280 }, dpr: 1 },
];
const HEADERS = { 'Tailscale-User-Login': 'owner@example.com', 'X-Forwarded-For': '100.64.0.9' };

const checks = [];
const shots = [];
const check = (name, ok, detail) => checks.push({ name, ok: Boolean(ok), detail: detail === undefined ? '' : String(detail).slice(0, 300) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function atSize(browser, size) {
  const at = (what) => `${what} (${size.name})`;
  const context = await browser.newContext({
    viewport: size.viewport, deviceScaleFactor: size.dpr, isMobile: true, hasTouch: true,
    extraHTTPHeaders: HEADERS,
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    if (m.type() !== 'error') return;
    const from = (m.location && m.location() && m.location().url) || '';
    if (from.includes('/speak')) return;
    errors.push(`console: ${m.text()}`);
  });
  const posts = [];
  page.on('request', (r) => { if (r.method() === 'POST') posts.push(r.url().replace(BASE, '')); });
  await page.route('**/speak', (r) => r.fulfill({ status: 503, contentType: 'application/json', body: '{"ok":false,"kind":"no_key","reason":"no voice under test"}' }));
  // A microphone that makes noise, so a recording that must NOT be sent is shown not to be
  // sent rather than being too short to send.
  await page.addInitScript(() => {
    const AC = window.AudioContext || window.webkitAudioContext;
    const ac = new AC();
    const dest = ac.createMediaStreamDestination();
    const osc = ac.createOscillator(); const gain = ac.createGain(); gain.gain.value = 0.2;
    osc.frequency.value = 220; osc.connect(gain); gain.connect(dest); osc.start();
    navigator.mediaDevices.getUserMedia = async () => { await ac.resume(); return dest.stream; };
  });

  const shot = async (name) => {
    if (!OUT) return;
    const file = path.join(OUT, `split-${size.name}-${name}.png`);
    await page.waitForTimeout(400);
    await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
    shots.push(path.basename(file));
  };
  // Everything on the glass that identifies a half: the header band, the chips, and the cards
  // in order with what each is about. This is the string the owner was comparing by eye.
  const screen = () => page.evaluate(() => {
    const head = document.querySelector('#branch-head');
    return {
      mode: document.body.dataset.mode,
      head: head && !head.hidden ? head.textContent.replace(/\s+/g, ' ').trim() : '',
      headState: head ? head.dataset.state || '' : '',
      cards: Array.from(document.querySelectorAll('#cards .card')).map((c) => `${c.dataset.type || ''}:${c.dataset.ref || ''}`),
      chips: Array.from(document.querySelectorAll('.branch-chip')).map((c) => ({
        head: c.dataset.head || '', pressed: c.getAttribute('aria-pressed') === 'true',
        text: c.textContent.replace(/\s+/g, ' ').trim(),
        h: Math.round(c.getBoundingClientRect().height),
        onScreen: c.getBoundingClientRect().right <= innerWidth + 1 && c.getBoundingClientRect().left >= -1,
      })),
      offers: Array.from(document.querySelectorAll('#cards .half-empty .rail-chip')).map((b) => ({
        words: b.textContent.trim(), command: b.dataset.offer || '',
        h: Math.round(b.getBoundingClientRect().height),
      })),
      answer: ((document.querySelector('#answer') || {}).textContent || '').trim(),
      toast: ((document.querySelector('#toast') || {}).textContent || '').trim(),
      wide: document.documentElement.scrollWidth > innerWidth + 1,
    };
  });
  const branchesNow = () => page.evaluate(async () => {
    const id = localStorage.getItem('crooks.session') || '';
    const r = await fetch(`/branches?session_id=${encodeURIComponent(id)}`, { cache: 'no-store' });
    const d = await r.json();
    return { count: (d.branches || []).length, focused: d.focused || '', ids: (d.branches || []).map((b) => b.branch_id),
             heads: (d.branches || []).map((b) => (b.headline || {}).title || ''), states: (d.branches || []).map((b) => b.state || '') };
  });
  const say = async (text) => {
    await page.evaluate(() => { const s = document.querySelector('#settings'), d = document.querySelector('#dev'); if (d) d.hidden = false; if (s && !s.open && s.showModal) s.showModal(); });
    await page.fill('#dev-text', text);
    await page.press('#dev-text', 'Enter');
    await sleep(1500);
    await page.evaluate(() => { const s = document.querySelector('#settings'); if (s && s.open) s.close(); });
    await sleep(300);
  };
  const tapChip = async (id) => {
    await page.evaluate((b) => { const c = document.querySelector(`.branch-chip[data-branch="${b}"]`); if (c) c.click(); }, id);
    await sleep(1500);
  };

  await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);
  await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });

  // ---- 1. the visible way in. The gesture is a shortcut; the button is the path that works.
  const splitChip = await page.evaluate(() => {
    const c = document.querySelector('#branch-bar [data-action="split"], #branch-rail [data-action="split"]');
    if (!c) return null;
    const b = c.getBoundingClientRect();
    return { host: c.parentElement.id, h: Math.round(b.height), w: Math.round(b.width), label: c.getAttribute('aria-label') || '',
             onScreen: b.top >= 0 && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth };
  });
  check(at('a visible Split control is on the idle screen, finger-sized and on screen'),
        Boolean(splitChip && splitChip.h >= 40 && splitChip.onScreen), JSON.stringify(splitChip));
  const why = await page.evaluate(() => {
    const n = document.querySelector('#branch-bar .branch-why');
    if (!n) return null;
    const b = n.getBoundingClientRect();
    return { text: n.textContent.trim(), onScreen: b.left >= 0 && b.right <= innerWidth };
  });
  check(at('and it says what it is for, rather than only what it is called'),
        Boolean(why && why.text && why.onScreen), JSON.stringify(why));

  // ---- 2. one half, asked for a list. Then divide.
  await say("show me today's orders");
  const first = await screen();
  check(at('the first half draws its list'), first.cards.some((c) => c.startsWith('order_list')), JSON.stringify(first.cards));
  check(at('with one half there is no header to tell apart'), first.head === '', `head="${first.head}"`);

  posts.length = 0;
  await page.evaluate(() => { const c = document.querySelector('#branch-bar [data-action="split"], #branch-rail [data-action="split"]'); if (c) c.click(); });
  await sleep(1600);
  const divided = await branchesNow();
  check(at('the Split button divides the orb'), divided.count === 2, `branches=${divided.count}`);
  check(at('and the division sends no speech turn'), !posts.includes('/turn'), `posted: ${posts.join(', ') || 'nothing'}`);
  const afterSplit = await screen();
  check(at('both halves are chips a finger can hit, each naming what it is'),
        afterSplit.chips.length === 2 && afterSplit.chips.every((c) => c.h >= 40 && c.onScreen && c.head),
        JSON.stringify(afterSplit.chips));
  check(at('the screen now says which half it is'), /ORDERS/.test(afterSplit.head) && /half 1 of 2/.test(afterSplit.head),
        `head="${afterSplit.head}"`);
  await shot('01-divided');

  // ---- 3. the fresh half shows ITS OWN nothing, with somewhere to go — never the other
  // half's cards under a different chip, which is the whole of the owner's complaint.
  const other = divided.ids.find((id) => id !== divided.focused);
  await tapChip(other);
  const onSecond = await screen();
  check(at('tapping the other half redraws: the first half\'s cards are gone'),
        !onSecond.cards.some((c) => c.startsWith('order_list')), JSON.stringify(onSecond.cards));
  check(at('the fresh half says it is the fresh half'),
        /EMPTY|ORDER/.test(onSecond.head) && /half 2 of 2/.test(onSecond.head), `head="${onSecond.head}"`);
  check(at('and offers somewhere to go, as controls a thumb can hit'),
        onSecond.offers.length >= 4 && onSecond.offers.every((o) => o.h >= 40 && o.command),
        JSON.stringify(onSecond.offers));
  // "Divided." is about the thing he just did, and belongs on screen. What must never be
  // there is a line about the OTHER half's work: the selector says READY, and that is all.
  check(at('and nothing about the other half was thrown over this one'),
        !/other half/i.test(onSecond.toast), `toast="${onSecond.toast}"`);
  await shot('02-second-half');

  // ---- 4. two halves, two questions, two screens. This is the assertion the session needed.
  await say('find emails needing replies');
  const secondAnswered = await screen();
  check(at('the second half draws its own place'), secondAnswered.cards.some((c) => c.startsWith('email_list')),
        JSON.stringify(secondAnswered.cards));
  check(at('and says so in its header'), /INBOX/.test(secondAnswered.head), `head="${secondAnswered.head}"`);

  await tapChip(divided.focused);
  const backOnFirst = await screen();
  await tapChip(other);
  const backOnSecond = await screen();
  const differ = JSON.stringify(backOnFirst.cards) !== JSON.stringify(backOnSecond.cards);
  check(at('switching halves changes the cards on screen, both ways'),
        differ && backOnFirst.cards.some((c) => c.startsWith('order_list')) && backOnSecond.cards.some((c) => c.startsWith('email_list')),
        JSON.stringify({ first: backOnFirst.cards, second: backOnSecond.cards }));
  check(at('and changes the header with them'), backOnFirst.head !== backOnSecond.head,
        JSON.stringify({ first: backOnFirst.head, second: backOnSecond.head }));
  check(at('the lit chip is the half being talked to'),
        backOnSecond.chips.filter((c) => c.pressed).length === 1, JSON.stringify(backOnSecond.chips.map((c) => c.pressed)));
  await shot('03-both-halves');

  // ---- 5. nothing on either half runs off the side of an eight-inch screen.
  check(at('no half of this ever scrolls sideways'), !backOnSecond.wide, 'the page is wider than the screen');

  // ---- 6. a background half that finishes says READY on the selector, and gives up its work
  // when it is tapped. Asked on the half NOT on screen, so the answer lands elsewhere.
  const finished = await page.evaluate(async (id) => {
    const s = localStorage.getItem('crooks.session') || '';
    const r = await fetch('/turn', {
      method: 'POST', headers: { 'content-type': 'application/json' }, cache: 'no-store',
      body: JSON.stringify({ text: 'show me order 1938', session_id: s, branch_id: id }),
    });
    const d = await r.json();
    return { ok: r.ok, answer: String(d.answer || '').slice(0, 80) };
  }, divided.focused);
  await sleep(600);
  await page.evaluate(async () => {
    const s = localStorage.getItem('crooks.session') || '';
    const r = await fetch(`/branches?session_id=${encodeURIComponent(s)}`, { cache: 'no-store' });
    window.__branches = await r.json();
  });
  await page.evaluate(() => { if (window.__branches) window.dispatchEvent(new Event('focus')); });
  const listed = await branchesNow();
  check(at('the half that answered while he was elsewhere says READY'),
        finished.ok && listed.states.includes('READY'), JSON.stringify({ ok: finished.ok, states: listed.states }));
  const whileElsewhere = await screen();
  check(at('and says it on the selector, not over the half he is reading'),
        !/other half/i.test(whileElsewhere.toast) && whileElsewhere.cards.some((c) => c.startsWith('email_list')),
        JSON.stringify({ toast: whileElsewhere.toast, cards: whileElsewhere.cards }));
  await tapChip(divided.focused);
  const retrieved = await screen();
  check(at('and tapping it shows the work it finished'),
        retrieved.cards.some((c) => c.startsWith('order')), JSON.stringify(retrieved.cards));
  await shot('04-ready-retrieved');

  // ---- 7. a one-finger hold is still a question, and a second finger joining it is still
  // not one: the Phase 2/3 gesture-safety work must not regress with a visible Split button.
  const pill = await page.evaluate(() => { const b = document.querySelector('#talk-label').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
  const cdp = await context.newCDPSession(page);
  const touches = (type, points) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: points });
  posts.length = 0;
  await touches('touchStart', [{ x: pill.x - 90, y: pill.y }]);
  await sleep(140);
  await touches('touchStart', [{ x: pill.x - 90, y: pill.y }, { x: pill.x + 90, y: pill.y }]);
  for (let i = 1; i <= 8; i++) {
    await touches('touchMove', [{ x: pill.x - 90 + i * 10, y: pill.y }, { x: pill.x + 90 - i * 10, y: pill.y }]);
    await sleep(30);
  }
  await touches('touchEnd', []);
  await sleep(1800);
  check(at('a second finger joining a hold merges and never becomes a sentence'),
        !posts.includes('/turn'), `posted: ${posts.join(', ') || 'nothing'}`);

  check(at('no script error during the whole run'), errors.length === 0, errors.slice(0, 3).join(' | '));
  await context.close();
}

async function main() {
  const browser = await chromium.launch({
    executablePath: process.env.CROOKS_CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  });
  try {
    for (const size of SIZES) await atSize(browser, size);
  } finally {
    await browser.close();
  }
  const ok = checks.every((c) => c.ok);
  process.stdout.write(`${JSON.stringify({ ok, checks, shots, viewports: SIZES.map((s) => s.name) })}\n`);
  return ok ? 0 : 1;
}

main().then((code) => process.exit(code)).catch((e) => {
  process.stdout.write(`${JSON.stringify({ ok: false, checks: checks.concat([{ name: 'split run', ok: false, detail: String(e && e.message).slice(0, 400) }]), shots })}\n`);
  process.exit(1);
});
