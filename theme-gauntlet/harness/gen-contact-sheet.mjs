// Generates report/contact-sheet.html — every screenshot cited in report.md,
// grouped by finding, with relative links into ../shots/.
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SHOTS = path.join(ROOT, 'shots');
const report = fs.readFileSync(path.join(ROOT, 'report', 'report.md'), 'utf8');
const files = fs.readdirSync(SHOTS).filter(f => f.endsWith('.png'));

// every shot-like token in the report
const cited = [...new Set([...report.matchAll(/[a-z0-9][a-z0-9-]+(?:\.png)?/gi)]
  .map(m => m[0].replace(/\.png$/i, ''))
  .filter(t => /^(b\d{2}-|census-)/.test(t)))];

const resolve = t => files.find(f => f === t + '.png') || files.find(f => f.startsWith(t)) || null;

const groups = [
  ['The membership trial ambush (3/3 buyers)', ['b04-05-checkout-trial-surprise','b12-07','b15-05','b04-04-pricing-full','b04-06']],
  ['Prices withheld until checkout (10/20 taxed)', ['b01-03-price-shock-99','b12-02-course-catalog','b10-02-course-catalog','b12-09','b10-05-zendala-price-clear','b13-06','b12-04','b14-02']],
  ['The certification tier: broken money pages', ['b03-04-pricing-cards','b03-06-checkout-full-price-mislabel','b09-04-teacher-training-stale-date','b09-05-course-full-contradiction','b09-03-startdate-no-year','b05-04-coaching-program-pricing','census-amcert-pricing-m']],
  ['Naming: the beginner who could not find the beginner course', ['b06-02-courses-list-no-basics','b06-03-wrong-course-certification-price','b06-04-abandon-no-basics-course','b01-05-neurographica-chakras','b13-05-zendala-course','census-basics-404-m']],
  ['No gift path (3/3 gift buyers)', ['b14-05','b14-06-abandon','b15-05','b16-06-no-direct-purchase-path']],
  ['The book dead-ends off-site (2/2 book buyers)', ['b05-01-landing','b05-02','b05-05-abandon-no-onsite-checkout','b16-06']],
  ['Contact & schedule information gaps', ['b20-03-email-found-in-privacy-policy','b20-05','b18-02','b20-02']],
  ['What sells: the working formula', ['b01-06-price-59-good','b01-07','b01-09-checkout-filled','b02-03-price-in-pounds','b02-05-checkout-gbp','b15-06','b03-05-checkout-split-payment','b01-08-graduates-directory','b19-02-directory-found','b08-03-zendala-teacher','b08-04']],
  ['Quarantined (environment artifacts, not site defects)', ['b18-03','b05-03-redirected-to-amazon','b16-05']],
  ['Integrity & corrections', ['b07-07-no-testimonials-found','b17-03','b17-04','b11-07-menu-retry','census-checkout-badcoupon-m']],
];

const used = new Set();
let body = '';
for (const [title, keys] of groups) {
  const cards = keys.map(k => {
    const f = resolve(k);
    if (!f || used.has(f)) return '';
    used.add(f);
    return `<figure><a href="../shots/${f}"><img loading="lazy" src="../shots/${f}" alt="${f}"></a><figcaption>${f}</figcaption></figure>`;
  }).join('');
  if (cards) body += `<h2>${title}</h2><div class="grid">${cards}</div>`;
}
const leftovers = cited.map(resolve).filter(f => f && !used.has(f));
if (leftovers.length) {
  body += `<h2>Other cited shots</h2><div class="grid">` + [...new Set(leftovers)].map(f =>
    `<figure><a href="../shots/${f}"><img loading="lazy" src="../shots/${f}" alt="${f}"></a><figcaption>${f}</figcaption></figure>`).join('') + '</div>';
}

const html = `<!doctype html><html><head><meta charset="utf-8">
<title>Contact sheet — annadenning.com buyer gauntlet</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font:15px/1.45 system-ui,sans-serif;margin:2rem;background:#fafafa;color:#222}
h1{font-size:1.4rem} h2{margin-top:2.2rem;border-bottom:2px solid #ddd;padding-bottom:.3rem}
.grid{display:flex;flex-wrap:wrap;gap:14px}
figure{margin:0;width:240px}
img{width:100%;height:300px;object-fit:cover;object-position:top;border:1px solid #ccc;border-radius:6px;background:#fff}
figcaption{font-size:.72rem;color:#555;word-break:break-all;margin-top:4px}
p.note{max-width:60rem;color:#444}
</style></head><body>
<h1>Contact sheet — annadenning.com Buyer's Cut (2026-08-19)</h1>
<p class="note">Every screenshot cited in <code>report.md</code>, grouped by finding. Click any image for full size. Single-site run: no OLD/NEW pairs exist (decisions.md D1). Images are relative links into <code>../shots/</code> — open this file from the repository checkout.</p>
${body}
</body></html>`;
fs.writeFileSync(path.join(ROOT, 'report', 'contact-sheet.html'), html);
console.log('wrote contact-sheet.html:', used.size + (leftovers ? new Set(leftovers).size : 0), 'images referenced');
