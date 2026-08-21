/* CROOKSLDN — street sightings.
 *
 * Enhancement only. The section ships three readable frames and three working
 * links without this file; the arrows are `hidden` in the markup and revealed
 * here, so nothing on the page is a control that does nothing.
 *
 * One frame is selected at a time. Selecting is what drives the purple border,
 * the LOCATION line, the counter and the SUBJECT WEARING bar. It happens three
 * ways, matched to how the person is actually using the page:
 *   - arrows and keyboard, everywhere
 *   - hover and focus, on a device that has a real pointer
 *   - the snapped frame, on a phone, where the strip is a scroller
 * Tapping a frame is left alone: it is a link to the piece, and hijacking it
 * would make the obvious gesture do the least useful thing.
 */
(function () {
  'use strict';

  function init(root) {
    var strip = root.querySelector('[data-crk-sight-strip]');
    var controls = root.querySelector('[data-crk-sight-controls]');
    if (!strip) return;

    var frames = [].slice.call(strip.querySelectorAll('[data-crk-sight-frame]'));
    if (frames.length < 2) return;

    var prevBtn = root.querySelector('[data-crk-sight-prev]');
    var nextBtn = root.querySelector('[data-crk-sight-next]');
    var counter = root.querySelector('[data-crk-sight-counter]');
    var pieceOut = root.querySelector('[data-crk-sight-piece-out]');
    var cta = root.querySelector('[data-crk-sight-cta]');
    var say = root.querySelector('[data-crk-sight-say]');
    var SAY_TPL = root.getAttribute('data-crk-sight-say-tpl') || '';

    var current = 0;
    for (var i = 0; i < frames.length; i++) {
      if (frames[i].getAttribute('aria-current') === 'true') { current = i; break; }
    }

    var fine = true;
    try { fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches; } catch (e) {}
    var still = false;
    try { still = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

    /* The strip is a scroller on a phone and a static three-up on a desktop.
       Ask the element rather than re-testing the breakpoint, so a change to the
       CSS cannot leave this file believing something else. */
    function scrolls() {
      return strip.scrollWidth - strip.clientWidth > 4;
    }

    function paint(i, opts) {
      var frame = frames[i];
      if (!frame) return;
      current = i;

      for (var n = 0; n < frames.length; n++) {
        frames[n].setAttribute('aria-current', n === i ? 'true' : 'false');
      }

      var piece = frame.getAttribute('data-crk-sight-piece') || '';
      var href = frame.getAttribute('data-crk-sight-href') || '';

      if (counter) counter.textContent = frame.getAttribute('data-crk-sight-no') || '';
      if (pieceOut) {
        pieceOut.textContent = piece;
        pieceOut.setAttribute('data-crk-redacted', href ? 'false' : 'true');
      }
      if (cta) {
        if (href) { cta.href = href; cta.hidden = false; }
        else { cta.hidden = true; cta.removeAttribute('href'); }
      }
      if (say && SAY_TPL) {
        say.textContent = SAY_TPL.replace('[n]', String(i + 1)).replace('[piece]', piece);
      }

      if (opts && opts.scroll && scrolls()) {
        try {
          strip.scrollTo({ left: frame.offsetLeft - (strip.clientWidth - frame.clientWidth) / 2, behavior: still ? 'auto' : 'smooth' });
        } catch (e) {
          strip.scrollLeft = frame.offsetLeft;
        }
      }
      if (opts && opts.focus) frame.focus();
    }

    function step(delta) {
      var next = (current + delta + frames.length) % frames.length;
      paint(next, { scroll: true });
    }

    if (prevBtn) prevBtn.addEventListener('click', function () { step(-1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { step(1); });

    /* Hover and focus follow the eye, but only where there is a pointer that
       can hover. On a touch screen the same events fire on tap, a beat before
       the link navigates, which would repaint the bar for nobody to read. */
    for (var f = 0; f < frames.length; f++) {
      (function (el, idx) {
        if (fine) el.addEventListener('mouseenter', function () { paint(idx); });
        el.addEventListener('focus', function () { paint(idx); }, true);
      })(frames[f], f);
    }

    strip.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        paint((current + 1) % frames.length, { scroll: true, focus: true });
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        paint((current - 1 + frames.length) % frames.length, { scroll: true, focus: true });
      }
    });

    /* On a phone the frame you have swiped to IS the selection — the arrows are
       a second way to do the same thing, not the only one. */
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (!scrolls()) return;
        var best = null;
        for (var n = 0; n < entries.length; n++) {
          if (!entries[n].isIntersecting) continue;
          if (!best || entries[n].intersectionRatio > best.intersectionRatio) best = entries[n];
        }
        if (!best) return;
        var idx = frames.indexOf(best.target);
        if (idx > -1 && idx !== current) paint(idx);
      }, { root: strip, threshold: [0.5, 0.75, 1] });
      for (var o = 0; o < frames.length; o++) io.observe(frames[o]);
    }

    if (controls) controls.hidden = false;
    paint(current);
  }

  function mountAll(scope) {
    var scoped = scope && scope.querySelectorAll ? scope : document;
    var nodes = scoped.querySelectorAll('[data-crk-section="sightings"]');
    for (var i = 0; i < nodes.length; i++) {
      if (!nodes[i]._crkSight) { nodes[i]._crkSight = true; init(nodes[i]); }
    }
    if (scoped.matches && scoped.matches('[data-crk-section="sightings"]') && !scoped._crkSight) {
      scoped._crkSight = true; init(scoped);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else {
    mountAll(document);
  }
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
})();
