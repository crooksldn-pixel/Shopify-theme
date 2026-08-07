import { chromium } from 'playwright';
const sets = [
  ['pq-off','--disable-features=PostQuantumKyber,TLS13KyberX25519Draft00,UseMLKEM,EncryptedClientHello'],
  ['ech-off','--disable-features=EncryptedClientHello'],
  ['mlkem-off','--disable-features=UseMLKEM'],
];
for (const [name,feat] of sets) {
  const b = await chromium.launch({ args:['--no-sandbox','--proxy-server=http://127.0.0.1:36431','--ignore-certificate-errors',feat] });
  const ctx = await b.newContext({ ignoreHTTPSErrors:true });
  const p = await ctx.newPage();
  try { const r = await p.goto('https://example.com',{waitUntil:'domcontentloaded',timeout:30000}); console.log(name,'OK',r.status(),JSON.stringify(await p.title())); }
  catch(e){ console.log(name,'FAIL',e.message.split('\n')[0]); }
  await b.close();
}
