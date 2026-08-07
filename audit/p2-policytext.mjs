import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';
const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const page = await ctx.newPage();
const out={};
for (const [k,u] of [['refund','/policies/refund-policy'],['tos','/policies/terms-of-service'],['shipping','/policies/shipping-policy']]) {
  await page.goto(BASE+u,{waitUntil:'domcontentloaded',timeout:120000});
  await page.waitForTimeout(2500);
  const t = await page.evaluate(()=>document.body.innerText.replace(/\s+/g,' '));
  out[k]={ brackets: [...new Set(t.match(/\[[^\]]{2,60}\]/g)||[])], full: t };
  console.log(`\n===== ${k} — bracketed placeholders: ${JSON.stringify(out[k].brackets)}`);
  for (const b of out[k].brackets) {
    const i=t.indexOf(b);
    console.log('   ...'+t.slice(Math.max(0,i-130), i+b.length+60).trim()+'...');
  }
}
fs.writeFileSync('audit/evidence/policy-text.json',JSON.stringify(out,null,2));
await browser.close();
