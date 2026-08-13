/* CROOKSLDN — typeahead for the query bar.

   Products come from /search/suggest.json, which is Shopify's own suggestion
   endpoint and needs no app. Pages come from the curated link list rendered
   into [data-crk-linkdata] as attributes: Shopify does not index /policies/*,
   and it cannot index Terms or FAQ either, because their text lives in section
   settings rather than in page.content. Matching those in the browser is the
   only way "refund" reaches the refund policy.

   Progressive enhancement: the form submits normally with this file absent. */
(function () {
  'use strict';

  var root = document.querySelector('[data-crk-section="search-bar"]');
  if (!root) return;

  var input = root.querySelector('#crk-q');
  var box = root.querySelector('[data-crk-suggest]');
  var form = root.querySelector('.crk-query__form');
  if (!input || !box || !form) return;

  var headingProducts = box.getAttribute('data-crk-heading-products') || 'ITEMS';
  var headingLinks = box.getAttribute('data-crk-heading-links') || 'PAGES';

  var links = [];
  var nodes = root.querySelectorAll('[data-crk-linkdata] li');
  for (var i = 0; i < nodes.length; i++) {
    links.push({
      label: nodes[i].getAttribute('data-label') || '',
      url: nodes[i].getAttribute('data-url') || '#',
      note: nodes[i].getAttribute('data-note') || '',
      keywords: (nodes[i].getAttribute('data-keywords') || '').split(','),
      newTab: nodes[i].getAttribute('data-new-tab') === 'true'
    });
  }

  var timer = null;
  var lastQuery = '';
  var controller = null;
  var items = [];      // flat list of anchors, for keyboard traversal
  var active = -1;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function close() {
    box.hidden = true;
    box.innerHTML = '';
    items = [];
    active = -1;
    input.setAttribute('aria-expanded', 'false');
  }

  function matchLinks(q) {
    var out = [];
    for (var i = 0; i < links.length; i++) {
      var keys = links[i].keywords;
      for (var k = 0; k < keys.length; k++) {
        var key = keys[k].trim();
        if (key && (q.indexOf(key) !== -1 || key.indexOf(q) === 0)) { out.push(links[i]); break; }
      }
      if (out.length >= 5) break;
    }
    return out;
  }

  function render(products, matched) {
    if (!products.length && !matched.length) { close(); return; }

    var html = '';
    if (matched.length) {
      html += '<p class="crk-suggest__head crk-eyebrow">' + esc(headingLinks) + '</p><ul>';
      for (var i = 0; i < matched.length; i++) {
        var l = matched[i];
        html += '<li><a class="crk-suggest__row" role="option" href="' + esc(l.url) + '"' +
          (l.newTab ? ' target="_blank" rel="noopener noreferrer"' : '') + '>' +
          '<span class="crk-suggest__label">' + esc(l.label) + '</span>' +
          (l.note ? '<span class="crk-suggest__note">' + esc(l.note) + '</span>' : '') +
          '</a></li>';
      }
      html += '</ul>';
    }
    if (products.length) {
      html += '<p class="crk-suggest__head crk-eyebrow">' + esc(headingProducts) + '</p><ul>';
      for (var p = 0; p < products.length; p++) {
        var it = products[p];
        html += '<li><a class="crk-suggest__row" role="option" href="' + esc(it.url) + '">' +
          (it.image ? '<img class="crk-suggest__img" src="' + esc(it.image) + '" alt="" width="40" height="40" loading="lazy">' : '<span class="crk-suggest__img"></span>') +
          '<span class="crk-suggest__label">' + esc(it.title) + '</span>' +
          (it.price ? '<span class="crk-suggest__note">' + esc(it.price) + '</span>' : '') +
          '</a></li>';
      }
      html += '</ul>';
    }

    box.innerHTML = html;
    box.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    items = box.querySelectorAll('.crk-suggest__row');
    active = -1;
  }

  // suggest.json returns price as a decimal string ("25.00") with no symbol, so
  // the shop's own money format is handed over in a data attribute.
  var moneyFormat = box.getAttribute('data-crk-money-format') || '£{{amount}}';
  function money(value) {
    var n = parseFloat(value);
    if (isNaN(n)) return '';
    var amount = (n % 1 === 0) ? n.toFixed(0) : n.toFixed(2);
    return moneyFormat.replace(/\{\{\s*amount[^}]*\}\}/, amount);
  }

  function thumb(url) {
    if (!url) return '';
    return url + (url.indexOf('?') === -1 ? '?' : '&') + 'width=80';
  }

  function fetchProducts(q, matched) {
    if (controller) controller.abort();
    controller = ('AbortController' in window) ? new AbortController() : null;

    var url = '/search/suggest.json?q=' + encodeURIComponent(q) +
      '&resources[type]=product,page&resources[limit]=6' +
      '&resources[options][unavailable_products]=last';

    fetch(url, controller ? { signal: controller.signal } : undefined)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || input.value.trim().toLowerCase() !== q) return;
        var results = (data.resources && data.resources.results) || {};
        var products = (results.products || []).map(function (p) {
          return {
            title: p.title,
            url: p.url,
            image: thumb(p.featured_image && p.featured_image.url),
            price: money(p.price)
          };
        });

        // Indexed pages join the curated links, deduped on destination.
        var seen = {};
        var all = matched.slice();
        for (var m = 0; m < all.length; m++) seen[all[m].url.split('?')[0]] = true;
        var pages = results.pages || [];
        for (var g = 0; g < pages.length && all.length < 6; g++) {
          var key = (pages[g].url || '').split('?')[0];
          if (seen[key]) continue;
          seen[key] = true;
          all.push({ label: pages[g].title, url: pages[g].url, note: '', newTab: false });
        }
        render(products, all);
      })
      .catch(function () {
        // Network failure or an aborted keystroke: the curated links still stand.
        render([], matched);
      });
  }

  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-autocomplete', 'list');
  input.setAttribute('aria-controls', 'crk-suggest');
  input.setAttribute('aria-expanded', 'false');

  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    if (q === lastQuery) return;
    lastQuery = q;
    if (timer) clearTimeout(timer);
    if (q.length < 2) { close(); return; }
    timer = setTimeout(function () { fetchProducts(q, matchLinks(q)); }, 180);
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { close(); return; }
    if (!items.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      active += (e.key === 'ArrowDown') ? 1 : -1;
      if (active < 0) active = items.length - 1;
      if (active >= items.length) active = 0;
      for (var i = 0; i < items.length; i++) items[i].setAttribute('data-active', i === active ? 'true' : 'false');
      items[active].focus();
    }
  });

  box.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { close(); input.focus(); }
  });

  document.addEventListener('click', function (e) {
    if (!root.contains(e.target)) close();
  });

  form.addEventListener('submit', close);
})();
