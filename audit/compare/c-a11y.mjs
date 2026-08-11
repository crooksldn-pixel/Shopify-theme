// Accessibility: axe-core, keyboard first stops, 200% zoom reflow. Usage: node audit/compare/c-a11y.mjs <tag>
import { launch, newContext, MOBILE, loadSite, saveEvidence } from './clib.mjs';
import fs from 'fs';

const tag = process.argv[2];
const site = loadSite(tag);
const axe = fs.readFileSync('node_modules/axe-core/axe.min.js', 'utf8');
const browser = await launch();
const out = { tag, pages: {} };

async function audit(label, url) {
  if (!url) return;
  const ctx = await newContext(browser, MOBILE);
  const p = await ctx.newPage();
  try {
    await p.goto(url, { waitUntil: 'load', timeout: 120000 });
    await p.waitForTimeout(3000);
    await p.evaluate(axe);
    const axeRes = await p.evaluate(async () => {
      const r = await window.axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] });
      return r.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.length }));
    });
    // keyboard: first 8 tab stops
    const stops = [];
    for (let i = 0; i < 8; i++) {
      await p.keyboard.press('Tab');
      stops.push(await p.evaluate(() => {
        const e = document.activeElement;
        if (!e || e === document.body) return null;
        const cs = getComputedStyle(e);
        return { tag: e.tagName, text: (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 40),
          focusVisible: cs.outlineStyle !== 'none' || cs.boxShadow !== 'none' };
      }));
    }
    // 200% zoom equivalent: 195px layout viewport
    const zctx = await newContext(browser, { ...MOBILE, viewport: { width: 195, height: 422 } });
    const zp = await zctx.newPage();
    await zp.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });
    await zp.waitForTimeout(2500);
    const zoom = await zp.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
    await zctx.close();
    out.pages[label] = { url, axeViolations: axeRes, tabStops: stops.filter(Boolean), zoom: { ...zoom, horizontalScroll: zoom.scrollWidth > zoom.clientWidth } };
  } catch (e) { out.pages[label] = { url, error: String(e).slice(0, 180) }; }
  await ctx.close();
}
await audit('home', site.homeUrl);
await audit('pdp', site.pdpUrl);
saveEvidence(tag, 'a11y', out);
for (const [k, v] of Object.entries(out.pages)) {
  if (v.error) { console.log(k, 'ERROR', v.error); continue; }
  console.log(`${k}: ${v.axeViolations.length} axe violation types (${v.axeViolations.filter(x => x.impact === 'critical' || x.impact === 'serious').length} serious+) | zoom hscroll: ${v.zoom.horizontalScroll}`);
}
await browser.close();
