const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', proxy: { server: process.env.HTTPS_PROXY }, args: ['--ssl-version-max=tls1.2', '--disable-background-networking'] });
  const OUT = {};
  const accept = async (p) => { try { const b = p.locator('button:has-text("Accept")').first(); if (await b.isVisible({ timeout: 1500 })) { await b.click(); await new Promise(r=>setTimeout(r,500)); } } catch(e){} };
  // NEW crewneck: dump every accordion header + body text via DOM structure
  {
    const page = await (await browser.newContext({ viewport: {width:390,height:844}, isMobile:true, hasTouch:true })).newPage();
    await page.goto('https://caijh1httspvte6b-100410786135.shopifypreview.com/products/charcoal-cellblock-crewneck', { waitUntil:'load', timeout:60000 });
    await new Promise(r=>setTimeout(r,1200)); await accept(page);
    // click every heading that looks like an accordion, then read the panel that expands
    OUT.new_headers = await page.evaluate(() => Array.from(document.querySelectorAll('h2, summary, button')).map(e=>(e.textContent||'').replace(/\s+/g,' ').trim()).filter(t=>/SPEC|DESCRIPTION|MEASURE|CHAIN|CUSTODY|SHIPPING|RETURN|SIZE/i.test(t)&&t.length<60).slice(0,10));
    // expand: click each header text
    for (const t of ['SPECIFICATION','ITEM DESCRIPTION','MEASUREMENTS','CHAIN OF CUSTODY']) {
      try { const el = page.locator(`text=${t}`).first(); if (await el.isVisible({timeout:800})) { await el.click({timeout:2500}); await new Promise(r=>setTimeout(r,500)); } } catch(e){}
    }
    await new Promise(r=>setTimeout(r,700));
    await page.screenshot({ path:'captures/new/live/fu-crewneck-expanded.jpg', type:'jpeg', quality:60, fullPage:true });
    // grab visible text near those headers
    OUT.new_expanded_text = await page.evaluate(() => {
      const out = {};
      for (const h of document.querySelectorAll('h2, [class*="acc"], details, summary')) {
        const t = (h.textContent||'').replace(/\s+/g,' ').trim();
        if (/SPEC|DESCRIPTION|MEASURE|CHAIN|CUSTODY|SHIPPING|RETURN/i.test(t) && t.length < 400) {
          // sibling/next content
          let body = '';
          let n = h.nextElementSibling;
          for (let i=0;i<3 && n;i++){ body += ' ' + (n.textContent||'').replace(/\s+/g,' ').trim(); n = n.nextElementSibling; }
          out[t.slice(0,40)] = (t + ' :: ' + body).slice(0,500);
        }
      }
      return out;
    });
    // full page innerText for shipping/returns keywords
    OUT.new_pdp_bodytext_has = await page.evaluate(() => {
      const t = document.body.innerText.toLowerCase();
      return { returns_days: /\b\d+\s*(day|days)\b/.test(t), free_returns: t.includes('free return'), returns_word: t.includes('return'), shipping_cost: /£|\$|free (uk )?shipping/.test(t), measurements: t.includes('measurement')||t.includes('waist')||t.includes('chest') };
    });
    await page.context().close();
  }
  // OLD crewneck comparison
  {
    const page = await (await browser.newContext({ viewport: {width:390,height:844}, isMobile:true, hasTouch:true })).newPage();
    await page.goto('https://crooksldn.com/products/charcoal-cellblock-crewneck', { waitUntil:'load', timeout:60000 });
    await new Promise(r=>setTimeout(r,1500));
    OUT.old_pdp_bodytext_has = await page.evaluate(() => {
      const t = document.body.innerText.toLowerCase();
      return { returns_days: /\b\d+\s*(day|days)\b/.test(t), returns_word: t.includes('return'), shipping_cost: /£|\$|free (uk )?shipping/.test(t), measurements: t.includes('measurement')||t.includes('waist')||t.includes('chest'), size_chart: t.includes('size chart')||t.includes('size guide') };
    });
    OUT.old_headers = await page.evaluate(() => Array.from(document.querySelectorAll('h2,summary,button,a')).map(e=>(e.textContent||'').replace(/\s+/g,' ').trim()).filter(t=>/SHIPPING|RETURN|SIZE|DESCRIPTION|DETAIL|DELIVERY/i.test(t)&&t.length<50).slice(0,10));
    await page.screenshot({ path:'captures/old/live/fu-crewneck-pdp.jpg', type:'jpeg', quality:60, fullPage:true });
    await page.context().close();
  }
  fs.writeFileSync('data/followup-accordions.json', JSON.stringify(OUT,null,1));
  console.log(JSON.stringify(OUT,null,1));
  await browser.close();
})().catch(e=>{console.error('FAIL',e.message);process.exit(1);});
