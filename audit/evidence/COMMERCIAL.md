# COMMERCIAL BASELINE — pulled from the live Shopify Admin API, 2026-08-08

Added during Phase 4. A council peer reviewer objected that every "highest-value change" claim was unfalsifiable because nobody had looked at a commercial number. They were right, and the data changed the verdict.

## Trading

| Period | Sales | Orders | AOV |
|---|---|---|---|
| July 2026 | £9,585.45 | 186 | £54.09 |
| August 2026 (to 8th) | £994.66 | 16 | £60.68 |
| June 2026 | **−£195.09** | 9 | £0.00 |
| May 2026 | £718.66 | 30 | £40.31 |
| **90-day total** | **£11,103.68** | | |

Lifetime orders: **764** (latest `CROOKS-1764`). Units sold, 365 days: **878**.

**This corrects the audit's premise.** The brief described a brand with "no reviews, no press, no retail presence" where "every sale is a first-time buyer". True as far as it goes — but this is a trading business with 764 completed orders. The proof that people buy here exists; it simply is not visible anywhere on the storefront.

## Top sellers, 365 days (units)

| Product | Units | On the storefront today? |
|---|---|---|
| CROOKS EXPRESS TEE | 146 | **No — archived** |
| V2 BAGGIES | 127 | Yes (M, L, XL sold out) |
| BLACK CONVICT JOGGERS | 105 | **No — archived** |
| LARGE DUFFLE BAG | 51 | Yes |
| CHARCOAL CELLBLOCK SHORTS | 48 | Yes |
| GREY WASH JORTS | 46 | Yes |
| OG JEANS | 46 | **No — archived** |
| BLUE WASH JORTS | 40 | Yes |
| V1 HOODIE | 36 | **No — archived** |
| CRXST★RZ T-SHIRT | 29 | Yes |
| BLACK CONVICT HOODIE | 28 | **No — archived** |
| 3 CLIVES TEE | 19 | Yes |

## Archived and draft products still holding inventory

| Product | Status | Units in stock | Price | Lifetime units sold |
|---|---|---|---|---|
| CRX GARMS T-SHIRT | ARCHIVED | 985 | £25 | 14 |
| BLACK CONVICT JOGGERS | ARCHIVED | 104 | £60 | 105 |
| OG JEANS | ARCHIVED | 93 | £60 | 46 |
| HYRDOCUFF WINDBREAKER | ARCHIVED | 73 | £85 | 15 |
| V1 HOODIE | ARCHIVED | 72 | £60 | 36 |
| PINK CRSDR JOGGERS | ARCHIVED | 41 | £60 | — |
| BLACK CONVICT HOODIE | ARCHIVED | 39 | £60 | 28 |
| CROOKS EXPRESS TEE | ARCHIVED | 33 | £25 | 146 |
| DOUBLE AGENT BALACLAVA | DRAFT | 8 | £25 | — |
| OG CROOK TEE | ARCHIVED | 4 | £25 | — |
| PINK CRSDR HOODIE | ARCHIVED | 0 | £60 | — |
| **Total** | | **1,452** | | |

**Caveat, stated plainly:** CRX GARMS T-SHIRT at 985 units and the active CRXST★RZ T-SHIRT at 970 units both look like inventory-sync artefacts rather than real stock, and should be counted by hand before anyone acts on them. Excluding CRX GARMS, the remainder is **467 units ≈ £28,270 at retail** — roughly 2.5× the last 90 days of revenue, invisible to every shopper.

## Active products currently overselling

Every variant of these three carries `inventoryPolicy: CONTINUE`, so Shopify keeps accepting orders past zero. All three render `IN STOCK · Ships within 24 hours` on the storefront.

| Product | Total inventory | Worst variant |
|---|---|---|
| MONEY CLIVE TEE | **−22** | `S / BLACK` at −7 |
| 3 CLIVES TEE | **−19** | `S / BLACK` at −5 |
| BROADCAST TEE | **−8** | `S / BLACK` at −3 |

**49 units have been sold that do not exist.** This is the most plausible explanation for June 2026 finishing at −£195.09 net, and it directly contradicts the homepage's own WITNESS STATEMENT: *"When a run is gone it does not come back."* The store keeps selling after the run is gone.

Separately, `V2 BAGGIES / M` sits at `inventoryQuantity: -1` under a `DENY` policy — one unit was oversold before the policy took effect. Inventory policy is inconsistent across the catalogue.

## Why this outranks the storefront findings

The audit's largest measured storefront win is ~933 KB off the homepage from re-uploading eight image masters. That is real and worth doing. It is not worth doing before putting five figures of proven-selling stock back in front of traffic the brand is already paying to acquire, or before stopping the store selling units it does not have.

## Queries used

```
list-orders (limit 20)                                  → 764 total
SHOW total_sales, orders, average_order_value FROM sales SINCE -90d GROUP BY month
SHOW net_items_sold FROM sales SINCE -365d GROUP BY product_title ORDER BY net_items_sold DESC
products(first: 40) { status totalInventory publishedAt onlineStoreUrl }
productVariants { inventoryQuantity availableForSale inventoryPolicy }
```
