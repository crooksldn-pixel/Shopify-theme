import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';
const browser = await launch();
const out = {};
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const page = await ctx.newPage();
async function go(url){ for(let i=0;i<3;i++){ try{ await page.goto(url,{waitUntil:'domcontentloaded',timeout:120000}); await page.waitForTimeout(4000); return true;}catch(e){ console.log('retry',i,e.message.split('\n')[0]); } } return false; }
await go(BASE + '/products/cb2-wash-jeans');
await page.evaluate(() => { document.querySelector('.ctc-close')?.click(); document.querySelector('#shopify-pc__banner__btn-accept')?.click(); });
await page.waitForTimeout(1000);
const grab = () => page.evaluate(() => {
  const rows = [...document.querySelectorAll('table tr, [class*="measure"] tr, .crk-measure-row')].map(tr => tr.innerText.replace(/\s+/g,' ').trim()).filter(Boolean);
  const raw = (document.body.innerText.replace(/\s+/g,' ').match(/SIZE WAIST INSEAM RISE HEM[^]{0,220}/) || [null])[0];
  const active = [...document.querySelectorAll('.crk-unit')].map(b => b.innerText.trim() + (b.getAttribute('aria-pressed')==='true'||/is-|active|sel/.test(b.className) ? '*' : ''));
  return { rows: rows.slice(0,7), raw, active };
});
out.unitsCM = await grab();
await page.locator('.crk-unit', { hasText: /^IN$/ }).first().click();
await page.waitForTimeout(1000);
out.unitsIN = await grab();
console.log('=== UNIT TOGGLE ===');
console.log(' CM active:', out.unitsCM.active, '\n   ', out.unitsCM.raw);
console.log(' IN active:', out.unitsIN.active, '\n   ', out.unitsIN.raw);
await page.screenshot({ path: 'audit/screens/check-measure-inches.png' });

await page.evaluate(() => window.scrollTo(0,0)); await page.waitForTimeout(700);
await page.locator('.crk-textbtn', { hasText: /SIZE GUIDE/i }).first().click();
await page.waitForTimeout(1600);
out.sizeGuideLanding = await page.evaluate(() => {
  const vis=[]; for (const el of document.querySelectorAll('.crk-section-head, h1, .crk-h1, [class*="measure"]')) { const r=el.getBoundingClientRect(); if (r.bottom>0 && r.top<innerHeight) vis.push(el.innerText.replace(/\s+/g,' ').trim().slice(0,46)+` @${Math.round(r.top)}`); }
  return { scrollY: Math.round(scrollY), visible: vis };
});
console.log('\n=== SIZE GUIDE LANDING ===', JSON.stringify(out.sizeGuideLanding,null,1));
await page.screenshot({ path: 'audit/screens/check-sizeguide-landing.png' });

out.socialProof = await page.evaluate(() => {
  const t = document.body.innerText;
  return { starRatings: document.querySelectorAll('[class*="rating"],[class*="stars"],[itemprop="ratingValue"]').length,
    reviewBlocks: document.querySelectorAll('[class*="review"]').length,
    urgency: /\d+ (people|viewing|left|sold)|only \d+ left|hurry|ends in/i.test(t),
    companyNo: /company (no|number)/i.test(t), ltd: /\bLTD\b/.test(t), postcode: /[A-Z]{1,2}\d{1,2} ?\d[A-Z]{2}/.test(t),
    socials: [...document.querySelectorAll('a[href*="instagram"],a[href*="tiktok"]')].map(a=>a.getAttribute('href')),
    mailto: [...document.querySelectorAll('a[href^="mailto:"]')].map(a=>a.getAttribute('href')) };
});
console.log('\n=== TRUST SIGNALS ON PDP (strict) ===', JSON.stringify(out.socialProof,null,1));
fs.writeFileSync('audit/evidence/p2-fix.json', JSON.stringify(out,null,2));
await browser.close();
