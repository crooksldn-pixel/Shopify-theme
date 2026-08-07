import fs from 'fs';
import { launch, newContext, primePreview, applyThrottle, INIT_SCRIPT, readVitals, BASE, MOBILE, ANDROID, DESKTOP } from './lib.mjs';

const browser = await launch();
const results = {};

/** Facts recorder. Each step captures what is actually on screen, plus timing and taps. */
function makeJourney(id, name) {
  const j = { id, name, steps: [], taps: 0, t0: Date.now() };
  return {
    j,
    tap() { j.taps++; },
    async step(page, title, extra = {}) {
      const n = j.steps.length + 1;
      const shot = `audit/screens/p${id}-step${n}.png`;
      await page.screenshot({ path: shot }).catch(() => {});
      const seen = await page.evaluate(() => {
        const inView = [];
        const walk = (el) => {
          for (const c of el.children) {
            const r = c.getBoundingClientRect();
            if (r.bottom > 0 && r.top < innerHeight && r.width > 0 && r.height > 0) {
              const own = [...c.childNodes].filter(x => x.nodeType === 3 && x.textContent.trim()).map(x => x.textContent.trim()).join(' ');
              if (own) inView.push(own.replace(/\s+/g, ' ').slice(0, 90));
              walk(c);
            }
          }
        };
        walk(document.body);
        const overlays = [...document.querySelectorAll('.ctc-overlay, .shopify-pc__banner, dialog[open]')].map(e => {
          const r = e.getBoundingClientRect();
          return { what: e.className || e.tagName, coversPct: Math.round(100 * Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0)) / innerHeight) };
        });
        return {
          firstViewportText: [...new Set(inView)].slice(0, 26),
          scrollY: Math.round(scrollY),
          scrollViewports: +(scrollY / innerHeight).toFixed(2),
          docViewports: +(document.documentElement.scrollHeight / innerHeight).toFixed(2),
          overlays,
          scrollLocked: getComputedStyle(document.documentElement).overflow === 'hidden' || getComputedStyle(document.body).overflow === 'hidden',
          url: location.pathname + location.search,
          priceVisible: /£\d/.test([...document.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; }).map(e => e.textContent).join(' ')),
        };
      }).catch(() => ({}));
      j.steps.push({ n, title, screenshot: shot, seconds: +((Date.now() - j.t0) / 1000).toFixed(1), tapsSoFar: j.taps, ...seen, ...extra });
      console.log(`  [P${id}] step ${n}: ${title} — ${((Date.now() - j.t0) / 1000).toFixed(1)}s, ${j.taps} taps, scroll ${seen.scrollViewports ?? '?'}vh${seen.overlays?.length ? ', OVERLAY: ' + seen.overlays.map(o => o.what + ' ' + o.coversPct + '%').join(' + ') : ''}`);
      return j.steps.at(-1);
    },
  };
}

async function coldContext(device = MOBILE) {
  const ctx = await newContext(browser, device);
  await primePreview(ctx);
  // priming visited the homepage; clear the popup flag so the persona gets a true cold arrival
  const t = await ctx.newPage();
  await t.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });
  await t.evaluate(() => { try { localStorage.removeItem('crooksldn_ctc_seen'); } catch (e) {} });
  await t.close();
  return ctx;
}

// ============================================================
// P1 — Cold click from Instagram, straight onto a product page
// ============================================================
{
  const ctx = await coldContext();
  const page = await ctx.newPage();
  await page.addInitScript(INIT_SCRIPT);
  await applyThrottle(page);
  const J = makeJourney(1, 'Cold click from Instagram');
  J.j.t0 = Date.now();
  await page.goto(BASE + '/products/3-clives-tee', { waitUntil: 'commit', timeout: 180000 });
  await page.waitForTimeout(1500);
  await J.step(page, 'First paint — 1.5s after tapping the story link');
  await page.waitForLoadState('load', { timeout: 180000 }).catch(() => {});
  await page.waitForTimeout(700);
  await J.step(page, 'Page loaded');
  await page.waitForTimeout(2200);
  await J.step(page, 'At ~4.5s — the Crack the Cuffs popup fires on a 3s timer', { note: 'popup is rendered site-wide in theme.liquid, not homepage-only' });
  // close it
  const closed = await page.evaluate(() => { const b = document.querySelector('.ctc-close'); if (b) { b.click(); return true; } return false; });
  if (closed) J.tap();
  await page.waitForTimeout(900);
  await J.step(page, 'Popup dismissed — first real look at the product', { popupClosed: closed });
  // hunt for size
  const sizeInfo = await page.evaluate(() => {
    const s = document.querySelector('.crk-size');
    if (!s) return { found: false };
    const r = s.getBoundingClientRect();
    return { found: true, inFirstViewport: r.top < innerHeight && r.bottom > 0, topPx: Math.round(r.top + scrollY), sizes: [...document.querySelectorAll('.crk-size')].map(b => b.innerText.trim()) };
  });
  await J.step(page, 'Looking for sizes', { sizeInfo });
  await page.locator('.crk-size', { hasText: /^M$/ }).first().click().catch(() => {}); J.tap();
  await page.waitForTimeout(700);
  await J.step(page, 'Tapped size M');
  // hunt for shipping cost
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.45));
  await page.waitForTimeout(900);
  await J.step(page, 'Scrolling to find delivery cost and timing');
  const shipFacts = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    const heads = [...document.querySelectorAll('.crk-section-head')].map(h => ({ label: h.innerText.replace(/\s+/g, ' ').trim(), expanded: h.getAttribute('aria-expanded') }));
    return { heads, mentionsFreeUK: /FREE UK SHIPPING/i.test(t), chainCollapsed: heads.find(h => /CHAIN OF CUSTODY/.test(h.label))?.expanded };
  });
  await page.evaluate(() => { const h = [...document.querySelectorAll('.crk-section-head')].find(x => /CHAIN OF CUSTODY/.test(x.innerText)); if (h) { h.scrollIntoView({ block: 'center' }); h.click(); } }); J.tap();
  await page.waitForTimeout(900);
  await J.step(page, 'Opened CHAIN OF CUSTODY to find shipping', { shipFacts });
  const vitals = await readVitals(page);
  results.p1 = { ...J.j, vitals };
  await ctx.close();
}

// ============================================================
// P2 — Returning fan hunting the new drop
// ============================================================
{
  const ctx = await coldContext();
  const page = await ctx.newPage();
  await applyThrottle(page);
  const J = makeJourney(2, 'Returning fan hunting the new drop');
  J.j.t0 = Date.now();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(1500);
  await J.step(page, 'Homepage — first viewport');
  await page.waitForTimeout(2200);
  await J.step(page, 'Popup fires at 3s');
  await page.evaluate(() => document.querySelector('.ctc-close')?.click()); J.tap();
  await page.waitForTimeout(600);
  // look for any "new" signal
  const newSignal = await page.evaluate(() => {
    const t = document.body.innerText;
    return {
      wordNewOnPage: /\bNEW\b/.test(t),
      newInFooterOnly: !![...document.querySelectorAll('footer a')].find(a => a.innerText.trim() === 'NEW'),
      newInGrid: [...document.querySelectorAll('.crk-card')].filter(c => /NEW/.test(c.innerText)).length,
      gridBadges: [...new Set([...document.querySelectorAll('.crk-card')].map(c => (c.innerText.match(/AVAILABLE|SOLD OUT|NEW|LOW/g) || []).join('|')))].slice(0, 5),
      anyDates: /\b(20\d\d|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b/.test(t),
      menuHasNew: true,
    };
  });
  await J.step(page, 'Scanning for what is new', { newSignal });
  await page.evaluate(() => window.scrollTo(0, innerHeight * 1.3));
  await page.waitForTimeout(800);
  await J.step(page, 'The catalogue grid');
  // go to the sold-out product
  await page.goto(BASE + '/products/v2-baggies', { waitUntil: 'load', timeout: 180000 }); J.tap();
  await page.waitForTimeout(2500);
  await page.evaluate(() => document.querySelector('.ctc-close')?.click());
  await J.step(page, 'V2 BAGGIES — the item they missed (M, L, XL are sold out)');
  const soldOut = await page.evaluate(() => ({
    sizes: [...document.querySelectorAll('.crk-size')].map(b => ({ label: b.innerText.trim(), strike: getComputedStyle(b).textDecorationLine, colour: getComputedStyle(b).color, ariaDisabled: b.getAttribute('aria-disabled'), reallyDisabled: b.disabled })),
    stockLine: [...document.querySelectorAll('.crk-data,.crk-display')].map(e => e.innerText.trim()).filter(t => /stock/i.test(t)),
    notifyOffered: /notify|restock|back in stock|email me|waitlist/i.test(document.body.innerText),
  }));
  await page.locator('.crk-size', { hasText: /^L$/ }).first().click({ force: true }).catch(() => {}); J.tap();
  await page.waitForTimeout(800);
  const afterTap = await page.evaluate(() => ({ sticky: document.querySelector('.crk-stickybar')?.innerText.replace(/\s+/g, ' ').trim(), variantId: document.querySelector('[name="id"]')?.value, buyEnabled: !document.querySelector('.crk-btn')?.disabled }));
  await J.step(page, 'Tapped the sold-out size L', { soldOut, afterTap });
  results.p2 = J.j;
  await ctx.close();
}

// ============================================================
// P3 — Size-anxious denim buyer
// ============================================================
for (const [dev, label] of [[MOBILE, 'mobile'], [DESKTOP, 'desktop']]) {
  const ctx = await coldContext(dev);
  const page = await ctx.newPage();
  await applyThrottle(page);
  const J = makeJourney(label === 'mobile' ? 3 : '3d', `Size-anxious denim buyer (${label})`);
  J.j.t0 = Date.now();
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(2000);
  await J.step(page, 'Arrived on BLUE WASH OG JEANS, £60');
  await page.waitForTimeout(1600);
  await page.evaluate(() => document.querySelector('.ctc-close')?.click());
  await page.waitForTimeout(500);
  await J.step(page, 'Popup dismissed');
  // find measurements
  const sg = await page.evaluate(() => {
    const b = [...document.querySelectorAll('.crk-textbtn')].find(x => /SIZE GUIDE/i.test(x.innerText));
    if (!b) return null; const r = b.getBoundingClientRect();
    return { size: [Math.round(r.width), Math.round(r.height)], top: Math.round(r.top + scrollY) };
  });
  const yBefore = await page.evaluate(() => scrollY);
  await page.locator('.crk-textbtn', { hasText: /SIZE GUIDE/i }).first().click().catch(() => {}); J.tap();
  await page.waitForTimeout(1400);
  const yAfter = await page.evaluate(() => scrollY);
  const measureVisible = await page.evaluate(() => {
    const el = [...document.querySelectorAll('*')].find(e => /GARMENT LAID FLAT/.test(e.textContent || '') && e.children.length <= 2);
    if (!el) return { found: false };
    const r = el.getBoundingClientRect();
    return { found: true, top: Math.round(r.top), inViewport: r.top > -20 && r.top < innerHeight };
  });
  await J.step(page, 'Tapped SIZE GUIDE', { sizeGuideButton: sg, scrolledPx: yAfter - yBefore, measureVisible });
  await page.evaluate(() => { const el = [...document.querySelectorAll('*')].find(e => /GARMENT LAID FLAT/.test(e.textContent || '') && e.children.length <= 2); el?.scrollIntoView({ block: 'center' }); });
  await page.waitForTimeout(800);
  const table = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ').match(/GARMENT LAID FLAT[^]*?XL \d+cm \d+cm \d+cm \d+cm/);
    return t ? t[0] : null;
  });
  await J.step(page, 'Reading the measurement table', { table });
  // unit toggle
  await page.locator('.crk-unit', { hasText: /^IN$/ }).first().click().catch(() => {}); J.tap();
  await page.waitForTimeout(700);
  const inches = await page.evaluate(() => { const t = document.body.innerText.replace(/\s+/g, ' ').match(/GARMENT LAID FLAT[^]*?XL [\d."]+ [\d."]+ [\d."]+ [\d."]+/); return t ? t[0] : null; });
  await J.step(page, 'Switched the table to inches', { inches });
  // returns policy
  await page.evaluate(() => { const h = [...document.querySelectorAll('.crk-section-head')].find(x => /CHAIN OF CUSTODY/.test(x.innerText)); if (h) { h.scrollIntoView({ block: 'center' }); h.click(); } }); J.tap();
  await page.waitForTimeout(900);
  const returns = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    return { returnWindow: (t.match(/You have \d+ days[^.]*\./) || [null])[0], howToReturn: (t.match(/Start a return[^.]*\./) || [null])[0], contradictions: (t.match(/\d+\s*-\s*\d+ days delivery uk|UK \d[–-]\d working days|Ships within 24 hours|24HR DISPATCH/gi) || []) };
  });
  await J.step(page, 'Checking the returns policy', { returns });
  results[label === 'mobile' ? 'p3' : 'p3desktop'] = J.j;
  await ctx.close();
}

// ============================================================
// P4 — The sceptic
// ============================================================
{
  const ctx = await coldContext();
  const page = await ctx.newPage();
  await applyThrottle(page);
  const J = makeJourney(4, 'The sceptic');
  J.j.t0 = Date.now();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(3400);
  await J.step(page, 'Homepage, popup already up');
  await page.evaluate(() => document.querySelector('.ctc-close')?.click()); J.tap();
  await page.waitForTimeout(600);
  // 1. email address
  const emailHunt = await page.evaluate(() => {
    const a = [...document.querySelectorAll('a[href^="mailto:"]')];
    const inFooter = a.filter(x => x.closest('footer'));
    const r = a[0]?.getBoundingClientRect();
    return { count: a.length, address: a[0]?.getAttribute('href'), inFooter: inFooter.length > 0, requiresScrollViewports: r ? +((r.top + scrollY) / innerHeight).toFixed(2) : null, anyEmailTextOnHome: /@crooksldn|info@/i.test(document.body.innerText) };
  });
  await page.evaluate(() => document.querySelector('footer')?.scrollIntoView({ block: 'start' }));
  await page.waitForTimeout(900);
  await J.step(page, 'Scrolled to the footer hunting for a human', { emailHunt });
  // 2. returns policy — count taps
  await page.locator('footer a', { hasText: /^REFUNDS$/ }).first().click().catch(() => {}); J.tap();
  await page.waitForLoadState('load', { timeout: 180000 }).catch(() => {});
  await page.waitForTimeout(2200);
  const refundFacts = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    return { url: location.pathname, hasPolicy: /REFUND POLICY/i.test(t), lastUpdated: (t.match(/Last Updated:? ?[\d/]+/i) || [null])[0], mentionsCompany: (t.match(/Crooksldn LTD/g) || []).length, wordCount: t.split(' ').length, styled: !!document.querySelector('.crk-root') };
  });
  await J.step(page, 'Refund policy reached', { refundFacts, tapsFromHome: J.j.taps });
  // 3. social proof
  const proof = await page.evaluate(() => {
    const t = document.body.innerText;
    return { reviewsWidget: /review|rating|stars|trustpilot|verified buyer/i.test(t), socialLinks: [...document.querySelectorAll('a[href*="instagram"],a[href*="tiktok"]')].map(a => a.getAttribute('href')), companyNumber: /company (no|number)|registered in/i.test(t), address: /Unit \d|London[, ]/i.test(t) };
  });
  await J.step(page, 'Looking for evidence other people have bought here', { proof });
  // 4. contact page
  await page.goto(BASE + '/pages/contact', { waitUntil: 'load', timeout: 180000 }); J.tap();
  await page.waitForTimeout(2200);
  const contactFacts = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    return { fields: [...document.querySelectorAll('input,textarea')].map(i => i.name || i.type).filter(Boolean), hasEmailShown: /@/.test(t.replace(/Email\*?/g, '')), hasAddress: /Unit|Street|London\b/.test(t), hasResponseTime: /within \d+ (hours|days)|respond/i.test(t), textLen: t.length };
  });
  await J.step(page, 'The contact page', { contactFacts });
  results.p4 = J.j;
  await ctx.close();
}

// ============================================================
// P5 — The aimless browser
// ============================================================
{
  const ctx = await coldContext();
  const page = await ctx.newPage();
  await applyThrottle(page);
  const J = makeJourney(5, 'The aimless browser');
  J.j.t0 = Date.now();
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(1600);
  await J.step(page, 'Landed — the first screen is the canvas board');
  await page.waitForTimeout(2000);
  await J.step(page, 'Popup arrives offering a discount game');
  await page.evaluate(() => document.querySelector('.ctc-close')?.click()); J.tap();
  await page.waitForTimeout(600);
  for (const [frac, title] of [[0.5, 'Scrolled half a screen'], [1.3, 'Reached the catalogue grid'], [2.6, 'CASE 001 game section'], [3.6, 'WITNESS STATEMENT'], [4.6, 'REGISTER AS INFORMANT']]) {
    await page.evaluate((f) => window.scrollTo(0, innerHeight * f), frac);
    await page.waitForTimeout(800);
    await J.step(page, title);
  }
  const hooks = await page.evaluate(() => {
    const t = document.body.innerText;
    return {
      gameLink: [...document.querySelectorAll('a')].filter(a => /OPEN CASE FILE/i.test(a.innerText)).map(a => a.getAttribute('href')),
      emailCapture: !!document.querySelector('#crk-informant-email, input[type=email]'),
      emailCopy: (t.match(/Drops go to the register[^.]*\./) || [null])[0],
      socials: [...document.querySelectorAll('a[href*="instagram"],a[href*="tiktok"]')].length,
      witness: (t.match(/CROOKSLDN is an independent label[^]*?not for display\./) || [null])[0],
    };
  });
  await J.step(page, 'What is here to bring them back', { hooks });
  results.p5 = J.j;
  await ctx.close();
}

fs.writeFileSync('audit/evidence/journeys-1-5.json', JSON.stringify(results, null, 2));
console.log('\nwrote audit/evidence/journeys-1-5.json');
await browser.close();
