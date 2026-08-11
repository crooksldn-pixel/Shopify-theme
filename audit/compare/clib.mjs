// Site-agnostic audit library for the competitor comparison.
// Same TLS bridge as the crooks audit (audit/bridge.mjs on 127.0.0.1:38081).
import { chromium } from 'playwright';
import fs from 'fs';

export const PROXY = 'http://127.0.0.1:38081';

export const MOBILE = {
  viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
};
export const DESKTOP = { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, isMobile: false, hasTouch: false };

export const THROTTLE = { download: (1.6 * 1024 * 1024) / 8, upload: (750 * 1024) / 8, latency: 150, cpu: 4 };

export async function launch() {
  return chromium.launch({ args: ['--no-sandbox', `--proxy-server=${PROXY}`, '--ignore-certificate-errors', '--disable-dev-shm-usage'] });
}
export async function newContext(browser, device = MOBILE, extra = {}) {
  return browser.newContext({ ...device, ignoreHTTPSErrors: true, locale: 'en-GB', timezoneId: 'Europe/London', ...extra });
}
export async function applyThrottle(page, t = THROTTLE) {
  const c = await page.context().newCDPSession(page);
  await c.send('Network.enable');
  await c.send('Network.emulateNetworkConditions', { offline: false, downloadThroughput: t.download, uploadThroughput: t.upload, latency: t.latency });
  await c.send('Emulation.setCPUThrottlingRate', { rate: t.cpu });
  return c;
}

export function loadSite(tag) {
  return JSON.parse(fs.readFileSync(`audit/compare/sites/${tag}.json`, 'utf8'));
}
export function saveEvidence(tag, kind, data) {
  const p = `audit/compare/evidence/${tag}-${kind}.json`;
  fs.writeFileSync(p, JSON.stringify(data, null, 2));
  console.log('wrote', p);
}

export const VITALS_INIT = `
window.__v = { cls: 0, shifts: [], lcp: 0, lcpEl: null, inp: 0, longTasks: 0, longMs: 0 };
new PerformanceObserver(l => { for (const e of l.getEntries()) { window.__v.lcp = Math.round(e.startTime);
  window.__v.lcpEl = e.element ? (e.element.tagName + '.' + String(e.element.className).slice(0,60) + (e.element.currentSrc ? ' src=' + e.element.currentSrc.split('/').pop().split('?')[0] : '')) : null; } })
  .observe({ type: 'largest-contentful-paint', buffered: true });
new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) { window.__v.cls += e.value;
  if (e.value > 0.01) window.__v.shifts.push({ v: +e.value.toFixed(4), t: Math.round(e.startTime),
    src: (e.sources||[]).map(s => s.node ? String(s.node.className||s.node.tagName).slice(0,50) : '?') }); } })
  .observe({ type: 'layout-shift', buffered: true });
new PerformanceObserver(l => { for (const e of l.getEntries()) { window.__v.longTasks++; window.__v.longMs += Math.round(e.duration); } })
  .observe({ type: 'longtask', buffered: true });
new PerformanceObserver(l => { for (const e of l.getEntries()) { const d = e.processingEnd - e.startTime; if (d > window.__v.inp) window.__v.inp = Math.round(d); } })
  .observe({ type: 'event', buffered: true, durationThreshold: 40 });
`;

export async function collectVitals(page) {
  return page.evaluate(() => {
    // LCP can be 0 if the observer missed the entry (video/canvas hero, late observer
    // attach after a client-side redirect). Fall back to buffered entries; report null
    // rather than 0 so a miss is never read as "instant".
    if (!window.__v.lcp) {
      const es = performance.getEntriesByType('largest-contentful-paint');
      if (es.length) window.__v.lcp = Math.round(es[es.length - 1].startTime);
      else window.__v.lcp = null;
    }
    const nav = performance.getEntriesByType('navigation')[0] || {};
    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
    return { ...window.__v, shifts: window.__v.shifts.slice(0, 8),
      ttfb: Math.round(nav.responseStart || 0), fcp: Math.round(fcp ? fcp.startTime : 0),
      domContentLoaded: Math.round(nav.domContentLoadedEventEnd || 0), load: Math.round(nav.loadEventEnd || 0) };
  });
}

export function trackTransfer(page) {
  const assets = [];
  page.on('response', async (r) => {
    try {
      const req = r.request();
      let bytes = 0;
      try { bytes = (await r.body()).length; } catch { bytes = Number(r.headers()['content-length'] || 0); }
      assets.push({ url: r.url(), host: new URL(r.url()).host, type: req.resourceType(), status: r.status(), bytes, mime: (r.headers()['content-type'] || '').split(';')[0] });
    } catch {}
  });
  return {
    summary() {
      const total = assets.reduce((a, x) => a + x.bytes, 0);
      const byType = {};
      for (const a of assets) byType[a.type] = (byType[a.type] || 0) + a.bytes;
      for (const k in byType) byType[k] = Math.round(byType[k] / 1024);
      const largest = [...assets].sort((a, b) => b.bytes - a.bytes).slice(0, 8)
        .map(a => ({ name: a.url.split('/').pop().split('?')[0].slice(0, 60), host: a.host, kb: Math.round(a.bytes / 1024), type: a.type, mime: a.mime }));
      const thirdParty = {};
      for (const a of assets) { thirdParty[a.host] = (thirdParty[a.host] || 0) + a.bytes; }
      const tp = Object.entries(thirdParty).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([h, b]) => ({ host: h, kb: Math.round(b / 1024) }));
      return { totalKB: Math.round(total / 1024), requests: assets.length, byTypeKB: byType, largest, topHosts: tp };
    }
  };
}

// ---- generic commerce heuristics -------------------------------------------
export const HEURISTICS = `
window.__h = {
  atc() {
    const els = [...document.querySelectorAll('button, input[type=submit], a[role=button], a')];
    return els.find(e => /add to (cart|bag|basket)|^add$|buy now|purchase/i.test((e.innerText || e.value || '').trim()) && e.offsetParent !== null) || null;
  },
  price() {
    const m = document.body.innerText.match(/[£$€]\\s?\\d{1,4}(?:[.,]\\d{2})?/);
    return m ? m[0] : null;
  },
  sizeControls() {
    const sels = [...document.querySelectorAll('button, [role=radio], [role=option], select option, label, input[type=radio]')];
    return sels.filter(e => /^(XXS|XS|S|M|L|XL|XXL|2XL|3XL|\\d{2})$/i.test((e.innerText || e.textContent || e.value || '').trim()) && (e.offsetParent !== null || e.tagName === 'OPTION')).length;
  },
  overlays() {
    const out = [];
    for (const e of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(e);
      if ((cs.position === 'fixed' || cs.position === 'sticky') && e.offsetParent !== null) {
        const r = e.getBoundingClientRect();
        const pct = Math.round((Math.min(r.width, innerWidth) * Math.min(r.height, innerHeight)) / (innerWidth * innerHeight) * 100);
        if (pct >= 20 && Number(cs.zIndex) > 10) out.push({ cls: String(e.className).slice(0, 60), pct, z: cs.zIndex });
      }
    }
    return out.slice(0, 6);
  },
  cookieBanner() {
    const e = [...document.querySelectorAll('[class*=cookie i],[id*=cookie i],[class*=consent i],[id*=consent i],[id*=onetrust i],[class*=cmp i],[class*=gdpr i],[class*=privacy-banner i]')]
      .find(x => x.offsetParent !== null && x.getBoundingClientRect().height > 40);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cls: (e.className || e.id || '').toString().slice(0, 60), h: Math.round(r.height), pctOfViewport: Math.round(r.height / innerHeight * 100) };
  },
  trustWords() {
    const t = document.body.innerText;
    return {
      returns: /return|refund/i.test(t), shippingInfo: /shipping|delivery|dispatch/i.test(t),
      tracking: /track/i.test(t), contact: /contact/i.test(t),
      sizeGuide: /size (guide|chart)|measurements|fit guide/i.test(t),
      reviews: /reviews?|rated|stars|trustpilot/i.test(t),
      urgency: /only \\d+ left|selling fast|hurry|limited stock|\\d+ people (are )?(viewing|looking)/i.test(t),
      countdown: /\\d{1,2}:\\d{2}:\\d{2}/.test(t),
    };
  },
  seoSurface() {
    const g = (s) => document.querySelector(s);
    const ld = [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => { try { const d = JSON.parse(s.textContent); return Array.isArray(d) ? d.map(x => x['@type']).join(',') : d['@type']; } catch { return 'parse-error'; } });
    return {
      title: document.title, titleLen: document.title.length,
      metaDesc: g('meta[name=description]')?.content?.slice(0, 200) || null,
      h1: g('h1')?.innerText?.trim().slice(0, 90) || null,
      h1Count: document.querySelectorAll('h1').length,
      canonical: g('link[rel=canonical]')?.href || null,
      ogImage: !!g('meta[property="og:image"]'), jsonLdTypes: ld,
      robotsMeta: g('meta[name=robots]')?.content || null,
      wordCount: document.body.innerText.split(/\\s+/).length,
    };
  },
  firstViewportAnswers() {
    const vh = innerHeight;
    const inView = (el) => { if (!el) return false; const r = el.getBoundingClientRect(); return r.top < vh && r.bottom > 0 && r.width > 0; };
    const priceEl = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && /[£$€]\\s?\\d/.test(e.innerText || '') && inView(e));
    const atcEl = this.atc();
    return {
      titleVisible: inView(document.querySelector('h1')),
      priceVisible: !!priceEl,
      sizesVisible: this.sizeControls() > 0 && inView([...document.querySelectorAll('button,[role=radio],label')].find(e => /^(XS|S|M|L|XL)$/i.test((e.innerText || '').trim()))),
      atcVisible: inView(atcEl),
      atcText: atcEl ? (atcEl.innerText || atcEl.value || '').trim().slice(0, 40) : null,
      stockWordVisible: /in stock|available|ready to ship/i.test((document.body.innerText || '').slice(0, 3000)),
    };
  },
};
`;
