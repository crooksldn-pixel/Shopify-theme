const { chromium } = require('playwright');
const { execSync } = require('child_process');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    args: ['--disable-features=UseMLKEM,PostQuantumKeyAgreement,PostQuantumKyber']
  });
  const out = execSync("for p in $(pgrep -f pw-browsers); do tr '\\0' ' ' < /proc/$p/cmdline; echo; echo ---; done").toString();
  console.log(out);
  await browser.close();
})().catch(e => { console.error('FAIL', e.message.split('\n')[0]); process.exit(1); });
