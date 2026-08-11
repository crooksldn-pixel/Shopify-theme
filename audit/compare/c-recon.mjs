// Recon: discover a site's shape. Usage: node audit/compare/c-recon.mjs <tag> <homeUrl> [pdpUrl] [collectionUrl]
// Writes sites/<tag>.json (config) and evidence/<tag>-recon.json.
import { launch, newContext, MOBILE, HEURISTICS, saveEvidence } from './clib.mjs';
import fs from 'fs';

const [tag, homeUrl, pdpArg, colArg] = process.argv.slice(2);
if (!tag || !homeUrl) { console.error('usage: c-recon.mjs <tag> <homeUrl> [pdpUrl] [collectionUrl]'); process.exit(1); }

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
const p = await ctx.newPage();
const out = { tag, homeUrl, fetchedAt: new Date().toISOString() };

const resp = await p.goto(homeUrl, { waitUntil: 'domcontentloaded', timeout: 90000 });
out.homeStatus = resp.status();
await p.waitForTimeout(4000);
await p.evaluate(HEURISTICS);
out.botWall = await p.evaluate(() => /just a moment|access denied|verify you are human|cloudflare|captcha/i.test(document.title + ' ' + document.body.innerText.slice(0, 600)));
out.home = await p.evaluate(() => ({
  seo: window.__h.seoSurface(),
  overlaysAtArrival: window.__h.overlays(),
  cookieBanner: window.__h.cookieBanner(),
  trust: window.__h.trustWords(),
  platform: (document.querySelector('meta[name=generator]')?.content) || (window.Shopify ? 'Shopify' : null) || (document.querySelector('link[href*="cdn.shopify"]') ? 'Shopify' : null) || (document.querySelector('[data-wf-site]') ? 'Webflow' : null) || 'unknown',
}));
// popup watch: what appears by 6s and by 12s
await p.waitForTimeout(6000);
out.overlaysAt10s = await p.evaluate(() => window.__h.overlays());

// nav + product link discovery
out.nav = await p.evaluate(() => {
  const links = [...document.querySelectorAll('a[href]')].map(a => ({ t: (a.innerText || '').trim().slice(0, 40), href: a.getAttribute('href') })).filter(l => l.t);
  const uniq = []; const seen = new Set();
  for (const l of links) { const k = l.t + '|' + l.href; if (!seen.has(k) && uniq.length < 60) { seen.add(k); uniq.push(l); } }
  return uniq;
});
const prodLinks = out.nav.filter(l => /\/products?\/|\/shop\/|\/item\/|\/p\//.test(l.href || ''));
const colLinks = out.nav.filter(l => /\/collections?\/|\/category\/|\/shop$/.test(l.href || ''));
const abs = (h) => { try { return new URL(h, homeUrl).href; } catch { return null; } };
const pdpUrl = pdpArg || (prodLinks[0] ? abs(prodLinks[0].href) : null);
const collectionUrl = colArg || (colLinks[0] ? abs(colLinks[0].href) : null);
out.discovered = { pdpUrl, collectionUrl, productLinkCount: prodLinks.length };

if (pdpUrl) {
  const r2 = await p.goto(pdpUrl, { waitUntil: 'domcontentloaded', timeout: 90000 }).catch(e => null);
  if (r2) {
    await p.waitForTimeout(4000);
    await p.evaluate(HEURISTICS);
    out.pdp = await p.evaluate(() => ({
      seo: window.__h.seoSurface(),
      firstViewport: window.__h.firstViewportAnswers(),
      sizeControls: window.__h.sizeControls(),
      price: window.__h.price(),
      trust: window.__h.trustWords(),
      cookieBanner: window.__h.cookieBanner(),
      overlays: window.__h.overlays(),
    }));
    await p.screenshot({ path: `audit/compare/screens/${tag}-pdp.png` }).catch(() => {});
  }
}
await p.screenshot({ path: `audit/compare/screens/${tag}-home.png`, fullPage: false }).catch(() => {});

fs.writeFileSync(`audit/compare/sites/${tag}.json`, JSON.stringify({ tag, homeUrl, pdpUrl, collectionUrl }, null, 2));
saveEvidence(tag, 'recon', out);
console.log(JSON.stringify({ tag, status: out.homeStatus, botWall: out.botWall, platform: out.home?.platform, pdpUrl, title: out.home?.seo?.title }, null, 1));
await browser.close();
