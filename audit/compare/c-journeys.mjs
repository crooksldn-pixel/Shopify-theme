// Ten scripted persona journeys, site-agnostic. Usage: node audit/compare/c-journeys.mjs <tag>
// Collects the measurable spine of each journey; the felt-experience notes are authored at
// report time from this evidence. Non-destructive: adds to cart at most, never checkout.
import { launch, newContext, applyThrottle, MOBILE, DESKTOP, HEURISTICS, VITALS_INIT, collectVitals, loadSite, saveEvidence } from './clib.mjs';

const tag = process.argv[2];
const site = loadSite(tag);
const browser = await launch();
const out = { tag, personas: {} };

async function freshPage(device = MOBILE, throttled = true) {
  const ctx = await newContext(browser, device);
  const p = await ctx.newPage();
  await p.addInitScript(VITALS_INIT);
  if (throttled) await applyThrottle(p);
  return { ctx, p };
}
async function snap(p) {
  await p.evaluate(HEURISTICS);
  return p.evaluate(() => ({
    url: location.pathname, overlays: window.__h.overlays(), cookie: window.__h.cookieBanner(),
    fv: window.__h.firstViewportAnswers(), price: window.__h.price(), trust: window.__h.trustWords(),
  }));
}
async function acceptBanner(p) {
  const btn = p.locator('button:has-text("Accept"), button:has-text("Agree"), button:has-text("Allow all")').first();
  if (await btn.isVisible().catch(() => false)) { await btn.click().catch(() => {}); await p.waitForTimeout(500); return true; }
  return false;
}
async function run(key, fn) {
  try { out.personas[key] = await fn(); }
  catch (e) { out.personas[key] = { error: String(e).slice(0, 200) }; }
  console.log(key, out.personas[key]?.error ? 'ERROR' : 'ok');
}

// P1 cold social click: straight to PDP, throttled mobile
await run('p1_coldClick', async () => {
  const { ctx, p } = await freshPage();
  const t0 = Date.now();
  await p.goto(site.pdpUrl || site.homeUrl, { waitUntil: 'load', timeout: 180000 });
  const atLoad = await snap(p);
  await p.waitForTimeout(5000);
  const at5s = await snap(p);
  const vit = await collectVitals(p);
  await ctx.close();
  return { wallMs: Date.now() - t0, lcp: vit.lcp, cls: +vit.cls.toFixed(4), atLoad, at5s };
});

// P2 returning fan: homepage → what is new → a PDP
await run('p2_returningFan', async () => {
  const { ctx, p } = await freshPage();
  await p.goto(site.homeUrl, { waitUntil: 'load', timeout: 180000 });
  await acceptBanner(p);
  const newSignal = await p.evaluate(() => {
    const t = document.body.innerText;
    return { wordNew: /\bnew (in|arrivals?|drop)\b/i.test(t), dates: /\b(0?[1-9]|[12]\d|3[01])[./](0?[1-9]|1[0-2])\b/.test(t),
      badges: (t.match(/\bNEW\b/g) || []).length, justDropped: /just (dropped|landed)|latest drop/i.test(t) };
  });
  await ctx.close();
  return { newSignal };
});

// P3 size-anxious: PDP → size guide → measurements quality
await run('p3_sizeAnxious', async () => {
  const { ctx, p } = await freshPage();
  await p.goto(site.pdpUrl, { waitUntil: 'load', timeout: 180000 });
  await acceptBanner(p);
  const sg = p.locator('a, button').filter({ hasText: /size (guide|chart)|fit guide/i }).first();
  const present = await sg.isVisible().catch(() => false);
  let table = null;
  if (present) {
    await sg.click().catch(() => {});
    await p.waitForTimeout(1800);
    table = await p.evaluate(() => {
      const t = document.body.innerText;
      return { units: { cm: /\d+\s?cm/.test(t), inches: /\d+\s?(in|")/.test(t) },
        dims: ['waist', 'chest', 'length', 'inseam', 'hem', 'shoulder'].filter(d => new RegExp(d, 'i').test(t)),
        laidFlat: /laid flat|garment measurements/i.test(t), modelInfo: /model (is|wears|height)/i.test(t) };
    });
  }
  await ctx.close();
  return { sizeGuidePresent: present, table };
});

// P4 sceptic: policies + contact + who-are-they
await run('p4_sceptic', async () => {
  const { ctx, p } = await freshPage(MOBILE, false);
  const checks = {};
  for (const [k, path] of [['refund', '/policies/refund-policy'], ['contact', '/pages/contact'], ['about', '/pages/about']]) {
    try {
      const r = await p.goto(new URL(path, site.homeUrl).href, { waitUntil: 'domcontentloaded', timeout: 45000 });
      checks[k] = r.status() >= 400 ? { status: r.status() } : await p.evaluate(() => ({
        status: 200, words: document.body.innerText.split(/\s+/).length,
        placeholders: (document.body.innerText.match(/\[[A-Za-z][^\]]{2,40}\]/g) || []).slice(0, 4),
        email: (document.body.innerText.match(/[\w.+-]+@[\w-]+\.[\w.]+/) || [null])[0],
        address: /\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b|\d{5}/.test(document.body.innerText),
      }));
    } catch { checks[k] = { status: 'unreachable' }; }
  }
  await ctx.close();
  return checks;
});

// P5 aimless browser: homepage dwell — what is there beyond products?
await run('p5_aimless', async () => {
  const { ctx, p } = await freshPage();
  await p.goto(site.homeUrl, { waitUntil: 'load', timeout: 180000 });
  await acceptBanner(p);
  const hooks = await p.evaluate(() => {
    const t = document.body.innerText;
    return { newsletter: /newsletter|sign ?up|subscribe|mailing list|10% off/i.test(t),
      editorial: /lookbook|journal|blog|stories|about us|our story/i.test(t),
      social: [...document.querySelectorAll('a[href*=instagram], a[href*=tiktok], a[href*=twitter], a[href*=youtube]')].length,
      anythingPlayful: /game|quiz|playlist|radio|archive/i.test(t) };
  });
  await ctx.close();
  return { hooks };
});

// P6 accessibility user: covered by c-a11y; journey adds ATC-by-keyboard attempt
await run('p6_a11y', async () => {
  const { ctx, p } = await freshPage(MOBILE, false);
  await p.goto(site.pdpUrl, { waitUntil: 'load', timeout: 120000 });
  await acceptBanner(p);
  let reachedAtc = false;
  for (let i = 0; i < 40; i++) {
    await p.keyboard.press('Tab');
    const t = await p.evaluate(() => (document.activeElement?.innerText || '').trim().slice(0, 40));
    if (/add to (cart|bag|basket)|buy/i.test(t)) { reachedAtc = true; break; }
  }
  await ctx.close();
  return { atcReachableByKeyboard: reachedAtc };
});

// P7 slow connection: home under throttle — time to first product image
await run('p7_slow', async () => {
  const { ctx, p } = await freshPage();
  const t0 = Date.now();
  await p.goto(site.homeUrl, { waitUntil: 'load', timeout: 240000 });
  const vit = await collectVitals(p);
  const productImgVisible = await p.evaluate(() => {
    const imgs = [...document.querySelectorAll('img')].filter(i => i.complete && i.naturalWidth > 50);
    return imgs.some(i => { const r = i.getBoundingClientRect(); return r.top < innerHeight && r.width > 80; });
  });
  await ctx.close();
  return { wallMs: Date.now() - t0, lcp: vit.lcp, productImgInFirstViewport: productImgVisible };
});

// P8 post-purchase: can they find tracking + returns path?
await run('p8_postPurchase', async () => {
  const { ctx, p } = await freshPage(MOBILE, false);
  await p.goto(site.homeUrl, { waitUntil: 'load', timeout: 120000 });
  await acceptBanner(p);
  const hunt = await p.evaluate(() => {
    const links = [...document.querySelectorAll('a')].map(a => (a.innerText || '').trim().toLowerCase());
    return { trackLink: links.some(t => /track/.test(t)), accountLink: links.some(t => /account|log ?in|sign ?in/.test(t)),
      returnsLink: links.some(t => /returns?|refund/.test(t)), faqLink: links.some(t => /faq|help/.test(t)) };
  });
  await ctx.close();
  return { hunt };
});

// P9 comparison shopper: cross-tab decision spine — price clarity, delivery cost clarity,
// returns cost clarity, and anything that differentiates (all from PDP + one click)
await run('p9_comparison', async () => {
  const { ctx, p } = await freshPage(MOBILE, false);
  await p.goto(site.pdpUrl, { waitUntil: 'load', timeout: 120000 });
  await acceptBanner(p);
  const spine = await p.evaluate(() => {
    const t = document.body.innerText;
    return { price: (t.match(/[£$€]\s?\d{1,4}(?:[.,]\d{2})?/) || [null])[0],
      shippingCostStated: /free (uk )?(shipping|delivery)|shipping (from|calculated)|[£$€]\s?\d+(\.\d{2})? (uk )?(shipping|delivery)/i.test(t),
      returnsCostStated: /free returns?|return (postage|label)|returns? (are )?(free|paid)/i.test(t),
      materialStated: /\d+\s?(gsm|oz)|100% cotton|polyester|fleece/i.test(t),
      madeWhere: /made in [A-Z][a-z]+/.test(t) };
  });
  await ctx.close();
  return { spine };
});

// P10 gift buyer: novice landing on home — can they find "for someone else" affordances?
await run('p10_gift', async () => {
  const { ctx, p } = await freshPage(MOBILE, false);
  await p.goto(site.homeUrl, { waitUntil: 'load', timeout: 120000 });
  await acceptBanner(p);
  const aff = await p.evaluate(() => {
    const t = document.body.innerText;
    return { giftCard: /gift ?card|gift voucher/i.test(t), sizeHelpFromHome: /size guide|fit guide/i.test(t),
      exchangePolicyVisible: /exchange/i.test(t), returnWindowVisible: /(\d+)[- ]day returns?|return within/i.test(t),
      categoriesClear: [...document.querySelectorAll('a')].filter(a => /tees?|t-shirts?|hoodies?|jeans|denim|shorts|accessories/i.test((a.innerText || '').trim())).length };
  });
  await ctx.close();
  return { aff };
});

saveEvidence(tag, 'journeys', out);
await browser.close();
