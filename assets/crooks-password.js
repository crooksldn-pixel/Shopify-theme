/*
 * CROOKSLDN — the lock-up (password / holding page).
 *
 * Drives three things off one clock:
 *   1. the countdown digits,
 *   2. the drill-depth bar and the vault dial angle,
 *   3. the waiting counter.
 *
 * Vanilla ES5-safe. No dependencies, no build step. Everything it needs
 * arrives on data- attributes from the section, because Liquid is not
 * allowed inside a script tag in this theme.
 *
 * THE TARGET IS ABSOLUTE. The section computes it in Liquid from the shop's
 * London clock and hands it over as a Unix timestamp, so this file never
 * has to know what timezone anybody is in — it subtracts and formats.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-crk-section="password"]');
  if (!root) return;

  var target = parseInt(root.getAttribute('data-crk-target'), 10) * 1000;
  if (!target || isNaN(target)) return;

  var span = (parseInt(root.getAttribute('data-crk-span'), 10) || 43200) * 1000;

  var hh = root.querySelector('[data-crk-hh]');
  var mm = root.querySelector('[data-crk-mm]');
  var ss = root.querySelector('[data-crk-ss]');
  var spoken = root.querySelector('[data-crk-spoken]');
  var fill = root.querySelector('[data-crk-fill]');
  var pct = root.querySelector('[data-crk-pct]');
  var openBox = root.querySelector('[data-crk-open]');
  var heading = root.querySelector('[data-crk-heading]');
  var sub = root.querySelector('[data-crk-sub]');
  var reload = root.querySelector('[data-crk-reload]');

  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Whether the page was loaded while there was still time on the clock.
     Only then is an automatic reload at zero the right thing: it means we
     watched it cross. Landing on a page that is already at zero must not
     reload, or a store whose password is still on would loop forever. */
  var watchedItCross = Date.now() < target;
  var opened = false;
  var lastSpokenMinute = -1;

  function pad(n) {
    return n < 10 ? '0' + n : String(n);
  }

  /* Hours are not wrapped at 24. With an unlock date days out the clock
     reads 61:14:09, which is unambiguous, where "13:14:09" would not be. */
  function paint(remaining) {
    var total = Math.max(0, Math.floor(remaining / 1000));
    var h = Math.floor(total / 3600);
    var m = Math.floor((total % 3600) / 60);
    var s = total % 60;

    if (hh) hh.textContent = pad(h);
    if (mm) mm.textContent = pad(m);
    if (ss) ss.textContent = pad(s);

    /* The live region announces whole minutes only. A per-second update
       would make a screen reader talk over everything else on the page. */
    if (spoken && m !== lastSpokenMinute) {
      lastSpokenMinute = m;
      spoken.textContent = h > 0
        ? h + (h === 1 ? ' hour ' : ' hours ') + m + (m === 1 ? ' minute' : ' minutes') + ' until the store opens'
        : m + (m === 1 ? ' minute ' : ' minutes ') + s + (s === 1 ? ' second' : ' seconds') + ' until the store opens';
    }
  }

  function progressOf(remaining) {
    var p = 1 - (remaining / span);
    if (p < 0) p = 0;
    if (p > 1) p = 1;
    return p;
  }

  function open() {
    if (opened) return;
    opened = true;

    root.setAttribute('data-crk-state', 'open');

    var h = root.getAttribute('data-crk-open-heading');
    var s = root.getAttribute('data-crk-open-sub');
    if (heading && h) heading.textContent = h;
    if (sub && s) sub.textContent = s;
    if (openBox) openBox.hidden = false;

    /* One reload, and only if this tab watched the clock run out. Delayed
       so the door animation is seen and so a burst of tabs does not all
       hit the origin on the same second. */
    if (watchedItCross) {
      window.setTimeout(function () {
        window.location.reload();
      }, 4000 + Math.floor(Math.random() * 4000));
    }
  }

  function tick() {
    var remaining = target - Date.now();

    if (remaining <= 0) {
      paint(0);
      if (fill) fill.style.width = '100%';
      if (pct) pct.textContent = '100%';
      open();
      return;
    }

    paint(remaining);

    var p = progressOf(remaining);
    if (fill) fill.style.width = (p * 100).toFixed(1) + '%';
    if (pct) pct.textContent = Math.round(p * 100) + '%';

    /* Two full turns of the wheel across the progress window, so the dial
       is visibly further round than it was an hour ago. */
    root.style.setProperty('--crk-dial', (p * 720).toFixed(1));
  }

  tick();
  window.setInterval(tick, 250);

  if (reload) {
    reload.addEventListener('click', function () {
      window.location.reload();
    });
  }

  /* ---- the waiting counter ------------------------------------------
     Simulated: a bounded random walk around a centre that drifts up as the
     clock runs down, so it reads as a room filling rather than noise. This
     is scenery and the section's schema says so — nothing on a password
     page can count live visitors. Fixed mode shows the number as typed.
     Under prefers-reduced-motion it does not move at all: a number that
     rewrites itself every few seconds is motion like any other. */
  var countEl = root.querySelector('[data-crk-count]');
  var mode = root.getAttribute('data-crk-count-mode');

  if (countEl && mode === 'simulated' && !still) {
    var base = parseInt(root.getAttribute('data-crk-count-base'), 10) || 0;
    var drift = parseInt(root.getAttribute('data-crk-count-drift'), 10) || 0;

    if (drift > 0) {
      var value = base;
      var stepSize = Math.max(1, Math.round(drift / 8));

      window.setInterval(function () {
        var centre = base + (drift * 0.6 * progressOf(target - Date.now()));
        var pull = (centre - value) * 0.25;
        value += pull + ((Math.random() * 2 - 1) * stepSize);

        if (value < base - drift) value = base - drift;
        if (value > base + drift) value = base + drift;

        countEl.textContent = String(Math.round(value));
      }, 2600 + Math.floor(Math.random() * 2600));
    }
  }
})();
