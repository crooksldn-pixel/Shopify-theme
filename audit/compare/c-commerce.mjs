// Commerce surface: PDP first-viewport answers, size guide, sold-out handling, delivery
// findability, trust plumbing, non-destructive add-to-cart. Usage: node audit/compare/c-commerce.mjs <tag>
import { launch, newContext, MOBILE, HEURISTICS, loadSite, saveEvidence } from './clib.mjs';

const tag = process.argv[2];
const site = loadSite(tag);
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
const p = await ctx.newPage();
const out = { tag };

// dismiss cookie banner like a shopper: click accept-ish button if present
async function dismissBanner() {
  const btn = p.locator('button:has-text("Accept"), button:has-text("Agree"), button:has-text("Allow all"), [id*=accept i] >> visible=true').first();
  if (await btn.isVisible().catch(() => false)) { await btn.click().catch(() => {}); await p.waitForTimeout(600); return true; }
  return false;
}

if (site.pdpUrl) {
  await p.goto(site.pdpUrl, { waitUntil: 'load', timeout: 120000 });
  await p.waitForTimeout(3500);
  await p.evaluate(HEURISTICS);
  out.pdpBefore = await p.evaluate(() => ({ fv: window.__h.firstViewportAnswers(), cookie: window.__h.cookieBanner(), overlays: window.__h.overlays() }));
  out.bannerDismissed = await dismissBanner();
  await p.evaluate(HEURISTICS);
  out.pdp = await p.evaluate(() => ({
    fv: window.__h.firstViewportAnswers(), sizeControls: window.__h.sizeControls(), price: window.__h.price(), trust: window.__h.trustWords(),
  }));
  // size guide: is there a control, does it lead to measurements?
  const sg = p.locator('a, button').filter({ hasText: /size (guide|chart)|fit guide/i }).first();
  out.sizeGuide = { present: await sg.isVisible().catch(() => false) };
  if (out.sizeGuide.present) {
    await sg.click().catch(() => {});
    await p.waitForTimeout(1500);
    out.sizeGuide.leadsToMeasurements = await p.evaluate(() => /\d+\s?(cm|in|")/.test(document.body.innerText.slice(0, 20000)) && /(waist|chest|length|inseam|hem|pit)/i.test(document.body.innerText));
    await p.keyboard.press('Escape').catch(() => {});
  }
  // delivery findability: shipping words + a concrete timeframe anywhere on the PDP
  out.delivery = await p.evaluate(() => {
    const t = document.body.innerText;
    const m = t.match(/(\d+[-–]\d+|\d+)\s?(working\s)?(day|hour)s?[^.\n]{0,50}/i);
    return { claim: m ? m[0].slice(0, 80) : null, mentionsFree: /free (uk )?(shipping|delivery)/i.test(t) };
  });
  // sold-out handling: any struck/disabled size control?
  out.soldOutSignal = await p.evaluate(() => {
    const els = [...document.querySelectorAll('button, [role=radio], label, option')].filter(e => /^(XXS|XS|S|M|L|XL|XXL)$/i.test((e.innerText || e.textContent || '').trim()));
    const disabled = els.filter(e => e.disabled || e.getAttribute('aria-disabled') === 'true' || /sold|unavailable|disabled|strik|line-through|crossed/i.test(e.className) || getComputedStyle(e).textDecorationLine === 'line-through');
    return { sizeEls: els.length, visiblyDisabled: disabled.length };
  });
  // non-destructive add-to-cart: click ATC, observe response; never proceed to checkout
  const atcHandle = await p.evaluateHandle(() => window.__h.atc());
  const atcEl = atcHandle.asElement();
  if (atcEl) {
    const before = await p.evaluate(() => location.href);
    await atcEl.click().catch(() => {});
    await p.waitForTimeout(2500);
    out.addToCart = await p.evaluate((prev) => ({
      urlChanged: location.href !== prev,
      drawerOpened: !!document.querySelector('[class*=drawer i][class*=open i], [class*=cart i][aria-hidden=false], [class*=mini-cart i]'),
      feedbackText: (document.body.innerText.match(/added to (cart|bag)|item added|in your (cart|bag)|select (a )?size|choose (a )?size/i) || [null])[0],
    }), before);
  }
}
// trust plumbing on policy/contact pages
out.trustPages = {};
for (const path of ['/policies/refund-policy', '/pages/contact', '/policies/shipping-policy']) {
  try {
    const u = new URL(path, site.homeUrl).href;
    const r = await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
    const ok = r.status() < 400;
    out.trustPages[path] = !ok ? { status: r.status() } : await p.evaluate(() => ({
      status: 200, words: document.body.innerText.split(/\s+/).length,
      placeholders: (document.body.innerText.match(/\[[A-Za-z][^\]]{2,40}\]/g) || []).slice(0, 6),
      email: (document.body.innerText.match(/[\w.+-]+@[\w-]+\.[\w.]+/) || [null])[0],
    }));
  } catch { out.trustPages[path] = { status: 'unreachable' }; }
}
saveEvidence(tag, 'commerce', out);
console.log(JSON.stringify({ fv: out.pdp?.fv, sizeGuide: out.sizeGuide, delivery: out.delivery, soldOut: out.soldOutSignal, atc: out.addToCart }, null, 1));
await browser.close();
