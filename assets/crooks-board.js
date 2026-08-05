/*
 * CROOKSLDN — CASE 001 attract board.
 * Ported verbatim from the terminal prototype's src/lib/board/{map,sprites,renderer,attract}.js.
 * The four ES modules are concatenated into one IIFE because Shopify asset URLs are
 * CDN-hashed and relative `import` paths do not resolve. No build step, no imports.
 *
 * Public API (window.CrooksBoard):
 *   mount(element, options)  -> instance with .destroy(); element may be a <canvas> or a
 *                               container (a <canvas> is created inside if absent).
 *   destroy(root)            -> tears down every board within `root` (default: document).
 *   mountAll(root)           -> mounts every not-yet-mounted [data-crk-board] within `root`.
 *
 * Auto-mount: any element carrying `data-crk-board` (or containing a <canvas>) is mounted on
 * DOMContentLoaded and on `shopify:section:load`, and torn down on `shopify:section:unload`.
 */
(function () {
  'use strict';

  /* ---- map.js — CASE 001 map data, verbatim from the game ---- */
  var COLS = 13, ROWS = 11;
  var MAP = [
    '#############',
    '#......#....#',
    '#.##.#.#.##.#',
    '#.#..X....#.#',
    '#...##.##...#',
    '#.#....X..#.#',
    '#.##.###.##.#',
    '#....X......#',
    '#.##.#.##.#.#',
    '#...........#',
    '#############',
  ];
  var EXIT = { x: 11, y: 1 };
  var PACKAGES = [{ x: 3, y: 1 }, { x: 4, y: 5 }, { x: 10, y: 7 }];
  var PATROL = [{ x: 6, y: 7 }, { x: 9, y: 7 }];

  // Fixed walkable attract loop: start -> pkg 1 -> pkg 2 -> pkg 3 -> exit. Deterministic.
  var ROUTE = [
    [1, 9], [1, 8], [1, 7], [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1], [2, 1], [3, 1],
    [4, 1], [4, 2], [4, 3], [3, 3], [3, 4], [3, 5], [4, 5],
    [4, 6], [4, 7], [4, 8], [4, 9], [5, 9], [6, 9], [7, 9], [8, 9], [9, 9], [9, 8], [9, 7], [10, 7],
    [11, 7], [11, 6], [11, 5], [11, 4], [11, 3], [11, 2], [11, 1],
  ];

  var TILE_COLORS = {
    floorA: '#141218',
    floorB: '#181521',
    brick: '#262031',
    mortar: '#0B0A0E',
    concrete: '#1f1b28',
    crate: '#39304a',
    crateEdge: '#211b2e',
    fence: '#4a4458',
  };

  /* ---- sprites.js — 8x8 sprite grids drawn with fillRect ---- */
  var PLAYER = [
    '..1111..', '.111111.', '.111111.', '.122221.',
    '.111111.', '..1111..', '.11..11.', '.11..11.',
  ];
  var COP = [
    '...RR...', '..4444..', '.444444.', '.445544.',
    '.444444.', '..4444..', '..4..4..', '..4..4..',
  ];
  var SPRITE_COLORS = {
    '1': '#1b1824', // dark outfit
    '2': '#A77AC7', // purple identifier
    '4': '#222b40', // navy
    '5': '#DDD7C9', // paper
  };
  var LIGHT_RED = '#A83232'; // blinking police light — the only red
  var LIGHT_OFF = '#222b40';

  /* ---- renderer.js — pure canvas draw for the attract board ---- */
  var STEP_MS = 140;
  var HOLD_MS = 1200;
  var LAST = ROUTE.length - 1;
  var CYCLE_MS = LAST * STEP_MS + HOLD_MS;

  var COP_X = [PATROL[0].x, 7, 8, PATROL[1].x, 8, 7]; // ping-pong at y = 7

  var PKG_STEP = PACKAGES.map(function (p) {
    for (var i = 0; i < ROUTE.length; i++) {
      if (ROUTE[i][0] === p.x && ROUTE[i][1] === p.y) return i;
    }
    return Infinity;
  });

  function sprite(ctx, grid, gx, gy, tile, blink) {
    var u = tile / 8;
    for (var r = 0; r < 8; r++) {
      for (var c = 0; c < 8; c++) {
        var ch = grid[r].charAt(c);
        if (ch === '.') continue;
        ctx.fillStyle = ch === 'R' ? (blink ? LIGHT_RED : LIGHT_OFF) : SPRITE_COLORS[ch];
        ctx.fillRect(Math.round(gx * tile + c * u), Math.round(gy * tile + r * u), Math.ceil(u), Math.ceil(u));
      }
    }
  }

  // Draws one full frame. `t` is milliseconds into the current cycle.
  function drawFrame(ctx, canvasWidth, t, now) {
    var tile = canvasWidth / COLS;
    ctx.imageSmoothingEnabled = false;
    var blink = Math.floor(now / 400) % 2 === 0;
    var sf = Math.min(t / STEP_MS, LAST);
    var step = Math.floor(sf), frac = sf - step;

    for (var y = 0; y < ROWS; y++) {
      for (var x = 0; x < COLS; x++) {
        var ch = MAP[y].charAt(x), X = x * tile, Y = y * tile;
        if (ch === '#') {
          var edge = x === 0 || y === 0 || x === COLS - 1 || y === ROWS - 1;
          ctx.fillStyle = edge ? TILE_COLORS.concrete : TILE_COLORS.brick;
          ctx.fillRect(X, Y, tile, tile);
          if (!edge) {
            ctx.fillStyle = TILE_COLORS.mortar;
            ctx.fillRect(X, Y + tile / 3, tile, 1);
            ctx.fillRect(X, Y + (2 * tile) / 3, tile, 1);
            ctx.fillRect(X + tile / 2, Y, 1, tile / 3);
            ctx.fillRect(X + tile / 4, Y + (2 * tile) / 3, 1, tile / 3);
          }
        } else {
          ctx.fillStyle = (x * 3 + y * 5) % 7 < 3 ? TILE_COLORS.floorA : TILE_COLORS.floorB;
          ctx.fillRect(X, Y, tile, tile);
          if (ch === 'X') {
            ctx.fillStyle = TILE_COLORS.crate;
            ctx.fillRect(X + tile / 8, Y + tile / 8, tile * 0.75, tile * 0.75);
            ctx.fillStyle = TILE_COLORS.crateEdge;
            ctx.fillRect(X + tile / 8, Y + tile / 8, tile * 0.75, 2);
            ctx.fillRect(X + tile / 8, Y + tile / 8 + tile * 0.75 - 2, tile * 0.75, 2);
          }
        }
      }
    }

    var q = tile / 8;
    for (var p = 0; p < PACKAGES.length; p++) {
      if (step >= PKG_STEP[p]) continue;
      ctx.fillStyle = blink ? '#A77AC7' : '#542578';
      ctx.fillRect(PACKAGES[p].x * tile + 2.5 * q, PACKAGES[p].y * tile + 2.5 * q, 3 * q, 3 * q);
    }

    ctx.fillStyle = blink ? '#DDD7C9' : '#6b6459';
    for (var k = 0; k < 2; k++) {
      var ox = EXIT.x * tile + q * (1.5 + k * 3);
      var oy = EXIT.y * tile;
      ctx.fillRect(ox, oy + 2 * q, q, q);
      ctx.fillRect(ox + q, oy + 3 * q, q, 2 * q);
      ctx.fillRect(ox, oy + 5 * q, q, q);
    }

    var gs = t / STEP_MS;
    var ci = Math.floor(gs) % COP_X.length, cf = gs - Math.floor(gs);
    var cx = COP_X[ci] + (COP_X[(ci + 1) % COP_X.length] - COP_X[ci]) * cf;
    sprite(ctx, COP, cx, PATROL[0].y, tile, blink);

    var a = ROUTE[step], b = ROUTE[Math.min(step + 1, LAST)];
    sprite(ctx, PLAYER, a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac, tile, blink);
  }

  /* ---- attract.js — sizing, rAF loop, pause when hidden, teardown ---- */
  function createAttract(canvas) {
    var ctx = canvas.getContext('2d');
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var visible = true, raf = 0, start = 0, destroyed = false;

    function size() {
      var w = canvas.clientWidth || (canvas.parentNode && canvas.parentNode.clientWidth) || 288;
      var dpr = window.devicePixelRatio || 1;
      var tile = Math.max(6, Math.round((w * dpr) / COLS));
      canvas.width = tile * COLS;
      canvas.height = tile * ROWS;
    }

    function staticFrame() {
      // One static frame mid-route, board fully drawn, no timers.
      drawFrame(ctx, canvas.width, 18 * STEP_MS, 0);
    }

    function frame(now) {
      raf = 0;
      if (destroyed) return;
      if (!start) start = now;
      drawFrame(ctx, canvas.width, (now - start) % CYCLE_MS, now);
      schedule();
    }
    function schedule() {
      if (!destroyed && !reduced && visible && !document.hidden && !raf) {
        raf = requestAnimationFrame(frame);
      }
    }
    function stop() {
      if (raf) { cancelAnimationFrame(raf); raf = 0; }
    }

    function onVisibility() {
      if (document.hidden) stop(); else schedule();
    }
    function onResize() {
      size();
      if (reduced) staticFrame();
    }

    var io = null;
    size();
    if (reduced) {
      staticFrame();
    } else {
      if ('IntersectionObserver' in window) {
        io = new IntersectionObserver(function (entries) {
          visible = entries[0].isIntersecting;
          if (visible) schedule(); else stop();
        });
        io.observe(canvas);
      }
      document.addEventListener('visibilitychange', onVisibility);
      schedule();
    }
    window.addEventListener('resize', onResize);

    return {
      destroy: function () {
        destroyed = true;
        stop();
        if (io) io.disconnect();
        document.removeEventListener('visibilitychange', onVisibility);
        window.removeEventListener('resize', onResize);
      },
    };
  }

  /* ---- public API + Shopify section lifecycle ---- */
  function resolveCanvas(element, create) {
    if (!element) return null;
    if (element.tagName === 'CANVAS') return element;
    var found = element.querySelector('canvas');
    if (found) return found;
    if (!create) return null;
    var canvas = document.createElement('canvas');
    canvas.className = 'crk-board';
    canvas.setAttribute('aria-hidden', 'true');
    element.appendChild(canvas);
    return canvas;
  }

  function mount(element, options) {
    var canvas = resolveCanvas(element, true);
    if (!canvas) return null;
    if (canvas._crkBoard) canvas._crkBoard.destroy();
    canvas._crkBoard = createAttract(canvas, options || {});
    return canvas._crkBoard;
  }

  function eachBoard(root, fn) {
    var scope = root && root.querySelectorAll ? root : document;
    var nodes = scope.querySelectorAll('[data-crk-board]');
    for (var i = 0; i < nodes.length; i++) {
      var canvas = resolveCanvas(nodes[i], false);
      if (canvas) fn(canvas);
    }
    // If the root element itself is the marked node (e.g. shopify:section:load target)
    if (root && root.matches && root.matches('[data-crk-board]')) {
      var self = resolveCanvas(root, false);
      if (self) fn(self);
    }
  }

  function mountAll(root) {
    eachBoard(root, function (canvas) {
      if (!canvas._crkBoard) canvas._crkBoard = createAttract(canvas, {});
    });
  }

  function destroyAll(root) {
    eachBoard(root, function (canvas) {
      if (canvas._crkBoard) { canvas._crkBoard.destroy(); canvas._crkBoard = null; }
    });
  }

  window.CrooksBoard = { mount: mount, mountAll: mountAll, destroy: destroyAll };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountAll(document); });
  } else {
    mountAll(document);
  }

  // Theme editor: re-mount / tear down as sections are added, removed, or reordered.
  document.addEventListener('shopify:section:load', function (e) { mountAll(e.target); });
  document.addEventListener('shopify:section:unload', function (e) { destroyAll(e.target); });
})();
