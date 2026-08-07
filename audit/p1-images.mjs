import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);
const page = await ctx.newPage();
await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });

// 1. product identity check across the whole catalogue
const handles = ['3-clives-tee','black-socks','cb1-wash-jorts','cb2-wash-jeans','broadcast-tee','charcoal-cellblock-crewneck','charcoal-cellblock-shorts','crxst-rz-t-shirt','cb2-wash-jorts','cb1-wash-jeans','large-duffle-bag','evil-clive-tee','v2-baggies','white-socks'];
const catalogue = [];
for (const h of handles) {
  const j = await page.evaluate(async (h) => (await fetch(`/products/${h}.js`)).json(), h);
  catalogue.push({
    handle: h, title: j.title, price: j.price / 100, available: j.available,
    tags: j.tags, type: j.type,
    featured: (j.featured_image || '').split('/').pop().split('?')[0],
    imageCount: (j.images || []).length,
    images: (j.images || []).map(u => u.split('/').pop().split('?')[0]),
    variants: (j.variants || []).map(v => ({ t: v.title, avail: v.available, price: v.price / 100 })),
    descLen: (j.description || '').replace(/<[^>]*>/g, '').trim().length,
    descText: (j.description || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 400),
  });
}
fs.writeFileSync('audit/evidence/catalogue.json', JSON.stringify(catalogue, null, 2));
console.log('--- CATALOGUE ---');
for (const c of catalogue) {
  console.log(`${c.handle.padEnd(30)} "${c.title}" £${c.price} avail=${c.available} imgs=${c.imageCount} desc=${c.descLen}ch variants=${c.variants.map(v=>v.t+(v.avail?'':'(SOLD)')).join('/')}`);
  console.log(`${' '.repeat(31)}featured=${c.featured}`);
}

// 2. ground-truth image bytes/dimensions straight from the CDN, at the exact URLs the page requests
async function probeUrls(pageUrl, label) {
  const p = await ctx.newPage();
  await p.goto(pageUrl, { waitUntil: 'load', timeout: 120000 });
  await p.waitForTimeout(3000);
  await p.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await p.waitForTimeout(2500);
  const list = await p.evaluate(() => [...document.querySelectorAll('img')].map(i => {
    const r = i.getBoundingClientRect();
    return { current: i.currentSrc || i.src, srcsetWidths: (i.srcset || '').split(',').map(s => s.trim().split(' ').pop()).filter(Boolean), sizes: i.sizes, css: [Math.round(r.width), Math.round(r.height)], natural: [i.naturalWidth, i.naturalHeight], cls: (typeof i.className === 'string' ? i.className : '') };
  }).filter(i => i.css[0] > 0));
  const results = [];
  for (const i of list) {
    const info = await p.evaluate(async (u) => {
      const r = await fetch(u, { cache: 'reload' });
      const b = await r.blob();
      const bmp = await createImageBitmap(b);
      return { bytes: b.size, type: b.type, w: bmp.width, h: bmp.height };
    }, i.current);
    results.push({ ...i, ...info, name: i.current.split('/').pop().split('?')[0], param: (i.current.split('?')[1] || '') });
  }
  await p.close();
  console.log(`\n--- IMAGE GROUND TRUTH: ${label} ---`);
  for (const r of results) {
    const needW = r.css[0] * 3;
    console.log(`${String(Math.round(r.bytes/1024)).padStart(5)}KB ${r.type.padEnd(10)} real=${r.w}x${r.h} css=${r.css[0]}x${r.css[1]} need@3x=${needW}px  ratio=${(r.w/needW).toFixed(2)}x  ${r.name.slice(0,50)}  [${r.param.slice(0,40)}]`);
    console.log(`         srcset widths: ${r.srcsetWidths.slice(0,12).join(',')}  sizes="${r.sizes}"`);
  }
  return { label, pageUrl, results };
}

const probes = [];
probes.push(await probeUrls(BASE + '/', 'homepage'));
probes.push(await probeUrls(BASE + '/products/3-clives-tee', 'PDP 3 CLIVES TEE'));
probes.push(await probeUrls(BASE + '/products/cb1-wash-jeans', 'PDP cb1-wash-jeans'));
probes.push(await probeUrls(BASE + '/products/cb2-wash-jeans', 'PDP cb2-wash-jeans'));
fs.writeFileSync('audit/evidence/images.json', JSON.stringify(probes, null, 2));

// 3. does the CDN serve webp when asked?
const fmt = await page.evaluate(async () => {
  const base = document.querySelector('img[src*="cdn"], img')?.src || '';
  const out = [];
  for (const q of ['width=800', 'width=800&format=webp', 'width=1400']) {
    const u = base.split('?')[0] + '?' + q;
    try { const r = await fetch(u, { cache: 'reload' }); const b = await r.blob(); out.push({ q, type: b.type, kb: Math.round(b.size / 1024) }); } catch (e) { out.push({ q, err: String(e) }); }
  }
  return { base: base.split('/').pop().split('?')[0], out };
});
console.log('\n--- CDN FORMAT NEGOTIATION ---'); console.log(JSON.stringify(fmt, null, 2));

await browser.close();
