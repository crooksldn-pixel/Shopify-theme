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
    { id: 'unknown', label: 'Unsupported type', items: [{ type: 'hologram', data: { html: '<b>should never render</b>' } }, { type: 'assistant', data: { text: 'The unsupported item before this one was skipped; only this card should show. <img src=x onerror=alert(1)> stays as text.' } }] },
  ];

  root.CrooksFixtures = { list };
})(typeof window !== 'undefined' ? window : globalThis);
