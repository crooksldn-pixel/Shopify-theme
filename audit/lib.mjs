import { chromium } from 'playwright';
import fs from 'fs';

export const BASE = 'https://bbushaa5dr2elw8f-100410786135.shopifypreview.com';
export const PROXY = 'http://127.0.0.1:38081';

export const PAGES = {
  home:      { url: BASE + '/',                            label: 'Homepage' },
  pdpTee:    { url: BASE + '/products/3-clives-tee',       label: 'PDP — 3 CLIVES TEE' },
  pdpDenim:  { url: BASE + '/products/cb2-wash-jeans',     label: 'PDP — BLUE WASH OG JEANS (cb2-wash-jeans, £60)' },
  cart:      { url: BASE + '/cart',                        label: 'Cart' },
};

export const MOBILE = {
  viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
};
export const ANDROID = {
  viewport: { width: 360, height: 800 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
};
export const DESKTOP = { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, isMobile: false, hasTouch: false };

export const THROTTLE = {
  // "Slow 4G": ~1.6 Mbps down, 750 Kbps up, 150ms RTT
  download: (1.6 * 1024 * 1024) / 8,
  upload: (750 * 1024) / 8,
  latency: 150,
  cpu: 4,
};

export async function launch() {
  return chromium.launch({ args: ['--no-sandbox', `--proxy-server=${PROXY}`, '--ignore-certificate-errors', '--disable-dev-shm-usage'] });
}

export async function newContext(browser, device = MOBILE, extra = {}) {
  return browser.newContext({ ...device, ignoreHTTPSErrors: true, locale: 'en-GB', timezoneId: 'Europe/London', ...extra });
}

/**
 * Visit the preview root so the preview session cookie is set for this context,
 * then force the GB market. The session's egress proxy exits in the US, so Shopify
 * Markets otherwise geolocates the browser to country=US and converts every price
 * to USD at ~1.376 — a harness artefact, not a site behaviour. A real UK shopper
 * sees GBP, so we pin GBP before measuring anything.
 */
export async function primePreview(context, { forceGB = true } = {}) {
  // Share links can be invalidated mid-run (a theme push kills outstanding links).
  // Establish the preview session ONCE, persist its cookies, and reuse them in every
  // later context so the link only needs to be alive for the first priming.
  const STATE = 'audit/.preview-state.json';
  if (forceGB) {
    await context.addCookies([{ name: 'cart_currency', value: 'GBP', domain: new URL(BASE).host, path: '/' }]);
  }
  const verify = async (p) => {
    await p.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });
    await p.waitForTimeout(1200);
    return p.evaluate(() => ({
      crk: !!document.querySelector('.crk-root'),
      theme: window.Shopify?.theme?.name,
      cur: window.Shopify?.currency?.active,
    }));
  };
  const p = await context.newPage();
  if (fs.existsSync(STATE)) {
    try {
      const saved = JSON.parse(fs.readFileSync(STATE, 'utf8'));
      await context.addCookies(saved.cookies.filter(c => c.name !== 'cart_currency'));
      const st = await verify(p);
      if (st.crk) { await p.close(); return st; }
      // saved session no longer serves the preview — fall through to a fresh prime
    } catch { /* corrupt state file — reprime */ }
  }
  const state = await verify(p);
  if (!state.crk) throw new Error('PREVIEW PRIMING FAILED — .crk-root absent; would be auditing the live theme.');
  const full = await context.storageState();
  fs.writeFileSync(STATE, JSON.stringify({ savedAt: new Date().toISOString(), cookies: full.cookies }, null, 2));
  await p.close();
  return state;
}

export async function applyThrottle(page, { cpu = THROTTLE.cpu, net = true } = {}) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  if (net) {
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false, downloadThroughput: THROTTLE.download, uploadThroughput: THROTTLE.upload, latency: THROTTLE.latency,
    });
  }
  if (cpu > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
  return cdp;
}

/** Byte-accurate transfer accounting straight off the wire via CDP. */
export function attachNetworkAccounting(cdp) {
  const byReqId = new Map();
  const finished = [];
  cdp.on('Network.requestWillBeSent', (e) => byReqId.set(e.requestId, { url: e.request.url, start: e.timestamp }));
  cdp.on('Network.responseReceived', (e) => {
    const r = byReqId.get(e.requestId) || {};
    Object.assign(r, {
      url: e.response.url, status: e.response.status, mimeType: e.response.mimeType, type: e.type,
      fromCache: e.response.fromDiskCache, protocol: e.response.protocol,
      contentEncoding: e.response.headers?.['content-encoding'] || e.response.headers?.['Content-Encoding'] || '',
    });
    byReqId.set(e.requestId, r);
  });
  cdp.on('Network.loadingFinished', (e) => {
    const r = byReqId.get(e.requestId);
    if (r) { r.encodedDataLength = e.encodedDataLength; finished.push(r); }
  });
  cdp.on('Network.loadingFailed', (e) => {
    const r = byReqId.get(e.requestId);
    if (r) { r.failed = e.errorText; finished.push(r); }
  });
  return finished;
}

/** Injected before any page script: web-vitals collection + rAF counting + first-product-image timing. */
export const INIT_SCRIPT = `
(() => {
  window.__crk = { lcp: 0, lcpEl: '', cls: 0, clsSources: [], inp: 0, longTasks: [], raf: 0, firstProductImg: null, shifts: [] };
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) {
        window.__crk.lcp = e.startTime;
        window.__crk.lcpEl = e.element ? (e.element.tagName + (e.element.id ? '#'+e.element.id : '') + (e.element.className && typeof e.element.className==='string' ? '.'+e.element.className.split(' ').slice(0,3).join('.') : '') + (e.url ? ' url='+e.url.split('/').pop().split('?')[0] : '')) : e.url || '(none)';
      }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) {
        if (!e.hadRecentInput) {
          window.__crk.cls += e.value;
          if (e.value > 0.005) window.__crk.shifts.push({ v: +e.value.toFixed(4), t: Math.round(e.startTime), src: (e.sources||[]).map(s => s.node ? (s.node.tagName||'') + '.' + ((s.node.className&&typeof s.node.className==='string') ? s.node.className.split(' ')[0] : '') : '?').slice(0,3) });
        }
      }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (e) {}
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) if (e.duration > window.__crk.inp) window.__crk.inp = e.duration;
    }).observe({ type: 'event', buffered: true, durationThreshold: 16 });
  } catch (e) {}
  try {
    new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__crk.longTasks.push({ t: Math.round(e.startTime), d: Math.round(e.duration) }); })
      .observe({ type: 'longtask', buffered: true });
  } catch (e) {}
  const _raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) { return _raf(function (ts) { window.__crk.raf++; return cb(ts); }); };
  // first product image actually painted inside the viewport
  const PRODUCT_IMG = 'img';
  const check = () => {
    if (window.__crk.firstProductImg !== null) return;
    for (const img of document.querySelectorAll(PRODUCT_IMG)) {
      const src = img.currentSrc || img.src || '';
      if (!/cdn\\.shopify|shopifycdn|\\/files\\//.test(src)) continue;
      if (!img.complete || !img.naturalWidth) continue;
      const r = img.getBoundingClientRect();
      if (r.width < 40 || r.height < 40) continue;
      if (r.bottom <= 0 || r.top >= innerHeight) continue;
      window.__crk.firstProductImg = { t: Math.round(performance.now()), src: src.split('/').pop().split('?')[0], w: Math.round(r.width), h: Math.round(r.height) };
      return;
    }
    _raf(check);
  };
  _raf(check);
})();
`;

export async function readVitals(page) {
  return page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0] || {};
    const paints = Object.fromEntries(performance.getEntriesByType('paint').map(p => [p.name, Math.round(p.startTime)]));
    return {
      lcp: Math.round(window.__crk?.lcp || 0),
      lcpElement: window.__crk?.lcpEl || '',
      cls: +((window.__crk?.cls || 0).toFixed(4)),
      clsShifts: (window.__crk?.shifts || []).slice(0, 8),
      inp: Math.round(window.__crk?.inp || 0),
      ttfb: Math.round(nav.responseStart || 0),
      domContentLoaded: Math.round(nav.domContentLoadedEventEnd || 0),
      loadEvent: Math.round(nav.loadEventEnd || 0),
      fcp: paints['first-contentful-paint'] ?? null,
      firstProductImage: window.__crk?.firstProductImg || null,
      longTasksOver50ms: (window.__crk?.longTasks || []).filter(t => t.d > 50).length,
      longTaskTotalMs: (window.__crk?.longTasks || []).reduce((a, t) => a + t.d, 0),
    };
  });
}

export function summariseBytes(finished) {
  const byType = {};
  let total = 0;
  const assets = [];
  for (const r of finished) {
    if (r.failed) continue;
    const len = r.encodedDataLength || 0;
    total += len;
    const t = classify(r);
    byType[t] = (byType[t] || 0) + len;
    assets.push({ name: r.url.split('/').pop().split('?')[0].slice(0, 70), host: safeHost(r.url), type: t, bytes: len, mime: r.mimeType, status: r.status });
  }
  assets.sort((a, b) => b.bytes - a.bytes);
  return { totalBytes: total, byType, top: assets.slice(0, 18), all: assets };
}
function safeHost(u) { try { return new URL(u).host; } catch { return '?'; } }
export function classify(r) {
  const m = r.mimeType || '';
  if (/^image\//.test(m)) return 'image';
  if (/javascript|ecmascript/.test(m)) return 'script';
  if (/css/.test(m)) return 'css';
  if (/font|woff/.test(m)) return 'font';
  if (/html/.test(m)) return 'document';
  if (/json/.test(m)) return 'json';
  return m ? 'other:' + m.split('/')[0] : 'other';
}
export const kb = (b) => Math.round(b / 1024) + ' KB';
