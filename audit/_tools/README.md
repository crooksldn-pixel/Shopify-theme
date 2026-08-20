# Audit harness — how to drive the site

Run everything from the repo root (`/home/user/Shopify-theme`). Node 22, ESM.
Put your script in `audit/_tools/` and run `node audit/_tools/<yours>.mjs`.

**Never call `chromium.launch()` yourself.** Use `session()`. It sets the
preview cookie (without it you are silently auditing the LIVE theme), pins the
GB market (without it prices come back in USD and the carriage bar does not
render at all), and asserts `.crk-root` + theme id `202053779799`, throwing if
either is wrong.

## API — `import { ... } from './lib.mjs'`

```js
session({ device, slow, reducedMotion, zoom, js, colorScheme })
  // device: 'mobile' (390x844 dpr3, default) | 'desktop' (1440x900)
  //       | 'mobileLandscape' (844x390) | 'androidSlow' (360x800)
  // slow: true          -> Slow 4G + 4x CPU
  // js: false           -> JavaScript disabled
  // zoom: 2             -> 200% page zoom
  // reducedMotion: true -> prefers-reduced-motion: reduce
  // returns { browser, context, page, identity, close }

go(page, '/products/handle')   // navigate + re-assert theme; returns {status,url,crkRoot,themeId,ok,gb,...}
shot(page, 'pdp-size-row')     // -> audit/screens/pdp-size-row.png  (full:true for fullPage)
visibleText(page, 'main')      // what the shopper can actually read
assertTheme(page)              // {crkRoot, themeId, ok, currency, country, ...}
write(file, content) / append(file, line) / sleep(ms)
PREVIEW                        // base URL
```

## Worked example

```js
import { session, go, shot, visibleText, sleep } from './lib.mjs';

const s = await session({ device: 'mobile' });
const { page } = s;
console.log('identity', JSON.stringify(s.identity));   // must show ok:true, gb:true

await go(page, '/products/cb1-wash-jeans');
await page.getByRole('button', { name: /^M$/ }).click();   // pick a size
await sleep(800);
console.log(await visibleText(page, 'main'));
console.log(await shot(page, 'pdp-size-m'));

// add to bag, then read the cart back
await page.getByRole('button', { name: /ADD TO BAG/i }).click();
await sleep(2500);
await go(page, '/cart');
console.log(await visibleText(page, 'main'));

await s.close();
```

## Things that bite

- **One browser per script.** Always `await s.close()` in a `finally`, or the
  process hangs.
- **Keep it to 1–2 browsers at a time.** 4 cores. This audit reports *felt*
  speed; contention would fake it.
- Selectors: prefer `getByRole` / `getByText`. Theme classes are all `crk-*`.
  Sizes are buttons; accordions are `<details>`; the set toggle is a checkbox.
- After a click that changes the page, `await sleep(600..1200)` — this theme
  re-renders in vanilla JS with no framework settle signal.
- `visibleText(page,'main')` is your primary evidence. Paste real strings into
  your notes; never paraphrase a message the shopper is shown.
- Screenshot anything you assert. A finding without a shot is not a finding.
- Timings: use `Date.now()` around a navigation if you want to report how long
  a shopper waited. Report it as felt duration, not as a metric.

## Hard limits

No order. No card details. No real personal data — use `buyer+test@example.com`
and obvious test values. Do not modify any store setting, product or discount.
Checkout may be walked **to the payment step and abandoned**, never submitted.
