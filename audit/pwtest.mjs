import { chromium } from 'playwright';
const b = await chromium.launch({ proxy: { server: 'http://127.0.0.1:36431' } });
const ctx = await b.newContext({ ignoreHTTPSErrors: true });
const p = await ctx.newPage();
for (const url of ['https://example.com','https://crooksldn.com','https://ezvw3xrffzdt93es-100410786135.shopifypreview.com']) {
  try { const r = await p.goto(url,{waitUntil:'domcontentloaded',timeout:45000}); console.log(url, r.status(), JSON.stringify(await p.title())); }
  catch(e){ console.log(url, 'FAIL', e.message.split('\n')[0]); }
}
await b.close();
