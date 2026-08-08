/*
 * CROOKSLDN — terminal section behaviours.
 * Vanilla ES2019, no build step, no dependencies. All configuration arrives via
 * data-* attributes on section roots, so no Liquid ever appears inside a <script>
 * and this file stays cacheable.
 *
 * Progressive enhancement throughout — with JS disabled:
 *   status bar  : first message shows (the bar clips the rest)
 *   hero boot   : lines render as plain text, already legible
 *   exhibit log : every card renders; filter buttons simply do nothing
 */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- status bar: rotate messages ---------- */
  function initStatusBar(root) {
    var msgs = root.querySelectorAll('.crk-status__msg');
    if (msgs.length < 2) return;
    for (var i = 1; i < msgs.length; i++) msgs[i].hidden = true;
    if (reduced || root.getAttribute('data-crk-rotate') === 'false') return;

    var interval = parseInt(root.getAttribute('data-crk-interval'), 10);
    if (!interval || interval < 1000) interval = 8000;
    var idx = 0, paused = false;

    root.addEventListener('mouseenter', function () { paused = true; });
    root.addEventListener('mouseleave', function () { paused = false; });

    var timer = setInterval(function () {
      if (paused || document.hidden) return;
      msgs[idx].hidden = true;
      idx = (idx + 1) % msgs.length;
      msgs[idx].hidden = false;
    }, interval);
    root._crkTimer = timer;
  }

  /* ---------- hero: boot line typing ---------- */
  function initBoot(root) {
    var lines = root.querySelectorAll('.crk-boot__line');
    var mark = root.querySelector('.crk-hero__mark');
    if (!lines.length) return;

    // Type once per session, and never under reduced motion.
    var skip = reduced;
    try { if (sessionStorage.getItem('crk_booted')) skip = true; } catch (e) { /* storage blocked */ }
    if (skip) return;

    if (mark) mark.classList.add('crk-wait');
    var texts = [];
    for (var i = 0; i < lines.length; i++) {
      texts.push(lines[i].textContent.trim());
      lines[i].textContent = ' ';
    }

    var li = 0, timers = [];
    function done() {
      try { sessionStorage.setItem('crk_booted', '1'); } catch (e) { /* storage blocked */ }
      if (mark) mark.classList.remove('crk-wait');
    }
    function typeLine() {
      if (li >= lines.length) { done(); return; }
      var el = lines[li], text = texts[li], ci = 0;
      var tick = Math.max(16, Math.floor(450 / Math.max(1, text.length)));
      el.textContent = ' ';
      var t = setInterval(function () {
        ci += 1;
        el.textContent = text.slice(0, ci);
        if (ci >= text.length) { clearInterval(t); li += 1; typeLine(); }
      }, tick);
      timers.push(t);
    }
    typeLine();
    root._crkBootTimers = timers;
  }

  /* ---------- exhibit log: client-side category filter ---------- */
  function initLog(root) {
    // Scoped to [data-crk-filter]: the view-mode buttons share the .crk-filter
    // class so they look identical, but they are not category filters. A bare
    // .crk-filter selector picked them up here and a click on PRODUCT/MODEL ran
    // apply(null), which matched no category and hid every cell.
    var buttons = root.querySelectorAll('.crk-filter[data-crk-filter]');
    var cells = root.querySelectorAll('.crk-log__cell');
    var empty = root.querySelector('.crk-log__empty');
    if (!buttons.length || !cells.length) return;

    function apply(cat) {
      var shown = 0;
      for (var i = 0; i < cells.length; i++) {
        var match = cat === 'ALL' || cells[i].getAttribute('data-crk-category') === cat;
        cells[i].hidden = !match;
        if (match) shown++;
      }
      for (var b = 0; b < buttons.length; b++) {
        var on = buttons[b].getAttribute('data-crk-filter') === cat;
        buttons[b].setAttribute('aria-pressed', on ? 'true' : 'false');
      }
      if (empty) empty.hidden = shown !== 0;
    }

    for (var b = 0; b < buttons.length; b++) {
      buttons[b].addEventListener('click', function (e) {
        apply(e.currentTarget.getAttribute('data-crk-filter'));
      });
    }
    if (empty) empty.hidden = true;
  }

  /* ---------- catalogue view mode: PRODUCT / MODEL ---------- */
  function initViews(root) {
    var btns = root.querySelectorAll('[data-crk-view-btn]');
    if (!btns.length) return;
    function apply(view) {
      root.setAttribute('data-crk-view', view);
      for (var i = 0; i < btns.length; i++) {
        var on = btns[i].getAttribute('data-crk-view-btn') === view;
        btns[i].setAttribute('aria-pressed', on ? 'true' : 'false');
      }
    }
    for (var b = 0; b < btns.length; b++) {
      btns[b].addEventListener('click', function (e) {
        apply(e.currentTarget.getAttribute('data-crk-view-btn'));
      });
    }
    apply(root.getAttribute('data-crk-view') || 'product');
  }

  /* ---------- product image outline: evaluation toggle ---------- */
  function initOutline(root) {
    var btn = root.querySelector('[data-crk-outline-btn]');
    if (!btn) return;
    var el = document.documentElement;

    // Session choice wins; otherwise the section's configured default. Stored
    // rather than held in memory so the product page inherits the same choice.
    var stored = null;
    try { stored = sessionStorage.getItem('crk-outline'); } catch (e) {}
    var on = stored ? stored !== 'off' : btn.getAttribute('data-crk-outline-default') !== 'off';

    function apply(next) {
      on = next;
      if (on) el.removeAttribute('data-crk-outline');
      else el.setAttribute('data-crk-outline', 'off');
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      try { sessionStorage.setItem('crk-outline', on ? 'on' : 'off'); } catch (e) {}
    }
    btn.addEventListener('click', function () { apply(!on); });
    apply(on);
  }

  /* ---------- boot ---------- */
  var INIT = [
    ['[data-crk-section="status-bar"]', initStatusBar],
    ['[data-crk-section="hero-intake"]', initBoot],
    ['[data-crk-section="exhibit-log"]', initLog],
    ['[data-crk-section="exhibit-log"]', initViews],
    ['[data-crk-section="exhibit-log"]', initOutline]
  ];

  function mountAll(scope) {
    var root = scope && scope.querySelectorAll ? scope : document;
    for (var i = 0; i < INIT.length; i++) {
      var sel = INIT[i][0], fn = INIT[i][1];
      // Flag is per-initialiser, not per-element: two entries can share a
      // selector (the exhibit log runs both initLog and initViews) and a single
      // shared flag would silently skip the second one.
      var key = '_crkInit' + i;
      var nodes = root.querySelectorAll(sel);
      for (var n = 0; n < nodes.length; n++) {
        if (!nodes[n][key]) { nodes[n][key] = true; fn(nodes[n]); }
      }
      if (root.matches && root.matches(sel) && !root[key]) {
        root[key] = true; fn(root);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else {
    mountAll(document);
  }
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
})();
