/* Build report/contact-sheet.html — side-by-side OLD vs NEW screenshots per journey/device/step. */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const index = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'capture-index.json'), 'utf8'));

const JTITLES = {
  j1: 'J1 Buy-now (charcoal crewneck)', j2: 'J2 Search-led buy (jeans)', j3: 'J3 Research/compare (ad landing)',
  j4: 'J4 Browse/graze (catalogue)', j5: 'J5 Gift hunt', j6: 'J6 Lookup/support', j7: 'J7 Returning customer (jorts)',
  edge: 'Edge sweep (mobile)', 'edge-slow4g': 'Edge: Slow-4G', 'edge-zoom': 'Edge: 200% zoom (desktop)',
};

let html = `<!doctype html><html><head><meta charset="utf-8"><title>Theme gauntlet — contact sheet</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#141416;color:#eee}
h1{padding:16px 24px;margin:0;background:#1d1d21;font-size:20px}
h2{padding:12px 24px;margin:24px 0 0;background:#1d1d21;font-size:16px;position:sticky;top:0;z-index:2}
h3{padding:6px 24px;margin:8px 0 0;color:#aaa;font-size:13px;font-weight:600}
.row{display:flex;gap:12px;padding:12px 24px;overflow-x:auto}
.cell{flex:0 0 auto;width:300px}
.cell img{width:100%;border:1px solid #333;border-radius:4px;display:block}
.cell .cap{font-size:11px;color:#bbb;padding:4px 2px;line-height:1.4}
.old .cap b{color:#7ab8ff}.new .cap b{color:#c39bff}
.meta{font-size:11px;color:#888;padding:0 24px 8px;line-height:1.5}
.pair{display:flex;gap:8px}
</style></head><body>
<h1>CROOKSLDN theme gauntlet — contact sheet (OLD = live theme 202044309847, NEW = staging 202053779799)</h1>
<p class="meta">Full-page captures, preview bar hidden, theme id asserted per load. Cookie-consent modal visible in first NEW screenshots is what a real first-time visitor sees.</p>`;

for (const j of ['j1', 'j2', 'j3', 'j4', 'j5', 'j6', 'j7', 'edge', 'edge-slow4g', 'edge-zoom']) {
  const anyTheme = index.themes.old[j] || index.themes.new[j];
  if (!anyTheme) continue;
  html += `<h2>${JTITLES[j] || j}</h2>`;
  for (const device of Object.keys(anyTheme)) {
    const oldS = (index.themes.old[j] || {})[device];
    const newS = (index.themes.new[j] || {})[device];
    if (!oldS && !newS) continue;
    html += `<h3>${device}</h3><div class="row">`;
    const maxSteps = Math.max(oldS ? oldS.steps.length : 0, newS ? newS.steps.length : 0);
    for (let i = 0; i < maxSteps; i++) {
      const o = oldS && oldS.steps[i];
      const n = newS && newS.steps[i];
      html += `<div class="cell"><div class="pair">`;
      html += o ? `<div class="old" style="flex:1"><img loading="lazy" src="../${o.file}"><div class="cap"><b>OLD</b> ${o.n}. ${o.label}</div></div>` : '<div style="flex:1"></div>';
      html += n ? `<div class="new" style="flex:1"><img loading="lazy" src="../${n.file}"><div class="cap"><b>NEW</b> ${n.n}. ${n.label}</div></div>` : '<div style="flex:1"></div>';
      html += `</div></div>`;
    }
    html += `</div>`;
  }
}
html += '</body></html>';
fs.writeFileSync(path.join(ROOT, 'report', 'contact-sheet.html'), html);
console.log('contact sheet written');
