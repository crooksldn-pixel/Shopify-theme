import fs from 'fs';
import { launch, newContext, primePreview, applyThrottle, INIT_SCRIPT, readVitals, attachNetworkAccounting, BASE, MOBILE, ANDROID, DESKTOP } from './lib.mjs';

const browser = await launch();
const results = {};

function makeJourney(id, name) {
  const j = { id, name, steps: [], taps: 0, t0: Date.now() };
  return {
    j, tap() { j.taps++; },
    async step(page, title, extra = {}) {
      const n = j.steps.length + 1;
      const shot = `audit/screens/p${id}-step${n}.png`;
      await page.screenshot({ path: shot }).catch(() => {});
      const seen = await page.evaluate(() => {
        const inView = [];
        (function walk(el) {
          for (const c of el.children) {
            const r = c.getBoundingClientRect();
            if (r.bottom > 0 && r.top < innerHeight && r.width > 0 && r.height > 0) {
              const own = [...c.childNodes].filter(x => x.nodeType === 3 && x.textContent.trim()).map(x => x.textContent.trim()).join(' ');
              if (own) inView.push(own.replace(/\s+/g, ' ').slice(0, 80));
              walk(c);
            }
          }
        })(document.body);
        return { firstViewportText: [...new Set(inView)].slice(0, 22), scrollViewports: +(scrollY / innerHeight).toFixed(2), url: location.pathname };
      }).catch(() => ({}));
      j.steps.push({ n, title, screenshot: shot, seconds: +((Date.now() - j.t0) / 1000).toFixed(1), tapsSoFar: j.taps, ...seen, ...extra });
      console.log(`  [P${id}] ${n}: ${title} — ${((Date.now() - j.t0) / 1000).toFixed(1)}s, ${j.taps} taps`);
      return j.steps.at(-1);
    },
  };
}
async function cold(device = MOBILE, extra = {}) {
  const ctx = await newContext(browser, device, extra);
  await primePreview(ctx);
  const t = await ctx.newPage();
  await t.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 150000 });
  await t.evaluate(() => { try { localStorage.removeItem('crooksldn_ctc_seen'); } catch (e) {} });
  await t.close();
  return ctx;
}
const clearOverlays = (page) => page.evaluate(() => { document.querySelector('.ctc-close')?.click(); document.querySelector('#shopify-pc__banner__btn-accept')?.click(); });

// ============================================================
// P6 — The accessibility user
// ============================================================
for (const [dev, label, id] of [[MOBILE, 'mobile', 6], [DESKTOP, 'desktop', '6d']]) {
  const ctx = await cold(dev);
  const page = await ctx.newPage();
  const J = makeJourney(id, `Accessibility user (${label})`);
  J.j.t0 = Date.now();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(4000);
  await J.step(page, 'Homepage on arrival — before any key is pressed');

  // --- keyboard-only: how many Tabs to reach the first product? ---
  const tabTo = async (predicate, max = 90) => {
    const seq = [];
    for (let i = 0; i < max; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(35);
      const cur = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return { sel: '(body)', text: '' };
        return {
          sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id.slice(0, 20) : '') + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : ''),
          text: (el.innerText || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30),
          href: el.getAttribute?.('href') || '',
        };
      });
      seq.push(cur);
      if (predicate(cur)) return { found: true, tabs: i + 1, seq };
    }
    return { found: false, tabs: max, seq };
  };
  const toProduct = await tabTo(c => /\/products\//.test(c.href || ''));
  await J.step(page, 'Tabbing from the top of the homepage to the first product link', {
    tabsToFirstProduct: toProduct.tabs, found: toProduct.found,
    firstStops: toProduct.seq.slice(0, 8).map(s => `${s.sel}${s.text ? ' "' + s.text + '"' : ''}`),
    cookieBannerStops: toProduct.seq.slice(0, 4).filter(s => /shopify-pc/.test(s.sel)).length,
  });

  // --- keyboard-only on a PDP: reach size + add to bag ---
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(3800);
  await clearOverlays(page); await page.waitForTimeout(800);
  await page.evaluate(() => window.scrollTo(0, 0));
  const toSize = await tabTo(c => /crk-size/.test(c.sel));
  await J.step(page, 'Tabbing to the size buttons on the PDP', { tabsToSize: toSize.tabs, found: toSize.found });
  // select a size with the keyboard
  await page.keyboard.press('Enter'); J.tap();
  await page.waitForTimeout(700);
  const afterEnter = await page.evaluate(() => ({ sticky: document.querySelector('.crk-stickybar')?.innerText.replace(/\s+/g, ' ').trim(), focused: document.activeElement?.innerText?.trim() }));
  const toATC = await tabTo(c => /ADD TO BAG/i.test(c.text || ''), 25);
  await J.step(page, 'Selected a size with Enter, then tabbed to ADD TO BAG', { afterEnter, extraTabsToATC: toATC.tabs, reachedATC: toATC.found });

  // --- accessible names / screen-reader surface ---
  const sr = await page.evaluate(() => {
    const named = (el) => el.getAttribute('aria-label') || el.getAttribute('title') || (el.innerText || '').replace(/\s+/g, ' ').trim() || (el.querySelector('img')?.alt) || '';
    const controls = [...document.querySelectorAll('button, a[href], input, [role="button"]')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    const unnamed = controls.filter(e => !named(e)).map(e => e.tagName.toLowerCase() + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : ''));
    return {
      totalControls: controls.length,
      unnamedControls: [...new Set(unnamed)],
      h1: [...document.querySelectorAll('h1')].map(h => h.innerText.trim()),
      headingOutline: [...document.querySelectorAll('h1,h2,h3')].map(h => h.tagName + ': ' + h.innerText.replace(/\s+/g, ' ').trim().slice(0, 40)).slice(0, 12),
      landmarks: [...document.querySelectorAll('header,nav,main,footer,[role="main"],[role="navigation"]')].map(e => e.tagName.toLowerCase()),
      imagesMissingAlt: [...document.querySelectorAll('img')].filter(i => !i.alt && !i.getAttribute('aria-hidden')).length,
      sizeButtonSemantics: [...document.querySelectorAll('.crk-size')].slice(0, 3).map(b => ({ text: b.innerText.trim(), role: b.getAttribute('role'), pressed: b.getAttribute('aria-pressed'), label: b.getAttribute('aria-label'), disabled: b.getAttribute('aria-disabled') })),
      canvasAlt: (() => { const c = document.querySelector('canvas'); return c ? { role: c.getAttribute('role'), label: c.getAttribute('aria-label'), hidden: c.getAttribute('aria-hidden'), fallback: c.innerText?.trim().slice(0, 80) } : null; })(),
      popupSemantics: null,
    };
  });
  await J.step(page, 'Screen-reader surface of the PDP', { sr });

  // --- 200% zoom ---
  const zctx = await cold({ ...dev, viewport: { width: Math.round(dev.viewport.width / 2), height: Math.round(dev.viewport.height / 2) }, deviceScaleFactor: (dev.deviceScaleFactor || 1) * 2 });
  const zp = await zctx.newPage();
  await zp.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
  await zp.waitForTimeout(3500);
  await clearOverlays(zp); await zp.waitForTimeout(700);
  const zoom = await zp.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
    horizontalScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    overflowing: [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > document.documentElement.clientWidth + 2; }).slice(0, 6).map(e => e.tagName.toLowerCase() + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : '') + ` (+${Math.round(e.getBoundingClientRect().right - document.documentElement.clientWidth)}px)`),
    atcVisible: !!document.querySelector('.crk-stickybar'),
  }));
  await zp.screenshot({ path: `audit/screens/p${id}-zoom200.png` });
  J.j.steps.push({ n: J.j.steps.length + 1, title: 'At 200% browser zoom', screenshot: `audit/screens/p${id}-zoom200.png`, seconds: +((Date.now() - J.j.t0) / 1000).toFixed(1), tapsSoFar: J.j.taps, zoom });
  console.log(`  [P${id}] zoom200: hScroll=${zoom.horizontalScroll} ${zoom.scrollWidth}/${zoom.clientWidth}`);
  await zctx.close();

  // --- reduced motion ---
  const rctx = await cold(dev, { reducedMotion: 'reduce' });
  const rp = await rctx.newPage();
  await rp.addInitScript(`window.__f=0;const _r=requestAnimationFrame;window.requestAnimationFrame=cb=>_r(t=>{window.__f++;return cb(t)});`);
  await rp.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await rp.waitForTimeout(3800);
  await clearOverlays(rp);
  await rp.evaluate(() => document.querySelector('canvas')?.scrollIntoView({ block: 'center' }));
  await rp.waitForTimeout(1000);
  const a = await rp.evaluate(() => window.__f); await rp.waitForTimeout(3000); const b2 = await rp.evaluate(() => window.__f);
  const rm = { boardFps: +(((b2 - a) / 3000) * 1000).toFixed(1), popupStillFires: await rp.evaluate(() => !!document.querySelector('.ctc-overlay')) };
  await rp.screenshot({ path: `audit/screens/p${id}-reducedmotion.png` });
  J.j.steps.push({ n: J.j.steps.length + 1, title: 'With prefers-reduced-motion: reduce', screenshot: `audit/screens/p${id}-reducedmotion.png`, seconds: +((Date.now() - J.j.t0) / 1000).toFixed(1), tapsSoFar: J.j.taps, reducedMotion: rm });
  console.log(`  [P${id}] reduced-motion: board ${rm.boardFps} fps`);
  await rctx.close();

  results[id === 6 ? 'p6' : 'p6desktop'] = J.j;
  await ctx.close();
}

// ============================================================
// P7 — The slow connection (older Android, 360x800)
// ============================================================
{
  const ctx = await cold(ANDROID);
  const page = await ctx.newPage();
  await page.addInitScript(INIT_SCRIPT);
  const cdp = await applyThrottle(page, { cpu: 6 }); // older device: harsher CPU penalty
  const finished = attachNetworkAccounting(cdp);
  const J = makeJourney(7, 'The slow connection');
  J.j.t0 = Date.now();
  const nav = page.goto(BASE + '/', { waitUntil: 'commit', timeout: 240000 });
  await nav.catch(() => {});
  for (const ms of [3000, 5000, 10000]) {
    const wait = ms - (Date.now() - J.j.t0);
    if (wait > 0) await page.waitForTimeout(wait);
    const snap = await page.evaluate(() => {
      const imgs = [...document.querySelectorAll('img')].filter(i => i.complete && i.naturalWidth > 0);
      const inView = imgs.filter(i => { const r = i.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0 && r.width > 40; });
      return {
        textChars: document.body.innerText.replace(/\s+/g, ' ').trim().length,
        imagesLoaded: imgs.length, imagesLoadedInViewport: inView.length,
        canvasPresent: !!document.querySelector('canvas'),
        canvasPainted: (() => { const c = document.querySelector('canvas'); if (!c) return false; try { const g = c.getContext('2d'); const d = g.getImageData(0, 0, Math.min(8, c.width), Math.min(8, c.height)).data; return d.some((v, i) => i % 4 !== 3 && v > 0); } catch { return null; } })(),
        cls: +(window.__crk?.cls || 0).toFixed(4),
        overlays: [...document.querySelectorAll('.ctc-overlay,.shopify-pc__banner')].map(e => e.className),
        fontsLoaded: document.fonts.status,
      };
    }).catch(() => ({}));
    await J.step(page, `At ${ms / 1000}s`, snap);
  }
  await page.waitForLoadState('load', { timeout: 240000 }).catch(() => {});
  await J.step(page, 'Fully loaded');
  const v = await readVitals(page);
  // continue to a product then the cart
  await clearOverlays(page); await page.waitForTimeout(600);
  const t1 = Date.now();
  await page.goto(BASE + '/products/3-clives-tee', { waitUntil: 'load', timeout: 240000 }).catch(() => {}); J.tap();
  await J.step(page, 'Product page', { navMs: Date.now() - t1 });
  await page.evaluate(async () => { const id = document.querySelector('[name="id"]')?.value; await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) }); }); J.tap();
  const t2 = Date.now();
  await page.goto(BASE + '/cart', { waitUntil: 'load', timeout: 240000 }).catch(() => {}); J.tap();
  await J.step(page, 'Cart', { navMs: Date.now() - t2 });
  const bytes = finished.reduce((a, r) => a + (r.encodedDataLength || 0), 0);
  results.p7 = { ...J.j, homepageVitals: v, totalBytesAcrossJourney: Math.round(bytes / 1024) + ' KB' };
  await ctx.close();
}

// ============================================================
// P8 — Post-purchase
// ============================================================
{
  const ctx = await cold();
  const page = await ctx.newPage();
  const J = makeJourney(8, 'Post-purchase');
  J.j.t0 = Date.now();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(3800);
  await J.step(page, 'Homepage — looking for "track my order"');
  await clearOverlays(page); await page.waitForTimeout(700);
  const hunt = await page.evaluate(() => {
    const t = document.body.innerText;
    const links = [...document.querySelectorAll('a')].map(a => ({ text: a.innerText.replace(/\s+/g, ' ').trim(), href: a.getAttribute('href') }));
    return {
      trackWordPresent: /track|order status|my order/i.test(t),
      accountLinkInFooter: links.some(l => /account/i.test(l.text) && l.closest),
      footerLinks: links.filter(l => l.href && !l.href.startsWith('#')).map(l => l.text + ' -> ' + l.href).slice(-14),
      returnsLinkText: links.filter(l => /refund|return/i.test(l.text)).map(l => l.text + ' -> ' + l.href),
    };
  });
  await J.step(page, 'Scanning every link on the homepage for order tracking', { hunt });
  // menu
  await page.locator('button', { hasText: /^MENU$/ }).first().click().catch(() => {}); J.tap();
  await page.waitForTimeout(1200);
  const menu = await page.evaluate(() => {
    const d = document.querySelector('.crk-drawer, dialog[open], [class*="drawer"]');
    return d ? { links: [...d.querySelectorAll('a')].map(a => a.innerText.replace(/\s+/g, ' ').trim() + ' -> ' + a.getAttribute('href')), hasTracking: /track/i.test(d.innerText) } : null;
  });
  await J.step(page, 'Opened MENU', { menu });
  // account
  await page.goto(BASE + '/account', { waitUntil: 'load', timeout: 180000 }); J.tap();
  await page.waitForTimeout(3000);
  const acct = await page.evaluate(() => ({
    url: location.pathname, host: location.host,
    text: document.body.innerText.replace(/\s+/g, ' ').trim().slice(0, 300),
    styledAsTheme: !!document.querySelector('.crk-root'),
    typeface: getComputedStyle(document.body).fontFamily,
    bg: getComputedStyle(document.body).backgroundColor,
    hasOrderLookup: /order|track/i.test(document.body.innerText),
  }));
  await J.step(page, 'Account / sign-in', { acct });
  // returns
  await page.goto(BASE + '/policies/refund-policy', { waitUntil: 'load', timeout: 180000 }); J.tap();
  await page.waitForTimeout(2500);
  const ret = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    return {
      howToStart: (t.match(/(email|contact)[^.]{0,80}(info@|return)[^.]{0,60}\./i) || [null])[0],
      emailShown: (t.match(/[\w.]+@[\w.]+/) || [null])[0],
      window: (t.match(/within \d+ days|14 days/i) || [null])[0],
      returnsPortal: /portal|start a return|returns centre|returns center/i.test(t),
      whoPaysPostage: (t.match(/(return (shipping|postage)|customer is responsible)[^.]{0,90}\./i) || [null])[0],
      words: t.split(' ').length,
      typeface: getComputedStyle(document.querySelector('main') || document.body).fontFamily,
    };
  });
  await J.step(page, 'Refund policy — how do I actually return something?', { ret });
  results.p8 = J.j;
  await ctx.close();
}

fs.writeFileSync('audit/evidence/journeys-6-8.json', JSON.stringify(results, null, 2));
console.log('\nwrote audit/evidence/journeys-6-8.json');
await browser.close();
