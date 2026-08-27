/* CROOKSLDN — change a size from the cart.
 *
 * A shopper who picked the wrong size had no way to say so here: the cart
 * printed the size as read-only text, so the only routes were delete-and-start-
 * again or carry on and hope. One audit shopper worked around it and came
 * within a tap of checking out a £50 basket in the wrong size.
 *
 * Progressive enhancement, deliberately. Nothing in Horizon's cart markup is
 * touched; this finds the read-only variant list and adds a control beside it.
 * If this file never loads the cart is exactly what it was.
 *
 * Shopify's cart API cannot change a line's variant, so a swap is add-the-new
 * then remove-the-old. That order matters: if the new size turns out to be gone
 * between rendering and tapping, the add fails and the shopper still has what
 * they had. Doing it the other way round can empty a line and then fail to
 * refill it.
 *
 * Bundles are excluded for free — Horizon renders no variant list for a line
 * with components, so there is nothing here to attach to. Their sizes are two
 * options on one line and swapping them is a different problem.
 */
(function () {
  'use strict';

  var host = document.querySelector('[data-crk-cart-size]');
  if (!host) return;

  var L = {
    change: host.getAttribute('data-label-change') || 'CHANGE SIZE',
    close: host.getAttribute('data-label-close') || 'KEEP THIS SIZE',
    legend: host.getAttribute('data-label-legend') || 'Change size',
    gone: host.getAttribute('data-label-gone') || 'GONE',
    failed: host.getAttribute('data-label-failed') || 'That size just went. Nothing has changed in your bag.',
    working: host.getAttribute('data-label-working') || 'CHANGING…'
  };

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (d) { return { ok: r.ok, data: d }; });
    });
  }

  /* The size option is found by name, the same rule the register and the
     related rail use: an option actually called size. The socks' "Quantity"
     and one-size pieces are left alone. */
  function sizeIndex(names) {
    for (var i = 0; i < names.length; i++) {
      if (String(names[i]).toLowerCase().indexOf('size') > -1) return i;
    }
    return -1;
  }

  function build(row, line) {
    var wrap = row.querySelector('.cart-items__variants-wrapper');
    var list = row.querySelector('.cart-items__variants');
    if (!wrap || !list) return;

    var idx = sizeIndex(line.options_with_values.map(function (o) { return o.name; }));
    if (idx < 0) return;

    var open = false;
    var panel = null;

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'crk-cartsize__toggle';
    toggle.textContent = L.change;
    toggle.setAttribute('aria-expanded', 'false');

    var note = document.createElement('p');
    note.className = 'crk-cartsize__note';
    note.hidden = true;

    function say(msg) { note.textContent = msg; note.hidden = !msg; }

    function shut() {
      open = false;
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = L.change;
      if (panel) { panel.remove(); panel = null; }
    }

    function swap(newId, btn) {
      /* Add first. If the target is gone the bag is untouched and the shopper
         keeps what they had. */
      btn.disabled = true;
      var was = btn.textContent;
      btn.textContent = L.working;
      say('');
      post('/cart/add.js', { items: [{ id: newId, quantity: line.quantity }] })
        .then(function (res) {
          if (!res.ok) throw new Error('add');
          return post('/cart/change.js', { id: line.key, quantity: 0 });
        })
        .then(function (res) {
          if (!res.ok) throw new Error('remove');
          /* A full reload rather than morphing Horizon's cart in place: this is
             the one page where being certainly right beats being smooth. */
          window.location.reload();
        })
        .catch(function () {
          btn.disabled = false;
          btn.textContent = was;
          say(L.failed);
        });
    }

    function draw(product) {
      panel = document.createElement('div');
      panel.className = 'crk-cartsize__panel';
      var legend = document.createElement('p');
      legend.className = 'crk-cartsize__legend';
      legend.textContent = L.legend;
      panel.appendChild(legend);

      var row2 = document.createElement('div');
      row2.className = 'crk-cartsize__sizes';

      var current = line.options_with_values[idx].value;
      var seen = {};
      product.variants.forEach(function (v) {
        var val = v.options[idx];
        if (val == null || seen[val]) return;
        /* Only variants matching every OTHER option, so a tee in black does not
           offer sizes that only exist in white. */
        var matches = line.options_with_values.every(function (o, i) {
          return i === idx || v.options[i] === o.value;
        });
        if (!matches) return;
        seen[val] = true;

        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'crk-size crk-cartsize__size';
        b.textContent = val;
        if (val === current) {
          b.setAttribute('aria-pressed', 'true');
          b.disabled = true;
        } else if (!v.available) {
          b.setAttribute('aria-disabled', 'true');
          b.disabled = true;
          b.title = L.gone;
        } else {
          b.addEventListener('click', function () { swap(v.id, b); });
        }
        row2.appendChild(b);
      });

      panel.appendChild(row2);
      wrap.appendChild(panel);
      var first = panel.querySelector('button:not([disabled])');
      if (first) first.focus();
    }

    toggle.addEventListener('click', function () {
      if (open) { shut(); return; }
      open = true;
      toggle.setAttribute('aria-expanded', 'true');
      toggle.textContent = L.close;
      say('');
      /* Fetched on open, not on load: a cart of six lines should not make six
         requests for panels nobody opened. */
      fetch('/products/' + line.handle + '.js', { headers: { Accept: 'application/json' } })
        .then(function (r) { return r.json(); })
        .then(draw)
        .catch(function () { shut(); say(L.failed); });
    });

    wrap.appendChild(toggle);
    wrap.appendChild(note);
  }

  fetch('/cart.js', { headers: { Accept: 'application/json' } })
    .then(function (r) { return r.json(); })
    .then(function (cart) {
      var byKey = {};
      cart.items.forEach(function (i) { byKey[i.key] = i; });
      var rows = document.querySelectorAll('.cart-items__table-row[data-key]');
      for (var i = 0; i < rows.length; i++) {
        var line = byKey[rows[i].getAttribute('data-key')];
        if (line && line.options_with_values && line.options_with_values.length) build(rows[i], line);
      }
    })
    .catch(function () { /* leave the cart exactly as rendered */ });
})();
