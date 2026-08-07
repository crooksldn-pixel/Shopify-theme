import fs from 'fs';
import { launch, newContext, primePreview, applyThrottle, BASE, MOBILE } from './lib.mjs';

const browser = await launch();
const out = {};

async function cold() {
  const ctx = await newContext(browser, MOBILE);
  await primePreview(ctx);
  const t = await ctx.newPage();
  await t.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });
  await t.evaluate(() => { try { localStorage.removeItem('crooksldn_ctc_seen'); } catch (e) {} });
  await t.close();
  return ctx;
}

// --- A. Does the cookie banner block the footer? ---
{
  const ctx = await cold();
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(4000);
  await page.evaluate(() => document.querySelector('.ctc-close')?.click());
  await page.waitForTimeout(600);
  await page.evaluate(() => document.querySelector('footer')?.scrollIntoView({ block: 'end' }));
  await page.waitForTimeout(900);

  out.footerBlocked = await page.evaluate(() => {
    const rows = [];
    for (const a of document.querySelectorAll('footer a')) {
      const r = a.getBoundingClientRect();
      if (r.width === 0 || r.bottom < 0 || r.top > innerHeight) continue;
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const hit = document.elementFromPoint(cx, cy);
      const blocked = hit && !a.contains(hit) && hit !== a;
      rows.push({
        label: a.innerText.replace(/\s+/g, ' ').trim(), href: a.getAttribute('href'),
        y: Math.round(r.top), blocked,
        blockedBy: blocked ? (hit.closest('[class*="shopify-pc"]') ? 'cookie banner' : (hit.className || hit.tagName).toString().slice(0, 40)) : null,
      });
    }
    const b = document.querySelector('.shopify-pc__banner');
    const br = b ? b.getBoundingClientRect() : null;
    return { banner: br ? { top: Math.round(br.top), height: Math.round(br.height), viewportH: innerHeight } : null, links: rows };
  });
  console.log('=== FOOTER LINKS vs COOKIE BANNER ===');
  console.log('banner:', JSON.stringify(out.footerBlocked.banner));
  for (const l of out.footerBlocked.links) console.log(`  ${l.blocked ? 'BLOCKED ' : 'clickable'} y=${String(l.y).padStart(4)}  ${l.label.padEnd(14)} -> ${l.href}${l.blockedBy ? '   by ' + l.blockedBy : ''}`);
  await page.screenshot({ path: 'audit/screens/check-footer-vs-cookiebanner.png' });

  // try an actual click on REFUNDS
  const before = page.url();
  await page.locator('footer a', { hasText: /^REFUNDS$/ }).first().click({ timeout: 8000 }).catch(e => console.log('  click threw:', e.message.split('\n')[0]));
  await page.waitForTimeout(3500);
  out.refundClick = { before, after: page.url(), navigated: page.url() !== before };
  console.log('  clicking REFUNDS ->', JSON.stringify(out.refundClick));
  await ctx.close();
}

// --- B. Same test with the banner accepted ---
{
  const ctx = await cold();
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(4000);
  await page.evaluate(() => document.querySelector('.ctc-close')?.click());
  await page.evaluate(() => document.querySelector('#shopify-pc__banner__btn-accept')?.click());
  await page.waitForTimeout(1200);
  await page.evaluate(() => document.querySelector('footer')?.scrollIntoView({ block: 'end' }));
  await page.waitForTimeout(800);
  const before = page.url();
  await page.locator('footer a', { hasText: /^REFUNDS$/ }).first().click({ timeout: 8000 }).catch(e => console.log('  click threw:', e.message.split('\n')[0]));
  await page.waitForTimeout(3500);
  out.refundClickAfterAccept = { before, after: page.url(), navigated: page.url() !== before };
  console.log('\n=== AFTER ACCEPTING COOKIES ===');
  console.log('  clicking REFUNDS ->', JSON.stringify(out.refundClickAfterAccept));
  const facts = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    return { url: location.pathname, heading: document.querySelector('h1,h2')?.innerText.trim(), lastUpdated: (t.match(/Last Updated:? ?[\d/]+/i) || [null])[0], words: t.split(' ').length, styledAsTheme: !!document.querySelector('.crk-root'), typeface: getComputedStyle(document.querySelector('main p, main') || document.body).fontFamily };
  });
  out.refundPage = facts;
  console.log('  refund page:', JSON.stringify(facts));
  await ctx.close();
}

// --- C. CM/IN toggle: does it actually convert? ---
{
  const ctx = await cold();
  const page = await ctx.newPage();
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(3800);
  await page.evaluate(() => { document.querySelector('.ctc-close')?.click(); document.querySelector('#shopify-pc__banner__btn-accept')?.click(); });
  await page.waitForTimeout(900);
  const grab = () => page.evaluate(() => {
    const rows = [...document.querySelectorAll('table tr, .crk-measure tr, [class*="measure"] tr')].map(tr => tr.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean);
    const active = [...document.querySelectorAll('.crk-unit')].map(b => b.innerText.trim() + (b.getAttribute('aria-pressed') === 'true' || /is-|active|sel/.test(b.className) ? '*' : ''));
    return { rows: rows.slice(0, 7), active };
  });
  out.unitsCM = await grab();
  await page.locator('.crk-unit', { hasText: /^IN$/ }).first().click();
  await page.waitForTimeout(900);
  out.unitsIN = await grab();
  console.log('\n=== MEASUREMENT UNIT TOGGLE ===');
  console.log('  CM:', JSON.stringify(out.unitsCM, null, 1).slice(0, 700));
  console.log('  IN:', JSON.stringify(out.unitsIN, null, 1).slice(0, 700));
  await page.screenshot({ path: 'audit/screens/check-measure-inches.png' });

  // where does SIZE GUIDE actually land you?
  await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(600);
  await page.locator('.crk-textbtn', { hasText: /SIZE GUIDE/i }).first().click();
  await page.waitForTimeout(1500);
  out.sizeGuideLanding = await page.evaluate(() => {
    const vis = [];
    for (const el of document.querySelectorAll('.crk-section-head, .crk-measure, table, h1, .crk-h1')) {
      const r = el.getBoundingClientRect();
      if (r.bottom > 0 && r.top < innerHeight) vis.push(el.innerText.replace(/\s+/g, ' ').trim().slice(0, 50) + ` @${Math.round(r.top)}`);
    }
    return { scrollY: Math.round(scrollY), visibleAnchors: vis };
  });
  console.log('\n=== WHERE "SIZE GUIDE" LANDS YOU ===', JSON.stringify(out.sizeGuideLanding, null, 1));
  await page.screenshot({ path: 'audit/screens/check-sizeguide-landing.png' });
  await ctx.close();
}

// --- D. Social proof: strict check ---
{
  const ctx = await cold();
  const page = await ctx.newPage();
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(3500);
  await page.evaluate(() => { document.querySelector('.ctc-close')?.click(); document.querySelector('#shopify-pc__banner__btn-accept')?.click(); });
  await page.waitForTimeout(700);
  out.socialProof = await page.evaluate(() => {
    const t = document.body.innerText;
    return {
      starRatings: document.querySelectorAll('[class*="rating"],[class*="stars"],[itemprop="ratingValue"]').length,
      reviewBlocks: document.querySelectorAll('[class*="review"]').length,
      wordReviewInBody: (t.match(/\breview(s|ed)?\b/gi) || []).length,
      trustBadges: document.querySelectorAll('[class*="trust"],[class*="badge"][class*="secure"]').length,
      urgency: /\d+ (people|viewing|left|sold)|only \d+|hurry|ends in/i.test(t),
      companyIdentity: { companyNo: /company (no|number)|\bltd\b/i.test(t), registeredAddress: /Unit \d+|[A-Z]{1,2}\d{1,2} ?\d[A-Z]{2}/.test(t) },
      socials: [...document.querySelectorAll('a[href*="instagram"],a[href*="tiktok"]')].map(a => a.getAttribute('href')),
      emailLinks: [...document.querySelectorAll('a[href^="mailto:"]')].map(a => a.getAttribute('href')),
    };
  });
  console.log('\n=== SOCIAL PROOF / TRUST SIGNALS ON A PDP (strict) ===', JSON.stringify(out.socialProof, null, 1));
  await ctx.close();
}

fs.writeFileSync('audit/evidence/p2-fix.json', JSON.stringify(out, null, 2));
await browser.close();
