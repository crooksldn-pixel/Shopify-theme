import { launch, newContext, primePreview, applyThrottle, BASE, MOBILE } from './lib.mjs';
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const page = await ctx.newPage();
const reqs = [];
page.on('request', r => { if (/woff2/.test(r.url())) reqs.push({ url: r.url(), t: Date.now() }); });
const warns = [];
page.on('console', m => { if (/preload/i.test(m.text())) warns.push(m.text().slice(0, 220)); });
await applyThrottle(page);
const t0 = Date.now();
await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
await page.waitForTimeout(6000);
console.log('=== woff2 requests ===');
for (const r of reqs) console.log(`  +${r.t - t0}ms  ${r.url.replace(/^https?:\/\/[^/]+/, '')}`);
const dupes = {};
for (const r of reqs) { const k = r.url.split('?')[0].split('/').pop(); dupes[k] = (dupes[k] || 0) + 1; }
console.log('\nrequest count per file:', dupes);
console.log('\npreload console warnings:'); for (const w of warns) console.log('  ' + w);
const timing = await page.evaluate(() => {
  const fcp = performance.getEntriesByName('first-contentful-paint')[0]?.startTime;
  const f = performance.getEntriesByType('resource').filter(r => /woff2/.test(r.name)).map(r => ({ name: r.name.split('/').pop().split('?')[0], start: Math.round(r.startTime), end: Math.round(r.responseEnd), initiator: r.initiatorType, size: r.transferSize }));
  return { fcp: Math.round(fcp || 0), fonts: f };
});
console.log('\nFCP =', timing.fcp, 'ms');
for (const f of timing.fonts) console.log(`  ${f.name.padEnd(20)} start=${f.start}ms end=${f.end}ms initiator=${f.initiator} bytes=${f.size}`);
await browser.close();
