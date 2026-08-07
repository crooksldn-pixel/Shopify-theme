import fs from 'fs';
import { launch, newContext, primePreview, applyThrottle, BASE, MOBILE, ANDROID, DESKTOP } from './lib.mjs';

const PAGES = [
  ['home', BASE + '/', 'Homepage'],
  ['pdpTee', BASE + '/products/3-clives-tee', 'PDP — 3 CLIVES TEE'],
  ['pdpDenim', BASE + '/products/cb2-wash-jeans', 'PDP — BLUE WASH OG JEANS'],
  ['cart', BASE + '/cart', 'Cart'],
  ['collection', BASE + '/collections/all', 'Collection — all'],
];

const out = { generated: new Date().toISOString(), pages: {}, overflow: {}, board: {} };
const browser = await launch();

// ---------- A. scroll depth, tap targets, thumb zone ----------
{
  const ctx = await newContext(browser, MOBILE);
  await primePreview(ctx);
  // seed cart so /cart is meaningful
  const s = await ctx.newPage();
  await s.goto(BASE + '/products/3-clives-tee', { waitUntil: 'load', timeout: 120000 });
  await s.waitForTimeout(1200);
  await s.evaluate(async () => { const id = document.querySelector('[name="id"]')?.value; await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) }); });
  await s.close();

  for (const [key, url, label] of PAGES) {
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'load', timeout: 150000 });
    await page.waitForTimeout(2500);

    // popup state on arrival
    const popup = await page.evaluate(() => {
      const cands = [...document.querySelectorAll('dialog[open], [class*="popup"], [class*="modal"], [class*="overlay"]')]
        .filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 100 && r.height > 100 && cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0.1; });
      return cands.map(e => { const r = e.getBoundingClientRect(); return { cls: (typeof e.className === 'string' ? e.className : e.tagName), tag: e.tagName, coversPctOfViewport: Math.round(100 * Math.min(r.height, innerHeight) * Math.min(r.width, innerWidth) / (innerWidth * innerHeight)), z: getComputedStyle(e).zIndex, scrollLocked: getComputedStyle(document.body).overflow }; });
    });

    // dismiss any first-visit popup so the rest of the measurements reflect the page itself
    await page.evaluate(() => {
      document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } });
      document.querySelectorAll('[class*="popup"],[class*="modal"]').forEach(e => { const r = e.getBoundingClientRect(); if (r.height > innerHeight * 0.5) e.remove(); });
      document.body.style.overflow = '';
    });
    await page.waitForTimeout(400);

    const measured = await page.evaluate(() => {
      const vh = innerHeight, vw = innerWidth;
      const abs = (el) => { const r = el.getBoundingClientRect(); return r.top + scrollY; };
      const sel = (el) => { if (!el) return null; const c = typeof el.className === 'string' ? el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''; return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (c ? '.' + c : ''); };

      const firstProductCard = document.querySelector('[class*="crk-card"], a[href*="/products/"]');
      const addToCart = document.querySelector('button[name="add"], [type="submit"][name="add"], .crk-buy, [class*="add-to-cart"], button[class*="buy"]');
      const price = [...document.querySelectorAll('*')].find(e => /^£\s?\d/.test((e.textContent || '').trim()) && e.children.length === 0);
      const footer = document.querySelector('footer, [class*="footer"]');
      const checkout = document.querySelector('[name="checkout"], button[name="checkout"], a[href*="/checkout"]');

      const depth = (el) => el ? +(abs(el) / vh).toFixed(2) : null;

      // tap targets
      const INTERACTIVE = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role="button"], [role="link"], [role="tab"], [tabindex]:not([tabindex="-1"]), label[for]';
      const small = [];
      const all = [];
      for (const el of document.querySelectorAll(INTERACTIVE)) {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
        if (r.width === 0 || r.height === 0) continue;
        const rec = { sel: sel(el), w: Math.round(r.width), h: Math.round(r.height), text: (el.innerText || el.getAttribute('aria-label') || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 34) };
        all.push(rec);
        if (r.width < 44 || r.height < 44) small.push(rec);
      }
      // de-dup identical selector+size
      const seen = new Set(); const smallU = [];
      for (const s of small) { const k = s.sel + s.w + 'x' + s.h; if (!seen.has(k)) { seen.add(k); smallU.push({ ...s, count: small.filter(x => x.sel === s.sel && x.w === s.w && x.h === s.h).length }); } }

      // thumb zone for the page's primary action
      const primary = addToCart || checkout || firstProductCard;
      let thumb = null;
      if (primary) {
        const r = primary.getBoundingClientRect();
        const centreFromTopOfDoc = r.top + scrollY + r.height / 2;
        // where it sits in the FIRST viewport
        const inFirst = r.top + scrollY < vh;
        const pct = ((r.top + scrollY) % vh) / vh;
        thumb = { sel: sel(primary), inFirstViewport: inFirst, topOfDocPx: Math.round(r.top + scrollY), band: pct < 0.33 ? 'top third' : pct < 0.6 ? 'middle' : 'bottom 40% (thumb zone)', viewportsDown: +((r.top + scrollY) / vh).toFixed(2) };
      }

      return {
        viewport: [vw, vh],
        docHeight: document.documentElement.scrollHeight,
        docHeightInViewports: +(document.documentElement.scrollHeight / vh).toFixed(2),
        scrollDepthViewports: {
          firstProductCard: depth(firstProductCard), firstProductCardSel: sel(firstProductCard),
          addToCart: depth(addToCart), addToCartSel: sel(addToCart),
          firstPrice: depth(price), firstPriceText: price ? price.textContent.trim().slice(0, 20) : null,
          footer: depth(footer),
          checkout: depth(checkout),
        },
        tapTargets: { total: all.length, under44: small.length, under44Unique: smallU.sort((a, b) => a.w * a.h - b.w * b.h).slice(0, 30) },
        thumbZone: thumb,
      };
    });

    // sticky buy bar behaviour on PDPs
    let stickyBar = null;
    if (key.startsWith('pdp')) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.6));
      await page.waitForTimeout(900);
      stickyBar = await page.evaluate(() => {
        const bars = [...document.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); const r = e.getBoundingClientRect(); return (cs.position === 'fixed' || cs.position === 'sticky') && r.height > 30 && r.width > innerWidth * 0.6 && r.top > innerHeight * 0.4 && cs.visibility !== 'hidden' && +cs.opacity > 0.1; });
        return bars.map(e => ({ cls: typeof e.className === 'string' ? e.className : e.tagName, h: Math.round(e.getBoundingClientRect().height), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 60) }));
      });
      await page.evaluate(() => window.scrollTo(0, 0));
    }

    out.pages[key] = { label, url, popupOnArrival: popup, ...measured, stickyBar };
    console.log(`\n[${key}] ${label}`);
    console.log(`  page height: ${measured.docHeightInViewports} viewports`);
    console.log(`  scroll depth (viewports): card=${measured.scrollDepthViewports.firstProductCard} price=${measured.scrollDepthViewports.firstPrice} ATC=${measured.scrollDepthViewports.addToCart} footer=${measured.scrollDepthViewports.footer}`);
    console.log(`  tap targets: ${measured.tapTargets.under44}/${measured.tapTargets.total} under 44x44`);
    console.log(`  primary action: ${measured.thumbZone ? measured.thumbZone.sel + ' @ ' + measured.thumbZone.viewportsDown + ' viewports — ' + measured.thumbZone.band : 'none found'}`);
    if (popup.length) console.log(`  POPUP ON ARRIVAL: ${popup.map(p => p.tag + '.' + String(p.cls).slice(0, 30) + ' covers ' + p.coversPctOfViewport + '% z=' + p.z).join(' | ')}`);
    if (stickyBar && stickyBar.length) console.log(`  sticky bar after scroll: ${JSON.stringify(stickyBar)}`);
    await page.close();
  }
  await ctx.close();
}

// ---------- B. horizontal overflow at 320 / 360 / 390 ----------
for (const w of [320, 360, 390]) {
  const ctx = await newContext(browser, { ...MOBILE, viewport: { width: w, height: 720 } });
  await primePreview(ctx);
  out.overflow[w] = {};
  for (const [key, url] of PAGES) {
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'load', timeout: 150000 });
    await page.waitForTimeout(2200);
    await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } }); document.querySelectorAll('[class*="popup"],[class*="modal"]').forEach(e => { if (e.getBoundingClientRect().height > innerHeight * 0.5) e.remove(); }); document.body.style.overflow = ''; });
    const r = await page.evaluate(() => {
      const vw = document.documentElement.clientWidth;
      const offenders = [];
      for (const el of document.querySelectorAll('body *')) {
        const b = el.getBoundingClientRect();
        if (b.width === 0) continue;
        if (b.right > vw + 1 || b.left < -1) {
          const cs = getComputedStyle(el);
          if (cs.position === 'fixed' && b.width <= vw + 1) continue;
          offenders.push({ sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''), left: Math.round(b.left), right: Math.round(b.right), w: Math.round(b.width), overflowPx: Math.round(Math.max(b.right - vw, -b.left)) });
        }
      }
      const seen = new Set(); const uniq = [];
      for (const o of offenders) { if (!seen.has(o.sel)) { seen.add(o.sel); uniq.push(o); } }
      return { scrollWidth: document.documentElement.scrollWidth, clientWidth: vw, horizontalScroll: document.documentElement.scrollWidth > vw + 1, offenders: uniq.sort((a, b) => b.overflowPx - a.overflowPx).slice(0, 12) };
    });
    out.overflow[w][key] = r;
    console.log(`overflow @${w} ${key}: scrollW=${r.scrollWidth} clientW=${r.clientWidth} hScroll=${r.horizontalScroll}${r.offenders.length ? ' offenders: ' + r.offenders.slice(0, 3).map(o => o.sel + '(+' + o.overflowPx + 'px)').join(', ') : ''}`);
    await page.close();
  }
  await ctx.close();
}

// ---------- C. canvas board: frame rate, off-screen pause, tab-blur pause ----------
{
  const ctx = await newContext(browser, MOBILE);
  await primePreview(ctx);
  const page = await ctx.newPage();
  await applyThrottle(page, { cpu: 4, net: true });
  await page.addInitScript(`
    window.__frames = 0; window.__marks = [];
    const _raf = requestAnimationFrame;
    window.requestAnimationFrame = (cb) => _raf((t) => { window.__frames++; return cb(t); });
  `);
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(3500);
  await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } }); document.querySelectorAll('[class*="popup"],[class*="modal"]').forEach(e => { if (e.getBoundingClientRect().height > innerHeight * 0.5) e.remove(); }); document.body.style.overflow = ''; });

  const boardInfo = await page.evaluate(() => {
    const c = document.querySelector('canvas');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return { present: true, cssSize: [Math.round(r.width), Math.round(r.height)], bitmap: [c.width, c.height], topOfDocPx: Math.round(r.top + scrollY), viewportsDown: +((r.top + scrollY) / innerHeight).toFixed(2) };
  });

  const sample = async (ms, label) => {
    const a = await page.evaluate(() => window.__frames);
    await page.waitForTimeout(ms);
    const b = await page.evaluate(() => window.__frames);
    const fps = +(((b - a) / ms) * 1000).toFixed(1);
    console.log(`  board sample [${label}]: ${b - a} frames in ${ms}ms = ${fps} fps`);
    return { label, frames: b - a, ms, fps };
  };

  const samples = [];
  // scroll board into view
  if (boardInfo) await page.evaluate(() => { const c = document.querySelector('canvas'); c.scrollIntoView({ block: 'center' }); });
  await page.waitForTimeout(1200);
  samples.push(await sample(3000, 'board in viewport, idle'));

  // full-page scroll while board runs
  const scrollFps = await page.evaluate(async () => {
    const start = performance.now(); let frames = 0; let raf;
    const tick = () => { frames++; raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    window.scrollTo(0, 0);
    const total = document.body.scrollHeight - innerHeight;
    const steps = 60;
    for (let i = 0; i <= steps; i++) { window.scrollTo(0, (total * i) / steps); await new Promise(r => setTimeout(r, 33)); }
    const dur = performance.now() - start;
    cancelAnimationFrame(raf);
    return { frames, durMs: Math.round(dur), fps: +((frames / dur) * 1000).toFixed(1) };
  });
  console.log(`  full-page scroll: ${scrollFps.fps} fps over ${scrollFps.durMs}ms`);

  // board scrolled far off-screen
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1500);
  samples.push(await sample(3000, 'board OFF-screen'));

  // tab blur (real visibility change via CDP)
  const cdp = await page.context().newCDPSession(page);
  if (boardInfo) await page.evaluate(() => document.querySelector('canvas').scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(1200);
  samples.push(await sample(2000, 'board in viewport (control before blur)'));
  await cdp.send('Emulation.setPageVisibilityOverride', { visibility: 'hidden' }).catch(async () => {
    await page.evaluate(() => { Object.defineProperty(document, 'hidden', { value: true, configurable: true }); Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true }); document.dispatchEvent(new Event('visibilitychange')); });
  });
  await page.waitForTimeout(600);
  samples.push(await sample(2500, 'tab HIDDEN'));

  out.board = { boardInfo, samples, scrollFps };
  await page.close();
  await ctx.close();
}

fs.writeFileSync('audit/evidence/layout.json', JSON.stringify(out, null, 2));
console.log('\nwrote audit/evidence/layout.json');
await browser.close();
