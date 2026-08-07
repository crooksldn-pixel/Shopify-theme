import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const out = {};

// --- 1. measurement tables across every product: placeholder or real? ---
const handles = ['cb2-wash-jeans', 'cb1-wash-jeans', 'cb1-wash-jorts', 'cb2-wash-jorts', 'v2-baggies', 'charcoal-cellblock-crewneck', 'charcoal-cellblock-shorts', '3-clives-tee', 'broadcast-tee', 'large-duffle-bag', 'white-socks'];
out.measurements = {};
for (const h of handles) {
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/' + h, { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2200);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.querySelectorAll('.crk-section-head').forEach(x => { if (x.getAttribute('aria-expanded') === 'false') x.click(); }); });
  await p.waitForTimeout(500);
  out.measurements[h] = await p.evaluate(() => {
    const body = document.body.innerText.replace(/\s+/g, ' ');
    const m = body.match(/GARMENT LAID FLAT[^]*?(?=CHAIN OF CUSTODY|FILED UNDER)/);
    const spec = body.match(/SPECIFICATION − ([^]*?)(?=STATEMENT OF PROVENANCE)/);
    return { title: document.querySelector('h1, .crk-h1')?.innerText.trim(), table: m ? m[0].trim().slice(0, 300) : null, spec: spec ? spec[1].trim().slice(0, 200) : null };
  });
  await p.close();
}
console.log('=== MEASUREMENT TABLES ===');
for (const [h, v] of Object.entries(out.measurements)) {
  console.log(`\n${h}  "${v.title}"`);
  console.log(`   spec: ${v.spec}`);
  console.log(`   ${v.table || '(no measurement table)'}`);
}

// --- 2. sold-out variant presentation on V2 BAGGIES ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/v2-baggies', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  out.soldOutVisual = await p.evaluate(() => [...document.querySelectorAll('.crk-size')].map(b => {
    const cs = getComputedStyle(b);
    return { label: b.innerText.trim(), classes: b.className, ariaDisabled: b.getAttribute('aria-disabled'), disabled: b.disabled, color: cs.color, bg: cs.backgroundColor, border: cs.borderColor, opacity: cs.opacity, textDecoration: cs.textDecorationLine, pointerEvents: cs.pointerEvents };
  }));
  console.log('\n=== V2 BAGGIES SIZE BUTTONS (M, L, XL are sold out) ===');
  for (const b of out.soldOutVisual) console.log(`  ${b.label.padEnd(3)} aria-disabled=${String(b.ariaDisabled).padEnd(5)} disabled=${b.disabled} colour=${b.color} bg=${b.bg} border=${b.border} opacity=${b.opacity} strike=${b.textDecoration}`);

  // what actually happens when a shopper taps a sold-out size
  const seq = [];
  for (const size of ['XS', 'M', 'L']) {
    await p.locator('.crk-size', { hasText: new RegExp(`^${size}$`) }).first().click({ force: true });
    await p.waitForTimeout(900);
    seq.push(await p.evaluate((s) => ({
      tapped: s,
      stickybar: document.querySelector('.crk-stickybar')?.innerText.replace(/\s+/g, ' ').trim(),
      buyButton: document.querySelector('.crk-btn')?.innerText.trim(),
      buyDisabled: document.querySelector('.crk-btn')?.disabled,
      stockLine: [...document.querySelectorAll('.crk-data, .crk-display, [class*="stock"]')].map(e => e.innerText.replace(/\s+/g, ' ').trim()).filter(t => /stock|sold/i.test(t)).slice(0, 3),
      selectedVariantId: document.querySelector('[name="id"]')?.value,
      pressed: [...document.querySelectorAll('.crk-size')].map(b => b.innerText.trim() + ':' + (b.getAttribute('aria-pressed') || b.className.includes('is-') ? 'sel' : '-')),
    }), size));
  }
  out.soldOutTapSequence = seq;
  console.log('\n=== TAPPING SIZES ON A PART-SOLD-OUT PRODUCT ===');
  for (const s of seq) console.log(`  tapped ${s.tapped}: sticky="${s.stickybar}"  buy="${s.buyButton}" disabled=${s.buyDisabled}  variantId=${s.selectedVariantId}  stock=${JSON.stringify(s.stockLine)}`);
  await p.screenshot({ path: 'audit/screens/check-soldout-v2baggies.png' });

  // can a sold-out size actually be added to the cart?
  out.soldOutAddAttempt = await p.evaluate(async () => {
    const id = document.querySelector('[name="id"]')?.value;
    const r = await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) });
    const j = await r.json().catch(() => ({}));
    return { status: r.status, variantAttempted: id, response: JSON.stringify(j).slice(0, 300) };
  });
  console.log('\n  add-to-cart with that variant selected:', JSON.stringify(out.soldOutAddAttempt));
  await p.close();
}

// --- 3. what does the SIZE GUIDE button do? ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  const before = await p.evaluate(() => ({ y: scrollY, dialogs: document.querySelectorAll('dialog[open]').length }));
  await p.locator('.crk-textbtn', { hasText: /SIZE GUIDE/i }).first().click();
  await p.waitForTimeout(1400);
  const after = await p.evaluate(() => ({ y: scrollY, dialogs: document.querySelectorAll('dialog[open]').length, measureVisible: (() => { const m = [...document.querySelectorAll('*')].find(e => /GARMENT LAID FLAT/.test(e.innerText || '') && e.children.length < 4); if (!m) return null; const r = m.getBoundingClientRect(); return { top: Math.round(r.top), inViewport: r.top >= 0 && r.top < innerHeight }; })() }));
  out.sizeGuideButton = { before, after, behaviour: after.dialogs > before.dialogs ? 'opens dialog' : after.y !== before.y ? `scrolls page ${after.y - before.y}px` : 'no visible effect' };
  console.log('\n=== SIZE GUIDE BUTTON ===', JSON.stringify(out.sizeGuideButton));
  await p.screenshot({ path: 'audit/screens/check-sizeguide-click.png' });
  await p.close();
}

// --- 4. what is RELEASE REQUEST? ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  out.releaseRequest = await p.evaluate(() => {
    const el = [...document.querySelectorAll('*')].find(e => (e.innerText || '').trim() === 'RELEASE REQUEST' && e.children.length === 0);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const p2 = el.closest('button, a, label, fieldset, div');
    return { tag: el.tagName, cls: el.className, size: [Math.round(r.width), Math.round(r.height)], parentTag: p2?.tagName, parentCls: p2?.className, isInteractive: !!el.closest('button,a'), context: p2?.parentElement?.innerText.replace(/\s+/g, ' ').trim().slice(0, 160) };
  });
  console.log('\n=== "RELEASE REQUEST" ===', JSON.stringify(out.releaseRequest, null, 1));
  await p.close();
}

// --- 5. delivery-time contradiction, gathered per product ---
out.deliveryClaims = {};
for (const h of ['cb2-wash-jeans', '3-clives-tee', 'charcoal-cellblock-crewneck']) {
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/' + h, { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2200);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.querySelectorAll('.crk-section-head').forEach(x => { if (x.getAttribute('aria-expanded') === 'false') x.click(); }); });
  await p.waitForTimeout(500);
  out.deliveryClaims[h] = await p.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    const grab = re => { const m = t.match(re); return m ? m[0].trim() : null; };
    return {
      announcement: grab(/FREE UK SHIPPING[^A-Z]*[^]{0,40}?DISPATCH AVAILABLE/),
      stockLine: grab(/In stock · [^A-Z]{0,40}/),
      provenance: grab(/\d+\s*-\s*\d+ days delivery uk[^]{0,50}/i),
      chainOfCustody: grab(/UK \d[^.]*\. International [^.]*\./),
      returnWindow: grab(/You have \d+ days from delivery[^.]*\./),
    };
  });
  await p.close();
}
console.log('\n=== DELIVERY CLAIMS PER PDP ===');
for (const [h, v] of Object.entries(out.deliveryClaims)) { console.log(`\n  ${h}`); for (const [k, val] of Object.entries(v)) console.log(`     ${k.padEnd(16)} ${val}`); }

fs.writeFileSync('audit/evidence/checks.json', JSON.stringify(out, null, 2));
await browser.close();
