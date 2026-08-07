import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE, attachNetworkAccounting } from './lib.mjs';

const browser = await launch();
const ctx = await newContext(browser, MOBILE);
await primePreview(ctx);

// Capture what the <img> elements ACTUALLY receive: headers + magic bytes, via CDP.
async function capture(url, label) {
  const page = await ctx.newPage();
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  const meta = new Map();
  const ids = [];
  cdp.on('Network.responseReceived', e => {
    if (!/^image\//.test(e.response.mimeType) && !/\.(png|webp|jpe?g)/i.test(e.response.url)) return;
    meta.set(e.requestId, { url: e.response.url, mime: e.response.mimeType, headers: e.response.headers, status: e.response.status });
    ids.push(e.requestId);
  });
  cdp.on('Network.loadingFinished', e => { const m = meta.get(e.requestId); if (m) m.encoded = e.encodedDataLength; });

  await page.goto(url, { waitUntil: 'load', timeout: 120000 });
  await page.waitForTimeout(2500);
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(3000);

  const rows = [];
  for (const id of ids) {
    const m = meta.get(id);
    if (!m || !m.encoded) continue;
    let magic = '?';
    try {
      const b = await cdp.send('Network.getResponseBody', { requestId: id });
      const buf = Buffer.from(b.body, b.base64Encoded ? 'base64' : 'utf8');
      const sig = buf.slice(0, 16);
      if (sig.slice(0, 8).toString('hex') === '89504e470d0a1a0a') magic = 'PNG';
      else if (sig.slice(0, 4).toString() === 'RIFF' && sig.slice(8, 12).toString() === 'WEBP') magic = 'WEBP';
      else if (sig[0] === 0xff && sig[1] === 0xd8) magic = 'JPEG';
      else if (sig.slice(4, 8).toString() === 'ftyp') magic = 'AVIF/HEIF';
      else if (sig.slice(0, 4).toString() === '<svg' || buf.slice(0, 200).toString().includes('<svg')) magic = 'SVG';
      else magic = sig.toString('hex').slice(0, 12);
    } catch (e) { magic = 'body-unavailable'; }
    rows.push({
      name: m.url.split('/').pop().split('?')[0], param: (m.url.split('?')[1] || '').slice(0, 40),
      contentType: m.headers['content-type'] || m.mime, magic, encodedKB: Math.round(m.encoded / 1024),
      vary: m.headers['vary'] || '', cdnCache: m.headers['x-cache'] || m.headers['cf-cache-status'] || '',
    });
  }
  await page.close();
  console.log(`\n=== ${label} — what the <img> tags actually received ===`);
  console.log('  bytes  content-type      magic   file');
  for (const r of rows) console.log(`  ${String(r.encodedKB).padStart(5)}KB ${String(r.contentType).padEnd(16)} ${r.magic.padEnd(7)} ${r.name.slice(0, 55)}  [${r.param}]`);
  return { label, url, rows };
}

const res = [];
res.push(await capture(BASE + '/', 'HOMEPAGE'));
res.push(await capture(BASE + '/products/3-clives-tee', 'PDP 3 CLIVES TEE'));
res.push(await capture(BASE + '/products/cb2-wash-jeans', 'PDP BLUE WASH OG JEANS (cb2-wash-jeans)'));
fs.writeFileSync('audit/evidence/image-formats.json', JSON.stringify(res, null, 2));

// Direct A/B: same master, requested with an image Accept header vs */*
const p = await ctx.newPage();
await p.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 120000 });
const ab = await p.evaluate(async () => {
  const targets = [
    { label: 'PNG-named master', file: null }, { label: 'WEBP-named master', file: null },
  ];
  const imgs = [...document.querySelectorAll('img')].map(i => (i.currentSrc || i.src).split('?')[0]);
  const png = imgs.find(u => /\.png$/i.test(u) && !/IMG_3682/.test(u));
  const webp = imgs.find(u => /\.webp$/i.test(u));
  const out = [];
  for (const [label, base] of [['png-named', png], ['webp-named', webp]]) {
    if (!base) continue;
    for (const [mode, headers] of [['accept:image/webp', { Accept: 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8' }], ['accept:*/*', { Accept: '*/*' }]]) {
      const u = base + '?width=1400';
      const r = await fetch(u, { headers, cache: 'reload' });
      const b = await r.blob();
      const head = new Uint8Array(await b.slice(0, 16).arrayBuffer());
      const hex = [...head].map(x => x.toString(16).padStart(2, '0')).join('');
      out.push({ label, mode, file: base.split('/').pop(), ct: r.headers.get('content-type'), kb: Math.round(b.size / 1024), magic: hex.startsWith('89504e47') ? 'PNG' : (hex.slice(0, 8) === '52494646' ? 'WEBP' : hex.slice(0, 12)) });
    }
  }
  return out;
});
console.log('\n=== A/B: same master URL, different Accept header ===');
for (const r of ab) console.log(`  ${r.label.padEnd(11)} ${r.mode.padEnd(18)} -> ${String(r.ct).padEnd(12)} ${r.magic.padEnd(6)} ${String(r.kb).padStart(5)}KB  ${r.file}`);
fs.writeFileSync('audit/evidence/image-ab.json', JSON.stringify(ab, null, 2));
await browser.close();
