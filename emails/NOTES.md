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

**Light and dark added (second pass).** The first version of this template was
dark-only, with the dark palette inlined. It now inlines light and applies dark
through `prefers-color-scheme`. Full detail, palettes and rationale in §3. No
Liquid changed in that pass — it was a colour and class transform over the
existing markup, verified by re-checking Liquid tag balance and table nesting
afterwards.

**Not carried over:** the scanline texture (no `repeating-linear-gradient` in
Outlook), VT323, all rounded corners, all shadows.

---

## 3. Light and dark

The template ships both palettes in one file. **Light is the base**: every
colour is inlined as its light value, so a client that strips the `<style>`
block still renders a complete, correct light email. Dark is applied by a
`@media (prefers-color-scheme: dark)` block that overrides those inline values
with `!important` on a set of `d-*` classes.

| Role | Light (inline) | Dark (media override) |
|---|---|---|
| Ground | `#F0EDE4` | `#0B0A0E` |
| Panel | `#FAF8F2` | `#0E0C13` |
| Hairline | `#C7BCD2` | `#3A2F4A` |
| Text | `#1C1A22` | `#DDD7C9` |
| Dim | `#6B6459` | `#8A8377` |
| Accent (labels, links) | `#542578` | `#A77AC7` |
| Red (warnings) | `#A8302C` | `#C4433F` |
| Connector glyph | `#A79CB5` | `#3A2F4A` |
| Button fill | `#542578` | `#542578` |
| Button label | `#F5F1E8` | `#F5F1E8` |

Neither ground is pure `#FFFFFF` or `#000000`, so the most aggressive inversion
heuristics stay off. `#A77AC7` is only ~2.6:1 on paper, so light mode promotes
the accent role to `#542578` (11:1) rather than washing labels out. Everything
else keeps its relationship. The button never flips: purple fill, light label,
both modes.

The classes, if you need to hand-edit:

| Class | Overrides |
|---|---|
| `d-g` / `d-p` / `d-u` | ground bg / panel bg / filled 1px rule |
| `d-t` / `d-d` / `d-a` / `d-r` / `d-c` | text / dim / accent / red / connector |
| `d-b` / `d-bt` / `d-bb` | border / border-top / border-bottom colour |
| `d-gt` | hidden preheader text (matches ground so it never shows) |

**Why light is the base and not dark.** Only a minority of clients read
`prefers-color-scheme`. The rest show whatever is inlined, and the ones that
don't will apply their own inversion instead. Those inversion algorithms are
tuned for light emails going dark — that direction produces a decent result.
Dark-first is the direction that breaks, which is exactly why Outlook.com
mangled the previous version. Light base plus a dark override is therefore both
what you asked for and the more robust of the two.

The cost is that the dark brand look is no longer what most recipients see. If
you would rather have dark as the default and let light-mode Apple Mail users
be the exception, that is a swap of the two palettes in the file — say the word.

The previous dark-only version is in git history at the first commit on this
branch if you want to compare them side by side.

---

## 4. Clients expected to alter it

| Client | What happens |
|---|---|
| **Apple Mail (macOS), Mail (iOS)** | Full support. Follows the system setting, light or dark, and loads IBM Plex Mono. This is the reference rendering for both modes. |
| **Outlook for Mac (new), Thunderbird, HEY, Superhuman** | Also honour `prefers-color-scheme`. Expect correct switching. |
| **Gmail web / iOS / Android** | Strips `prefers-color-scheme` entirely — **always shows the light base**. In Gmail's own dark mode it applies its own inversion to that light email, which lands close to the dark palette but is not it. Also strips the web font → Courier New. |
| **Gmail with a non-Google account (Gmailified)** | Most aggressive inverter. Light base gives it the input it handles best, so this is now much better behaved than under the dark-first version. `.crx-unstyle` still pins the address blocks. |
| **Outlook.com / Outlook web** | Ignores `prefers-color-scheme`. Shows light, and in its dark mode applies partial inversion. This was the known failure case before and is largely fixed by going light-first. |
| **Outlook 2016–2021 Windows (Word engine)** | No media queries at all, so always light. That is the correct fallback rather than a broken dark. Table layout, `bgcolor` attributes and explicit image dimensions are all there for this client. Letter-spacing renders loosely. |
| **Yahoo / AOL** | Light only. Occasionally drops `letter-spacing` on `<div>` — labels lose tracking, nothing breaks. |
| **Samsung Mail / Android default** | Force-inverts. Light base inverts cleanly. |

Summary: dark renders properly in the Apple clients and a few others; everyone
else gets the light version, or their own approximation of dark built from it.
No client should now see something illegible.

---

## 5. Policy discrepancies (§7)

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

## 6. Test checklist — where it is most likely to break

Run the test send, then look at these in this order. They are ranked by how
likely they are to be wrong and how bad it is if they are.

1. **Mode switching in Apple Mail.** Open on macOS, then flip System Settings
   between Light and Dark with the message open. The whole email should switch,
   including panel backgrounds, hairlines and the `EXH nn` micro-labels. Anything
   that stays light in dark mode is an element that lost its `d-*` class.
2. **Gmail and Outlook.com show light — confirm that is what you get.** Neither
   reads `prefers-color-scheme`, so both should render the light palette even
   when the client itself is in dark mode (they will tint it themselves). If
   either shows the dark palette, something is wrong with the inline base.
3. **The purple button in both modes.** Fill `#542578`, label `#F5F1E8`, in
   light and dark alike. If a client inverts the fill but not the label, the
   button goes blank — this is the single most likely visual failure.
4. **The address blocks.** `format_address` emits its own markup; clients love to
   colour those lines blue or black. Check the shipping and billing addresses use
   the body text colour in whichever mode you are looking at — `#1C1A22` on light,
   `#DDD7C9` on dark — and not the client's default link colour.
5. **Images blocked.** Turn images off. Every product row should still show
   `EXH nn`, title, variant, quantity and price, with no collapsed columns and no
   large empty gaps where the 60px thumbnails were.
6. **375px phone.** Address columns should stack (Apple Mail, iOS) or sit
   side-by-side and still fit (Gmail app). Nothing should scroll sideways. Watch
   the totals rows — long money strings with `money_with_currency` are the widest
   things in the email.
7. **Discount code order.** Place the real test order with a code. You should see:
   the per-line discount under the item in accent, the "Order discount" row, the
   named discount line beneath it, and "You saved" under the total. Four places,
   all fed by different Liquid. This is the branch most likely to have been
   damaged in the restyle.
8. **Order number legibility.** 32px in Courier New is wider than in Plex Mono.
   On a 375px screen with a long order name plus a `#`, confirm it does not wrap
   awkwardly against the date on the right.
9. **The order date.** New field. If it renders blank, `order.created_at` is not
   exposed in this context and I will swap it.
10. **Footer shop address.** Also new and guarded. Blank is fine and expected on
   some setups; malformed is not.
11. **Preheader.** Check the inbox preview line reads "Order #1234 confirmed.
   Dispatch within 24 hours." and that the padding characters after it are not
   visible in the email body.
12. **Outlook Windows, if you have access.** Look for gaps between table cells
    and any 1px hairline that has vanished or doubled.

---

## 7. Reuse for shipping confirmation / shipping update

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
