/*
 * CROOKSLDN — the bag drawer.
 *
 * Tapping BAG opens the cart in place instead of costing a page load and the
 * shopper's scroll position. It also opens by itself after anything adds to
 * the cart, so the confirmation IS the bag rather than a line of text under a
 * button.
 *
 * NO MONEY IS FORMATTED HERE. The contents come from
 * /cart?view=crk-drawer as HTML that Liquid has already run `money` over, so
 * presentment currency and market conversion stay Shopify's job. That is also
 * why a bundle line can name both its garments: /cart.js reports
 * has_components but never says how many, and Liquid can read them.
 *
 * Progressive enhancement throughout. The header bag link is a real link to
 * /cart; this file intercepts the click only once it has loaded. If it never
 * loads, or JS is off, the cart page is still there. The drawer also links to
 * the full bag on purpose — it is a shortcut, not a replacement.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-crk-bagdrawer]');
  if (!root) return;

  var panel = root.querySelector('[data-crk-bagdrawer-panel]');
  var body = root.querySelector('[data-crk-bag-body]');
  var headCount = root.querySelector('[data-crk-bag-headcount]');
  if (!panel || !body) return;

  var VIEW = '/cart?view=crk-drawer';
  var opener = null;      /* what to hand focus back to */
  var open = false;
  var busy = false;
  var loadedOnce = false;

  /* ---- focus ---------------------------------------------------------- */
  var FOCUSABLE = 'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

  function focusables() {
    return Array.prototype.filter.call(
      panel.querySelectorAll(FOCUSABLE),
      function (el) { return el.offsetParent !== null || el === document.activeElement; }
    );
  }

  function onKey(e) {
    if (!open) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key !== 'Tab') return;
    var f = focusables();
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  /* ---- open / close --------------------------------------------------- */
  function show() {
    if (open) return;
    open = true;
    opener = document.activeElement;
    root.hidden = false;
    /* Next frame, so the transition has a frame to start from rather than
       being collapsed into the same style recalculation as `hidden`. */
    window.requestAnimationFrame(function () {
      root.setAttribute('data-crk-open', 'true');
    });
    document.documentElement.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey, true);
    var f = focusables();
    if (f.length) f[0].focus();
  }

  function close() {
    if (!open) return;
    open = false;
    root.removeAttribute('data-crk-open');
    document.documentElement.style.overflow = '';
    document.removeEventListener('keydown', onKey, true);
    /* Wait out the slide before hiding, unless motion is off. */
    var wait = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 260;
    window.setTimeout(function () { if (!open) root.hidden = true; }, wait);
    if (opener && typeof opener.focus === 'function') opener.focus();
    opener = null;
  }

  /* ---- contents ------------------------------------------------------- */
  function paintCount() {
    var el = body.querySelector('[data-crk-bag-count-value]');
    if (!el || !headCount) return;
    var n = el.getAttribute('data-crk-bag-count-value');
    headCount.textContent = n ? '[' + n + ']' : '';
    /* Same number, same rule, one repaint: the header count is whatever
       Liquid just counted, not a second arithmetic. */
    if (window.crkBag && n) window.crkBag.paint(n);
  }

  function load() {
    body.setAttribute('aria-busy', 'true');
    return fetch(VIEW, { credentials: 'same-origin', headers: { Accept: 'text/html' } })
      .then(function (r) {
        if (!r.ok) throw new Error('bag ' + r.status);
        return r.text();
      })
      .then(function (html) {
        body.innerHTML = html;
        loadedOnce = true;
        paintCount();
      })
      .catch(function () {
        /* A drawer that cannot draw itself must not become a dead end. */
        body.innerHTML = '';
        var p = document.createElement('p');
        p.className = 'crk-bagdrawer__err';
        p.textContent = 'Could not open the bag.';
        var a = document.createElement('a');
        a.className = 'crk-bagdrawer__view';
        a.href = '/cart';
        a.textContent = 'Go to the bag';
        body.appendChild(p);
        body.appendChild(a);
      })
      .then(function () {
        body.setAttribute('aria-busy', 'false');
      });
  }

  function change(key, qty, btn) {
    if (busy) return;
    busy = true;
    if (btn) btn.disabled = true;
    body.setAttribute('aria-busy', 'true');

    fetch('/cart/change.js', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ id: key, quantity: qty })
    })
      .then(function (r) {
        if (!r.ok) throw new Error('change ' + r.status);
        return load();
      })
      .catch(function () {
        body.setAttribute('aria-busy', 'false');
        if (btn) btn.disabled = false;
      })
      .then(function () { busy = false; });
  }

  /* Delegated, because the body is replaced on every change. */
  body.addEventListener('click', function (e) {
    var qtyBtn = e.target.closest ? e.target.closest('[data-crk-bag-qty]') : null;
    if (!qtyBtn) return;
    e.preventDefault();
    var line = qtyBtn.closest('[data-crk-bag-line]');
    if (!line) return;
    var qty = parseInt(qtyBtn.getAttribute('data-crk-bag-qty'), 10);
    if (isNaN(qty) || qty < 0) return;
    change(line.getAttribute('data-crk-key'), qty, qtyBtn);
  });

  /* The checkout form posts normally — no interception. Only the double-press
     is stopped, because a second POST while the first is in flight is how a
     shopper ends up looking at an error instead of a till. */
  body.addEventListener('submit', function (e) {
    var btn = e.target.querySelector('[data-crk-bag-checkout]');
    if (!btn) return;
    if (btn.disabled) { e.preventDefault(); return; }
    btn.disabled = true;
  });

  root.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('[data-crk-bag-close]')) {
      e.preventDefault();
      close();
    }
  });

  /* ---- what opens it -------------------------------------------------- */
  function openFrom(e) {
    /* Let a modified click do what the shopper asked: new tab, new window,
       download. Only a plain left click becomes the drawer. */
    if (e && (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0)) return;
    if (e) e.preventDefault();
    show();
    if (!loadedOnce) load();
    else load();
  }

  var links = document.querySelectorAll('a[href$="/cart"], a[href*="/cart?"], [data-crk-bag-open]');
  for (var i = 0; i < links.length; i++) {
    (function (el) {
      el.addEventListener('click', openFrom);
    })(links[i]);
  }

  /* Opened by crk:cartchanged, not by the raw add. crooks-record.js fires
     crk:added on its own element first and lets listeners put promises on
     detail.waitFor — the set toggle uses that to clear the component line a
     bundle replaces. Opening on the add would show the shopper a bag mid-edit;
     crk:cartchanged is dispatched once all of that has settled. */
  document.addEventListener('crk:cartchanged', function (e) {
    var openIt = !e.detail || e.detail.open !== false;
    if (openIt) show();
    if (open) load();
  });

  window.crkBagDrawer = { open: function () { openFrom(null); }, close: close, refresh: load };
})();
