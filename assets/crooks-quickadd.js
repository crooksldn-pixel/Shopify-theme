/*
 * CROOKSLDN — quick add on the catalogue card.
 *
 * Pick a size on the card, press the button, the variant lands in the bag.
 * No page load, no trip to the product page, no guessing.
 *
 * WHAT IT WILL NOT DO. A size only names a variant when the product has one
 * option. A tee sold in black and white has two variants wearing "M", and a
 * quick add that picked one would post a garment nobody chose — the kind of
 * wrong order that costs the sale twice, once in the refund and once in the
 * trust. Those sizes are marked data-crk-qa-choose in Liquid and the button
 * opens the product page with the size carried over, saying so on its face.
 *
 * The bag count is repainted through window.crkBag, the same rule the product
 * page and the set toggle use, because a bundle line holds two garments and
 * cart.item_count cannot see that.
 *
 * There is no cart drawer on this storefront — BAG is a link to /cart — so a
 * successful add confirms in place rather than opening something that does not
 * exist.
 *
 * Progressive enhancement: without this file the buttons stay as Liquid drew
 * them, disabled, and the card is still a working link to the product.
 */
(function () {
  'use strict';

  var cards = document.querySelectorAll('[data-crk-qa]');
  if (!cards.length) return;

  function setMsg(el, text, isError) {
    if (!el) return;
    if (!text) { el.hidden = true; el.textContent = ''; return; }
    el.textContent = text;
    el.setAttribute('data-crk-qa-out', isError ? 'true' : 'false');
    el.hidden = false;
  }

  function init(card) {
    var btn = card.querySelector('[data-crk-qa-btn]');
    if (!btn) return;
    var msg = card.querySelector('[data-crk-qa-msg]');
    var sizes = card.querySelectorAll('[data-crk-qa-size]');
    var url = card.getAttribute('data-crk-qa-url') || '';

    var L = {
      add: btn.getAttribute('data-crk-qa-add') || 'QUICK ADD',
      select: btn.getAttribute('data-crk-qa-select') || 'SELECT SIZE',
      choose: btn.getAttribute('data-crk-qa-choose') || 'CHOOSE OPTIONS',
      busy: btn.getAttribute('data-crk-qa-busy') || 'ADDING',
      done: btn.getAttribute('data-crk-qa-done') || 'ADDED',
      error: btn.getAttribute('data-crk-qa-error') || 'COULD NOT ADD'
    };

    /* Sold out as a whole: Liquid already disabled the button and there is no
       size to choose. Nothing to wire up. */
    if (btn.getAttribute('data-crk-qa-state') === 'sold') return;

    var chosen = null;      /* the pressed size button, not just its value */
    var busy = false;

    /* A product with no size option — socks by quantity, one-size pieces —
       arrives ready, with its variant already on the button. */
    var soloVariant = btn.getAttribute('data-crk-qa-variant');

    function paint() {
      if (busy) return;
      if (!sizes.length) {
        btn.disabled = !soloVariant;
        btn.textContent = L.add;
        btn.setAttribute('data-crk-qa-state', soloVariant ? 'ready' : 'need-size');
        return;
      }
      if (!chosen) {
        btn.disabled = true;
        btn.textContent = L.select;
        btn.setAttribute('data-crk-qa-state', 'need-size');
        return;
      }
      btn.disabled = false;
      if (chosen.getAttribute('data-crk-qa-choose') === 'true') {
        btn.textContent = L.choose;
        btn.setAttribute('data-crk-qa-state', 'choose');
      } else {
        btn.textContent = L.add;
        btn.setAttribute('data-crk-qa-state', 'ready');
      }
    }

    for (var i = 0; i < sizes.length; i++) {
      (function (b) {
        b.addEventListener('click', function () {
          /* aria-disabled rather than disabled: a sold-out size stays in the
             tab order so it can be read, it simply cannot be chosen. */
          if (b.getAttribute('aria-disabled') === 'true') return;
          if (busy) return;
          for (var k = 0; k < sizes.length; k++) sizes[k].setAttribute('aria-pressed', 'false');
          b.setAttribute('aria-pressed', 'true');
          chosen = b;
          setMsg(msg, '');
          paint();
        });
      })(sizes[i]);
    }

    btn.addEventListener('click', function () {
      if (busy || btn.disabled) return;

      /* The second decision is still open. Hand it to the product page with the
         size already picked, rather than choosing a colourway on their behalf. */
      if (chosen && chosen.getAttribute('data-crk-qa-choose') === 'true') {
        var size = chosen.getAttribute('data-crk-qa-size') || '';
        window.location.assign(url + (url.indexOf('?') > -1 ? '&' : '?') +
          'crk-size=' + encodeURIComponent(size));
        return;
      }

      var id = chosen ? chosen.getAttribute('data-crk-qa-variant') : soloVariant;
      if (!id) return;

      busy = true;
      btn.disabled = true;
      btn.setAttribute('data-crk-qa-state', 'busy');
      btn.textContent = L.busy;
      setMsg(msg, '');

      fetch('/cart/add.js', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ items: [{ id: id, quantity: 1 }] })
      })
        .then(function (r) {
          return r.json().then(function (j) { return { ok: r.ok, j: j }; });
        })
        .then(function (res) {
          if (!res.ok) {
            /* Shopify names the real reason — sold out, quantity limit. Say
               that rather than a generic failure: the shopper can act on it. */
            throw new Error((res.j && res.j.description) || L.error);
          }
          /* The add has already happened. A failure to read the count back is
             not a failed add, so it must not fall through to the error branch. */
          var read = window.crkBag ? window.crkBag.refresh() : Promise.resolve(null);
          return read.catch(function () { return null; });
        })
        .then(function () {
          busy = false;
          btn.setAttribute('data-crk-qa-state', 'done');
          btn.textContent = L.done;
          setMsg(msg, '');
          /* Back to a normal armed button shortly after, so the card does not
             sit there claiming a success that has scrolled out of mind. The
             chosen size is deliberately kept — they may want a second one. */
          window.setTimeout(function () {
            if (busy) return;
            paint();
          }, 2200);
        })
        .catch(function (e) {
          /* The selection survives a failure: making them pick the size again
             to retry is punishing them for our error. */
          busy = false;
          btn.setAttribute('data-crk-qa-state', 'error');
          setMsg(msg, (e && e.message) || L.error, true);
          paint();
        });
    });

    paint();
  }

  for (var c = 0; c < cards.length; c++) init(cards[c]);
})();
