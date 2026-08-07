import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const out = {};

// --- PDP anatomy: accordions, size guide, measurements ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(3000);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });

  out.pdp = await p.evaluate(() => {
    const sections = [...document.querySelectorAll('.crk-section-head')].map(h => ({
      label: h.innerText.replace(/\s+/g, ' ').trim(),
      expanded: h.getAttribute('aria-expanded'),
      bodyText: (h.parentElement?.querySelector('.crk-section-body, [class*="body"]')?.innerText || h.nextElementSibling?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
    }));
    return {
      sections,
      sizeGuideBtn: !!document.querySelector('.crk-textbtn'),
      sizeGuideText: document.querySelector('.crk-textbtn')?.innerText.trim(),
      fullText: document.body.innerText.replace(/\s+/g, ' ').trim(),
      deliveryMsg: document.querySelector('[class*="delivery"]')?.innerText?.trim() || null,
      stickybar: document.querySelector('.crk-stickybar')?.innerText.replace(/\s+/g, ' ').trim(),
    };
  });

  // open size guide
  const sg = p.locator('.crk-textbtn', { hasText: /SIZE GUIDE/i }).first();
  if (await sg.count()) {
    await sg.click();
    await p.waitForTimeout(1200);
    out.sizeGuide = await p.evaluate(() => {
      const dlg = document.querySelector('dialog[open], .crk-modal, [class*="sizeguide"], [class*="size-guide"]');
      return dlg ? { found: true, cls: dlg.className, text: dlg.innerText.replace(/\s+/g, ' ').trim().slice(0, 1200) } : { found: false, bodyDelta: document.body.innerText.length };
    });
    await p.screenshot({ path: 'audit/screens/recon-sizeguide.png' });
  }
  await p.close();
}

// --- measurements accordion content, expanded ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  await p.evaluate(() => { document.querySelectorAll('.crk-section-head').forEach(h => { if (h.getAttribute('aria-expanded') === 'false') h.click(); }); });
  await p.waitForTimeout(900);
  out.pdpExpanded = await p.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').trim());
  // measurement table
  out.measurements = await p.evaluate(() => {
    const t = document.querySelector('.crk-measure, table, [class*="measure"]');
    return t ? t.innerText.replace(/[ \t]+/g, ' ').trim().slice(0, 900) : null;
  });
  await p.screenshot({ path: 'audit/screens/recon-pdp-expanded.png', fullPage: true });
  await p.close();
}

// --- menu + footer + nav ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(3000);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  out.footer = await p.evaluate(() => {
    const f = document.querySelector('footer, [class*="crk-footer"]');
    return f ? { text: f.innerText.replace(/\s+/g, ' ').trim(), links: [...f.querySelectorAll('a')].map(a => `${a.innerText.replace(/\s+/g, ' ').trim()} -> ${a.getAttribute('href')}`) } : null;
  });
  const menuBtn = p.locator('button', { hasText: /^MENU$/ }).first();
  if (await menuBtn.count()) {
    await menuBtn.click(); await p.waitForTimeout(1200);
    out.menu = await p.evaluate(() => {
      const d = document.querySelector('.crk-drawer, dialog[open], [class*="drawer"]');
      return d ? { text: d.innerText.replace(/\s+/g, ' ').trim(), links: [...d.querySelectorAll('a')].map(a => `${a.innerText.replace(/\s+/g, ' ').trim()} -> ${a.getAttribute('href')}`) } : null;
    });
    await p.screenshot({ path: 'audit/screens/recon-menu.png' });
  }
  out.homeFullText = await p.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').trim());
  await p.close();
}

// --- content pages ---
for (const [key, url] of [['contact', '/pages/contact'], ['shipping', '/policies/shipping-policy'], ['refund', '/policies/refund-policy'], ['collectionNew', '/collections/new'], ['search', '/search?q=jeans'], ['account', '/account'], ['404', '/pages/does-not-exist']]) {
  const p = await ctx.newPage();
  try {
    const r = await p.goto(BASE + url, { waitUntil: 'load', timeout: 150000 });
    await p.waitForTimeout(2500);
    await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
    out[key] = { status: r.status(), url, text: (await p.locator('body').innerText()).replace(/\s+/g, ' ').trim().slice(0, 1600) };
    await p.screenshot({ path: `audit/screens/recon-${key}.png`, fullPage: true });
  } catch (e) { out[key] = { error: e.message.split('\n')[0] }; }
  await p.close();
}

// --- sold-out variant behaviour (V2 BAGGIES M/L/XL) ---
{
  const p = await ctx.newPage();
  await p.goto(BASE + '/products/v2-baggies', { waitUntil: 'load', timeout: 150000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  out.soldOut = await p.evaluate(() => ({
    sizeButtons: [...document.querySelectorAll('.crk-size')].map(b => ({ label: b.innerText.trim(), disabled: b.disabled, aria: b.getAttribute('aria-disabled'), cls: b.className, title: b.getAttribute('title') })),
    text: document.body.innerText.replace(/\s+/g, ' ').trim().slice(0, 900),
  }));
  // click a sold-out size
  const soldBtn = p.locator('.crk-size', { hasText: /^M$/ }).first();
  if (await soldBtn.count()) { await soldBtn.click({ force: true }).catch(() => {}); await p.waitForTimeout(1000); }
  out.soldOutAfterClick = await p.evaluate(() => ({
    stickybar: document.querySelector('.crk-stickybar')?.innerText.replace(/\s+/g, ' ').trim(),
    buyBtn: document.querySelector('.crk-btn')?.innerText.trim(),
    anyNotify: /notify|restock|back in stock|email me/i.test(document.body.innerText),
    inStockText: [...document.querySelectorAll('*')].filter(e => e.children.length === 0 && /stock|sold/i.test(e.innerText || '')).map(e => e.innerText.trim()).slice(0, 6),
  }));
  await p.screenshot({ path: 'audit/screens/recon-soldout.png' });
  await p.close();
}

fs.writeFileSync('audit/evidence/recon.json', JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 12000));
await browser.close();
