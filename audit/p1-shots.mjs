import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE, DESKTOP } from './lib.mjs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);

// correct catalogue, in GBP this time
const c0 = await ctx.newPage();
await c0.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });
const handles = ['3-clives-tee', 'black-socks', 'cb1-wash-jorts', 'cb2-wash-jeans', 'broadcast-tee', 'charcoal-cellblock-crewneck', 'charcoal-cellblock-shorts', 'crxst-rz-t-shirt', 'cb2-wash-jorts', 'cb1-wash-jeans', 'large-duffle-bag', 'evil-clive-tee', 'v2-baggies', 'white-socks'];
const catalogue = [];
for (const h of handles) {
  const j = await c0.evaluate(async (h) => (await fetch(`/products/${h}.js`)).json(), h);
  catalogue.push({ handle: h, title: j.title, priceGBP: j.price / 100, available: j.available, images: (j.images || []).length,
    featured: (j.featured_image || '').split('/').pop().split('?')[0],
    variants: (j.variants || []).map(v => ({ t: v.title, avail: v.available })),
    soldOutVariants: (j.variants || []).filter(v => !v.available).map(v => v.title),
    descChars: (j.description || '').replace(/<[^>]*>/g, '').trim().length,
    desc: (j.description || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim() });
}
const cur = await c0.evaluate(() => window.Shopify.currency.active);
fs.writeFileSync('audit/evidence/catalogue.json', JSON.stringify({ currency: cur, products: catalogue }, null, 2));
console.log('catalogue currency:', cur);
for (const c of catalogue) console.log(`  ${c.title.padEnd(32)} £${String(c.priceGBP).padEnd(6)} imgs=${c.images} desc=${c.descChars}ch soldOut=[${c.soldOutVariants.join(',')}]`);
await c0.close();

const shots = [
  ['home-firstpaint', BASE + '/', 0, false],
  ['home-popup', BASE + '/', 0, false],
  ['home-nopopup', BASE + '/', 0, true],
  ['pdp-tee', BASE + '/products/3-clives-tee', 0, true],
  ['pdp-denim', BASE + '/products/cb2-wash-jeans', 0, true],
  ['collection-all', BASE + '/collections/all', 0, true],
  ['cart', BASE + '/cart', 0, true],
  ['contact', BASE + '/pages/contact', 0, true],
  ['shipping-policy', BASE + '/policies/shipping-policy', 0, true],
  ['refund-policy', BASE + '/policies/refund-policy', 0, true],
  ['search', BASE + '/search', 0, true],
  ['account', BASE + '/account', 0, true],
];

for (const [name, url, _s, clear] of shots) {
  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: 'load', timeout: 150000 });
    await page.waitForTimeout(3200);
    if (clear) {
      await page.evaluate(() => {
        document.querySelectorAll('.ctc-overlay').forEach(e => e.remove());
        document.querySelectorAll('.shopify-pc__banner, [class*="shopify-pc__banner"]').forEach(e => e.remove());
        document.querySelectorAll('#PBarNextFrame, [id*="PBar"]').forEach(e => e.remove());
        document.body.style.overflow = '';
      });
      await page.waitForTimeout(500);
    }
    await page.screenshot({ path: `audit/screens/${name}.png` });
    await page.screenshot({ path: `audit/screens/${name}-full.png`, fullPage: true });
    const t = await page.locator('body').innerText();
    console.log(`shot ${name}: ${t.replace(/\s+/g, ' ').trim().slice(0, 90)}`);
  } catch (e) { console.log(`shot ${name} FAILED: ${e.message.split('\n')[0]}`); }
  await page.close();
}
await ctx.close();

// desktop set
const dctx = await newContext(browser, DESKTOP);
await primePreview(dctx);
for (const [name, url] of [['d-home', BASE + '/'], ['d-pdp-denim', BASE + '/products/cb2-wash-jeans'], ['d-collection', BASE + '/collections/all']]) {
  const page = await dctx.newPage();
  await page.goto(url, { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(3200);
  await page.evaluate(() => { document.querySelectorAll('.ctc-overlay,.shopify-pc__banner,[id*="PBar"]').forEach(e => e.remove()); document.body.style.overflow = ''; });
  await page.screenshot({ path: `audit/screens/${name}.png` });
  await page.close();
}
await browser.close();
console.log('screenshots written to audit/screens/');
