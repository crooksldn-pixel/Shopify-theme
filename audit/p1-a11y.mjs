import fs from 'fs';
import { launch, newContext, primePreview, BASE, MOBILE } from './lib.mjs';

const AXE = fs.readFileSync('node_modules/axe-core/axe.min.js', 'utf8');
const PAGES = [
  ['home', BASE + '/', 'Homepage'],
  ['pdpTee', BASE + '/products/3-clives-tee', 'PDP — 3 CLIVES TEE'],
  ['pdpDenim', BASE + '/products/cb2-wash-jeans', 'PDP — BLUE WASH OG JEANS'],
  ['cart', BASE + '/cart', 'Cart'],
  ['collection', BASE + '/collections/all', 'Collection'],
];

const out = { generated: new Date().toISOString(), contrast: {}, keyboard: {}, axe: {}, reducedMotion: {}, noJs: {}, zoom: {} };
const browser = await launch();

const CONTRAST_FN = `
(() => {
  const parse = (c) => {
    const m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
    const p = m[1].split(',').map(s => parseFloat(s));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const over = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); const hi = Math.max(l1, l2), lo = Math.min(l1, l2); return (hi + 0.05) / (lo + 0.05); };

  const effectiveBg = (el) => {
    let node = el, acc = null, overImage = false;
    while (node && node !== document.documentElement.parentNode) {
      const cs = getComputedStyle(node);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') overImage = true;
      const c = parse(cs.backgroundColor);
      if (c && c.a > 0) { acc = acc ? over(acc, c) : c; if (acc.a >= 0.999) return { color: acc, overImage }; }
      node = node.parentElement;
    }
    return { color: acc && acc.a > 0 ? acc : { r: 255, g: 255, b: 255, a: 1 }, overImage };
  };

  const results = [];
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length) continue;
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
    if (!hasText) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const fgRaw = parse(cs.color); if (!fgRaw) continue;
    const { color: bg, overImage } = effectiveBg(el);
    const fg = fgRaw.a < 1 ? over(fgRaw, bg) : fgRaw;
    const size = parseFloat(cs.fontSize);
    const weight = parseInt(cs.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const cr = ratio(fg, bg);
    const req = large ? 3 : 4.5;
    const key = cs.color + '|' + [bg.r, bg.g, bg.b].map(Math.round).join(',') + '|' + Math.round(size) + '|' + large;
    if (seen.has(key)) continue; seen.add(key);
    results.push({
      sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : ''),
      sample: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 42),
      fg: cs.color, bg: 'rgb(' + [bg.r, bg.g, bg.b].map(Math.round).join(', ') + ')',
      fontPx: +size.toFixed(1), weight, large, ratio: +cr.toFixed(2), required: req, pass: cr >= req, overImage,
      opacity: cs.opacity,
    });
  }
  return results.sort((a, b) => a.ratio - b.ratio);
})()
`;

// ---------- contrast + axe + keyboard ----------
{
  const ctx = await newContext(browser, MOBILE);
  await primePreview(ctx);
  const s = await ctx.newPage();
  await s.goto(BASE + '/products/3-clives-tee', { waitUntil: 'load', timeout: 120000 });
  await s.waitForTimeout(1200);
  await s.evaluate(async () => { const id = document.querySelector('[name="id"]')?.value; await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: Number(id), quantity: 1 }) }); });
  await s.close();

  for (const [key, url, label] of PAGES) {
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'load', timeout: 150000 });
    await page.waitForTimeout(2500);
    // close the first-visit popup and the cookie banner so we measure the page, not the overlays
    await page.evaluate(() => {
      document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } });
      document.querySelectorAll('.ctc-overlay, [class*="popup"], [class*="modal"]').forEach(e => { if (e.getBoundingClientRect().height > innerHeight * 0.5) e.remove(); });
      document.body.style.overflow = '';
    });
    await page.waitForTimeout(400);

    const contrast = await page.evaluate(CONTRAST_FN);
    const fails = contrast.filter(c => !c.pass);
    out.contrast[key] = { label, total: contrast.length, failing: fails.length, fails: fails.slice(0, 30), worstPassing: contrast.filter(c => c.pass).slice(0, 4) };
    console.log(`\n[contrast ${key}] ${fails.length}/${contrast.length} rendered text/bg pairs below threshold`);
    for (const f of fails.slice(0, 8)) console.log(`   ${String(f.ratio).padStart(5)}:1 (need ${f.required}) ${f.fontPx}px ${f.sel} — "${f.sample}"  ${f.fg} on ${f.bg}${f.overImage ? ' [over image]' : ''}`);

    // axe
    await page.addScriptTag({ content: AXE });
    const axeRes = await page.evaluate(async () => {
      const r = await window.axe.run(document, { resultTypes: ['violations'], runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'] } });
      return r.violations.map(v => ({ id: v.id, impact: v.impact, help: v.help, n: v.nodes.length, targets: v.nodes.slice(0, 4).map(n => n.target.join(' ')), summary: (v.nodes[0]?.failureSummary || '').replace(/\s+/g, ' ').slice(0, 160) }));
    });
    out.axe[key] = axeRes;
    console.log(`[axe ${key}] ${axeRes.length} violation types, ${axeRes.reduce((a, v) => a + v.n, 0)} nodes`);
    for (const v of axeRes) console.log(`   ${String(v.impact).padEnd(8)} ${v.id} x${v.n} — ${v.help}`);

    // keyboard traversal
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.keyboard.press('Escape');
    const stops = [];
    let trapped = false;
    const MAX = 65;
    for (let i = 0; i < MAX; i++) {
      await page.keyboard.press('Tab');
      const st = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return { sel: '(body — focus lost)', visible: false, text: '' };
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        const outline = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0;
        const ring = cs.boxShadow && cs.boxShadow !== 'none';
        const bordered = parseFloat(cs.borderWidth) > 0;
        return {
          sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''),
          text: (el.innerText || el.getAttribute('aria-label') || el.value || '').replace(/\s+/g, ' ').trim().slice(0, 34),
          focusIndicator: outline ? 'outline ' + cs.outlineWidth + ' ' + cs.outlineColor : ring ? 'box-shadow' : bordered ? 'border only' : 'NONE',
          inViewport: r.top >= -5 && r.bottom <= innerHeight + 5 && r.width > 0,
          offscreen: r.width === 0 || r.height === 0 || r.bottom < 0 || r.top > innerHeight,
          hidden: cs.visibility === 'hidden' || cs.display === 'none',
        };
      });
      stops.push(st);
      if (stops.length > 6) {
        const last6 = stops.slice(-6).map(s => s.sel);
        if (new Set(last6).size === 1) { trapped = true; break; }
      }
    }
    const noIndicator = stops.filter(s => s.focusIndicator === 'NONE');
    const hiddenFocus = stops.filter(s => s.hidden || (s.offscreen && !s.sel.includes('skip')));
    out.keyboard[key] = { label, stops: stops.length, trapped, order: stops.map(s => `${s.sel} [${s.focusIndicator}]${s.text ? ' "' + s.text + '"' : ''}`), noIndicatorCount: noIndicator.length, noIndicator: [...new Set(noIndicator.map(s => s.sel))].slice(0, 15), focusOnHidden: [...new Set(hiddenFocus.map(s => s.sel))].slice(0, 10) };
    console.log(`[keyboard ${key}] ${stops.length} stops, trap=${trapped}, ${noIndicator.length} stops with NO visible focus indicator, ${hiddenFocus.length} on hidden/offscreen elements`);
    await page.close();
  }
  await ctx.close();
}

// ---------- reduced motion ----------
{
  const ctx = await newContext(browser, MOBILE, { reducedMotion: 'reduce' });
  await primePreview(ctx);
  const page = await ctx.newPage();
  await page.addInitScript(`window.__frames=0; const _r=requestAnimationFrame; window.requestAnimationFrame=(cb)=>_r(t=>{window.__frames++;return cb(t)});`);
  await page.goto(BASE + '/', { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(3000);
  await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } }); document.querySelectorAll('.ctc-overlay').forEach(e => e.remove()); document.body.style.overflow = ''; });
  await page.evaluate(() => document.querySelector('canvas')?.scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(1200);
  const a = await page.evaluate(() => window.__frames); await page.waitForTimeout(3000);
  const b2 = await page.evaluate(() => window.__frames);
  const anim = await page.evaluate(() => {
    const running = [];
    for (const el of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(el);
      if (cs.animationName !== 'none' && cs.animationPlayState === 'running' && parseFloat(cs.animationDuration) > 0) running.push({ sel: el.tagName.toLowerCase() + '.' + (typeof el.className === 'string' ? el.className.split(' ')[0] : ''), name: cs.animationName, dur: cs.animationDuration, iter: cs.animationIterationCount });
    }
    const seen = new Set(); return running.filter(r => { const k = r.sel + r.name; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 20);
  });
  out.reducedMotion = { prefersReducedMotion: true, boardFramesIn3s: b2 - a, boardFps: +(((b2 - a) / 3000) * 1000).toFixed(1), stillRunningCssAnimations: anim, matches: await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches) };
  console.log(`\n[reduced-motion] media matches=${out.reducedMotion.matches}, canvas board fps=${out.reducedMotion.boardFps}, CSS animations still running: ${anim.length}`);
  for (const a2 of anim.slice(0, 8)) console.log(`   ${a2.sel} ${a2.name} ${a2.dur} x${a2.iter}`);
  await page.screenshot({ path: 'audit/screens/a11y-reduced-motion-home.png', fullPage: false });
  await ctx.close();
}

// ---------- 200% zoom ----------
{
  const ctx = await newContext(browser, { ...MOBILE, viewport: { width: 195, height: 422 }, deviceScaleFactor: 6 });
  await primePreview(ctx);
  const page = await ctx.newPage();
  await page.goto(BASE + '/products/cb2-wash-jeans', { waitUntil: 'load', timeout: 150000 });
  await page.waitForTimeout(2500);
  await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch { d.remove(); } }); document.querySelectorAll('.ctc-overlay').forEach(e => e.remove()); document.body.style.overflow = ''; });
  out.zoom = await page.evaluate(() => ({
    note: '390px viewport at 200% browser zoom == 195 CSS px of layout width',
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
    horizontalScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    clipped: [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > document.documentElement.clientWidth + 2; }).slice(0, 10).map(e => e.tagName.toLowerCase() + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : '')),
    atcReachable: !!document.querySelector('button[name="add"], .crk-btn'),
  }));
  console.log(`\n[200% zoom] horizontal scroll=${out.zoom.horizontalScroll} (scrollW ${out.zoom.scrollWidth} vs ${out.zoom.clientWidth})`);
  await page.screenshot({ path: 'audit/screens/a11y-zoom200-pdp.png', fullPage: false });
  await ctx.close();
}

// ---------- JavaScript disabled ----------
{
  const ctx = await newContext(browser, MOBILE, { javaScriptEnabled: false });
  for (const [key, url, label] of [['home', BASE + '/', 'Homepage'], ['pdpDenim', BASE + '/products/cb2-wash-jeans', 'PDP']]) {
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'load', timeout: 150000 });
    await page.waitForTimeout(2000);
    const html = await page.content();
    const text = await page.locator('body').innerText().catch(() => '');
    const shot = `audit/screens/a11y-nojs-${key}.png`;
    await page.screenshot({ path: shot, fullPage: false });
    const has = (re) => re.test(html);
    out.noJs[key] = {
      label, screenshot: shot,
      visibleTextChars: text.replace(/\s+/g, ' ').trim().length,
      visibleTextSample: text.replace(/\s+/g, ' ').trim().slice(0, 400),
      productLinks: (html.match(/href="[^"]*\/products\//g) || []).length,
      hasAddToCartForm: has(/<form[^>]+\/cart\/add/i),
      hasPriceInHtml: /£\s?\d/.test(text),
      hasNoscriptFallback: has(/<noscript/i),
      imagesInHtml: (html.match(/<img/g) || []).length,
    };
    console.log(`\n[no-JS ${key}] text=${out.noJs[key].visibleTextChars} chars, productLinks=${out.noJs[key].productLinks}, cart form=${out.noJs[key].hasAddToCartForm}, price visible=${out.noJs[key].hasPriceInHtml}, imgs=${out.noJs[key].imagesInHtml}`);
    console.log(`   sample: ${out.noJs[key].visibleTextSample.slice(0, 220)}`);
    await page.close();
  }
  await ctx.close();
}

fs.writeFileSync('audit/evidence/a11y.json', JSON.stringify(out, null, 2));
console.log('\nwrote audit/evidence/a11y.json');
await browser.close();
