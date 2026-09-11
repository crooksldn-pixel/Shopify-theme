/* CROOKS OS — what is actually on top of what, measured.
 *
 * The live tablet session recorded `clipped=0` for every render while the owner was looking at
 * overlapping text and controls. `clipped` was `scrollWidth > clientWidth` on a card: it can
 * only see a box that is too small for its own contents. It cannot see two boxes that are each
 * the right size and in the same place — which is what overlap is, and what he saw.
 *
 * So this measures geometry. It collects `getBoundingClientRect()` for every control, every
 * leaf of text, every notification and every piece of fixed chrome on screen, and reports the
 * pairs that are in the same place. Seven rules, named, each one a thing the owner would call
 * a fault:
 *
 *   control_over_control     two things a finger can press, in the same place
 *   text_over_control        words printed across a control
 *   notification_over_chrome a message covering the dock, the orb, the halves, the composer
 *   rail_over_content        an action rail laid over what it is about
 *   document_overflow_x      the page scrolls sideways by accident
 *   folded_action            a control that is on screen at no width, or a sliver of one
 *   content_under_chrome     something essential underneath the fixed furniture
 *
 * Two halves, deliberately: `check(records)` is arithmetic over plain rectangles and runs
 * anywhere, so the rules themselves are unit-testable without a browser; `collect(doc)` and
 * `scan(opts)` read a real document and are the only part that needs one. The tablet's
 * telemetry calls `scan` so a future session records the truth (web/telemetry.js), and
 * scripts/browser/collision.js calls it in Chromium so a defect fails a gate rather than
 * waiting for the owner to see it.
 *
 * Nothing here reads a word of what a card says. A record carries a selector — tag, id, the
 * first class — and a rectangle, and that is all.
 */
(function (root) {
  'use strict';

  const TOL = 2;              // px of overlap in BOTH axes before a pair counts
  const SLIVER = 8;           // a control narrower or shorter than this is folded away
  const TOUCH = 44;           // the practical hit area, in CSS px
  const MAX_HITS = 24;        // bounded: a report, not a dump

  const RULES = [
    'control_over_control',
    'text_over_control',
    'notification_over_chrome',
    'rail_over_content',
    'document_overflow_x',
    'folded_action',
    'content_under_chrome',
  ];

  // ---- what counts as what, as selectors. One list per kind; a node can be in several.
  const SEL = {
    // Something a finger presses. `#talk` is deliberately absent: it is the transparent
    // hold region that lies UNDER the dock by design, so counting it as a control would
    // report the design as a defect. It is chrome here, and a card control that strays into
    // its band is caught by `content_under_chrome` instead — which is the real fault.
    control: [
      'button:not(#talk)', '[role="button"]', '[role="tab"]', 'a[href]', 'input', 'select', 'textarea',
      'summary', '.action-surface', '.row.tappable', '.link-strip', '.variant-row', '.ws-opt',
    ],
    // A message. The three classes of web/notify.js, and the old floating bubble.
    notification: ['.note', '.toast', '[data-notify]'],
    // Furniture a message must never cover, and the controls the brief names: the dock, the
    // orb, the halves, Back, Next, Split, the composer, the approval surfaces.
    chrome: [
      '#talk', '#talk-label', '.dock-btn', '#orb-frame', '#branch-bar', '#branch-rail',
      '.branch-chip', '.branch-act', '[data-action="split"]', '#home-btn', '#back-btn', '#next-btn',
      '.action-surface', '.compose-btn', '.field-input', '.variant-add', '.armed',
    ],
    // An action rail: a group of controls that belongs beside its content, never over it.
    rail: ['.rail', '.actions', '.row-actions', '.compose-actions', '.link-chips', '.variant-foot', '.ws-options'],
    // What the first screenful has to carry. If one of these is underneath the furniture the
    // owner cannot read or reach it, whatever the backend returned.
    essential: [
      '.card-title', '.action-surface', '.rail-chip', '.compose-btn', '.field-input',
      '.variant-add', '.row.tappable', '.fold-head',
    ],
  };

  const sel = (kind) => SEL[kind].join(',');

  // ---- the arithmetic ------------------------------------------------------------------

  function overlap(a, b) {
    const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    return w > TOL && h > TOL ? { w: Math.round(w), h: Math.round(h) } : null;
  }

  // Ancestry by path, so the rules never need a node. A record's path is its position in the
  // tree as "/0/3/1"; `a` contains `b` when a's path is a prefix of b's at a boundary.
  function contains(a, b) {
    return b.path.length > a.path.length && b.path.indexOf(a.path) === 0 && b.path.charAt(a.path.length) === '/';
  }
  const related = (a, b) => a.path === b.path || contains(a, b) || contains(b, a);

  const has = (record, kind) => record.kinds.indexOf(kind) !== -1;
  const onScreen = (r, view) => r.rect.right > 0 && r.rect.left < view.w && r.rect.bottom > 0 && r.rect.top < view.h;
  const drawn = (r) => r.rect.width > 0 && r.rect.height > 0;

  /* The rules, over records. Pure: the same records give the same hits, in the same order,
     in Node or in Chromium. */
  function check(records, opts) {
    const options = opts || {};
    const view = options.viewport || { w: 0, h: 0 };
    const hits = [];
    const box = (r) => (r ? `${Math.round(r.rect.left)},${Math.round(r.rect.top)} ${Math.round(r.rect.width)}x${Math.round(r.rect.height)}` : '');
    const add = (rule, a, b, over, note) => {
      hits.push({
        rule, a: a ? a.sel : '', b: b ? b.sel : '',
        at: box(a), bt: box(b),
        w: over ? over.w : 0, h: over ? over.h : 0,
        note: note || '',
      });
    };

    const visible = records.filter((r) => r.shown && (!view.w || onScreen(r, view)));
    const controls = visible.filter((r) => has(r, 'control') && drawn(r));
    const texts = visible.filter((r) => has(r, 'text') && drawn(r));
    const notes = visible.filter((r) => has(r, 'notification') && drawn(r));
    const chrome = visible.filter((r) => has(r, 'chrome') && drawn(r));
    const rails = visible.filter((r) => has(r, 'rail') && drawn(r));

    // 1 · two controls in the same place.
    for (let i = 0; i < controls.length; i++) {
      for (let j = i + 1; j < controls.length; j++) {
        const a = controls[i]; const b = controls[j];
        if (related(a, b)) continue;
        const over = overlap(a.rect, b.rect);
        if (over) add('control_over_control', a, b, over);
      }
    }

    // 2 · words across a control. A text leaf inside the control is its label, not a fault.
    for (const t of texts) {
      for (const c of controls) {
        if (related(t, c)) continue;
        const over = overlap(t.rect, c.rect);
        if (over) add('text_over_control', t, c, over);
      }
    }

    // 3 · a message over the furniture. Both directions of containment are excluded: a note
    // drawn INSIDE the composer is attached to it, which is the whole point of a local one.
    for (const n of notes) {
      for (const c of chrome) {
        if (related(n, c)) continue;
        const over = overlap(n.rect, c.rect);
        if (over) add('notification_over_chrome', n, c, over);
      }
    }

    // 4 · a rail over content it does not own.
    for (const rail of rails) {
      for (const t of texts) {
        if (related(rail, t)) continue;
        const over = overlap(rail.rect, t.rect);
        if (over) add('rail_over_content', rail, t, over);
      }
    }

    // 5 · the document scrolls sideways.
    if (options.document && options.document.scroll_width > options.document.client_width + 1) {
      add('document_overflow_x', null, null, null,
        `${options.document.scroll_width} > ${options.document.client_width}`);
    }

    // 6 · a control that is on screen at no width, or a sliver of one. `shown` already
    // excludes display:none and [hidden]; what is left is a control the layout squeezed.
    for (const c of visible.filter((r) => has(r, 'control'))) {
      const asked = c.asked || c.rect;
      if (asked.width < 1 || asked.height < 1) add('folded_action', c, null, null, 'zero size');
      else if (asked.width < SLIVER || asked.height < SLIVER) {
        add('folded_action', c, null, null, `${Math.round(asked.width)}×${Math.round(asked.height)}`);
      }
    }

    // 7 · something essential underneath the furniture. The collector hit-tests each
    // essential element's own centre; `covered_by` is what the browser found on top.
    for (const e of visible) {
      if (!e.covered_by) continue;
      add('content_under_chrome', e, null, null, e.covered_by);
    }

    const counts = {};
    for (const rule of RULES) counts[rule] = 0;
    for (const hit of hits) counts[hit.rule] = (counts[hit.rule] || 0) + 1;
    // One example of every rule that fired, first; then as much of the tail as the cap allows.
    const kept = [];
    for (const rule of RULES) {
      const first = hits.find((h) => h.rule === rule);
      if (first) kept.push(first);
    }
    for (const hit of hits) {
      if (kept.length >= MAX_HITS) break;
      if (kept.indexOf(hit) === -1) kept.push(hit);
    }
    return { total: hits.length, counts, hits: kept };
  }

  /* Controls too small for a thumb, and text-only actions with no box at all (section 29).
     Not a collision — reported beside them because it is the same measurement. */
  function touch(records, opts) {
    const options = opts || {};
    const floor = options.floor || TOUCH;
    const view = options.viewport || { w: 0, h: 0 };
    const small = [];
    for (const r of records) {
      if (!r.shown || !has(r, 'control') || !drawn(r)) continue;
      if (view.w && !onScreen(r, view)) continue;
      if (r.decorative) continue;
      const asked = r.asked || r.rect;
      const w = Math.round(asked.width); const h = Math.round(asked.height);
      if (Math.min(w, h) + 0.5 < floor) small.push({ sel: r.sel, w, h });
    }
    return small.slice(0, MAX_HITS);
  }

  // ---- reading a real document ---------------------------------------------------------

  function selectorOf(node) {
    const tag = String(node.tagName || '').toLowerCase();
    const id = node.id ? `#${node.id}` : '';
    const cls = String(node.className || '');
    const first = cls && typeof cls === 'string' ? cls.trim().split(/\s+/)[0] : '';
    return `${tag}${id}${first ? `.${first}` : ''}`;
  }

  // Its own words, not its children's: a text LEAF. A card is not text; the line inside it is.
  function ownText(node) {
    let out = '';
    const kids = node.childNodes || [];
    for (let i = 0; i < kids.length; i++) {
      const kid = kids[i];
      if (kid.nodeType === 3 && kid.data) out += kid.data;
    }
    return out.trim();
  }

  function matches(node, selector) {
    try { return typeof node.matches === 'function' && node.matches(selector); } catch { return false; }
  }

  const intersect = (a, b) => ({
    left: Math.max(a.left, b.left), top: Math.max(a.top, b.top),
    right: Math.min(a.right, b.right), bottom: Math.min(a.bottom, b.bottom),
  });
  const boxOf = (rect) => ({
    left: rect.left, top: rect.top,
    right: rect.right === undefined ? rect.left + rect.width : rect.right,
    bottom: rect.bottom === undefined ? rect.top + rect.height : rect.bottom,
  });

  /* Every node worth a rectangle, walked once, each one clipped by what is above it.
     `root` defaults to the document body, so a scan covers the chrome and the cards
     together — which is where the overlaps are. */
  function collect(doc, opts) {
    const options = opts || {};
    const scope = options.root || (doc.body || null);
    if (!scope) return [];
    const view = options.viewport || { w: 0, h: 0 };
    const styles = typeof options.styleOf === 'function'
      ? options.styleOf
      : (node) => (doc.defaultView && doc.defaultView.getComputedStyle ? doc.defaultView.getComputedStyle(node) : null);
    const out = [];
    const seen = [];
    const screen = { left: 0, top: 0, right: view.w || 1e6, bottom: view.h || 1e6 };

    const walk = (node, path, clip) => {
      if (!node || node.nodeType !== 1) return;
      const tag = String(node.tagName || '').toUpperCase();
      if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'SVG' || tag === 'TEMPLATE') return;
      const style = styles(node) || {};
      const display = style.display || '';
      const gone = Boolean(node.hidden) || display === 'none';
      if (gone) return;   // and its children with it: nothing under display:none has a place
      const invisible = style.visibility === 'hidden' || style.opacity === '0';
      const inert = style.pointerEvents === 'none';
      const rect = node.getBoundingClientRect ? node.getBoundingClientRect() : null;
      // Fixed furniture is not inside anybody's scroller: the dock, the hold band and the
      // sheet are painted against the screen, so their clip is the screen.
      let here = style.position === 'fixed' ? screen : clip;
      if (rect) {
        const own = boxOf(rect);
        const box = intersect(own, here);
        const clipped = box.right - box.left <= 0 || box.bottom - box.top <= 0;
        const kinds = [];
        // A control that cannot be touched is not a control: the transparent overlays and the
        // decorative layers would otherwise read as a screenful of collisions.
        if (!inert && !invisible && matches(node, sel('control'))) kinds.push('control');
        if (matches(node, sel('notification'))) kinds.push('notification');
        if (matches(node, sel('chrome'))) kinds.push('chrome');
        if (matches(node, sel('rail'))) kinds.push('rail');
        if (matches(node, sel('essential'))) kinds.push('essential');
        if (!invisible && ownText(node)) kinds.push('text');
        if (kinds.length) {
          const record = {
            sel: selectorOf(node), path, kinds, shown: !invisible && !clipped,
            decorative: Boolean(node.getAttribute && node.getAttribute('aria-hidden') === 'true'),
            // The rectangle as it is DRAWN: what the element asked for, narrowed by every
            // scroller above it. A card scrolled half out of the deck is half a card here.
            rect: {
              left: box.left, top: box.top, right: box.right, bottom: box.bottom,
              width: Math.max(0, box.right - box.left), height: Math.max(0, box.bottom - box.top),
            },
            // And what it asked for, kept beside it: `folded_action` is about the layout
            // squeezing a control, not about the owner having scrolled past it.
            asked: { width: rect.width, height: rect.height },
            covered_by: '',
          };
          out.push(record);
          seen.push(node);
        }
        // A scroller narrows everything inside it. Per axis, because `overflow-x:auto` on a
        // table wrapper says nothing about its height.
        const ox = style.overflowX || style.overflow || 'visible';
        const oy = style.overflowY || style.overflow || 'visible';
        if (ox !== 'visible' || oy !== 'visible') {
          here = {
            left: ox === 'visible' ? here.left : Math.max(here.left, own.left),
            right: ox === 'visible' ? here.right : Math.min(here.right, own.right),
            top: oy === 'visible' ? here.top : Math.max(here.top, own.top),
            bottom: oy === 'visible' ? here.bottom : Math.min(here.bottom, own.bottom),
          };
        }
      }
      const kids = node.children || [];
      for (let i = 0; i < kids.length; i++) walk(kids[i], `${path}/${i}`, here);
    };
    walk(scope, '', screen);

    // The occlusion pass, which is the only honest way to ask "can he see it": take the
    // centre of each essential element and ask the browser what is on top there. Anything
    // that is neither the element nor part of it means something is over it.
    if (typeof doc.elementFromPoint === 'function' && view.w) {
      for (let i = 0; i < out.length; i++) {
        const record = out[i];
        if (record.kinds.indexOf('essential') === -1 || !drawn(record)) continue;
        const x = Math.round(record.rect.left + record.rect.width / 2);
        const y = Math.round(record.rect.top + record.rect.height / 2);
        if (x < 1 || y < 1 || x > view.w - 1 || y > view.h - 1) continue;
        let top = null;
        try { top = doc.elementFromPoint(x, y); } catch { top = null; }
        if (!top) continue;
        const mine = seen[i];
        if (top === mine || (mine.contains && mine.contains(top)) || (top.contains && top.contains(mine))) continue;
        record.covered_by = selectorOf(top);
      }
    }
    return out;
  }

  /* One reading of the screen: the records, the rules, the thumb sizes and the viewport. */
  function scan(opts) {
    const options = opts || {};
    const doc = options.document || (typeof document !== 'undefined' ? document : null);
    if (!doc) return { total: 0, counts: {}, hits: [], touch: [], records: 0 };
    const win = options.window || root;
    const viewport = options.viewport || {
      w: (win && win.innerWidth) || 0,
      h: (win && win.innerHeight) || 0,
    };
    const html = doc.documentElement || {};
    const records = collect(doc, { root: options.root, viewport, styleOf: options.styleOf });
    const result = check(records, {
      viewport,
      document: {
        scroll_width: html.scrollWidth || 0,
        client_width: html.clientWidth || (win && win.innerWidth) || 0,
        scroll_height: html.scrollHeight || 0,
        client_height: html.clientHeight || (win && win.innerHeight) || 0,
      },
    });
    result.touch = touch(records, { viewport, floor: options.touchFloor });
    result.records = records.length;
    result.viewport = viewport;
    return result;
  }

  const api = { RULES, SEL, TOL, SLIVER, TOUCH, check, touch, collect, scan, overlap, contains, intersect };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CrooksCollide = api;
})(typeof window !== 'undefined' ? window : globalThis);
