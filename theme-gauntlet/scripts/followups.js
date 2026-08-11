/* Pre-panel live checks: resolve ambiguous automation failures with targeted evidence.
 * Output: captures/{theme}/live/<check>.jpg + captures/live-checks.json
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const OUT = {};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const NEW = 'https://caijh1httspvte6b-100410786135.shopifypreview.com';
const OLD = 'https://crooksldn.com';

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    args: ['--ssl-version-max=tls1.2', '--disable-background-networking', '--disable-component-update'],
  });
  fs.mkdirSync(path.join(ROOT, 'captures', 'new', 'live'), { recursive: true });
  fs.mkdirSync(path.join(ROOT, 'captures', 'old', 'live'), { recursive: true });
  const shot = (page, theme, name, full = true) =>
    page.screenshot({ path: path.join(ROOT, 'captures', theme, 'live', name + '.jpg'), type: 'jpeg', quality: 60, fullPage: full }).catch(() => {});

  const mob = { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true };
  const desk = { viewport: { width: 1440, height: 900 } };
  const accept = async (page) => { try { const b = page.locator('button:has-text("Accept")').first(); if (await b.isVisible({ timeout: 1500 })) { await b.click(); await sleep(500); } } catch (e) {} };

  // A+B+C+D(mobile): NEW mobile menu, search, footer shipping, account hunt
  {
    const page = await (await browser.newContext(mob)).newPage();
    await page.goto(NEW, { waitUntil: 'load', timeout: 60000 }); await sleep(1000); await accept(page);
    // A: MENU
    try {
      await page.locator('header >> text=MENU').first().click({ timeout: 5000 });
      await sleep(900);
      await shot(page, 'new', 'menu-open-mobile', false);
      OUT.new_mobile_menu = { opens: true };
      const links = await page.evaluate(() => Array.from(document.querySelectorAll('.crk-drawer__link, [class*="drawer"] a')).map((a) => (a.textContent || '').trim() + '->' + a.getAttribute('href')).slice(0, 20));
      OUT.new_mobile_menu.links = links;
      await page.keyboard.press('Escape').catch(() => {});
      const close = page.locator('button:has-text("CLOSE"), [aria-label*="close" i]').first();
      if (await close.isVisible({ timeout: 800 }).catch(() => false)) await close.click().catch(() => {});
      await sleep(500);
    } catch (e) { OUT.new_mobile_menu = { opens: false, err: e.message.split('\n')[0] }; await shot(page, 'new', 'menu-open-mobile-FAILED', false); }
    // B: SEARCH
    try {
      await page.locator('header >> text=SEARCH').first().click({ timeout: 5000 });
      await sleep(1200);
      OUT.new_search = { afterClickUrl: page.url() };
      await shot(page, 'new', 'search-opened-mobile', false);
      const inp = page.locator('input[type="search"], input[name="q"]').first();
      if (await inp.isVisible({ timeout: 2000 }).catch(() => false)) {
        await inp.click(); await page.keyboard.type('jeans', { delay: 80 }); await sleep(1200);
        await shot(page, 'new', 'search-typed-mobile', false);
        await page.keyboard.press('Enter');
        await sleep(2000);
        OUT.new_search.resultsUrl = page.url();
        OUT.new_search.works = true;
        await shot(page, 'new', 'search-results-mobile');
      } else { OUT.new_search.works = 'no-input-found'; }
    } catch (e) { OUT.new_search = { works: false, err: e.message.split('\n')[0] }; }
    // C: footer shipping link
    try {
      await page.goto(NEW, { waitUntil: 'load', timeout: 60000 }); await sleep(800);
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(1200);
      const info = await page.evaluate(() => {
        const a = document.querySelector('a[href*="shipping-policy"]');
        if (!a) return { exists: false };
        const r = a.getBoundingClientRect();
        const cs = getComputedStyle(a);
        return { exists: true, text: (a.textContent || '').trim(), w: r.width, h: r.height, top: r.top, display: cs.display, visibility: cs.visibility, opacity: cs.opacity };
      });
      OUT.new_footer_shipping = info;
      await shot(page, 'new', 'footer-mobile', false);
      if (info.exists) {
        await page.locator('a[href*="shipping-policy"]').first().click({ timeout: 5000, force: true });
        await sleep(1500);
        OUT.new_footer_shipping.clickLandsOn = page.url();
        await shot(page, 'new', 'shipping-policy-mobile');
      }
    } catch (e) { OUT.new_footer_shipping = { err: e.message.split('\n')[0] }; }
    await page.context().close();
  }
  // D: account entry hunt on NEW (mobile menu + desktop header/footer)
  {
    const page = await (await browser.newContext(desk)).newPage();
    await page.goto(NEW, { waitUntil: 'load', timeout: 60000 }); await sleep(1000); await accept(page);
    OUT.new_account_desktop = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('a, button')).filter((e) => /account|log ?in|sign ?in/i.test((e.textContent || '') + (e.getAttribute('href') || '') + (e.getAttribute('aria-label') || '')));
      return els.map((e) => ({ tag: e.tagName, txt: (e.textContent || '').trim().slice(0, 30), href: (e.getAttribute('href') || '').slice(0, 60), visible: e.getBoundingClientRect().width > 0 })).slice(0, 10);
    });
    await shot(page, 'new', 'home-desktop-header', false);
    // E: NEW collection sort/filter presence
    await page.goto(NEW + '/collections/all', { waitUntil: 'load', timeout: 60000 }); await sleep(1200);
    OUT.new_collection_controls = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('a, button, select, summary')).filter((e) => /sort|filter|price/i.test((e.textContent || '') + (e.getAttribute('aria-label') || '')));
      return els.map((e) => ({ tag: e.tagName, txt: (e.textContent || '').trim().slice(0, 40), visible: e.getBoundingClientRect().width > 0 })).slice(0, 12);
    });
    await shot(page, 'new', 'collection-all-desktop', false);
    await page.context().close();
  }
  // F+G: OLD desktop footer links + account icon destination
  {
    const page = await (await browser.newContext(desk)).newPage();
    await page.goto(OLD, { waitUntil: 'load', timeout: 60000 }); await sleep(1200);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await sleep(1500);
    OUT.old_footer_links = await page.evaluate(() => {
      // bottom 1500px of the page = footer zone
      const bottom = document.body.scrollHeight - 1500;
      return Array.from(document.querySelectorAll('a')).filter((a) => {
        const r = a.getBoundingClientRect();
        return r.top + window.scrollY > bottom && r.width > 0;
      }).map((a) => (a.textContent || '').trim().slice(0, 30) + '->' + (a.getAttribute('href') || '').slice(0, 50)).slice(0, 25);
    });
    await shot(page, 'old', 'footer-desktop', false);
    try {
      await page.evaluate(() => window.scrollTo(0, 0)); await sleep(500);
      const acc = page.locator('header a[href*="account"], header [aria-label*="account" i], header a[href*="login"]').first();
      OUT.old_account_icon = { present: await acc.isVisible({ timeout: 2000 }).catch(() => false) };
      if (OUT.old_account_icon.present) {
        await acc.click({ timeout: 5000 });
        await sleep(3000);
        OUT.old_account_icon.landsOn = page.url();
        await shot(page, 'old', 'account-destination', false);
      }
    } catch (e) { OUT.old_account_icon = { err: e.message.split('\n')[0] }; }
    await page.context().close();
  }

  fs.writeFileSync(path.join(ROOT, 'captures', 'live-checks.json'), JSON.stringify(OUT, null, 1));
  console.log(JSON.stringify(OUT, null, 1));
  await browser.close();
})().catch((e) => { console.error('FAIL', e); process.exit(1); });
