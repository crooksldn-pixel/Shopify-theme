/*
 * CROOKSLDN — carriage status.
 * The section renders correct on load; this only keeps it correct when the cart
 * changes without a page load. Horizon dispatches 'cart:update' (assets/events.js),
 * and the theme's own add-to-bag path is covered by re-reading /cart.js.
 * With this file absent the readout is still right on every full page load.
 */
(function () {
  'use strict';

  function init(root) {
    var msg  = root.querySelector('[data-crk-carriage-msg]');
    var fill = root.querySelector('[data-crk-carriage-fill]');
    var track= root.querySelector('[data-crk-carriage-track]');
    if (!msg || !fill || !track) return;

    var t1 = parseInt(root.getAttribute('data-crk-tier1'), 10);
    var t2 = parseInt(root.getAttribute('data-crk-tier2'), 10);
    if (isNaN(t1) || isNaN(t2) || t2 <= 0) return;

    var L = {
      to1:  root.getAttribute('data-crk-label-to1')  || '[amount] to free delivery',
      to2:  root.getAttribute('data-crk-label-to2')  || '[amount] to free delivery',
      done: root.getAttribute('data-crk-label-done') || 'Free delivery unlocked'
    };

    // Mirror Shopify's money_format rather than assuming a symbol.
    var fmt = root.getAttribute('data-crk-money-format') || '£{{amount}}';
    function money(cents) {
      var v = (cents / 100).toFixed(2);
      var out = fmt.replace(/\{\{\s*amount\s*\}\}/, v)
                   .replace(/\{\{\s*amount_no_decimals\s*\}\}/, Math.round(cents / 100))
                   .replace(/\{\{\s*amount_with_comma_separator\s*\}\}/, v.replace('.', ','));
      return out.replace(/<[^>]*>/g, '');
    }

    function paint(total) {
      var state, remaining;
      if (total >= t2)      { state = 'done';  remaining = 0; }
      else if (total >= t1) { state = 'to2';   remaining = t2 - total; }
      else                  { state = 'to1';   remaining = t1 - total; }

      msg.textContent = state === 'done'
        ? L.done
        : L[state].replace('[amount]', money(remaining));

      // Floor, and hold at 99 until the tier is actually met: rounding showed a
      // full bar at £69.99 next to "£0.01 to go".
      var pct = Math.floor(total * 100 / t2);
      if (pct >= 100 && total < t2) pct = 99;
      if (pct > 100) pct = 100;
      fill.style.width = pct + '%';
      track.setAttribute('aria-valuenow', String(pct));

      var tiers = root.querySelectorAll('[data-crk-tier-state]');
      for (var i = 0; i < tiers.length; i++) {
        var n = tiers[i].getAttribute('data-crk-tier-state') === '1' ? t1 : t2;
        tiers[i].setAttribute('data-crk-met', total >= n ? 'true' : 'false');
      }
    }

    var busy = false;
    function refresh() {
      if (busy) return;
      busy = true;
      fetch('/cart.js', { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (c) { paint(c.total_price); })
        .catch(function () { /* leave the server-rendered state alone */ })
        .then(function () { busy = false; });
    }

    document.addEventListener('cart:update', refresh);
    document.addEventListener('crk:cart:update', refresh);
  }

  function mountAll(scope) {
    var root = scope && scope.querySelectorAll ? scope : document;
    var nodes = root.querySelectorAll('[data-crk-section="cart-progress"]');
    for (var i = 0; i < nodes.length; i++) {
      if (!nodes[i]._crkCarriage) { nodes[i]._crkCarriage = true; init(nodes[i]); }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else { mountAll(document); }
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
})();
