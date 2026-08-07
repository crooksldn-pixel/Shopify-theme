import { chromium } from 'playwright';
const b = await chromium.launch({ args:['--no-sandbox','--proxy-server=http://127.0.0.1:36999','--ignore-certificate-errors'] });
const ctx = await b.newContext({ ignoreHTTPSErrors:true });
const p = await ctx.newPage();
try { const r = await p.goto('https://example.com',{waitUntil:'domcontentloaded',timeout:30000}); console.log('OK',r.status(),await p.title()); }
catch(e){ console.log('FAIL',e.message.split('\n')[0]); }
await b.close();
