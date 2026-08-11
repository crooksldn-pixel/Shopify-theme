/* Deterministic persona roster, seed 42. Reusable regression panel.
 * Firewall: cards contain NO brand-intent language — personas arrive cold.
 * Prices referenced are the USD prices the storefront actually serves to the
 * capture vantage (crewneck $69, shorts $63, jorts $69, jeans $83, tees $35,
 * baggies $83, socks $9, duffle $25). Gift budget £60-100 ≈ $76-127.
 */
const fs = require('fs');
const path = require('path');

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rnd = mulberry32(42);
const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
const pickN = (arr, n) => {
  const cp = [...arr]; const out = [];
  while (out.length < n && cp.length) out.push(cp.splice(Math.floor(rnd() * cp.length), 1)[0]);
  return out;
};

const FIRST = ['Amara','Ben','Chloe','Dev','Ellis','Femi','Grace','Hana','Idris','Jaya','Kofi','Lena','Marcus','Nia','Omar','Priya','Quinn','Rosa','Sam','Tariq','Uma','Viktor','Wren','Ximena','Yusuf','Zara','Aiden','Bella','Callum','Daria','Eshan','Freya','Gio','Holly','Ivan','Jade','Kai','Lola','Milo','Nadia','Oscar','Poppy','Ravi','Sofia','Theo','Una','Vera','Will','Yara','Zeke'];
const LAST = ['Okafor','Hughes','Lin','Patel','Novak','Adeyemi','Kim','Silva','Byrne','Kaur','Mensah','Weber','Reid','Diallo','Haddad','Rossi','Frost','Alvarez','Cole','Nakamura','Osei','Doyle','Varga','Iqbal','Moreau'];

// trait pool with weights-ish sprinkling; some traits imply device/edge evidence
const TRAITS = [
  { key: 'price-sensitive', txt: 'compares every price against fast-fashion alternatives' },
  { key: 'brand-driven', txt: 'buys the story as much as the product; sniffs out effort' },
  { key: 'in-a-hurry', txt: 'shopping in stolen minutes; abandons fast', patience: 6 },
  { key: 'skeptical', txt: 'assumes unfamiliar stores are drop-shippers until proven otherwise' },
  { key: 'low-tech', txt: 'gets lost when interfaces behave unexpectedly; typos in search' },
  { key: 'comparison-shopper', txt: 'has a competitor tab mentally open the whole time' },
  { key: 'international', txt: 'outside the UK; anxious about currency, duties and shipping' },
  { key: 'low-vision', txt: 'browses at 200% zoom; judges from the zoomed desktop evidence', device: 'desktop', edge: 'edge-zoom' },
  { key: 'motor-limited', txt: 'navigates by keyboard/large targets; small tap targets are misses' },
  { key: 'late-night', txt: 'phone in bed on a weak connection; every second of loading counts', device: 'mobile', edge: 'edge-slow4g' },
];

const BAIL = [
  'a popup covering content before seeing anything',
  'no visible price on first screen',
  'being pushed to create an account',
  'no sizing help when unsure between two sizes',
  'no findable returns info before paying',
  'page still loading after ~5 seconds',
  'a button moving under their thumb mid-tap',
  'search that cannot be found or does not work',
  'prices in an unexpected currency with no explanation',
  'the item they came for being sold out',
  'checkout that looks different from the shop they were just in',
  'walls of identical-looking products with no guidance',
];

const TRUST = [
  'a findable returns window before checkout',
  'photos that look shot by the brand, not suppliers',
  'a real contact method (not just a form)',
  'reviews or any social proof',
  'consistent look between shop and checkout',
  'clear shipping costs before the payment page',
  'a brand story that explains who makes this',
  'stock/size availability that looks honest',
  'working social links with real activity',
  'no spelling errors or broken sections',
];

// intent plan: [intent, count, journeys, taskTemplates]
const PLAN = [
  ['buy-now', 30, ['j1', 'j2'], [
    'Buy the CHARCOAL CELLBLOCK CREWNECK in size M — friend recommended it, wants it ordered tonight',
    'Buy the BLUE WASH OG JEANS in a size that fits a 32in waist, quickly, between other errands',
    'Buy a grey crewneck under $80 for themselves before enthusiasm wears off',
    'Replace worn-out baggy jeans; find and buy wide-leg jeans in M without browsing anything else',
  ]],
  ['research-compare', 20, ['j3'], [
    'Clicked an ad straight to the $69 charcoal crewneck; decide if it beats the $63 shorts for value — must find shipping cost, returns and any reviews without leaving the funnel',
    'Deciding between the crewneck and shorts as a first order from an unknown brand; needs proof of quality and a returns escape hatch before adding to cart',
    'Comparing these jeans against a competitor tab; will only add to cart if shipping+returns make total risk acceptable',
  ]],
  ['browse-graze', 15, ['j4'], [
    'Kill ten minutes browsing the catalogue; open three products that catch the eye; leave if it gets boring or repetitive',
    'Scout the whole range to decide if this brand deserves a bookmark; sort by price to see the spread',
  ]],
  ['returning', 15, ['j7'], [
    'Bought BLUE WASH JORTS last month, wants the same again — search the exact name, then find where to log in / see orders',
    'Came back for jorts seen weeks ago; checks if an account or order history path exists before re-buying',
  ]],
  ['gift-hunt', 10, ['j5'], [
    'Find a gift around $76–127 for a nephew who lives in baggy streetwear; would love a gift-note option at checkout',
    'Buying for a teenager they do not understand; needs price filtering or clear price sorting to stay in a $76–127 budget, and safe returns if the size is wrong',
  ]],
  ['lookup-support', 10, ['j6'], [
    'Find, in order: what shipping costs, how many days to return, how to contact a human, a size guide, and where to track an order — timing each hunt',
    'Pre-purchase due diligence only: locate shipping policy, returns window, contact method, sizing help and order tracking without buying anything',
  ]],
];

const personas = [];
let id = 0;
const usedNames = new Set();

for (const [intent, count, journeys, tasks] of PLAN) {
  for (let i = 0; i < count; i++) {
    id++;
    const pid = 'P' + String(id).padStart(2, '0');
    let name;
    do { name = pick(FIRST) + ' ' + pick(LAST); } while (usedNames.has(name));
    usedNames.add(name);
    const nTraits = 1 + Math.floor(rnd() * 2); // 1-2 traits
    const traits = pickN(TRAITS, nTraits);
    const age = 15 + Math.floor(rnd() * 40);
    let patience = 5 + Math.floor(rnd() * 8); // 5-12
    for (const t of traits) if (t.patience) patience = Math.min(patience, t.patience);
    const journey = journeys[i % journeys.length];
    personas.push({
      id: pid,
      name,
      age,
      intent,
      journey,
      device: null, // assigned below to hit 60/40
      deviceForced: traits.find((t) => t.device)?.device || null,
      edgeEvidence: traits.filter((t) => t.edge).map((t) => t.edge),
      traits: traits.map((t) => t.key),
      backstory: `${age}yo; ${traits.map((t) => t.txt).join('; ')}`,
      task: tasks[i % tasks.length],
      patience_budget: patience,
      bail_triggers: pickN(BAIL, 2),
      trust_needs: pickN(TRUST, 2),
      order: id % 2 === 1 ? ['old', 'new'] : ['new', 'old'], // odd IDs OLD-first
    });
  }
}

// device assignment: 60 mobile / 40 desktop, honoring forced devices, spread across intents
let mobileLeft = 60, desktopLeft = 40;
for (const p of personas) {
  if (p.deviceForced === 'mobile') { p.device = 'mobile'; mobileLeft--; }
  if (p.deviceForced === 'desktop') { p.device = 'desktop'; desktopLeft--; }
}
for (const p of personas) {
  if (p.device) continue;
  // deterministic interleave weighted by remaining quota
  if (mobileLeft * 2 >= desktopLeft * 3 && mobileLeft > 0) { p.device = 'mobile'; mobileLeft--; }
  else if (desktopLeft > 0) { p.device = 'desktop'; desktopLeft--; }
  else { p.device = 'mobile'; mobileLeft--; }
}
for (const p of personas) delete p.deviceForced;

const counts = {};
for (const p of personas) {
  counts[p.intent] = (counts[p.intent] || 0) + 1;
  counts[p.device] = (counts[p.device] || 0) + 1;
}
console.log(counts);
fs.writeFileSync(path.join(__dirname, '..', 'data', 'personas.json'), JSON.stringify({ seed: 42, generated: '2026-08-11', personas }, null, 1));
console.log('personas:', personas.length);
