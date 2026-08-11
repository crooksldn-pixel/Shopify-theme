/* Post-panel live follow-ups (deduplicated from 10 batches' questions).
 * Output: captures/{theme}/live/*.jpg + data/followup-resolutions.json
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
  const shot = (page, theme, name, full = true) =>
    page.screenshot({ path: path.join(ROOT, 'captures', theme, 'live', name + '.jpg'), type: 'jpeg', quality: 60, fullPage: full }).catch(() => {});
  const mob = { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true };
  const desk = { viewport: { width: 1440, height: 900 } };
  const accept = async (page) => { try { const b = page.locator('button:has-text("Accept")').first(); if (await b.isVisible({ timeout: 1500 })) { await b.click(); await sleep(500); } } catch (e) {} };

  // FU1: NEW PDP accordions content (crewneck + jeans): expand all, extract text
  {
    const page = await (await browser.newContext(mob)).newPage();
    for (const [key, url] of [['crewneck', '/products/charcoal-cellblock-crewneck'], ['jeans', '/products/cb2-wash-jeans']]) {
      await page.goto(NEW + url, { waitUntil: 'load', timeout: 60000 }); await sleep(1200); await accept(page);
      // expand every accordion-ish header
      const heads = await page.locator('h2:has-text("SPECIFICATION"), h2:has-text("ITEM DESCRIPTION"), h2:has-text("MEASUREMENTS"), h2:has-text("CHAIN OF CUSTODY"), button:has-text("SIZE GUIDE"), summary').all();
      for (const h of heads.slice(0, 8)) { try { await h.click({ timeout: 2500 }); await sleep(500); } catch (e) {} }
      await sleep(800);
      await shot(page, 'new', `fu-accordions-${key}`);
      OUT[`new_pdp_accordions_${key}`] = await page.evaluate(() => {
        const grab = (sel) => Array.from(document.querySelectorAll(sel)).map((e) => (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 700));
        return {
          accordionText: grab('[class*="accordion"], details, [data-crk-acc], .crk-acc__body').slice(0, 10),
          sizeGuideVisible: !!Array.from(document.querySelectorAll('dialog, [class*="modal"], table')).find((e) => e.getBoundingClientRect().width > 0 && /size|waist|chest/i.test(e.textContent || '')),
        };
      });
      // try SIZE GUIDE dialog explicitly
      try {
        const sg = page.locator('button:has-text("SIZE GUIDE")').first();
        if (await sg.isVisible({ timeout: 1000 })) {
          await sg.click({ timeout: 3000 }); await sleep(900);
          await shot(page, 'new', `fu-sizeguide-${key}`, false);
          OUT[`new_sizeguide_${key}`] = await page.evaluate(() => {
            const d = Array.from(document.querySelectorAll('dialog, [class*="modal"], [class*="drawer"]')).find((e) => e.getBoundingClientRect().width > 100);
            return d ? (d.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 900) : 'no-dialog-appeared';
          });
          await page.keyboard.press('Escape').catch(() => {});
        } else OUT[`new_sizeguide_${key}`] = 'no-size-guide-button-on-this-product';
      } catch (e) { OUT[`new_sizeguide_${key}`] = 'err:' + e.message.split('\n')[0]; }
    }
    await page.context().close();
  }

  // FU2: currency selector hunt on NEW (mobile menu + desktop header/footer) and OLD control
  {
    const page = await (await browser.newContext(desk)).newPage();
    await page.goto(NEW, { waitUntil: 'load', timeout: 60000 }); await sleep(1200); await accept(page);
    OUT.new_currency_ui = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('select, button, a, [class*="currency"], [class*="localization"]')).filter((e) => /USD|GBP|currency|country|region|\$|£/.test((e.textContent || '').slice(0, 40)) && (e.textContent || '').length < 40);
      return els.map((e) => ({ tag: e.tagName, txt: (e.textContent || '').trim().slice(0, 30), visible: e.getBoundingClientRect().width > 0 })).slice(0, 10);
    });
    // open the desktop MENU drawer too (FU5: ACCOUNT in desktop menu?)
    try {
      await page.locator('header >> text=MENU').first().click({ timeout: 4000 }); await sleep(900);
      await shot(page, 'new', 'fu-desktop-menu', false);
      OUT.new_desktop_menu_links = await page.evaluate(() =>
        Array.from(document.querySelectorAll('[class*="drawer"] a, dialog a')).filter((a) => a.getBoundingClientRect().width > 0)
          .map((a) => (a.textContent || '').trim().slice(0, 25) + '->' + (a.getAttribute('href') || '')).slice(0, 20));
    } catch (e) { OUT.new_desktop_menu_links = 'menu-open-failed: ' + e.message.split('\n')[0]; }
    await page.context().close();
    const p2 = await (await browser.newContext(desk)).newPage();
    await p2.goto(OLD, { waitUntil: 'load', timeout: 60000 }); await sleep(1200);
    OUT.old_currency_ui = await p2.evaluate(() => {
      const els = Array.from(document.querySelectorAll('select, button, a, [class*="currency"], [class*="localization"]')).filter((e) => /USD|GBP|currency/.test((e.textContent || '').slice(0, 30)));
      return els.map((e) => ({ tag: e.tagName, txt: (e.textContent || '').trim().slice(0, 30), visible: e.getBoundingClientRect().width > 0 })).slice(0, 6);
    });
    await p2.context().close();
  }

  // FU3: timed popup on NEW mobile home — wait 20s
  {
    const page = await (await browser.newContext(mob)).newPage();
    await page.goto(NEW, { waitUntil: 'load', timeout: 60000 });
    await accept(page);
    await sleep(20000);
    const popup = await page.evaluate(() => {
      const d = Array.from(document.querySelectorAll('dialog, [class*="popup"], [class*="modal"]')).find((e) => e.getBoundingClientRect().width > 150 && /cuff|crack|discount|%/i.test(e.textContent || ''));
      return d ? (d.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 400) : null;
    });
    OUT.new_mobile_timed_popup = { appearedWithin20s: !!popup, text: popup };
    await shot(page, 'new', 'fu-home-after-20s', false);
    await page.context().close();
  }

  // FU4: account login walls, both themes
  {
    for (const [theme, base] of [['old', OLD], ['new', NEW]]) {
      const page = await (await browser.newContext(mob)).newPage();
      try {
        await page.goto(base + '/account/login', { waitUntil: 'load', timeout: 60000 }).catch(() => {});
        await sleep(8000);
        OUT[theme + '_account_login'] = {
          url: page.url().slice(0, 120),
          hasEmailField: await page.locator('input[type="email"], input[name*="email" i]').first().isVisible({ timeout: 1500 }).catch(() => false),
          bodySnippet: await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200)).catch(() => null),
        };
        await shot(page, theme, 'fu-account-login', false);
      } catch (e) { OUT[theme + '_account_login'] = { err: e.message.split('\n')[0] }; }
      await page.context().close();
    }
  }

  // FU6: consent persistence on NEW desktop: accept on home -> PDP + cart clean?
  {
    const page = await (await browser.newContext(desk)).newPage();
    await page.goto(NEW, { waitUntil: 'load', timeout: 60000 }); await sleep(1500);
    const seen1 = await page.locator('#shopify-pc__banner').isVisible({ timeout: 2500 }).catch(() => false);
    await accept(page);
    await page.goto(NEW + '/products/charcoal-cellblock-crewneck', { waitUntil: 'load', timeout: 60000 }); await sleep(1500);
    const seen2 = await page.locator('#shopify-pc__banner').isVisible({ timeout: 2000 }).catch(() => false);
    await page.goto(NEW + '/cart', { waitUntil: 'load', timeout: 60000 }); await sleep(1500);
    const seen3 = await page.locator('#shopify-pc__banner').isVisible({ timeout: 2000 }).catch(() => false);
    OUT.new_consent_persistence = { onHomeDesktop: seen1, onPdpAfterAccept: seen2, onCartAfterAccept: seen3 };
    await page.context().close();
  }

  // FU7: express-pay button in NEW cart (blank yellow?)
  {
    const page = await (await browser.newContext(mob)).newPage();
    await page.goto(NEW + '/products/charcoal-cellblock-crewneck', { waitUntil: 'load', timeout: 60000 }); await sleep(1200); await accept(page);
    try { await page.locator('button.crk-size[data-value="M"]').first().click({ timeout: 3000 }); } catch (e) {}
    try { await page.locator('button[name="add"]').first().click({ timeout: 5000 }); await sleep(2000); } catch (e) {}
    await page.goto(NEW + '/cart', { waitUntil: 'load', timeout: 60000 }); await sleep(2500);
    OUT.new_cart_express_pay = await page.evaluate(() => {
      const wall = document.querySelector('[data-shopify="dynamic-checkout-cart"], .additional-checkout-buttons, shopify-accelerated-checkout-cart');
      if (!wall) return { present: false };
      const ifr = wall.querySelector('iframe');
      return { present: true, hasIframe: !!ifr, iframeSrc: ifr ? (ifr.src || '').slice(0, 80) : null, text: (wall.textContent || '').trim().slice(0, 80), h: wall.getBoundingClientRect().height };
    }).catch(() => null);
    await shot(page, 'new', 'fu-cart-express-pay', false);
    await page.context().close();
  }

  // FU8: FILED status — is a FILED item buyable? (v2-baggies card shows FILED date)
  {
    const page = await (await browser.newContext(mob)).newPage();
    await page.goto(NEW + '/collections/all', { waitUntil: 'load', timeout: 60000 }); await sleep(1200); await accept(page);
    OUT.new_filed_cards = await page.evaluate(() =>
      Array.from(document.querySelectorAll('[class*="card"], li, article')).map((c) => (c.textContent || '').replace(/\s+/g, ' ').trim())
        .filter((t) => /FILED/.test(t) && t.length < 300).slice(0, 5));
    await page.goto(NEW + '/products/v2-baggies', { waitUntil: 'load', timeout: 60000 }); await sleep(1200);
    OUT.new_filed_pdp_buyable = await page.evaluate(() => {
      const b = document.querySelector('button[name="add"]');
      return { atcText: b ? b.textContent.trim().slice(0, 30) : null, disabled: b ? b.disabled : null, filedBadge: /FILED/.test(document.body.innerText) };
    });
    await page.context().close();
  }

  // FU9: social links hrefs + status
  {
    const page = await (await browser.newContext(mob)).newPage();
    await page.goto(NEW, { waitUntil: 'load', timeout: 60000 }); await sleep(1000); await accept(page);
    OUT.new_social_links = await page.evaluate(() =>
      Array.from(document.querySelectorAll('a[href*="instagram"], a[href*="tiktok"], a[href^="mailto"]')).map((a) => (a.textContent || '').trim().slice(0, 15) + '->' + a.href.slice(0, 80)));
    await page.context().close();
  }

  // FU10: OLD /pages/tracking content
  {
    const page = await (await browser.newContext(desk)).newPage();
    await page.goto(OLD + '/pages/tracking', { waitUntil: 'load', timeout: 60000 }); await sleep(1500);
    OUT.old_tracking_page = {
      bodyText: await page.evaluate(() => (document.querySelector('main') || document.body).innerText.replace(/\s+/g, ' ').trim().slice(0, 300)).catch(() => null),
      hasForm: await page.locator('main input, main form').first().isVisible({ timeout: 1500 }).catch(() => false),
    };
    await shot(page, 'old', 'fu-tracking-page', false);
    // FU12: OLD account icon destination with patience
    await page.goto(OLD, { waitUntil: 'load', timeout: 60000 }); await sleep(1000);
    try {
      await page.locator('header a[href*="account"], header [aria-label*="account" i], header a[href*="login"]').first().click({ timeout: 5000 });
      await sleep(6000);
      OUT.old_account_click = { landsOn: page.url().slice(0, 130), bodySnippet: await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 150)).catch(() => null) };
      await shot(page, 'old', 'fu-account-destination', false);
    } catch (e) { OUT.old_account_click = { err: e.message.split('\n')[0] }; }
    await page.context().close();
  }

  fs.writeFileSync(path.join(ROOT, 'data', 'followup-resolutions.json'), JSON.stringify(OUT, null, 1));
  console.log(JSON.stringify(OUT, null, 1).slice(0, 6000));
  await browser.close();
})().catch((e) => { console.error('FAIL', e); process.exit(1); });
