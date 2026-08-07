import fs from 'fs';
import { launch, newContext, primePreview, applyThrottle, BASE, MOBILE } from './lib.mjs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const page = await ctx.newPage();

await page.addInitScript(`
  window.__shifts = [];
  new PerformanceObserver(l => {
    for (const e of l.getEntries()) {
      if (e.hadRecentInput) continue;
      window.__shifts.push({
        value: +e.value.toFixed(4), t: Math.round(e.startTime),
        sources: (e.sources||[]).map(s => ({
          node: s.node ? (s.node.tagName + (typeof s.node.className === 'string' && s.node.className ? '.' + s.node.className.trim().split(/\\s+/).slice(0,3).join('.') : '')) : '?',
          text: s.node && s.node.innerText ? s.node.innerText.replace(/\\s+/g,' ').trim().slice(0,40) : '',
          from: s.previousRect ? [Math.round(s.previousRect.x), Math.round(s.previousRect.y), Math.round(s.previousRect.width), Math.round(s.previousRect.height)] : null,
          to: s.currentRect ? [Math.round(s.currentRect.x), Math.round(s.currentRect.y), Math.round(s.currentRect.width), Math.round(s.currentRect.height)] : null,
        }))
      });
    }
  }).observe({type:'layout-shift', buffered:true});
`);
await applyThrottle(page);
await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
await page.waitForTimeout(7000);

const shifts = await page.evaluate(() => window.__shifts);
console.log('=== LAYOUT SHIFTS on PDP ===');
let total = 0;
for (const s of shifts) {
  total += s.value;
  console.log(`\n  ${s.value} @ ${s.t}ms`);
  for (const src of s.sources) console.log(`     ${src.node} "${src.text}"  ${JSON.stringify(src.from)} -> ${JSON.stringify(src.to)}  (moved ${src.from && src.to ? src.to[1] - src.from[1] : '?'}px vertically)`);
}
console.log(`\nTOTAL CLS = ${total.toFixed(4)}`);

// what is the element that appears/changes size?
const anatomy = await page.evaluate(() => {
  const grid = document.querySelector('.crk-grid');
  const out = { grid: null, sizeRow: null, gallery: null, fontStatus: document.fonts.status };
  if (grid) { const r = grid.getBoundingClientRect(); out.grid = { top: Math.round(r.top + scrollY), h: Math.round(r.height), html: grid.innerHTML.replace(/\s+/g, ' ').slice(0, 300) }; }
  const sz = document.querySelector('.crk-size'); if (sz) { const r = sz.getBoundingClientRect(); out.sizeRow = { top: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; }
  const g = document.querySelector('.crk-tray-main, .crk-main-img'); if (g) { const r = g.getBoundingClientRect(); out.gallery = { top: Math.round(r.top + scrollY), h: Math.round(r.height) }; }
  out.fonts = [...document.fonts].map(f => `${f.family} ${f.status}`).slice(0, 10);
  return out;
});
console.log('\nPAGE ANATOMY:', JSON.stringify(anatomy, null, 2));

// tap-target detail with full context
const taps = await page.evaluate(() => {
  const SEL = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role="button"], [tabindex]:not([tabindex="-1"])';
  const rows = [];
  for (const el of document.querySelectorAll(SEL)) {
    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || r.width === 0) continue;
    if (r.width >= 44 && r.height >= 44) continue;
    rows.push({ sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''), size: `${Math.round(r.width)}x${Math.round(r.height)}`, text: (el.innerText || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30), inHeader: !!el.closest('header'), inFooter: !!el.closest('footer') });
  }
  return rows;
});
console.log('\nTAP TARGETS UNDER 44x44 (PDP):');
for (const t of taps) console.log(`   ${t.size.padEnd(9)} ${t.sel.padEnd(34)} "${t.text}"${t.inHeader ? ' [header]' : ''}${t.inFooter ? ' [footer]' : ''}`);

fs.writeFileSync('audit/evidence/cls-taps.json', JSON.stringify({ shifts, total, anatomy, taps }, null, 2));
await browser.close();
