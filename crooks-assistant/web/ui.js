/* The component vocabulary, rendered by hand.
 *
 * The backend sends `ui`: a list of { type, data } items chosen from a fixed vocabulary and
 * built from what the tools returned (app/presentation.py). This file turns those into DOM,
 * and it is the only file that does. Two rules hold throughout:
 *
 *   - Every string from outside — a customer's name, an email body, a product title — lands
 *     in the page through textContent. No innerHTML, no template strings into markup, no
 *     attribute built from data. What arrives as "<img onerror>" is shown as "<img onerror>".
 *   - Only the types listed in RENDERERS render. Anything else is reported as skipped and
 *     draws nothing. Claude cannot ask for a component; the presentation layer can.
 *
 * The file has no dependency on the rest of the app so that it can be exercised under Node
 * against a small DOM stand-in (tests/web/), where the two rules above are checked.
 */
(function (root, factory) {
  const api = factory();
  root.CrooksUI = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const doc = () => (typeof document !== 'undefined' ? document : globalThis.document);

  // ------------------------------------------------------------------ safe DOM

  function h(tag, attrs, children) {
    const el = doc().createElement(tag);
    if (attrs) {
      for (const key in attrs) {
        const value = attrs[key];
        if (value === null || value === undefined || value === false) continue;
        if (key === 'class') el.className = value;
        else if (key === 'text') el.textContent = String(value);
        else if (key === 'hidden') el.hidden = Boolean(value);
        else if (key === 'on' && typeof value === 'object') {
          for (const type in value) el.addEventListener(type, value[type]);
        } else if (key === 'data' && typeof value === 'object') {
          for (const d in value) el.dataset[d] = String(value[d]);
        } else el.setAttribute(key, String(value));
      }
    }
    append(el, children);
    return el;
  }

  function append(el, children) {
    if (children === null || children === undefined || children === false) return;
    if (Array.isArray(children)) { for (const c of children) append(el, c); return; }
    if (typeof children === 'string' || typeof children === 'number') {
      el.appendChild(doc().createTextNode(String(children)));
      return;
    }
    el.appendChild(children);
  }

  const text = (value, fallback) => {
    if (value === null || value === undefined || value === '') return fallback === undefined ? '' : fallback;
    return String(value);
  };
  const num = (value) => (typeof value === 'number' && Number.isFinite(value) ? value : null);
  const list = (value, limit) => (Array.isArray(value) ? value.slice(0, limit || 50).filter((v) => v && typeof v === 'object') : []);
  // The same bound, for the fields the backend sends as plain strings. `list` drops anything
  // that is not an object — which is right for rows and wrong, silently, for an array of
  // sentences: the capability card's "Try asking" chips and the whole "Since the last build"
  // section were filtered to nothing and never appeared on screen at all, while the code that
  // draws them read as though they did.
  const strings = (value, limit) => (Array.isArray(value) ? value.slice(0, limit || 50).map((v) => text(v)).filter(Boolean) : []);

  // ------------------------------------------------------------------ formatting

  const DATE_FMT = { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' };
  const DAY_FMT = { day: 'numeric', month: 'short' };
  const DATE_DAY_YEAR = { day: 'numeric', month: 'short', year: 'numeric' };

  function formatDate(value, opts) {
    const raw = text(value);
    if (!raw) return '';
    const ms = Date.parse(raw);
    if (!Number.isFinite(ms)) return raw;
    try {
      return new Intl.DateTimeFormat('en-GB', opts || DATE_FMT).format(new Date(ms));
    } catch (error) {
      return raw;
    }
  }

  const STATUS_TONE = {
    fulfilled: 'ok', paid: 'ok', success: 'ok', delivered: 'ok', active: 'ok',
    unfulfilled: 'warn', 'partially fulfilled': 'warn', pending: 'warn', authorized: 'warn',
    'partially paid': 'warn', 'in progress': 'warn', 'on hold': 'warn', scheduled: 'warn',
    refunded: 'bad', 'partially refunded': 'bad', voided: 'bad', cancelled: 'bad', failure: 'bad',
    error: 'bad', restocked: 'bad',
  };
  const tone = (status) => STATUS_TONE[text(status).toLowerCase()] || '';

  function badge(label, cls) {
    const value = text(label);
    if (!value) return null;
    return h('span', { class: `badge ${cls || tone(value)}`.trim(), text: value });
  }

  function kicker(label) { return h('p', { class: 'card-kicker', text: label }); }

  // Two letters from a name, for the avatar disc that makes a person read as a person.
  function initials(name) {
    const parts = text(name).trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return '·';
    return (parts.length === 1 ? parts[0].slice(0, 2) : parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  function avatar(name, cls) { return h('span', { class: `avatar${cls ? ' ' + cls : ''}`, 'aria-hidden': 'true', text: initials(name) }); }

  // An order's life as a strip of steps, lit as far as it has got. What a packer looks for
  // first, before the number: has it been paid, has it gone.
  function orderTimeline(d) {
    const pay = text(d.payment).toLowerCase();
    const ful = text(d.fulfillment).toLowerCase();
    const shipped = list(d.fulfillments, 6).map((f) => f.shipped_at).filter(Boolean)[0];
    const cancelled = Boolean(d.cancelled_at);
    const steps = [
      { label: 'Placed', done: true, when: formatDate(d.placed_at, DAY_FMT) },
      { label: 'Paid', done: pay === 'paid' || pay === 'partially refunded' || pay === 'partially_refunded' || pay === 'refunded', partial: pay === 'partially paid' || pay === 'partially_paid' || pay === 'authorized' },
      cancelled
        ? { label: 'Cancelled', done: true, bad: true, when: formatDate(d.cancelled_at, DAY_FMT) }
        : { label: ful === 'fulfilled' ? 'Shipped' : 'To ship', done: ful === 'fulfilled', partial: ful === 'partial' || ful === 'partially fulfilled' || ful === 'partially_fulfilled', when: shipped ? formatDate(shipped, DAY_FMT) : '' },
    ];
    return h('ol', { class: 'tl', 'aria-label': 'Order progress' }, steps.map((st) => h('li', {
      class: `tl-step${st.done ? ' is-done' : ''}${st.partial ? ' is-partial' : ''}${st.bad ? ' is-bad' : ''}`,
    }, [h('span', { class: 'tl-dot', 'aria-hidden': 'true' }), h('span', { class: 'tl-label', text: st.label }), st.when ? h('span', { class: 'tl-when', text: st.when }) : null])));
  }

  function kv(pairs, opts) {
    const dl = h('dl', { class: 'kv' });
    for (const [k, v, cls] of pairs) {
      const value = text(v);
      if (!value) continue;
      dl.appendChild(h('dt', { text: k }));
      dl.appendChild(h('dd', { class: cls || null, text: value }));
    }
    return dl.childNodes && dl.childNodes.length === 0 && !opts ? null : dl;
  }

  function card(kind, children, opts) {
    opts = opts || {};
    const el = h('article', { class: `card card-${kind}${opts.className ? ' ' + opts.className : ''}`, data: { type: kind } }, children);
    if (opts.fixture) {
      el.classList.add('is-fixture');
      el.appendChild(h('span', { class: 'fixture-tag', text: 'Fixture · not live' }));
    }
    return el;
  }

  // The Mac's window ends at the start of the day after it ("until", exclusive). The day the
  // owner sees as the end is the one before that.
  function lastDayOf(until) {
    const ms = Date.parse(String(until || ''));
    return Number.isFinite(ms) ? new Date(ms - 1).toISOString() : until;
  }

  // A card of tabs. panels: [{ name, label, node }]. One panel is open at a time, which is
  // what keeps an order card the height of the screen instead of seven thousand pixels.
  //
  // `opts.initial` opens a named panel — how the back stack puts a card back on the tab it
  // was left on. `opts.onChange(name)` is called when the owner moves, so the app can tell
  // the Mac where the branch now is. The wrapper carries data-tab, so nothing has to be
  // scraped out of the DOM to know.
  function tabs(panels, opts) {
    const settings = opts || {};
    const kept = panels.filter((p) => p && p.node);
    const wrap = h('div', { class: 'tabbed' });
    if (!kept.length) return wrap;
    let open = 0;
    if (settings.initial) {
      const found = kept.findIndex ? kept.findIndex((p) => p.name === settings.initial) : -1;
      if (found >= 0) open = found;
    }
    const bar = h('div', { class: 'tabs', role: 'tablist' });
    const bodies = [];
    const show = (i) => {
      bodies.forEach((b, j) => {
        b.body.hidden = j !== i;
        b.tab.setAttribute('aria-selected', j === i ? 'true' : 'false');
      });
      wrap.dataset.tab = kept[i].name || String(i);
      if (typeof settings.onChange === 'function') settings.onChange(kept[i].name || String(i), kept[i].label);
    };
    kept.forEach((p, i) => {
      const body = h('div', { class: 'panel', role: 'tabpanel', hidden: i !== open, data: { panel: p.name || String(i) } }, p.node);
      const tab = h('button', {
        class: 'tab', type: 'button', role: 'tab', 'aria-selected': i === open ? 'true' : 'false', text: p.label,
        data: { tab: p.name || String(i) },
        on: { click: () => show(i) },
      });
      bodies.push({ body, tab });
      bar.appendChild(tab);
    });
    wrap.dataset.tab = kept[open].name || String(open);
    append(wrap, [bar, bodies.map((b) => b.body)]);
    return wrap;
  }

  function expandable(el, label) {
    // A clamp with a "more" control, for long bodies. Nothing is hidden from the reader.
    el.classList.add('clamp');
    const btn = h('button', { class: 'link-btn', type: 'button', text: label || 'More', on: { click: () => {
      const open = el.classList.toggle('is-open');
      btn.textContent = open ? 'Less' : (label || 'More');
    } } });
    return [el, btn];
  }

  // ------------------------------------------------------------------ components

  function renderAssistant(d) {
    const body = h('p', { class: 'card-body', text: text(d.text) });
    return card('assistant', [kicker('Assistant'), text(d.text).length > 420 ? expandable(body) : body]);
  }

  // A row that names an order opens it. The id has always been on the wire; nothing on the
  // page ever used it, so the list was a picture of the orders rather than a way into them —
  // the only route to #1938 from a list of today's orders was to say its number out loud.
  // `data-ref` and `data-kind` are what the deck's click handler posts to `open.entity`, which
  // is the same command the word "open that one" reaches.
  function orderRow(o) {
    const ref = text(o.order_id);
    return h('li', {
      class: ref ? 'row tappable' : 'row', role: ref ? 'button' : null, tabindex: ref ? '0' : null,
      data: ref ? { ref, kind: 'order' } : {},
    }, [
      h('span', { class: 'row-main' }, [h('strong', { text: text(o.order_number, '—') }), ' ', text(o.customer_name)]),
      h('span', { class: 'row-sub', text: formatDate(o.placed_at) }),
      h('span', { class: 'row-side' }, [h('span', { class: 'amount', text: text(o.total) }), badge(o.fulfillment)]),
      ref ? h('span', { class: 'row-go', 'aria-hidden': 'true', text: '\u203a' }) : null,
    ]);
  }

  // ---- images. A card carries an image only as a path the Mac signed for it; the renderer
  // draws nothing for any other source. In fixture mode a small inline SVG stands in, so the
  // developer grid can show what a thumbnail looks like without a store behind it.
  const MEDIA_PATH = /^\/media\/shopify\/[0-9a-f]{32}\/\d{3}\?u=[A-Za-z0-9%._~-]+$/;
  const FIXTURE_IMAGE = /^data:image\/svg\+xml;base64,[A-Za-z0-9+/=]+$/;

  function imageSource(value, opts) {
    const src = text(value);
    if (MEDIA_PATH.test(src)) return src;
    if (opts && opts.fixture && FIXTURE_IMAGE.test(src)) return src;
    return '';
  }

  function thumb(item, opts) {
    const box = h('span', { class: 'thumb', 'aria-hidden': 'true' }, [
      h('span', { class: 'thumb-mono', text: (text(item.title).trim().charAt(0) || '·').toUpperCase() }),
    ]);
    const src = imageSource(item.image, opts);
    if (src) {
      const img = h('img', { class: 'thumb-img', alt: '', loading: 'lazy', decoding: 'async', width: '64', height: '64', referrerpolicy: 'no-referrer' });
      img.addEventListener('load', () => box.classList.add('is-loaded'));
      img.addEventListener('error', () => box.classList.add('is-missing'));
      img.setAttribute('src', src);
      box.appendChild(img);
    }
    return box;
  }

  function stockWords(stock) {
    if (!stock || typeof stock !== 'object') return '';
    if (stock.tracked === false) return 'untracked';
    const n = num(stock.available);
    if (n === null) return '';
    if (n < 0) return `oversold by ${-n}`;
    if (n === 0) return 'none left';
    return `${n} left`;
  }
  function stockTone(stock) {
    if (!stock || typeof stock !== 'object' || stock.tracked === false) return '';
    const n = num(stock.available);
    if (n === null) return '';
    return n <= 0 ? 'bad' : n <= 5 ? 'warn' : '';
  }

  function section(kind, label, children, extra) {
    return h('section', { class: `sec sec-${kind}`, 'aria-label': label }, [
      h('p', { class: 'sec-kicker' }, [h('span', { text: label }), extra || null]),
    ].concat(children || []));
  }

  function itemsList(items, opts, truncated) {
    const rows = items.map((it) => h('li', { class: 'item' }, [
      thumb(it, opts),
      h('span', { class: 'item-main' }, [
        h('span', { class: 'item-title', text: text(it.title, '—') }),
        h('span', { class: 'item-sub', text: [text(it.variant), it.sku ? `SKU ${text(it.sku)}` : ''].filter(Boolean).join(' · ') }),
      ]),
      h('span', { class: 'item-side' }, [
        h('span', { class: 'amount', text: [num(it.quantity) !== null && it.quantity > 1 ? `× ${it.quantity}` : '', text(it.total)].filter(Boolean).join('  ') }),
        stockWords(it.stock) ? h('span', { class: `item-stock ${stockTone(it.stock)}`.trim(), text: stockWords(it.stock) }) : null,
      ]),
    ]));
    if (truncated) rows.push(h('li', { class: 'item item-more', text: 'More items than shown.' }));
    return h('ul', { class: 'items' }, rows);
  }

  function moneyBlock(d) {
    const m = d.money && typeof d.money === 'object' ? d.money : {};
    const zero = (v) => /^[^0-9]*0(?:\.00?)?$/.test(text(v));
    const pairs = [['Subtotal', m.subtotal], ['Shipping', m.shipping], ['Tax', m.tax]];
    if (m.discounts && !zero(m.discounts)) pairs.push(['Discounts', m.discounts]);
    if (m.refunded && !zero(m.refunded)) pairs.push(['Refunded', m.refunded, 'bad']);
    if (m.outstanding && !zero(m.outstanding)) pairs.push(['Outstanding', m.outstanding, 'warn']);
    pairs.push(['Total', d.total, 'total']);
    const dl = h('dl', { class: 'money' });
    for (const [k, v, cls] of pairs) {
      const value = text(v);
      if (!value) continue;
      dl.appendChild(h('dt', { text: k }));
      dl.appendChild(h('dd', { class: cls || null, text: value }));
    }
    return dl.childNodes.length ? dl : null;
  }

  function addressLines(a) {
    if (!a || typeof a !== 'object') return [];
    const streets = Array.isArray(a.lines) ? a.lines.slice(0, 3).map((l) => text(l)).filter(Boolean) : [];
    const town = [text(a.city), text(a.zip)].filter(Boolean).join(' ');
    return [text(a.name), text(a.company)].concat(streets, [town, text(a.province), text(a.country)]).filter(Boolean);
  }

  function addressBlock(a) {
    const rows = addressLines(a);
    if (!rows.length) return h('p', { class: 'card-note', text: 'No shipping address on the order.' });
    return h('address', { class: 'addr' }, rows.map((line) => h('span', { class: 'addr-line', text: line })));
  }

  function shippingBlock(d) {
    const fulfils = list(d.fulfillments, 6);
    const tracking = fulfils.length
      ? h('ul', { class: 'rows' }, fulfils.map((f) => h('li', { class: 'row' }, [
        h('span', { class: 'row-main', text: [text(f.carrier), text(f.number)].filter(Boolean).join(' · ') || 'Shipment' }),
        h('span', { class: 'row-sub', text: formatDate(f.shipped_at) }),
        h('span', { class: 'row-side' }, [badge(f.status)]),
      ])))
      : h('p', { class: 'card-note', text: d.cancelled_at ? 'Not shipped.' : 'Not shipped yet.' });
    return [
      d.shipping_method ? h('p', { class: 'ship-method', text: text(d.shipping_method) }) : null,
      addressBlock(d.shipping_address),
      tracking,
    ];
  }

  // ---- the customer's history, beside their order or on their own card.
  function historyBlock(hist) {
    // Not found, and could not be read, are different facts and get different sentences. The
    // Phase 2 live test found a failed read printed as "No customer on this order." under a
    // header naming the customer — infrastructure turned into business truth.
    if (!hist || typeof hist !== 'object') return [h('p', { class: 'card-note', text: 'No customer is attached to this order.' })];
    if (hist.available === false) return [h('p', { class: 'card-note unread-line', text: 'I couldn’t load the customer this time. Say “what else has this customer ordered?” to try again.' })];
    const orders = num(hist.orders);
    const stats = h('div', { class: 'stats three' }, [
      h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: orders === null ? '—' : String(orders) }), h('div', { class: 'stat-k', text: orders === 1 ? 'Order' : 'Orders' })]),
      h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: text(hist.spent, '—') }), h('div', { class: 'stat-k', text: 'Lifetime' })]),
      h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: formatDate(hist.since, { month: 'short', year: 'numeric' }) || '—' }), h('div', { class: 'stat-k', text: 'Since' })]),
    ]);
    const lines = [];
    if (hist.first_order_at) lines.push(h('li', { class: 'hist-line', text: `First order ${formatDate(hist.first_order_at, DATE_DAY_YEAR)}` }));
    const waiting = list(Array.isArray(hist.other_unfulfilled) ? hist.other_unfulfilled.map((n) => ({ n })) : [], 5).map((x) => text(x.n)).filter(Boolean);
    if (waiting.length) lines.push(h('li', { class: 'hist-line warn', text: `Also waiting to ship: ${waiting.join(', ')}` }));
    const recent = list(hist.recent, 5);
    if (hist.recent_truncated && recent.length && orders !== null) lines.push(h('li', { class: 'hist-line', text: `Last ${recent.length} of ${orders} orders shown` }));
    // A customer's earlier orders are the second-commonest hop in the whole graph — you are
    // looking at #1938 and you want the one before it — and they were plain text. The row that
    // names #1912 opens #1912, unless it names the order you are already on.
    const rows = recent.length ? h('ul', { class: 'rows compact hist-rows' }, recent.map((r) => {
      const ref = r.current ? '' : text(r.order_id);
      return h('li', {
        class: `row${r.current ? ' is-current' : ''}${ref ? ' tappable' : ''}`,
        role: ref ? 'button' : null, tabindex: ref ? '0' : null,
        data: ref ? { ref, kind: 'order' } : {},
      }, [
        h('span', { class: 'row-main' }, [h('strong', { text: text(r.order_number, '—') }), ' ', h('span', { class: 'card-meta', text: formatDate(r.placed_at, DAY_FMT) }), r.current ? badge('this order', 'quiet') : null]),
        h('span', { class: 'row-sub', text: text(r.items_brief) }),
        h('span', { class: 'row-side' }, [h('span', { class: 'amount', text: text(r.total) }), badge(r.cancelled ? 'cancelled' : r.fulfillment)]),
        ref ? h('span', { class: 'row-go', 'aria-hidden': 'true', text: '\u203a' }) : null,
      ]);
    })) : null;
    return [stats, lines.length ? h('ul', { class: 'hist-lines' }, lines) : null, rows];
  }

  // ---- email that is about this order, with how sure that is on every line.
  function relatedEmailBlock(email) {
    if (!email || typeof email !== 'object') return [h('p', { class: 'card-note', text: 'Email not checked.' })];
    if (email.available === false) {
      // Not configured is a setting; unavailable is a read that failed. Only one of them is
      // worth trying again, and only one of them must not be read as "no email".
      const reason = text(email.reason);
      if (/unavailable|read_failed|timeout/i.test(reason)) return [h('p', { class: 'card-note unread-line', text: 'I couldn’t check the inbox this time. Say “check the inbox for this order” to try again.' })];
      return [h('p', { class: 'card-note', text: `Email not checked${reason ? ' · ' + reason : ''}` })];
    }
    const threads = list(email.threads, 3);
    if (!threads.length) return [h('p', { class: 'card-note', text: 'No recent email from them about this.' })];
    return [h('ul', { class: 'rows mail' }, threads.map((t) => {
      // Three words for three certainties: the mail server vouched for the sender; the
      // From line matches the order and nothing else does; or the order is merely mentioned.
      const verified = t.verified_sender === true;
      const matches = verified || t.sender_match === true;
      const row = h('li', { class: 'row tappable', role: 'button', tabindex: '0', data: { thread: text(t.thread_id) } }, [
        h('span', { class: 'row-main' }, [
          badge(verified ? 'From the customer · verified' : matches ? 'Sender matches' : 'Mentions the order', verified ? 'quiet ok' : matches ? 'quiet warn' : 'quiet'),
          ' ', h('strong', { text: text(t.subject, '(no subject)') }),
        ]),
        h('span', { class: 'row-sub', text: [text(t.from), text(t.snippet)].filter(Boolean).join(' — ') }),
        h('span', { class: 'row-side' }, [h('span', { class: 'card-meta', text: formatDate(t.date) })]),
      ]);
      row.addEventListener('click', () => row.classList.toggle('is-open'));
      return row;
    }))];
  }

  // ---- the rail: the changes the Mac says make sense for this order. A chip is not a
  // button that does something; it primes the hold with the words that ask for the change,
  // so the ask, the proposal and the gesture stay exactly what they are by voice. A chip the
  // Mac disabled shows its one reason and does nothing.
  //
  // Two kinds of chip share the rail. An "ask" chip primes the hold (and, when it carries a
  // family, tells the Mac what the next sentence is about). A "stage" chip is a row action
  // (app/actions/rows.py) on the record itself: the tap asks the Mac to PREPARE the change,
  // and the card that comes back still waits for a gesture. `ref` is the record the stage
  // chips act on; it is posted back with the action id and nothing else.
  function rail(actions, opts, ref) {
    const list_ = list(actions, 6);
    if (!list_.length) return null;
    return h('div', { class: 'rail', role: 'group', 'aria-label': 'Changes' }, list_.map((a) => {
      const staged = text(a.mode) === 'stage';
      const enabled = a.enabled === true && (staged ? Boolean(text(ref)) : Boolean(text(a.instruction)));
      const chip = h('button', {
        class: `rail-chip risk-${text(a.risk) === 'red' ? 'red' : 'amber'}${enabled ? '' : ' is-off'}`, type: 'button',
        'aria-disabled': enabled ? 'false' : 'true', title: staged ? text(a.detail) : null,
        // `family` is the spoken control this chip arms, when it arms one — the Mac's own
        // mapping (commands.SPOKEN_CONTROLS), carried here so the page never invents one and
        // so the armed chip can be found again when the Mac says it is listening.
        data: { action: text(a.id), mode: text(a.mode, 'ask'), family: text(a.family), ref: staged ? text(ref) : null },
      }, [
        h('span', { class: 'rail-label', text: text(a.label, '—') }),
        !enabled && a.reason ? h('span', { class: 'rail-why', text: text(a.reason) }) : null,
      ]);
      if (enabled && staged) {
        chip.addEventListener('click', (event) => {
          if (event && typeof event.stopPropagation === 'function') event.stopPropagation();
          if (!opts || typeof opts.onRowAction !== 'function' || chip.disabled) return;
          chip.disabled = true;
          opts.onRowAction(text(a.id), text(ref), chip);
        });
      } else if (enabled) {
        chip.addEventListener('click', () => { if (opts && typeof opts.onAction === 'function') opts.onAction(a, chip); });
      }
      return chip;
    }));
  }

  function pendingLine(what) {
    return h('p', { class: 'card-note pending-line', text: what });
  }

  function renderOrder(d, opts) {
    const items = list(d.items, 12);
    const tags = Array.isArray(d.tags) ? d.tags.slice(0, 3).map((t) => text(t)).filter(Boolean) : [];
    // Number, who, how much, what state — the four things worth knowing in the first second,
    // on two lines. The "ORDER" kicker went because the card already says #1938 in 30px mono;
    // the customer's tags moved up beside their name because a VIP badge on a line of its own
    // cost 30px to say one word; and the money came UP here, which is the point of the change.
    // It was only in the Overview tab, so the total was never on screen with the status — and
    // it was then repeated in the Money breakdown below, so £84.00 appeared four times on one
    // card and not once in its header.
    const head = h('div', { class: 'card-head' }, [
      h('div', { class: 'head-main' }, [
        h('h2', { class: 'card-title mono', text: text(d.order_number, '—') }),
        h('p', { class: 'card-sub' }, [
          h('span', { text: text(d.customer_name) }),
          ...tags.map((t) => badge(t, 'quiet')),
        ]),
        d.customer_email ? h('p', { class: 'card-meta', text: text(d.customer_email) }) : null,
      ]),
      h('div', { class: 'head-side' }, [
        d.total ? h('p', { class: 'head-total mono', text: text(d.total) }) : null,
        h('div', { class: 'badges' }, [badge(d.fulfillment), badge(d.payment)]),
      ]),
    ]);
    // Placed and Total are in the header and the timeline now; repeating them here was most of
    // what made the Overview tab a second copy of the card it sits inside.
    const overview = kv([
      ['Ships to', d.ships_to],
      ['Cancelled', d.cancelled_at ? [formatDate(d.cancelled_at), text(d.cancel_reason)].filter(Boolean).join(' · ') : ''],
    ], true);
    if (!d.detail) {
      const brief = card('order', [head, orderTimeline(d), overview, h('p', { class: 'card-note', text: 'Ask for the order to see its items and shipping.' })], opts);
      brief.dataset.ref = text(d.order_id);
      return brief;
    }
    const pending = Array.isArray(d.pending) ? d.pending.map((x) => text(x)) : [];
    const historyBody = pending.indexOf('history') !== -1 ? [pendingLine('Reading their history…')] : historyBlock(d.history);
    const emailBody = pending.indexOf('email') !== -1 ? [pendingLine('Checking the inbox…')] : relatedEmailBlock(d.email);
    const standing = d.history && typeof d.history === 'object' ? text(d.history.standing) : '';
    // Five tabs, one open. The September session drew order cards 7,524 pixels tall against
    // 655 pixels of screen and recorded 131 scrolls; the same facts, one at a time, fit.
    const panels = [
      { name: 'overview', label: 'Overview', node: [
        overview,
        section('money', 'Money', [moneyBlock(d)]),
        d.note ? section('note', 'Note', [h('blockquote', { class: 'note-quote', text: text(d.note) })]) : null,
      ] },
      { name: 'items', label: `Items${items.length ? ' · ' + items.length : ''}`, node: [
        section('items', `Items${items.length ? ' · ' + items.length : ''}`, [items.length ? itemsList(items, opts, Boolean(d.items_truncated)) : h('p', { class: 'card-note', text: 'No items on the order.' })]),
      ] },
      { name: 'shipping', label: 'Shipping', node: [section('shipping', 'Shipping', shippingBlock(d))] },
      { name: 'customer', label: 'Customer', node: [section('history', 'Customer', historyBody, standing ? badge(standing, 'quiet') : null)] },
      { name: 'email', label: 'Email', node: [section('email', 'Email', emailBody)] },
    ];
    const full = card('order', [
      head,
      orderTimeline(d),
      d.cancelled_at ? h('p', { class: 'card-note bad', text: `Cancelled ${formatDate(d.cancelled_at)}${d.cancel_reason ? ' · ' + text(d.cancel_reason) : ''}` }) : null,
      rail(d.actions, opts),
      tabs(panels, { initial: opts && opts.tab, onChange: opts && opts.onTab ? (name, label) => opts.onTab('order', name, label) : null }),
    ], opts);
    full.dataset.ref = text(d.order_id);
    full.dataset.pending = pending.join(' ');
    return full;
  }

  // The rest of an order card, collected by the app from /context/order once the card is
  // up: the history and the inbox that missed the turn's budget. Returns what is still to
  // come, so the app knows whether to ask again.
  function hydrateOrder(node, ext) {
    if (!node || !ext || typeof ext !== 'object') return [];
    const pending = Array.isArray(ext.pending) ? ext.pending.map((x) => text(x)) : [];
    const fill = (kind, body) => {
      const sec = node.querySelector(`.sec-${kind}`);
      if (!sec) return;
      const keep = sec.querySelector('.sec-kicker');
      while (sec.firstChild) sec.removeChild(sec.firstChild);
      if (keep) sec.appendChild(keep);
      append(sec, body);
    };
    if (pending.indexOf('history') === -1 && Object.prototype.hasOwnProperty.call(ext, 'history')) {
      fill('history', historyBlock(ext.history));
      const k = node.querySelector('.sec-history') && node.querySelector('.sec-history').querySelector('.sec-kicker');
      const standing = ext.history && typeof ext.history === 'object' ? text(ext.history.standing) : '';
      if (k && standing && !k.querySelector('.badge')) k.appendChild(badge(standing, 'quiet'));
    }
    if (pending.indexOf('email') === -1 && Object.prototype.hasOwnProperty.call(ext, 'email')) fill('email', relatedEmailBlock(ext.email));
    if (Array.isArray(ext.attention)) placeAttention(node, ext.order_id, ext.attention);
    // A region the Mac tried and could not read: its tab says so, the way it does when the
    // tablet stops asking (settleOrder), so a closed tab is never an all-clear.
    for (const kind of (Array.isArray(ext.failed) ? ext.failed : [])) markTabUnread(node, kind);
    node.dataset.pending = pending.join(' ');
    return pending;
  }

  const TAB_OF_REGION = { email: 'email', history: 'customer' };
  function markTabUnread(node, kind) {
    const want = TAB_OF_REGION[kind] || kind;
    const tabs = node.querySelectorAll('[role="tab"]');
    const tab = tabs.find ? tabs.find((t) => (t.textContent || '').toLowerCase().indexOf(want) !== -1)
      : Array.prototype.find.call(tabs, (t) => (t.textContent || '').toLowerCase().indexOf(want) !== -1);
    if (tab && !tab.querySelector('.tab-mark')) {
      tab.setAttribute('data-unread', '1');
      tab.appendChild(h('span', { class: 'tab-mark', text: '?', title: 'not read' }));
    }
  }

  // What never arrived, said so. The tablet asks for the rest of an order three times and
  // then stops asking — and the panel it stopped asking for kept reading "Checking the
  // inbox…", byte for byte, 34.8 seconds later. Held in one hand, the card read as complete
  // and calm while the one thing that made the order urgent — a customer waiting on a reply —
  // had silently gone from the screen. A read that failed is drawn as a read that failed:
  // the region says so in words, with what to say to try again, and the tab it lives behind
  // carries a mark, so a closed tab is not an all-clear.
  function settleOrder(node, opts) {
    if (!node || !node.dataset) return [];
    const pending = text(node.dataset.pending).split(' ').filter(Boolean);
    if (!pending.length) return [];
    const number = text(opts && opts.number) || text((node.querySelector('.card-title') || {}).textContent).replace(/^#/, '');
    const words = {
      email: `The inbox could not be read this time. Say “check the inbox for ${number ? '#' + number : 'this order'}” to try again.`,
      history: 'Their history could not be read this time. Say “what else has this customer ordered?” to try again.',
    };
    for (const kind of pending) {
      const sec = node.querySelector(`.sec-${kind}`);
      if (sec) {
        const keep = sec.querySelector('.sec-kicker');
        while (sec.firstChild) sec.removeChild(sec.firstChild);
        if (keep) sec.appendChild(keep);
        sec.appendChild(h('p', { class: 'card-note unread-line', text: words[kind] || 'This could not be read this time.' }));
      }
      markTabUnread(node, kind);
    }
    node.dataset.pending = '';
    return pending;
  }

  // The attention card sits right after the order it reads; a later reading replaces it.
  function placeAttention(orderNode, orderId, items) {
    const parent = orderNode.parentNode;
    if (!parent) return null;
    const ref = text(orderId);
    const old = parent.querySelectorAll('.card-attention').filter ? parent.querySelectorAll('.card-attention').filter((n) => n.dataset.for === ref) : Array.prototype.filter.call(parent.querySelectorAll('.card-attention'), (n) => n.dataset.for === ref);
    old.forEach((n) => parent.removeChild(n));
    if (!items.length) return null;
    const fresh = renderAttention({ items, for: ref }, {});
    const siblings = Array.prototype.slice.call(parent.childNodes);
    const after = siblings[siblings.indexOf(orderNode) + 1] || null;
    if (after && typeof parent.insertBefore === 'function') parent.insertBefore(fresh, after); else parent.appendChild(fresh);
    return fresh;
  }

  function renderOrderList(d, opts) {
    const orders = list(d.orders, 10);
    const meta = [];
    if (num(d.count) !== null) meta.push(`${d.count} order${d.count === 1 ? '' : 's'}`);
    if (d.truncated) meta.push('more not shown');
    return card('order_list', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Orders'), h('h2', { class: 'card-title', text: text(d.title, 'Orders') }), h('p', { class: 'card-meta', text: meta.join(' · ') })])]),
      h('ul', { class: 'rows' }, orders.map(orderRow)),
    ], opts);
  }

  function renderCustomer(d, opts) {
    const orders = num(d.orders);
    const standing = orders === null ? '' : orders === 0 ? 'No orders yet' : orders === 1 ? 'First order' : orders >= 4 ? 'Regular' : 'Returning';
    const node = card('customer', [
      h('div', { class: 'card-head profile' }, [
        avatar(d.name, 'lg'),
        h('div', {}, [kicker('Customer'), h('h2', { class: 'card-title', text: text(d.name, 'Customer') }), h('p', { class: 'card-sub', text: text(d.email) })]),
        standing ? h('div', { class: 'badges' }, [badge(standing, 'quiet')]) : null,
      ]),
      customerPanels(d, orders, opts),
    ], opts);
    node.dataset.ref = text(d.customer_id);
    return node;
  }

  // Overview, Orders, Email — and only the tabs there is something to put behind. A customer
  // card with nothing but a name is a card, not a tab bar with two empty panels.
  function customerPanels(d, orders, opts) {
    const overview = h('div', { class: 'stats' }, [
      h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: orders === null ? '—' : String(orders) }), h('div', { class: 'stat-k', text: 'Orders' })]),
      h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: text(d.spent, '—') }), h('div', { class: 'stat-k', text: 'Lifetime' })]),
    ]);
    const history = d.history && typeof d.history === 'object' ? section('history', 'Orders', historyBlock(d.history)) : null;
    const mail = d.related_email && typeof d.related_email === 'object' ? section('email', 'Email', relatedEmailBlock(d.related_email)) : null;
    if (!history && !mail) {
      return [overview, h('p', { class: 'card-note', text: 'Ask for their orders or their emails to see more.' })];
    }
    return tabs([
      { name: 'overview', label: 'Overview', node: [overview] },
      history ? { name: 'orders', label: 'Orders', node: [history] } : null,
      mail ? { name: 'email', label: 'Email', node: [mail] } : null,
    ].filter(Boolean), { initial: opts && opts.tab, onChange: opts && opts.onTab ? (name, label) => opts.onTab('customer', name, label) : null });
  }

  function renderCustomerList(d, opts) {
    const customers = list(d.customers, 6);
    return card('customer_list', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker(d.ambiguous ? 'Which one?' : 'Customers'), h('h2', { class: 'card-title', text: text(d.title, 'Customers') })])]),
      h('ul', { class: 'rows' }, customers.map((c) => h('li', { class: 'row' }, [
        h('span', { class: 'row-main', text: text(c.name, '—') }),
        h('span', { class: 'row-sub', text: text(c.email) }),
        h('span', { class: 'row-side' }, [
          num(c.orders) !== null ? h('span', { class: 'card-meta', text: `${c.orders} order${c.orders === 1 ? '' : 's'}` }) : null,
          c.spent ? h('span', { class: 'amount', text: text(c.spent) }) : null,
        ]),
      ]))),
      d.ambiguous ? h('p', { class: 'card-note', text: 'Say which one you mean.' }) : null,
    ], opts);
  }

  function renderProduct(d, opts) {
    const products = list(d.products, 4);
    if (!products.length) return null;
    const p = products[0];
    const facts = kv([['Fabric', p.fabric], ['Cut', p.cut], ['Origin', p.origin], ['Care', p.care]], true);
    const desc = p.description ? expandable(h('p', { class: 'card-body', text: text(p.description) }), 'Read more') : null;
    let table = null;
    const measurements = list(p.measurements, 8);
    if (measurements.length) {
      const cols = Object.keys(measurements[0]);
      table = h('div', { class: 'table-wrap' }, h('table', { class: 'mtable' }, [
        h('thead', {}, h('tr', {}, cols.map((c) => h('th', { text: c })))),
        h('tbody', {}, measurements.map((m) => h('tr', {}, cols.map((c) => h('td', { text: text(m[c]) }))))),
      ]));
    }
    return card('product', [
      h('div', { class: 'card-head' }, [
        h('div', {}, [kicker('Product'), h('h2', { class: 'card-title', text: text(p.title, 'Product') }), h('p', { class: 'card-sub', text: text(p.subtitle) })]),
        h('div', { class: 'badges' }, [badge(p.status)]),
      ]),
      facts, desc, table,
      p.measurements_note && !measurements.length ? h('p', { class: 'card-note', text: text(p.measurements_note) }) : null,
      products.length > 1 ? h('p', { class: 'card-note', text: `Also matched: ${products.slice(1).map((x) => text(x.title)).filter(Boolean).join(', ')}` }) : null,
    ], opts);
  }

  const LEVEL_LABEL = { out: 'Out of stock', low: 'Low stock', oversold: 'Oversold', untracked: 'Not tracked', unknown: 'Unknown', ok: 'In stock' };
  const LEVEL_TONE = { out: 'bad', low: 'warn', oversold: 'bad', ok: 'ok', untracked: '', unknown: '' };

  function stockRow(v, withProduct) {
    const avail = num(v.available);
    const level = text(v.level, 'unknown');
    let amount = avail === null ? '—' : `${avail} left`;
    if (level === 'oversold') amount = `−${v.oversold_by}`;
    if (level === 'untracked') amount = 'untracked';
    return h('li', { class: 'row' }, [
      h('span', { class: 'row-main', text: withProduct ? text(v.product, 'Product') : text(v.variant, 'Variant') }),
      h('span', { class: 'row-sub', text: withProduct ? text(v.variant) : text(v.sku) }),
      h('span', { class: 'row-side' }, [h('span', { class: 'amount', text: amount }), badge(LEVEL_LABEL[level] || level, LEVEL_TONE[level] || '')]),
    ]);
  }

  function renderInventory(d, opts) {
    const products = list(d.products, 4);
    const exceptions = list(d.exceptions, 16);
    const children = [h('div', { class: 'card-head' }, [h('div', {}, [kicker('Inventory'), h('h2', { class: 'card-title', text: text(d.query, 'Stock') }), d.size ? h('p', { class: 'card-meta', text: `Size ${text(d.size)}` }) : null])])];
    if (exceptions.length) {
      children.push(h('p', { class: 'card-kicker', text: 'Needs attention' }));
      children.push(h('ul', { class: 'rows' }, exceptions.map((e) => stockRow(e, true))));
    } else {
      children.push(h('p', { class: 'card-note', text: `Nothing at or below ${num(d.low_stock_at) === null ? 'the low-stock line' : d.low_stock_at + ' left'}.` }));
    }
    const all = products.map((p) => h('div', {}, [
      h('p', { class: 'card-kicker', text: [text(p.title), num(p.total_inventory) !== null ? `${p.total_inventory} total` : ''].filter(Boolean).join(' · ') }),
      h('ul', { class: 'rows' }, list(p.variants, 16).map((v) => stockRow(v, false))),
    ]));
    if (all.length) {
      const full = h('div', { class: 'panel' }, all);
      full.hidden = true;
      const toggle = h('button', { class: 'link-btn', type: 'button', text: 'All variants', on: { click: () => {
        full.hidden = !full.hidden;
        toggle.textContent = full.hidden ? 'All variants' : 'Hide all variants';
      } } });
      children.push(toggle, full);
    }
    return card('inventory', children, opts);
  }

  function renderSales(d, opts) {
    const days = list(d.by_day, 31).filter((day) => day && typeof day === 'object');
    const stats = [
      [text(d.orders === null || d.orders === undefined ? '—' : d.orders), 'Orders'],
      [text(d.aov, '—'), 'Avg order'],
    ];
    return card('sales_summary', [
      kicker(text(d.title, 'Sales')),
      h('div', { class: 'big', text: text(d.revenue, '—') }),
      h('p', { class: 'card-meta', text: num(d.days) === 1 || !d.until ? formatDate(d.since, DAY_FMT) : [formatDate(d.since, DAY_FMT), formatDate(lastDayOf(d.until), DAY_FMT)].filter(Boolean).join(' → ') }),
      h('div', { class: 'stats' }, stats.map(([v, k]) => h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: v }), h('div', { class: 'stat-k', text: k })]))),
      days.length > 1 ? salesBars(days) : null,
      days.length ? h('ul', { class: 'rows compact' }, days.map((day) => h('li', { class: 'row' }, [
        h('span', { class: 'row-main', text: formatDate(dayNoon(day.date), DAY_ROW_FMT) || text(day.date, '—') }),
        h('span', { class: 'row-side' }, [
          h('strong', { text: text(day.revenue, '—') }),
          h('span', { class: 'card-meta', text: num(day.orders) === null ? '' : ` · ${day.orders} order${num(day.orders) === 1 ? '' : 's'}` }),
        ]),
      ]))) : null,
      d.complete === false ? h('p', { class: 'card-note', text: text(d.caveat, 'Partial figure.') }) : null,
      d.basis ? h('p', { class: 'card-note', text: text(d.basis) }) : null,
    ], opts);
  }
  const DAY_ROW_FMT = { weekday: 'short', day: 'numeric', month: 'short' };

  // Revenue per day as bars, from the money strings the Mac formatted. The height is a
  // clamped number of our own making, never a value from outside written into the page.
  function moneyValue(value) {
    const n = parseFloat(text(value).replace(/[^0-9.\-]/g, ''));
    return Number.isFinite(n) ? n : 0;
  }
  function salesBars(days) {
    const values = days.map((d) => moneyValue(d.revenue));
    const top = Math.max(1, ...values);
    return h('div', { class: 'bars', 'aria-hidden': 'true' }, days.map((d, i) => {
      const pct = Math.max(4, Math.min(100, Math.round((values[i] / top) * 100)));
      const bar = h('span', { class: 'bar', data: { pct: String(pct) } });
      if (bar.style) bar.style.height = `${pct}%`;
      return h('span', { class: 'bar-col', title: formatDate(dayNoon(d.date), DAY_ROW_FMT) }, [bar, h('span', { class: 'bar-day', text: formatDate(dayNoon(d.date), { weekday: 'narrow' }) })]);
    }));
  }
  // A calendar date with no time parses as UTC midnight, which is the previous evening west of
  // Greenwich; noon local is the same calendar day everywhere.
  function dayNoon(value) {
    const raw = text(value);
    return /^\d{4}-\d{2}-\d{2}$/.test(raw) ? `${raw}T12:00:00` : raw;
  }

  function renderEmailList(d, opts) {
    const threads = list(d.threads, 10);
    // A badge that is on every row is not information. In the inbox it separates customers
    // from strangers and earns its place; on the work queue every row is a customer by
    // construction, so three identical green badges were three pieces of furniture.
    const mixed = threads.some((t) => !t.known_customer) && threads.some((t) => t.known_customer);
    return card('email_list', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Email'), h('h2', { class: 'card-title', text: text(d.title, 'Email') }), h('p', { class: 'card-meta', text: num(d.count) === null ? '' : `${d.count} thread${d.count === 1 ? '' : 's'}` })])]),
      h('ul', { class: 'rows' }, threads.map((t) => {
        const row = h('li', { class: 'row tappable', role: 'button', tabindex: '0', data: { ref: text(t.thread_id), kind: 'email_thread' } }, [
          h('span', { class: 'row-main' }, [h('strong', { text: text(t.from, '—') }), ' — ', text(t.subject, '(no subject)')]),
          h('span', { class: 'row-sub', text: text(t.snippet) }),
          h('span', { class: 'row-side' }, [
            h('span', { class: 'card-meta', text: formatDate(t.date) }),
            mixed && t.known_customer ? badge('Customer', 'quiet ok') : null,
            t.likely_bulk ? badge('Bulk', 'quiet') : null,
          ]),
          rowActions(t, opts),
          // The affordance instead of the sentence. This card used to end with 'Say "read that
          // one" to open a thread.' — a line of instruction under rows that gave no sign of
          // being tappable at all. A chevron says it on every row, once, and costs no height.
          h('span', { class: 'row-go', 'aria-hidden': 'true', text: '\u203a' }),
        ]);
        row.addEventListener('click', () => row.classList.toggle('is-open'));
        return row;
      })),
      d.note ? h('p', { class: 'card-note', text: text(d.note) }) : null,
    ], opts);
  }

  // The buttons beside a row, exactly as the Mac listed them (app/actions/rows.py). The
  // tablet renders what it is given and posts back only WHICH action and WHICH row: the
  // arguments are built on the Mac, from a fresh read, and the change that comes back still
  // waits for a gesture. Nothing here decides what a button means.
  function rowActions(row, opts) {
    const actions = Array.isArray(row && row.actions) ? row.actions.slice(0, 3) : [];
    const ref = text(row && row.thread_id);
    if (!actions.length || !ref) return null;
    const onRow = opts && typeof opts.onRowAction === 'function' ? opts.onRowAction : null;
    return h('span', { class: 'row-actions' }, actions.map((a) => {
      const id = text(a && a.id);
      const button = h('button', {
        class: 'row-btn', type: 'button', text: text(a && a.label, 'Do'),
        title: text(a && a.detail), data: { action: id, ref },
        disabled: a && a.enabled === false ? 'disabled' : null,
      });
      button.addEventListener('click', (event) => {
        if (event && typeof event.stopPropagation === 'function') event.stopPropagation();
        if (!onRow || button.disabled) return;
        button.disabled = true;
        button.textContent = 'Preparing…';
        onRow(id, ref, button);
      });
      return button;
    }));
  }

  function renderEmailThread(d, opts) {
    const messages = list(d.messages, 6);
    const nodes = messages.map((m, i) => {
      const last = i === messages.length - 1;
      const msg = h('div', { class: `msg${last ? ' is-latest' : ' is-collapsed'}` }, [
        avatar(m.from),
        h('div', { class: 'msg-main' }, [
          h('div', { class: 'msg-head' }, [
            h('div', {}, [h('div', { class: 'msg-from', text: text(m.from, '—') }), h('div', { class: 'msg-addr', text: text(m.from_email) })]),
            h('div', { class: 'msg-date', text: formatDate(m.date) }),
          ]),
          h('p', { class: 'msg-body', text: text(m.body) }),
        ]),
      ]);
      if (!last) msg.addEventListener('click', () => msg.classList.toggle('is-collapsed'));
      return msg;
    });
    // The rail. `rail()` was called from one place — the order card — so an email had no
    // controls on the tablet at all: Reply, Rewrite and Archive were on the Mac and reachable
    // only by a spoken sentence, and the only way out of a thread was to put the tablet down.
    return card('email_thread', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Email thread'), h('h2', { class: 'card-title', text: text(d.subject, '(no subject)') }), h('p', { class: 'card-meta', text: [num(d.message_count) === null ? '' : `${d.message_count} message${d.message_count === 1 ? '' : 's'}`, d.truncated ? 'older messages not shown' : ''].filter(Boolean).join(' · ') })])]),
      linkedOrderStrip(d),
      rail(d.actions, opts, d.thread_id),
      h('div', {}, nodes),
    ], opts);
  }

  // The order this thread is about, under the head, from what the Mac worked out
  // (app/context/graph.py) and never from the words on the card. A confident link is one
  // tappable row; a possible one is up to three chips; nothing is a quiet line. `data-kind`
  // and `data-ref` are what the deck's click handler posts to `open.entity` — the same
  // command a tapped list row reaches — so the strip is a door, not a caption. The reasons
  // ride underneath in small type, because a wrong link on the thread the owner is about to
  // reply to is worse than none, and he can only judge it if he can see why it was drawn.
  function linkedOrderStrip(d) {
    const confidence = text(d.link_confidence, 'none');
    const why = strings(d.link_provenance, 4).join(' · ');
    const note = why ? h('p', { class: 'link-why', text: why }) : null;
    const chip = (o, cls) => {
      const ref = text(o.order_id);
      const words = [text(o.order_number, 'order'), text(o.total), text(o.fulfillment)].filter(Boolean).join(' · ');
      return h(ref ? 'button' : 'span', {
        class: `link-chip${cls ? ' ' + cls : ''}`, type: ref ? 'button' : null,
        data: ref ? { ref, kind: 'order' } : {},
      }, [h('span', { class: 'link-chip-label', text: words }), ref ? h('span', { class: 'row-go', 'aria-hidden': 'true', text: '\u203a' }) : null]);
    };
    const customer = d.linked_customer && typeof d.linked_customer === 'object' && text(d.linked_customer.customer_id)
      ? h('button', { class: 'link-chip link-customer', type: 'button', data: { ref: text(d.linked_customer.customer_id), kind: 'customer' } }, [
        h('span', { class: 'link-chip-label', text: text(d.linked_customer.name, 'Customer') }),
      ])
      : null;
    if (confidence === 'confident' && d.linked_order && typeof d.linked_order === 'object') {
      const o = d.linked_order;
      const ref = text(o.order_id);
      const row = h('div', {
        class: `link-strip is-confident${ref ? ' tappable' : ''}`, role: ref ? 'button' : null, tabindex: ref ? '0' : null,
        data: ref ? { ref, kind: 'order' } : {},
      }, [
        h('span', { class: 'link-kicker', text: 'Linked order' }),
        h('span', { class: 'link-main', text: [text(o.order_number, 'order'), text(o.total), text(o.fulfillment)].filter(Boolean).join(' · ') }),
        ref ? h('span', { class: 'row-go', 'aria-hidden': 'true', text: '\u203a' }) : null,
      ]);
      return h('div', { class: 'link-block' }, [row, customer ? h('div', { class: 'link-chips' }, [customer]) : null, note]);
    }
    const possible = list(d.possible_orders, 3);
    if (confidence === 'possible' && possible.length) {
      return h('div', { class: 'link-block is-possible' }, [
        h('span', { class: 'link-kicker', text: 'Possibly about' }),
        h('div', { class: 'link-chips' }, possible.map((o) => chip(o)).concat(customer ? [customer] : [])),
        note,
      ]);
    }
    return h('div', { class: 'link-block is-none' }, [
      h('p', { class: 'link-none', text: 'No confident order is linked' }),
      customer ? h('div', { class: 'link-chips' }, [customer]) : null,
      note,
    ]);
  }

  function renderEmailDraft(d, opts) {
    // An email after a proven change: saved as a draft in Gmail, or sent. There is no send
    // here — sending is a gesture on the confirmation card, answered by the Mac.
    const sent = text(d.state) === 'sent';
    return card('email_draft', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker(sent ? 'Sent' : 'Draft · saved in Gmail'), h('h2', { class: 'card-title', text: text(d.subject, '(no subject)') }), h('p', { class: 'card-sub', text: d.to ? `To ${text(d.to)}` : '' })]), h('div', { class: 'badges' }, [badge(sent ? 'Sent' : 'Draft', sent ? 'ok' : 'warn')])]),
      h('p', { class: 'msg-body', text: text(d.body) }),
      sent ? null : h('p', { class: 'future', text: 'Nothing has been sent. Say "send it" to send this draft, or send it from Gmail.' }),
    ], opts);
  }

  function renderAttention(d, opts) {
    const items = list(d.items, 8);
    const node = card('attention', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Attention'), h('h2', { class: 'card-title', text: `${items.length} require${items.length === 1 ? 's' : ''} attention` })])]),
      h('ul', { class: 'rows' }, items.map((a) => h('li', { class: 'row' }, [
        h('span', { class: 'row-main', text: text(a.title, '—') }),
        h('span', { class: 'row-sub', text: text(a.detail) }),
        h('span', { class: 'row-side' }, [badge(text(a.kind), a.level === 'red' ? 'bad' : a.level === 'green' ? 'ok' : 'warn')]),
      ]))),
    ], opts);
    if (d.for) node.dataset.for = text(d.for);
    return node;
  }

  // ------------------------------------------------------------------ actions
  //
  // A proposal the Mac has staged. The card shows what the Mac decided; the surface is how
  // the owner authorises it. The tap sends a proposal id and nothing else — no order, no
  // note, no argument — and the Mac executes what it stored.
  //
  // The dead time: a surface cannot be committed the instant it appears. A finger lifting
  // off the orb must never count as a tap on a card that materialised beneath it, so a
  // press that began before the surface armed does not commit when it ends, and nothing
  // commits while the app says it is busy (recording, submitting, waiting).

  // The grammar, as the tablet performs it. Each kind is one gesture with its own dead time:
  //   tap_commit        a tap, once the surface has armed
  //   swipe_commit      a swipe of the handle most of the way along the track, then release
  //   hold_to_arm       a hold of 900 ms (the Mac is told when it began), then a tap
  //   hold_drag_target  a hold of 900 ms, then, without lifting, the handle dragged onto the
  //                     target and released there
  // A hold is reported to the Mac the moment it begins (opts.onArm) and the Mac hands back a
  // token; the commit carries it. Nothing here decides what the change is or whether it may
  // be applied — the Mac decided both when it staged the card.
  const INTERACTIONS = ['tap_commit', 'swipe_commit', 'hold_to_arm', 'hold_drag_target'];
  const HOLD_MS = 900;
  const HOLD_MARGIN_MS = 150;       // the Mac measures the hold from its own clock, a round trip later
  const ARMED_FOR_MS = 5000;
  const SWIPE_FRACTION = 0.72;
  const SLOP_PX = 12;               // a wobble this big during a hold is a scroll, not a hold
  const DEFAULT_TRACK_PX = 300;

  function renderConfirmation(d, opts) {
    opts = opts || {};
    const risk = text(d.risk, text(d.tier, 'amber')) === 'red' ? 'red' : 'amber';
    const interaction = d.interaction && typeof d.interaction === 'object' ? d.interaction : {};
    const kind = text(interaction.kind, 'tap_commit');
    const supported = INTERACTIONS.indexOf(kind) !== -1;
    const armedAfter = num(interaction.armed_after_ms) === null ? 650 : Math.max(0, interaction.armed_after_ms);
    const status = text(d.status, 'pending');
    // The Mac already knows whether a gesture from this tablet could apply it. When it
    // cannot, the surface says so and never arms: an honest card beats a button that fails.
    const blocked = d.commit && typeof d.commit === 'object' && d.commit.allowed === false ? d.commit : null;
    const live = supported && status === 'pending' && Boolean(d.proposal_id) && !blocked;
    const label = live ? text(interaction.label, gestureLabel(kind)) : (blocked ? blockedLabel(blocked.code) : (supported ? settledLabel(status) : 'Needs a newer tablet build'));
    const surface = buildSurface(kind, label, text(interaction.target), live ? 'arming' : (blocked ? 'unavailable' : (supported ? status : 'unsupported')), live);
    const facts = list(d.facts, 8).filter((f) => text(f.value));
    const footer = text(interaction.footer, 'nothing happens until you tap');
    const node = card('confirmation', [
      h('div', { class: 'card-head' }, [
        h('div', { class: `mark ${risk === 'red' ? 'bad' : 'warn'}` }, h('span', { text: '!' })),
        h('div', {}, [
          kicker(blocked ? 'Prepared · cannot apply from here' : (risk === 'red' ? 'Proposed · needs care' : 'Proposed')),
          h('h2', { class: 'card-title', text: text(d.title, 'Confirm') }),
          h('p', { class: 'card-sub', text: text(d.entity, text(d.detail)) }),
        ]),
      ]),
      d.summary ? h('blockquote', { class: 'action-summary', text: text(d.summary) }) : null,
      // An email's whole text, when the change is an email: what the gesture sends, read here.
      d.body ? h('blockquote', { class: 'action-summary action-body' }, h('p', { class: 'msg-body', text: text(d.body) })) : null,
      // What the gesture authorises, fact by fact, from the Mac. The owner reads this, not
      // the model's sentence, before moving a hand.
      facts.length ? h('dl', { class: 'facts' }, facts.map((f) => [h('dt', { text: text(f.label) }), h('dd', { class: text(f.tone) || null, text: text(f.value) })]).flat()) : null,
      d.detail && d.entity ? h('p', { class: 'card-meta', text: text(d.detail) }) : null,
      surface,
      // The reason a gesture would be refused is the one line the owner must read: body
      // size, not the 11 px caption.
      blocked ? h('p', { class: 'card-sub action-why', text: text(blocked.reason) }) : null,
      h('p', { class: 'action-meta', text: live ? (num(d.ttl_s) !== null ? `Waits ${Math.round(d.ttl_s)} s · ${footer}` : capitalise(footer)) : '' }),
    ], Object.assign({ className: `tier-${risk} kind-${kind}` }, opts));
    node.dataset.proposal = text(d.proposal_id);
    node.dataset.ref = text(d.entity_ref);
    if (live) wireGesture(node, surface, kind, text(d.proposal_id), armedAfter, opts, num(d.ttl_s), (left) => `Waits ${left} s · ${footer}`);
    return node;
  }

  function capitalise(s) { const t = text(s); return t ? t.charAt(0).toUpperCase() + t.slice(1) : t; }

  function gestureLabel(kind) {
    return { tap_commit: 'Tap to apply', swipe_commit: 'Swipe to apply', hold_to_arm: 'Hold to arm, then tap', hold_drag_target: 'Hold, then drag to the target' }[kind] || 'Not available';
  }

  // The surface for a kind. A tap is a plain surface; a swipe and a drag carry a track with a
  // handle, and a drag carries a target at the far end that names the consequence.
  function buildSurface(kind, label, target, state, live) {
    const withTrack = kind === 'swipe_commit' || kind === 'hold_drag_target';
    const children = [h('span', { class: 'action-label', text: label }), h('span', { class: 'action-arm', 'aria-hidden': 'true' })];
    if (withTrack) {
      children.push(h('span', { class: 'action-track', 'aria-hidden': 'true' }, [
        h('span', { class: 'action-handle' }, [h('span', { class: 'action-grip', text: '›' })]),
        kind === 'hold_drag_target' ? h('span', { class: 'action-target', text: target || 'Drop to apply' }) : null,
      ]));
    }
    return h('div', {
      class: `action-surface kind-${kind}`, role: 'button', tabindex: live ? '0' : '-1', 'aria-disabled': 'true',
      data: { state, kind },
    }, children);
  }

  // Who is stopping the gesture, in five words: the Mac's switch, its allow-list, this
  // tablet's login, or Shopify's grant. "This tablet" is blamed only when it is the reason.
  function blockedLabel(code) {
    return {
      writes_disabled: 'Changes are switched off on the Mac', allow_list_missing: 'No allowed logins set on the Mac',
      not_authorised: "This tablet's login is not on the Mac's list", not_authorised_local: 'The Mac itself may not apply changes',
      scope_missing: 'Shopify has not granted the scope this needs',
    }[text(code)] || "Can't apply from here";
  }

  function settledLabel(status) {
    return { verified: 'Applied', stale: 'Not applied', expired: 'Expired', revoked: 'Withdrawn', failed: 'Not applied', unverified: 'Not confirmed', executing: 'Applying…', executed: 'Applying…' }[status] || 'Not available';
  }

  // One wiring for every kind. The states a surface passes through:
  //   arming → armed → (holding → held →) committing → a settled state
  // A press that began before arming never counts, whatever it ends as; nothing counts while
  // the app says it is busy; and a settled surface answers to nothing.
  function wireGesture(node, surface, kind, proposalId, armedAfter, opts, ttlS, word) {
    const now = opts.now || (() => Date.now());
    const shown = now();
    const timers = opts.timers || { set: (fn, ms) => setTimeout(fn, ms), clear: (id) => clearTimeout(id) };
    const trackWidth = () => {
      const track = surface.querySelector ? surface.querySelector('.action-track') : null;
      const w = track && typeof track.clientWidth === 'number' && track.clientWidth > 0 ? track.clientWidth : (num(opts.trackWidth) || DEFAULT_TRACK_PX);
      const handle = surface.querySelector ? surface.querySelector('.action-handle') : null;
      const hw = handle && typeof handle.clientWidth === 'number' && handle.clientWidth > 0 ? handle.clientWidth : 56;
      return Math.max(1, w - hw);
    };
    let committed = false;
    let press = null;        // { at, x, y, dx } for the press in progress
    let holdTimer = null;
    let heldTimer = null;
    let nonce = '';          // the Mac's token for the hold in progress
    let armRequest = 0;
    const armed = () => now() - shown >= armedAfter;
    const blocked = () => (typeof opts.blocked === 'function' ? Boolean(opts.blocked()) : false);
    const state = () => surface.dataset.state;
    const setState = (s) => { surface.dataset.state = s; surface.setAttribute('aria-disabled', s === 'armed' || s === 'held' ? 'false' : 'true'); };
    const labelEl = surface.childNodes[0];
    const baseLabel = labelEl.textContent;
    const say = (words) => { labelEl.textContent = String(words); };
    const handle = surface.querySelector ? surface.querySelector('.action-handle') : null;
    const moveHandle = (px) => { if (handle && handle.style && handle.style.setProperty) handle.style.setProperty('--dx', `${Math.round(px)}px`); surface.dataset.dx = String(Math.round(px)); };
    const needsHold = kind === 'hold_to_arm' || kind === 'hold_drag_target';
    const needsTrack = kind === 'swipe_commit' || kind === 'hold_drag_target';
    // The visible fill lasts exactly as long as the arming does: one number, ours.
    if (surface.style && surface.style.setProperty) surface.style.setProperty('--arm-ms', `${Math.round(armedAfter)}ms`);
    if (surface.style && surface.style.setProperty) surface.style.setProperty('--hold-ms', `${HOLD_MS + HOLD_MARGIN_MS}ms`);
    const armTimer = timers.set(() => { if (!committed && state() === 'arming') setState('armed'); }, armedAfter);
    const expiryTimer = ttlS !== null && ttlS !== undefined ? timers.set(() => {
      if (!committed && ['arming', 'armed', 'holding', 'held'].indexOf(state()) !== -1) node.settle('expired', 'Expired');
    }, Math.max(0, ttlS * 1000 - 1000)) : null;
    const metas = node.querySelectorAll ? node.querySelectorAll('.action-meta') : [];
    const meta = metas.length ? metas[metas.length - 1] : null;
    let countdown = null;
    if (meta && word && ttlS !== null && ttlS !== undefined) {
      const tick = () => {
        const left = Math.max(0, Math.round(ttlS - (now() - shown) / 1000));
        if (committed) return;
        meta.textContent = word(left);
        if (left > 0) countdown = timers.set(tick, 1000);
      };
      countdown = timers.set(tick, 1000);
    }
    const clearHold = () => { if (holdTimer !== null) { timers.clear(holdTimer); holdTimer = null; } };
    const clearHeld = () => { if (heldTimer !== null) { timers.clear(heldTimer); heldTimer = null; } };
    const disarmHold = (why) => {
      // Back to armed: the hold did not complete, or it lapsed. The token is worthless now.
      clearHold(); clearHeld(); nonce = ''; press = null; moveHandle(0);
      if (!committed && ['holding', 'held'].indexOf(state()) !== -1) setState('armed');
      say(why || baseLabel);
      if (why) timers.set(() => { if (!committed && state() === 'armed') say(baseLabel); }, 1400);
    };
    const commit = () => {
      committed = true;
      clearHold(); clearHeld();
      setState('committing');
      say('Applying…');
      if (typeof opts.onCommit === 'function') opts.onCommit(proposalId, node, nonce);
    };
    node.settle = (s, label) => {
      timers.clear(armTimer);
      if (expiryTimer !== null) timers.clear(expiryTimer);
      if (countdown !== null) { timers.clear(countdown); countdown = null; }
      clearHold(); clearHeld();
      if (meta && s !== 'armed') meta.textContent = '';
      committed = s !== 'armed';
      press = null; nonce = '';
      moveHandle(0);
      setState(s);
      if (label !== undefined) say(label);
    };

    // ---- the hold: told to the Mac as it begins; completes only if the hand stays still.
    const beginHold = () => {
      setState('holding');
      const request = ++armRequest;
      nonce = '';
      const holdFor = (ms) => {
        clearHold();
        holdTimer = timers.set(() => {
          holdTimer = null;
          if (committed || state() !== 'holding' || !press) return;
          if (typeof opts.onArm === 'function' && !nonce) {
            // The hold is long enough but the Mac has not answered yet: keep holding a little.
            holdTimer = timers.set(() => {
              holdTimer = null;
              if (committed || state() !== 'holding' || !press) return;
              if (!nonce) { disarmHold("The Mac hasn't armed it"); return; }
              held();
            }, 1200);
            return;
          }
          held();
        }, ms);
      };
      if (typeof opts.onArm === 'function') {
        Promise.resolve(opts.onArm(proposalId)).then((token) => {
          if (request !== armRequest || committed) return;
          if (!token) { disarmHold("The Mac won't arm this"); return; }
          nonce = String(token);
          // The Mac measures the hold from when it stamped this token, which is never later
          // than now: the hold here runs its full length from now as well, so the Mac's
          // clock is met however long the round trip took.
          if (state() === 'holding' && press) holdFor(HOLD_MS + HOLD_MARGIN_MS);
        }).catch(() => { if (request === armRequest && !committed) disarmHold("The Mac won't arm this"); });
      }
      holdFor(HOLD_MS + HOLD_MARGIN_MS);
    };
    const held = () => {
      setState('held');
      say(kind === 'hold_drag_target' ? 'Now drag to the target' : 'Armed · tap to apply');
      // A tap or a drag must follow within the window the Mac keeps, or the arming lapses
      // here as it does there — the surface never says "held" about a hold the Mac forgot.
      heldTimer = timers.set(() => { if (!committed && state() === 'held') disarmHold('Hold again'); }, ARMED_FOR_MS);
    };

    const canBegin = () => armed() && !blocked() && !committed;

    surface.addEventListener('contextmenu', (e) => { if (e && e.preventDefault) e.preventDefault(); });
    surface.addEventListener('selectstart', (e) => { if (e && e.preventDefault) e.preventDefault(); });

    surface.addEventListener('pointerdown', (e) => {
      const x = e && typeof e.clientX === 'number' ? e.clientX : 0;
      const y = e && typeof e.clientY === 'number' ? e.clientY : 0;
      if (e && e.currentTarget && typeof e.currentTarget.setPointerCapture === 'function' && e.pointerId !== undefined) {
        try { e.currentTarget.setPointerCapture(e.pointerId); } catch (error) { /* unsupported */ }
      }
      const s = state();
      if (!canBegin()) { press = null; return; }
      if (s === 'armed') {
        press = { at: now(), x, y, dx: 0 };
        surface.dataset.pressed = 'true';
        if (needsHold) beginHold();
        return;
      }
      if (s === 'held' && kind === 'hold_to_arm') {
        // The tap that follows the hold.
        press = { at: now(), x, y, dx: 0, tap: true };
        surface.dataset.pressed = 'true';
        return;
      }
      press = null;
    });

    surface.addEventListener('pointermove', (e) => {
      if (!press || committed) return;
      const x = e && typeof e.clientX === 'number' ? e.clientX : press.x;
      const y = e && typeof e.clientY === 'number' ? e.clientY : press.y;
      const dx = x - press.x;
      const dy = y - press.y;
      const s = state();
      if (s === 'holding') {
        if (Math.abs(dx) > SLOP_PX || Math.abs(dy) > SLOP_PX) { disarmHold('Hold still'); }
        return;
      }
      if (needsTrack && (s === 'armed' && kind === 'swipe_commit' || s === 'held' && kind === 'hold_drag_target')) {
        if (Math.abs(dy) > 2 * SLOP_PX && dx < SLOP_PX) { press = null; moveHandle(0); if (s === 'held') disarmHold(''); return; }   // the scroller wins
        press.dx = Math.max(0, Math.min(trackWidth(), dx));
        moveHandle(press.dx);
      }
    });

    const end = (cancelled) => {
      if (!press) { surface.dataset.pressed = 'false'; return; }
      const p = press;
      press = null;
      surface.dataset.pressed = 'false';
      const s = state();
      if (cancelled || committed || blocked() || !armed()) { if (s === 'holding' || s === 'held') disarmHold(''); moveHandle(0); return; }
      if (kind === 'tap_commit') { if (s === 'armed') commit(); return; }
      if (kind === 'swipe_commit') {
        if (s === 'armed' && p.dx >= SWIPE_FRACTION * trackWidth()) commit(); else moveHandle(0);
        return;
      }
      if (kind === 'hold_to_arm') {
        if (s === 'holding') { disarmHold(''); return; }          // lifted before the hold completed
        if (s === 'held' && p.tap && nonce) { commit(); return; }  // the tap after the hold
        return;                                                    // the lift that ends the hold itself
      }
      if (kind === 'hold_drag_target') {
        if (s === 'holding') { disarmHold(''); return; }
        if (s === 'held') { if (p.dx >= SWIPE_FRACTION * trackWidth() && nonce) commit(); else disarmHold(''); }
      }
    };
    surface.addEventListener('pointerup', () => end(false));
    surface.addEventListener('pointercancel', () => end(true));
    surface.addEventListener('pointerleave', () => { if (kind === 'tap_commit') end(true); });
    surface.addEventListener('keydown', (e) => {
      // A keyboard has no hold: Enter applies a tap kind only.
      if (kind !== 'tap_commit') return;
      if ((e.key === 'Enter' || e.key === ' ') && canBegin() && state() === 'armed') {
        if (e.preventDefault) e.preventDefault();
        commit();
      }
    });
  }

  // Kept for the success card's undo and for anyone who only ever needs a tap.
  function wireTapCommit(node, surface, proposalId, armedAfter, opts, ttlS, word) {
    return wireGesture(node, surface, 'tap_commit', proposalId, armedAfter, opts, ttlS, word);
  }

  const CHECK = () => {
    const svg = doc().createElementNS ? doc().createElementNS('http://www.w3.org/2000/svg', 'svg') : h('span');
    if (svg.setAttribute) {
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      const path = doc().createElementNS ? doc().createElementNS('http://www.w3.org/2000/svg', 'path') : h('span');
      if (path.setAttribute) path.setAttribute('d', 'M5 12.5l4.5 4.5L19 7');
      svg.appendChild(path);
    }
    return svg;
  };

  function renderSuccess(d, opts) {
    opts = opts || {};
    const node = card('success', [
      h('div', { class: 'card-head' }, [h('div', { class: 'mark ok' }, CHECK()), h('div', {}, [kicker('Done'), h('h2', { class: 'card-title', text: text(d.title, 'Done') }), h('p', { class: 'card-sub', text: text(d.detail) })])]),
      // What the Mac's proof could not yet see: said on the card as well as out loud.
      d.note ? h('p', { class: 'card-meta note-line', text: text(d.note) }) : null,
    ], Object.assign({ className: 'success' }, opts));
    // Keyed by the proposal that is still live. The forward one is settled and nothing looks
    // it up again; the undo is the card the Mac may name in a turn's `revoked` list.
    // A reversible action offers its undo: a second proposal the Mac staged, authorised the
    // same way (its own dead time, its own tap) and executed by the same path.
    const undo = d.undo && typeof d.undo === 'object' && d.undo.proposal_id ? d.undo : null;
    if (!undo && d.proposal_id) node.dataset.proposal = text(d.proposal_id);
    if (undo) {
      const armedAfter = num(undo.armed_after_ms) === null ? 650 : undo.armed_after_ms;
      // The undo is as grave as the change it reverses: its kind comes from the Mac.
      const kind = INTERACTIONS.indexOf(text(undo.interaction)) !== -1 ? text(undo.interaction) : 'tap_commit';
      const surface = buildSurface(kind, kind === 'tap_commit' ? text(undo.label, 'Undo') : `${text(undo.label, 'Undo')} · ${gestureLabel(kind).toLowerCase()}`, '', 'arming', true);
      surface.classList.add('quiet');
      node.dataset.proposal = text(undo.proposal_id);
      node.appendChild(surface);
      node.appendChild(h('p', { class: 'action-meta', text: num(undo.ttl_s) !== null ? `Undo available for ${Math.round(undo.ttl_s)} s` : '' }));
      // The undo has its own minute on the Mac's clock, and says how much of it is left.
      wireGesture(node, surface, kind, text(undo.proposal_id), armedAfter, opts, num(undo.ttl_s), (left) => (left > 0 ? `Undo available for ${left} s` : 'The undo has expired.'));
    }
    return node;
  }

  function renderError(d, opts) {
    return card('error', [
      h('div', { class: 'card-head' }, [h('div', { class: 'mark bad' }, h('span', { text: '×' })), h('div', {}, [kicker(text(d.service, 'assistant')), h('h2', { class: 'card-title', text: text(d.title, 'Something went wrong') }), h('p', { class: 'card-sub', text: text(d.recovery) })])]),
    ], opts);
  }

  // ---- the read layer's cards: figures the Mac formatted, drawn as text and bars.

  function analyticHead(kicker_, d, fallback) {
    return h('div', { class: 'card-head' }, [h('div', {}, [kicker(kicker_), h('h2', { class: 'card-title', text: text(d.title, fallback) }), h('p', { class: 'card-meta', text: text(d.subtitle) })])]);
  }

  function analyticFoot(d) {
    return [
      d.complete === false ? h('p', { class: 'card-note', text: 'Partial: the Mac is still reading Shopify.' }) : null,
      d.truncated ? h('p', { class: 'card-note', text: 'More rows than shown.' }) : null,
      d.note ? h('p', { class: 'card-note', text: text(d.note) }) : null,
    ];
  }

  function legend(d) {
    const measured = Array.isArray(d.measured) ? d.measured : [];
    const derived = Array.isArray(d.derived) ? d.derived : [];
    if (!derived.length) return null;
    return h('p', { class: 'legend' }, [
      measured.length ? h('span', { text: `Measured: ${measured.join(', ')}` }) : null,
      h('span', { class: 'derived', text: `Derived: ${derived.join(', ')}` }),
    ]);
  }

  function renderRanking(d, opts) {
    const rows = list(d.rows, 25);
    const kick = d.mode === 'restock' ? 'Restock priority' : 'Ranking';
    return card('ranking', [
      analyticHead(kick, d, d.mode === 'restock' ? 'Restock priority' : 'Best sellers'),
      h('ol', { class: 'rank-rows' }, rows.map((r) => {
        const primary = r.primary && typeof r.primary === 'object' ? r.primary : {};
        const secondary = r.secondary && typeof r.secondary === 'object' ? r.secondary : null;
        const pct = num(r.pct);
        const fill = pct === null ? null : h('span', { class: 'rank-fill' });
        if (fill && fill.style && fill.style.setProperty) fill.style.setProperty('--w', `${Math.max(0, Math.min(100, pct))}%`);
        const li = h('li', { class: `rank${r.known === false ? ' is-unknown' : ''}`, data: { ref: text(r.ref), kind: text(r.kind) } }, [
          h('span', { class: 'rank-n', text: num(r.rank) === null ? '' : String(r.rank) }),
          h('div', { class: 'rank-main' }, [
            h('div', { class: 'rank-label', text: text(r.label, '—') }),
            r.sublabel ? h('div', { class: 'rank-sub', text: text(r.sublabel) }) : null,
            fill ? h('div', { class: 'rank-track' }, fill) : null,
            list(r.lines, 6).length ? h('div', { class: 'rank-lines' }, list(r.lines, 6).map((l) => h('span', { class: l.derived ? 'derived' : '', text: `${text(l.value, '—')} ${text(l.label)}` }))) : null,
          ]),
          h('div', { class: 'rank-side' }, [
            h('div', { class: 'rank-v', text: text(primary.value, '—') }),
            h('div', { class: 'rank-k', text: text(primary.label) }),
            secondary ? h('div', { class: 'card-meta', text: `${text(secondary.value, '—')} ${text(secondary.label)}` }) : null,
          ]),
        ]);
        return li;
      })),
      list(d.totals, 4).length ? h('div', { class: `stats${list(d.totals, 4).length === 3 ? ' three' : ''}` }, list(d.totals, 4).map((t) => h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: text(t.value, '—') }), h('div', { class: 'stat-k', text: text(t.label) })]))) : null,
      legend(d),
    ].concat(analyticFoot(d)), opts);
  }

  function renderMetricGroup(d, opts) {
    const metrics = list(d.metrics, 6);
    return card('metric_group', [
      analyticHead('Figures', d, 'Sales'),
      h('div', { class: `stats${metrics.length === 3 ? ' three' : ''}` }, metrics.map((m) => h('div', { class: 'stat' }, [
        h('div', { class: 'stat-v', text: text(m.value, '—') }),
        h('div', { class: 'stat-k', text: `${text(m.label)}${m.measured === false ? ' · derived' : ''}` }),
      ]))),
    ].concat(analyticFoot(d)), opts);
  }

  function renderTable(d, opts) {
    const columns = list(d.columns, 8);
    const rows = list(d.rows, 25);
    return card('table', [
      analyticHead('Table', d, 'Table'),
      h('div', { class: 'tbl-wrap' }, h('table', { class: 'tbl' }, [
        h('thead', {}, h('tr', {}, columns.map((c) => h('th', { class: c.numeric ? 'num' : '', text: text(c.label) })))),
        h('tbody', {}, rows.map((r) => h('tr', { data: { ref: text(r.ref) } }, (Array.isArray(r.cells) ? r.cells.slice(0, 8) : []).map((cell, i) => h('td', { class: columns[i] && columns[i].numeric ? 'num' : '', text: text(cell, '—') }))))),
      ])),
    ].concat(analyticFoot(d)), opts);
  }

  function renderComparison(d, opts) {
    const current = d.current && typeof d.current === 'object' ? d.current : {};
    const previous = d.previous && typeof d.previous === 'object' ? d.previous : {};
    const col = (side, cls) => h('div', { class: `compare-col ${cls}` }, [
      h('div', { class: 'compare-k', text: text(side.label, cls === 'now' ? 'This period' : 'Before') }),
      list(side.metrics, 4).map((m) => h('div', { class: 'compare-row' }, [h('span', { class: 'card-meta', text: text(m.label) }), h('strong', { text: text(m.value, '—') })])),
    ]);
    return card('comparison', [
      analyticHead('Compared', d, 'Compared'),
      h('div', { class: 'compare' }, [col(current, 'now'), col(previous, 'then')]),
      list(d.changes, 4).length ? h('div', { class: 'changes' }, list(d.changes, 4).map((c) => h('span', { class: `change ${text(c.direction, 'flat')}`, text: `${text(c.label)} ${text(c.delta, '')} (${text(c.pct, '—')})`.replace('  ', ' ') }))) : null,
    ].concat(analyticFoot(d)), opts);
  }

  function renderVariantMatrix(d, opts) {
    const rows = Array.isArray(d.rows) ? d.rows.slice(0, 12).map((r) => text(r)) : [];
    const cols = Array.isArray(d.cols) ? d.cols.slice(0, 10).map((c) => text(c)) : [];
    const cells = list(d.cells, 64);
    const at = (r, c) => cells.find((x) => text(x.row) === r && text(x.col) === c);
    let top = 0;
    for (const c of cells) top = Math.max(top, num(c.value) || 0);
    return card('variant_matrix', [
      analyticHead('By size', d, 'Sizes'),
      h('div', { class: 'matrix-wrap' }, h('table', { class: 'matrix' }, [
        h('thead', {}, h('tr', {}, [h('th', { text: text(d.row_label) })].concat(cols.map((c) => h('th', { text: c }))))),
        h('tbody', {}, rows.map((r) => h('tr', {}, [h('td', { text: r })].concat(cols.map((c) => {
          const cell = at(r, c);
          const value = cell ? num(cell.value) : null;
          return h('td', { class: value === null ? 'zero' : (top && value === top ? 'hot' : ''), text: cell ? text(cell.display, '—') : '·' });
        }))))),
      ])),
      d.metric ? h('p', { class: 'card-meta', text: text(d.metric) }) : null,
    ].concat(analyticFoot(d)), opts);
  }

  function renderTrend(d, opts) {
    const points = list(d.points, 31);
    const values = points.map((p) => Math.max(0, num(p.value) || 0));
    const top = Math.max(1, ...values);
    return card('trend', [
      analyticHead('Trend', d, 'Trend'),
      d.total ? h('div', { class: 'trend-total', text: text(d.total) }) : null,
      points.length ? h('div', { class: 'bars', 'aria-hidden': 'true' }, points.map((p, i) => {
        const pct = Math.max(4, Math.min(100, Math.round((values[i] / top) * 100)));
        const bar = h('span', { class: 'bar', data: { pct: String(pct) } });
        if (bar.style) bar.style.height = `${pct}%`;
        return h('span', { class: 'bar-col', title: text(p.label) }, [bar, h('span', { class: 'bar-day', text: text(p.label).slice(-2) })]);
      })) : null,
      points.length ? h('ul', { class: 'rows compact' }, points.slice(-7).map((p) => h('li', { class: 'row' }, [h('span', { class: 'row-main', text: text(p.label) }), h('span', { class: 'row-side' }, h('strong', { text: text(p.display, '—') }))]))) : null,
      d.metric ? h('p', { class: 'card-meta', text: text(d.metric) }) : null,
    ].concat(analyticFoot(d)), opts);
  }

  // The working set: what "these" means now, and what it comes to.
  //
  // This card always follows one that has just listed the very same members, and the nav bar
  // carries the set as a chip besides — so a full-dress card repeating the title, re-listing
  // "#1940 · #1938 · #1939" and explaining the word "these" was 276px of a 1280px screen to
  // say three things the owner had just read. What is genuinely only here is the arithmetic
  // over the set, so that is what is left: a strip of totals under the list they belong to.
  function renderWorkingSet(d, opts) {
    const lines = list(d.lines, 3);
    const where = d.step === 'filter' ? 'Narrowed' : d.step === 'correlate' ? 'Cross-referenced' : 'These';
    const node = card('working_set', [
      h('p', { class: 'set-strip-head' }, [
        h('span', { class: 'set-strip-kicker', text: where }),
        h('span', { text: `${num(d.count) === null ? '?' : d.count} ${text(d.kind, 'items')}${d.truncated ? ' · first 500' : ''}` }),
        d.parent_label ? h('span', { class: 'set-strip-from', text: `from ${text(d.parent_label)}` }) : null,
      ]),
      lines.length ? h('div', { class: `stats${lines.length === 3 ? ' three' : ''}` }, lines.map((l) => h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: text(l.value, '—') }), h('div', { class: 'stat-k', text: text(l.label) })]))) : null,
    ], opts);
    node.classList.add('set-strip');
    node.dataset.set = text(d.set_id);
    return node;
  }

  // ---- what this build can do. The manifest, grouped by the part of the shop it touches.
  // Thirty capabilities read aloud are not a list; the sentence stays one line and this is
  // the list. Chips are questions the fast lane has a recipe for, so tapping one is answered
  // without the model — they post the same text a spoken question would.

  function capabilityRow(item) {
    const state = text(item.state);
    const tone = state === 'ready' ? 'good' : state === 'blocked' ? 'bad' : state === 'disabled' ? 'quiet' : 'quiet';
    const kindLabel = item.kind === 'change' ? 'Change' : item.kind === 'bulk' ? 'Bulk' : 'Read';
    return h('li', { class: 'cap-row' }, [
      h('div', { class: 'cap-main' }, [
        h('span', { class: 'cap-what', text: text(item.what, item.name) }),
        h('span', { class: 'cap-kind', text: kindLabel }),
      ]),
      state && state !== 'ready' ? badge(state, tone) : null,
    ]);
  }

  function renderCapability(d, opts) {
    const groups = list(d.groups, 8);
    const counts = d.counts && typeof d.counts === 'object' ? d.counts : {};
    const changed = d.changed && typeof d.changed === 'object' ? d.changed : null;
    const examples = strings(d.examples, 6);
    const meta = [];
    if (num(counts.reads) !== null) meta.push(`${counts.reads} readings`);
    if (num(counts.changes) !== null) meta.push(d.writes_enabled ? `${counts.changes} changes` : 'changes off');
    if (num(counts.bulk) !== null && counts.bulk) meta.push(`${counts.bulk} bulk`);
    const panels = groups.map((g) => ({
      name: text(g.area, 'other'),
      label: text(g.label, 'Other'),
      node: [
        h('ul', { class: 'cap-rows' }, list(g.items, 10).map(capabilityRow)),
        g.truncated ? h('p', { class: 'card-note', text: 'More than shown.' }) : null,
      ],
    }));
    const node = card('capability', [
      h('div', { class: 'card-head' }, [h('div', {}, [
        kicker('Capabilities'),
        h('h2', { class: 'card-title', text: text(d.title, 'What this can do') }),
        h('p', { class: 'card-meta', text: meta.join(' \u00b7 ') }),
      ])]),
      d.note ? h('p', { class: 'card-note', text: text(d.note) }) : null,
      changed && (strings(changed.added, 12).length || strings(changed.gone, 12).length)
        ? section('cap-changed', 'Since the last build', [
            strings(changed.added, 12).length
              ? h('ul', { class: 'cap-rows' }, strings(changed.added, 12).map((x) => h('li', { class: 'cap-row new', text: '+ ' + x })))
              : null,
            strings(changed.gone, 12).length
              ? h('ul', { class: 'cap-rows' }, strings(changed.gone, 12).map((x) => h('li', { class: 'cap-row gone', text: '\u2212 ' + x })))
              : null,
          ])
        : null,
      panels.length ? tabs(panels, { initial: opts && opts.tab, onChange: opts && opts.onTab ? (name, label) => opts.onTab('capability', name, label) : null }) : null,
      examples.length
        ? section('cap-examples', 'Try asking', [
            h('div', { class: 'chips' }, examples.map((q) => {
              const chip = h('button', { class: 'chip', type: 'button', text: q });
              chip.dataset.ask = q;
              return chip;
            })),
          ])
        : null,
    ], opts);
    node.dataset.build = text(d.build);
    return node;
  }

  // ---- bulk changes: one card for many proposals, and the count afterwards. The gesture
  // wiring is the confirmation card's; the id it names is the batch's.

  function renderBatchAction(d, opts) {
    opts = opts || {};
    const risk = text(d.risk, 'amber') === 'red' ? 'red' : 'amber';
    const interaction = d.interaction && typeof d.interaction === 'object' ? d.interaction : {};
    const kind = text(interaction.kind, 'hold_to_arm');
    const supported = INTERACTIONS.indexOf(kind) !== -1;
    const armedAfter = num(interaction.armed_after_ms) === null ? 650 : Math.max(0, interaction.armed_after_ms);
    const status = text(d.status, 'pending');
    const blocked = d.commit && typeof d.commit === 'object' && d.commit.allowed === false ? d.commit : null;
    const live = supported && status === 'pending' && Boolean(d.batch_id) && !blocked;
    const label = live ? text(interaction.label, gestureLabel(kind)) : (blocked ? blockedLabel(blocked.code) : (supported ? settledLabel(status) : 'Needs a newer tablet build'));
    const surface = buildSurface(kind, label, text(interaction.target, 'Apply to all'), live ? 'arming' : (blocked ? 'unavailable' : (supported ? status : 'unsupported')), live);
    const scope = d.set && typeof d.set === 'object' ? d.set : {};
    const eligible = num(d.eligible) === null ? 0 : d.eligible;
    const requested = num(d.requested) === null ? eligible : d.requested;
    const excluded = list(d.excluded, 50);
    const members = Array.isArray(d.members) ? d.members.map((m) => text(m)).filter(Boolean).slice(0, 50) : [];
    const facts = list(d.facts, 8).filter((f) => text(f.value));
    const footer = text(interaction.footer, 'nothing happens until you hold the card');
    const preview = d.preview && typeof d.preview === 'object' ? d.preview : null;
    const node = card('batch_action', [
      h('div', { class: 'card-head' }, [
        h('div', { class: `mark ${risk === 'red' ? 'bad' : 'warn'}` }, h('span', { text: String(eligible) })),
        h('div', {}, [
          kicker(blocked ? 'Prepared · cannot apply from here' : `Proposed for ${eligible} of ${requested}`),
          h('h2', { class: 'card-title', text: text(d.title, 'Apply to all') }),
          h('p', { class: 'card-sub', text: `${text(scope.label, 'the set')} · ${num(scope.count) === null ? requested : scope.count} ${text(scope.kind, 'items')}` }),
        ]),
      ]),
      d.summary ? h('blockquote', { class: 'action-summary', text: text(d.summary) }) : null,
      // A draft campaign: one member's email as it will be saved is the card; the template
      // it was filled from sits behind a fold, named as a template.
      preview && (preview.subject || preview.body) ? h('div', { class: 'batch-preview' }, [
        h('p', { class: 'card-meta', text: `As it will be saved for ${text(preview.to, 'the first customer')}` }),
        preview.subject ? h('p', { class: 'batch-preview-subject', text: text(preview.subject) }) : null,
        preview.body ? h('p', { class: 'msg-body', text: text(preview.body) }) : null,
      ]) : null,
      d.body ? h('details', { class: 'batch-members' }, [
        h('summary', { text: preview ? 'The template · filled in for each one' : 'The text' }),
        h('p', { class: 'msg-body', text: text(d.body) }),
      ]) : null,
      facts.length ? h('dl', { class: 'facts' }, facts.map((f) => [h('dt', { text: text(f.label) }), h('dd', { class: text(f.tone) || null, text: text(f.value) })]).flat()) : null,
      d.detail ? h('p', { class: 'card-meta', text: text(d.detail) }) : null,
      // Who is left out, and why: read before the hand moves; a long list sits behind a fold.
      excluded.length ? (excluded.length <= 3
        ? h('div', { class: 'batch-excluded' }, [
          h('p', { class: 'card-note', text: `${excluded.length} excluded` }),
          h('ul', { class: 'batch-list' }, excluded.map((x) => h('li', {}, [h('span', { class: 'batch-item', text: text(x.label) }), h('span', { class: 'batch-why', text: text(x.reason) })]))),
        ])
        : h('details', { class: 'batch-members batch-excluded' }, [
          h('summary', { text: `${excluded.length} excluded · ${excluded.slice(0, 3).map((x) => text(x.label)).join(' · ')} …` }),
          h('ul', { class: 'batch-list' }, excluded.map((x) => h('li', {}, [h('span', { class: 'batch-item', text: text(x.label) }), h('span', { class: 'batch-why', text: text(x.reason) })]))),
        ])) : null,
      // Every member the gesture will touch, one tap away, never hidden behind a count.
      members.length ? h('details', { class: 'batch-members' }, [
        h('summary', { text: `All ${members.length} · ${members.slice(0, 4).join(' · ')}${members.length > 4 ? ' …' : ''}` }),
        h('ul', { class: 'batch-list' }, members.map((m) => h('li', {}, h('span', { class: 'batch-item', text: m })))),
      ]) : null,
      surface,
      blocked ? h('p', { class: 'card-sub action-why', text: text(blocked.reason) }) : null,
      h('p', { class: 'action-meta', text: live ? (num(d.ttl_s) !== null ? `Waits ${Math.round(d.ttl_s)} s · ${footer}` : capitalise(footer)) : '' }),
    ], Object.assign({ className: `tier-${risk} kind-${kind} batch` }, opts));
    node.dataset.proposal = text(d.batch_id);
    node.dataset.set = text(scope.set_id);
    if (live) wireGesture(node, surface, kind, text(d.batch_id), armedAfter, opts, num(d.ttl_s), (left) => `Waits ${left} s · ${footer}`);
    return node;
  }

  function renderBatchResult(d, opts) {
    opts = opts || {};
    const counts = d.counts && typeof d.counts === 'object' ? d.counts : {};
    const n = (k) => (num(counts[k]) === null ? 0 : counts[k]);
    const rows = list(d.rows, 50);
    const all = d.all_verified === true;
    const stat = (label, key) => (n(key) ? h('div', { class: `stat ${key === 'verified' ? 'ok' : 'warn'}` }, [h('div', { class: 'stat-v', text: String(n(key)) }), h('div', { class: 'stat-k', text: label })]) : null);
    const node = card('batch_result', [
      h('div', { class: 'card-head' }, [
        h('div', { class: `mark ${all ? 'ok' : 'warn'}` }, all ? CHECK() : h('span', { text: String(n('verified')) })),
        h('div', {}, [kicker(text(d.summary, all ? 'Done' : 'Done in part')), h('h2', { class: 'card-title', text: text(d.title, 'Done') }), h('p', { class: 'card-sub', text: text(d.detail) })]),
      ]),
      h('div', { class: 'stats counts' }, [stat('applied', 'verified'), stat('excluded', 'excluded'), stat('not applied', 'failed'), stat('changed meanwhile', 'stale'), stat('not confirmed', 'unverified'), stat('not attempted', 'not_attempted')].filter(Boolean)),
      d.note ? h('p', { class: 'card-note bad', text: text(d.note) }) : null,
      rows.length ? h('details', { class: 'batch-members', open: all ? null : '' }, [
        h('summary', { text: `Each of the ${rows.length}` }),
        h('ul', { class: 'batch-list' }, rows.map((r) => h('li', { class: text(r.code) === 'verified' ? 'ok' : (text(r.code) === 'excluded' ? '' : 'bad') }, [h('span', { class: 'batch-item', text: text(r.label) }), h('span', { class: 'batch-why', text: text(r.outcome) })]))),
      ]) : null,
    ], Object.assign({ className: all ? 'success' : 'partial' }, opts));
    // The undo the Mac staged for what was proven: a batch of its own, the same gesture.
    const undo = d.undo && typeof d.undo === 'object' && d.undo.batch_id ? d.undo : null;
    if (!undo && d.batch_id) node.dataset.proposal = text(d.batch_id);
    if (undo) {
      const armedAfter = num(undo.armed_after_ms) === null ? 650 : undo.armed_after_ms;
      const kind = INTERACTIONS.indexOf(text(undo.interaction)) !== -1 ? text(undo.interaction) : 'hold_to_arm';
      const surface = buildSurface(kind, kind === 'tap_commit' ? text(undo.label, 'Undo all') : `${text(undo.label, 'Undo all')} · ${gestureLabel(kind).toLowerCase()}`, 'Undo all', 'arming', true);
      surface.classList.add('quiet');
      node.dataset.proposal = text(undo.batch_id);
      node.appendChild(surface);
      node.appendChild(h('p', { class: 'action-meta', text: num(undo.ttl_s) !== null ? `Undo available for ${Math.round(undo.ttl_s)} s` : '' }));
      wireGesture(node, surface, kind, text(undo.batch_id), armedAfter, opts, num(undo.ttl_s), (left) => (left > 0 ? `Undo available for ${left} s` : 'The undo has expired.'));
    }
    return node;
  }

  // Who is waiting on whom in one thread, in one line: "Waiting since 5h ago · last from
  // Mia · no reply from us". The Mac worked it out from the thread's own labels and stamps
  // (app/families/order_email.py); the page prints the words it was given. Warn-toned while
  // the customer is the one waiting, because that is the only state that asks for a hand.
  function renderReplyState(d, opts) {
    const waiting = text(d.latest_direction) === 'inbound' && d.replied !== true;
    const parts = [];
    if (waiting && text(d.waiting_since)) parts.push(`Waiting since ${text(d.waiting_since)}`);
    else if (text(d.latest_direction) === 'outbound') parts.push(`We replied ${text(d.replied_since, 'already')}`);
    else if (text(d.latest_direction) === 'none') parts.push('No email either way');
    if (text(d.last_from)) parts.push(`last from ${text(d.last_from)}`);
    if (text(d.latest_direction) === 'inbound') parts.push(d.replied === true ? 'answered since' : 'no reply from us');
    const line = text(d.line) || parts.join(' · ');
    const ref = text(d.thread_id);
    const order = text(d.order_number);
    return card('reply_state', [
      h('div', { class: 'card-head' }, [h('div', {}, [
        kicker('Reply state'),
        h('p', { class: `reply-line${waiting ? ' warn' : ''}`, text: line || '—' }),
        h('p', { class: 'card-meta', text: [order ? `about ${order}` : '', text(d.confidence) ? `${text(d.confidence)} link` : ''].filter(Boolean).join(' · ') }),
      ])]),
      strings(d.provenance, 4).length ? h('p', { class: 'link-why', text: strings(d.provenance, 4).join(' · ') }) : null,
      ref ? h('button', { class: 'link-chip', type: 'button', data: { ref, kind: 'email_thread' } }, [h('span', { class: 'link-chip-label', text: 'Open the thread' })]) : null,
    ], opts);
  }

  const RENDERERS = {
    assistant: renderAssistant,
    order: renderOrder,
    order_list: renderOrderList,
    customer: renderCustomer,
    customer_list: renderCustomerList,
    product: renderProduct,
    inventory: renderInventory,
    sales_summary: renderSales,
    email_list: renderEmailList,
    email_thread: renderEmailThread,
    email_draft: renderEmailDraft,
    attention: renderAttention,
    confirmation: renderConfirmation,
    success: renderSuccess,
    error: renderError,
    metric_group: renderMetricGroup,
    ranking: renderRanking,
    table: renderTable,
    comparison: renderComparison,
    variant_matrix: renderVariantMatrix,
    trend: renderTrend,
    working_set: renderWorkingSet,
    batch_action: renderBatchAction,
    capability: renderCapability,
    batch_result: renderBatchResult,
    reply_state: renderReplyState,
  };
  const TYPES = Object.keys(RENDERERS).concat(['context_stack']);
  const CONTEXT_TYPES = ['order', 'order_list', 'customer', 'customer_list', 'product', 'inventory', 'sales_summary', 'email_list', 'email_thread', 'email_draft', 'attention', 'confirmation', 'success', 'assistant',
    'metric_group', 'ranking', 'table', 'comparison', 'variant_matrix', 'trend', 'working_set', 'batch_action', 'batch_result', 'capability'];

  function isValid(item) {
    return Boolean(item) && typeof item === 'object' && typeof item.type === 'string'
      && TYPES.indexOf(item.type) !== -1 && item.data !== null && typeof item.data === 'object' && !Array.isArray(item.data);
  }

  function renderItem(item, opts) {
    if (!isValid(item) || !RENDERERS[item.type]) return null;
    try {
      return RENDERERS[item.type](item.data, opts || {}) || null;
    } catch (error) {
      return null;   // a malformed payload draws nothing; the spoken answer still stands
    }
  }

  // A supporting card, folded away behind its own title (brief section 22). The Mac decides
  // which cards are secondary — the second ranking of a turn, the second list — because it
  // is the one that knows what the answer was about; the tablet decides how that looks. The
  // card itself is untouched and complete: this is disclosure, not truncation, and the header
  // says what is inside so nothing is hidden from the reader.
  function folded(node, label) {
    const wrap = h('article', { class: 'card card-folded', data: { type: 'folded', of: node.dataset ? node.dataset.type || '' : '' } });
    const btn = h('button', { class: 'fold-head', type: 'button', 'aria-expanded': 'false' }, [
      h('span', { class: 'fold-label', text: label || 'More' }),
      h('span', { class: 'fold-mark', text: '+', 'aria-hidden': 'true' }),
    ]);
    const body = h('div', { class: 'fold-body', hidden: true }, [node]);
    btn.addEventListener('click', () => {
      const open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', open ? 'false' : 'true');
      body.hidden = open;
      btn.querySelector('.fold-mark').textContent = open ? '+' : '−';
    });
    append(wrap, [btn, body]);
    return wrap;
  }

  // What a folded card says on its header: its own title where it has one, else its kind.
  const FOLD_WORDS = {
    ranking: 'Another ranking', order_list: 'Another list of orders', email_list: 'More email',
    table: 'Another table', metric_group: 'More numbers', comparison: 'Another comparison', trend: 'Another trend',
  };
  function foldLabel(item) {
    const title = item.data && typeof item.data.title === 'string' ? text(item.data.title) : '';
    return title || FOLD_WORDS[item.type] || 'More';
  }

  function render(items, opts) {
    const out = { nodes: [], skipped: [], stack: null, errors: [], hasContext: false };
    if (!Array.isArray(items)) return out;
    for (const item of items.slice(0, 16)) {   // more than the vocabulary is long is a bug upstream
      if (!isValid(item)) { out.skipped.push(item && typeof item.type === 'string' ? item.type : 'invalid'); continue; }
      if (item.type === 'context_stack') { out.stack = list(item.data.entries, 6); continue; }
      if (item.type === 'error') out.errors.push(item.data);
      let node = renderItem(item, opts);
      if (!node) { out.skipped.push(item.type); continue; }
      if (item.data && item.data.secondary === true) node = folded(node, foldLabel(item));
      out.nodes.push(node);
      if (CONTEXT_TYPES.indexOf(item.type) !== -1) out.hasContext = true;
    }
    return out;
  }

  function renderStack(entries, opts) {
    // Chips for the context stack; the active one is pressed. Selection is the app's.
    opts = opts || {};
    return list(entries, 6).map((e) => h('button', {
      class: 'chip', type: 'button', 'aria-pressed': opts.active === e.ref ? 'true' : 'false',
      data: { kind: text(e.kind), ref: text(e.ref) },
      on: { click: () => opts.onSelect && opts.onSelect(e) },
    }, [h('span', { class: 'chip-kind', text: text(e.kind) }), h('span', { class: 'chip-label', text: text(e.label) })]));
  }

  return { render, renderItem, renderStack, hydrateOrder, settleOrder, isValid, formatDate, TYPES, CONTEXT_TYPES, h };
});
