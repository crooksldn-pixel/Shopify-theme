const { chromium } = require('playwright');
const fs = require('fs');
const NEW = 'https://caijh1httspvte6b-100410786135.shopifypreview.com';
const sleep = ms => new Promise(r=>setTimeout(r,ms));
(async () => {
  const browser = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', proxy:{server:process.env.HTTPS_PROXY}, args:['--ssl-version-max=tls1.2','--disable-background-networking'] });
  const page = await (await browser.newContext({ viewport:{width:1440,height:900} })).newPage();
  const accept = async () => { try { const b=page.locator('button:has-text("Accept")').first(); if (await b.isVisible({timeout:1500})) { await b.click(); await sleep(400);} } catch(e){} };
  const grab = async (label) => {
    return await page.evaluate(() => {
      const seen = new Set(); const out = [];
      const push = (kind, txt, extra) => {
        txt = (txt||'').replace(/\s+/g,' ').trim();
        if (!txt || txt.length>90) return;
        const key = kind+'|'+txt;
        if (seen.has(key)) return; seen.add(key);
        out.push({kind, txt, ...(extra||{})});
      };
      // nav/header
      document.querySelectorAll('header a, header button, [data-crk-section="header"] a, [data-crk-section="header"] button, nav a').forEach(e=>push('nav', e.textContent));
      // buttons & links site-wide (short)
      document.querySelectorAll('button, a[role="button"], .crk-btn, [class*="btn"]').forEach(e=>push('button', e.textContent));
      // headings
      document.querySelectorAll('h1,h2,h3,h4').forEach(e=>push('heading', e.textContent));
      // accordion / summary
      document.querySelectorAll('summary, [class*="acc"] , details > *:first-child').forEach(e=>push('accordion', e.textContent));
      // badges / status / chips / tabs / toggles
      document.querySelectorAll('[class*="badge"],[class*="chip"],[class*="tab"],[class*="status"],[class*="stock"],[class*="toggle"],[role="tab"],[aria-pressed]').forEach(e=>push('badge/toggle', e.textContent));
      // footer
      document.querySelectorAll('footer a, footer button, footer h2, footer h3, [data-crk-section="footer"] a').forEach(e=>push('footer', e.textContent));
      // small/uppercase decorative lines (monospace terminal vibe)
      document.querySelectorAll('small, [class*="micro"], [class*="terminal"], [class*="eyebrow"], [class*="label"], [class*="meta"], p').forEach(e=>{
        const t=(e.textContent||'').replace(/\s+/g,' ').trim();
        if (t && t.length<=90 && /[A-Z]{3,}|\/\/|::|v\d|»|→|●|▮|█/.test(t)) push('decorative?', t);
      });
      return out;
    });
  };
  const pages = [
    ['HOME', NEW+'/'],
    ['COLLECTION_ALL', NEW+'/collections/all'],
    ['PDP', NEW+'/products/charcoal-cellblock-crewneck'],
    ['CART', NEW+'/cart'],
    ['SEARCH', NEW+'/search?q=jeans'],
  ];
  const all = {};
  for (const [name,url] of pages) {
    await page.goto(url, {waitUntil:'load', timeout:60000}); await sleep(1200); await accept();
    // open menu drawer to catch its links (home only)
    if (name==='HOME') { try { await page.locator('header >> text=MENU').first().click({timeout:3000}); await sleep(700);} catch(e){} }
    // expand PDP accordions
    if (name==='PDP') { for (const t of ['Specification','Item description','Chain of custody','Release']) { try { await page.locator(`text=${t}`).first().click({timeout:1200}); await sleep(300);} catch(e){} } }
    all[name] = await grab(name);
  }
  fs.writeFileSync('data/copy-inventory.json', JSON.stringify(all,null,1));
  for (const [name, items] of Object.entries(all)) {
    console.log('\n===== '+name+' =====');
    const byKind = {};
    for (const it of items) (byKind[it.kind]=byKind[it.kind]||[]).push(it.txt);
    for (const [k,v] of Object.entries(byKind)) console.log(`[${k}] `+v.join('  |  '));
  }
  await browser.close();
})().catch(e=>{console.error('FAIL',e.message);process.exit(1);});
