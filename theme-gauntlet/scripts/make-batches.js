/* Slice personas.json into 10 batch files with the capture sessions each persona needs. */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const { personas } = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'personas.json'), 'utf8'));
const index = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'capture-index.json'), 'utf8'));

fs.mkdirSync(path.join(ROOT, 'data', 'panel'), { recursive: true });

// journey fallback: if a persona's journey+device combo is missing, note it
function sessionsFor(p) {
  const out = [];
  for (const theme of p.order) {
    const j = index.themes[theme] && index.themes[theme][p.journey];
    const dev = j && (j[p.device] || j[Object.keys(j)[0]]);
    if (dev) out.push({ theme, journey: p.journey, device: p.device, dir: dev.dir, steps: dev.steps, checks: dev.checks, actions: dev.actions, loads: dev.loads.map(l => ({url: l.url, loadMs: l.loadMs, cls: l.cls})), uniqueConsoleErrors: dev.uniqueConsoleErrors });
    for (const edge of p.edgeEvidence || []) {
      const e = index.themes[theme] && index.themes[theme][edge];
      const ed = e && (e[p.device] || e[Object.keys(e)[0]]);
      if (ed) out.push({ theme, journey: edge, device: Object.keys(e)[0], dir: ed.dir, steps: ed.steps, checks: ed.checks });
    }
  }
  return out;
}

for (let b = 1; b <= 10; b++) {
  const slice = personas.slice((b - 1) * 10, b * 10);
  const batch = {
    batch: b,
    personas: slice.map((p) => ({ ...p, sessions: sessionsFor(p) })),
  };
  fs.writeFileSync(path.join(ROOT, 'data', 'panel', `batch-${b}.json`), JSON.stringify(batch, null, 1));
  console.log('batch', b, slice.map((p) => p.id + ':' + p.intent + ':' + p.device).join(' '));
}
