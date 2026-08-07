import { launch, newContext, primePreview, applyThrottle, BASE, MOBILE } from './lib.mjs';
const browser = await launch();
async function run(label, blockPattern) {
  const ctx = await newContext(browser, MOBILE);
  await primePreview(ctx);
  const page = await ctx.newPage();
  if (blockPattern) await page.route(blockPattern, r => r.abort());
  await page.addInitScript(`window.__cls=0;new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__cls+=e.value}).observe({type:'layout-shift',buffered:true});`);
  await applyThrottle(page);
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 180000 });
  await page.waitForTimeout(7000);
  const cls = await page.evaluate(() => +window.__cls.toFixed(4));
  const fonts = await page.evaluate(() => [...new Set([...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family))]);
  console.log(`${label.padEnd(34)} CLS=${cls}   loaded fonts: ${fonts.join(', ')}`);
  await ctx.close();
  return cls;
}
await run('baseline (all fonts)', null);
await run('crx-mono.woff2 blocked', '**/crx-mono*.woff2');
await run('vt323.woff2 blocked', '**/vt323*.woff2');
await run('all theme woff2 blocked', '**/*.woff2');
await browser.close();
