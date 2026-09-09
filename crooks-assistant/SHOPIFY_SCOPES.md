# Shopify app scopes

Least privilege, per change. The read scopes are what the read tools need; each write scope
is named by the one reviewed mutation that uses it (`app/clients/shopify.py`,
`REVIEWED_MUTATIONS`), and `/health` says per change whether the store has granted it. A
scope the store has not granted blocks that change alone and names itself; the others go
on working. Set the scopes on the Dev Dashboard app and release a version; a new scope on
a released app then needs approval in the store admin before it takes effect.

## Reads

```
read_orders
read_marketplace_orders
read_quick_sale
read_customers
read_products
read_inventory
read_locations
read_assigned_fulfillment_orders
read_merchant_managed_fulfillment_orders
read_third_party_fulfillment_orders
read_marketplace_fulfillment_orders
```

- `read_all_orders` is deliberately absent. Without it Shopify exposes only the last sixty
  days of orders; the assistant says so rather than implying there is nothing there.
- The `*_fulfillment_orders` read scopes serve `fulfillments { trackingInfo }` on the order,
  the fulfilment orders a shipment is built from, and the destination check after an address
  change (read best-effort: a store without them still changes the address, and says the
  destination was not checked).
- `read_locations` serves the single-location check before a restock or a stock change.

## Writes, one scope per change

| Change | Reviewed mutation | Scope |
| --- | --- | --- |
| Order note | `orderUpdate` (note) | `write_orders` |
| Tags | `tagsAdd` / `tagsRemove` | `write_orders` |
| Cancel | `orderCancel` | `write_orders` |
| Refund | `refundCreate` | `write_orders` |
| Address | `orderUpdate` (shippingAddress + note) | `write_orders` |
| Fulfil | `fulfillmentCreate` | `write_merchant_managed_fulfillment_orders` |
| Stock | `inventorySetQuantities` (compare-and-swap) | `write_inventory` |

Nothing executes without `CROOKS_WRITES_ENABLED=true`, a login on `CROOKS_ALLOWED_LOGINS`,
that login on the tablet making the gesture, and the scope above — checked on every commit.
Email changes are Gmail's, not Shopify's: their scopes come from the Gmail credential itself
(`gmail.modify`, `gmail.compose`) and show on `/health` the same way.

## Adding a scope, in order

1. Dev Dashboard → the app → Configuration → Admin API access scopes → add the scope → save
   and release a new version.
2. Store admin → Apps → the app → approve the new permission.
3. `make shopify` (or `/health?fresh=1`) — the change's row moves from
   "blocked — Shopify … scope missing" to "ready".

The list of reads was produced by validating every query in `app/tools/shopify_tools.py` and
`app/context/order.py` against the Admin schema, not by guessing; the writes are validated the
same way, mutation by mutation, in `tests/`.
