import fs from 'fs';
import { launch, newContext, primePreview, applyThrottle, attachNetworkAccounting, INIT_SCRIPT, readVitals, summariseBytes, PAGES, BASE, MOBILE, THROTTLE } from './lib.mjs';

const out = { generated: new Date().toISOString(), conditions: THROTTLE, pages: {}, notes: [] };

const browser = await launch();

// ---- measure the harness's own overhead so the throttled numbers have error bars ----
{
  const ctx = await newContext(browser, MOBILE);
  await primePreview(ctx);
  const p = await ctx.newPage();
  const t0 = Date.now();
  await p.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });
  const unthrottledDcl = Date.now() - t0;
  const nav = await p.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; return { ttfb: Math.round(n.responseStart), dcl: Math.round(n.domContentLoadedEventEnd) }; });
  out.harnessBaseline = { unthrottledWallMs: unthrottledDcl, unthrottledTtfbMs: nav.ttfb, unthrottledDclMs: nav.dcl,
    note: 'Unthrottled, but still through the session egress proxy + local TLS bridge. Treat throttled figures as an upper bound; the proxy hop adds a fixed penalty to TTFB that a real shopper would not pay.' };
  await ctx.close();
}

async function measure(key, { url, label }, { device = MOBILE, dismissPopup = false, seedCart = false } = {}) {
  const ctx = await newContext(browser, device);
  await primePreview(ctx);
  if (seedCart) {
    const s = await ctx.newPage();
    await s.goto(BASE + '/products/3-clives-tee', { waitUntil: 'load', timeout: 120000 });
    await s.waitForTimeout(1500);
    await s.evaluate(async () => {
      const id = document.querySelector('[name="id"]')?.value || document.querySelector('input[name=id]')?.value;
      await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) });
    });
    await s.close();
  }
  if (dismissPopup) {
    const s = await ctx.newPage();
    await s.goto(BASE + '/', { waitUntil: 'load', timeout: 120000 });
    await s.waitForTimeout(2500);
    await s.evaluate(() => { for (const b of document.querySelectorAll('[data-crk-popup-close], .crk-popup__close, dialog [aria-label*="lose" i], [aria-label*="lose" i]')) b.click(); });
    await s.waitForTimeout(600);
    await s.close();
  }

  const page = await ctx.newPage();
  await page.addInitScript(INIT_SCRIPT);
  const cdp = await applyThrottle(page);
  const finished = attachNetworkAccounting(cdp);
  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message.slice(0, 200)));

  const t0 = Date.now();
  await page.goto(url, { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(6000); // let lazy assets + LCP settle under throttle
  const wall = Date.now() - t0;

  const vitals = await readVitals(page);
  const bytes = summariseBytes(finished);

  const onTheme = await page.evaluate(() => ({ crkRoot: !!document.querySelector('.crk-root'), theme: window.Shopify?.theme?.name }));

  // ---- image efficiency ----
  const images = await page.evaluate(() => [...document.querySelectorAll('img')].map(img => {
    const r = img.getBoundingClientRect();
    const cs = getComputedStyle(img);
    return {
      src: (img.currentSrc || img.src || '').split('?')[0].split('/').pop(),
      full: (img.currentSrc || img.src || '').split('?')[0],
      query: (img.currentSrc || img.src || '').split('?')[1] || '',
      natural: [img.naturalWidth, img.naturalHeight],
      rendered: [Math.round(r.width), Math.round(r.height)],
      loading: img.loading, fetchpriority: img.fetchPriority,
      hasSrcset: !!img.srcset, sizes: img.sizes || '',
      objectFit: cs.objectFit,
      inFirstViewport: r.top < innerHeight && r.bottom > 0,
      alt: img.alt || '',
    };
  }).filter(i => i.rendered[0] > 0));
  const dpr = device.deviceScaleFactor;
  const byteByName = new Map(bytes.all.map(a => [a.name, a.bytes]));
  for (const i of images) {
    i.bytes = byteByName.get(i.full.split('/').pop()) ?? byteByName.get(i.src) ?? null;
    i.format = /\.webp/i.test(i.full) ? 'webp' : /\.avif/i.test(i.full) ? 'avif' : /\.png/i.test(i.full) ? 'png' : /\.jpe?g/i.test(i.full) ? 'jpg' : /\.svg/i.test(i.full) ? 'svg' : '?';
    i.overscaleVsDpr = i.rendered[0] ? +(i.natural[0] / (i.rendered[0] * dpr)).toFixed(2) : null;
    i.overscaleVsCss = i.rendered[0] ? +(i.natural[0] / i.rendered[0]).toFixed(2) : null;
  }

  out.pages[key] = {
    label, url, device: `${device.viewport.width}x${device.viewport.height}@${dpr}x`,
    throttled: true, onTheme, wallClockMs: wall, vitals, consoleErrors: consoleErrors.slice(0, 12),
    transfer: { totalBytes: bytes.totalBytes, totalKB: Math.round(bytes.totalBytes / 1024), byTypeKB: Object.fromEntries(Object.entries(bytes.byType).map(([k, v]) => [k, Math.round(v / 1024)])), requestCount: bytes.all.length, largest: bytes.top.slice(0, 12) },
    images: { count: images.length, formats: images.reduce((a, i) => (a[i.format] = (a[i.format] || 0) + 1, a), {}), detail: images.slice(0, 30) },
  };
  console.log(`[${key}] LCP=${vitals.lcp}ms CLS=${vitals.cls} TTFB=${vitals.ttfb}ms total=${Math.round(bytes.totalBytes / 1024)}KB imgs=${images.length} firstProdImg=${vitals.firstProductImage?.t ?? 'never'}ms`);
  await page.close();
  await ctx.close();
}

await measure('home', PAGES.home);
await measure('pdpTee', PAGES.pdpTee);
await measure('pdpDenim', PAGES.pdpDenim);
await measure('cart', PAGES.cart, { seedCart: true });

// ---- desktop pass for the same pages (personas 1,3,6 run desktop too) ----
import { DESKTOP } from './lib.mjs';
const dOut = {};
for (const [k, cfg] of [['home', PAGES.home], ['pdpDenim', PAGES.pdpDenim]]) {
  const key = k + 'Desktop';
  await measure(key, { ...cfg, label: cfg.label + ' [desktop]' }, { device: DESKTOP });
}

fs.mkdirSync('audit/evidence', { recursive: true });
fs.writeFileSync('audit/evidence/perf.json', JSON.stringify(out, null, 2));
console.log('\nwrote audit/evidence/perf.json');
await browser.close();
