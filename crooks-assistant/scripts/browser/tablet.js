/* The tablet as it physically is: 601 × 889 CSS px at DPR 1.33, the Galaxy Tab A 8.0 in the
 * owner's hand during the Phase 2 live test. Every check here is a failure that test found
 * on the device and that the 800 × 1280 gate could not see — a footer that swallowed the dock,
 * a second finger that became a sentence.
 *
 *   node scripts/browser/tablet.js http://127.0.0.1:8765 /path/to/screenshots
 *
 * Prints one JSON object: { ok, checks: [{name, ok, detail}], shots: [...] }.
 */
'use strict';

const { chromium } = require('playwright-core');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = process.argv[3] || '';
const VIEWPORT = { width: 601, height: 889 };
const DPR = 1.33;
const HEADERS = { 'Tailscale-User-Login': 'owner@example.com', 'X-Forwarded-For': '100.64.0.9' };

const checks = [];
const shots = [];
const check = (name, ok, detail) => checks.push({ name, ok: Boolean(ok), detail: detail === undefined ? '' : String(detail).slice(0, 300) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const browser = await chromium.launch({ executablePath: process.env.CROOKS_CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const context = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: DPR, isMobile: true, hasTouch: true, extraHTTPHeaders: HEADERS });
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
  // A microphone that makes noise, so the encoder produces bytes the way the room does: a
  // recording that ends by mistake must be shown NOT to be sent, not to be too short to send.
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
    const file = path.join(OUT, `tab-${name}.png`);
    await page.waitForTimeout(450);
    await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
    shots.push(path.basename(file));
  };
  const cdp = await context.newCDPSession(page);
  const touches = (type, points) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: points });
  const sessionId = () => page.evaluate(() => localStorage.getItem('crooks.session') || '');
  const branchesNow = () => page.evaluate(async () => {
    const id = localStorage.getItem('crooks.session') || '';
    const r = await fetch(`/branches?session_id=${encodeURIComponent(id)}`, { cache: 'no-store' });
    const d = await r.json();
    return { count: (d.branches || []).length, focused: d.focused || '', ids: (d.branches || []).map((b) => b.branch_id) };
  });
  const screen = () => page.evaluate(() => ({
    mode: document.body.dataset.mode,
    state: document.querySelector('#stage').dataset.state,
    card: ((document.querySelector('#cards .card') || {}).dataset || {}).type || '',
    ref: ((document.querySelector('#cards .card') || {}).dataset || {}).ref || '',
    answer: ((document.querySelector('#answer') || {}).textContent || '').trim(),
    // What the page is saying, from wherever it is saying it. The one floating bubble is gone:
    // a message now belongs to a control, to the workspace, or — for the two states of the
    // machine itself — to the region above the wordmark (web/notify.js). Read as one string,
    // because what these checks care about is whether the words appeared at all.
    toast: Array.from(document.querySelectorAll('#notes-global .note-words, #notes-orb .note-words, #notes-deck .note-words, #cards .note-control .note-words'))
      .filter((n) => !n.closest('.note').hidden)
      .map((n) => n.textContent.trim()).join(' · '),
    errorCard: Boolean(document.querySelector('#cards .card[data-type="error"]')),
    sub: ((document.querySelector('#state-sub') || {}).textContent || '').trim(),
  }));

  await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);
  await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });
  const vp = await page.evaluate(() => [innerWidth, innerHeight, +devicePixelRatio.toFixed(2), document.body.dataset.mode]);
  check('the page is at the tablet\'s real size, idle', vp[0] === 601 && vp[1] === 889 && vp[3] === 'orb', JSON.stringify(vp));
  await shot('01-idle');

  // ---- 1. the idle dock is a way in
  const orders = await page.evaluate(() => { const b = document.querySelector('.dock-btn[data-area="orders"]').getBoundingClientRect(); return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; });
  const under = await page.evaluate((p) => { const e = document.elementFromPoint(p.x, p.y); return e ? `${e.tagName}${e.id ? '#' + e.id : ''}.${(e.className || '').toString().split(' ')[0]}` : 'none'; }, orders);
  check('nothing sits between the thumb and the dock on the idle screen', /dock-btn|dock-label|svg|path/i.test(under), `under the Orders icon: ${under}`);
  posts.length = 0;
  await page.touchscreen.tap(orders.x, orders.y);
  await sleep(1600);
  const afterDock = await screen();
  check('tapping Orders from idle lands on the order list by the landing command, not a sentence', afterDock.card === 'order_list' && posts.includes('/command') && !posts.includes('/turn'), JSON.stringify({ card: afterDock.card, posts }));
  await shot('02-dock-orders');

  // ---- 2. two fingers on the orb: a division, never a sentence
  // Back to the idle screen the way the tablet gets there: a fresh load of the same session.
  await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(900);
  await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });
  const reloaded = await screen();
  check('a reload brings back what the tablet was looking at, from the Mac', reloaded.mode === 'context' && reloaded.card === 'order_list', JSON.stringify({ mode: reloaded.mode, card: reloaded.card }));
  const before = await branchesNow();
  // The Split chip sits under the orb on the idle screen and in the rail beside Next when
  // cards are up: wherever the thumb is, and never behind a gesture alone.
  const splitChip = await page.evaluate(() => { const c = document.querySelector('#branch-bar [data-action="split"], #branch-rail [data-action="split"]'); if (!c) return null; const b = c.getBoundingClientRect(); return { host: c.parentElement.id, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2), w: Math.round(b.width), h: Math.round(b.height), visible: b.width > 0 && b.height > 0 }; });
  check('a visible Split control exists while there is one half', Boolean(splitChip && splitChip.visible && splitChip.h >= 40), JSON.stringify(splitChip));
  const orb = await page.evaluate(() => { const b = document.querySelector('#orb-frame').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
  posts.length = 0;
  await touches('touchStart', [{ x: orb.x - 20, y: orb.y }]);                         // first finger: the hold begins
  await sleep(140);
  await touches('touchStart', [{ x: orb.x - 20, y: orb.y }, { x: orb.x + 20, y: orb.y }]); // second finger
  for (let i = 1; i <= 8; i++) {
    await touches('touchMove', [{ x: orb.x - 20 - i * 12, y: orb.y }, { x: orb.x + 20 + i * 12, y: orb.y }]);
    await sleep(30);
  }
  await touches('touchEnd', []);
  await sleep(2200);
  const afterSplit = await screen();
  const branchesAfter = await branchesNow();
  check('a two-finger spread divides the orb', branchesAfter.count === 2 && before.count < 2, `branches ${before.count} -> ${branchesAfter.count}`);
  check('and sends no speech turn at all', !posts.includes('/turn'), `posted: ${posts.join(', ') || 'nothing'}`);
  check('and shows no hearing error', !afterSplit.errorCard && !/could not hear|cannot hear|closer to the microphone|not running/i.test(afterSplit.answer + ' ' + afterSplit.toast + ' ' + afterSplit.sub) && afterSplit.state !== 'ERROR',
    JSON.stringify({ state: afterSplit.state, answer: afterSplit.answer, toast: afterSplit.toast, sub: afterSplit.sub }));
  check('and says so', /divided/i.test(afterSplit.toast), `toast="${afterSplit.toast}"`);
  await shot('03-divided');

  // ---- 3. the halves are named, and the other one can be tapped
  const chips = await page.evaluate(() => Array.from(document.querySelectorAll('#branch-bar .branch-chip, #branch-rail .branch-chip')).map((c) => ({ id: c.dataset.branch, pressed: c.getAttribute('aria-pressed'), h: Math.round(c.getBoundingClientRect().height) })));
  check('both halves are on screen as chips a finger can hit', chips.length === 2 && chips.every((c) => c.h >= 40), JSON.stringify(chips));

  // ---- 4. pinch merges, and posts nothing either. With cards up the hold surface is the dock
  // band along the bottom (and the small orb); two fingers there, drawn together.
  const pill = await page.evaluate(() => { const b = document.querySelector('#talk-label').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
  posts.length = 0;
  await touches('touchStart', [{ x: pill.x - 110, y: pill.y }]);
  await sleep(140);
  await touches('touchStart', [{ x: pill.x - 110, y: pill.y }, { x: pill.x + 110, y: pill.y }]);
  for (let i = 1; i <= 8; i++) {
    await touches('touchMove', [{ x: pill.x - 110 + i * 12, y: pill.y }, { x: pill.x + 110 - i * 12, y: pill.y }]);
    await sleep(30);
  }
  await touches('touchEnd', []);
  await sleep(2000);
  const merged = await branchesNow();
  check('a pinch on the dock band merges the halves and sends no speech turn', merged.count === 1 && !posts.includes('/turn'), `branches=${merged.count} posted=${posts.join(', ') || 'nothing'}`);

  // ---- 5. the Split button reaches the same command as the gesture
  if ((await branchesNow()).count > 1) { await page.evaluate(() => { const c = document.querySelector('[data-action="cancel"]'); if (c) c.click(); }); await sleep(1200); }
  const again = await page.evaluate(() => { const c = document.querySelector('#branch-bar [data-action="split"], #branch-rail [data-action="split"]'); if (!c) return false; c.click(); return true; });
  await sleep(1500);
  const viaButton = await branchesNow();
  check('the Split button divides the orb too', again && viaButton.count === 2, `clicked=${again} branches=${viaButton.count}`);

  // ---- 5b. switching halves switches workspaces
  // The first half (focused after a split) is asked for the list; the second is fresh. Tapping
  // between them must change what is ON SCREEN, not only who is listening.
  const say = async (text) => {
    await page.evaluate(() => { const s2 = document.querySelector('#settings'), d = document.querySelector('#dev'); if (d) d.hidden = false; if (s2 && !s2.open && s2.showModal) s2.showModal(); });
    await page.fill('#dev-text', text);
    await page.press('#dev-text', 'Enter');
    await sleep(1300);
    await page.evaluate(() => { const s2 = document.querySelector('#settings'); if (s2 && s2.open) s2.close(); });
    await sleep(300);
  };
  await say("show me today's orders");
  const onFirst = await screen();
  const half = await branchesNow();
  const other = half.ids.find((id) => id !== half.focused);
  const tapChip = async (id) => { await page.evaluate((b) => { const c = document.querySelector(`.branch-chip[data-branch="${b}"]`); if (c) c.click(); }, id); await sleep(1500); };
  await tapChip(other);
  const onSecondEmpty = await screen();
  await say('show me order 1938');
  const onSecond = await screen();
  await tapChip(half.focused);
  const backOnFirst = await screen();
  await tapChip(other);
  const backOnSecond = await screen();
  check('the first half shows its list; the fresh half shows nothing of it',
    onFirst.card === 'order_list' && onSecondEmpty.card === '' && onSecondEmpty.mode === 'orb',
    JSON.stringify({ first: onFirst.card, secondEmpty: onSecondEmpty.card, mode: onSecondEmpty.mode, toast: onSecondEmpty.toast }));
  check('each half keeps its own workspace across taps',
    onSecond.card === 'order' && backOnFirst.card === 'order_list' && backOnSecond.card === 'order' && /1938/.test(backOnSecond.ref),
    JSON.stringify({ second: onSecond.card, first: backOnFirst.card, secondAgain: backOnSecond.card, ref: backOnSecond.ref }));
  await shot('04-second-half');

  // ---- 5c. a reload brings the focused half's workspace back from the Mac
  await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1600);
  await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });
  const restored = await screen();
  const restoredChips = await page.evaluate(() => document.querySelectorAll('.branch-chip').length);
  check('after a reload the workspace is back, and both halves with it',
    restored.mode === 'context' && restored.card === 'order' && /1938/.test(restored.ref) && restoredChips === 2,
    JSON.stringify({ mode: restored.mode, card: restored.card, ref: restored.ref, chips: restoredChips }));
  await shot('05-reloaded');

  // ---- 6. an ordinary one-finger hold still records and sends — no delay was added. On the
  // dock band, where the thumb is when cards are up.
  await page.evaluate(() => { const c = document.querySelector('[data-action="cancel"]'); if (c) c.click(); });
  await sleep(1200);
  const pill2 = await page.evaluate(() => { const b = document.querySelector('#talk-label').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
  posts.length = 0;
  await touches('touchStart', [{ x: pill2.x, y: pill2.y }]);
  await sleep(900);
  await touches('touchEnd', []);
  await sleep(2500);
  check('a one-finger hold is still a question', posts.includes('/turn'), `posted: ${posts.join(', ') || 'nothing'}`);

  // ---- 7. tap Reply on a thread: the armed state is on the control, unclipped, cancellable
  await say('which customers need replying to?');
  await page.evaluate(() => { const row = document.querySelector('#cards .row.tappable[data-kind="email_thread"]'); if (row) row.click(); });
  await sleep(1500);
  await page.evaluate(() => { const c = document.querySelector('#cards .rail-chip[data-family="email.reply"]'); if (c) c.click(); });
  await sleep(1400);
  const armed = await page.evaluate(() => {
    const pill = document.querySelector('#cards .armed-inline');
    const band = document.querySelector('#armed');
    const chip = document.querySelector('#cards .rail-chip[data-family="email.reply"]');
    if (!pill) return { pill: false, band: band && !band.hidden ? band.textContent.trim() : '' };
    const what = pill.querySelector('.armed-what');
    const cancel = pill.querySelector('.armed-cancel');
    const pr = pill.getBoundingClientRect(); const wr = what.getBoundingClientRect(); const cr = cancel.getBoundingClientRect();
    const cardR = pill.closest('.card').getBoundingClientRect();
    return {
      pill: true, text: what.textContent.trim(),
      clipped: what.scrollHeight > what.clientHeight + 2 || what.scrollWidth > what.clientWidth + 2,
      insideCard: pr.left >= cardR.left - 1 && pr.right <= cardR.right + 1,
      onScreen: pr.left >= 0 && pr.right <= innerWidth && pr.bottom <= innerHeight,
      afterRail: Boolean(pill.previousElementSibling && pill.previousElementSibling.classList.contains('rail')),
      cancelH: Math.round(cr.height), height: Math.round(pr.height), lines: Math.round(wr.height / 17),
      chipLit: chip ? chip.getAttribute('aria-pressed') === 'true' : false,
    };
  });
  check('tapping Reply arms the control itself, in words about the person', armed.pill && /^Replying to \w+/.test(armed.text) && armed.chipLit, JSON.stringify(armed));
  check('the armed state is attached to the rail, inside the card, on screen, unclipped',
    armed.pill && armed.afterRail && armed.insideCard && armed.onScreen && !armed.clipped && armed.height <= 64, JSON.stringify(armed));
  check('and Cancel is a finger-sized control', armed.pill && armed.cancelH >= 44, `cancel=${armed.cancelH}px`);
  await shot('06-armed-reply');
  await page.evaluate(() => { const c = document.querySelector('#cards .armed-inline .armed-cancel'); if (c) c.click(); });
  await sleep(900);
  const gone = await page.evaluate(() => ({ pill: Boolean(document.querySelector('#cards .armed-inline')), band: Boolean(document.querySelector('#armed') && !document.querySelector('#armed').hidden), listening: document.body.dataset.listeningFor || '' }));
  check('Cancel lets it go', !gone.pill && !gone.band && gone.listening === '', JSON.stringify(gone));

  check('no script error during the whole run', errors.length === 0, errors.slice(0, 3).join(' | '));
  await browser.close();
  const ok = checks.every((c) => c.ok);
  process.stdout.write(`${JSON.stringify({ ok, checks, shots, viewport: '601x889@1.33' })}\n`);
  return ok ? 0 : 1;
}

main().then((code) => process.exit(code)).catch((e) => {
  process.stdout.write(`${JSON.stringify({ ok: false, checks: [{ name: 'tablet run', ok: false, detail: String(e && e.message).slice(0, 400) }], shots })}\n`);
  process.exit(1);
});
