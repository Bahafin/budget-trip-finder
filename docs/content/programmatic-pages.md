# Spec: programmatic destination and month pages

Written 2026-11-25. For the coding agent and the owner. Nothing here is built yet; this is the spec.

## Goal

Turn the data we already refresh every day (`site/data.json`) into static, indexable pages that answer
"what does a trip to X cost from Toronto" and "where does $X get us in <month>", each with today's dated
numbers and a link into the trip finder with the inputs pre-filled.

Built by the same daily GitHub Actions job that writes `data.json`, as plain HTML files under `site/`
(GitHub Pages for now). No server, no database.

## What the data supports today (checked 2026-11-25)

| Field in data.json | Use on pages | Coverage today |
|---|---|---|
| `destinations[].fares[]` (depart, ret, price per person CAD, foundOn, Aviasales link) | Flight ranges, cheapest dates, "found on" date | 25 destinations; fares cover **Dec 2026 – Feb 2027 only** (Aviasales cache horizon). Some cities have 1-3 fares in a month (Chicago, Dallas, Honolulu) |
| `destinations[].bands[]` (month, tier, low/mid/high per night, n hotels, asOf, source) | Hotel per-night ranges by comfort tier | 3 months × 3 tiers for most; Canadian cities and Fort Lauderdale lack upscale; Kingston has mid only; Punta Cana budget tier has only 5-8 hotels |
| `destinations[].priceLevel` + `constants.dailyBase` | Daily spending estimate | All 25; **estimate, not verified** (validation doc: about 40% of totals, unchecked) |
| `advisories{}` (travel.gc.ca level, text, url) | Advisory badge + link | 16 countries; none for Canada itself (domestic) |
| `notes{}` (know-before-you-go, source_url, reviewed_at) | Know-before-you-go section | Only Mexico (cash declaration) so far |

Not in the data: Lisbon (mentioned in planning, not one of the 25), all-inclusive resort pricing, resort/property fees
(validation doc point 4), activities (Viator not approved yet).

## Page types and URL scheme

Lowercase, hyphens, no dates in URLs (pages update in place; the date is in the content).

| Page | URL | Count now | Example |
|---|---|---|---|
| Destination hub | `/from-toronto/<dest-slug>/` | 25 | `/from-toronto/cancun/` |
| Destination × month | `/from-toronto/<dest-slug>/<month-name>/` | up to 75 (25 × 3 months), gated | `/from-toronto/cancun/january/` |
| Month × budget | `/from-toronto/<month-name>/under-<budget>/` | 3 months × 4 budgets = 12 | `/from-toronto/january/under-2000/` |
| Month hub | `/from-toronto/<month-name>/` | 3 | `/from-toronto/january/` |
| Seasonal | `/from-toronto/march-break/`, `/from-toronto/reading-week/` | as fares become available | |
| Origin hub | `/from-toronto/` | 1 | lists everything above |

- `<dest-slug>`: from destination name: `cancun`, `punta-cana`, `new-york`, `bali` (not "denpasar-bali"), `liberia-costa-rica`
  (disambiguate), `kingston-jamaica`. Keep a fixed slug table in code so renames never break URLs.
- `<month-name>`: `january` … `december`. The page always shows the **next** occurrence of that month that we have fares for,
  with the year in the H1 ("Cancún from Toronto in January 2027").
- Budgets: 1500, 2000, 3000, 5000 (CAD, whole trip). Default group: **2 adults**; a toggle on the page links to the tool for other sizes.
- `under-<budget>` pages are for 2 adults, mid tier by default, with a budget-tier column.
- Future origins (Montreal, Vancouver) get `/from-montreal/...` with the same structure. That's why the origin is in the path now.

## Template: destination hub (`/from-toronto/cancun/`)

H1: **Cancún from Toronto: what a trip really costs** (title tag: "Cancún trip cost from Toronto (2026-27): flights, hotel and daily spend in CAD")

1. **Answer box (top, plain text, ~50 words).** "A 7-night trip for 2 adults from Toronto in January 2027 is estimated at **$X–$Y CAD**,
   most likely about **$Z**, for flights, a mid-range hotel and daily spending. Estimated on <date> from cached fares and hotel prices."
   This is the snippet AI Overviews and Google will quote, so it must be a complete, dated, honest sentence.
2. **Cost table by comfort tier** (budget / mid / upscale): flights, hotel, daily, total; low–expected–high. 2 adults, 7 nights
   (or the nearest length we have fares for, stated).
3. **By month** (one row per month in data): cheapest cached fare per person, its dates and "found on" date; hotel per-night median by tier.
4. **Cheapest dates we've seen** (top 5 fares with dates and age), each with an outbound flight link (Aviasales, `rel="sponsored"`).
5. **What's in and what's not.** Included: return flight, hotel room, daily food/transport/entry estimate. Not included: travel insurance,
   checked bags (if the fare excludes them), resort/property fees paid at the hotel, activities, tips. Plain list, same on every page.
6. **How sure are these numbers?** Confidence labels from the engine (`cached (Nd)`, `sampled (Nd)`, `estimated`), the number of hotels
   sampled, and a link to the validation write-up. One sentence on known weaknesses (holiday dates run low; daily spend unverified).
7. **Travel advisory.** "Government of Canada advisory: **Level N – <level text>**" + link to the travel.gc.ca page. No copied advisory text.
   "Always verify entry requirements with official sources."
8. **Know before you go.** Items from `notes[country]`, each summarised in our words with its source link and reviewed date. Hidden if empty.
9. **Try your own numbers.** Button into the tool with `?dest=CUN&adults=2&nights=7&month=2027-01&tier=mid` pre-filled.
10. **Email sign-up.** "Get a monthly email when Cancún trips from Toronto get cheaper" (see email note below).
11. **Related pages** (internal links, see below).
12. **Footer block on every page:** affiliate disclosure, "prices are estimates in CAD, checked on <date>; you book and pay on the partner's site",
    data sources (Travelpayouts/Aviasales cache, LiteAPI hotel sample, World Bank price levels CC BY 4.0).

Optional, hand-written (not generated): a 100-200 word "local tips" paragraph per destination written by the owner over time.
Pages with a human paragraph are visibly better than pure templates. Prioritise the top 10 (see README).

## Template: destination × month (`/from-toronto/cancun/january/`)

Same as hub sections 1-2 and 4-12, restricted to that month, plus:
- **Trip lengths that fit common budgets**: rows for $1,500 / $2,000 / $3,000 / $5,000 → longest trip that fits at each tier (engine `bestPackage` with `nights=null`).
- **Compared with other months** (one line each, links to sibling month pages).

## Template: month × budget (`/from-toronto/january/under-2000/`)

H1: **Where $2,000 gets two people from Toronto in January 2027**
1. Answer box: how many of our 25 destinations fit, the cheapest three, date estimated.
2. **Fits** list: engine `search()` results with `fit == "within"`, sorted by expected total; for each: total range, nights, dates, tier, one-line "why it fits".
3. **Stretch** list: `fit == "stretch"` (expected over budget, low under).
4. **Doesn't fit this month, and what it would take**: destinations over budget with their expected total ("Tokyo: about $6,900 for 7 nights").
   Honest "no" answers are useful and rare.
5. Method box: 2 adults, which tiers, nights rule, what's included.
6. Links: same budget other months; same month other budgets; each listed destination's month page.

"Why it fits" blurbs may be LLM-written from structured fields only, with every number in the blurb checked against the engine output
and the blurb discarded on mismatch (PHASE1_SPEC section 7). Simpler first version: template sentences, no LLM.

## Indexing gates (avoid thin pages and Google's scaled-content policy)

A page is generated with `<meta name="robots" content="index,follow">` only if:
- **Destination × month:** ≥ 5 cached fares in that month, **and** at least one fare within ±2 nights of 7, **and** a hotel band for mid tier with n ≥ 10.
  Otherwise the page is generated with `noindex,follow` (still useful from the tool) or skipped. Today this keeps out e.g. Chicago and Honolulu in January.
- **Destination hub:** ≥ 2 months of fares. All 25 qualify today.
- **Month × budget:** ≥ 3 destinations within or stretch. A "nothing fits under $1,500 in February" page is noindex but can exist.
- **Freshness:** if the newest fare used is older than 14 days, or `data.json` hasn't refreshed for 3 days, the page shows a warning banner
  and switches to `noindex` until fresh again.
- **No near-duplicates:** pages must differ in their numbers, not just the city name. Don't generate per-tier or per-group-size URLs; those are tool states, not pages.
- Sitemap (`/sitemap.xml`) lists only indexable pages, with `<lastmod>` = data date.
- **Whole site stays `noindex` until launch** (current testing state). The generator reads one flag, `INDEXABLE=true`, flipped at launch after Gate B.

## Update cadence

- **Numbers:** rebuilt daily with `data.json` (existing workflow). Every number carries the date it was estimated; the page shows "Updated <date>".
- **`dateModified` in structured data:** only change it when a headline number moves by more than 5% or the month set changes, so Google doesn't see 25 pages "updated" every day with trivial changes. Store the last published headline numbers to compare.
- **Month rollover:** when a month leaves the fare window (past), its page switches to next year's month once fares exist; until then it shows "last seen" prices clearly labelled as last year's and is noindex.
- **Hand-written paragraphs:** reviewed quarterly.

## Internal linking

- `/from-toronto/` → all hubs and month hubs (the crawl root; linked from the site header/footer).
- Destination hub ↔ its month pages; month pages → sibling months.
- Month hub → its budget pages → each destination month page listed in the results.
- Destination pages → 3 "similar budget" destinations (same region or total within ±15%) and → relevant guides (e.g. Cancún → "spending money in Mexico", "all-inclusive vs DIY").
- Guides/articles → destination and budget pages with descriptive anchors ("what a week in Punta Cana costs"), never "click here".
- Breadcrumbs on every page: From Toronto › January › Cancún.
- The trip finder results link to the matching destination page ("See the full cost breakdown"). This gives the pages internal links from the most-used page.

## Structured data (schema.org, JSON-LD)

Keep it to types that describe the page honestly. Don't mark estimates as offers.

- Every page: `BreadcrumbList`; `WebPage` (or `Article` for month × budget) with `datePublished`, `dateModified`, `author`/`publisher` = the site (Organization).
- Destination hub: `TouristDestination` (name, `geo`, `containedInPlace` country) as the page's `about`.
- FAQ content (e.g. "How much spending money do I need for Cancún?") can use `FAQPage` markup, but Google shows FAQ rich results only for
  authoritative government/health sites since 2023, so it's optional and low value. Keep the Q&A on the page anyway; AI answers read it.
- **Do not use `Offer`, `Product`, `AggregateOffer` or `Flight` with prices.** We are not selling, the prices are estimates, and `Offer` markup
  invites "price" rich results that would look like we're the seller (TICO, Competition Bureau). Prices live in visible text and tables only.
- `Dataset` markup is possible later for a "Toronto trip cost index" page (good for links from journalists).

## Guardrails (must-haves, checked in tests)

1. **Every price is a dated estimate in CAD**: shown with "est." / range and "estimated on <YYYY-MM-DD>". A build test fails if a page contains a `$` amount not inside an element with a `data-asof` attribute.
2. **Headline numbers are whole-trip expected totals**, never the cheapest single component (drip-pricing optics).
3. **Affiliate disclosure** near the top of any page with partner links, plus the footer block. Partner links use `rel="sponsored nofollow"`.
4. **Referral wording only.** Words list checked at build: no "book now", "our price", "buy", "deal" in our own copy. Use "See flights on Aviasales", "Check hotels on Expedia", "You book and pay on the partner's site".
5. **No copied text** from partners, travel.gc.ca or competitors. Advisories: level number + level name + link (the level names are short official labels, used as labels). Know-before-you-go items are paraphrased (`summary` field is already our wording) with source links.
6. **Viator content is not indexable.** When activities arrive, load them client-side from the live API after page load, mark the container `data-nosnippet`, and never write Viator text, images or prices into the generated HTML. Same rule for any partner whose terms restrict caching or display.
7. **No LLM-produced numbers** (PHASE1_SPEC section 7). Generated prose may only contain numbers injected from engine output.
8. **Entry requirements:** not shown on static pages (nationality is session-only); pages say "Entry rules depend on your passport. Check travel.gc.ca."
9. **Thin-page gates** above, and the global noindex flag until launch.
10. **Attribution:** World Bank data credited (CC BY 4.0) on the sources page and in the footer.
11. **Privacy:** pages need no cookies; email sign-up form goes to a provider with a Canadian-compliant consent flow (CASL: express consent, unsubscribe link). Choosing the provider is an owner task.

## Email (the owned channel)

Every page has one sign-up box, scoped to the page ("Cancún from Toronto", "Trips under $2,000"). Phase 1 can be a simple monthly digest built from the same data:
"This month's cheapest whole trips from Toronto". Needs an email provider account (owner decision; free tiers exist). Not built until the owner picks one.

## Build notes for the coding agent

- Generator: Python script in `backend/` (reuses the engine directly) that writes `site/from-toronto/**/index.html` from Jinja templates, run in the daily workflow after `data.json`.
- Reuse the engine: numbers must match the tool exactly (parity test pattern already exists).
- Add tests: guardrail 1 (dated amounts), guardrail 4 (banned words), indexing gates, sitemap only lists indexable pages.
- Page weight: no JS needed for content; the "try your own numbers" button is a plain link.
