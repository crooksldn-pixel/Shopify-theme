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

  // ------------------------------------------------------------------ formatting

  const DATE_FMT = { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' };
  const DAY_FMT = { day: 'numeric', month: 'short' };

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

  function tabs(panels) {
    // panels: [{ label, node }]. Touch-native segmented control; the first panel is open.
    const wrap = doc().createDocumentFragment ? doc().createDocumentFragment() : h('div');
    const bar = h('div', { class: 'tabs', role: 'tablist' });
    const bodies = [];
    panels.forEach((p, i) => {
      const body = h('div', { class: 'panel', role: 'tabpanel', hidden: i !== 0 }, p.node);
      const tab = h('button', {
        class: 'tab', type: 'button', role: 'tab', 'aria-selected': i === 0 ? 'true' : 'false', text: p.label,
        on: { click: () => {
          bodies.forEach((b, j) => { b.body.hidden = j !== i; b.tab.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
        } },
      });
      bodies.push({ body, tab });
      bar.appendChild(tab);
    });
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

  function orderRow(o) {
    return h('li', { class: 'row' }, [
      h('span', { class: 'row-main' }, [h('strong', { text: text(o.order_number, '—') }), ' ', text(o.customer_name)]),
      h('span', { class: 'row-sub', text: formatDate(o.placed_at) }),
      h('span', { class: 'row-side' }, [h('span', { class: 'amount', text: text(o.total) }), badge(o.fulfillment)]),
    ]);
  }

  function renderOrder(d, opts) {
    const items = list(d.items, 12);
    const fulfils = list(d.fulfillments, 6);
    const head = h('div', { class: 'card-head' }, [
      h('div', {}, [
        kicker('Order'),
        h('h2', { class: 'card-title mono', text: text(d.order_number, '—') }),
        h('p', { class: 'card-sub', text: text(d.customer_name) }),
        d.customer_email ? h('p', { class: 'card-meta', text: text(d.customer_email) }) : null,
      ]),
      h('div', { class: 'badges' }, [badge(d.fulfillment), badge(d.payment)]),
    ]);
    const overview = kv([
      ['Placed', formatDate(d.placed_at)],
      ['Total', d.total],
      ['Ships to', d.ships_to],
      ['Cancelled', d.cancelled_at ? formatDate(d.cancelled_at) : ''],
    ], true);
    if (d.note) overview.appendChild(h('dt', { text: 'Note' }));
    if (d.note) overview.appendChild(h('dd', { class: 'note-quote', text: text(d.note) }));
    if (!d.detail) {
      const brief = card('order', [head, orderTimeline(d), overview, h('p', { class: 'card-note', text: 'Ask for the order to see its items and shipping.' })], opts);
      brief.dataset.ref = text(d.order_id);
      return brief;
    }
    // The first few items in the overview itself: an order should read as an order at a
    // glance, without a second tap for what was bought.
    const preview = items.length ? h('ul', { class: 'items-preview' }, items.slice(0, 3).map((it) => h('li', {}, [
      h('span', { class: 'ip-title', text: [text(it.title), text(it.variant)].filter(Boolean).join(' · ') }),
      h('span', { class: 'ip-side', text: [num(it.quantity) !== null && it.quantity > 1 ? `× ${it.quantity}` : '', text(it.total)].filter(Boolean).join('  ') }),
    ])).concat(items.length > 3 ? [h('li', { class: 'ip-more', text: `and ${items.length - 3} more` })] : [])) : null;
    const overviewPanel = h('div', {}, [preview, overview]);
    const itemList = h('ul', { class: 'rows' }, items.map((it) => h('li', { class: 'row' }, [
      h('span', { class: 'row-main', text: text(it.title) }),
      h('span', { class: 'row-sub', text: [text(it.variant), it.sku ? `SKU ${text(it.sku)}` : ''].filter(Boolean).join(' · ') }),
      h('span', { class: 'row-side' }, [
        h('span', { class: 'amount', text: text(it.total) }),
        num(it.quantity) !== null ? h('span', { class: 'card-meta', text: `× ${it.quantity}` }) : null,
      ]),
    ])));
    if (d.items_truncated) itemList.appendChild(h('li', { class: 'row card-note', text: 'More items than shown.' }));
    const shipping = fulfils.length
      ? h('ul', { class: 'rows' }, fulfils.map((f) => h('li', { class: 'row' }, [
        h('span', { class: 'row-main', text: [text(f.carrier), text(f.number)].filter(Boolean).join(' · ') || 'Shipment' }),
        h('span', { class: 'row-sub', text: formatDate(f.shipped_at) }),
        h('span', { class: 'row-side' }, [badge(f.status)]),
      ])))
      : h('p', { class: 'card-note', text: 'Not shipped yet.' });
    const customer = kv([['Name', d.customer_name], ['Email', d.customer_email], ['Ships to', d.ships_to]], true);
    const full = card('order', [head, orderTimeline(d), tabs([
      { label: 'Overview', node: overviewPanel },
      { label: `Items${items.length ? ' · ' + items.length : ''}`, node: itemList },
      { label: 'Shipping', node: shipping },
      { label: 'Customer', node: customer },
    ])], opts);
    full.dataset.ref = text(d.order_id);
    return full;
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
      h('div', { class: 'stats' }, [
        h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: orders === null ? '—' : String(orders) }), h('div', { class: 'stat-k', text: 'Orders' })]),
        h('div', { class: 'stat' }, [h('div', { class: 'stat-v', text: text(d.spent, '—') }), h('div', { class: 'stat-k', text: 'Lifetime' })]),
      ]),
      h('p', { class: 'card-note', text: 'Ask for their orders or their emails to see more.' }),
    ], opts);
    node.dataset.ref = text(d.customer_id);
    return node;
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
    return card('email_list', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Email'), h('h2', { class: 'card-title', text: text(d.title, 'Email') }), h('p', { class: 'card-meta', text: num(d.count) === null ? '' : `${d.count} thread${d.count === 1 ? '' : 's'}` })])]),
      h('ul', { class: 'rows' }, threads.map((t) => {
        const row = h('li', { class: 'row tappable', role: 'button', tabindex: '0' }, [
          h('span', { class: 'row-main' }, [h('strong', { text: text(t.from, '—') }), ' — ', text(t.subject, '(no subject)')]),
          h('span', { class: 'row-sub', text: text(t.snippet) }),
          h('span', { class: 'row-side' }, [
            h('span', { class: 'card-meta', text: formatDate(t.date) }),
            t.known_customer ? badge('Customer', 'quiet ok') : null,
            t.likely_bulk ? badge('Bulk', 'quiet') : null,
          ]),
        ]);
        row.addEventListener('click', () => row.classList.toggle('is-open'));
        return row;
      })),
      h('p', { class: 'card-note', text: 'Say "read that one" to open a thread.' }),
    ], opts);
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
    return card('email_thread', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Email thread'), h('h2', { class: 'card-title', text: text(d.subject, '(no subject)') }), h('p', { class: 'card-meta', text: [num(d.message_count) === null ? '' : `${d.message_count} message${d.message_count === 1 ? '' : 's'}`, d.truncated ? 'older messages not shown' : ''].filter(Boolean).join(' · ') })])]),
      h('div', {}, nodes),
    ], opts);
  }

  function renderEmailDraft(d, opts) {
    // Architecture only: Gmail is read-only. There is no send here and there must not be one.
    return card('email_draft', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Draft · not sent'), h('h2', { class: 'card-title', text: text(d.subject, '(no subject)') }), h('p', { class: 'card-sub', text: d.to ? `To ${text(d.to)}` : '' })]), h('div', { class: 'badges' }, [badge('Draft', 'warn')])]),
      h('p', { class: 'msg-body', text: text(d.body) }),
      h('p', { class: 'future', text: 'Editing and sending are not connected. Nothing has been sent.' }),
    ], opts);
  }

  function renderAttention(d, opts) {
    const items = list(d.items, 8);
    return card('attention', [
      h('div', { class: 'card-head' }, [h('div', {}, [kicker('Attention'), h('h2', { class: 'card-title', text: `${items.length} require${items.length === 1 ? 's' : ''} attention` })])]),
      h('ul', { class: 'rows' }, items.map((a) => h('li', { class: 'row' }, [
        h('span', { class: 'row-main', text: text(a.title, '—') }),
        h('span', { class: 'row-sub', text: text(a.detail) }),
        h('span', { class: 'row-side' }, [badge(text(a.kind), a.level === 'red' ? 'bad' : a.level === 'green' ? 'ok' : 'warn')]),
      ]))),
    ], opts);
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

  const INTERACTIONS = ['tap_commit'];   // implemented here; the grammar lists more

  function renderConfirmation(d, opts) {
    opts = opts || {};
    const risk = text(d.risk, text(d.tier, 'amber')) === 'red' ? 'red' : 'amber';
    const interaction = d.interaction && typeof d.interaction === 'object' ? d.interaction : {};
    const kind = text(interaction.kind, 'tap_commit');
    const supported = INTERACTIONS.indexOf(kind) !== -1;
    const armedAfter = num(interaction.armed_after_ms) === null ? 650 : Math.max(0, interaction.armed_after_ms);
    const status = text(d.status, 'pending');
    // The Mac already knows whether a tap from this tablet could apply it. When it cannot,
    // the surface says so and never arms: an honest card beats a button that fails.
    const blocked = d.commit && typeof d.commit === 'object' && d.commit.allowed === false ? d.commit : null;
    const live = supported && status === 'pending' && Boolean(d.proposal_id) && !blocked;
    const surface = h('div', {
      class: 'action-surface', role: 'button', tabindex: live ? '0' : '-1', 'aria-disabled': 'true',
      data: { state: live ? 'arming' : (blocked ? 'unavailable' : (supported ? status : 'unsupported')), kind },
    }, [
      h('span', { class: 'action-label', text: live ? text(interaction.label, 'Tap to apply') : (blocked ? blockedLabel(blocked.code) : (supported ? settledLabel(status) : 'Needs a newer tablet build')) }),
      h('span', { class: 'action-arm', 'aria-hidden': 'true' }),
    ]);
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
      d.detail && d.entity ? h('p', { class: 'card-meta', text: text(d.detail) }) : null,
      surface,
      // The reason a tap would be refused is the one line the owner must read: body size,
      // not the 11 px caption.
      blocked ? h('p', { class: 'card-sub action-why', text: text(blocked.reason) }) : null,
      h('p', { class: 'action-meta', text: live ? (num(d.ttl_s) !== null ? `Waits ${Math.round(d.ttl_s)} s · nothing happens until you tap` : 'Nothing happens until you tap') : '' }),
    ], Object.assign({ className: `tier-${risk}` }, opts));
    node.dataset.proposal = text(d.proposal_id);
    node.dataset.ref = text(d.entity_ref);
    if (live) wireTapCommit(node, surface, text(d.proposal_id), armedAfter, opts, num(d.ttl_s));
    return node;
  }

  // Who is stopping the tap, in five words: the Mac's switch, its allow-list, this tablet's
  // login, or Shopify's grant. "This tablet" is blamed only when it is the reason.
  function blockedLabel(code) {
    return {
      writes_disabled: 'Changes are switched off on the Mac', allow_list_missing: 'No allowed logins set on the Mac',
      not_authorised: "This tablet's login is not on the Mac's list", not_authorised_local: 'The Mac itself may not apply changes',
      scope_missing: 'Shopify has not granted write_orders',
    }[text(code)] || "Can't apply from here";
  }

  function settledLabel(status) {
    return { verified: 'Applied', stale: 'Not applied', expired: 'Expired', revoked: 'Withdrawn', failed: 'Not applied', unverified: 'Not confirmed', executing: 'Applying…', executed: 'Applying…' }[status] || 'Not available';
  }

  function wireTapCommit(node, surface, proposalId, armedAfter, opts, ttlS) {
    const now = opts.now || (() => Date.now());
    const shown = now();
    let downAt = null;
    let committed = false;
    const armed = () => now() - shown >= armedAfter;
    const blocked = () => (typeof opts.blocked === 'function' ? Boolean(opts.blocked()) : false);
    // Bound wrappers: a host timer called through a plain object is an illegal invocation in Chromium.
    const timers = opts.timers || { set: (fn, ms) => setTimeout(fn, ms), clear: (id) => clearTimeout(id) };
    // The visible fill lasts exactly as long as the arming does: one number, ours, not a string from the data.
    if (surface.style && surface.style.setProperty) surface.style.setProperty('--arm-ms', `${Math.round(armedAfter)}ms`);
    const armTimer = timers.set(() => {
      if (!committed && surface.dataset.state === 'arming') {
        surface.dataset.state = 'armed';
        surface.setAttribute('aria-disabled', 'false');
      }
    }, armedAfter);
    // The Mac's clock decides expiry; this only stops the surface from inviting a tap that
    // would be answered "Expired". A little early rather than a little late.
    const expiryTimer = ttlS !== null && ttlS !== undefined ? timers.set(() => {
      if (!committed && (surface.dataset.state === 'arming' || surface.dataset.state === 'armed')) node.settle('expired', 'Expired');
    }, Math.max(0, ttlS * 1000 - 1000)) : null;
    // "Waits 60 s" counts down, so the line is true for as long as it is shown.
    const meta = node.querySelector ? node.querySelector('.action-meta') : null;
    let countdown = null;
    if (meta && ttlS !== null && ttlS !== undefined) {
      const tick = () => {
        const left = Math.max(0, Math.round(ttlS - (now() - shown) / 1000));
        if (committed) return;
        meta.textContent = `Waits ${left} s · nothing happens until you tap`;
        if (left > 0) countdown = timers.set(tick, 1000);
      };
      countdown = timers.set(tick, 1000);
    }
    node.settle = (state, label) => {
      // Called by the app when the Mac has answered, or the proposal has gone stale.
      timers.clear(armTimer);
      if (expiryTimer !== null) timers.clear(expiryTimer);
      if (countdown !== null) { timers.clear(countdown); countdown = null; }
      if (meta && state !== 'armed') meta.textContent = '';
      committed = state !== 'armed';
      surface.dataset.state = state;
      surface.setAttribute('aria-disabled', state === 'armed' ? 'false' : 'true');
      if (label !== undefined) surface.childNodes[0].textContent = String(label);
    };
    surface.addEventListener('pointerdown', () => {
      // Only a press that STARTS after arming can commit; a press carried over from the orb
      // (or from before the card existed) has downAt null and ends in nothing.
      downAt = armed() && !blocked() && !committed && surface.dataset.state === 'armed' ? now() : null;
      if (downAt !== null) surface.dataset.pressed = 'true';
    });
    surface.addEventListener('pointercancel', () => { downAt = null; surface.dataset.pressed = 'false'; });
    surface.addEventListener('pointerleave', () => { downAt = null; surface.dataset.pressed = 'false'; });
    surface.addEventListener('pointerup', () => {
      const ok = downAt !== null && armed() && !blocked() && !committed && surface.dataset.state === 'armed';
      downAt = null;
      surface.dataset.pressed = 'false';
      if (!ok) return;
      committed = true;
      surface.dataset.state = 'committing';
      surface.setAttribute('aria-disabled', 'true');
      surface.childNodes[0].textContent = 'Applying…';
      if (typeof opts.onCommit === 'function') opts.onCommit(proposalId, node);
    });
    surface.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && armed() && !blocked() && !committed && surface.dataset.state === 'armed') {
        if (e.preventDefault) e.preventDefault();
        committed = true;
        surface.dataset.state = 'committing';
        surface.setAttribute('aria-disabled', 'true');
        surface.childNodes[0].textContent = 'Applying…';
        if (typeof opts.onCommit === 'function') opts.onCommit(proposalId, node);
      }
    });
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
    ], Object.assign({ className: 'success' }, opts));
    if (d.proposal_id) node.dataset.proposal = text(d.proposal_id);
    // A reversible action offers its undo: a second proposal the Mac staged, authorised the
    // same way (its own dead time, its own tap) and executed by the same path.
    const undo = d.undo && typeof d.undo === 'object' && d.undo.proposal_id ? d.undo : null;
    if (undo) {
      const armedAfter = num(undo.armed_after_ms) === null ? 650 : undo.armed_after_ms;
      const surface = h('div', {
        class: 'action-surface quiet', role: 'button', tabindex: '0', 'aria-disabled': 'true',
        data: { state: 'arming', kind: 'tap_commit' },
      }, [h('span', { class: 'action-label', text: text(undo.label, 'Undo') }), h('span', { class: 'action-arm', 'aria-hidden': 'true' })]);
      node.appendChild(surface);
      node.appendChild(h('p', { class: 'action-meta', text: num(undo.ttl_s) !== null ? `Undo available for ${Math.round(undo.ttl_s)} s` : '' }));
      wireTapCommit(node, surface, text(undo.proposal_id), armedAfter, opts);
    }
    return node;
  }

  function renderError(d, opts) {
    return card('error', [
      h('div', { class: 'card-head' }, [h('div', { class: 'mark bad' }, h('span', { text: '×' })), h('div', {}, [kicker(text(d.service, 'assistant')), h('h2', { class: 'card-title', text: text(d.title, 'Something went wrong') }), h('p', { class: 'card-sub', text: text(d.recovery) })])]),
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
  };
  const TYPES = Object.keys(RENDERERS).concat(['context_stack']);
  const CONTEXT_TYPES = ['order', 'order_list', 'customer', 'customer_list', 'product', 'inventory', 'sales_summary', 'email_list', 'email_thread', 'email_draft', 'attention', 'confirmation', 'success', 'assistant'];

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

  function render(items, opts) {
    const out = { nodes: [], skipped: [], stack: null, errors: [], hasContext: false };
    if (!Array.isArray(items)) return out;
    for (const item of items.slice(0, 16)) {   // more than the vocabulary is long is a bug upstream
      if (!isValid(item)) { out.skipped.push(item && typeof item.type === 'string' ? item.type : 'invalid'); continue; }
      if (item.type === 'context_stack') { out.stack = list(item.data.entries, 6); continue; }
      if (item.type === 'error') out.errors.push(item.data);
      const node = renderItem(item, opts);
      if (!node) { out.skipped.push(item.type); continue; }
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

  return { render, renderItem, renderStack, isValid, formatDate, TYPES, CONTEXT_TYPES, h };
});
