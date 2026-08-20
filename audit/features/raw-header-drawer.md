# Header, drawer and the CASE 001 board — raw findings

Area key `header-drawer`. Mobile 390×844 (dpr 3), GB market, staging theme
`202053779799`, unless stated. Every quoted string is copied off the screen.
All screenshots cited were taken in this pass (`hdr-a*`, `hdr-d*`, `hdr-e*`);
the older `header-drawer-*` files in `audit/screens/` are from earlier aborted
runs and none of them is cited here.

---

### The header bar — what is in it and where each thing goes

**Should:** logo (with dark-mode flip), wordmark, `CATALOGUE`, `SEARCH`,
`ACCOUNT`, `BAG [n]`, `MENU`.

**Did:** on a 390px phone the bar wraps to two rows. Row one is the logo alone —
a white handcuffs mark, no text. Row two, left to right:

> `CATALOGUE`  `SEARCH`  `BAG [0]`  `LIGHT MODE`  `MENU`

Destinations, read off the live markup and walked:

| Control | Goes to | Notes |
|---|---|---|
| handcuffs logo | `/` | image only; no alt text you can read, no name beside it |
| `CATALOGUE` | `/collections/all` | h1 `ALL`, 12 items |
| `SEARCH` | `/search` | a full page, not an overlay |
| `BAG [0]` | `/cart` | the count is a `[n]` in lavender |
| `LIGHT MODE` | nothing — a theme toggle | **not in the brief's list of header elements** |
| `MENU` | opens the drawer | text trigger, no hamburger |

Two things are missing from the header that the brief expected there:

- **There is no wordmark anywhere in the header.** The `CROOKSLDN` wordmark
  setting is a *fallback for when no logo is uploaded*, and a logo is uploaded,
  so it never renders. On the homepage the name is rescued by the hero `h1`
  (`CROOKSLDN`), but on a collection page, a product page, the cart, the FAQ or
  Terms, the only thing identifying the shop at the top of the screen is a pair
  of handcuffs.
- **`ACCOUNT` is not in the header at all.** It lives in the drawer's foot, at
  `y=1044` in an 844-tall viewport — i.e. 200px below the fold of an already
  opened drawer. A returning customer wanting their orders has to open the menu
  and then scroll it.

**Verdict:** partly

**Shopper cost:** a returning customer looking for their account taps `MENU`,
sees twelve category links, and has to keep scrolling past a video-game panel
before `ACCOUNT` appears. On every page except the homepage the shop is
unnamed above the fold.

**Evidence:** `audit/screens/hdr-a05-header-bar.png` — bar reads
`CATALOGUE SEARCH BAG [0] LIGHT MODE MENU`; status bar above it reads
`12 PRODUCTS CURRENTLY ONLINE`.

---

_(remaining sections pending pass D/E)_
