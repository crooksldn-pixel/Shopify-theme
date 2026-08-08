// Corrected sold-out interaction check.
// Run-1's p2-checks removed overlays with '.shopify-pc__banner', which does NOT match
// the banner's real class (shopify-pc__banner__dialog) — every centre-point tap in the
// sequence landed on the banner's button row, in both runs. This script dismisses the
// banner the way a shopper does (Accept), then taps for real, and also records the
// JS-dispatch path so logic and hit-testing are separated.
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';
import fs from 'fs';
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const p = await ctx.newPage();
const errs = [];
p.on('pageerror', e => errs.push(String(e).slice(0, 200)));
await p.goto(BASE + '/products/v2-baggies', { waitUntil: 'load', timeout: 120000 });
await p.waitForTimeout(3000);
const out = { note: 'banner dismissed via Accept, then real taps', errors: errs };
const accept = p.locator('button:has-text("Accept")').first();
out.bannerShown = await accept.isVisible().catch(() => false);
if (out.bannerShown) { await accept.click(); await p.waitForTimeout(600); }
out.hitTestAfterAccept = await p.evaluate(() => [...document.querySelectorAll('.crk-size')].map(btn => {
  const b = btn.getBoundingClientRect();
  const hit = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
  return { size: btn.textContent.trim(), hits: hit === btn || btn.contains(hit) };
}));
const seq = [];
for (const size of ['XS', 'M', 'L']) {
  await p.locator('.crk-size', { hasText: new RegExp(`^${size}$`) }).first().click({ force: true });
  await p.waitForTimeout(900);
  seq.push(await p.evaluate((s) => ({
    tapped: s,
    selectedVariantId: document.querySelector('[name="id"]')?.value,
    stockLine: [...document.querySelectorAll('[data-crk-stockline]')].map(e => e.innerText.trim()),
    buy: (() => { const x = document.querySelector('[data-crk-buy]'); return x && { text: x.innerText.trim(), disabled: x.disabled }; })(),
    sticky: document.querySelector('.crk-stickybar')?.innerText.replace(/\s+/g, ' ').trim(),
    notifyHidden: document.querySelector('[data-crk-notify-panel]')?.hidden,
  }), size));
}
out.tapSequenceAfterAccept = seq;
out.addAttemptOnSoldChoice = await p.evaluate(async () => {
  const id = document.querySelector('[name="id"]')?.value;
  if (!id) return { note: 'variant id empty — form disarmed, nothing to attempt', id };
  const r = await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) });
  return { status: r.status, body: JSON.stringify(await r.json().catch(() => ({}))).slice(0, 200) };
});
fs.writeFileSync('audit/evidence/checks-corrected.json', JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 1));
await browser.close();
