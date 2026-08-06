/*
 * CROOKSLDN — light / dark theme control.
 * Ported from THE EXHIBIT RECORD prototype's ThemeToggle.jsx and generalised
 * to the whole site: the attribute lives on <html>, so every .crk-root on the
 * page (header, homepage sections, PDP, footer) follows one switch.
 *
 * The attribute is set by a tiny inline script in theme.liquid <head> so the
 * correct theme is painted on first frame. This file only handles the button.
 *
 * Persistence matches the prototype: sessionStorage, key 'crk-theme'.
 */
(function () {
  'use strict';

  var KEY = 'crk-theme';

  function current() {
    return document.documentElement.getAttribute('data-crk-theme') === 'light' ? 'light' : 'dark';
  }

  function label(btn, theme) {
    // The button says what it will DO, matching the prototype.
    var toLight = btn.getAttribute('data-crk-to-light') || 'LIGHT MODE';
    var toDark = btn.getAttribute('data-crk-to-dark') || 'DARK MODE';
    btn.textContent = theme === 'dark' ? toLight : toDark;
    btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
  }

  function apply(theme) {
    document.documentElement.setAttribute('data-crk-theme', theme);
    try { sessionStorage.setItem(KEY, theme); } catch (e) { /* private mode */ }
    var btns = document.querySelectorAll('[data-crk-theme-toggle]');
    for (var i = 0; i < btns.length; i++) label(btns[i], theme);
  }

  function init(btn) {
    label(btn, current());
    btn.hidden = false;
    btn.addEventListener('click', function () {
      apply(current() === 'dark' ? 'light' : 'dark');
    });
  }

  function mountAll(scope) {
    var root = scope && scope.querySelectorAll ? scope : document;
    var btns = root.querySelectorAll('[data-crk-theme-toggle]');
    for (var i = 0; i < btns.length; i++) {
      if (!btns[i]._crkTheme) { btns[i]._crkTheme = true; init(btns[i]); }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else {
    mountAll(document);
  }
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
})();
