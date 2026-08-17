// RUN 3 — new-surface instrument: FAQ (QUESTIONS), TERMS, SEARCH, skinned policies,
// homepage packaging manifest, game-in-menu. Writes audit/evidence/newtabs.json.
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';
import fs from 'fs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const p = await ctx.newPage();
const out = { generated: new Date().toISOString() };

// ---- footer reachability -----------------------------------------------------
await p.goto(BASE + '/', { waitUntil: 'load', timeout: 120000 });
await p.waitForTimeout(2500);
out.footerLinks = await p.evaluate(() => [...document.querySelectorAll('footer a, .crk-footer a')]
  .map(a => ({ t: (a.innerText || '').trim(), href: a.getAttribute('href') })).filter(l => l.t).slice(0, 24));

// homepage: packaging manifest replaces CASE 001; game now in menu
out.homepage = await p.evaluate(() => ({
  packagingManifest: !!document.querySelector('[class*=packaging], [data-crk-section*=packaging]') || /PACKAGING MANIFEST/i.test(document.body.innerText),
  case001OnHome: /CASE 001 — ATTRACT MODE|CASE 001\b/.test(document.body.innerText),
  boardPresent: !!document.querySelector('canvas'),
}));
await p.evaluate(() => { const b = [...document.querySelectorAll('button, a')].find(x => /menu/i.test(x.getAttribute('aria-label') || x.innerText)); b && b.click(); });
await p.waitForTimeout(900);
out.menu = await p.evaluate(() => {
  const links = [...document.querySelectorAll('a, button')].map(a => (a.innerText || '').trim()).filter(Boolean);
  return { entries: [...new Set(links)].slice(0, 20), hasGame: links.some(t => /CASE 001|GAME|CRACK/i.test(t)), hasQuestions: links.some(t => /QUESTIONS|FAQ/i.test(t)) };
});

// ---- FAQ ---------------------------------------------------------------------
const faqLink = out.footerLinks.find(l => /QUESTIONS|FAQ/i.test(l.t));
out.faq = { linkedFrom: faqLink || null };
const faqUrl = faqLink ? new URL(faqLink.href, BASE).href : BASE + '/pages/faq';
try {
  await p.goto(faqUrl, { waitUntil: 'load', timeout: 90000 });
  await p.waitForTimeout(2000);
  Object.assign(out.faq, await p.evaluate(() => {
    const qs = [...document.querySelectorAll('[data-crk-accordion], details summary, .crk-section-head')];
    const t = document.body.innerText;
    return {
      status: 200, inDesignSystem: !!document.querySelector('.crk-root'),
      questionCount: qs.length,
      groups: [...document.querySelectorAll('h2, .crk-h')].map(h => h.innerText.trim()).filter(x => x && x.length < 40).slice(0, 8),
      coversDelivery: /dispatch|delivery/i.test(t), coversSizing: /size/i.test(t), coversReturns: /return|refund/i.test(t),
      coversTracking: /track/i.test(t),
      faqSchema: [...document.querySelectorAll('script[type="application/ld+json"]')].some(s => /FAQPage/.test(s.textContent)),
      firstAccordionOpens: (() => { const a = document.querySelector('[data-crk-accordion], details summary'); if (!a) return null; a.click(); const body = document.querySelector('[data-crk-accordion]')?.closest('.crk-section')?.querySelector('.crk-section-body'); return body ? !body.hidden : 'unknown'; })(),
    };
  }));
  // no-JS render
  const nj = await newContext(browser, MOBILE, { javaScriptEnabled: false });
  const np = await nj.newPage();
  await np.goto(faqUrl, { waitUntil: 'domcontentloaded', timeout: 90000 });
  out.faq.noJs = await np.evaluate(() => ({ textVisible: document.body.innerText.length > 800, answersReadable: /dispatch|working days/i.test(document.body.innerText) }));
  await nj.close();
} catch (e) { out.faq.error = String(e).slice(0, 150); }

// ---- TERMS -------------------------------------------------------------------
const termsLink = out.footerLinks.find(l => /TERMS/i.test(l.t));
out.terms = { linkedFrom: termsLink || null };
try {
  await p.goto(termsLink ? new URL(termsLink.href, BASE).href : BASE + '/pages/terms', { waitUntil: 'load', timeout: 90000 });
  await p.waitForTimeout(1500);
  Object.assign(out.terms, await p.evaluate(() => {
    const t = document.body.innerText;
    return {
      status: 200, inDesignSystem: !!document.querySelector('.crk-root'),
      sections: [...document.querySelectorAll('h2, .crk-h')].map(h => h.innerText.trim()).filter(x => x && x.length < 40).slice(0, 12),
      words: t.split(/\s+/).length,
      placeholders: (t.match(/\[[A-Za-z][^\]]{2,40}\]/g) || []).slice(0, 6),
      email: (t.match(/[\w.+-]+@[\w-]+\.[\w.]+/) || [null])[0],
      statesReturnPostage: /return postage|cost of returning|you pay.{0,30}return|return.{0,30}your (own )?cost|we (do not |don't )?(pay|cover).{0,20}return/i.test(t),
      statesReturnWindow: /\d+ days?/i.test(t),
      governingLaw: /england|wales|governing law|jurisdiction/i.test(t),
    };
  }));
} catch (e) { out.terms.error = String(e).slice(0, 150); }

// ---- SEARCH ------------------------------------------------------------------
out.search = {};
try {
  await p.goto(BASE + '/', { waitUntil: 'load', timeout: 90000 });
  await p.waitForTimeout(1500);
  out.search.headerLink = await p.evaluate(() => {
    const a = [...document.querySelectorAll('a')].find(x => /^SEARCH$/i.test((x.innerText || '').trim()));
    return a ? a.getAttribute('href') : null;
  });
  await p.goto(BASE + '/search', { waitUntil: 'load', timeout: 90000 });
  await p.waitForTimeout(1500);
  out.search.fieldPresent = await p.evaluate(() => !!document.querySelector('.crk-query__input, [data-crk-section="search-bar"] input[type=search], input[name=q]'));
  // typeahead
  const input = p.locator('.crk-query__input, input[name=q]').first();
  await input.fill('jea');
  await p.waitForTimeout(1200);
  out.search.typeahead = await p.evaluate(() => {
    const box = document.querySelector('[data-crk-suggest]');
    return box ? { visible: !box.hidden && box.offsetParent !== null, items: box.querySelectorAll('a, [role=option]').length, sample: (box.innerText || '').replace(/\s+/g, ' ').slice(0, 120) } : null;
  });
  // full query: product term
  await input.fill('jeans'); await input.press('Enter');
  await p.waitForLoadState('load'); await p.waitForTimeout(2000);
  out.search.productQuery = await p.evaluate(() => ({
    url: location.pathname + location.search,
    resultCount: document.querySelectorAll('.crk-card, [class*=result] a[href*="/products/"], a[href*="/products/"]').length,
    jeansInResults: /JEANS|BAGGIES|JORTS/i.test(document.body.innerText),
  }));
  // page term: does search surface QUESTIONS/TERMS pages?
  await p.goto(BASE + '/search?q=returns&type=product%2Cpage', { waitUntil: 'load', timeout: 90000 });
  await p.waitForTimeout(2000);
  out.search.pageQuery = await p.evaluate(() => ({
    surfacesPages: [...document.querySelectorAll('a')].some(a => /\/pages\/|policies\//.test(a.getAttribute('href') || '') && /question|term|faq|refund|return/i.test(a.innerText + a.getAttribute('href'))),
    text: document.body.innerText.replace(/\s+/g, ' ').slice(0, 200),
  }));
  // no-JS search
  const nj2 = await newContext(browser, MOBILE, { javaScriptEnabled: false });
  const np2 = await nj2.newPage();
  await np2.goto(BASE + '/search?q=jeans', { waitUntil: 'domcontentloaded', timeout: 90000 });
  out.search.noJs = await np2.evaluate(() => ({ resultsRendered: [...document.querySelectorAll('a')].filter(a => /\/products\//.test(a.getAttribute('href') || '')).length }));
  await nj2.close();
} catch (e) { out.search.error = String(e).slice(0, 150); }

// ---- skinned policy pages ----------------------------------------------------
out.policies = {};
for (const path of ['/policies/refund-policy', '/policies/privacy-policy', '/policies/shipping-policy']) {
  try {
    await p.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(1200);
    out.policies[path] = await p.evaluate(() => ({
      inDesignSystem: !!document.querySelector('.crk-root'),
      placeholders: (document.body.innerText.match(/\[[A-Za-z][^\]]{2,40}\]/g) || []).slice(0, 5),
      email: (document.body.innerText.match(/[\w.+-]+@[\w-]+\.[\w.]+/) || [null])[0],
    }));
  } catch (e) { out.policies[path] = { error: String(e).slice(0, 100) }; }
}

fs.writeFileSync('audit/evidence/newtabs.json', JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 1).slice(0, 2400));
await browser.close();
