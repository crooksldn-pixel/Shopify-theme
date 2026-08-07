import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';

const out = {};
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const s = await ctx.newPage();
await s.goto(BASE + '/products/3-clives-tee', { waitUntil: 'load', timeout: 120000 });
await s.waitForTimeout(1200);
await s.evaluate(async () => { const id = document.querySelector('[name="id"]')?.value; await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) }); });
await s.close();

// ---- 1. checkout button focus ring, measured from actual pixels ----
{
  const page = await ctx.newPage();
  await page.goto(BASE + '/cart', { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(2500);
  await page.evaluate(() => { document.querySelectorAll('.ctc-overlay').forEach(e => e.remove()); document.querySelectorAll('.shopify-pc__banner').forEach(e => e.remove()); document.body.style.overflow = ''; });
  const btn = page.locator('#checkout').first();
  await btn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  await btn.focus();
  await page.waitForTimeout(400);
  out.checkoutFocus = await page.evaluate(() => {
    const el = document.getElementById('checkout');
    const cs = getComputedStyle(el);
    let n = el.parentElement, pageBg = '';
    while (n) { const c = getComputedStyle(n).backgroundColor; if (c && !/rgba\(0, 0, 0, 0\)/.test(c)) { pageBg = c; break; } n = n.parentElement; }
    return { outline: `${cs.outlineWidth} ${cs.outlineStyle} ${cs.outlineColor}`, outlineOffset: cs.outlineOffset, buttonBg: cs.backgroundColor, buttonColor: cs.color, surroundingBg: pageBg, boxShadow: cs.boxShadow, text: el.innerText.trim() };
  });
  await btn.screenshot({ path: 'audit/screens/verify-checkout-focus.png' }).catch(() => {});
  await page.screenshot({ path: 'audit/screens/verify-cart-checkout-focused.png' });
  console.log('CHECKOUT BUTTON WHEN FOCUSED:', JSON.stringify(out.checkoutFocus, null, 2));
  await page.close();
}

// ---- 2. do horizontal rails scroll the focused item into view? ----
{
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(3000);
  await page.evaluate(() => { document.querySelectorAll('.ctc-overlay').forEach(e => e.remove()); document.querySelectorAll('.shopify-pc__banner').forEach(e => e.remove()); document.body.style.overflow = ''; });

  out.rails = await page.evaluate(() => {
    const report = [];
    const rails = [...document.querySelectorAll('*')].filter(e => e.scrollWidth > e.clientWidth + 8 && e.clientWidth > 100 && getComputedStyle(e).overflowX !== 'visible');
    for (const rail of rails.slice(0, 4)) {
      const items = [...rail.querySelectorAll('a[href], button')];
      const info = { rail: rail.tagName.toLowerCase() + '.' + (typeof rail.className === 'string' ? rail.className.trim().split(/\s+/).slice(0, 2).join('.') : ''), scrollWidth: rail.scrollWidth, clientWidth: rail.clientWidth, items: items.length, hiddenItems: 0, itemLabels: [] };
      const rr = rail.getBoundingClientRect();
      for (const it of items) {
        const r = it.getBoundingClientRect();
        const visible = r.left >= rr.left - 2 && r.right <= rr.right + 2;
        if (!visible) info.hiddenItems++;
        info.itemLabels.push(((it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18) || '(img)') + (visible ? '' : ' [OFF-RAIL]'));
      }
      report.push(info);
    }
    return report;
  });
  console.log('\nHORIZONTAL RAILS:', JSON.stringify(out.rails, null, 2));

  // focus the last item of the first rail and see whether the rail scrolls
  out.railFocusTest = await page.evaluate(async () => {
    const rail = [...document.querySelectorAll('*')].find(e => e.scrollWidth > e.clientWidth + 8 && e.clientWidth > 100 && getComputedStyle(e).overflowX !== 'visible');
    if (!rail) return null;
    const items = [...rail.querySelectorAll('a[href], button')];
    const last = items.at(-1);
    const before = rail.scrollLeft;
    last.focus();
    await new Promise(r => setTimeout(r, 500));
    const after = rail.scrollLeft;
    const rr = rail.getBoundingClientRect(), lr = last.getBoundingClientRect();
    return { rail: rail.className, item: (last.innerText || '').trim().slice(0, 20), scrollLeftBefore: before, scrollLeftAfter: after, railScrolled: after !== before, itemNowVisible: lr.left >= rr.left - 2 && lr.right <= rr.right + 2 };
  });
  console.log('\nRAIL FOCUS TEST:', JSON.stringify(out.railFocusTest, null, 2));
  await page.close();
}

// ---- 3. cookie banner geometry + does it cover the sticky buy bar? ----
{
  const page = await ctx.newPage();
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(3000);
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.5));
  await page.waitForTimeout(1200);
  out.cookieBanner = await page.evaluate(() => {
    const b = document.querySelector('.shopify-pc__banner, [class*="shopify-pc__banner"]');
    const bar = document.querySelector('.crk-stickybar');
    const g = e => { if (!e) return null; const r = e.getBoundingClientRect(); return { top: Math.round(r.top), bottom: Math.round(r.bottom), h: Math.round(r.height), z: getComputedStyle(e).zIndex, pos: getComputedStyle(e).position }; };
    const B = g(b), S = g(bar);
    return { viewportH: innerHeight, banner: B, stickyBar: S, bannerCoversPctOfViewport: B ? Math.round(100 * B.h / innerHeight) : 0, overlaps: B && S ? !(B.bottom <= S.top || B.top >= S.bottom) : null, bannerText: b ? b.innerText.replace(/\s+/g, ' ').slice(0, 120) : null };
  });
  console.log('\nCOOKIE BANNER vs STICKY BUY BAR:', JSON.stringify(out.cookieBanner, null, 2));
  await page.screenshot({ path: 'audit/screens/verify-cookiebanner-over-buybar.png' });
  await page.close();
}

// ---- 4. confirm the "keyboard trap" is the Shopify preview bar, not the theme ----
{
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(2500);
  out.previewBar = await page.evaluate(() => {
    const f = document.querySelector('#PBarNextFrame, iframe[id*="PBar"]');
    return f ? { present: true, id: f.id, src: (f.src || '').slice(0, 80), note: 'Shopify theme-preview bar. Injected only by the share-preview session; absent on the published theme.' } : { present: false };
  });
  console.log('\nPREVIEW BAR:', JSON.stringify(out.previewBar, null, 2));
  await page.close();
}

fs.writeFileSync('audit/evidence/verify.json', JSON.stringify(out, null, 2));
console.log('\nwrote audit/evidence/verify.json');
await browser.close();
