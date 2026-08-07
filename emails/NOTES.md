# Order confirmation — restyle notes

`emails/order-confirmation.liquid` is a restyle of Shopify's default order
confirmation notification. Paste it into **Settings → Notifications → Order
confirmation**. Single file, no includes, no external CSS.

> `emails/order-confirmation-original.liquid` was not in the repo when this was
> built — the original was worked from the version pasted into the brief. Drop
> the original in when convenient so future diffs are mechanical.

---

## 1. Liquid inventory

Every Liquid object, filter, tag and conditional branch found in the original,
with a tick where it survives into the new template.

### Setup / status logic

| Item | Kept |
|---|---|
| `delivery_agreements \| map: 'delivery_method_type' \| uniq` | ✓ |
| `has_split_cart` / `non_none_count` loop | ✓ |
| `non_none_agreements_count` loop | ✓ |
| `email_title` / `email_body` captures | ✓ |
| `has_pending_payment` | ✓ |
| `buyer_action_required` | ✓ |
| `payment_charged_on_fulfillment` | ✓ |
| `customer.first_name` | ✓ |
| `requires_shipping` | ✓ |
| `split_cart_delivery_method` case (`pick-up` / `local` / `shipping` / else) | ✓ |
| `delivery_method` case (`pick-up` / `local` / else) | ✓ |
| `delivery_instructions != blank` | ✓ |
| `consolidated_estimated_delivery_time` (both the >1 agreement and single variants) | ✓ |
| `line_items \| where: "gift_card"` | ✓ |
| `properties["__shopify_send_gift_card_to_recipient"]` + `properties["Recipient email"]` | ✓ |
| gift-card recipient vs. "separate emails" branch | ✓ |

### Head / header

| Item | Kept |
|---|---|
| `/assets/notifications/styles.css` link | ✓ |
| `shop.email_accent_color` | ✗ — see §2 |
| `shop.email_logo_url` / `shop.email_logo_width` | ✓ |
| `shop.name`, `shop.url` | ✓ |
| `order_name` | ✓ |
| `po_number` | ✓ |

### Action buttons

| Item | Kept |
|---|---|
| `order_status_url` present / absent branches | ✓ |
| `shop_app_tracking_url` + `shop_app_tracking_button_variant_key` | ✓ |
| `track_with_shop` vs. download variant | ✓ |
| `mailer/shop_logo.png \| cdn_asset_url` | ✗ — see §2 |
| "Visit our store" secondary + fallback primary | ✓ |

### Pending payment

| Item | Kept |
|---|---|
| `transactions \| size` guard | ✓ |
| `transaction.show_buyer_pending_payment_instructions?` | ✓ |
| `transaction.buyer_pending_payment_notice` | ✓ |
| `buyer_pending_payment_instructions` header/value loop | ✓ |
| `transaction.amount \| money` | ✓ |

### Order summary — split cart (`delivery_method_types.size > 1`)

| Item | Kept |
|---|---|
| Legacy `subtotal_line_items` without `delivery_agreement` | ✓ |
| `line.groups.size == 0` guard | ✓ |
| `legacy_separator` + separator rule | ✓ |
| Legacy `line_item_groups` without `components.first.delivery_agreement` | ✓ |
| `for delivery_agreement in delivery_agreements` | ✓ |
| `delivery_agreement.line_items != blank` | ✓ |
| `delivery_agreements.size > 1` heading | ✓ |
| `delivery_method_name` | ✓ |
| `delivery_method_type == 'pick-up'` + `estimated_delivery_date` | ✓ |
| `'shipping' / 'local' / 'pickup-point'` + `presentment_title` + `estimated_delivery_date` | ✓ |
| `delivery_agreement.non_parent_line_items` | ✓ |
| `delivery_agreement.line_item_groups` (deliverable / parent-agreement / components fallback) | ✓ (single hoisted branch — see §2) |
| `{% unless forloop.last %}` separator between agreements | ✓ |

### Order summary — single delivery method

| Item | Kept |
|---|---|
| `subtotal_line_items` flat loop | ✓ |
| `line_item_groups` flat loop | ✓ |

### Line item internals (all four render sites)

| Item | Kept |
|---|---|
| `line.nested_line_child?` skip | ✓ |
| `presentment_title` / `title` / `product.title` fallback chain | ✓ |
| `line.image` + `line \| img_url: 'compact_cropped'` | ✓ (filter untouched) |
| `'notifications/no-image.png' \| shopify_asset_url` | ✓ |
| `variant.title != 'Default Title'` | ✓ (collapsed — see §2) |
| `line.groups` "For:" / "Part of:" | ✓ |
| `line.bundle_components` loop | ✗ — dead branch, see §2 |
| gift card + line item properties loop, `_`-prefix skip, `/uploads/` link, `split: '/' \| last` | ✓ |
| `selling_plan_allocation.selling_plan.name` | ✓ |
| `refunded_quantity > 0` | ✓ |
| `discount_allocations` where `target_selection != 'all'`, `\| upcase`, `amount \| money` | ✓ |
| `original_line_price != final_line_price` strikethrough | ✓ |
| `final_line_price > 0` else "Free" | ✓ |
| `unit_price \| unit_price_with_measurement: unit_price_measurement` | ✓ |
| `nested_line_parent?` + `nested_lines` children | ✓ |
| `line.quantity < line.quantity` "X of Y" | ✗ — always false, see §2 |

### Line item group internals (all render sites)

| Item | Kept |
|---|---|
| `deliverable?` true/false split | ✓ |
| component price summing (`final_line_price`, `original_line_price`) | ✓ |
| discount key de-dup (`title \| append: type`, `split: "," \| uniq`) and per-key amount summing | ✓ |
| `parent_sales_line_item` | ✓ |
| `display_title`, `quantity`, `variant.title`, `image` / `parent_line_item.image` | ✓ |
| `'notifications.views.mailers.notifications.discount_free' \| t` | ✓ |
| component rows: title order flips on `deliverable?`, variant, per-component discounts, per-component price cell only when `deliverable?` | ✓ |

### Totals

| Item | Kept |
|---|---|
| `discount_applications` loop, `order_discount_count`, `total_order_discount_amount` | ✓ |
| shipping discount: `has_shipping_discount`, `shipping_discount_title`, `discount_value_price`, `epsilon` compare, `value_type == 'percentage' and value == 100`, `free_shipping`, `discounted_shipping_price` | ✓ |
| Subtotal (`subtotal_price \| plus: total_order_discount_amount`) | ✓ |
| Order discount / Order discounts (singular + plural) and per-application lines | ✓ |
| `retail_delivery_only` unless | ✓ |
| `shipping_methods` `price_with_discounts` / `original_price` sums | ✓ |
| `pickup_methods` sum + pickup line + its discount line | ✓ |
| `delivery_method_for_subtotal` + `render_fallback_delivery_subtotal` (both triggers) | ✓ |
| fallback Shipping / Pickup title capture, free vs. discounted vs. plain | ✓ |
| `total_duties` | ✓ |
| `tax_price` | ✓ |
| `total_tip > 0` | ✓ |

### Transactions / payment terms

| Item | Kept |
|---|---|
| sale / capture / authorization / refund / change accumulation, `status` guards | ✓ |
| `amount_rounding` / `net_transaction_amount_rounding` | ✓ |
| `shopify_pay_captured`, `shop_cash_offers_captured`, the shop-cash top-up loop | ✓ |
| `payment_terms.automatic_capture_at_fulfillment == false or b2b?` | ✓ |
| `next_payment.due_at`, `due_at_date` | ✓ |
| Cash rounding rows (both branches) | ✓ |
| Total / Total paid today / Total due on receipt / on fulfillment / due `{{ due_at_date }}` | ✓ |
| `total_outstanding`, `next_payment.amount_due` | ✓ |
| `total_discounts` "You saved" (all three placements) | ✓ |
| `financial_status == 'paid'` + `order.transactions \| map: 'gateway_display_name' \| uniq \| join` | ✓ |
| `transaction_amount != total_price and payment_terms == nil` with the authorized-only skip | ✓ |
| Per-transaction breakdown (`transaction_size > 1 or transaction_amount < total_price`) | ✓ |
| gift card / credit card / gateway name captures | ✓ |
| refund rows, `refund_method_title` chain, `shopify_store_credit` → `routes.account_profile_url` "View" link | ✓ |
| `times: -1` on refund amounts | ✓ |
| `original_presentment_currency \| default: currency`, `wallet_brand` wechat_pay / alipay CNY note | ✓ |

### Customer information

| Item | Kept |
|---|---|
| `requires_shipping and shipping_address` + `format_address` | ✓ |
| `billing_address` + `format_address` | ✓ |
| `company_location.name` | ✓ |
| `payment_section_body` capture + `strip` + `b2b?` show flag | ✓ |
| `payment_terms.translated_name`, `due_date \| date: format: 'date'`, receipt/fulfillment special case | ✓ |
| gift card digits + `payment_icon_source \| payment_type_img_url` | ✓ |
| `shop_pay_installments` + `credit_card_company == "unknown"` | ✓ |
| `type == "card"` + `credit_card_company \| payment_icon_png_url` + last four | ✓ |
| `first_installment_amount` / `installment_count` | ✓ |
| `gateway_display_name == "Gift card"` + `gateway_icon_source` + `gift_card.last_four_characters \| upcase` + `gift_card.balance` | ✓ |
| `payment_details.local_payment?` + `payment_method_display_name` | ✓ |
| Shop Cash / shop_offer exclusions and the Shop Cash authorization line | ✓ |
| `shipping_methods \| map: 'title' \| uniq`, `delivery_promise_branded_shipping_line`, `shipping_method.title` fallback | ✓ |

### Footer / attachments

| Item | Kept |
|---|---|
| `shop.email` mailto contact line | ✓ |
| `'notifications/spacer.png' \| shopify_asset_url` | ✓ |
| `billing_address.country_code == 'DE' or 'DK'` | ✓ |
| `shop.terms_of_service \| attach_as_pdf` | ✓ |
| `shop.refund_policy \| attach_as_pdf` | ✓ |

---

## 2. What changed, and why

**Removed — dead code the Shopify build had already constant-folded.** These are
compile-time feature flags baked into the template as literals, not order-state
branches. None of them can fire for any customer. Leaving them in doubles the
file for markup that never renders, and the brief asks for something readable in
the admin editor. Each one, and what it folded to:

- `{% if false %} … bundle_components loop … {% else %} … line.groups … {% endif %}`
  → kept the `line.groups` branch. (Three occurrences.)
- `{% if false and is_parent %}` on the image cell and price cell → kept the else
  branch in both. (Two occurrences each.)
- `{% if true %}` / `{% if false %}` blocks that only picked CSS class names →
  the classes are gone anyway, replaced by inline styles.
- The variant-title `if / elsif / elsif` chain
  (`is_parent == false` / `nested_line_parent?` / `bundle_parent? and false == false`)
  → the three branches are a complete cover of `variant.title != 'Default Title'`,
  so it collapses to that single test with no behaviour change.
- `{% if line.quantity < line.quantity %}` "X of Y" → never true, folded to the
  plain quantity. In the components-fallback loop the original wrote
  `line.quantity < component.quantity`, comparing a component against whatever
  `line` was left over from an earlier `for` loop — that one *could* fire and
  print a nonsense "3 of 1". Folded to the component quantity. **This is a bug
  fix, not just a fold** — worth knowing if you ever diff against Shopify's
  template again.

**Restructured, same output.** Inside `delivery_agreement.line_item_groups` the
original emitted the identical group block twice — once for
`deliverable? == false`, once for a deliverable group whose parent belongs to
this agreement. Hoisted into a `render_group` boolean so the block appears once.
Same conditions, same markup, half the code.

**`shop.email_accent_color` dropped.** It drove link and button colour from the
admin's notification settings. The design system fixes those at `#542578` /
`#A77AC7`, and a merchant-set accent would break the palette. If you want it
back, it is three inline colours.

**`mailer/shop_logo.png` (Shop app logo) dropped from the tracking button.** It
is a dark asset and would be invisible on the dark button; the button now reads
"Track order with Shop" / "Download to track with Shop" as text. Logic and URL
unchanged.

**`notifications/discounttag.png` dropped.** Same reason — a dark grey tag icon
on `#0B0A0E`. Discount lines now use an en-dash and the uppercase code, which
also survives images-off.

**Invalid nesting fixed.** The original wrapped `<tr>` elements in `<div>`
(`.payment-terms`, `.subtotal-line__value-small`) and rendered the whole
`email_body` capture — which contains `<p>` and `<h3>` — inside a `<p>`. Both
crash Outlook's table parser. The divs are gone and `email_body` sits in a
`<td>`.

**Order date added.** `{{ order.created_at | default: created_at }}` in the
confirmation block. Not in the original; §6 asks for a date. Confirm it renders
on the test send.

**`shop.address` added to the footer.** Guarded by `{% if shop.address %}`, so
it renders nothing if the object is unavailable in the notification context.
Check the test send; delete the block if it comes out blank or malformed.

**Not carried over:** the scanline texture (no `repeating-linear-gradient` in
Outlook), VT323, all rounded corners, all shadows.

---

## 3. Clients expected to alter it

| Client | What happens |
|---|---|
| **Apple Mail (macOS), Mail (iOS)** | Renders as designed. IBM Plex Mono loads. This is the reference rendering. |
| **Gmail web / Gmail iOS + Android** | Strips the web font → Courier New. Strips the `<style>` block's media queries in some app contexts, so the mobile stacking of the address columns may not fire — the columns stay side by side but still fit at 375px. Colours held by inline styles survive. |
| **Gmail with a non-Google account (Gmailified)** | Most aggressive dark-mode inversion. Expect it to flip panels toward light and force its own link colours. `#0B0A0E` avoids the worst of it; `.crx-unstyle` forces the address blocks back to `#DDD7C9`. |
| **Outlook.com / Outlook web** | Rewrites colours in dark mode, sometimes inverting backgrounds while leaving text light — the known failure case. Legible, not ours. Also ignores `max-width`, hence the fixed `width="600"`. |
| **Outlook 2016–2021 Windows (Word engine)** | No `border-radius` needed (radius 0 anyway), no media queries, no `background-image`. Table layout, `bgcolor` attributes and `width`/`height` on images are all there for this client. Letter-spacing renders but loosely. |
| **Yahoo / AOL** | Fine. Occasionally drops `letter-spacing` on `<div>` — labels lose their tracking, nothing breaks. |
| **Samsung Mail / Android default** | Force-inverts dark emails. Expect a light rendering with dark text. Readable. |

Aim was legible-if-altered. The two that will not look like the design are
Outlook.com dark mode and Gmailified accounts.

---

## 4. Policy discrepancies (§7)

The original template contains **no** shipping times, returns window, or contact
address — Shopify's default says only "We're getting your order ready to be
shipped." So nothing in §7 contradicts the original outright. Two things to
confirm before this goes live, because both are quoted back at us in disputes:

1. **`info@crooksldn.com` vs `{{ shop.email }}`.** The chain-of-custody returns
   step hard-codes `info@crooksldn.com` per the brief. The footer uses
   `{{ shop.email }}` from the original. If the shop's notification email is not
   `info@crooksldn.com`, the email gives customers two different addresses.
   Either set the shop email to match, or tell me and I will point the returns
   line at `{{ shop.email }}` too.
2. **"Free UK shipping on every order"** is asserted in step 02 while the totals
   block renders whatever shipping actually cost. If any rate charges for UK
   shipping, that copy contradicts the receipt directly above it. Worth checking
   against the live shipping profile.

Also note the theme's own locale strings still carry Shopify's stock
"Free 30-day returns" (`locales/en.default.schema.json`), which conflicts with
the 14-day window in §7. That is storefront copy, not this email, but it is the
same claim in two places saying different things.

---

## 5. Test checklist — where it is most likely to break

Run the test send, then look at these in this order. They are ranked by how
likely they are to be wrong and how bad it is if they are.

1. **Dark mode inversion, Outlook.com and Gmail app.** Open in each. Is the text
   still readable, and does anything become dark-on-dark or light-on-light?
   Specifically check the purple button — if a client inverts the background but
   not the `#DDD7C9` label, the button goes blank.
2. **The address blocks.** `format_address` emits its own markup; clients love to
   colour those lines blue or black. Check the shipping and billing addresses are
   `#DDD7C9` and not the client's default link colour.
3. **Images blocked.** Turn images off. Every product row should still show
   `EXH nn`, title, variant, quantity and price, with no collapsed columns and no
   large empty gaps where the 60px thumbnails were.
4. **375px phone.** Address columns should stack (Apple Mail, iOS) or sit
   side-by-side and still fit (Gmail app). Nothing should scroll sideways. Watch
   the totals rows — long money strings with `money_with_currency` are the widest
   things in the email.
5. **Discount code order.** Place the real test order with a code. You should see:
   the per-line discount under the item in accent, the "Order discount" row, the
   named discount line beneath it, and "You saved" under the total. Four places,
   all fed by different Liquid. This is the branch most likely to have been
   damaged in the restyle.
6. **Order number legibility.** 32px in Courier New is wider than in Plex Mono.
   On a 375px screen with a long order name plus a `#`, confirm it does not wrap
   awkwardly against the date on the right.
7. **The order date.** New field. If it renders blank, `order.created_at` is not
   exposed in this context and I will swap it.
8. **Footer shop address.** Also new and guarded. Blank is fine and expected on
   some setups; malformed is not.
9. **Preheader.** Check the inbox preview line reads "Order #1234 confirmed.
   Dispatch within 24 hours." and that the padding characters after it are not
   visible in the email body.
10. **Outlook Windows, if you have access.** Look for gaps between table cells
    and any 1px hairline that has vanished or doubled.

---

## 6. Reuse for shipping confirmation / shipping update

Three blocks are self-contained and can be lifted verbatim — they are marked
with banner comments in the file:

- `BLOCK: HEADER (reusable)` — logo/wordmark, release-notice label, order number,
  PO number.
- `BLOCK: CHAIN OF CUSTODY (reusable)` — the four steps. For shipping
  confirmation, step 02 becomes the current state; consider marking the active
  step in `#DDD7C9` and the rest in `#8A8377`.
- `BLOCK: FOOTER (reusable)` — contact, address, wordmark, sign-off.

The line item, totals and customer information blocks are order-confirmation
specific and will need their own Liquid inventory against those templates'
originals — shipping notifications expose `fulfillment.item_count`,
`fulfillment.fulfillment_line_items` and `fulfillment.tracking_urls` rather than
`subtotal_line_items`, so they are not a copy-paste.
