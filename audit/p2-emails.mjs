import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const page = await ctx.newPage();
const out = {};
for (const [k,u] of [['refund','/policies/refund-policy'],['shipping','/policies/shipping-policy'],['pdp','/products/cb2-wash-jeans'],['home','/'],['contact','/pages/contact'],['tos','/policies/terms-of-service'],['privacy','/policies/privacy-policy']]) {
  try {
    await page.goto(BASE+u,{waitUntil:'domcontentloaded',timeout:120000});
    await page.waitForTimeout(2500);
    await page.evaluate(()=>{document.querySelector('.ctc-close')?.click();document.querySelector('#shopify-pc__banner__btn-accept')?.click();document.querySelectorAll('.crk-section-head').forEach(h=>{if(h.getAttribute('aria-expanded')==='false')h.click()})});
    await page.waitForTimeout(500);
    out[k] = await page.evaluate(()=>{
      const t=document.body.innerText.replace(/\s+/g,' ');
      return { emails:[...new Set(t.match(/[\w.+-]+@[\w.-]+\.\w+/g)||[])], mailto:[...new Set([...document.querySelectorAll('a[href^="mailto:"]')].map(a=>a.getAttribute('href')))],
        returnHow:(t.match(/[^.]{0,120}(return|refund)[^.]{0,120}(email|contact)[^.]{0,80}\./i)||[null])[0],
        postage:(t.match(/[^.]{0,100}(return (shipping|postage)|cost of return|responsible for)[^.]{0,120}\./i)||[null])[0] };
    });
  } catch(e){ out[k]={err:e.message.split('\n')[0]}; }
}
console.log(JSON.stringify(out,null,1));
fs.writeFileSync('audit/evidence/emails.json',JSON.stringify(out,null,2));
await browser.close();
