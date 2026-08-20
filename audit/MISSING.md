# MISSING — what a shopper looked for and could not find

Separate from broken, deliberately: a missing thing and a broken thing need
different responses. Nothing here is a fault in code — it is an absence a real
shopper reached for and did not meet.

Everything below is lifted from `audit/features/FEATURES.md §3` and carries its
evidence there. The journeys that hit each one are named in
`audit/journeys/SUMMARY.md §3`.

**The four that cost a sale in this run**, before the full list:

1. **A photograph of a garment on a person** that a phone shopper can reach.
   Journey 01 arrived from a video of someone wearing the jeans and met
   `PHOTO 1 OF 1`, a flat shot of the back. Journey 10 chose between two £60
   jeans on nothing but which one had a model shot. The pictures exist on four
   of twelve cards — reachable only by hovering a mouse, which this brand's
   traffic does not have.
2. **A gift card.** Journey 09 abandoned on the payment page with £60 in the
   bag. Checked the header, the drawer, fourteen footer links, two collections
   and four searches. Confirmed off at the shop, not merely unlinked: the
   checkout field reads `Discount code`, not "Discount code or gift card".
3. **A guest route to an order.** Journey 20 had already paid. See
   `CONTRADICTIONS.md` group D — the FAQ promises this twice and the tracking
   page has no form at all.
4. **A price for postage before the last screen.** Journey 07's £6 order became
   £9 after six address fields. The product page states what is *free* and never
   what it costs when it isn't.

---

## 3. What I expected to exist and could not find

Absences, not faults. These need copy, data or a decision — not a repair.

**On the goods**

- **Any way to enlarge a product photograph.** Not by tapping, double-tapping, hovering or
  clicking, on either device. The largest view of a £60 pair of jeans a shopper can obtain is a
  332-pt square. The detail exists — the store holds a 2048px master — and the page never lets a
  shopper near it. Evidence: `audit/screens/pdpcore-82-after-photo-tap.png`,
  `audit/screens/pdpcore-105-after-click-photo.png`.
- **A second angle on the expensive garments.** Seven of twelve products have exactly one
  photograph, four of those seven at £50–£60. `GREY WASH OG JEANS` (£60) is one flat cut-out of
  the **back**; there is no front, no waistband, no hem, no leg opening, nothing on a body and no
  scale reference — while `SPECIFICATION` says `14oz denim` and asks to be taken on faith.
  Evidence: `audit/screens/pdpcore-101-desktop-jeans.png`.
- **Any photograph of the clothes on a person, anywhere.** No lookbook on the homepage — the
  word appears in no text and no link. The only photograph on the whole homepage is the packaging
  shot. Evidence: `audit/screens/homepage-A9-full.png`.
- **A legend for the low-stock mark.** A 4×4px purple square sits on XL of `cb1-wash-jeans` with
  no key, no tooltip, nothing. Select XL and it resolves to `3 LEFT IN SIZE XL` — a real number,
  quietly stated, which is right. A shopper who never taps XL never learns the mark means
  anything. Evidence: `audit/screens/pdpcore-150-lowstock-xl.png`.
- **A sold-out card state that could be observed at all.** Nothing in the register is currently
  sold out, so the register's most important status has never been seen in the wild.

**On copy the theme has nowhere to put**

- **Any collection description on any collection page.** This is *not* the known "three
  collections have no description" item — it is worse. The Denim collection **has** a description
  in admin (`Jorts, jeans and denim.`) and the register never shows it, because there is no slot
  for one. `/collections/denim` reads, in full, before the first card: `DENIM` / `4 ITEMS` /
  `FLAT` / `ON MODEL`. The eight outstanding collection descriptions in the SEO plan would put
  zero words on the page as things stand. Evidence: `audit/screens/catalogue-C01-denim-fold.png`.
- **Any sentence on the homepage saying what CROOKSLDN is or where it ships from.**
  `OWN THE STREETS™` is a slogan; the only prose above the footer is the packaging paragraph.
- **An About page.** Nothing in the header, the drawer, the footer or the FAQ. On a brand with no
  reviews, there is nowhere to learn who this is.
- **A plain-English resolution of the packaging footnote.** `* CONTRABAND 03 SHIPS WITH SWEAT
  BOTTOMS ONLY.` — nothing on the site is called "contraband", and no product is called "sweat
  bottoms"; the register sells `CHARCOAL CELLBLOCK SHORTS`, `V2 BAGGIES` and `CHARCOAL CELLBLOCK
  CREWNECK`, all filed under `SWEATS`. The one item with a condition attached is the one item a
  shopper cannot act on. Evidence: `audit/screens/homepage-A4-packaging-manifest.png`.

**On answers a shopper needs before paying**

- **A price for postage on the product page.** The accordion titled `SHIPPING & RETURNS` mentions
  money twice — `over £20`, `over £70` — and never gives a price. `£3` and `£4.99` exist, well
  written, on the Shipping policy, two taps away and never in the place a shopper looks.
- **International shipping cost, on any page.** "Calculated at checkout" is the answer on all
  three surfaces that address it. An Irish or Dutch shopper cannot find out what postage costs
  without building a cart.
- **The £20 free-shipping threshold anywhere on the shopping path except the rotating strip.**
  The full visible text of the homepage, the catalogue, a product page with every accordion
  forced open, and the cart were scanned: `£20` appears nowhere else. The single commercial fact
  most likely to make someone add a second item is delivered at 9px, for eight seconds out of
  every sixteen, only above the fold, and on the homepage it is behind an overlay.
- **Any statement that a size swap is possible, free, and posted back out at the shop's
  expense** — at the moment of the size decision. It is the single most reassuring sentence on
  the site for a shopper hovering between M and L, and it lives two taps away on a policy page.
- **A "which size am I" prompt at the point of decision.** `QUESTIONS` offers *"If the piece you
  want is not listed yet, message us and we will measure it for you."* and Contact offers
  *"message us your usual fit and we'll point you to the right one"*. The product page, where the
  shopper is actually stuck, offers neither.
- **A method note for the columns that need one** — `SHOULDER`, `SLEEVE`, `LENGTH`. One caption
  is doing duty for jeans, sweatpants, crewnecks and tees, and it names columns those tables do
  not have.
- **Any sign that a four- or five-column measurements table can be dragged sideways.** On the
  crewneck the `SLEEVE` values are sliced mid-character at the phone's edge — `62.2cr`, `63.5cr`,
  `64.8cr` — and sleeve length is exactly what someone buying a heavy crewneck checks. Evidence:
  `audit/screens/pdp-sizing-crew-sizeguide-after.png`.
- **A restock or drops answer in the FAQ**, on a store where sold-out sizes stay visible by
  design and a notify field sits on the product page.
- **Any FAQ answer about discount codes**, on a store running `10CROOKS` and an £85 set.
- **Care instructions outside the product page's `SPECIFICATION` accordion.**
- **A phone number anywhere a shopper would look.** The only one on the site, `+44 7449 010089`,
  is in the last paragraph of the privacy policy — while `/pages/contact` asks the shopper for
  theirs.
- **Any guest route to an order.** Only the dispatch email.

**On the set**

- **The total (`£85`) in the collapsed line.** A shopper deciding whether to open the offer knows
  only "£50, plus something, minus £10". The two numbers that make the case — £95 and £85 — are
  both behind the tick. Evidence: `audit/screens/set-01-collapsed-row.png`.
- **The partner's price (`£45`) anywhere in the offer**, so `Save £10.` can be checked.
- **Any positive stock signal for the partner.** The panel's only stock sentence is a negative
  one; for every genuinely buyable pairing — including the 4-unit ones — the line is blank, while
  the garment on screen says `IN STOCK` two inches above.
- **Measurements or a size guide for the partner garment**, at the moment its size is being
  asked for. The thumbnail in the offer is not a link.
- **Any statement that this is two garments.** "The full fit" is doing that job alone until the
  cart.
- **Any offer to convert two halves already in the cart into the £85 set.**
- **Any route to browse sets.** `Sets` is in no menu; the crewneck and shorts pages never link to
  `CELLBLOCK SET`. Search finds it; browsing never will. Its own page shows two size rows, the
  second named (`CHARCOAL CELLBLOCK SHORTS (SIZE)`) and the first bare (`SIZE`), a crewneck-only
  hero image, and no measurements for either garment. Evidence:
  `audit/screens/set-25-bundle-pdp.png`.

**On the cart and checkout**

- **Any undo, or any confirmation, after removing a line.**
- **Any statement of what carriage *costs* if the free tier is not reached.** The cart names only
  the free thresholds, then `Duties and taxes included. Shipping is calculated at checkout.`
- **A cart note field.** A shopper cannot say "leave with a neighbour".
- **Any CROOKSLDN framing on the empty cart.** No title, no register line — Shopify's stock
  `Your cart is empty` / `Have an account? Log in to check out faster.` / `Continue shopping`,
  in sentence case, in a shop that writes in uppercase evidence-log register everywhere else.
  Evidence: `audit/screens/cc-30-empty-cart-newsession.png`.

**On navigation**

- **A wordmark in the header.** The `CROOKSLDN` wordmark only appears when no logo is uploaded,
  and one is — so on every page except the homepage the only thing naming the shop above the fold
  is a pair of handcuffs.
- **`ACCOUNT` in the header.** It is at the foot of the drawer, 200px below the fold of an
  already-opened menu. A returning customer looking for their orders taps `MENU`, scrolls past
  twelve category links and a video game, and only then finds it.
- **Any sign on the homepage that CASE 001 exists.** The only pointer outside the drawer is a
  footer link at y=4769 of a 4890-tall page — the last 2.5%.
- **A label on the CASE 001 panel.** The art has no heading; the only words are on the button,
  and the button is 118px below the fold of the opened drawer.
- **A way back to the shop from the CASE 001 game.** Its only three controls are `START CASE`,
  `LEADERBOARD` and `SOUND: ON`. It opens in a new tab, so the shop survives — but a phone user
  who does not realise a tab was opened has no route home.
- **Anchors on the search page's FAQ links.** `SIZE GUIDE` and `QUESTIONS` both land at the top
  of a fourteen-question page; the sizing answer is at y=821 and the returns answer at y=946.
- **A pre-typed link to `TERMS`** on the blank search page — the page carrying carriage,
  dispatch, returns and refunds in plain English has to be guessed at.
- **Any heading on `/search`.** The template has none, blank or with results.
- **A second hero route.** One button, `CATALOGUE`, and it is an in-page jump to a heading
  already visible on the same screen once the cookie sheet is gone.
- **Return to the shopper's place in the list after Back.** The filter survives perfectly; the
  scroll position does not.
- **The `OUTLINE` control on collection pages**, where the treatment still applies. It exists on
  the homepage only, so a shopper arriving from `CATALOGUE`, a search result or a shared link
  sees the treatment with no way to turn it off.
- **A carriage readout anywhere near the buy controls.**

---