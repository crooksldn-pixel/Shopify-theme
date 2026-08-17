/*
 * CROOKSLDN — CASE 001 attract board.
 *
 * Sprites and tiles ported from the CURRENT game build (base44 app
 * "CASE 001: THE GETAWAY (Copy)", src/lib/game/render.js) — the detailed
 * artwork: thief in beanie and domino mask with a loot sack, UK police in a
 * custodian helmet and hi-vis with a Sillitoe tartan band and a flashing
 * light, gold coins, raised brickwork. The previous port used the first
 * build's flat 8x8 grids and no longer matched what the game looks like.
 *
 * Level 1's map, exit, coin positions and patrol are identical between the two
 * builds, so the attract route below is unchanged.
 *
 * The game draws at a fixed 64px tile, with every sprite expressed in absolute
 * offsets from the tile origin. Rather than rescale all of that by hand — the
 * kind of arithmetic that silently drifts — the canvas backing store is fixed
 * at 13x11 tiles of 64px and CSS scales the element. The draw code is then a
 * straight port, and `image-rendering: pixelated` keeps the edges hard.
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

  /* ---- maps.js — LEVELS[0], verbatim from the game ---- */
  var COLS = 13, ROWS = 11, TILE = 64, S = 8;
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
  var PICKUP = { x: 1, y: 1 };          // energy drink
  var PATROL_Y = 7;
  var RESPONSE = { x: 9, y: 4 };        // dormant until the game triggers it

  // Fixed walkable attract loop: start -> coin 1 -> coin 2 -> coin 3 -> exit. Deterministic.
  var ROUTE = [
    [1, 9], [1, 8], [1, 7], [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1], [2, 1], [3, 1],
    [4, 1], [4, 2], [4, 3], [3, 3], [3, 4], [3, 5], [4, 5],
    [4, 6], [4, 7], [4, 8], [4, 9], [5, 9], [6, 9], [7, 9], [8, 9], [9, 9], [9, 8], [9, 7], [10, 7],
    [11, 7], [11, 6], [11, 5], [11, 4], [11, 3], [11, 2], [11, 1],
  ];

  /* ---- render.js — palette, verbatim ---- */
  var C = {
    floor: '#141218', floor2: '#181521', wall: '#262031', mortar: '#0B0A0E',
    concrete: '#1f1b28', crate: '#39304a', crateEdge: '#211b2e', fence: '#4a4458',
    purple: '#542578', lav: '#A77AC7', paper: '#DDD7C9', red: '#A83232',
    dark: '#17151f', amber: '#D4A038', bright: '#FFE54F',
  };
  var SKIN = '#c9a87f', SKIN_SHADOW = '#b8967a', MOUTH = '#7a5a3a';

  function px(ctx, ox, oy, grid, colors) {
    for (var j = 0; j < grid.length; j++) {
      var row = grid[j];
      for (var i = 0; i < row.length; i++) {
        var c = colors[row[i]];
        if (c) { ctx.fillStyle = c; ctx.fillRect(ox + i * S, oy + j * S, S, S); }
      }
    }
  }

  var ENERGY_DRINK = [
    '........', '..1111..', '.122221.', '.123321.',
    '.122221.', '.123321.', '.122221.', '..1111..',
  ];
  var ENERGY_COLORS = { '1': '#3a2f1a', '2': C.amber, '3': C.bright };

  /* ---- tiles ---- */
  function drawFloor(ctx, x, y) {
    var ox = x * TILE, oy = y * TILE;
    ctx.fillStyle = ((x * 3 + y * 5) % 7 < 3) ? C.floor : C.floor2;
    ctx.fillRect(ox, oy, TILE, TILE);
    var h = (x * 31 + y * 17) % 5;
    if (h === 0) { ctx.fillStyle = '#100e15'; ctx.fillRect(ox + 16, oy + 40, S, S); }
    if (h === 2) { ctx.fillStyle = '#1d1926'; ctx.fillRect(ox + 40, oy + 16, S, S); }
    if (y === 9 && x % 3 === 1) { ctx.fillStyle = '#26212f'; ctx.fillRect(ox + 16, oy + 28, 32, 6); }
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(ox, oy + TILE - 1, TILE, 1);
    ctx.fillRect(ox + TILE - 1, oy, 1, TILE);
  }

  function drawWall(ctx, x, y) {
    var ox = x * TILE, oy = y * TILE;
    var v = (x * 7 + y * 13) % 3;
    if (v === 2 && x > 0 && x < COLS - 1 && y > 0 && y < ROWS - 1) {
      ctx.fillStyle = C.dark;
      ctx.fillRect(ox, oy, TILE, TILE);
      ctx.fillStyle = C.fence;
      for (var i = 4; i < TILE; i += 16) ctx.fillRect(ox + i, oy + 4, 4, TILE - 8);
      ctx.fillRect(ox, oy + 10, TILE, 4);
      ctx.fillRect(ox, oy + TILE - 14, TILE, 4);
    } else if (v === 1) {
      ctx.fillStyle = C.concrete;
      ctx.fillRect(ox, oy, TILE, TILE);
      ctx.fillStyle = C.mortar;
      ctx.fillRect(ox, oy + TILE - 4, TILE, 4);
      ctx.fillRect(ox + 24, oy + 12, 4, 20);
    } else {
      ctx.fillStyle = C.wall;
      ctx.fillRect(ox, oy, TILE, TILE);
      ctx.fillStyle = C.mortar;
      for (var j = 0; j < TILE; j += 16) {
        ctx.fillRect(ox, oy + j, TILE, 3);
        var off = (j / 16) % 2 === 0 ? 16 : 32;
        for (var k = off; k < TILE; k += 32) ctx.fillRect(ox + k, oy + j, 3, 16);
      }
    }
    ctx.fillStyle = '#4a3f5a';
    ctx.fillRect(ox, oy, TILE, 2);
    ctx.fillStyle = '#3a2f4a';
    ctx.fillRect(ox, oy + 2, TILE, 1);
  }

  function drawCrate(ctx, x, y) {
    var ox = x * TILE, oy = y * TILE;
    ctx.fillStyle = C.floor;
    ctx.fillRect(ox, oy, TILE, TILE);
    ctx.fillStyle = C.crate;
    ctx.fillRect(ox + 6, oy + 6, TILE - 12, TILE - 12);
    ctx.fillStyle = C.crateEdge;
    ctx.fillRect(ox + 6, oy + 6, TILE - 12, 5);
    ctx.fillRect(ox + 6, oy + TILE - 11, TILE - 12, 5);
    ctx.fillRect(ox + 6, oy + 6, 5, TILE - 12);
    ctx.fillRect(ox + TILE - 11, oy + 6, 5, TILE - 12);
    ctx.fillRect(ox + 14, oy + 28, TILE - 28, 5);
  }

  function drawExit(ctx, exit, unlocked, now) {
    var ox = exit.x * TILE, oy = exit.y * TILE;
    ctx.fillStyle = '#0e0c13';
    ctx.fillRect(ox, oy, TILE, TILE);
    ctx.fillStyle = C.dark;
    for (var j = 6; j < 30; j += 8) ctx.fillRect(ox + 4, oy + j, TILE - 8, 4);
    var blink = unlocked && Math.floor(now / 500) % 2 === 0;
    ctx.fillStyle = blink ? C.lav : C.purple;
    for (var i = 0; i < 3; i++) {
      ctx.fillRect(ox + 10 + i * 16, oy + 40, 8, 8);
      ctx.fillRect(ox + 14 + i * 16, oy + 48, 8, 8);
    }
    if (!unlocked) { ctx.fillStyle = C.red; ctx.fillRect(ox + TILE - 12, oy + 4, 8, 8); }
  }

  /* ---- loot: level 1 is coins ---- */
  function drawCoin(ctx, ox, oy, flick) {
    var g = flick ? '#FFD700' : '#D4A038';
    var e = '#8B6914', s = '#FFF8B0', d = '#B8860B';
    ctx.fillStyle = e;
    ctx.fillRect(ox + 22, oy + 14, 20, 4);
    ctx.fillRect(ox + 16, oy + 18, 32, 4);
    ctx.fillRect(ox + 14, oy + 22, 36, 20);
    ctx.fillRect(ox + 16, oy + 42, 32, 4);
    ctx.fillRect(ox + 22, oy + 46, 20, 4);
    ctx.fillStyle = g;
    ctx.fillRect(ox + 24, oy + 16, 16, 4);
    ctx.fillRect(ox + 18, oy + 20, 28, 4);
    ctx.fillRect(ox + 16, oy + 24, 32, 16);
    ctx.fillRect(ox + 18, oy + 40, 28, 4);
    ctx.fillRect(ox + 24, oy + 44, 16, 4);
    ctx.fillStyle = d;
    ctx.fillRect(ox + 26, oy + 22, 12, 2);
    ctx.fillRect(ox + 22, oy + 24, 2, 16);
    ctx.fillRect(ox + 40, oy + 24, 2, 16);
    ctx.fillRect(ox + 26, oy + 40, 12, 2);
    ctx.fillStyle = s;
    ctx.fillRect(ox + 22, oy + 18, 8, 2);
    ctx.fillRect(ox + 20, oy + 20, 4, 4);
    ctx.fillStyle = e;
    ctx.fillRect(ox + 30, oy + 28, 4, 2);
    ctx.fillRect(ox + 28, oy + 30, 2, 8);
    ctx.fillRect(ox + 30, oy + 34, 6, 2);
    ctx.fillRect(ox + 30, oy + 38, 4, 2);
  }

  /* ---- characters ---- */
  function drawThief(ctx, x, y) {
    var p = x, q = y;
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(p + 16, q + 57, 32, 3);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 19, q + 52, 13, 7);
    ctx.fillRect(p + 32, q + 52, 13, 7);
    ctx.fillStyle = '#2a2438';
    ctx.fillRect(p + 19, q + 57, 13, 2);
    ctx.fillRect(p + 32, q + 57, 13, 2);
    ctx.fillStyle = '#1a1620';
    ctx.fillRect(p + 21, q + 42, 9, 12);
    ctx.fillRect(p + 34, q + 42, 9, 12);
    ctx.fillStyle = '#2a2335';
    ctx.fillRect(p + 17, q + 26, 30, 18);
    ctx.fillStyle = '#1e1929';
    ctx.fillRect(p + 17, q + 26, 3, 18);
    ctx.fillRect(p + 44, q + 26, 3, 18);
    ctx.fillStyle = '#1a1620';
    ctx.fillRect(p + 31, q + 30, 2, 10);
    ctx.fillRect(p + 17, q + 39, 30, 4);
    ctx.fillStyle = '#D4A038';
    ctx.fillRect(p + 29, q + 39, 6, 4);
    ctx.fillStyle = '#FFE54F';
    ctx.fillRect(p + 30, q + 40, 4, 2);
    ctx.fillStyle = '#1a1620';
    ctx.fillRect(p + 24, q + 26, 16, 3);
    ctx.fillStyle = '#2a2335';
    ctx.fillRect(p + 24, q + 27, 3, 3);
    ctx.fillRect(p + 37, q + 27, 3, 3);
    ctx.fillRect(p + 12, q + 28, 6, 14);
    ctx.fillRect(p + 46, q + 28, 6, 14);
    ctx.fillStyle = SKIN;
    ctx.fillRect(p + 12, q + 40, 6, 4);
    ctx.fillRect(p + 46, q + 40, 6, 4);
    ctx.fillStyle = '#4a3a28';
    ctx.fillRect(p + 47, q + 31, 8, 11);
    ctx.fillStyle = '#5a4a35';
    ctx.fillRect(p + 47, q + 31, 8, 2);
    ctx.fillStyle = '#D4A038';
    ctx.fillRect(p + 49, q + 30, 4, 2);
    ctx.fillStyle = SKIN;
    ctx.fillRect(p + 23, q + 14, 18, 14);
    ctx.fillStyle = '#1a1620';
    ctx.fillRect(p + 21, q + 7, 22, 7);
    ctx.fillRect(p + 23, q + 5, 18, 3);
    ctx.fillRect(p + 25, q + 3, 14, 3);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 20, q + 10, 24, 4);
    ctx.fillStyle = '#2a2438';
    ctx.fillRect(p + 22, q + 8, 5, 2);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 22, q + 17, 20, 6);
    ctx.fillStyle = SKIN;
    ctx.fillRect(p + 21, q + 18, 2, 2);
    ctx.fillRect(p + 41, q + 18, 2, 2);
    ctx.fillStyle = '#E8E4D8';
    ctx.fillRect(p + 25, q + 18, 4, 3);
    ctx.fillRect(p + 35, q + 18, 4, 3);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 27, q + 19, 2, 2);
    ctx.fillRect(p + 37, q + 19, 2, 2);
    ctx.fillStyle = SKIN_SHADOW;
    ctx.fillRect(p + 31, q + 23, 2, 2);
    ctx.fillStyle = MOUTH;
    ctx.fillRect(p + 29, q + 26, 6, 1);
  }

  function drawCop(ctx, x, y, isResponse, dormant, lightOn) {
    var p = x, q = y;
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(p + 16, q + 57, 32, 3);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 19, q + 52, 13, 7);
    ctx.fillRect(p + 32, q + 52, 13, 7);
    ctx.fillStyle = isResponse ? '#2a1515' : '#1a2540';
    ctx.fillRect(p + 21, q + 42, 9, 12);
    ctx.fillRect(p + 34, q + 42, 9, 12);
    var jacket = isResponse ? '#ff8c1a' : '#ffd700';
    ctx.fillStyle = jacket;
    ctx.fillRect(p + 17, q + 26, 30, 18);
    ctx.fillStyle = '#b8c0c8';
    ctx.fillRect(p + 17, q + 30, 30, 4);
    ctx.fillRect(p + 17, q + 37, 30, 4);
    ctx.fillStyle = '#e8f0f8';
    ctx.fillRect(p + 17, q + 30, 30, 1);
    ctx.fillRect(p + 17, q + 37, 30, 1);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 17, q + 42, 30, 4);
    ctx.fillStyle = '#2a2335';
    ctx.fillRect(p + 22, q + 42, 4, 4);
    ctx.fillRect(p + 38, q + 42, 4, 4);
    ctx.fillStyle = jacket;
    ctx.fillRect(p + 12, q + 28, 6, 14);
    ctx.fillRect(p + 46, q + 28, 6, 14);
    ctx.fillStyle = SKIN;
    ctx.fillRect(p + 12, q + 40, 6, 4);
    ctx.fillRect(p + 46, q + 40, 6, 4);
    ctx.fillRect(p + 23, q + 16, 18, 12);
    var hat = isResponse ? '#3a1a1a' : '#1a2540';
    ctx.fillStyle = hat;
    ctx.fillRect(p + 22, q + 7, 20, 9);
    ctx.fillRect(p + 24, q + 5, 16, 3);
    ctx.fillRect(p + 26, q + 3, 12, 3);
    ctx.fillStyle = isResponse ? '#5a2a2a' : '#2a3550';
    ctx.fillRect(p + 22, q + 7, 20, 2);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 20, q + 12, 24, 3);
    ctx.fillStyle = '#c0c8d0';
    ctx.fillRect(p + 30, q + 8, 4, 3);
    ctx.fillStyle = '#e0e8f0';
    ctx.fillRect(p + 31, q + 9, 2, 1);
    for (var i = 0; i < 6; i++) {
      ctx.fillStyle = (i % 2 === 0) ? '#0d0a14' : '#E8E4D8';
      ctx.fillRect(p + 20 + i * 4, q + 14, 4, 2);
    }
    ctx.fillStyle = '#E8E4D8';
    ctx.fillRect(p + 26, q + 20, 3, 2);
    ctx.fillRect(p + 35, q + 20, 3, 2);
    ctx.fillStyle = '#0d0a14';
    ctx.fillRect(p + 27, q + 20, 2, 2);
    ctx.fillRect(p + 36, q + 20, 2, 2);
    ctx.fillStyle = SKIN_SHADOW;
    ctx.fillRect(p + 31, q + 23, 2, 2);
    ctx.fillStyle = MOUTH;
    ctx.fillRect(p + 28, q + 25, 8, 1);
    var lc = dormant ? '#3a2430' : (lightOn ? '#ff3333' : '#5a1f1f');
    if (lightOn && !dormant) {
      ctx.fillStyle = 'rgba(255,50,50,0.2)';
      ctx.fillRect(p + 27, q - 1, 10, 8);
    }
    ctx.fillStyle = lc;
    ctx.fillRect(p + 30, q + 1, 4, 4);
  }

  /* ---- attract timing ---- */
  var STEP_MS = 140;
  var HOLD_MS = 1200;
  var LAST = ROUTE.length - 1;
  var CYCLE_MS = LAST * STEP_MS + HOLD_MS;
  var COP_X = [6, 7, 8, 9, 8, 7]; // ping-pong along the level-1 patrol waypoints

  var PKG_STEP = PACKAGES.map(function (p) {
    for (var i = 0; i < ROUTE.length; i++) {
      if (ROUTE[i][0] === p.x && ROUTE[i][1] === p.y) return i;
    }
    return Infinity;
  });

  // Draws one full frame. `t` is milliseconds into the current cycle.
  function drawFrame(ctx, t, now) {
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, COLS * TILE, ROWS * TILE);

    var flick = Math.floor(now / 600) % 2 === 0;
    var lightOn = Math.floor(now / 400) % 2 === 0;
    var sf = Math.min(t / STEP_MS, LAST);
    var step = Math.floor(sf), frac = sf - step;

    for (var y = 0; y < ROWS; y++) {
      for (var x = 0; x < COLS; x++) {
        var ch = MAP[y].charAt(x);
        if (ch === '#') drawWall(ctx, x, y);
        else if (ch === 'X') { drawFloor(ctx, x, y); drawCrate(ctx, x, y); }
        else drawFloor(ctx, x, y);
      }
    }

    var collected = 0;
    for (var p = 0; p < PACKAGES.length; p++) if (step >= PKG_STEP[p]) collected++;
    drawExit(ctx, EXIT, collected === PACKAGES.length, now);

    if (step < 8) {
      ctx.globalAlpha = flick ? 1 : 0.85;
      px(ctx, PICKUP.x * TILE, PICKUP.y * TILE, ENERGY_DRINK, ENERGY_COLORS);
      ctx.globalAlpha = 1;
    }

    for (var c = 0; c < PACKAGES.length; c++) {
      if (step >= PKG_STEP[c]) continue;
      drawCoin(ctx, PACKAGES[c].x * TILE, PACKAGES[c].y * TILE, flick);
    }

    drawCop(ctx, RESPONSE.x * TILE, RESPONSE.y * TILE, true, true, false);

    var gs = t / STEP_MS;
    var ci = Math.floor(gs) % COP_X.length, cf = gs - Math.floor(gs);
    var cx = COP_X[ci] + (COP_X[(ci + 1) % COP_X.length] - COP_X[ci]) * cf;
    drawCop(ctx, cx * TILE, PATROL_Y * TILE, false, false, lightOn);

    var a = ROUTE[step], b = ROUTE[Math.min(step + 1, LAST)];
    drawThief(ctx, (a[0] + (b[0] - a[0]) * frac) * TILE, (a[1] + (b[1] - a[1]) * frac) * TILE);
  }

  /* ---- attract.js — sizing, rAF loop, pause when hidden, teardown ---- */
  function createAttract(canvas) {
    var ctx = canvas.getContext('2d');
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var visible = true, raf = 0, start = 0, destroyed = false;

    function size() {
      // Fixed backing store at the game's own 64px tile; CSS scales the element.
      if (canvas.width !== COLS * TILE) canvas.width = COLS * TILE;
      if (canvas.height !== ROWS * TILE) canvas.height = ROWS * TILE;
    }

    function staticFrame() {
      // One static frame mid-route, board fully drawn, no timers.
      drawFrame(ctx, 18 * STEP_MS, 0);
    }

    function frame(now) {
      raf = 0;
      if (destroyed) return;
      if (!start) start = now;
      drawFrame(ctx, (now - start) % CYCLE_MS, now);
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
