/* CROOKSLDN — street sightings.
 *
 * Enhancement only. The section renders in two shapes and the block count
 * decides which: up to three frames it is a contact sheet with every frame on
 * screen and the middle one selected; past three it is a filmstrip that
 * scrolls. Both are server-rendered and readable with this file absent, every
 * live frame a link to its piece, and no control anywhere that depends on the
 * script having run.
 *
 * What this adds is that the SUBJECT WEARING bar follows the frame you are
 * looking at — the one you have scrolled to on a touch screen, the one under
 * the pointer on a device that has one — and a rail that says the row carries
 * on past the edge.
 *
 * Selection never changes any width, so nothing here can reflow the row under
 * the pointer or under a thumb mid-swipe.
 */
(function () {
  'use strict';

  function init(root) {
    var frames = [].slice.call(root.querySelectorAll('[data-crk-sight-frame]'));
    if (frames.length < 2) return;

    var strip = root.querySelector('[data-crk-sight-strip]');
    var railTrack = root.querySelector('[data-crk-sight-rail]');
    var railBar = root.querySelector('[data-crk-sight-railbar]');
    var pieceOut = root.querySelector('[data-crk-sight-piece-out]');
    var cta = root.querySelector('[data-crk-sight-cta]');
    var say = root.querySelector('[data-crk-sight-say]');
    var SAY_TPL = root.getAttribute('data-crk-sight-say-tpl') || '';

    /* Where the markup left it, so returning to it is exact rather than a
       guess at which frame the middle one is. */
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
       so a change to the CSS cannot leave this file believing something else. */
    function scrolls() {
      return strip ? strip.scrollWidth - strip.clientWidth > 4 : false;
    }

    /* Which frame the strip is scrolled to, as a share of the distance
     * travelled rather than whichever frame happens to sit under the middle.
     *
     * Two bugs, one replacement. It was an IntersectionObserver picking the
     * most-visible frame, and it bounced: a callback only carries the frames
     * that just crossed a threshold, so the "most visible" of that batch is not
     * the most visible on screen, and a steady scroll flipped the selection
     * backwards and forwards between two frames. Reading the middle of the
     * viewport fixed the bounce but could never reach the ends — with under
     * three frames in view the last frame is at the edge when the strip is
     * fully scrolled, never the middle, so the final frame could not be
     * selected at all. Here it is the whole scroll range mapped onto the whole
     * strip: scrolled to the start is the first frame, scrolled to the end is
     * the last, monotonic in between, and it agrees with the markup at rest so
     * there is nothing to correct on load.
     */
    function atScroll() {
      var span = strip.scrollWidth - strip.clientWidth;
      if (span <= 0) return current;
      var t = strip.scrollLeft / span;
      if (t < 0) t = 0; else if (t > 1) t = 1;
      return Math.round(t * (frames.length - 1));
    }

    function rail() {
      if (!railTrack || !railBar) return;
      if (!scrolls()) { railTrack.hidden = true; return; }
      railTrack.hidden = false;
      var span = strip.scrollWidth;
      railBar.style.width = (strip.clientWidth / span * 100) + '%';
      railBar.style.left = (strip.scrollLeft / span * 100) + '%';
    }

    if (strip) {
      var ticking = 0;
      strip.addEventListener('scroll', function () {
        if (ticking) return;
        ticking = window.requestAnimationFrame(function () {
          ticking = 0;
          rail();
          if (scrolls()) paint(atScroll());
        });
      }, { passive: true });

      /* How many frames fit is a media query, so the scroll range and the rail
         that reports it both change when the window does. */
      window.addEventListener('resize', function () {
        rail();
        if (scrolls()) paint(atScroll());
      });

      rail();
      /* Agrees with the markup at a scroll position of zero, so this settles
         the state without ever repainting it on load. */
      if (scrolls()) paint(atScroll());
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
