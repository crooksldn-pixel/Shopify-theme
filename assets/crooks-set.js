/* CROOKSLDN — complete-the-set toggle.
 *
 * Ticking the box swaps the product form's variant id to the matching BUNDLE
 * variant (one per size pair, so inventory and fulfilment track per component)
 * and relabels the button. Unticking restores whatever crooks-record.js had
 * decided. One add to cart, one line, no second request.
 *
 * Every price string is pre-rendered by Liquid through `money` and carried in a
 * data attribute — this file never assembles a currency string, so presentment
 * currency and geo conversion are Shopify's to handle, not ours.
 *
 * Progressive enhancement: with this file absent the toggle stays collapsed and
 * inert, and the panel is `hidden`, so the page still sells the single item.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-crk-section="exhibit-record"]');
  if (!root) return;
  var set = root.querySelector('[data-crk-set]');
  if (!set) return;

  var check = set.querySelector('[data-crk-set-check]');
  var panel = set.querySelector('[data-crk-set-panel]');
  var sizesBox = set.querySelector('[data-crk-set-sizes]');
  var stockLine = set.querySelector('[data-crk-set-stock]');
  var wasEl = set.querySelector('[data-crk-set-was]');
  var nowEl = set.querySelector('[data-crk-set-now]');
  if (!check || !panel) return;

  var SOLD_TPL = set.getAttribute('data-crk-set-sold') || '';
  var PICK_TPL = set.getAttribute('data-crk-set-pick') || '';
  var MAIN_TPL = set.getAttribute('data-crk-set-main-first') || 'Pick your size first';

  var variants = [];
  var nodes = set.querySelectorAll('[data-crk-set-variants] li');
  for (var i = 0; i < nodes.length; i++) {
    var n = nodes[i];
    variants.push({
      id: n.getAttribute('data-id'),
      main: n.getAttribute('data-main'),
      partner: n.getAttribute('data-partner'),
      available: n.getAttribute('data-available') === 'true',
      was: n.getAttribute('data-was'),
      now: n.getAttribute('data-now'),
      cta: n.getAttribute('data-cta')
    });
  }
  if (!variants.length) return;

  var addBtn = set.querySelector('[data-crk-set-add]');
  var sizeBtns = sizesBox ? sizesBox.querySelectorAll('[data-crk-set-size]') : [];
  /* partnerSize stays null until the shopper picks one themselves. It is never
     seeded from the main size: someone buying a crewneck in L is not thereby
     buying shorts in L, and a pre-pressed button is indistinguishable from a
     choice they made. The wrong-size exchange it causes is one we now charge
     them postage for, which makes the guess worse than it was. */
  var partnerSize = null;
  var mainSize = null;

  function find(main, partner) {
    for (var i = 0; i < variants.length; i++) {
      if (variants[i].main === main && variants[i].partner === partner) return variants[i];
    }
    return null;
  }

  function partnerAvailable(size) {
    // A partner size is offerable if ANY pairing with it can be bought.
    for (var i = 0; i < variants.length; i++) {
      if (variants[i].partner === size && variants[i].available) return true;
    }
    return false;
  }

  function paintSizes() {
    for (var i = 0; i < sizeBtns.length; i++) {
      var val = sizeBtns[i].getAttribute('data-crk-set-size');
      var on = val === partnerSize;
      sizeBtns[i].setAttribute('aria-pressed', on ? 'true' : 'false');
      sizeBtns[i].setAttribute('data-selected', on ? 'true' : 'false');
      if (partnerAvailable(val)) sizeBtns[i].removeAttribute('aria-disabled');
      else sizeBtns[i].setAttribute('aria-disabled', 'true');
    }
  }

  /* Re-render on any change: the shopper's main size, their partner size, or
     the tick itself. Returns the bundle variant when the set is sellable. */
  function current() {
    if (!check.checked || !mainSize || !partnerSize) return null;
    var v = find(mainSize, partnerSize);
    return v && v.available ? v : null;
  }

  function paint() {
    /* The card is always on the page now, so the panel is never hidden. The
       tick still decides whether the form is armed with the bundle variant. */
    set.setAttribute('data-crk-set-on', check.checked ? 'true' : 'false');
    paintSizes();

    /* ADD BOTH needs both sizes before it can name a bundle variant. */
    if (addBtn) {
      var ready = !!(mainSize && partnerSize && find(mainSize, partnerSize) &&
                     find(mainSize, partnerSize).available);
      addBtn.disabled = !ready;
    }
    if (!check.checked) return;

    var v = mainSize && partnerSize ? find(mainSize, partnerSize) : null;
    if (v && v.available) {
      if (stockLine) { stockLine.textContent = ''; stockLine.hidden = true; }
      if (wasEl) wasEl.textContent = v.was;
      if (nowEl) nowEl.textContent = v.now;
      return;
    }
    if (wasEl) wasEl.textContent = '';
    if (nowEl) nowEl.textContent = '';
    if (!stockLine) return;
    stockLine.hidden = false;
    /* Three reasons the pair is not sellable, and only the last is a fault.
       Ticking the box before choosing your own size used to fall through to the
       sold-out branch and announce "sold out in M" against full stock, because
       find() cannot match a pair when half of it is missing. A false sold-out on
       the upsell is the most expensive sentence on the page. */
    if (!mainSize) {
      stockLine.setAttribute('data-out', 'false');
      stockLine.textContent = MAIN_TPL;
    } else if (!partnerSize) {
      // Waiting on a choice, not reporting a fault: no red.
      stockLine.setAttribute('data-out', 'false');
      stockLine.textContent = PICK_TPL;
    } else {
      stockLine.setAttribute('data-out', 'true');
      stockLine.textContent = SOLD_TPL.replace('[size]', partnerSize);
    }
  }

  /* crooks-record.js calls this after it has settled the normal buy state, so
     the set has the last word without racing it. */
  root._crkAfterRender = function (state) {
    /* The main key is every one of this product's chosen option values,
       joined the way Shopify titles a variant. A one-option garment gives
       "XS"; the Pink hoodie, which has a V1/V2 axis as well as a size,
       gives "XS / V1". Reading a single size option instead matched the
       wrong bundle variant on any garment with more than one axis. Null
       until every axis has been chosen — a half-built key matches nothing
       and would report a false sold-out. */
    var nextMain = null;
    if (state.selected && state.selected.length) {
      var parts = [];
      for (var q = 0; q < state.selected.length; q++) {
        if (!state.selected[q]) { parts = null; break; }
        parts.push(state.selected[q]);
      }
      if (parts) nextMain = parts.join(' / ');
    }
    if (nextMain !== mainSize) {
      mainSize = nextMain;
      paint();
    }

    var v = current();
    if (!v) {
      /* The box is ticked and a main size is chosen, but the set is not
         specified yet. Leaving the record's own ADD TO BAG enabled here would
         quietly sell one item to someone who asked for two, so the button
         states what is missing instead. Every other case is the record's to
         own and is left alone. */
      if (check.checked && mainSize && !partnerSize && PICK_TPL) {
        state.setBuy(PICK_TPL, true);
      }
      return;
    }
    if (state.idInput) state.idInput.value = v.id;
    state.setBuy(v.cta, false);
  };

  check.addEventListener('change', function () {
    paint();
    // Re-ask the record to settle the buy state, which re-enters the hook.
    root.dispatchEvent(new CustomEvent('crk:rerender'));
  });

  /* The bundle contains both garments, so any loose component line is now a
     duplicate the shopper would pay twice for. crooks-record.js announces every
     successful add; if what landed was one of our bundle variants, zero the
     components. /cart/update.js takes variant ids, which is exactly what we
     hold. Best effort: if it fails the cart is still correct, just untidy, and
     the shopper can see and remove the line themselves. */
  function isBundleVariant(id) {
    for (var i = 0; i < variants.length; i++) {
      if (String(variants[i].id) === String(id)) return true;
    }
    return false;
  }

  root.addEventListener('crk:added', function (e) {
    var added = e && e.detail && e.detail.id;
    if (!added || !isBundleVariant(added)) return;
    var componentIds = set.getAttribute('data-crk-set-components') || '';
    var ids = componentIds.split(',').filter(function (x) { return x; });
    if (!ids.length) return;
    var updates = {};
    for (var i = 0; i < ids.length; i++) updates[ids[i]] = 0;
    var done = fetch('/cart/update.js', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates: updates })
    }).catch(function () {});
    /* Hand the promise back so the PDP reads the bag count — and leaves for the
       till — only after these lines are actually gone. Without it the count is
       read mid-flight and reports garments the shopper no longer has. */
    if (e.detail && e.detail.waitFor) e.detail.waitFor.push(done);
  });

  for (var b = 0; b < sizeBtns.length; b++) {
    (function (btn) {
      btn.addEventListener('click', function () {
        partnerSize = btn.getAttribute('data-crk-set-size');
        paint();
        root.dispatchEvent(new CustomEvent('crk:rerender'));
      });
    })(sizeBtns[b]);
  }

  /* Arriving from the cart's "complete the set" line, with the set already
     switched on. Without this the offer sends you to a page where the thing it
     just offered you is off by default, and the obvious next move — adding the
     other garment on its own page — costs GBP 95 for a GBP 85 set. */
  try {
    if (new URLSearchParams(window.location.search).get('set') === '1') {
      check.checked = true;
    }
  } catch (e) {}

  /* ADD BOTH is a second action, not a second cart call. It ticks the box the
     existing logic already runs on and then presses the page's own buy button,
     so the bundle variant, the component line it replaces and the waitFor
     dispatch are all handled by the code that already handles them. */
  if (addBtn) {
    addBtn.addEventListener('click', function () {
      if (addBtn.disabled) return;
      check.checked = true;
      paint();
      root.dispatchEvent(new CustomEvent('crk:rerender'));
      var buy = root.querySelector('[data-crk-buy]');
      if (buy && !buy.disabled) buy.click();
    });
  }

  paint();
})();
