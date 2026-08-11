const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', proxy: { server: process.env.HTTPS_PROXY }, args: ['--ssl-version-max=tls1.2', '--disable-background-networking'] });
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })).newPage();
  await page.goto('https://caijh1httspvte6b-100410786135.shopifypreview.com/products/charcoal-cellblock-crewneck', { waitUntil: 'load', timeout: 60000 });
  await new Promise(r => setTimeout(r, 1500));
  // fixed body children (preview badge hunt)
  console.log('FIXED BODY CHILDREN:', await page.evaluate(() => Array.from(document.body.children).map(el => {
    const cs = getComputedStyle(el);
    return cs.position === 'fixed' ? { tag: el.tagName, id: el.id, cls: (el.className||'').toString().slice(0,60), txt: (el.textContent||'').trim().slice(0,60) } : null;
  }).filter(Boolean)));
  // consent dialog
  console.log('CONSENT:', await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(b => /accept/i.test(b.textContent||''));
    return b ? { cls: b.className.slice(0,60), parent: b.closest('div,dialog,section') ? (b.closest('[class]')||{}).className : null } : null;
  }));
  // accept consent then dump variant picker area
  try { await page.locator('button:has-text("Accept")').first().click({ timeout: 3000 }); await new Promise(r => setTimeout(r, 800)); } catch(e) { console.log('no accept click', e.message.split('\n')[0]); }
  console.log('VARIANT MARKUP:', await page.evaluate(() => {
    const f = document.querySelector('form[action*="/cart/add"]');
    if (!f) return 'no form';
    const clone = f.cloneNode(true);
    clone.querySelectorAll('script,style,svg').forEach(e => e.remove());
    return clone.outerHTML.replace(/\s+/g,' ').slice(0, 2500);
  }));
  console.log('RADIOS:', await page.evaluate(() => Array.from(document.querySelectorAll('input[type="radio"]')).map(i => ({name:i.name, value:i.value, id:i.id.slice(0,40), disabled:i.disabled})).slice(0,10)));
  console.log('SIZE BUTTONS:', await page.evaluate(() => Array.from(document.querySelectorAll('button, [role="radio"], label')).filter(e => /^(XS|S|M|L|XL|XXL)$/.test((e.textContent||'').trim())).map(e => ({tag:e.tagName, cls:(e.className||'').toString().slice(0,50), txt:(e.textContent||'').trim()})).slice(0,10)));
  await browser.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
