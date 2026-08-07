import { chromium } from 'playwright';
const variants = [
  { name:'args-proxy+nosandbox', opts:{ args:['--no-sandbox','--proxy-server=http://127.0.0.1:36431','--ignore-certificate-errors','--disable-dev-shm-usage'] } },
  { name:'headed-chromium-channel', opts:{ channel:'chromium', proxy:{server:'http://127.0.0.1:36431'}, args:['--no-sandbox','--ignore-certificate-errors'] } },
];
for (const v of variants) {
  try {
    const b = await chromium.launch(v.opts);
    const ctx = await b.newContext({ ignoreHTTPSErrors:true });
    const p = await ctx.newPage();
    p.on('requestfailed', r => console.log('  reqfail', r.url().slice(0,60), r.failure()?.errorText));
    try { const r = await p.goto('https://example.com',{waitUntil:'domcontentloaded',timeout:30000}); console.log(v.name,'OK',r.status(),await p.title()); }
    catch(e){ console.log(v.name,'FAIL',e.message.split('\n')[0]); }
    await b.close();
  } catch(e){ console.log(v.name,'LAUNCHFAIL',e.message.split('\n')[0]); }
}
