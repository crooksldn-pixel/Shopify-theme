// Perf: home + PDP, mobile throttled; PDP desktop unthrottled. Usage: node audit/compare/c-perf.mjs <tag>
import { launch, newContext, applyThrottle, MOBILE, DESKTOP, VITALS_INIT, collectVitals, trackTransfer, loadSite, saveEvidence } from './clib.mjs';

const tag = process.argv[2];
const site = loadSite(tag);
const browser = await launch();
const out = { tag, generatedAt: new Date().toISOString(), pages: {} };

async function measure(label, url, device, throttled) {
  if (!url) return;
  const ctx = await newContext(browser, device);
  const p = await ctx.newPage();
  await p.addInitScript(VITALS_INIT);
  const tr = trackTransfer(p);
  if (throttled) await applyThrottle(p);
  const t0 = Date.now();
  try {
    await p.goto(url, { waitUntil: 'load', timeout: 180000 });
    await p.waitForTimeout(6000);
    // one representative interaction for INP: tap body
    await p.mouse.click(20, 200).catch(() => {});
    await p.waitForTimeout(1500);
    out.pages[label] = { url, device: device === MOBILE ? 'mobile-390' : 'desktop-1440', throttled,
      wallMs: Date.now() - t0, vitals: await collectVitals(p), transfer: tr.summary() };
  } catch (e) {
    out.pages[label] = { url, error: String(e).slice(0, 180) };
  }
  await ctx.close();
}

await measure('home', site.homeUrl, MOBILE, true);
await measure('pdp', site.pdpUrl, MOBILE, true);
await measure('pdpDesktop', site.pdpUrl, DESKTOP, false);
saveEvidence(tag, 'perf', out);
for (const [k, v] of Object.entries(out.pages)) {
  if (v.error) { console.log(k, 'ERROR', v.error); continue; }
  console.log(`${k}: LCP ${v.vitals.lcp} CLS ${v.vitals.cls.toFixed ? v.vitals.cls.toFixed(4) : v.vitals.cls} INP ${v.vitals.inp} | ${v.transfer.totalKB}KB / ${v.transfer.requests} req`);
}
await browser.close();
