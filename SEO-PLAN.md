# SEO plan — CROOKSLDN

Written 2026-08-17 against staging theme `202053779799`. Every number below was
measured, not estimated; the method is noted so it can be re-run.

---

## The baseline, as measured

| Measure | Value | How |
|---|---|---|
| Indexable URLs | **29** — 14 products, 8 collections, 5 pages, 1 blog index | `/sitemap.xml` and its four children |
| Blog articles | **0** | Admin API `blogs { articlesCount }` |
| Products with an SEO title or description | **0 of 14** | Admin API `products { seo }` |
| Collections with an SEO title or description | **0 of 8** | Admin API `collections { seo }` |
| Collections with no description at all | 3 of 8 (frontpage, TRACKSUITS, ALL) | same |
| Homepage `<title>` | `CROOKSLDN` — 9 chars | live HTML |
| Homepage meta description | missing | live HTML |
| Canonical, Open Graph, image alt | present and correct | live HTML |

The constraint this creates: 29 URLs carrying near-duplicate two-line
descriptions is not enough surface to rank. Four products share the sentence
"built for structure and everyday wear" verbatim.

---

## The launch blocker that was fixed

The live theme emits `ProductGroup` JSON-LD from Horizon's
`sections/product-information.liquid`. The Crooks product template does not use
that section, and `sections/header.liquid` — which emitted `Organization` — is
disabled in this theme's header group.

**Publishing the redesign before this change would have deleted every product
rich result and all Google Shopping free-listing eligibility.** Verified: the
staging homepage carried zero JSON-LD blocks.

### What now ships

| Page | Structured data | Source |
|---|---|---|
| Product | `ProductGroup` + one `Product` per variant, each with `Offer` (price, currency, availability, condition, seller) | `snippets/crooks-schema-product.liquid` |
| Product | `BreadcrumbList` — Home > Collection > Product | same |
| Collection | `CollectionPage` + `ItemList` of the products actually rendered | `sections/crooks-exhibit-log.liquid` |
| Collection | `BreadcrumbList` — Home > Collection | same |
| Every page | `Organization` (logo, contact, sameAs) + `WebSite` with `SearchAction` | `snippets/crooks-schema-site.liquid` |
| Questions | `FAQPage`, 14 Q&As | `sections/crooks-faq.liquid` |

All server-rendered in Liquid, never injected by JS, per Google's December 2025
JS-SEO guidance. Every interpolated value passes through the `json` filter.

Deliberately **not** emitted:
- `aggregateRating` / `review` — no reviews app is installed. Inventing ratings
  is a manual action, not an optimisation.
- `OfferShippingDetails` — the rate card is tiered and country-dependent, and
  wrong shipping data in schema is worse than none.

Two details worth knowing: `sameAs` is filtered to an allowlist of social hosts,
because without it the footer's CASE 001 link was being published as a CROOKSLDN
profile; and the product breadcrumb falls back to the product's own collection
when a visitor lands directly, which is what a search result always is.

### Verified on the deployed pages

    PDP jeans     ProductGroup, 5 variants, £60.00 GBP, InStock, variesBy=size
                  Breadcrumb: Home > Denim > BLUE WASH OG JEANS
    PDP socks     ProductGroup, 4 variants, £6.00 GBP
                  Breadcrumb: Home > Accessories > BLACK/BLUE MOTIONTEC SOCKS
    Collection    CollectionPage, numberOfItems 4, all 4 listed
    Every page    Organization sameAs [instagram, tiktok], WebSite SearchAction
    Headings      exactly one h1 on homepage, collection and product

Collection pages previously had **no h1 at all**, on this theme or the live one.
They do now; the homepage register still uses h2 because the hero owns the h1
there.

---

## What only the owner can do

Ordered by leverage.

1. **Google Search Console.** Verify the domain, submit `/sitemap.xml`. Until
   this exists there is no baseline and no way to know whether any of this
   worked. Nothing else on this list is measurable without it.
2. **Google Analytics 4**, if not already connected.
3. **Rewrite the 14 product descriptions.** 150–300 words, no shared sentences,
   covering fabric weight, fit, wear, sizing. Fix the contradictions found in
   audit B7 while editing: the jeans say "9-16 days delivery uk" against
   custody's "UK 1–2 working days".
4. **Write the 8 collection descriptions.** Three have none.
5. **Set SEO title + description** per product and collection — currently 0 of 22.
6. **Homepage title and meta description**: Online Store → Preferences. The
   title is the brand name alone today, which matches nothing anyone searches.
7. **Start the blog.** Zero articles is the single largest reason there is
   nothing to rank.
8. **A reviews app** (Judge.me has a free tier) — this is what makes
   `aggregateRating` legitimate, and star ratings in results follow.
9. **Add SKUs to variants.** All variants currently return `sku: null`, which
   weakens Merchant Center matching.
10. **Google Merchant Center**, once the theme carrying product schema is live.

---

## Measurement

Set the baseline the day Search Console is verified. Everything before that is
unmeasurable.

| Metric | Source | Baseline | 3 months | 6 months |
|---|---|---|---|---|
| Impressions | GSC Performance | set on day 1 | ×3 | ×6 |
| Clicks | GSC Performance | set on day 1 | ×2 | ×4 |
| Indexed pages | GSC Coverage | ~29 | 40+ | 60+ |
| Queries in top 20 | GSC Performance | set on day 1 | 25+ | 75+ |
| Valid product rich results | GSC Enhancements | 0 (new theme, pre-fix) | 14 | 14 |
| Core Web Vitals | CrUX / GSC | CLS failing | all green | all green |

Realistic expectation: a 14-product store with no editorial content and little
authority will not rank for "streetwear". What is winnable is brand search,
long-tail product terms ("baggy grey wash jorts"), and Google Shopping free
listings. That is the 3–6 month picture.

---

## Tooling note

The `claude-seo` plugin (v2.2.4, MIT) is installed at `~/.claude/skills/`. Its
25 skills are usable as methodology, but **its automated fetchers cannot run
from the remote container**: all egress here goes through a loopback proxy and
`scripts/url_safety.py` refuses to resolve loopback addresses by design. That is
the plugin behaving correctly — the guard was not weakened to work around it.
Run those crawlers from a local machine instead.
