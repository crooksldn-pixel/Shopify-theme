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
    var priceEl = root.querySelector('[data-crk-price]');
    var stickyMeta = root.querySelector('[data-crk-sticky-meta]');
    // Variant-level restock capture: hidden until the chosen variant is the sold-out one.
    var notifyPanel = root.querySelector('[data-crk-notify-panel]');
    var notifyVariant = root.querySelector('[data-crk-notify-variant]');
    var deliveryLine = root.querySelector('[data-crk-delivery]');

    var L = {
      add: root.getAttribute('data-crk-label-add') || 'Add to bag',
      select: root.getAttribute('data-crk-label-select') || 'Select a size',
      selectOption: root.getAttribute('data-crk-label-select-option') || 'Select [option]',
      sold: root.getAttribute('data-crk-label-sold') || 'SOLD OUT',
      inStock: root.getAttribute('data-crk-label-instock') || 'IN STOCK',
      low: root.getAttribute('data-crk-label-low') || '[n] LEFT IN SIZE [size]',
      soldSize: root.getAttribute('data-crk-label-soldsize') || 'SIZE [size] IS SOLD OUT'
    };
    var LOW = parseInt(root.getAttribute('data-crk-low-threshold'), 10) || 3;

    function setBuy(label, disabled) {
      if (!buyBtn) return;
      buyBtn.textContent = label;
      buyBtn.disabled = !!disabled;
      var sticky = root.querySelector('[data-crk-buybar] button');
      if (sticky) { sticky.textContent = label; sticky.disabled = !!disabled; }
    }

    /* ---- variant matrix, read from DOM data (never a Liquid JSON blob) ---- */
    var variants = [];
    var vnodes = root.querySelectorAll('[data-crk-variants] span');
    for (var vi = 0; vi < vnodes.length; vi++) {
      var vn = vnodes[vi];
      variants.push({
        id: vn.getAttribute('data-id'),
        opts: [vn.getAttribute('data-o1') || '', vn.getAttribute('data-o2') || '', vn.getAttribute('data-o3') || ''],
        available: vn.getAttribute('data-available') === 'true',
        qty: parseInt(vn.getAttribute('data-qty'), 10) || 0,
        price: vn.getAttribute('data-price') || ''
      });
    }

    var groups = root.querySelectorAll('[data-crk-optgroup]');
    var nOpts = groups.length;
    var selected = [];
    for (var gi = 0; gi < nOpts; gi++) {
      var pre = groups[gi].querySelector('.crk-size[data-selected="true"]');
      selected.push(pre ? pre.getAttribute('data-value') : null);
    }

    // A candidate selection matches a variant when every CHOSEN option agrees.
    function match(sel) {
      for (var i = 0; i < variants.length; i++) {
        var ok = true;
        for (var o = 0; o < nOpts; o++) {
          if (sel[o] !== null && variants[i].opts[o] !== sel[o]) { ok = false; break; }
        }
        if (ok) return variants[i];
      }
      return null;
    }
    // Is any AVAILABLE variant reachable if this option took this value,
    // holding the other current selections?
    function reachable(optIndex, value) {
      for (var i = 0; i < variants.length; i++) {
        var v = variants[i];
        if (!v.available) continue;
        if (v.opts[optIndex] !== value) continue;
        var ok = true;
        for (var o = 0; o < nOpts; o++) {
          if (o === optIndex) continue;
          if (selected[o] !== null && v.opts[o] !== selected[o]) { ok = false; break; }
        }
        if (ok) return true;
      }
      return false;
    }
    // The variant this value would resolve to, given the other selections.
    function resolveFor(optIndex, value) {
      var probe = selected.slice();
      probe[optIndex] = value;
      return match(probe);
    }

    function firstMissingOptionName() {
      for (var o = 0; o < nOpts; o++) {
        if (selected[o] === null) return groups[o].getAttribute('data-crk-optname') || '';
      }
      return '';
    }

    function render() {
      for (var g = 0; g < nOpts; g++) {
        var btns = groups[g].querySelectorAll('.crk-size');
        for (var b = 0; b < btns.length; b++) {
          var btn = btns[b], val = btn.getAttribute('data-value');
          var on = selected[g] === val;
          btn.setAttribute('data-selected', on ? 'true' : 'false');
          btn.setAttribute('aria-pressed', on ? 'true' : 'false');
          // Buyability from variant.available, never from the count.
          if (reachable(g, val)) btn.removeAttribute('aria-disabled');
          else btn.setAttribute('aria-disabled', 'true');
          var rv = resolveFor(g, val);
          var low = !!(rv && rv.available && rv.qty > 0 && rv.qty <= LOW);
          btn.setAttribute('data-low', low ? 'true' : 'false');
        }
      }

      var complete = true;
      for (var o = 0; o < nOpts; o++) { if (selected[o] === null) { complete = false; break; } }
      var v = complete ? match(selected) : null;

      if (idInput) idInput.value = (v && v.available) ? v.id : '';
      if (priceEl && v && v.price) priceEl.textContent = v.price;
      if (stickyMeta && v && v.price) {
        var chosen = selected.filter(function (x) { return x; }).join(' · ');
        stickyMeta.textContent = v.price + (chosen ? ' · ' + chosen : '');
      }

      if (stockLine) {
        if (!complete) {
          var nm = firstMissingOptionName();
          stockLine.textContent = nm ? L.selectOption.replace('[option]', nm) : L.select;
          stockLine.setAttribute('data-out', 'false');
        } else if (!v || !v.available) {
          var label = selected[selected.length - 1] || '';
          stockLine.textContent = L.soldSize.replace('[size]', label);
          stockLine.setAttribute('data-out', 'true');
        } else if (v.qty > 0 && v.qty <= LOW) {
          stockLine.textContent = L.low.replace('[n]', v.qty).replace('[size]', selected.join(' / '));
          stockLine.setAttribute('data-out', 'false');
        } else {
          stockLine.textContent = L.inStock;
          stockLine.setAttribute('data-out', 'false');
        }
      }

      if (!complete) setBuy(L.select, true);
      else if (v && v.available) setBuy(L.add, false);
      else setBuy(L.sold, true);

      // The notify form appears only once a full option set is chosen and that
      // combination is unavailable — never while the shopper is still mid-choice.
      var soldChoice = complete && (!v || !v.available);
      if (notifyPanel) {
        notifyPanel.hidden = !soldChoice;
        if (soldChoice && notifyVariant) {
          notifyVariant.value = selected.filter(function (x) { return x; }).join(' / ');
        }
      }
      // A dispatch promise must not sit under a sold-out line.
      if (deliveryLine) deliveryLine.hidden = soldChoice;

      if (v && v.available) {
        try {
          var u = new URL(window.location.href);
          u.searchParams.set('variant', v.id);
          window.history.replaceState(null, '', u.pathname + u.search);
        } catch (e) { /* older browser */ }
      }

      // highlight the measurements row matching whichever chosen value names a size
      var rows = root.querySelectorAll('[data-crk-measure-row]');
      for (var r = 0; r < rows.length; r++) {
        var key = rows[r].getAttribute('data-crk-measure-row').toUpperCase();
        var hit = false;
        for (var sIdx = 0; sIdx < selected.length; sIdx++) {
          if (selected[sIdx] && String(selected[sIdx]).toUpperCase() === key) { hit = true; break; }
        }
        rows[r].setAttribute('data-active', hit ? 'true' : 'false');
      }
    }

    for (var gg = 0; gg < nOpts; gg++) {
      (function (group, gIndex) {
        var btns = group.querySelectorAll('.crk-size');
        for (var k = 0; k < btns.length; k++) {
          (function (btn, kIndex) {
            btn.addEventListener('click', function () {
              // A sold-out value is still selectable so its state can be read,
              // but render() will refuse to arm the form for it.
              selected[gIndex] = btn.getAttribute('data-value');
              render();
            });
            btn.addEventListener('keydown', function (e) {
              if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
              e.preventDefault();
              var d = e.key === 'ArrowRight' ? 1 : -1;
              var n = (kIndex + d + btns.length) % btns.length;
              if (btns[n]) btns[n].focus();
            });
          })(btns[k], k);
        }
      })(groups[gg], gg);
    }

    if (nOpts) render();

    if (form) {
      form.addEventListener('submit', function (e) {
        if (!idInput || !idInput.value) { e.preventDefault(); render(); }
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
