import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';

const PAGES = [
  ['home', BASE + '/', 'Homepage'],
  ['pdpDenim', BASE + '/products/cb2-wash-jeans', 'PDP — BLUE WASH OG JEANS'],
  ['cart', BASE + '/cart', 'Cart'],
  ['collection', BASE + '/collections/all', 'Collection'],
];

const contrastOf = (a, b) => {
  const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = c => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
  const l1 = lum(a), l2 = lum(b);
  return +(((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)).toFixed(2));
};
const rgb = s => (s.match(/\d+/g) || []).slice(0, 3).map(Number);

const out = { generated: new Date().toISOString(), pages: {} };
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const s = await ctx.newPage();
await s.goto(BASE + '/products/3-clives-tee', { waitUntil: 'load', timeout: 120000 });
await s.waitForTimeout(1200);
await s.evaluate(async () => { const id = document.querySelector('[name="id"]')?.value; await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) }); });
await s.close();

for (const [key, url, label] of PAGES) {
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(2500);
  await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } }); document.querySelectorAll('.ctc-overlay').forEach(e => e.remove()); document.body.style.overflow = ''; });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);

  const stops = [];
  const MAX = 140;
  let verdict = 'completed traversal';
  for (let i = 0; i < MAX; i++) {
    await page.keyboard.press('Tab');
    await page.waitForTimeout(45); // let focus-scroll settle before measuring position
    const st = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return { sel: '(document body)', end: true };
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const outlineOn = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0;
      // effective background behind the focused element
      let n = el, bg = 'rgb(255, 255, 255)';
      while (n) { const c = getComputedStyle(n).backgroundColor; if (c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) { bg = c; break; } n = n.parentElement; }
      let hiddenAncestor = false;
      for (let a = el; a; a = a.parentElement) { const c = getComputedStyle(a); if (c.display === 'none' || c.visibility === 'hidden') { hiddenAncestor = true; break; } }
      return {
        sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id.slice(0, 24) : '') + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''),
        text: (el.innerText || el.getAttribute('aria-label') || el.value || '').replace(/\s+/g, ' ').trim().slice(0, 32),
        outlineOn, outlineColor: cs.outlineColor, outlineWidth: cs.outlineWidth,
        boxShadow: cs.boxShadow !== 'none',
        bg,
        onScreen: r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight,
        hiddenAncestor,
        size: [Math.round(r.width), Math.round(r.height)],
      };
    });
    if (st.end) { verdict = `focus left the page (browser chrome) after ${stops.length} stops — no trap`; break; }
    stops.push(st);
    // real trap detection: the SAME element (selector + text + size) focused 4x in a row
    if (stops.length >= 4) {
      const k = x => x.sel + '|' + x.text + '|' + x.size.join('x');
      const last4 = stops.slice(-4).map(k);
      if (new Set(last4).size === 1) { verdict = `TRAP — focus stuck on ${stops.at(-1).sel}`; break; }
    }
    // full cycle back to the first stop = normal wrap
    if (stops.length > 5 && stops.at(-1).sel === stops[0].sel && stops.at(-1).text === stops[0].text) { verdict = `wrapped to first stop after ${stops.length - 1} stops — no trap`; break; }
  }

  const invisible = stops.filter(x => x.outlineOn && contrastOf(rgb(x.outlineColor), rgb(x.bg)) < 3);
  const noIndicator = stops.filter(x => !x.outlineOn && !x.boxShadow);
  const hidden = stops.filter(x => x.hiddenAncestor);
  const offscreen = stops.filter(x => !x.onScreen && !x.hiddenAncestor && !/skip/i.test(x.sel));

  out.pages[key] = {
    label, url, totalStops: stops.length, verdict,
    cookieBannerStopsFirst: stops.slice(0, 4).filter(x => /shopify-pc__banner/.test(x.sel)).length,
    focusRing: [...new Set(stops.filter(x => x.outlineOn).map(x => `${x.outlineWidth} ${x.outlineColor} on ${x.bg} = ${contrastOf(rgb(x.outlineColor), rgb(x.bg))}:1`))],
    invisibleFocusRing: [...new Set(invisible.map(x => `${x.sel} — ${x.outlineWidth} ${x.outlineColor} on ${x.bg} = ${contrastOf(rgb(x.outlineColor), rgb(x.bg))}:1`))].slice(0, 12),
    invisibleCount: invisible.length,
    noIndicatorAtAll: [...new Set(noIndicator.map(x => x.sel))],
    focusOnHiddenElements: [...new Set(hidden.map(x => x.sel))],
    focusOffscreenAfterSettle: [...new Set(offscreen.map(x => x.sel))],
    order: stops.map((x, i) => `${i + 1}. ${x.sel}${x.text ? ' "' + x.text + '"' : ''} [${x.outlineOn ? x.outlineWidth + ' ' + x.outlineColor + ' → ' + contrastOf(rgb(x.outlineColor), rgb(x.bg)) + ':1' : x.boxShadow ? 'box-shadow' : 'NO INDICATOR'}]`),
  };
  const o = out.pages[key];
  console.log(`\n[${key}] ${o.totalStops} stops — ${o.verdict}`);
  console.log(`  cookie banner occupies first ${o.cookieBannerStopsFirst} tab stops`);
  console.log(`  focus rings in use: ${o.focusRing.join(' | ')}`);
  console.log(`  INVISIBLE focus ring (<3:1) on ${o.invisibleCount} stops: ${o.invisibleFocusRing.slice(0, 4).join(' ; ')}`);
  console.log(`  no indicator at all: ${o.noIndicatorAtAll.join(', ') || 'none'}`);
  console.log(`  focus on display:none/hidden: ${o.focusOnHiddenElements.join(', ') || 'none'}`);
  console.log(`  focus offscreen after settle: ${o.focusOffscreenAfterSettle.join(', ') || 'none'}`);
  await page.close();
}

fs.writeFileSync('audit/evidence/keyboard.json', JSON.stringify(out, null, 2));
console.log('\nwrote audit/evidence/keyboard.json');
await browser.close();
