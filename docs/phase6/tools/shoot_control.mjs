// Render the twelve CROOKS Control states and write a PNG of each.
//
// The app itself is SwiftUI and cannot be built on this machine, so this is not a screenshot of
// CROOKS Control. It is a screenshot of the same DECISIONS and the same palette, at the window
// size the app opens at, which is the most that can honestly be looked at from here — and a
// great deal more than the nothing that had been looked at before.
//
//   node docs/phase6/tools/shoot_control.mjs [outdir]
import { createRequire } from "module";
const require_ = createRequire(import.meta.url);
const { chromium } = require_("/opt/node22/lib/node_modules/playwright");
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";
import { readFileSync, mkdirSync } from "fs";
import { createServer } from "http";

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(process.argv[2] || resolve(here, "../evidence/control"));
mkdirSync(out, { recursive: true });

const states = JSON.parse(readFileSync(resolve(here, "control_states.json"), "utf8")).states;

// Served over HTTP rather than opened as a file: the harness fetches its states as JSON, and a
// file:// page is not allowed to.
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json" };
const server = createServer((req, res) => {
  const name = decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/^\/+/, "") || "control_harness.html";
  try {
    const body = readFileSync(resolve(here, name));
    res.writeHead(200, { "content-type": TYPES[name.slice(name.lastIndexOf("."))] || "text/plain" });
    res.end(body);
  } catch { res.writeHead(404); res.end("no"); }
});
await new Promise(done => server.listen(0, "127.0.0.1", done));
const origin = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 520, height: 900 }, deviceScaleFactor: 2 });

page.on("pageerror", e => { console.error("PAGE ERROR:", e.message); process.exitCode = 1; });

for (const s of states) {
  await page.goto(`${origin}/control_harness.html?state=${s.key}`);
  await page.waitForSelector("body[data-ready] .win", { timeout: 10000 });
  const win = await page.$(".win");
  await win.screenshot({ path: resolve(out, `${s.key}.png`) });
  console.log("wrote", `${s.key}.png`);
}

// And one contact sheet, because the twelve have to be judged against each other.
await page.setViewportSize({ width: 1420, height: 2100 });
await page.goto(`${origin}/control_harness.html`);
await page.waitForSelector("body[data-ready] .win");
await page.screenshot({ path: resolve(out, "_all.png"), fullPage: true });
console.log("wrote _all.png");

await browser.close();
server.close();
