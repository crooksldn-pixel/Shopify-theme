/* Theme gauntlet capture runner.
 * 7 journeys x 2 themes x 2 devices + mobile edge sweep.
 * Evidence: full-page screenshots + meta.jsonl (theme-id assertion, timings,
 * console errors, failed requests, blind-spot checks) per session.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const CAP = path.join(ROOT, 'captures');

const THEMES = {
  old: { base: 'https://crooksldn.com', id: 202044309847 },
  new: { base: 'https://caijh1httspvte6b-100410786135.shopifypreview.com', id: 202053779799 },
};
const DEVICES = {
  mobile: {
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
  },
  desktop: { viewport: { width: 1440, height: 900 } },
};

const P = {
  crewneck: '/products/charcoal-cellblock-crewneck',
  shorts: '/products/charcoal-cellblock-shorts',
  jeansBlue: '/products/cb2-wash-jeans',
  jeansGrey: '/products/cb1-wash-jeans',
  jortsBlue: '/products/cb1-wash-jorts',
  baggies: '/products/v2-baggies',
  collectionAll: '/collections/all',
};

const rand = (a, b) => a + Math.floor(Math.random() * (b - a));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const HIDE_PREVIEW = `
  (function(){
    const css = '#preview-bar-iframe, iframe[src*="preview_bar"], iframe[src*="preview-bar"], [id*="PreviewBar"], #PBarNextFrameWrapper, shopify-preview-bar {display:none !important;} body {padding-bottom: 0 !important;}';
    const add = () => { try {
      if (!document.getElementById('__gauntlet_hide')) {
        const s = document.createElement('style'); s.id='__gauntlet_hide'; s.textContent = css;
        (document.head || document.documentElement).appendChild(s);
      }
      document.querySelectorAll('#preview-bar-iframe, iframe[src*="preview_bar"], iframe[src*="preview-bar"], shopify-preview-bar, #PBarNextFrameWrapper').forEach(e => e.remove());
    } catch(e){} };
    add();
    new MutationObserver(add).observe(document.documentElement, {childList:true, subtree:true});
    window.__cls = 0;
    try {
      new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
        .observe({type:'layout-shift', buffered:true});
    } catch(e){}
  })();
`;

class Session {
  constructor(browser, themeKey, journey, deviceKey) {
    this.browser = browser;
    this.themeKey = themeKey;
    this.theme = THEMES[themeKey];
    this.journey = journey;
    this.deviceKey = deviceKey;
    this.dir = path.join(CAP, themeKey, journey, deviceKey);
    fs.mkdirSync(this.dir, { recursive: true });
    this.metaPath = path.join(this.dir, 'meta.jsonl');
    fs.writeFileSync(this.metaPath, '');
    this.stepNo = 0;
    this.consoleErrors = [];
    this.failedRequests = [];
    this.t0 = Date.now();
    this.poisoned = false;
  }
  log(obj) {
    fs.appendFileSync(this.metaPath, JSON.stringify({ t: new Date().toISOString(), ms: Date.now() - this.t0, ...obj }) + '\n');
  }
  async init() {
    this.ctx = await this.browser.newContext({ ...DEVICES[this.deviceKey], serviceWorkers: 'block' });
    await this.ctx.addInitScript(HIDE_PREVIEW);
    this.page = await this.ctx.newPage();
    this.page.on('console', (m) => { if (m.type() === 'error') this.consoleErrors.push({ text: m.text().slice(0, 300), url: this.page.url() }); });
    this.page.on('pageerror', (e) => this.consoleErrors.push({ text: ('pageerror: ' + e.message).slice(0, 300), url: this.page.url() }));
    this.page.on('requestfailed', (r) => {
      const f = r.failure();
      this.failedRequests.push({ url: r.url().slice(0, 160), error: f ? f.errorText : '?' });
    });
    return this;
  }
  async think() { await sleep(rand(300, 800)); }
  async assertTheme(note) {
    let tid = null;
    try { tid = await this.page.evaluate(() => (window.Shopify && window.Shopify.theme) ? window.Shopify.theme.id : null); } catch (e) {}
    const url = this.page.url();
    const onPreview = url.includes('shopifypreview.com');
    const isCheckout = /checkout|\/cn\//.test(url);
    let ok = true;
    if (tid !== null) {
      ok = tid === this.theme.id;
      // live-domain pages during a NEW session (e.g. checkout redirect) are expected to be off-preview
      if (!ok && this.themeKey === 'new' && !onPreview) ok = 'off-preview-domain';
    }
    if (tid === null && !isCheckout) ok = 'no-theme-object';
    if (ok === false) this.poisoned = true;
    this.log({ type: 'assert-theme', themeId: tid, expect: this.theme.id, ok, url: url.slice(0, 140), note });
    return ok;
  }
  async goto(pathOrUrl, note) {
    const url = pathOrUrl.startsWith('http') ? pathOrUrl : this.theme.base + pathOrUrl;
    const t = Date.now();
    let status = null, err = null;
    try {
      const resp = await this.page.goto(url, { waitUntil: 'load', timeout: 60000 });
      status = resp ? resp.status() : null;
    } catch (e) { err = e.message.split('\n')[0]; }
    await sleep(1000);
    let perf = null, cls = null;
    try {
      perf = await this.page.evaluate(() => {
        const n = performance.getEntriesByType('navigation')[0];
        const fcp = performance.getEntriesByName('first-contentful-paint')[0];
        return n ? { dcl: Math.round(n.domContentLoadedEventEnd), load: Math.round(n.loadEventEnd), fcp: fcp ? Math.round(fcp.startTime) : null } : null;
      });
      cls = await this.page.evaluate(() => Math.round((window.__cls || 0) * 1000) / 1000);
    } catch (e) {}
    this.log({ type: 'load', url: url.slice(0, 140), status, err, loadMs: Date.now() - t, perf, cls, note });
    await this.assertTheme(note);
    return { status, err };
  }
  async step(label, extra) {
    this.stepNo++;
    const file = `step-${String(this.stepNo).padStart(2, '0')}-${label}.jpg`;
    const fp = path.join(this.dir, file);
    try {
      await this.page.screenshot({ path: fp, type: 'jpeg', quality: 60, fullPage: true, timeout: 30000 });
    } catch (e) {
      try { await this.page.screenshot({ path: fp, type: 'jpeg', quality: 60, fullPage: false, timeout: 15000 }); } catch (e2) {}
    }
    const rel = path.relative(ROOT, fp);
    this.log({
      type: 'step', n: this.stepNo, label, file: rel, url: this.page.url().slice(0, 140),
      consoleErrors: this.consoleErrors.splice(0), failedRequests: this.failedRequests.splice(0),
      ...(extra || {}),
    });
    return rel;
  }
  // try a list of locators, click first visible; returns descriptor or null
  async tryClick(cands, note, opts) {
    for (const sel of cands) {
      try {
        const loc = this.page.locator(sel).first();
        if (await loc.isVisible({ timeout: 700 })) {
          await loc.scrollIntoViewIfNeeded({ timeout: 2000 }).catch(() => {});
          await loc.click({ timeout: 5000, ...(opts || {}) });
          this.log({ type: 'action', note, ok: true, how: sel });
          return sel;
        }
      } catch (e) {}
    }
    this.log({ type: 'action', note, ok: false, tried: cands });
    return null;
  }
  async check(name, data) { this.log({ type: 'check', name, ...data }); }
  async close() {
    this.log({ type: 'summary', theme: this.themeKey, journey: this.journey, device: this.deviceKey, poisoned: this.poisoned, steps: this.stepNo, durationMs: Date.now() - this.t0 });
    try { await this.ctx.close(); } catch (e) {}
  }
}

/* ---------- shared selector packs ---------- */
const SEL = {
  menuToggle: [
    'header button[aria-label*="menu" i]', 'header [aria-controls*="menu" i]',
    'header-drawer button', 'header summary[aria-label*="menu" i]',
    '.crk-header__burger', 'header [class*="burger"]', 'header [class*="hamburger"]',
    'header button[aria-haspopup="dialog"]',
  ],
  searchTrigger: [
    'header button[aria-label*="search" i]', 'header a[href="/search"]', 'header a[href^="/search"]',
    '[aria-controls*="search" i]', 'header [class*="search"] button', 'header summary[aria-label*="search" i]',
  ],
  searchInput: ['input[type="search"]', 'input[name="q"]'],
  cartTrigger: [
    'header a[href="/cart"]', 'header button[aria-label*="cart" i]', 'header a[aria-label*="cart" i]',
    '[class*="cart-drawer-trigger"]', 'header [class*="cart"] a', 'header [class*="cart"] button',
  ],
  atc: [
    'button[name="add"]:not([disabled])', 'form[action*="/cart/add"] button[type="submit"]:not([disabled])',
    'add-to-cart-component button', 'button[id*="AddToCart" i]', 'form[action*="/cart/add"] [type="submit"]',
  ],
  checkout: [
    'button[name="checkout"]', 'a[href*="/checkout"]', 'form[action="/cart"] button[type="submit"]',
    '[class*="checkout"] button', 'button[id*="checkout" i]', 'input[name="checkout"]',
  ],
  accountEntry: [
    'header a[href*="/account"]', 'a[href*="customer_authentication"]', 'header a[aria-label*="account" i]',
    'a[href*="/account/login"]', '[class*="account"] a',
  ],
};

async function clickProductLink(s, handle) {
  // some themes render several anchors per card (image, title, quick-view) — click the first VISIBLE one
  try {
    const links = s.page.locator(`a[href*="${handle}"]`);
    const n = Math.min(await links.count(), 8);
    for (let i = 0; i < n; i++) {
      const l = links.nth(i);
      try {
        if (await l.isVisible({ timeout: 400 })) {
          await l.scrollIntoViewIfNeeded({ timeout: 2500 }).catch(() => {});
          await s.think();
          await l.click({ timeout: 5000 });
          await s.page.waitForURL(/\/products\//, { timeout: 12000 });
          await sleep(1100);
          return true;
        }
      } catch (e) {}
    }
    // last resort: JS click on the raw element
    const clicked = await s.page.evaluate((h) => {
      const a = Array.from(document.querySelectorAll(`a[href*="${h}"]`)).find((e) => e.getBoundingClientRect().width > 0);
      if (a) { a.click(); return true; }
      return false;
    }, handle);
    if (clicked) {
      await s.page.waitForURL(/\/products\//, { timeout: 12000 });
      await sleep(1100);
      return true;
    }
  } catch (e) {}
  return false;
}

async function openMobileMenuIfNeeded(s) {
  if (s.deviceKey !== 'mobile') return null;
  return await s.tryClick(SEL.menuToggle, 'open-menu');
}

async function tapTargets(s, which) {
  try {
    const data = await s.page.evaluate((sels) => {
      const out = {};
      for (const [name, list] of Object.entries(sels)) {
        for (const sel of list) {
          const el = document.querySelector(sel);
          if (el) {
            const r = el.getBoundingClientRect();
            if (r.width > 0) { out[name] = { sel, w: Math.round(r.width), h: Math.round(r.height) }; break; }
          }
        }
      }
      return out;
    }, which);
    await s.check('tap-targets', { targets: data });
  } catch (e) { await s.check('tap-targets', { err: e.message.slice(0, 120) }); }
}

async function dismissConsent(s) {
  // Shopify Customer Privacy banner (and any theme consent) — record presence as evidence, then accept
  try {
    const btn = s.page.locator('#shopify-pc__banner button.shopify-pc__banner__btn-accept, button:has-text("Accept")').first();
    if (await btn.isVisible({ timeout: 1500 })) {
      await s.check('cookie-consent', { present: true, note: 'modal shown before content; accepted to proceed' });
      await btn.click({ timeout: 4000 });
      await sleep(800);
      return true;
    }
  } catch (e) {}
  await s.check('cookie-consent', { present: false });
  return false;
}

async function selectSize(s, want) {
  // NEW theme buttons, then radio/label pickers, then <select>
  const labels = [`button.crk-size[data-value="${want}"]`, `label:has-text("${want}")`, `variant-picker label:has-text("${want}")`, `fieldset label:has-text("${want}")`];
  for (const sel of labels) {
    try {
      const loc = s.page.locator(sel).filter({ hasText: new RegExp(`^\\s*${want}\\s*$`) }).first();
      if (await loc.isVisible({ timeout: 700 })) {
        await loc.click({ timeout: 4000 });
        s.log({ type: 'action', note: 'select-size', ok: true, how: sel, value: want });
        return true;
      }
    } catch (e) {}
  }
  try {
    const selEl = s.page.locator('select').filter({ has: s.page.locator(`option:has-text("${want}")`) }).first();
    if (await selEl.isVisible({ timeout: 700 })) {
      await selEl.selectOption({ label: want });
      s.log({ type: 'action', note: 'select-size', ok: true, how: 'select', value: want });
      return true;
    }
  } catch (e) {}
  s.log({ type: 'action', note: 'select-size', ok: false, value: want });
  return false;
}

async function variantStateCheck(s) {
  try {
    const read = () => s.page.evaluate(() => {
      const k = document.querySelector('button.crk-size[data-selected="true"]');
      const c = document.querySelector('input[type="radio"]:checked');
      const sel = document.querySelector('select');
      return (k && k.dataset.value) || (c && (c.value || c.id)) || (sel && sel.value) || null;
    });
    const before = await read();
    await s.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await sleep(700);
    await s.page.evaluate(() => window.scrollTo(0, 0));
    await sleep(700);
    const after = await read();
    await s.check('variant-persistence', { before, after, stable: before === after });
  } catch (e) { await s.check('variant-persistence', { err: e.message.slice(0, 120) }); }
}

async function stickyAtcCheck(s) {
  if (s.deviceKey !== 'mobile') return;
  try {
    await s.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.6));
    await sleep(800);
    const sticky = await s.page.evaluate(() => {
      const vh = window.innerHeight;
      const els = Array.from(document.querySelectorAll('button, a')).filter((e) => {
        const t = (e.textContent || '').toLowerCase();
        if (!/add|cart|buy/.test(t)) return false;
        const r = e.getBoundingClientRect();
        if (r.top < 0 || r.bottom > vh || r.width === 0) return false;
        let n = e;
        while (n && n !== document.body) {
          const cs = getComputedStyle(n);
          if (cs.position === 'fixed' || cs.position === 'sticky') return true;
          n = n.parentElement;
        }
        return false;
      });
      return els.length > 0;
    });
    await s.check('sticky-atc-on-scroll', { sticky });
    await s.step('pdp-scrolled', { note: 'sticky-atc evidence' });
    await s.page.evaluate(() => window.scrollTo(0, 0));
    await sleep(500);
  } catch (e) { await s.check('sticky-atc-on-scroll', { err: e.message.slice(0, 120) }); }
}

async function detectCartMode(s) {
  try {
    const onCartPage = new URL(s.page.url()).pathname === '/cart';
    const drawer = await s.page.evaluate(() => {
      const cands = document.querySelectorAll('dialog[open], [class*="cart-drawer"], [id*="cart-drawer" i], [class*="crk-cart"], [aria-modal="true"]');
      for (const el of cands) {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        if (r.width > 100 && cs.visibility !== 'hidden' && cs.display !== 'none') return true;
      }
      return false;
    });
    const mode = onCartPage ? 'page' : drawer ? 'drawer' : 'none-visible';
    await s.check('cart-mode', { mode });
    return mode;
  } catch (e) { await s.check('cart-mode', { err: e.message.slice(0, 120) }); return 'unknown'; }
}

async function focusTrapCheck(s) {
  try {
    const inTrap = [];
    for (let i = 0; i < 10; i++) {
      await s.page.keyboard.press('Tab');
      await sleep(120);
      const where = await s.page.evaluate(() => {
        const a = document.activeElement;
        if (!a) return 'none';
        const drawer = a.closest('dialog, [class*="cart-drawer"], [id*="cart-drawer" i], [class*="crk-cart"], [aria-modal="true"]');
        return drawer ? 'in-drawer' : (a.tagName + '.' + (a.className || '').toString().slice(0, 40));
      });
      inTrap.push(where);
    }
    const trapped = inTrap.filter((w) => w === 'in-drawer').length >= 8;
    await s.check('cart-drawer-focus-trap', { trapped, sample: inTrap.slice(0, 10) });
  } catch (e) { await s.check('cart-drawer-focus-trap', { err: e.message.slice(0, 120) }); }
}

async function openCart(s) {
  const mode = await detectCartMode(s);
  if (mode === 'drawer' || mode === 'page') return mode;
  await s.think();
  const clicked = await s.tryClick(SEL.cartTrigger, 'open-cart');
  await sleep(1200);
  const m2 = await detectCartMode(s);
  if (m2 !== 'none-visible' && m2 !== 'unknown') return m2;
  if (!clicked) { await s.goto('/cart', 'cart-fallback'); return 'page'; }
  return m2;
}

async function goCheckout(s) {
  await s.think();
  const clicked = await s.tryClick(SEL.checkout, 'go-checkout');
  if (clicked) {
    await s.page.waitForURL(/checkout|\/cn\/|\/checkouts\//, { timeout: 20000 }).catch(() => {});
    await sleep(1500);
  }
  if (!/checkout|\/cn\/|\/checkouts\//.test(s.page.url())) {
    s.log({ type: 'action', note: 'checkout-click-did-not-navigate', ok: false, clicked: clicked || 'none', url: s.page.url().slice(0, 120) });
    await s.step('checkout-click-failed', { note: 'evidence: checkout affordance did not navigate' });
    await s.goto('/checkout', 'checkout-fallback');
    await sleep(1500);
  }
  await s.step('checkout', { note: 'STOP — never submit' });
}

/* Route from homepage to a PDP "the fastest way the theme offers". */
async function routeToProduct(s, productPath, collectionFallback) {
  const handle = productPath.split('/').pop();
  // 1) direct product link on the page?
  if (await clickProductLink(s, handle)) {
    s.log({ type: 'action', note: 'route-to-product', ok: true, how: 'direct-home-link' });
    await s.assertTheme('pdp-arrival');
    return 'direct-home-link';
  }
  // 2) via nav/menu to a collection
  const opened = await openMobileMenuIfNeeded(s);
  if (opened) { await sleep(800); await s.step('menu-open'); }
  const navClicked = await s.tryClick(
    [`a[href="${collectionFallback}"]`, `a[href*="${collectionFallback}"]`, 'a[href*="/collections/new"]', 'a[href*="/collections/all"]'],
    'nav-to-collection'
  );
  if (navClicked) {
    await s.page.waitForURL(/\/collections\//, { timeout: 15000 }).catch(() => {});
    await sleep(1500);
    await s.assertTheme('collection');
    await s.step('collection');
    if (await clickProductLink(s, handle)) {
      s.log({ type: 'action', note: 'route-to-product', ok: true, how: 'menu>collection>card' });
      await s.assertTheme('pdp-arrival');
      return 'menu>collection>card';
    }
  }
  // 3) give up politely: direct URL (logged as friction evidence)
  s.log({ type: 'action', note: 'route-to-product', ok: false, how: 'fallback-direct-url' });
  await s.goto(productPath, 'pdp-direct-fallback');
  return 'fallback-direct-url';
}

/* ---------------- journeys ---------------- */

async function j1_buy_now(s) {
  await s.goto('/', 'home');
  await s.step('home', { note: 'five-second source' });
  await dismissConsent(s);
  await tapTargets(s, { menu: SEL.menuToggle, search: SEL.searchTrigger, cart: SEL.cartTrigger });
  await s.think();
  const route = await routeToProduct(s, P.crewneck, '/collections/sweats');
  await s.step('pdp', { route });
  await tapTargets(s, { atc: SEL.atc });
  await s.think();
  await selectSize(s, 'M');
  await sleep(600);
  await s.step('variant-selected');
  await variantStateCheck(s);
  await stickyAtcCheck(s);
  await s.tryClick(SEL.atc, 'add-to-cart');
  await sleep(1800);
  await s.step('after-atc');
  const mode = await openCart(s);
  await s.step('cart', { cartMode: mode });
  if (mode === 'drawer') await focusTrapCheck(s);
  await goCheckout(s);
}

async function j2_search_buy(s) {
  await s.goto('/', 'home');
  await s.step('home', { note: 'five-second source' });
  await dismissConsent(s);
  await s.think();
  const trig = await s.tryClick(SEL.searchTrigger, 'open-search');
  await sleep(900);
  let typed = false;
  if (trig) {
    for (const sel of SEL.searchInput) {
      try {
        const inp = s.page.locator(sel).first();
        if (await inp.isVisible({ timeout: 800 })) {
          await inp.click();
          await s.page.keyboard.type('jeans', { delay: 90 });
          typed = true;
          await sleep(1400);
          await s.step('search-suggest');
          await s.page.keyboard.press('Enter');
          await s.page.waitForURL(/\/search/, { timeout: 12000 }).catch(() => {});
          break;
        }
      } catch (e) {}
    }
  }
  if (!typed) {
    s.log({ type: 'action', note: 'search-ui', ok: false, how: 'fallback-url' });
    await s.goto('/search?q=jeans', 'search-fallback');
  }
  await sleep(1200);
  await s.assertTheme('results');
  await s.step('results');
  await s.think();
  if (!(await clickProductLink(s, 'cb2-wash-jeans'))) {
    await s.tryClick(['a[href*="/products/"]'], 'first-result');
    await s.page.waitForURL(/\/products\//, { timeout: 15000 }).catch(() => {});
  }
  await sleep(600);
  await s.assertTheme('pdp');
  await s.step('pdp');
  await selectSize(s, 'M');
  await sleep(500);
  await s.tryClick(SEL.atc, 'add-to-cart');
  await sleep(1800);
  await s.step('after-atc');
  const mode = await openCart(s);
  await s.step('cart', { cartMode: mode });
  await goCheckout(s);
}

async function findInPage(s, name, regex) {
  const t = Date.now();
  try {
    const found = await s.page.evaluate((re) => {
      const rx = new RegExp(re, 'i');
      const els = Array.from(document.querySelectorAll('summary, button, a, h2, h3, [class*="accordion"] *'));
      for (const el of els) {
        const txt = (el.textContent || '').trim();
        if (txt.length < 80 && rx.test(txt)) {
          const r = el.getBoundingClientRect();
          return { text: txt.slice(0, 60), tag: el.tagName, y: Math.round(r.top + window.scrollY), clickable: ['SUMMARY', 'BUTTON', 'A'].includes(el.tagName) };
        }
      }
      return null;
    }, regex);
    await s.check('pdp-find-' + name, { found: !!found, detail: found, ms: Date.now() - t });
    return found;
  } catch (e) { await s.check('pdp-find-' + name, { found: false, err: e.message.slice(0, 100) }); return null; }
}

async function j3_research(s) {
  await s.goto(P.crewneck, 'pdp-landing (ad click)');
  await s.step('pdp-landing', { note: 'five-second source for research intent' });
  await dismissConsent(s);
  await s.think();
  // buy box evaluation: what is visible without scrolling
  await s.check('buybox-viewport', {
    visible: await s.page.evaluate(() => {
      const vh = window.innerHeight;
      const vis = (sel) => { const e = document.querySelector(sel); if (!e) return false; const r = e.getBoundingClientRect(); return r.top < vh && r.bottom > 0 && r.width > 0; };
      return {
        price: vis('[class*="price"]'),
        atc: vis('button[name="add"], form[action*="/cart/add"] button[type="submit"]'),
        variantPicker: vis('variant-picker, fieldset, select'),
      };
    }).catch(() => null),
  });
  // in-funnel hunts
  const ship = await findInPage(s, 'shipping', 'shipping|delivery');
  if (ship && ship.clickable) {
    await s.page.evaluate((y) => window.scrollTo(0, Math.max(0, y - 200)), ship.y);
    await sleep(600);
    const sel = ship.tag === 'SUMMARY' ? `summary:has-text("${ship.text.slice(0, 25)}")` : `${ship.tag.toLowerCase()}:has-text("${ship.text.slice(0, 25)}")`;
    await s.tryClick([sel], 'open-shipping-info');
    await sleep(700);
    await s.step('shipping-info');
  }
  const ret = await findInPage(s, 'returns', 'returns?|refund');
  if (ret && ret.clickable) {
    await s.tryClick([`${ret.tag.toLowerCase()}:has-text("${ret.text.slice(0, 25)}")`], 'open-returns-info');
    await sleep(700);
    await s.step('returns-info');
  }
  await findInPage(s, 'reviews', 'review|rating|stars');
  await s.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(900);
  await s.step('pdp-bottom', { note: 'evidence for shipping/returns/reviews presence below fold' });
  await s.page.evaluate(() => window.scrollTo(0, 0)); await sleep(500);
  // compare: prefer on-page recommendation link
  let how = 'recommendation';
  try {
    const rec = s.page.locator(`a[href*="/products/"]:not([href*="charcoal-cellblock-crewneck"])`).last();
    await rec.scrollIntoViewIfNeeded({ timeout: 3000 });
    await s.think();
    await rec.click({ timeout: 5000 });
    await s.page.waitForURL(/\/products\//, { timeout: 12000 });
  } catch (e) { how = 'direct-url'; await s.goto(P.shorts, 'compare-direct'); }
  await sleep(1000);
  await s.assertTheme('compare-pdp');
  await s.step('pdp-compare', { how });
  await selectSize(s, 'M');
  await sleep(400);
  await s.tryClick(SEL.atc, 'add-to-cart');
  await sleep(1600);
  await s.step('after-atc');
}

async function j4_browse(s) {
  await s.goto('/', 'home');
  await s.step('home', { note: 'five-second source' });
  await dismissConsent(s);
  await s.think();
  const opened = await openMobileMenuIfNeeded(s);
  if (opened) { await sleep(700); await s.step('menu-open'); }
  const nav = await s.tryClick([`a[href="${P.collectionAll}"]`, `a[href*="/collections/all"]`], 'nav-to-all');
  if (!nav) await s.goto(P.collectionAll, 'collection-fallback');
  await s.page.waitForURL(/\/collections\//, { timeout: 15000 }).catch(() => {});
  await sleep(1200);
  await s.assertTheme('collection');
  await s.step('collection');
  // filter/sort
  const facet = await s.tryClick(
    ['button:has-text("Filter")', 'button:has-text("Sort")', 'summary:has-text("Filter")', 'summary:has-text("Sort")', '[aria-controls*="filter" i]', '[class*="facet"] button', 'select[name*="sort" i]'],
    'open-filter-sort'
  );
  await sleep(900);
  if (facet) await s.step('filter-open');
  let sorted = false;
  try {
    const sel = s.page.locator('select[name*="sort" i], select[id*="sort" i]').first();
    if (await sel.isVisible({ timeout: 800 })) { await sel.selectOption({ value: 'price-ascending' }).catch(() => sel.selectOption({ index: 2 })); sorted = true; }
  } catch (e) {}
  if (!sorted) {
    const opt = await s.tryClick(['a[href*="sort_by=price-ascending"]', 'label:has-text("Price, low to high")', 'button:has-text("Low to high")', 'input[value="price-ascending"]'], 'sort-low-high');
    if (!opt) { await s.goto(P.collectionAll + '?sort_by=price-ascending', 'sort-fallback-url'); sorted = 'url'; }
  }
  await sleep(1500);
  await s.step('filtered', { sortedVia: sorted });
  const urlAfterFilter = s.page.url();
  // open 3 PDPs with back button between (distinct visible cards)
  let handles = [];
  try {
    handles = await s.page.evaluate(() => {
      const hs = [];
      for (const a of document.querySelectorAll('a[href*="/products/"]')) {
        const m = a.href.match(/\/products\/([a-z0-9-]+)/);
        if (m && a.getBoundingClientRect().width > 0 && !hs.includes(m[1])) hs.push(m[1]);
      }
      return hs.slice(0, 3);
    });
  } catch (e) {}
  for (let i = 0; i < Math.min(3, Math.max(handles.length, 3)); i++) {
    try {
      const clicked = handles[i] ? await clickProductLink(s, handles[i]) : false;
      if (!clicked) { s.log({ type: 'action', note: 'browse-card-' + (i + 1), ok: false }); continue; }
      await s.assertTheme('pdp-' + (i + 1));
      await s.step(`pdp-${i + 1}`);
      await s.think();
      await s.page.goBack({ timeout: 15000 }).catch(() => {});
      await sleep(1200);
      const backUrl = s.page.url();
      await s.check('back-after-filter-' + (i + 1), {
        backUrl: backUrl.slice(0, 140),
        filterSurvived: backUrl === urlAfterFilter,
        landedOnCollection: backUrl.includes('/collections/'),
      });
      if (i === 0) await s.step('back-1');
    } catch (e) { s.log({ type: 'action', note: 'browse-pdp-' + (i + 1), ok: false, err: e.message.slice(0, 120) }); }
  }
  // return home via logo
  const logo = await s.tryClick(['header a[href="/"]', 'a[class*="logo"]', 'header a:has(img)'], 'logo-home');
  if (!logo) await s.goto('/', 'home-return-fallback');
  await sleep(1000);
  await s.step('home-return');
}

async function j5_gift(s) {
  await s.goto('/', 'home');
  await s.step('home', { note: 'five-second source' });
  await dismissConsent(s);
  await s.think();
  const opened = await openMobileMenuIfNeeded(s);
  if (opened) await sleep(600);
  const nav = await s.tryClick([`a[href="${P.collectionAll}"]`, 'a[href*="/collections/all"]'], 'nav-to-all');
  if (!nav) await s.goto(P.collectionAll, 'collection-fallback');
  await sleep(1200);
  await s.step('collection');
  // price filter attempt (budget cap £100 => any; try the facet anyway and record)
  const priceFacet = await s.tryClick(
    ['summary:has-text("Price")', 'button:has-text("Price")', 'label:has-text("Price")', '[aria-controls*="price" i]'],
    'open-price-filter'
  );
  await sleep(800);
  await s.check('price-filter-available', { available: !!priceFacet });
  if (priceFacet) await s.step('price-filter');
  await s.think();
  // gift target: grey OG jeans
  if (!(await clickProductLink(s, 'cb1-wash-jeans'))) await s.goto(P.jeansGrey, 'gift-pdp-fallback');
  await sleep(600);
  await s.assertTheme('gift-pdp');
  await s.step('pdp');
  await findInPage(s, 'gift-options', 'gift|wrap|note');
  await selectSize(s, 'M');
  await sleep(500);
  await s.tryClick(SEL.atc, 'add-to-cart');
  await sleep(1800);
  await s.step('after-atc');
  const mode = await openCart(s);
  // gift/cart note affordance in cart
  const note = await s.page.evaluate(() => {
    const el = document.querySelector('textarea[name*="note" i], [class*="cart-note"], summary, label');
    const cands = Array.from(document.querySelectorAll('textarea, summary, label, button')).filter((e) => /note|gift/i.test(e.textContent || '') || /note/i.test(e.getAttribute('name') || ''));
    return cands.length ? cands[0].textContent.trim().slice(0, 60) || 'unnamed-note-field' : null;
  }).catch(() => null);
  await s.check('cart-gift-note', { found: !!note, detail: note });
  await s.step('cart', { cartMode: mode });
}

async function j6_support(s) {
  await s.goto('/', 'home');
  await s.step('home');
  await dismissConsent(s);
  const items = [
    { name: 'shipping-policy', hrefs: ['a[href*="shipping-policy"]'], urlFallback: '/policies/shipping-policy' },
    { name: 'returns', hrefs: ['a[href*="refund-policy"]', 'a[href*="return"]'], urlFallback: '/policies/refund-policy' },
    { name: 'contact', hrefs: ['a[href*="contact"]'], urlFallback: '/pages/contact' },
  ];
  for (const item of items) {
    const t = Date.now();
    // scroll to footer to look for the link the way a human would
    await s.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(900);
    if (item.name === 'shipping-policy') await s.step('footer', { note: 'support-links evidence' });
    let how = null;
    for (const sel of item.hrefs) {
      try {
        const loc = s.page.locator(sel).first();
        if (await loc.isVisible({ timeout: 800 })) { await loc.click({ timeout: 5000 }); how = 'footer-link:' + sel; break; }
      } catch (e) {}
    }
    if (!how) {
      // try the mobile menu drawer
      await s.page.evaluate(() => window.scrollTo(0, 0)); await sleep(400);
      const opened = await openMobileMenuIfNeeded(s);
      if (opened) {
        await sleep(600);
        for (const sel of item.hrefs) {
          try {
            const loc = s.page.locator(sel).first();
            if (await loc.isVisible({ timeout: 700 })) { await loc.click({ timeout: 5000 }); how = 'menu-link:' + sel; break; }
          } catch (e) {}
        }
        if (!how) await s.page.keyboard.press('Escape').catch(() => {});
      }
    }
    if (!how) { how = 'not-found-in-ui'; await s.goto(item.urlFallback, item.name + '-fallback'); }
    await sleep(1100);
    await s.check('support-' + item.name, { how, ms: Date.now() - t, url: s.page.url().slice(0, 120) });
    await s.step(item.name);
    await s.goto('/', 'home-again'); await sleep(400);
  }
  // size guide: must live on PDP if anywhere (no /pages/size-guide)
  const t = Date.now();
  await s.goto(P.crewneck, 'pdp-for-size-guide');
  const sg = await findInPage(s, 'size-guide', 'size (guide|chart)|sizing');
  if (sg && sg.clickable) {
    await s.tryClick([`${sg.tag.toLowerCase()}:has-text("${sg.text.slice(0, 20)}")`], 'open-size-guide');
    await sleep(800);
  }
  await s.check('support-size-guide', { found: !!sg, ms: Date.now() - t });
  await s.step('size-guide');
  // order tracking
  const t2 = Date.now();
  await s.goto('/', 'home-for-tracking');
  await s.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(800);
  let how2 = null;
  try {
    const loc = s.page.locator('a[href*="tracking"], a[href*="track"]').first();
    if (await loc.isVisible({ timeout: 900 })) { await loc.click({ timeout: 5000 }); how2 = 'footer-link'; }
  } catch (e) {}
  if (!how2) {
    const opened = await openMobileMenuIfNeeded(s);
    if (opened) {
      await sleep(600);
      try {
        const loc = s.page.locator('a[href*="tracking"], a[href*="track"]').first();
        if (await loc.isVisible({ timeout: 700 })) { await loc.click({ timeout: 5000 }); how2 = 'menu-link'; }
      } catch (e) {}
    }
  }
  if (!how2) { how2 = 'not-found-in-ui'; await s.goto('/pages/tracking', 'tracking-fallback'); }
  await sleep(1000);
  await s.check('support-tracking', { how: how2, ms: Date.now() - t2, url: s.page.url().slice(0, 120) });
  await s.step('tracking');
}

async function j7_returning(s) {
  await s.goto('/', 'home');
  await s.step('home', { note: 'five-second source' });
  await dismissConsent(s);
  await s.think();
  const trig = await s.tryClick(SEL.searchTrigger, 'open-search');
  await sleep(800);
  let typed = false;
  if (trig) {
    for (const sel of SEL.searchInput) {
      try {
        const inp = s.page.locator(sel).first();
        if (await inp.isVisible({ timeout: 800 })) {
          await inp.click();
          await s.page.keyboard.type('BLUE WASH JORTS', { delay: 70 });
          typed = true;
          await sleep(1300);
          await s.step('search-suggest');
          await s.page.keyboard.press('Enter');
          await s.page.waitForURL(/\/search/, { timeout: 12000 }).catch(() => {});
          break;
        }
      } catch (e) {}
    }
  }
  if (!typed) await s.goto('/search?q=BLUE+WASH+JORTS', 'search-fallback');
  await sleep(1200);
  await s.step('results');
  if (!(await clickProductLink(s, 'cb1-wash-jorts'))) await s.goto(P.jortsBlue, 'pdp-fallback');
  await sleep(600);
  await s.assertTheme('pdp');
  await s.step('pdp');
  // account entry
  await s.page.evaluate(() => window.scrollTo(0, 0)); await sleep(300);
  let accHow = await s.tryClick(SEL.accountEntry, 'account-entry-header');
  if (!accHow) {
    const opened = await openMobileMenuIfNeeded(s);
    if (opened) { await sleep(600); accHow = await s.tryClick(SEL.accountEntry, 'account-entry-menu'); }
  }
  if (!accHow) {
    await s.check('account-entry', { found: false, note: 'no visible account entry in header or menu' });
    await s.goto('/account/login', 'account-fallback');
  } else {
    await sleep(2500); // hosted login may redirect
  }
  await s.step('account-login', { note: 'STOP — no credentials, no signup' });
  await s.check('account-entry', { found: !!accHow, how: accHow || 'direct-url', url: s.page.url().slice(0, 140) });
  // reorder-friendly paths: back to store, check recently-viewed/reorder affordances on home
  await s.goto('/', 'home-after-account');
  const reorder = await s.page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('a, h2, h3, button')).filter((e) => /recently viewed|buy again|reorder|order history/i.test(e.textContent || ''));
    return els.map((e) => (e.textContent || '').trim().slice(0, 50)).slice(0, 5);
  }).catch(() => []);
  await s.check('reorder-affordances', { found: reorder.length > 0, detail: reorder });
  await s.step('home-end');
}

/* ---------------- edge sweep (mobile) ---------------- */

async function edge_sweep(s) {
  // typo search
  await s.goto('/search?q=charcol+crewneck', 'typo-search');
  await s.step('typo-results');
  await dismissConsent(s);
  // zero results
  await s.goto('/search?q=xyzzyplugh', 'zero-results');
  await s.step('zero-results');
  // 404
  await s.goto('/products/this-does-not-exist', '404');
  await s.step('404');
  // OOS variant
  await s.goto(P.baggies, 'oos-pdp');
  await s.step('oos-pdp');
  try {
    const state = await s.page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('variant-picker input[type="radio"], fieldset input[type="radio"]'));
      return inputs.map((i) => {
        const lbl = document.querySelector(`label[for="${i.id}"]`);
        return { value: i.value, disabled: i.disabled, cls: (lbl ? lbl.className : '').slice(0, 80) };
      });
    });
    await s.check('oos-variant-states', { variants: state });
    // click through sizes to find one that shows sold-out UI
    for (const size of ['S', 'M', 'L', 'XL', 'XXL']) {
      await selectSize(s, size);
      await sleep(700);
      const atcState = await s.page.evaluate(() => {
        const b = document.querySelector('button[name="add"], form[action*="/cart/add"] button[type="submit"]');
        return b ? { text: (b.textContent || '').trim().slice(0, 40), disabled: b.disabled } : null;
      });
      if (atcState && (atcState.disabled || /sold|unavailable|out/i.test(atcState.text))) {
        await s.check('oos-ui', { size, atcState });
        await s.step('oos-variant', { size });
        break;
      }
    }
  } catch (e) { await s.check('oos-ui', { err: e.message.slice(0, 120) }); }
  // cart quantity edit + remove + discount field
  await s.goto(P.crewneck, 'cart-ops-pdp');
  await selectSize(s, 'M');
  await sleep(400);
  await s.tryClick(SEL.atc, 'add-to-cart');
  await sleep(1800);
  const mode = await openCart(s);
  await s.step('cart-before-ops', { cartMode: mode });
  const plus = await s.tryClick(
    ['button[name="plus"]', 'button[aria-label*="increase" i]', 'button:has-text("+")', '[class*="quantity"] button:last-of-type'],
    'qty-increase'
  );
  await sleep(1500);
  await s.step('cart-qty', { plusClicked: !!plus });
  const discount = await s.page.evaluate(() => {
    const el = document.querySelector('input[name*="discount" i], input[placeholder*="discount" i], input[placeholder*="code" i], [class*="discount"]');
    return el ? (el.getAttribute('placeholder') || el.className || el.name || 'present').slice(0, 60) : null;
  }).catch(() => null);
  await s.check('discount-field-in-cart', { found: !!discount, detail: discount });
  const removed = await s.tryClick(
    ['button[aria-label*="remove" i]', 'a[href*="quantity=0"]', 'button:has-text("Remove")', 'cart-remove-button button', '[class*="remove"]'],
    'remove-item'
  );
  await sleep(1500);
  await s.step('cart-removed', { removed: !!removed });
  // discount field at checkout: re-add and go
  await s.goto(P.crewneck, 'checkout-discount-pdp');
  await selectSize(s, 'M');
  await sleep(400);
  await s.tryClick(SEL.atc, 'add-to-cart');
  await sleep(1500);
  await openCart(s);
  await s.tryClick(SEL.checkout, 'go-checkout');
  await s.page.waitForURL(/checkout|\/cn\/|\/checkouts\//, { timeout: 30000 }).catch(() => {});
  await sleep(2000);
  const discountCheckout = await s.page.evaluate(() => {
    const el = document.querySelector('input[name*="reduction" i], input[placeholder*="discount" i], input[placeholder*="gift card" i], input[id*="reduction" i]');
    return el ? (el.getAttribute('placeholder') || 'present').slice(0, 60) : null;
  }).catch(() => null);
  await s.check('discount-field-at-checkout', { found: !!discountCheckout, detail: discountCheckout });
  await s.step('discount-checkout', { note: 'STOP — never submit' });
}

async function edge_slow4g(s) {
  const cdp = await s.ctx.newCDPSession(s.page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false, latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8,
  });
  for (const [label, url] of [['slow4g-home', '/'], ['slow4g-pdp', P.crewneck]]) {
    const t = Date.now();
    const nav = s.page.goto(s.theme.base + url, { waitUntil: 'load', timeout: 90000 }).catch((e) => ({ err: e.message }));
    await sleep(3000);
    await s.step(label + '-at-3s', { note: 'what a slow-connection shopper sees after 3s' });
    await nav;
    const loadMs = Date.now() - t;
    let perf = null;
    try {
      perf = await s.page.evaluate(() => {
        const n = performance.getEntriesByType('navigation')[0];
        const fcp = performance.getEntriesByName('first-contentful-paint')[0];
        return { load: n ? Math.round(n.loadEventEnd) : null, fcp: fcp ? Math.round(fcp.startTime) : null };
      });
    } catch (e) {}
    await s.check(label, { loadMs, perf });
    await s.assertTheme(label);
    await s.step(label + '-loaded');
    await dismissConsent(s);
  }
}

async function edge_zoom200(s) {
  let first = true;
  for (const [label, url] of [['zoom-home', '/'], ['zoom-pdp', P.crewneck]]) {
    await s.goto(url, label);
    if (first) { await dismissConsent(s); first = false; }
    await s.page.evaluate(() => { document.body.style.zoom = '2'; });
    await sleep(1200);
    await s.step(label + '-200pct', { note: 'low-vision evidence: 200% zoom desktop' });
  }
}

/* ---------------- runner ---------------- */

const JOURNEYS = {
  j1: j1_buy_now, j2: j2_search_buy, j3: j3_research, j4: j4_browse,
  j5: j5_gift, j6: j6_support, j7: j7_returning,
};

async function runSession(browser, themeKey, journey, deviceKey, fn) {
  const s = new Session(browser, themeKey, journey, deviceKey);
  await s.init();
  const started = Date.now();
  try {
    await fn(s);
    console.log(`[done] ${themeKey}/${journey}/${deviceKey} in ${Math.round((Date.now() - started) / 1000)}s${s.poisoned ? '  !! POISONED' : ''}`);
  } catch (e) {
    s.log({ type: 'journey-error', err: e.message.slice(0, 300) });
    try { await s.step('journey-error'); } catch (e2) {}
    console.log(`[ERR ] ${themeKey}/${journey}/${deviceKey}: ${e.message.split('\n')[0]}`);
  }
  await s.close();
}

(async () => {
  const only = process.argv[2] || ''; // e.g. "old:j1:mobile" or "new" or ":j2"
  const [fTheme, fJourney, fDevice] = only.split(':');
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    args: ['--ssl-version-max=tls1.2', '--disable-background-networking', '--disable-component-update'],
  });

  const themeKeys = Object.keys(THEMES).filter((t) => !fTheme || t === fTheme);
  // one worker per theme => max 2 concurrent pages
  await Promise.all(themeKeys.map(async (themeKey) => {
    for (const journey of Object.keys(JOURNEYS).filter((j) => !fJourney || j === fJourney)) {
      for (const deviceKey of ['mobile', 'desktop'].filter((d) => !fDevice || d === fDevice)) {
        await runSession(browser, themeKey, journey, deviceKey, JOURNEYS[journey]);
      }
    }
    if (!fJourney || fJourney === 'edge') {
      if (!fDevice || fDevice === 'mobile') {
        await runSession(browser, themeKey, 'edge', 'mobile', edge_sweep);
        await runSession(browser, themeKey, 'edge-slow4g', 'mobile', edge_slow4g);
      }
      if (!fDevice || fDevice === 'desktop') {
        await runSession(browser, themeKey, 'edge-zoom', 'desktop', edge_zoom200);
      }
    }
  }));

  await browser.close();
  console.log('ALL CAPTURES COMPLETE');
})().catch((e) => { console.error('RUNNER FAIL', e); process.exit(1); });
