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
| Add an item to an order | `orderEditCommit` (after `orderEditBegin` + `orderEditAddVariant`) | `write_order_edits` |

`write_order_edits` covers all three of the order-edit mutations, and only the third changes
anything: the first two build and price a CalculatedOrder — a scratch copy of the order —
which is how the card can say what the line costs, what the order becomes and what the
customer will owe before the owner's gesture. Without the scope the whole family says so and
names itself (`app/families/order_edit.py`), the write tool is not offered to Claude at all,
and every other change goes on working.

Nothing executes without `CROOKS_WRITES_ENABLED=true`, a login on `CROOKS_ALLOWED_LOGINS`,
that login on the tablet making the gesture, and the scope above — checked on every commit.
Email changes are Gmail's, not Shopify's: their scopes come from the Gmail credential itself
(`gmail.modify`, `gmail.compose`) and show on `/health` the same way.

## Not granted, and not written: returns, exchanges, replacements, resends

Four changes the shop will want (§21) have their contract, their request shapes and their
refusal in `app/returns/contract.py`, and no mutation. Each names the scope to grant FIRST;
none of them will do anything until the scope is granted, the reviewed mutation is written and
it has been verified against a store.

| Change | Reviewed mutation it would use | Scope to grant |
| --- | --- | --- |
| Take an item back | `returnCreate` | `write_returns` (+ `read_returns` to read them back) |
| Swap an item | `returnCreate` with `exchangeLineItems` | `write_returns` + `write_order_edits` |
| Send a replacement | `draftOrderCreate` + `draftOrderComplete` (no payment) | `write_draft_orders` |
| Send it again | `fulfillmentCreate` on the remaining fulfilment order | `write_merchant_managed_fulfillment_orders` |

`/health` lists all four as NOT_IMPLEMENTED with the scope beside them, and the model is told
in one line not to attempt them.

Shipping is not a scope at all: Easyship is an external provider and needs credentials
(`CROOKS_EASYSHIP_TOKEN`) and a client that this build does not have. Its row says
DISCONNECTED and names both — see `app/shipping/`.

## Adding a scope, in order

1. Dev Dashboard → the app → Configuration → Admin API access scopes → add the scope → save
   and release a new version.
2. Store admin → Apps → the app → approve the new permission.
3. `make shopify` (or `/health?fresh=1`) — the change's row moves from
   "blocked — Shopify … scope missing" to "ready".

The list of reads was produced by validating every query in `app/tools/shopify_tools.py` and
`app/context/order.py` against the Admin schema, not by guessing; the writes are validated the
same way, mutation by mutation, in `tests/`.
