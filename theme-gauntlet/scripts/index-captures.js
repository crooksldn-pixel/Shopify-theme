/* Build data/capture-index.json — a compact map of every capture session:
 * steps (file, label, url), checks, action outcomes, load perf, error counts.
 * This is what panel subagents receive to navigate the evidence.
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const CAP = path.join(ROOT, 'captures');

const index = { themes: {}, builtAt: new Date().toISOString() };

for (const theme of fs.readdirSync(CAP)) {
  const tDir = path.join(CAP, theme);
  if (!fs.statSync(tDir).isDirectory()) continue;
  index.themes[theme] = {};
  for (const journey of fs.readdirSync(tDir)) {
    const jDir = path.join(tDir, journey);
    if (!fs.statSync(jDir).isDirectory()) continue;
    index.themes[theme][journey] = {};
    for (const device of fs.readdirSync(jDir)) {
      const dDir = path.join(jDir, device);
      const metaPath = path.join(dDir, 'meta.jsonl');
      if (!fs.existsSync(metaPath)) continue;
      const lines = fs.readFileSync(metaPath, 'utf8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l));
      const steps = lines.filter((l) => l.type === 'step').map((l) => ({
        n: l.n, label: l.label, file: l.file, url: l.url, atMs: l.ms,
        consoleErrors: (l.consoleErrors || []).length,
        failedRequests: (l.failedRequests || []).length,
        note: l.note,
      }));
      const checks = {};
      for (const l of lines.filter((l) => l.type === 'check')) {
        const { t, ms, type, name, ...rest } = l;
        checks[l.name] = rest;
      }
      const actions = lines.filter((l) => l.type === 'action').map((l) => ({ note: l.note, ok: l.ok, how: l.how }));
      const loads = lines.filter((l) => l.type === 'load').map((l) => ({ url: l.url, status: l.status, err: l.err, loadMs: l.loadMs, perf: l.perf, cls: l.cls }));
      const asserts = lines.filter((l) => l.type === 'assert-theme');
      const summary = lines.find((l) => l.type === 'summary') || {};
      const consoleErrorTexts = [];
      for (const l of lines.filter((l) => l.type === 'step')) {
        for (const e of l.consoleErrors || []) if (!consoleErrorTexts.includes(e.text.slice(0, 120))) consoleErrorTexts.push(e.text.slice(0, 120));
      }
      index.themes[theme][journey][device] = {
        dir: path.relative(ROOT, dDir),
        steps, checks, actions, loads,
        themeAssertions: { total: asserts.length, failed: asserts.filter((a) => a.ok === false).length },
        poisoned: summary.poisoned || false,
        durationMs: summary.durationMs,
        uniqueConsoleErrors: consoleErrorTexts.slice(0, 12),
        journeyError: (lines.find((l) => l.type === 'journey-error') || {}).err,
      };
    }
  }
}

fs.writeFileSync(path.join(ROOT, 'data', 'capture-index.json'), JSON.stringify(index, null, 1));
const t = index.themes;
for (const th of Object.keys(t)) for (const j of Object.keys(t[th])) for (const d of Object.keys(t[th][j]))
  console.log(th, j, d, 'steps:' + t[th][j][d].steps.length, 'poisoned:' + t[th][j][d].poisoned, t[th][j][d].journeyError ? 'ERR:' + t[th][j][d].journeyError.slice(0, 60) : '');
