#!/usr/bin/env node
// Gauntlet browser harness. One persistent Chromium per buyer id.
// Usage:
//   node browse.mjs start <id> mobile|desktop
//   node browse.mjs go <id> <url>
//   node browse.mjs click <id> <n>          (element index from last observation)
//   node browse.mjs clicktext <id> <text>   (visible text, first match)
//   node browse.mjs type <id> <n> <text>    (fill input by index)
//   node browse.mjs press <id> <key>        (e.g. Enter, Escape)
//   node browse.mjs scroll <id> down|up
//   node browse.mjs back <id>
//   node browse.mjs read <id>               (observe without acting)
//   node browse.mjs shot <id> <name>        (viewport screenshot -> shots/<name>.png)
//   node browse.mjs stop <id>
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PROFILES = path.join(ROOT, 'profiles');
const SHOTS = path.join(ROOT, 'shots');
const SESSIONS = path.join(ROOT, 'sessions');
fs.mkdirSync(PROFILES, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });
fs.mkdirSync(SESSIONS, { recursive: true });

const [, , cmd, id, ...args] = process.argv;
if (!cmd || !id) { console.error('usage: browse.mjs <cmd> <id> [...]'); process.exit(2); }
let hash = 0;
for (const ch of String(id)) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
const PORT = 9300 + (hash % 397);
const metaFile = path.join(PROFILES, `${id}.json`);
const elsFile = path.join(PROFILES, `${id}-els.json`);
const navLog = path.join(SESSIONS, `${id}-nav.log`);

function logNav(url) {
  try {
    const host = new URL(url).host;
    fs.appendFileSync(navLog, `${new Date().toISOString()}\t${host}\t${url}\n`);
  } catch {}
}

async function holdBrowser(profile) {
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  const mobile = profile === 'mobile';
  const ctx = await chromium.launchPersistentContext(path.join(PROFILES, `${id}-data`), {
    headless: true,
    executablePath: '/opt/pw-browsers/chromium',
    proxy: proxy ? { server: proxy } : undefined,
    ignoreHTTPSErrors: true,
    viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 900 },
    deviceScaleFactor: mobile ? 2 : 1,
    isMobile: mobile,
    hasTouch: mobile,
    userAgent: mobile
      ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
      : undefined,
    args: [`--remote-debugging-port=${PORT}`, '--remote-debugging-address=127.0.0.1', '--ssl-version-max=tls1.2'],
  });
  fs.writeFileSync(metaFile, JSON.stringify({ port: PORT, profile, pid: process.pid }));
  // keep process alive holding the browser
  setInterval(() => {}, 1 << 30);
  ctx.on('close', () => process.exit(0));
}

if (cmd === '__hold') { holdBrowser(args[0] || 'mobile'); }
else if (cmd === 'start') {
  const profile = args[0] === 'desktop' ? 'desktop' : 'mobile';
  if (fs.existsSync(metaFile)) { try { fs.rmSync(metaFile); } catch {} }
  const child = spawn(process.execPath, [fileURLToPath(import.meta.url), '__hold', id, profile], {
    detached: true, stdio: 'ignore', env: process.env,
  });
  child.unref();
  const deadline = Date.now() + 20000;
  (async () => {
    while (Date.now() < deadline) {
      if (fs.existsSync(metaFile)) {
        // wait until CDP answers
        try {
          const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
          await b.close();
          console.log(`OK started ${id} (${profile}) on port ${PORT}`);
          process.exit(0);
        } catch {}
      }
      await new Promise(r => setTimeout(r, 400));
    }
    console.error('FAIL: browser did not start in 20s');
    process.exit(1);
  })();
} else {
  run().catch(e => { console.error('ERROR: ' + (e && e.message ? e.message.split('\n')[0] : e)); process.exit(1); });
}

async function activePage(browser) {
  const ctx = browser.contexts()[0];
  if (!ctx) throw new Error('no context');
  const pages = ctx.pages().filter(p => !p.isClosed());
  if (!pages.length) return await ctx.newPage();
  return pages[pages.length - 1];
}

async function settle(page, ms = 900) {
  try { await page.waitForLoadState('domcontentloaded', { timeout: 15000 }); } catch {}
  await page.waitForTimeout(ms + Math.floor(Math.random() * 500));
}

async function observe(page) {
  const url = page.url();
  logNav(url);
  let title = '';
  try { title = await page.title(); } catch {}
  const data = await page.evaluate(() => {
    function visible(el) {
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return false;
      const s = getComputedStyle(el);
      if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return false;
      return true;
    }
    function cssPath(el) {
      const parts = [];
      while (el && el.nodeType === 1 && parts.length < 12) {
        let sel = el.tagName.toLowerCase();
        if (el.id) { parts.unshift(`#${CSS.escape(el.id)}`); break; }
        const parent = el.parentElement;
        if (parent) {
          const sibs = Array.from(parent.children).filter(c => c.tagName === el.tagName);
          if (sibs.length > 1) sel += `:nth-of-type(${sibs.indexOf(el) + 1})`;
        }
        parts.unshift(sel);
        el = parent;
      }
      return parts.join(' > ');
    }
    const vw = window.innerWidth, vh = window.innerHeight;
    // overlay detection
    let overlay = null;
    for (const el of document.body.querySelectorAll('*')) {
      const s = getComputedStyle(el);
      if ((s.position === 'fixed' || s.position === 'sticky') && visible(el)) {
        const r = el.getBoundingClientRect();
        if (r.width * r.height > vw * vh * 0.35 && (parseInt(s.zIndex) || 0) >= 10) {
          const t = (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 500);
          if (t.length > 20) { overlay = t; break; }
        }
      }
    }
    // interactive elements
    const els = [];
    const nodes = document.querySelectorAll('a,button,input,textarea,select,[role="button"],[role="link"],[role="tab"],summary,div[class*="hamburger"],div[class*="menu-toggle"],div[class*="nav-toggle"],label[for]');
    for (const el of nodes) {
      if (!visible(el)) continue;
      if (el.tagName === 'DIV' && el.parentElement && el.parentElement.closest('div[class*="hamburger"],div[class*="menu-toggle"],div[class*="nav-toggle"]')) continue;
      const r = el.getBoundingClientRect();
      const inView = r.bottom > 0 && r.top < vh;
      let text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 90);
      const tag = el.tagName.toLowerCase();
      if (tag === 'input') {
        const ty = el.type || 'text';
        if (['hidden', 'submit', 'button'].includes(ty) && !el.value) continue;
        text = text || `[${ty} input]`;
      }
      if (!text && tag === 'a') text = (el.getAttribute('href') || '').slice(0, 60);
      if (!text) {
        const cls = (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className) || '';
        const hint = String(cls).toLowerCase().match(/menu|nav|burger|hamburger|toggle|search|cart|close|drawer|expand/);
        const kids = el.querySelector('svg,i,img,span');
        if (hint) text = `[icon:${hint[0]}]`;
        else if (kids) {
          const kcls = String((kids.className && kids.className.baseVal !== undefined ? kids.className.baseVal : kids.className) || '') + ' ' + (kids.getAttribute('class') || '');
          const khint = kcls.toLowerCase().match(/menu|nav|burger|hamburger|toggle|search|cart|close|drawer|expand|bars|times/);
          if (khint) text = `[icon:${khint[0]}]`;
        }
      }
      if (!text) continue;
      els.push({
        tag, text,
        href: tag === 'a' ? (el.getAttribute('href') || '').slice(0, 120) : undefined,
        itype: tag === 'input' ? (el.type || 'text') : undefined,
        inView,
        path: cssPath(el),
      });
      if (els.length >= 120) break;
    }
    // visible text (in-viewport blocks)
    const seen = new Set(); const lines = [];
    const blocks = document.querySelectorAll('h1,h2,h3,h4,h5,p,li,figcaption,blockquote,label,td,th,dt,dd,span,div');
    for (const el of blocks) {
      const r = el.getBoundingClientRect();
      if (r.bottom < -vh * 0.2 || r.top > vh * 1.2) continue;
      if (!visible(el)) continue;
      if (el.children.length > 2 && !/^(P|LI|H\d|LABEL|TD|TH|FIGCAPTION|BLOCKQUOTE|DT|DD)$/.test(el.tagName)) continue;
      const t = (el.innerText || '').trim().replace(/\s+/g, ' ');
      if (t.length < 3 || t.length > 400) continue;
      if (seen.has(t)) continue;
      // skip if a parent already contributed this text
      let dup = false;
      for (const s of seen) { if (s.includes(t)) { dup = true; break; } }
      if (dup) continue;
      seen.add(t); lines.push(t);
      if (lines.join('\n').length > 3200) break;
    }
    return {
      overlay, els, text: lines.join('\n'),
      scrollY: Math.round(window.scrollY),
      scrollMax: Math.round(Math.max(0, (document.documentElement.scrollHeight || 0) - vh)),
    };
  }).catch(e => ({ overlay: null, els: [], text: '(page not readable: ' + e.message.split('\n')[0] + ')', scrollY: 0, scrollMax: 0 }));

  fs.writeFileSync(elsFile, JSON.stringify(data.els));
  const out = [];
  out.push(`URL: ${url}`);
  out.push(`TITLE: ${title}`);
  out.push(`SCROLL: ${data.scrollY}/${data.scrollMax}px`);
  if (data.overlay) out.push(`!! OVERLAY/POPUP ON SCREEN: ${data.overlay}`);
  out.push(`--- VISIBLE TEXT (current view) ---`);
  out.push(data.text || '(none)');
  out.push(`--- CLICKABLE [index] (v = in current view) ---`);
  data.els.forEach((e, i) => {
    const mark = e.inView ? 'v' : ' ';
    const extra = e.itype ? ` <${e.itype}>` : '';
    out.push(`[${i}]${mark} ${e.tag}${extra}: ${e.text}`);
  });
  console.log(out.join('\n'));
}

async function run() {
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  try {
    const page = await activePage(browser);
    page.setDefaultTimeout(12000);
    switch (cmd) {
      case 'go': {
        await page.goto(args[0], { waitUntil: 'domcontentloaded', timeout: 45000 });
        await settle(page, 1400);
        await observe(page);
        break;
      }
      case 'click': {
        const els = JSON.parse(fs.readFileSync(elsFile, 'utf8'));
        const el = els[parseInt(args[0], 10)];
        if (!el) throw new Error('no such element index');
        try {
          await page.click(el.path, { timeout: 8000 });
        } catch {
          await page.getByText(el.text, { exact: false }).first().click({ timeout: 8000 });
        }
        await settle(page);
        const p2 = await activePage(browser);
        await observe(p2);
        break;
      }
      case 'clicktext': {
        const t = args.join(' ');
        const loc = page.getByText(t, { exact: false }).first();
        await loc.click({ timeout: 10000 });
        await settle(page);
        const p2 = await activePage(browser);
        await observe(p2);
        break;
      }
      case 'type': {
        const els = JSON.parse(fs.readFileSync(elsFile, 'utf8'));
        const el = els[parseInt(args[0], 10)];
        if (!el) throw new Error('no such element index');
        await page.fill(el.path, args.slice(1).join(' '));
        await page.waitForTimeout(300);
        await observe(page);
        break;
      }
      case 'press': {
        await page.keyboard.press(args[0]);
        await settle(page);
        const p2 = await activePage(browser);
        await observe(p2);
        break;
      }
      case 'scroll': {
        const dir = args[0] === 'up' ? -1 : 1;
        await page.evaluate(d => window.scrollBy({ top: d * window.innerHeight * 0.85, behavior: 'instant' }), dir);
        await page.waitForTimeout(500);
        await observe(page);
        break;
      }
      case 'back': {
        await page.goBack({ waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
        await settle(page);
        await observe(page);
        break;
      }
      case 'read': {
        await observe(page);
        break;
      }
      case 'js': {
        const r = await page.evaluate(args.join(' '));
        console.log(typeof r === 'string' ? r : JSON.stringify(r, null, 1));
        break;
      }
      case 'shot': {
        const name = (args[0] || `shot-${Date.now()}`).replace(/[^a-zA-Z0-9_-]/g, '');
        const file = path.join(SHOTS, `${name}.png`);
        await page.screenshot({ path: file, fullPage: false });
        console.log(`SAVED ${path.relative(ROOT, file)}`);
        break;
      }
      case 'stop': {
        const ctx = browser.contexts()[0];
        if (ctx) await ctx.close().catch(() => {});
        try { fs.rmSync(metaFile); } catch {}
        console.log('OK stopped');
        break;
      }
      default:
        throw new Error('unknown command ' + cmd);
    }
  } finally {
    await browser.close().catch(() => {});
  }
}
