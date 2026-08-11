const { chromium } = require('playwright');
const { execSync } = require('child_process');
const MY = ['UseMLKEM', 'PostQuantumKeyAgreement', 'PostQuantumKyber'];
(async () => {
  const probe = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', proxy: { server: process.env.HTTPS_PROXY } });
  let defFlag = null;
  try {
    const cmdlines = execSync("cat /proc/$(pgrep -f 'chrome-linux/chrome' | head -1)/cmdline | tr '\\0' '\\n'").toString().split('\n');
    defFlag = cmdlines.find(a => a.startsWith('--disable-features='));
  } catch (e) { console.log('proc read failed', e.message); }
  console.log('default flag:', defFlag);
  await probe.close();
  const merged = '--disable-features=' + [...(defFlag ? defFlag.split('=')[1].split(',') : []), ...MY].join(',');
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    ignoreDefaultArgs: defFlag ? [defFlag] : [],
    args: [merged, '--disable-background-networking', '--disable-component-update']
  });
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })).newPage();
  for (const [name, url] of [['example','https://example.com'],['OLD','https://crooksldn.com'],['NEW','https://caijh1httspvte6b-100410786135.shopifypreview.com']]) {
    const t0 = Date.now();
    const r = await page.goto(url, { waitUntil: 'load', timeout: 60000 });
    const theme = await page.evaluate(() => window.Shopify && window.Shopify.theme && ({id: window.Shopify.theme.id, name: window.Shopify.theme.name})).catch(()=>null);
    console.log(name, r.status(), (Date.now()-t0)+'ms', JSON.stringify(theme));
  }
  await browser.close(); console.log('SMOKE4 OK');
})().catch(e => { console.error('FAIL', e.message.split('\n')[0]); process.exit(1); });
