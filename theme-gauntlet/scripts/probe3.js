const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', proxy: { server: process.env.HTTPS_PROXY }, args: ['--ssl-version-max=tls1.2', '--disable-background-networking'] });
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })).newPage();
  await page.goto('https://caijh1httspvte6b-100410786135.shopifypreview.com/products/v2-baggies', { waitUntil: 'load', timeout: 60000 });
  await new Promise(r => setTimeout(r, 1500));
  try { const b = page.locator('button:has-text("Accept")').first(); if (await b.isVisible({ timeout: 1500 })) { await b.click(); await new Promise(r => setTimeout(r, 600)); } } catch (e) {}
  const read = () => page.evaluate(() => {
    const atcb = document.querySelector('button[name="add"], form[action*="/cart/add"] button[type="submit"]');
    const m = document.querySelector('button.crk-size[data-value="M"]');
    return {
      stockline: (document.querySelector('[data-crk-stockline]') || {}).textContent,
      atc: atcb ? atcb.textContent.trim().slice(0, 40) : null,
      atcDisabled: atcb ? atcb.disabled : null,
      mBtnClass: m ? m.className : null,
      mBtnStyle: m ? getComputedStyle(m).textDecorationLine + '/op' + getComputedStyle(m).opacity : null,
    };
  });
  console.log('before:', JSON.stringify(await read()));
  await page.locator('button.crk-size[data-value="M"]').first().click({ timeout: 5000 });
  await new Promise(r => setTimeout(r, 1200));
  console.log('after selecting sold-out M:', JSON.stringify(await read()));
  await page.screenshot({ path: 'captures/new/live/oos-M-selected.jpg', type: 'jpeg', quality: 60 });
  await browser.close();
})().catch(e => { console.error('FAIL', e.message.split('\n')[0]); process.exit(1); });
