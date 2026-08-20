/**
 * CROOKSLDN behavioural audit — shared browser harness.
 *
 * Every script in this audit MUST use `session()` to open the site.
 * It guarantees three things that the audit is worthless without:
 *   1. the Shopify preview cookie (else you silently audit the LIVE theme)
 *   2. the GB market (else prices come back in USD and the carriage bar,
 *      which is gated to country_code GB, never renders)
 *   3. a theme-identity assertion on .crk-root + theme id 202053779799
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

export const PREVIEW = 'https://7chao18p5etruwy5-100410786135.shopifypreview.com';
export const PREVIEW_HOST = '7chao18p5etruwy5-100410786135.shopifypreview.com';
export const EXPECTED_THEME_ID = 202053779799;
export const EXEC = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
export const SHOTS = 'audit/screens';

// The egress proxy cannot complete Chromium's TLS 1.3 handshake; capping the
// client at TLS 1.2 is the only reason any of this reaches the network.
const PROXY = process.env.HTTPS_PROXY || process.env.https_proxy || null;
const ARGS = ['--no-sandbox', '--disable-dev-shm-usage', '--ssl-version-max=tls1.2'];

export const DEVICES = {
  mobile: {
    viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  },
  mobileLandscape: {
    viewport: { width: 844, height: 390 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  },
  androidSlow: {
    viewport: { width: 360, height: 800 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
  },
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, isMobile: false, hasTouch: false },
};

const GB_COOKIES = [
  { name: 'localization', value: 'GB', domain: PREVIEW_HOST, path: '/' },
  { name: 'cart_currency', value: 'GBP', domain: PREVIEW_HOST, path: '/' },
];

export async function launch(opts = {}) {
  return chromium.launch({ executablePath: EXEC, args: ARGS, ...(PROXY ? { proxy: { server: PROXY } } : {}), ...opts });
}

/* ------------------------------------------------------------------ *
 * Politeness. Many agents run at once, each in its own node process,
 * so the cap has to live on disk. Twelve browsers at once tripped the
 * store's bot protection: 429s, plus a Cloudflare challenge frame that
 * this environment's egress policy blocks, so pages hung forever.
 * ------------------------------------------------------------------ */
const LOCK_DIR = 'audit/_tools/.slots';
// 12 tripped the store's bot protection; 3 was verified safe. 4 for the feature
// census, which judges behaviour not speed. Phase 2 drops back to 3 because the
// persona journeys report felt slowness, and persona 14 runs alone.
const MAX_BROWSERS = Number(process.env.CRK_MAX_BROWSERS || 3);
const SLOT_STALE_MS = 8 * 60 * 1000;

function tryClaim(i) {
  const p = path.join(LOCK_DIR, 'slot-' + i);
  try { fs.mkdirSync(p, { recursive: false }); fs.writeFileSync(path.join(p, 'pid'), String(process.pid)); return p; }
  catch {
    try { // reap a slot whose owner died or wedged
      if (Date.now() - fs.statSync(p).mtimeMs > SLOT_STALE_MS) { fs.rmSync(p, { recursive: true, force: true }); }
    } catch {}
    return null;
  }
}

async function acquireSlot() {
  fs.mkdirSync(LOCK_DIR, { recursive: true });
  for (let attempt = 0; attempt < 400; attempt++) {
    for (let i = 0; i < MAX_BROWSERS; i++) { const p = tryClaim(i); if (p) return p; }
    await sleep(1500 + Math.random() * 1500);
  }
  throw new Error('Could not get a browser slot in ~10 minutes — too many sessions queued.');
}

function releaseSlot(p) { try { fs.rmSync(p, { recursive: true, force: true }); } catch {} }

/**
 * Open a fully-prepared shopping session.
 * @param {object} o
 * @param {string} o.device      key of DEVICES (default 'mobile')
 * @param {boolean} o.slow       Slow-4G + 4x CPU throttle
 * @param {boolean} o.reducedMotion
 * @param {number} o.zoom        page zoom factor, e.g. 2 for 200%
 * @param {boolean} o.js         set false to shop with JavaScript disabled
 * @param {string} o.colorScheme 'dark' | 'light'
 * @returns {{browser, context, page, identity, close}}
 */
export async function session(o = {}) {
  const dev = DEVICES[o.device || 'mobile'];
  const slot = await acquireSlot();
  const browser = await launch();
  const ctxOpts = {
    ...dev,
    locale: 'en-GB',
    timezoneId: 'Europe/London',
    javaScriptEnabled: o.js === false ? false : true,
    ...(o.reducedMotion ? { reducedMotion: 'reduce' } : {}),
    ...(o.colorScheme ? { colorScheme: o.colorScheme } : {}),
  };
  const context = await browser.newContext(ctxOpts);
  await context.addCookies(GB_COOKIES);
  const page = await context.newPage();

  // The bot-challenge host is blocked by this environment's egress policy, so a
  // challenge frame never resolves and the page waits on it forever. Fail it fast.
  try {
    await context.route('**://*.challenges.cloudflare.com/**', r => r.abort());
    await context.route('**://challenges.cloudflare.com/**', r => r.abort());
  } catch { /* JS-disabled contexts */ }
  if (o.slow) await throttle(page);
  if (o.zoom) await page.addInitScript(z => {
    document.addEventListener('DOMContentLoaded', () => { document.body.style.zoom = z; });
  }, o.zoom);

  let identity;
  try {
    identity = await enterPreview(page);
  } catch (e) { releaseSlot(slot); await browser.close(); throw e; }

  if (!identity.ok) {
    releaseSlot(slot);
    await browser.close();
    throw new Error('THEME ASSERTION FAILED — refusing to audit. ' + JSON.stringify(identity));
  }
  let closed = false;
  const close = async () => {
    if (closed) return; closed = true;
    releaseSlot(slot);
    await browser.close().catch(() => {});
  };
  process.once('exit', () => releaseSlot(slot));
  return { browser, context, page, identity, close };
}

/**
 * Navigate with backoff. The store answers 429 under load and can serve a bot
 * challenge instead of the page; both are transient and both need waiting out,
 * not retrying immediately.
 */
async function navigate(page, url, { settle, tries = 5 } = {}) {
  let wait = 4000;
  for (let attempt = 1; attempt <= tries; attempt++) {
    await sleep(250 + Math.random() * 600);           // human-ish pacing
    let resp, status = 0;
    try {
      resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      status = resp?.status() ?? 0;
    } catch (e) {
      if (attempt === tries) throw e;
      await sleep(wait); wait *= 2; continue;
    }
    const challenged = status === 429 || status === 503 ||
      await page.evaluate(() => /just a moment|attention required|checking your browser/i
        .test(document.title + ' ' + (document.body?.innerText || '').slice(0, 400))).catch(() => false);
    if (!challenged) { await sleep(settle); return { status, url: page.url() }; }
    if (attempt === tries) return { status, url: page.url(), throttled: true };
    await sleep(wait); wait *= 2;
  }
}

/** Slow 4G + 4x CPU, via CDP. */
export async function throttle(page, { down = 1_600_000 / 8, up = 750_000 / 8, latency = 150, cpu = 4 } = {}) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', { offline: false, downloadThroughput: down, uploadThroughput: up, latency });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
  return cdp;
}

/** First navigation in any context. Establishes the preview cookie. */
export async function enterPreview(page, { settle = 3500 } = {}) {
  const r = await navigate(page, PREVIEW, { settle });
  await hidePreviewBar(page);
  const id = await assertTheme(page);
  return { ...r, ...id };
}

/** Theme identity. Run-integrity only — never a finding, never in the report. */
export async function assertTheme(page) {
  const r = await page.evaluate(() => ({
    crkRoot: !!document.querySelector('.crk-root'),
    themeId: window.Shopify?.theme?.id ?? null,
    themeName: window.Shopify?.theme?.name ?? null,
    themeRole: window.Shopify?.theme?.role ?? null,
    currency: window.Shopify?.currency?.active ?? null,
    country: window.Shopify?.country ?? null,
  })).catch(() => ({}));
  r.ok = r.crkRoot === true && r.themeId === EXPECTED_THEME_ID;
  r.gb = r.currency === 'GBP' && r.country === 'GB';
  return r;
}

/** Shopify's "You are previewing" bar is not part of the shopper's view. */
export async function hidePreviewBar(page) {
  try {
    // #PBarNextFrameWrapper is the live one: a transparent, pointer-events:auto
    // wrapper fixed across the bottom 68px. It sits on top of the theme's own
    // sticky buy bar and swallows taps, so leaving it in place makes the sticky
    // ADD TO BAG look dead when it is not. It only exists on a preview URL.
    await page.addStyleTag({ content:
      '#PBarNextFrameWrapper,#preview-bar-iframe,#PreviewBarInjector,#admin-bar-iframe,' +
      '[id^="PBar"],[id^="preview-bar"],[id^="shopify-preview"],iframe[src*="preview_bar"],' +
      'iframe[src*="admin_bar"]{display:none !important;height:0 !important;' +
      'pointer-events:none !important;}' });
    // Belt and braces: the bar is sometimes an injected iframe with no stable id.
    await page.evaluate(() => {
      for (const f of document.querySelectorAll('iframe')) {
        const s = (f.getAttribute('src') || '') + ' ' + (f.id || '') + ' ' + (f.className || '');
        if (/preview|admin_bar|adminbar/i.test(s)) f.style.setProperty('display', 'none', 'important');
      }
    });
  } catch { /* JS-disabled contexts */ }
}

/** Navigate anywhere within the previewed store, re-asserting identity. */
export async function go(page, pathOrUrl, { settle = 2500, assert = true } = {}) {
  const url = pathOrUrl.startsWith('http') ? pathOrUrl : PREVIEW + pathOrUrl;
  const r = await navigate(page, url, { settle });
  await hidePreviewBar(page);
  const id = assert ? await assertTheme(page) : {};
  return { ...r, ...id };
}

let counter = 0;
/** Screenshot. Name them <persona-or-area>-<step>. */
export async function shot(page, name, { full = false } = {}) {
  fs.mkdirSync(SHOTS, { recursive: true });
  const safe = String(name).replace(/[^a-z0-9._-]/gi, '-') || `shot${++counter}`;
  const file = path.join(SHOTS, `${safe}.png`);
  try {
    await hidePreviewBar(page);
    await page.screenshot({ path: file, fullPage: full, timeout: 30000 });
  } catch (e) { return `SHOT-FAILED:${e.message.slice(0, 80)}`; }
  return file;
}

/** What a shopper can actually read on screen right now. */
export async function visibleText(page, sel = 'body') {
  return page.evaluate(s => (document.querySelector(s)?.innerText || '').replace(/\n{3,}/g, '\n\n').trim(), sel);
}

export function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
  return file;
}
export function append(file, line) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, line + '\n');
}
export const sleep = ms => new Promise(r => setTimeout(r, ms));
