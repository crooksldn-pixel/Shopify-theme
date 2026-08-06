/*
 * CROOKSLDN — exhibit record (PDP) behaviours.
 * Ported from THE EXHIBIT RECORD prototype. Vanilla ES2019, data-* config only.
 *
 * Progressive enhancement — with JS disabled the page still sells:
 *   - the server-selected variant is already in the form's hidden id input
 *   - accordion bodies are visible (the [hidden] is removed by JS setup only
 *     for the ones meant to start closed, so no-JS shows everything)
 *   - <noscript> renders ?variant= links for every size
 */
(function () {
  'use strict';

  function initRecord(root) {
    var form = root.querySelector('#crk-product-form') || root.querySelector('form[action*="/cart/add"]');
    var idInput = root.querySelector('[data-crk-variant-id]');
    var buyBtn = root.querySelector('[data-crk-buy]');
    var stockLine = root.querySelector('[data-crk-stockline]');
    var cells = root.querySelectorAll('.crk-size[data-size]');
    var priceEl = root.querySelector('[data-crk-price]');
    var stickyMeta = root.querySelector('[data-crk-sticky-meta]');

    var L = {
      add: root.getAttribute('data-crk-label-add') || 'Add to bag',
      select: root.getAttribute('data-crk-label-select') || 'Select a size',
      sold: root.getAttribute('data-crk-label-sold') || 'SOLD OUT',
      inStock: root.getAttribute('data-crk-label-instock') || 'IN STOCK',
      low: root.getAttribute('data-crk-label-low') || '[n] LEFT IN SIZE [size]',
      soldSize: root.getAttribute('data-crk-label-soldsize') || 'SIZE [size] IS SOLD OUT'
    };

    function setBuy(label, disabled) {
      if (!buyBtn) return;
      buyBtn.textContent = label;
      buyBtn.disabled = !!disabled;
      var sticky = root.querySelector('[data-crk-buybar] button');
      if (sticky) { sticky.textContent = label; sticky.disabled = !!disabled; }
    }

    function select(cell) {
      if (!cell) return;
      var id = cell.getAttribute('data-variant-id');
      var size = cell.getAttribute('data-size');
      var qty = parseInt(cell.getAttribute('data-quantity'), 10);
      var available = cell.getAttribute('data-available') === 'true';
      var price = cell.getAttribute('data-price');

      for (var i = 0; i < cells.length; i++) {
        var on = cells[i] === cell;
        cells[i].setAttribute('data-selected', on ? 'true' : 'false');
        cells[i].setAttribute('aria-pressed', on ? 'true' : 'false');
      }

      // A sold-out size is still selectable — it reveals its state rather than
      // being inert — but it must never become an addable variant.
      if (idInput) idInput.value = available && id ? id : '';
      if (priceEl && price) priceEl.textContent = price;
      if (stickyMeta && price) stickyMeta.textContent = price + (size ? ' · SIZE ' + size : '');

      try {
        var u = new URL(window.location.href);
        if (available && id) u.searchParams.set('variant', id);
        u.searchParams.set('size', size);
        window.history.replaceState(null, '', u.pathname + u.search);
      } catch (e) { /* older browser */ }

      if (stockLine) {
        if (!available) {
          stockLine.textContent = L.soldSize.replace('[size]', size);
          stockLine.setAttribute('data-out', 'true');
        } else if (!isNaN(qty) && qty > 0 && qty <= 3) {
          stockLine.textContent = L.low.replace('[n]', qty).replace('[size]', size);
          stockLine.setAttribute('data-out', 'false');
        } else {
          stockLine.textContent = L.inStock;
          stockLine.setAttribute('data-out', 'false');
        }
      }
      setBuy(available ? L.add : L.sold, !available);

      var rows = root.querySelectorAll('[data-crk-measure-row]');
      for (var r = 0; r < rows.length; r++) {
        var match = rows[r].getAttribute('data-crk-measure-row').toUpperCase() === String(size).toUpperCase();
        rows[r].setAttribute('data-active', match ? 'true' : 'false');
      }
    }

    for (var i = 0; i < cells.length; i++) {
      (function (cell, idx) {
        cell.addEventListener('click', function () { select(cell); });
        cell.addEventListener('keydown', function (e) {
          if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
          e.preventDefault();
          var d = e.key === 'ArrowRight' ? 1 : -1;
          var n = (idx + d + cells.length) % cells.length;
          if (cells[n]) cells[n].focus();
        });
      })(cells[i], i);
    }

    var pre = root.querySelector('.crk-size[data-selected="true"]');
    if (pre) select(pre);
    else if (cells.length) setBuy(L.select, true);

    if (form) {
      form.addEventListener('submit', function (e) {
        if (!idInput || !idInput.value) { e.preventDefault(); setBuy(L.select, true); }
      });
    }

    /* ---- accordions ---- */
    var heads = root.querySelectorAll('[data-crk-accordion]');
    for (var h = 0; h < heads.length; h++) {
      (function (btn) {
        var body = document.getElementById(btn.getAttribute('aria-controls'));
        var icon = btn.querySelector('[data-crk-accordion-icon]');
        function set(open) {
          btn.setAttribute('aria-expanded', open ? 'true' : 'false');
          if (body) body.hidden = !open;
          if (icon) icon.textContent = open ? '−' : '+';
        }
        set(btn.getAttribute('aria-expanded') === 'true');
        btn.addEventListener('click', function () {
          set(btn.getAttribute('aria-expanded') !== 'true');
        });
        btn._crkSet = set;
      })(heads[h]);
    }

    /* ---- size guide opens + scrolls to measurements ---- */
    var guide = root.querySelector('[data-crk-size-guide]');
    if (guide) {
      guide.addEventListener('click', function () {
        var sec = root.querySelector('#crk-measurements');
        var btn = sec && sec.querySelector('[data-crk-accordion]');
        if (btn && btn._crkSet) btn._crkSet(true);
        if (sec) sec.scrollIntoView({ block: 'start' });
      });
    }

    /* ---- cm / in unit toggle ---- */
    var units = root.querySelectorAll('[data-crk-unit]');
    var caption = root.querySelector('[data-crk-measure-caption]');
    function setUnit(unit) {
      for (var u = 0; u < units.length; u++) {
        var on = units[u].getAttribute('data-crk-unit') === unit;
        units[u].setAttribute('data-selected', on ? 'true' : 'false');
        units[u].setAttribute('aria-pressed', on ? 'true' : 'false');
      }
      var tds = root.querySelectorAll('td[data-cm]');
      for (var t = 0; t < tds.length; t++) {
        var cm = tds[t].getAttribute('data-cm');
        if (unit === 'cm') { tds[t].textContent = cm; continue; }
        var n = parseFloat(cm);
        tds[t].textContent = isNaN(n) ? cm : (Math.round((n / 2.54) * 10) / 10) + 'in';
      }
      if (caption) {
        var c = caption.getAttribute(unit === 'cm' ? 'data-cm' : 'data-in');
        if (c) caption.textContent = c;
      }
    }
    for (var u2 = 0; u2 < units.length; u2++) {
      (function (btn) {
        btn.addEventListener('click', function () { setUnit(btn.getAttribute('data-crk-unit')); });
      })(units[u2]);
    }

    /* ---- gallery ---- */
    var slides = root.querySelectorAll('[data-crk-slide]');
    var thumbs = root.querySelectorAll('[data-crk-thumb]');
    var counter = root.querySelector('[data-crk-photo-counter]');
    var counterTpl = root.getAttribute('data-crk-photo-label') || 'Photo [i] of [n]';
    var idx = 0;
    function show(n) {
      if (n < 0 || n >= slides.length) return;
      idx = n;
      for (var s = 0; s < slides.length; s++) slides[s].hidden = s !== n;
      for (var t = 0; t < thumbs.length; t++) thumbs[t].setAttribute('data-active', t === n ? 'true' : 'false');
      if (counter) counter.textContent = counterTpl.replace('[i]', n + 1).replace('[n]', slides.length);
    }
    for (var t2 = 0; t2 < thumbs.length; t2++) {
      (function (btn, i2) { btn.addEventListener('click', function () { show(i2); }); })(thumbs[t2], t2);
    }
    var tray = root.querySelector('[data-crk-gallery]');
    if (tray && slides.length > 1) {
      tray.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowRight') { e.preventDefault(); show(Math.min(idx + 1, slides.length - 1)); }
        if (e.key === 'ArrowLeft') { e.preventDefault(); show(Math.max(idx - 1, 0)); }
      });
      var tx = null;
      tray.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; }, { passive: true });
      tray.addEventListener('touchend', function (e) {
        if (tx == null) return;
        var dx = e.changedTouches[0].clientX - tx;
        if (Math.abs(dx) > 40) show(dx < 0 ? Math.min(idx + 1, slides.length - 1) : Math.max(idx - 1, 0));
        tx = null;
      });
    }

    /* ---- sticky bar: mobile only, only while the primary control is off-screen ---- */
    var bar = root.querySelector('[data-crk-buybar]');
    var spacer = root.querySelector('[data-crk-sticky-spacer]');
    if (bar && buyBtn && 'IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (en) {
        var off = !en[0].isIntersecting;
        bar.hidden = !off;
        if (spacer) spacer.hidden = !off;
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
