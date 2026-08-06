/*
 * CROOKSLDN — exhibit record (PDP) behaviours.
 * Vanilla ES2019. Configuration comes from data-* attributes only.
 *
 * Progressive enhancement — with JS disabled the page still sells:
 *   - the server-selected variant is already in the form's hidden id input
 *   - <noscript> renders ?variant= links for every size
 *   - add to bag is a normal form submit
 */
(function () {
  'use strict';

  function initRecord(root) {
    var form = root.querySelector('#crk-product-form') || root.querySelector('form[action*="/cart/add"]');
    var idInput = root.querySelector('[data-crk-variant-id]');
    var buyBtn = root.querySelector('[data-crk-buy]');
    var stockLine = root.querySelector('[data-crk-stockline]');
    var cells = root.querySelectorAll('.crk-size');
    var priceEl = root.querySelector('[data-crk-price]');

    var labels = {
      add: root.getAttribute('data-crk-label-add') || 'ADD TO BAG',
      select: root.getAttribute('data-crk-label-select') || 'SELECT A SIZE',
      sold: root.getAttribute('data-crk-label-sold') || 'SOLD OUT',
      inStock: root.getAttribute('data-crk-label-instock') || 'IN STOCK'
    };
    var lowTpl = root.getAttribute('data-crk-label-low') || '[n] LEFT IN SIZE [size]';
    var soldTpl = root.getAttribute('data-crk-label-soldsize') || 'SIZE [size] IS SOLD OUT';

    function setBuy(label, disabled) {
      if (!buyBtn) return;
      buyBtn.textContent = label;
      buyBtn.disabled = !!disabled;
    }

    function select(cell) {
      if (!cell || cell.getAttribute('aria-disabled') === 'true') return;
      for (var i = 0; i < cells.length; i++) cells[i].setAttribute('aria-pressed', 'false');
      cell.setAttribute('aria-pressed', 'true');

      var id = cell.getAttribute('data-variant-id');
      var size = cell.getAttribute('data-size');
      var qty = parseInt(cell.getAttribute('data-quantity'), 10);
      var available = cell.getAttribute('data-available') === 'true';
      var price = cell.getAttribute('data-price');

      if (idInput && id) idInput.value = id;
      if (priceEl && price) priceEl.textContent = price;

      // Keep the URL shareable and back-button friendly.
      try {
        var u = new URL(window.location.href);
        u.searchParams.set('variant', id);
        window.history.replaceState(null, '', u.pathname + u.search);
      } catch (e) { /* older browser */ }

      if (stockLine) {
        if (!available) {
          stockLine.textContent = soldTpl.replace('[size]', size);
          stockLine.classList.add('crk-stockline--out');
        } else if (!isNaN(qty) && qty > 0 && qty <= 3) {
          stockLine.textContent = lowTpl.replace('[n]', qty).replace('[size]', size);
          stockLine.classList.remove('crk-stockline--out');
        } else {
          stockLine.textContent = labels.inStock;
          stockLine.classList.remove('crk-stockline--out');
        }
      }
      setBuy(available ? labels.add : labels.sold, !available);

      // Highlight the matching measurements row.
      var rows = root.querySelectorAll('[data-crk-measure-row]');
      for (var r = 0; r < rows.length; r++) {
        var match = rows[r].getAttribute('data-crk-measure-row').toUpperCase() === String(size).toUpperCase();
        if (match) rows[r].setAttribute('data-selected', 'true');
        else rows[r].removeAttribute('data-selected');
      }
    }

    for (var i = 0; i < cells.length; i++) {
      (function (cell, idx) {
        cell.addEventListener('click', function () { select(cell); });
        cell.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = Math.min(idx + 1, cells.length - 1);
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = Math.max(idx - 1, 0);
          else if (e.key === 'Home') next = 0;
          else if (e.key === 'End') next = cells.length - 1;
          if (next === null) return;
          e.preventDefault();
          if (cells[next]) cells[next].focus();
        });
      })(cells[i], i);
    }

    // Reflect whatever the server already selected.
    var pre = root.querySelector('.crk-size[aria-pressed="true"]');
    if (pre) select(pre);
    else if (cells.length && buyBtn) setBuy(labels.select, true);

    // Guard: never submit without a variant id.
    if (form) {
      form.addEventListener('submit', function (e) {
        if (!idInput || !idInput.value) { e.preventDefault(); setBuy(labels.select, true); }
      });
    }

    /* ---- gallery ---- */
    var slides = root.querySelectorAll('[data-crk-slide]');
    var thumbs = root.querySelectorAll('[data-crk-thumb]');
    var counter = root.querySelector('[data-crk-photo-counter]');
    var counterTpl = root.getAttribute('data-crk-photo-label') || 'PHOTO [i] OF [n]';
    function show(n) {
      for (var s = 0; s < slides.length; s++) slides[s].hidden = s !== n;
      for (var t = 0; t < thumbs.length; t++) thumbs[t].setAttribute('aria-current', t === n ? 'true' : 'false');
      if (counter) counter.textContent = counterTpl.replace('[i]', n + 1).replace('[n]', slides.length);
    }
    for (var t = 0; t < thumbs.length; t++) {
      (function (btn, idx) {
        btn.addEventListener('click', function () { show(idx); });
        btn.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = Math.min(idx + 1, thumbs.length - 1);
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = Math.max(idx - 1, 0);
          if (next === null) return;
          e.preventDefault();
          thumbs[next].focus(); show(next);
        });
      })(thumbs[t], t);
    }
    if (slides.length > 1) show(0);

    /* ---- sticky buy bar: mobile only, only while the primary control is off-screen ---- */
    var bar = root.querySelector('[data-crk-buybar]');
    if (bar && buyBtn && 'IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (en) {
        bar.setAttribute('data-visible', en[0].isIntersecting ? 'false' : 'true');
      });
      io.observe(buyBtn);
      var barBtn = bar.querySelector('button');
      if (barBtn && form) {
        barBtn.addEventListener('click', function () {
          if (typeof form.requestSubmit === 'function') form.requestSubmit();
          else form.submit();
        });
      }
    }
  }

  function mountAll(scope) {
    var root = scope && scope.querySelectorAll ? scope : document;
    var nodes = root.querySelectorAll('[data-crk-section="exhibit-record"]');
    for (var i = 0; i < nodes.length; i++) {
      if (!nodes[i]._crkRec) { nodes[i]._crkRec = true; initRecord(nodes[i]); }
    }
    if (root.matches && root.matches('[data-crk-section="exhibit-record"]') && !root._crkRec) {
      root._crkRec = true; initRecord(root);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else {
    mountAll(document);
  }
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
})();
