const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', proxy: { server: process.env.HTTPS_PROXY }, args: ['--ssl-version-max=tls1.2', '--disable-background-networking'] });
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })).newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0,150)); });
  await page.goto('https://caijh1httspvte6b-100410786135.shopifypreview.com/search', { waitUntil: 'load', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2000));
  const state = () => page.evaluate(() => {
    const i = document.getElementById('cmdk-input');
    if (!i) return null;
    const r = i.getBoundingClientRect(); const cs = getComputedStyle(i);
    let anc = [], n = i;
    while (n && n !== document.body) { const c = getComputedStyle(n); if (c.display === 'none' || c.visibility === 'hidden' || c.opacity === '0') anc.push((n.tagName + '.' + (n.className||'')).slice(0,60) + ` d=${c.display} v=${c.visibility} o=${c.opacity}`); n = n.parentElement; }
    return { w: r.width, h: r.height, display: cs.display, hiddenAncestors: anc };
  });
  console.log('initial:', JSON.stringify(await state()));
  await page.keyboard.type('jean');
  await new Promise(r => setTimeout(r, 1500));
  console.log('after typing:', JSON.stringify(await state()));
  console.log('url now:', page.url());
  await page.screenshot({ path: 'captures/new/live/search-after-typing.jpg', type: 'jpeg', quality: 60 });
  console.log('console errors:', JSON.stringify(errs.slice(0,6), null, 1));
  await browser.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
