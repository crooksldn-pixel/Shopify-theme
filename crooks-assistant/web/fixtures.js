/* Development fixtures — sample `ui` payloads for looking at every component on the tablet.
 *
 * Loaded only when the page was opened with ?dev=1 (app.js injects this script; index.html
 * does not reference it). Every name, address and figure here is invented; every card built
 * from them is marked "Fixture · not live" by the renderer. Production renders only what the
 * backend returns from /turn.
 */
(function (root) {
  'use strict';

  const IMAGE = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNjAiIGhlaWdodD0iMTYwIiB2aWV3Qm94PSIwIDAgMTYwIDE2MCI+PHJlY3Qgd2lkdGg9IjE2MCIgaGVpZ2h0PSIxNjAiIGZpbGw9IiMxYTFjMjIiLz48cGF0aCBkPSJNNTIgMjhoNTZsMTAgMTA0SDQyeiIgZmlsbD0iIzJjMzI0MiIvPjxwYXRoIGQ9Ik02MiAyOGgzNmwtNCAxMDRINjZ6IiBmaWxsPSIjM2E0MjU4Ii8+PC9zdmc+';
  const HISTORY = {
    orders: 4, spent: '£410.00', since: '2025-01-02T00:00:00Z', standing: 'regular', first_order_at: '2025-01-02T10:00:00Z',
    other_unfulfilled: ['#1901'],
    recent: [
      { order_id: 'gid://shopify/Order/0', order_number: '#1930', placed_at: '2026-09-08T09:42:00Z', fulfillment: 'unfulfilled', payment: 'paid', total: '£145.00', items_brief: 'Blue Wash Yard Jeans, Convict Sweats', current: true },
      { order_id: 'gid://shopify/Order/1', order_number: '#1901', placed_at: '2026-08-20T10:00:00Z', fulfillment: 'unfulfilled', payment: 'paid', total: '£200.00', items_brief: 'Convict Hoodie ×2' },
      { order_id: 'gid://shopify/Order/2', order_number: '#1844', placed_at: '2026-05-02T10:00:00Z', fulfillment: 'fulfilled', payment: 'paid', total: '£65.00', items_brief: 'Cap' },
    ],
  };
  const EMAIL = { available: true, threads: [
    { thread_id: 't1', from: 'Sam Fixture', from_email: 'sam@example.com', subject: 'Address for order 1930', date: 'Tue, 8 Sep 2026 10:12:00 +0100', snippet: 'Could you send it to my work instead? 4 Example Row, London EC1A 1AA.', sender_match: true, verified_sender: true, match: 'both', provenance: 'CUSTOMER_EMAIL' },
    { thread_id: 't2', from: 'Kit Placeholder', from_email: 'kit@example.com', subject: 'Re: #1930', date: 'Mon, 7 Sep 2026 15:00:00 +0100', snippet: 'Is 1930 the one I ordered for my brother?', verified_sender: false, match: 'order_number', provenance: 'UNKNOWN' },
  ] };
  const ORDER = {
    order_id: 'gid://shopify/Order/0', order_number: '#1930', placed_at: '2026-09-08T09:42:00Z',
    fulfillment: 'unfulfilled', payment: 'paid', total: '£145.00', customer_name: 'Sam Fixture',
    customer_id: 'gid://shopify/Customer/0', customer_email: 'sam@example.com', detail: true, tags: ['vip'],
    items: [
      { title: 'Blue Wash Yard Jeans', variant: 'M', sku: 'YJ-BLU-M', quantity: 1, total: '£95.00', image: IMAGE, stock: { tracked: true, available: 3 } },
      { title: 'Convict Sweats', variant: 'L / Black', sku: 'CS-BLK-L', quantity: 1, total: '£50.00', image: IMAGE, stock: { tracked: true, available: 0 } },
    ],
    items_truncated: false,
    fulfillments: [],
    money: { subtotal: '£140.00', shipping: '£5.00', tax: '£23.33', discounts: '£0.00', refunded: '£0.00', outstanding: '£0.00' },
    shipping_method: 'Royal Mail Tracked 24',
    shipping_address: { name: 'Sam Fixture', lines: ['12 Somewhere Street', 'Flat 3'], city: 'London', zip: 'E1 6AN', country: 'United Kingdom', country_code: 'GB' },
    history: HISTORY, email: EMAIL, pending: [],
    actions: [
      { id: 'note', label: 'Note', operation: 'order_note_append', risk: 'amber', enabled: true, reason: '', instruction: 'Add a note to order 1930', mode: 'ask' },
      { id: 'cancel', label: 'Cancel', operation: 'order_cancel', risk: 'red', enabled: true, reason: '', instruction: 'Cancel order 1930', mode: 'ask' },
      { id: 'address', label: 'Address', operation: 'order_shipping_address_set', risk: 'red', enabled: true, reason: '', instruction: 'Change the address on order 1930', mode: 'ask' },
      { id: 'refund', label: 'Refund', operation: 'refund_create', risk: 'red', enabled: false, reason: 'not paid', instruction: 'Refund order 1930', mode: 'ask' },
    ],
    cancelled_at: '', note: 'Leave with the neighbour if out.', ships_to: 'London, United Kingdom',
  };
  const ORDER_READING = Object.assign({}, ORDER, { history: null, email: null, pending: ['history', 'email'] });

  const list = [
    { id: 'order', label: 'Order', items: [{ type: 'order', data: ORDER }] },
    { id: 'order_reading', label: 'Order · still reading', items: [{ type: 'order', data: ORDER_READING }] },
    { id: 'order_list', label: 'Orders today', items: [{ type: 'order_list', data: {
      title: 'Today', count: 3, truncated: false, orders: [
        { order_number: '#1931', placed_at: '2026-09-08T11:10:00Z', fulfillment: 'fulfilled', payment: 'paid', total: '£60.00', customer_name: 'Ada Sample' },
        { order_number: '#1930', placed_at: '2026-09-08T09:42:00Z', fulfillment: 'unfulfilled', payment: 'paid', total: '£145.00', customer_name: 'Sam Fixture' },
        { order_number: '#1929', placed_at: '2026-09-08T08:05:00Z', fulfillment: 'unfulfilled', payment: 'pending', total: '£95.00', customer_name: 'Kit Placeholder' },
      ] } }] },
    { id: 'customer', label: 'Customer', items: [{ type: 'customer', data: { customer_id: 'c0', name: 'Sam Fixture', email: 'sam@example.com', orders: 4, spent: '£410.00', history: HISTORY, related_email: EMAIL } }] },
    { id: 'customer_list', label: 'Which customer', items: [{ type: 'customer_list', data: { title: 'Which customer?', ambiguous: true, customers: [
      { customer_id: 'c1', name: 'Dan Sample', email: 'dan.s@example.com', orders: 2, spent: '£120.00' },
      { customer_id: 'c2', name: 'Dan Fixture', email: 'dan.f@example.com', orders: 7, spent: '£880.00' },
    ] } }] },
    { id: 'product', label: 'Product', items: [{ type: 'product', data: { query: 'Yard Jeans', products: [{
      product_id: 'p0', title: 'Blue Wash Yard Jeans', status: 'active', subtitle: 'Relaxed straight, 14oz selvedge',
      description: 'A relaxed straight jean cut from 14oz Japanese selvedge denim, washed once for softness. Sits at the waist with a straight leg and a slightly wider hem. Made in Portugal.',
      fabric: '14oz selvedge denim', cut: 'Relaxed straight', origin: 'Portugal', care: 'Wash cold, inside out, hang dry',
      measurements: [{ size: 'S', waist: '80', inseam: '78' }, { size: 'M', waist: '84', inseam: '79' }, { size: 'L', waist: '88', inseam: '80' }],
      measurements_note: 'Garment measurements in centimetres.',
    }] } }] },
    { id: 'inventory', label: 'Inventory', items: [{ type: 'inventory', data: { query: 'Yard Jeans', low_stock_at: 5,
      exceptions: [
        { product: 'Blue Wash Yard Jeans', variant: 'M', available: 3, oversold_by: 0, tracked: true, level: 'low' },
        { product: 'Blue Wash Yard Jeans', variant: 'S', available: 0, oversold_by: 0, tracked: true, level: 'out' },
        { product: 'Convict Sweats', variant: 'L', available: 2, oversold_by: 0, tracked: true, level: 'low' },
      ],
      products: [{ product_id: 'p0', title: 'Blue Wash Yard Jeans', status: 'active', total_inventory: 31, variants: [
        { variant: 'S', sku: 'YJ-S', available: 0, oversold_by: 0, tracked: true, level: 'out' },
        { variant: 'M', sku: 'YJ-M', available: 3, oversold_by: 0, tracked: true, level: 'low' },
        { variant: 'L', sku: 'YJ-L', available: 14, oversold_by: 0, tracked: true, level: 'ok' },
        { variant: 'XL', sku: 'YJ-XL', available: 14, oversold_by: 0, tracked: true, level: 'ok' },
      ] }] } }] },
    { id: 'sales', label: 'Sales', items: [{ type: 'sales_summary', data: { title: 'Today', since: '2026-09-08T00:00:00+01:00', until: '2026-09-09T00:00:00+01:00', orders: 12, revenue: '£1,430.00', aov: '£119.17', currency: 'GBP', by_day: [{ date: '2026-09-02', orders: 4, revenue: '£310.00' }, { date: '2026-09-03', orders: 2, revenue: '£120.00' }, { date: '2026-09-04', orders: 6, revenue: '£540.00' }, { date: '2026-09-05', orders: 3, revenue: '£210.00' }, { date: '2026-09-06', orders: 5, revenue: '£445.00' }, { date: '2026-09-07', orders: 1, revenue: '£60.00' }, { date: '2026-09-08', orders: 12, revenue: '£1,430.00' }], complete: true, basis: 'Orders created in the period, current totals.' } }] },
    { id: 'email_list', label: 'Email list', items: [{ type: 'email_list', data: { title: 'Email', count: 2, threads: [
      { thread_id: 't1', from: 'Sam Fixture', from_email: 'sam@example.com', subject: 'Re: Order #1930', date: 'Tue, 8 Sep 2026 10:12:00 +0100', snippet: 'Hi, just checking whether the jeans have shipped yet, I ordered them on Sunday and have not had a tracking email.', likely_bulk: false, known_customer: true },
      { thread_id: 't2', from: 'Carrier Updates', from_email: 'no-reply@example.com', subject: 'Your weekly shipping digest', date: 'Mon, 7 Sep 2026 07:00:00 +0100', snippet: 'This week in shipping…', likely_bulk: true, known_customer: false },
    ] } }] },
    { id: 'email_thread', label: 'Email thread', items: [{ type: 'email_thread', data: { thread_id: 't1', subject: 'Re: Order #1930', message_count: 2, truncated: false, messages: [
      { from: 'Sam Fixture', from_email: 'sam@example.com', date: 'Sun, 6 Sep 2026 18:30:00 +0100', subject: 'Order #1930', body: 'Hi,\n\nCould you let me know when order 1930 will ship? I need it for the weekend.\n\nThanks,\nSam' },
      { from: 'Sam Fixture', from_email: 'sam@example.com', date: 'Tue, 8 Sep 2026 10:12:00 +0100', subject: 'Re: Order #1930', body: 'Hi, just checking whether the jeans have shipped yet — I ordered them on Sunday and have not had a tracking email.\n\nSam' },
    ] } }] },
    { id: 'email_send', label: 'Email · hold to arm', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_email', status: 'pending', risk: 'red', operation: 'gmail_send_reply', title: 'Send the reply', entity: 'Email to Sam', entity_kind: 'email', entity_ref: 't1', summary: '', detail: 'Sends now. It cannot be unsent.',
      body: 'Hi Sam,\n\nThanks for your patience — order 1930 is being packed today and will ship with Royal Mail Tracked 24. You will get the tracking number by email as soon as it is scanned.\n\nCROOKS',
      facts: [{ label: 'To', value: 'Sam Fixture <sam@example.com>' }, { label: 'Subject', value: 'Re: Order #1930' }, { label: 'Replying to', value: 'sam@example.com, 8 Sep 10:12 · verified sender' }, { label: 'Order', value: '#1930 · the customer on the order' }, { label: 'From', value: 'team@example.com' }],
      interaction: { kind: 'hold_to_arm', label: 'Hold to arm, then tap', footer: 'nothing happens until you hold the card, then tap it', armed_after_ms: 650 }, ttl_s: 60, reversible: false, commit: { allowed: true } } }] },
    { id: 'email_draft', label: 'Email draft', items: [{ type: 'email_draft', data: { state: 'draft', to: 'sam@example.com', subject: 'Re: Order #1930', body: 'Hi Sam,\n\nThanks for your patience — order 1930 is being packed today and will ship with Royal Mail Tracked 24. You will get the tracking number by email as soon as it is scanned.\n\nCROOKS' } }] },
    { id: 'attention', label: 'Attention', items: [{ type: 'attention', data: { items: [
      { kind: 'orders', title: '2 orders unfulfilled since yesterday', detail: '#1929, #1930', level: 'amber' },
      { kind: 'stock', title: 'Blue Wash Yard Jeans S out of stock', detail: 'Sold out this morning', level: 'red' },
    ] } }] },
    { id: 'cancel', label: 'Cancel · hold and drag', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_cancel', status: 'pending', risk: 'red', operation: 'order_cancel', title: 'Cancel order', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0', summary: '', detail: 'Cancelling cannot be undone.',
      facts: [{ label: 'Customer', value: 'Sam Fixture' }, { label: 'Items', value: '2 · £145.00, paid' }, { label: 'Refund', value: '£145.00 to the original card', tone: 'bad' }, { label: 'Restock', value: '2 items' }, { label: 'Customer emailed', value: 'yes' }, { label: 'Reason', value: 'customer request' }],
      interaction: { kind: 'hold_drag_target', label: 'Hold, then drag to the target', footer: 'nothing happens until you hold the card and drag the handle onto the target', target: 'Drop to cancel and refund £145.00', armed_after_ms: 650, hold_ms: 900, armed_for_s: 5, swipe_fraction: 0.72 }, ttl_s: 60, reversible: false, commit: { allowed: true } } }] },
    { id: 'refund', label: 'Refund · hold and drag', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_refund', status: 'pending', risk: 'red', operation: 'refund_create', title: 'Refund', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0', summary: '', detail: 'A refund cannot be undone.',
      facts: [{ label: 'Amount', value: '£20.00 to the original card', tone: 'bad' }, { label: 'Of', value: '£145.00 paid · £125.00 remains refundable' }, { label: 'Items', value: 'none · goodwill' }, { label: 'Customer emailed', value: 'yes' }],
      interaction: { kind: 'hold_drag_target', label: 'Hold, then drag to the target', footer: 'nothing happens until you hold the card and drag the handle onto the target', target: 'Drop to refund £20.00', armed_after_ms: 650 }, ttl_s: 60, reversible: false, commit: { allowed: true } } }] },
    { id: 'address', label: 'Address · hold to arm', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_address', status: 'pending', risk: 'red', operation: 'order_shipping_address_set', title: 'Change the address', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0', summary: '', detail: 'Not shipped yet. If a label is already printed, reprint it.',
      facts: [{ label: 'From', value: '12 Somewhere Street, Flat 3, London E1 6AN' }, { label: 'To', value: '4 Example Row, London EC1A 1AA', tone: 'warn' }, { label: 'Changes', value: 'street, postcode' }, { label: 'Cited', value: 'Email from sam@example.com, 8 Sep 10:12 · verified · postcode found in the message' }],
      interaction: { kind: 'hold_to_arm', label: 'Hold to arm, then tap', footer: 'nothing happens until you hold the card, then tap it', armed_after_ms: 650 }, ttl_s: 60, reversible: false, commit: { allowed: true } } }] },
    { id: 'fulfil', label: 'Fulfil · hold to arm', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_fulfil', status: 'pending', risk: 'red', operation: 'fulfillment_create', title: 'Mark as shipped', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0', summary: '', detail: 'Marks every item shipped.',
      facts: [{ label: 'Items', value: 'Blue Wash Yard Jeans M, Convict Sweats L' }, { label: 'Carrier', value: 'Royal Mail' }, { label: 'Tracking', value: 'AB123456785GB' }, { label: 'Customer emailed', value: 'no' }],
      interaction: { kind: 'hold_to_arm', label: 'Hold to arm, then tap', footer: 'nothing happens until you hold the card, then tap it', armed_after_ms: 650 }, ttl_s: 60, reversible: false, commit: { allowed: true } } }] },
    { id: 'stock', label: 'Stock · hold to arm', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_stock', status: 'pending', risk: 'red', operation: 'inventory_set', title: 'Adjust stock', entity: 'Variant Blue Wash Yard Jeans M', entity_kind: 'variant', entity_ref: 'gid://shopify/ProductVariant/0', summary: '', detail: 'Changes what the shop can sell now. The undo puts it back.',
      facts: [{ label: 'Item', value: 'Blue Wash Yard Jeans M' }, { label: 'Location', value: 'CROOKS HQ' }, { label: 'Available', value: '4 → 6', tone: 'warn' }, { label: 'Reason', value: 'a delivery' }],
      interaction: { kind: 'hold_to_arm', label: 'Hold to arm, then tap', footer: 'nothing happens until you hold the card, then tap it', armed_after_ms: 650 }, ttl_s: 60, reversible: true, commit: { allowed: true } } }] },
    { id: 'swipe', label: 'Swipe · irreversible amber', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture_swipe', status: 'pending', risk: 'amber', operation: 'example_swipe', title: 'Swipe example', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0', summary: 'An AMBER change with no undo.', detail: '',
      interaction: { kind: 'swipe_commit', label: 'Swipe to apply', footer: 'nothing happens until you swipe', armed_after_ms: 650 }, ttl_s: 60, reversible: false, commit: { allowed: true } } }] },
    { id: 'confirmation', label: 'Confirmation', items: [{ type: 'confirmation', data: { proposal_id: 'prop_fixture0000', status: 'pending', risk: 'amber', operation: 'order_note_append', title: 'Add order note', entity: 'Order #1930', entity_kind: 'order', entity_ref: 'gid://shopify/Order/0', summary: 'Customer requested a sizing exchange.', detail: 'The order has no note yet.', interaction: { kind: 'tap_commit', label: 'Tap to apply', armed_after_ms: 650 }, ttl_s: 60, reversible: true } }] },
    { id: 'success', label: 'Success', items: [{ type: 'success', data: { title: 'Order #1930 fulfilled', detail: 'Tracking sent to Sam Fixture.' } }] },
    { id: 'error', label: 'Error', items: [{ type: 'error', data: { service: 'shopify', kind: 'tool_failed', title: 'Shopify unavailable', recovery: 'Ask again in a moment.' } }] },
    { id: 'stack', label: 'Context stack', items: [
      { type: 'order', data: ORDER },
      { type: 'context_stack', data: { entries: [
        { kind: 'order', label: '#1930', ref: 'gid://shopify/Order/0' },
        { kind: 'customer', label: 'Sam Fixture', ref: 'gid://shopify/Customer/0' },
        { kind: 'email', label: 'Re: Order #1930', ref: 't1' },
        { kind: 'product', label: 'Blue Wash Yard Jeans', ref: 'p0' },
      ] } },
    ] },
    { id: 'ranking', label: 'Best sellers', items: [{ type: 'ranking', data: { title: 'Best sellers', subtitle: 'last 30 days', mode: '', rows: [
      { rank: 1, label: 'Convict Joggers', ref: 'gid://shopify/Product/1', kind: 'product', primary: { key: 'units', label: 'units', value: '41' }, secondary: { key: 'revenue', label: 'revenue', value: '£1,845.00' }, pct: 54, lines: [], known: true },
      { rank: 2, label: 'Yard Jeans', ref: 'gid://shopify/Product/2', kind: 'product', primary: { key: 'units', label: 'units', value: '22' }, secondary: { key: 'revenue', label: 'revenue', value: '£1,980.00' }, pct: 29, lines: [], known: true },
      { rank: 3, label: 'Convict Hoodie', ref: 'gid://shopify/Product/3', kind: 'product', primary: { key: 'units', label: 'units', value: '13' }, secondary: { key: 'revenue', label: 'revenue', value: '£910.00' }, pct: 17, lines: [], known: true },
    ], totals: [{ key: 'units', label: 'units', value: '76' }, { key: 'revenue', label: 'revenue', value: '£4,735.00' }], measured: ['units', 'revenue'], derived: ['share'], note: '', complete: true, truncated: false } }] },
    { id: 'restock', label: 'Restock priority', items: [{ type: 'ranking', data: { title: 'Restock priority', subtitle: 'last 7 days', mode: 'restock', rows: [
      { rank: 1, label: 'Convict Joggers · Black / L', ref: 'gid://shopify/ProductVariant/1', kind: 'variant', primary: { key: 'days_cover', label: 'days cover', value: '1.6' }, secondary: { key: 'stock', label: 'in stock', value: '3' }, pct: null, lines: [{ key: 'stock', label: 'in stock', value: '3', derived: false }, { key: 'units', label: 'sold in period', value: '13', derived: false }, { key: 'velocity', label: 'a day', value: '1.86', derived: true }, { key: 'days_cover', label: 'days cover', value: '1.6', derived: true }], known: true },
      { rank: 2, label: 'Yard Jeans · Blue / M', ref: 'gid://shopify/ProductVariant/2', kind: 'variant', primary: { key: 'days_cover', label: 'days cover', value: '5.8' }, secondary: { key: 'stock', label: 'in stock', value: '7' }, pct: null, lines: [{ key: 'stock', label: 'in stock', value: '7', derived: false }, { key: 'units', label: 'sold in period', value: '8', derived: false }, { key: 'velocity', label: 'a day', value: '1.20', derived: true }, { key: 'days_cover', label: 'days cover', value: '5.8', derived: true }], known: true },
      { rank: 3, label: 'Convict Hoodie · Grey / M', ref: 'gid://shopify/ProductVariant/3', kind: 'variant', primary: { key: 'days_cover', label: 'days cover', value: '—' }, secondary: null, pct: null, lines: [{ key: 'units', label: 'sold in period', value: '2', derived: false }], known: false },
    ], totals: [], measured: ['units', 'stock'], derived: ['velocity', 'days_cover'], note: 'Velocity is units sold over the last 7 days divided by the days; cover is stock divided by that — an estimate from recent sales, not a forecast.', complete: true, truncated: false } }] },
    { id: 'comparison', label: 'This week against last', items: [{ type: 'comparison', data: { title: 'This week against last', subtitle: 'this week', current: { label: 'this week', metrics: [{ key: 'revenue', label: 'revenue', value: '£4,812.00' }, { key: 'orders', label: 'orders', value: '83' }, { key: 'aov', label: 'avg order', value: '£57.98' }] }, previous: { label: 'last week', metrics: [{ key: 'revenue', label: 'revenue', value: '£4,109.00' }, { key: 'orders', label: 'orders', value: '72' }, { key: 'aov', label: 'avg order', value: '£57.07' }] }, changes: [{ key: 'revenue', label: 'revenue', delta: '+£703.00', pct: '+17.1%', direction: 'up' }, { key: 'orders', label: 'orders', delta: '+11', pct: '+15.3%', direction: 'up' }, { key: 'aov', label: 'avg order', delta: '+£0.91', pct: '+1.6%', direction: 'up' }], note: '', complete: true } }] },
    { id: 'matrix', label: 'Sizes matrix', items: [{ type: 'variant_matrix', data: { title: 'Convict Joggers by colour and size', subtitle: 'this month · product joggers', row_label: 'Colour', col_label: 'Size', rows: ['Black', 'Pink', 'Grey'], cols: ['S', 'M', 'L', 'XL'], cells: [{ row: 'Black', col: 'S', value: 2, display: '2' }, { row: 'Black', col: 'M', value: 9, display: '9' }, { row: 'Black', col: 'L', value: 13, display: '13' }, { row: 'Black', col: 'XL', value: 4, display: '4' }, { row: 'Pink', col: 'M', value: 5, display: '5' }, { row: 'Pink', col: 'S', value: 3, display: '3' }, { row: 'Grey', col: 'L', value: 1, display: '1' }], metric: 'units', note: '' } }] },
    { id: 'trend', label: 'Sales trend', items: [{ type: 'trend', data: { title: 'Revenue by day', subtitle: 'last 7 days', metric: 'revenue', points: [{ label: '2026-09-03', value: 210, display: '£210.00' }, { label: '2026-09-04', value: 480, display: '£480.00' }, { label: '2026-09-05', value: 95, display: '£95.00' }, { label: '2026-09-06', value: 640, display: '£640.00' }, { label: '2026-09-07', value: 120.5, display: '£120.50' }, { label: '2026-09-08', value: 300, display: '£300.00' }, { label: '2026-09-09', value: 180, display: '£180.00' }], total: '£2,025.50', note: '' } }] },
    { id: 'metrics', label: 'Figures', items: [{ type: 'metric_group', data: { title: 'Unfulfilled orders', subtitle: 'last 90 days · fulfillment unfulfilled', metrics: [{ key: 'orders', label: 'orders', value: '23', measured: true }, { key: 'unfulfilled_value', label: 'unfulfilled value', value: '£1,481.00', measured: true }, { key: 'aov', label: 'avg order', value: '£64.39', measured: false }], note: '', complete: true } }] },
    { id: 'analytic-table', label: 'Table', items: [{ type: 'table', data: { title: 'Customers over £250', subtitle: 'last 90 days', columns: [{ key: 'customer', label: 'Customer', numeric: false }, { key: 'lifetime_orders', label: 'orders, all time', numeric: true }, { key: 'lifetime_spent', label: 'spent, all time', numeric: true }], rows: [{ ref: 'gid://shopify/Customer/3', cells: ['Cy Cole', '5', '£900.00'] }, { ref: 'gid://shopify/Customer/1', cells: ['Ann Able', '3', '£410.00'] }], note: '', truncated: false, complete: true } }] },
    { id: 'working-set', label: 'Working set', items: [
      { type: 'order_list', data: { title: 'Delayed orders', query: 'last 90 days · fulfillment unfulfilled', count: 23, truncated: true, value: '£1,481.00', orders: [
        { order_id: 'gid://shopify/Order/0', order_number: '#1938', placed_at: '2026-09-01T09:42:00Z', fulfillment: 'unfulfilled', payment: 'paid', total: '£60.00', customer_name: 'Sam Fixture', customer_id: 'gid://shopify/Customer/0' },
        { order_id: 'gid://shopify/Order/0', order_number: '#1927', placed_at: '2026-08-30T15:12:00Z', fulfillment: 'unfulfilled', payment: 'paid', total: '£95.00', customer_name: 'Jo Fixture', customer_id: 'gid://shopify/Customer/0' },
      ] } },
      { type: 'working_set', data: { set_id: 'set_fixture0001', kind: 'orders', count: 23, label: 'unfulfilled orders older than 5 days, last 90 days', parent_label: '', step: 'query', sample: [{ ref: 'gid://shopify/Order/0', label: '#1938' }, { ref: 'gid://shopify/Order/0', label: '#1927' }], truncated: false, lines: [{ label: 'value', value: '£1,481.00' }] } },
    ] },
    { id: 'batch-tags', label: 'Bulk tag · hold to arm', items: [{ type: 'batch_action', data: { batch_id: 'batch_fixture0001', status: 'pending', risk: 'red', operation: 'batch_order_tags_add', title: 'Add tags to 21 orders', summary: 'delayed-sept', detail: 'Added to each order\'s tags; nothing is removed. Each order is checked and proven on its own.',
      set: { set_id: 'set_fixture0001', label: 'unfulfilled orders older than 5 days, last 90 days', kind: 'orders', count: 23 }, requested: 23, eligible: 21, excluded_count: 2,
      excluded: [{ label: '#1902', reason: 'already has those tags' }, { label: '#1899', reason: 'already has those tags' }],
      members: ['#1938', '#1937', '#1935', '#1934', '#1931', '#1930', '#1929', '#1927', '#1926', '#1925', '#1924', '#1922', '#1921', '#1920', '#1919', '#1917', '#1916', '#1915', '#1913', '#1912', '#1911'], sample: ['#1938', '#1937', '#1935', '#1934', '#1931'],
      facts: [{ label: 'Tags', value: 'delayed-sept' }, { label: 'Set', value: 'unfulfilled orders older than 5 days · 23 orders' }], preview: null,
      interaction: { kind: 'hold_to_arm', label: 'Hold to arm, then tap', footer: 'nothing happens until you hold the card, then tap it', target: 'Apply to all', armed_after_ms: 650 }, ttl_s: 120, reversible: true, commit: { allowed: true } } }] },
    { id: 'batch-drafts', label: 'Bulk drafts · hold and drag', items: [{ type: 'batch_action', data: { batch_id: 'batch_fixture0002', status: 'pending', risk: 'red', operation: 'batch_email_drafts', title: 'Save 26 drafts', summary: 'Your order {order_number}', body: 'Hi {first_name},\n\nYour order {order_number} has been with us {order_age_days} days and is on its way this week. Sorry for the wait.',
      detail: 'One draft per customer, saved in Gmail drafts. Nothing is sent; sending is a separate step, one at a time.',
      set: { set_id: 'set_fixture0002', label: 'delayed orders — who have not emailed us', kind: 'orders', count: 26 }, requested: 26, eligible: 26, excluded_count: 0, excluded: [],
      members: ['#1938', '#1937', '#1935', '#1934', '#1931', '#1930'], sample: ['#1938', '#1937', '#1935', '#1934', '#1931'],
      facts: [{ label: 'Subject', value: 'Your order {order_number}' }, { label: 'Set', value: 'delayed orders — who have not emailed us · 26 orders' }],
      preview: { to: 'Sam Fixture <sam@example.com>', subject: 'Your order 1938', body: 'Hi Sam,\n\nYour order 1938 has been with us 8 days and is on its way this week. Sorry for the wait.\n\nCROOKS' },
      interaction: { kind: 'hold_drag_target', label: 'Hold, then drag to the target', footer: 'nothing happens until you hold the card and drag the handle onto the target', target: 'Save all 26', armed_after_ms: 650 }, ttl_s: 120, reversible: true, commit: { allowed: true } } }] },
    { id: 'batch-result', label: 'Bulk result', items: [{ type: 'batch_result', data: { batch_id: 'batch_fixture0001', operation: 'batch_order_tags_add', title: 'Tags added: 20 of 21', detail: 'unfulfilled orders older than 5 days · 23 orders · 2 excluded before the gesture', all_verified: false, summary: '20 applied, 1 not',
      counts: { requested: 23, eligible: 21, excluded: 2, verified: 20, unverified: 0, stale: 0, failed: 1, not_attempted: 0 },
      rows: [{ label: '#1938', outcome: 'applied', code: 'verified' }, { label: '#1937', outcome: 'applied', code: 'verified' }, { label: '#1935', outcome: 'not applied', code: 'failed' }, { label: '#1902', outcome: 'excluded: already has those tags', code: 'excluded' }],
      note: 'The 1 marked not applied was left as it was. Ask for the change again for those, or check them in Shopify.',
      undo: { batch_id: 'batch_fixture_undo', label: 'Undo all', interaction: 'hold_to_arm', ttl_s: 120, armed_after_ms: 650 } } }] },
    { id: 'unknown', label: 'Unsupported type', items: [{ type: 'hologram', data: { html: '<b>should never render</b>' } }, { type: 'assistant', data: { text: 'The unsupported item before this one was skipped; only this card should show. <img src=x onerror=alert(1)> stays as text.' } }] },
  ];

  root.CrooksFixtures = { list };
})(typeof window !== 'undefined' ? window : globalThis);
