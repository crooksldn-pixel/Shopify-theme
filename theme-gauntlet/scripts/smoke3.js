const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    args: ['--ssl-version-max=tls1.2', '--disable-background-networking', '--disable-component-update']
  });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  for (const [name, url] of [['example','https://example.com'],['OLD','https://crooksldn.com'],['NEW','https://caijh1httspvte6b-100410786135.shopifypreview.com']]) {
    const t0 = Date.now();
    const r = await page.goto(url, { waitUntil: 'load', timeout: 60000 });
    const theme = await page.evaluate(() => window.Shopify && window.Shopify.theme && ({id: window.Shopify.theme.id, name: window.Shopify.theme.name})).catch(()=>null);
    console.log(name, r.status(), (Date.now()-t0)+'ms', JSON.stringify(theme));
  }
  await browser.close(); console.log('SMOKE3 OK');
})().catch(e => { console.error('FAIL', e.message.split('\n')[0]); process.exit(1); });
