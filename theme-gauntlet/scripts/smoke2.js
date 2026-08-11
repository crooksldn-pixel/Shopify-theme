const { chromium } = require('playwright');
const ARGSETS = [
  ['--disable-features=EncryptedClientHello,PostQuantumKyber,UseMLKEM,UseDnsHttpsSvcb', '--disable-quic'],
  ['--disable-features=EncryptedClientHello', '--disable-quic'],
  ['--disable-quic'],
];
(async () => {
  for (const extra of ARGSETS) {
    const browser = await chromium.launch({
      executablePath: '/opt/pw-browsers/chromium',
      proxy: { server: process.env.HTTPS_PROXY },
      args: ['--disable-background-networking', '--disable-component-update', ...extra]
    });
    const page = await (await browser.newContext()).newPage();
    let ok = false;
    try {
      const r = await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 20000 });
      ok = r && r.status() === 200;
    } catch (e) { console.log('args', extra.join(' '), '->', e.message.split('\n')[0]); }
    if (ok) {
      console.log('WORKS with:', extra.join(' '));
      const r2 = await page.goto('https://caijh1httspvte6b-100410786135.shopifypreview.com', { waitUntil: 'domcontentloaded', timeout: 45000 });
      console.log('NEW status', r2.status(), JSON.stringify(await page.evaluate(() => window.Shopify && window.Shopify.theme)));
      await browser.close();
      process.exit(0);
    }
    await browser.close();
  }
  console.log('ALL ARGSETS FAILED');
  process.exit(1);
})();
