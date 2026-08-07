import { chromium } from 'playwright';
const PREVIEW = 'https://ezvw3xrffzdt93es-100410786135.shopifypreview.com';
const LIVE = 'https://crooksldn.com';

const launch = () => chromium.launch({ args: ['--no-sandbox', '--proxy-server=http://127.0.0.1:38080', '--ignore-certificate-errors'] });

async function probe(page, label) {
  const info = await page.evaluate(() => ({
    url: location.href,
    title: document.title,
    crkRoot: !!document.querySelector('.crk-root'),
    crkClassSample: Array.from(document.querySelectorAll('[class*="crk"]')).slice(0, 8).map(e => e.tagName + '.' + (typeof e.className === 'string' ? e.className : '')),
    themeName: window.Shopify?.theme?.name,
    themeId: window.Shopify?.theme?.id,
    themeRole: window.Shopify?.theme?.role,
    shop: window.Shopify?.shop,
    canvases: document.querySelectorAll('canvas').length,
    h1: document.querySelector('h1')?.innerText?.trim().slice(0, 80),
    bodyText: document.body.innerText.replace(/\s+/g, ' ').slice(0, 300),
    stylesheets: [...document.querySelectorAll('link[rel=stylesheet]')].map(l => l.href.split('/').pop().split('?')[0]),
    fonts: [...new Set([...document.querySelectorAll('*')].slice(0, 400).map(e => getComputedStyle(e).fontFamily))].slice(0, 8),
  }));
  console.log('=== ' + label + ' ===');
  console.log(JSON.stringify(info, null, 2));
  return info;
}

const b = await launch();
const ctx = await b.newContext({
  viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, ignoreHTTPSErrors: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
});
const page = await ctx.newPage();
const assetUrls = [];
page.on('request', r => assetUrls.push(r.url()));

const resp = await page.goto(PREVIEW, { waitUntil: 'load', timeout: 120000 });
console.log('preview status', resp.status(), '->', page.url());
await page.waitForTimeout(5000);
const prev = await probe(page, 'PREVIEW (staging)');
console.log('asset names containing crk/crooks:', [...new Set(assetUrls.filter(u => /crk|crooks/i.test(u)).map(u => u.split('/').pop().split('?')[0]))]);
console.log('cookies:', (await ctx.cookies()).map(c => c.name).join(', '));
await page.screenshot({ path: 'audit/screens/verify-preview-home.png' });

// now navigate deeper in the SAME context to prove cookie persistence
await page.goto(new URL('/collections/all', page.url()).href, { waitUntil: 'load', timeout: 120000 });
await page.waitForTimeout(2500);
const deep = await probe(page, 'PREVIEW deep nav /collections/all');

// live theme for comparison, separate context
const ctx2 = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, ignoreHTTPSErrors: true });
const p2 = await ctx2.newPage();
try {
  await p2.goto(LIVE, { waitUntil: 'load', timeout: 120000 });
  await p2.waitForTimeout(3000);
  await probe(p2, 'LIVE crooksldn.com');
  await p2.screenshot({ path: 'audit/screens/verify-live-home.png' });
} catch (e) { console.log('live fetch failed:', e.message.split('\n')[0]); }

await b.close();
