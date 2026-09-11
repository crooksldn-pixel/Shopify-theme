/* Does anything on this screen sit on top of anything else? Measured, in Chromium.
 *
 * The live tablet session recorded `clipped=0` on every render while the owner was looking at
 * overlapping text and controls, and said so out loud. `clipped` was one subtraction on one
 * card — scrollWidth against clientWidth — which cannot see two boxes that are each the right
 * size and in the same place. This file does not ask the page how it thinks it is doing. It
 * renders the worst data the shop can produce, reads every rectangle with
 * getBoundingClientRect(), and reports the pairs that collide (web/collide.js).
 *
 *   node scripts/browser/collision.js http://127.0.0.1:8765 [/path/to/screenshots]
 *
 * Two sizes, because a defect is a defect at the size the tablet actually is:
 *   601 × 889 at DPR 1.33 — the Galaxy Tab A 8.0 in the owner's hand
 *   800 × 1280 at DPR 1   — the gate's own portrait
 *
 * Fifteen fixtures, every one a value a real shop has: a customer with a very long name, an
 * eighty-character email address, a four-line postal address, a long SKU, a long tracking
 * number, a product title that does not fit, a subject that does not fit, a note with five
 * paragraphs in it, a total in the millions, nine status chips, five actions, the split, the
 * keyboard open, three notifications at once. Every one of them is DATA, handed to the page's
 * own renderer (window.CrooksUI) — nothing here builds markup, and nothing here can, because
 * the renderer only draws the types it knows.
 *
 * Prints one JSON object: { ok, checks: [{name, ok, detail}], viewports, cases, shots }.
 */
'use strict';

const { chromium } = require('playwright-core');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = process.argv[3] || '';
const HEADERS = { 'Tailscale-User-Login': 'owner@example.com', 'X-Forwarded-For': '100.64.0.9' };

// The tablet's own size first: it is the one the owner holds, and the one that finds the faults.
const VIEWPORTS = [
  { name: '601x889@1.33', width: 601, height: 889, dpr: 1.33 },
  { name: '800x1280@1', width: 800, height: 1280, dpr: 1 },
];

const checks = [];
const shots = [];
const check = (name, ok, detail) => checks.push({ name, ok: Boolean(ok), detail: detail === undefined ? '' : String(detail).slice(0, 400) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------- the stress values

const LONG_NAME = 'Alexandra Wilhelmina Constance Featherstonehaugh-Beauchamp';
const LONG_EMAIL = 'alexandra.wilhelmina.featherstonehaugh@a-very-long-department.example.com';
const LONG_TITLE = 'Blue Wash Selvedge Yard Jeans — Relaxed Straight, Unwashed, Limited Workshop Run 2026';
const LONG_SKU = 'CRK-YJ-BLUWASH-RELAXSTR-W34L32-SS26-LTD-000418-A';
const LONG_TRACK = 'AB0000000012345678901234567890GB';
const LONG_SUBJECT = 'Re: Re: Fwd: order 1938 — the jeans arrived in the wrong wash and the sweats are a size out, what do we do about the return postage';
const LONG_ADDRESS = {
  name: LONG_NAME,
  lines: ['Flat 14, Featherstonehaugh Mansions', '221b Upper Kennington Park Road South', 'Behind the old brewery yard'],
  city: 'Kingston upon Thames', zip: 'KT1 2AB', country: 'United Kingdom', country_code: 'GB',
};
const LONG_NOTE = 'Customer rang twice about this one.\n\nWants the exchange sent to the work address, not the home one, and the original collected on the same visit if the courier can do that.\n\nSaid the sweats were fine, it is only the jeans.\n\nIf the exchange cannot be done this week he would rather have the refund.';
const BIG_MONEY = '£1,284,367.45';

const CHIPS = ['vip', 'wholesale', 'repeat-return', 'fraud-checked', 'gift-wrap', 'pre-order', 'back-order', 'priority', 'staff-discount'];

const ACTIONS_FIVE = [
  { id: 'note', label: 'Note', operation: 'order_note_append', risk: 'amber', enabled: true, reason: '', instruction: 'Add a note', mode: 'ask', family: 'order.add_note' },
  { id: 'address', label: 'Change the delivery address', operation: 'order_shipping_address_set', risk: 'red', enabled: true, reason: '', instruction: 'Change the address', mode: 'ask' },
  { id: 'fulfil', label: 'Mark as shipped', operation: 'fulfillment_create', risk: 'red', enabled: true, reason: '', instruction: 'Mark shipped', mode: 'ask' },
  { id: 'refund', label: 'Refund', operation: 'refund_create', risk: 'red', enabled: true, reason: '', instruction: 'Refund', mode: 'ask' },
  { id: 'cancel', label: 'Cancel and refund the whole order', operation: 'order_cancel', risk: 'red', enabled: false, reason: 'a label has already been printed for this one', instruction: 'Cancel', mode: 'ask' },
];

function order(extra) {
  return Object.assign({
    order_id: 'gid://shopify/Order/0', order_number: '#1938', placed_at: '2026-09-08T09:42:00Z',
    fulfillment: 'unfulfilled', payment: 'paid', total: '£145.00',
    customer_name: 'Sam Fixture', customer_id: 'gid://shopify/Customer/0', customer_email: 'sam@example.com',
    detail: true, tags: ['vip'],
    items: [{ title: 'Yard Jeans', variant: 'M', sku: 'YJ-BLU-M', quantity: 1, total: '£95.00', stock: { tracked: true, available: 3 } }],
    items_truncated: false, fulfillments: [],
    money: { subtotal: '£140.00', shipping: '£5.00', tax: '£23.33', discounts: '£0.00', refunded: '£0.00', outstanding: '£0.00' },
    shipping_method: 'Royal Mail Tracked 24',
    shipping_address: { name: 'Sam Fixture', lines: ['12 Somewhere Street'], city: 'London', zip: 'E1 6AN', country: 'United Kingdom', country_code: 'GB' },
    history: { orders: 4, spent: '£410.00', standing: 'regular', recent: [] },
    email: { available: true, threads: [] }, pending: [],
    actions: [{ id: 'note', label: 'Note', operation: 'order_note_append', risk: 'amber', enabled: true, reason: '', instruction: 'Add a note', mode: 'ask', family: 'order.add_note' }],
    cancelled_at: '', note: '', ships_to: 'London, United Kingdom',
  }, extra || {});
}

function confirmation(facts, extra) {
  return Object.assign({
    proposal_id: 'prop_collide00001', status: 'pending', risk: 'red', operation: 'fulfillment_create',
    title: 'Mark as shipped', entity: 'Order #1938', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0',
    summary: '', detail: 'Marks every item shipped.', facts,
    interaction: { kind: 'hold_to_arm', label: 'Hold to arm, then tap', footer: 'nothing happens until you hold the card, then tap it', armed_after_ms: 650 },
    ttl_s: 60, reversible: false, commit: { allowed: true },
  }, extra || {});
}

// Every case is a name and a `ui` list. The renderer decides what any of it looks like.
const CASES = [
  { id: 'long_customer_name', ui: [{ type: 'order', data: order({ customer_name: LONG_NAME, shipping_address: Object.assign({}, LONG_ADDRESS, { lines: ['12 Somewhere Street'] }) }) }] },
  { id: 'long_email_address', ui: [{ type: 'order', data: order({ customer_email: LONG_EMAIL, email: { available: true, threads: [{ thread_id: 't1', from: LONG_NAME, from_email: LONG_EMAIL, subject: 'Re: #1938', date: 'Tue, 8 Sep 2026 10:12:00 +0100', snippet: 'Where is it?', verified_sender: true, match: 'both', provenance: 'CUSTOMER_EMAIL' }] } }) }] },
  { id: 'long_postal_address', ui: [{ type: 'order', data: order({ shipping_address: LONG_ADDRESS, ships_to: 'Kingston upon Thames, United Kingdom' }) }] },
  { id: 'long_sku', ui: [{ type: 'order', data: order({ items: [{ title: 'Yard Jeans', variant: 'W34 / L32 / Unwashed', sku: LONG_SKU, quantity: 1, total: '£95.00', stock: { tracked: true, available: 3 } }] }) }] },
  { id: 'long_product_title', ui: [{ type: 'order', data: order({ items: [{ title: LONG_TITLE, variant: 'W34 / L32', sku: LONG_SKU, quantity: 2, total: BIG_MONEY, stock: { tracked: true, available: 0 } }] }) }] },
  { id: 'long_tracking_number', ui: [{ type: 'confirmation', data: confirmation([{ label: 'Items', value: LONG_TITLE }, { label: 'Carrier', value: 'Royal Mail Tracked 24 (signed for)' }, { label: 'Tracking', value: LONG_TRACK }, { label: 'Customer emailed', value: 'no' }]) }] },
  { id: 'long_subject', ui: [{ type: 'email_thread', data: { thread_id: 't1', subject: LONG_SUBJECT, message_count: 2, truncated: false, messages: [
    { from: LONG_NAME, from_email: LONG_EMAIL, date: 'Sun, 6 Sep 2026 18:30:00 +0100', subject: LONG_SUBJECT, body: 'The jeans arrived in the wrong wash.' },
    { from: LONG_NAME, from_email: LONG_EMAIL, date: 'Tue, 8 Sep 2026 10:12:00 +0100', subject: LONG_SUBJECT, body: LONG_NOTE },
  ], actions: [{ id: 'reply', label: 'Reply', enabled: true, risk: 'amber', mode: 'ask', family: 'email.reply', instruction: 'Reply' }, { id: 'email_archive', label: 'Archive', enabled: true, risk: 'amber', mode: 'stage' }] } }] },
  { id: 'multi_line_note', ui: [{ type: 'order', data: order({ note: LONG_NOTE }) }] },
  { id: 'large_currency', ui: [{ type: 'order', data: order({ total: BIG_MONEY, money: { subtotal: BIG_MONEY, shipping: '£12,000.00', tax: '£214,061.24', discounts: '£99,999.99', refunded: '£1,000,000.00', outstanding: BIG_MONEY } }) }] },
  { id: 'many_status_chips', ui: [{ type: 'order', data: order({ tags: CHIPS, payment: 'partially_refunded', fulfillment: 'partial', cancelled_at: '' }) }] },
  { id: 'five_actions', ui: [{ type: 'order', data: order({ customer_name: LONG_NAME, actions: ACTIONS_FIVE }) }] },
  { id: 'composer', ui: [{ type: 'email_compose', data: {
    compose_id: 'cmp_collide1', kind: 'new', about: LONG_SUBJECT,
    to: { value: LONG_EMAIL, status: 'invalid', hint: 'That does not look like an email address.' },
    subject: { value: LONG_SUBJECT, status: 'uncertain', hint: 'Heard rather than typed — look at it.' },
    body: { value: LONG_NOTE, status: 'ok', hint: '' },
    original: LONG_NOTE,
    actions: [{ id: 'draft', label: 'Save as a draft', mode: 'stage', risk: 'amber' }, { id: 'send', label: 'Send it now', mode: 'stage', risk: 'red' }, { id: 'discard', label: 'Throw it away', mode: 'discard', risk: 'amber' }],
  } }] },
  { id: 'workspace', ui: [{ type: 'workspace', data: {
    workspace_id: 'ws_collide1', kicker: 'Not created yet', title: 'A discount code', subtitle: LONG_SUBJECT,
    field_command: 'workspace.field', choose_command: 'workspace.choose',
    facts: [{ label: 'Customer', value: LONG_NAME }, { label: 'Email', value: LONG_EMAIL }, { label: 'Value', value: BIG_MONEY, tone: 'warn' }],
    fields: [{ name: 'code', kind: 'text', label: 'Code', value: LONG_SKU, status: 'ok', hint: '' }, { name: 'note', kind: 'text', label: 'Note', value: LONG_NOTE, status: 'uncertain', hint: 'Heard rather than typed.', rows: 4 }],
    choices: [{ name: 'kind', label: 'What kind', options: [{ id: 'pct', label: 'A percentage off', selected: true }, { id: 'fixed', label: 'A fixed amount off' }, { id: 'ship', label: 'Free delivery' }] }],
    notes: ['Nothing exists in the shop until the card that follows is authorised.'],
    actions: [{ id: 'prepare', label: 'Prepare the change', command: 'workspace.prepare', args: 'workspace_id=ws_collide1', enabled: true, risk: 'amber' }, { id: 'discard', label: 'Throw it away', command: 'workspace.discard', args: 'workspace_id=ws_collide1', enabled: false, risk: 'amber' }],
  } }] },
  // Everything at once, which is how a workbench screen actually looks.
  { id: 'everything', ui: [
    { type: 'order', data: order({ customer_name: LONG_NAME, customer_email: LONG_EMAIL, tags: CHIPS, note: LONG_NOTE, total: BIG_MONEY, shipping_address: LONG_ADDRESS, actions: ACTIONS_FIVE, items: [{ title: LONG_TITLE, variant: 'W34 / L32', sku: LONG_SKU, quantity: 2, total: BIG_MONEY, stock: { tracked: true, available: 0 } }] }) },
    { type: 'confirmation', data: confirmation([{ label: 'Tracking', value: LONG_TRACK }, { label: 'To', value: LONG_EMAIL }]) },
  ] },
];

// ---------------------------------------------------------------- the run

async function main() {
  const viewports = [];
  const caseNames = CASES.map((c) => c.id).concat(['split_mode', 'keyboard_open', 'multiple_notifications']);
  const browser = await chromium.launch({ executablePath: process.env.CROOKS_CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  try {
    for (const vp of VIEWPORTS) {
      await one(browser, vp);
      viewports.push(vp.name);
    }
  } finally {
    await browser.close();
  }
  const ok = checks.every((c) => c.ok);
  process.stdout.write(`${JSON.stringify({ ok, checks, shots, viewports, cases: caseNames })}\n`);
  return ok ? 0 : 1;
}

async function one(browser, vp) {
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
    errors.push(`console: ${m.text()}`);
  });
  await page.route('**/speak', (r) => r.fulfill({ status: 503, contentType: 'application/json', body: '{"ok":false,"kind":"no_key","reason":"no voice under test"}' }));

  await page.goto(`${BASE}?dev=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(900);
  // The developer banner is a fixed strip over the top of the page that production never
  // shows. Leaving it in would be a collision this file invented.
  await page.evaluate(() => { for (const b of document.querySelectorAll('.dev-banner')) b.remove(); });

  const armed = await page.evaluate(() => Boolean(window.CrooksCollide && window.CrooksUI && window.CrooksUI.render));
  check(`${vp.name} · the page carries its renderer and its own geometry check`, armed, 'window.CrooksUI + window.CrooksCollide');
  if (!armed) { await context.close(); return; }

  // Draw through the app's own deck and the app's own renderer, exactly as the page does.
  await page.evaluate(() => {
    window.__collideDraw = (items) => {
      const root = document.querySelector('#cards');
      if (!root) return { nodes: 0, skipped: ['no deck'] };
      const out = window.CrooksUI.render(items, {});
      root.replaceChildren();
      out.nodes.forEach((n) => root.appendChild(n));
      document.body.dataset.mode = 'context';
      return { nodes: out.nodes.length, skipped: out.skipped };
    };
  });

  const results = [];
  const measure = async (id) => {
    const scan = await page.evaluate(() => window.CrooksCollide.scan({}));
    results.push({ id, scan });
    return scan;
  };

  // ---- the fixtures, one at a time
  for (const item of CASES) {
    const drawn = await page.evaluate((items) => window.__collideDraw(items), item.ui);
    if (!drawn.nodes) { check(`${vp.name} · ${item.id} renders`, false, `nodes=${drawn.nodes} skipped=${(drawn.skipped || []).join(',')}`); continue; }
    await page.waitForTimeout(140);
    // Open everything a tap would open, so the measurement covers the folded-away parts too:
    // a tab that has never been selected has never been laid out.
    await page.evaluate(() => {
      for (const t of document.querySelectorAll('#cards [role="tab"]')) t.click();
      for (const f of document.querySelectorAll('#cards .fold-head')) f.click();
    });
    await page.waitForTimeout(140);
    await measure(item.id);
  }
  await shot(page, `collide-${vp.width}-cards`);

  // ---- the split: two halves, the branch selector on screen, and a message about one of them
  await page.evaluate(() => {
    const split = document.querySelector('#branch-bar [data-action="split"], #branch-rail [data-action="split"]');
    if (split) split.click();
  });
  await sleep(1800);
  await measure('split_mode');
  await shot(page, `collide-${vp.width}-split`);

  // ---- three notifications at once, through whatever the page provides
  const noted = await page.evaluate(() => {
    if (window.CrooksNotify && typeof window.CrooksNotify.show === 'function') {
      window.CrooksNotify.show({ text: 'Draft saved in Gmail drafts.', class: 'workspace', tone: 'good', code: 'draft_saved' });
      window.CrooksNotify.show({ text: 'Archive verified on the Mac.', class: 'workspace', tone: 'good', code: 'archive_verified' });
      window.CrooksNotify.show({ text: 'The Mac cannot be reached. Nothing is lost; it will answer when it is back.', class: 'global', tone: 'bad', code: 'backend_down', machine: true });
      return 'notify';
    }
    // The old way: one floating bubble, which is the thing this run is here to measure.
    const node = document.querySelector('#toast');
    if (!node) return 'none';
    node.textContent = 'Merged. 2 changes still waiting over there.';
    node.hidden = false;
    return 'toast';
  });
  await page.waitForTimeout(200);
  await measure('multiple_notifications');
  await shot(page, `collide-${vp.width}-notifications`);

  // ---- the keyboard: `interactive-widget=resizes-content` shrinks the viewport, so this is
  // the same thing the tablet does when a finger lands in a field.
  await page.evaluate((items) => window.__collideDraw(items), CASES.find((c) => c.id === 'composer').ui);
  await page.waitForTimeout(160);
  await page.setViewportSize({ width: vp.width, height: Math.round(vp.height * 0.47) });
  await page.waitForTimeout(220);
  await page.evaluate(() => { const f = document.querySelector('#cards .field-input'); if (f && f.focus) f.focus(); });
  await page.waitForTimeout(260);
  await measure('keyboard_open');
  await shot(page, `collide-${vp.width}-keyboard`);
  await page.setViewportSize({ width: vp.width, height: vp.height });
  await page.waitForTimeout(160);

  // ---- one check per rule, naming every fixture that broke it
  const RULES = await page.evaluate(() => window.CrooksCollide.RULES);
  const WORDS = {
    control_over_control: 'no interactive control overlaps another',
    text_over_control: 'no text overlaps an action control',
    notification_over_chrome: 'no notification overlaps the dock, the orb or the halves',
    rail_over_content: 'no action rail overlaps content',
    document_overflow_x: 'nothing scrolls the page sideways by accident',
    folded_action: 'no action is folded away to nothing',
    content_under_chrome: 'nothing essential is hidden under the fixed furniture',
  };
  for (const rule of RULES) {
    const bad = results.filter((r) => (r.scan.counts || {})[rule]);
    const detail = bad.map((r) => {
      const hit = (r.scan.hits || []).find((x) => x.rule === rule) || {};
      return `${r.id}: ${(r.scan.counts || {})[rule]}× ${hit.a || ''}[${hit.at || ''}]${hit.b ? ` / ${hit.b}[${hit.bt || ''}]` : ''}${hit.note ? ` (${hit.note})` : ''}`;
    }).join(' | ');
    check(`${vp.name} · ${WORDS[rule] || rule}`, bad.length === 0, detail);
  }

  // ---- and the thumb (section 29), from the same rectangles
  const small = [];
  for (const r of results) {
    for (const t of r.scan.touch || []) {
      if (!small.some((s) => s.sel === t.sel)) small.push({ id: r.id, sel: t.sel, w: t.w, h: t.h });
    }
  }
  check(`${vp.name} · every control a finger uses is about 44px`, small.length === 0,
    small.map((s) => `${s.sel} ${s.w}×${s.h} (${s.id})`).join(', '));

  check(`${vp.name} · every fixture was measured`, results.length === CASES.length + 3,
    `${results.length} of ${CASES.length + 3}: ${results.map((r) => r.id).join(',')}`);
  check(`${vp.name} · the notification path is the one the page owns`, noted === 'notify', `via ${noted}`);
  check(`${vp.name} · no script error while measuring`, errors.length === 0, errors.slice(0, 3).join(' | '));
  await context.close();
}

async function shot(page, name) {
  if (!OUT) return;
  const file = path.join(OUT, `${name}.png`);
  await page.waitForTimeout(320);
  await page.screenshot({ path: file, fullPage: false, animations: 'disabled' });
  shots.push(path.basename(file));
}

main().then((code) => process.exit(code)).catch((e) => {
  process.stdout.write(`${JSON.stringify({ ok: false, checks: [{ name: 'collision run', ok: false, detail: String(e && e.message).slice(0, 400) }], shots })}\n`);
  process.exit(1);
});
