/* CROOKSLDN — street sightings.
 *
 * Enhancement only, and deliberately small. The section is a contact sheet:
 * three frames rendered side by side, the middle one selected, each live frame
 * a link to the piece. All of that is server-rendered and works with this file
 * absent — there is no carousel to drive and no control that depends on it.
 *
 * What this adds is that the SUBJECT WEARING bar follows your attention on a
 * device that has a pointer: hovering or focusing a frame names the piece in
 * that frame. Touch is left alone, where a tap is a link and the bar stays on
 * the selected frame, exactly as it renders.
 *
 * Selection never changes any width — the wide column is the middle one
 * whatever is selected — so nothing here can reflow the row under the pointer.
 */
(function () {
  'use strict';

  function init(root) {
    var frames = [].slice.call(root.querySelectorAll('[data-crk-sight-frame]'));
    if (frames.length < 2) return;

    var strip = root.querySelector('[data-crk-sight-strip]');
    var pieceOut = root.querySelector('[data-crk-sight-piece-out]');
    var cta = root.querySelector('[data-crk-sight-cta]');
    var say = root.querySelector('[data-crk-sight-say]');
    var SAY_TPL = root.getAttribute('data-crk-sight-say-tpl') || '';

    /* Where the markup left it, so returning to it is exact rather than a
       guess at which frame the middle is. */
    var home = 0;
    for (var i = 0; i < frames.length; i++) {
      if (frames[i].getAttribute('aria-current') === 'true') { home = i; break; }
    }
    var current = home;

    var fine = true;
    try { fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches; } catch (e) {}

    function paint(i) {
      var frame = frames[i];
      if (!frame || i === current) return;
      current = i;

      for (var n = 0; n < frames.length; n++) {
        frames[n].setAttribute('aria-current', n === i ? 'true' : 'false');
      }

      var piece = frame.getAttribute('data-crk-sight-piece') || '';
      var href = frame.getAttribute('data-crk-sight-href') || '';

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
    }

    for (var f = 0; f < frames.length; f++) {
      (function (el, idx) {
        if (fine) {
          el.addEventListener('mouseenter', function () { paint(idx); });
          /* Put it back when the pointer leaves the sheet altogether, so the
             bar does not sit on whichever frame the mouse happened to cross on
             its way somewhere else. */
          el.addEventListener('mouseleave', function () {
            window.setTimeout(function () {
              if (root.querySelector('.crk-sight__frame:hover')) return;
              /* If the row has been scrolled, the frame in view is the honest
                 answer, not the one the markup started on. */
              if (!scrolls()) paint(home);
            }, 60);
          });
        }
        el.addEventListener('focus', function () { paint(idx); }, true);
      })(frames[f], f);
    }

    /* Locked frames are tabindex=-1, so tabbing alone cannot reach every frame.
       Arrow keys walk the row once you are in it. */
    root.addEventListener('keydown', function (e) {
      if (frames.indexOf(e.target) < 0) return;
      var d = 0;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') d = 1;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') d = -1;
      else return;
      e.preventDefault();
      var next = (current + d + frames.length) % frames.length;
      paint(next);
      frames[next].focus();
    });

    /* Ask the element whether it scrolls rather than re-testing a breakpoint,
       so a change to the CSS cannot leave this file believing something else.
       With three frames it never does; with more, it does at every width. */
    function scrolls() {
      return strip ? strip.scrollWidth - strip.clientWidth > 4 : false;
    }

    /* When the row is a scroller, the frame you have scrolled to IS the
       selection — swiping is the whole interaction on a touch screen. */
    if (strip && 'IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (!scrolls()) return;
        var best = null;
        for (var n = 0; n < entries.length; n++) {
          if (!entries[n].isIntersecting) continue;
          if (!best || entries[n].intersectionRatio > best.intersectionRatio) best = entries[n];
        }
        if (!best) return;
        var idx = frames.indexOf(best.target);
        if (idx > -1) paint(idx);
      }, { root: strip, threshold: [0.5, 0.75, 1] });
      for (var o = 0; o < frames.length; o++) io.observe(frames[o]);
    }
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
