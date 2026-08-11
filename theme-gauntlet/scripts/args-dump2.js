const { chromium } = require('playwright');
const { execSync } = require('child_process');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    proxy: { server: process.env.HTTPS_PROXY },
    args: ['--disable-features=UseMLKEM,PostQuantumKeyAgreement,PostQuantumKyber']
  });
  const out = execSync(`for p in $(ls /proc | grep -E '^[0-9]+$'); do exe=$(readlink /proc/$p/exe 2>/dev/null); case "$exe" in *chrome*) echo "PID $p"; tr '\\0' '\\n' < /proc/$p/cmdline | head -60; echo ===;; esac; done`).toString();
  console.log(out.slice(0, 6000));
  await browser.close();
})().catch(e => { console.error('FAIL', e.message.split('\n')[0]); process.exit(1); });
