# Shopify app scopes

Read-only, and no more than the six tools actually need. Set these on the Dev Dashboard app
before releasing a version (M6). The list was produced by validating every query in
`app/tools/shopify_tools.py` against the live Admin schema, not by guessing.

```
read_orders
read_marketplace_orders
read_quick_sale
read_customers
read_products
read_inventory
read_assigned_fulfillment_orders
read_merchant_managed_fulfillment_orders
read_third_party_fulfillment_orders
read_marketplace_fulfillment_orders
```

Notes:

- **No `write_` scope appears here and none should.** If a scope list ever needs a write scope,
  a write tool has been introduced — check `app/tools/gate.py` first.
- `read_all_orders` is deliberately absent. Without it Shopify exposes only the last 60 days of
  orders, which is fine for Day 1; `shopify_find_order` says so explicitly rather than implying
  there is nothing there.
- The four `*_fulfillment_orders` scopes are required by the `fulfillments { trackingInfo }`
  selection in `shopify_order_detail` — that is where tracking numbers come from.
- Adding a scope to a released app is not enough on its own: new scopes need manual approval in
  the store admin before queries stop failing.
