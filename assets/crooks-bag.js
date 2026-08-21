/* CROOKSLDN — the bag count.
 *
 * The count means GARMENTS. A bundle ("complete the set") is a single cart line
 * holding two pieces, so cart.item_count called it 1 while the same two pieces
 * bought separately called it 2. /cart.js reports `has_components: true` on a
 * bundle line but never says how many components it holds, so this cannot be
 * worked out in JavaScript. templates/cart.crk-count.liquid answers it from
 * Liquid, where the components are readable, and this file fetches that after
 * anything that changes the cart.
 *
 * Exposed as window.crkBag so the PDP (crooks-record.js) and the set toggle
 * (crooks-set.js) both repaint through the same rule instead of each carrying
 * their own arithmetic.
 *
 * Progressive enhancement: with this file absent the header still prints the
 * count Liquid rendered on page load, which is correct until the shopper adds
 * something without a reload.
 */
(function () {
  'use strict';

  var header = document.querySelector('[data-crk-section="header"]');
  var url = (header && header.getAttribute('data-crk-bag-count-url')) || '/cart?view=crk-count';

  function paint(n) {
    var nodes = document.querySelectorAll('[data-crk-cart-count]');
    /* \u00a0 as an escape, not a literal invisible byte; textContent so nothing
       fetched can inject markup. */
    for (var i = 0; i < nodes.length; i++) nodes[i].textContent = '\u00a0[' + n + ']';
  }

  /* Resolves with the number so a caller can also put it in a message. Rejects
     rather than guessing: a caller that needs a number has a fallback of its
     own, and a wrong count in the header is worse than a stale one. */
  function refresh() {
    return fetch(url, { credentials: 'same-origin', headers: { Accept: 'text/html' } })
      .then(function (r) {
        if (!r.ok) throw new Error('bag count ' + r.status);
        return r.text();
      })
      .then(function (text) {
        var n = parseInt(String(text).trim(), 10);
        if (isNaN(n)) throw new Error('bag count not a number');
        paint(n);
        return n;
      });
  }

  window.crkBag = { refresh: refresh, paint: paint };
})();
