const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    args: ['--disable-background-networking', '--disable-component-update']
  });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  page.on('requestfailed', r => console.log('REQFAIL', r.url().slice(0,90), r.failure() && r.failure().errorText));
  for (const url of ['https://example.com', 'https://crooksldn.com', 'https://caijh1httspvte6b-100410786135.shopifypreview.com']) {
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        console.log('OK', url, resp && resp.status());
        break;
      } catch (e) {
        console.log('FAIL attempt', attempt, url, e.message.split('\n')[0]);
        await new Promise(r => setTimeout(r, 2000 * attempt));
      }
    }
  }
  const theme = await page.evaluate(() => window.Shopify && window.Shopify.theme).catch(() => null);
  console.log('theme:', JSON.stringify(theme));
  await browser.close();
})().catch(e => { console.error('SMOKE FAIL', e.message); process.exit(1); });
