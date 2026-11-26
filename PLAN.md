# Budget Trip Finder: Implementation Plan

Re-planned 2026-11-25 (first version 2026-11-21). The spec is [docs/PHASE1_SPEC.md](docs/PHASE1_SPEC.md). This file says what gets built, in what order, and what has to be true before each step. The owner's own tasks are in [TODO.md](TODO.md).

**Approach (unchanged):** work is ordered around the go/no-go gates, so nothing expensive is built before the data is proven.
- **A:** accuracy test.
- **B:** TICO's answer.
- **C:** demand test.
- **D:** revenue per 1,000 visitors.

What changed is that the proof of concept is done. The next job is to make it good enough for testers and for Gate A, so the conversations with your employer and TICO rest on evidence.

## Where we are (2026-11-25)

| Done | Evidence |
|---|---|
| Spec rebuilt; wedge decided (Canadian departures, CAD, Toronto first) | docs/PHASE1_SPEC.md |
| Data check: flights from Toronto (148 destinations), hotels via LiteAPI, price levels, advisories | docs/m0-coverage-report.md |
| Proof of concept: pricing engine (30 tests), refresh jobs, cost meter, CLI, local web page | docs/poc-report.md |
| Data cost measured: about $0 a month for 25 destinations (worst case under EUR 2) | docs/poc-report.md |
| Public test site with a browser copy of the engine, checked against the Python engine on every push | https://bahafin.github.io/budget-trip-finder/ |
| Spot check against Google Flights and Booking.com: whole-trip estimates within -8% to +4% after the flight fix | docs/validation-2026-11-24.md |
| API and partner research: what Travelpayouts and LiteAPI offer, which affiliate programs are open | docs/api-coverage-check.md, docs/affiliate-programs-check.md |
| Affiliate programs joined: Aviasales, Klook, KKday (Travelpayouts) | TODO.md |
| Gate A (2026-11-26): 50 trips checked by hand, median whole-trip error 11%, PASS (sandbox hotel prices) | docs/gate-a/report.md |
| Competitor tests: ChatGPT, Gemini, Google Flights Explore; 15 feature ideas | docs/research/ |

**Decisions 2026-11-26:**
- **Name:** Far Enough. **Development domain:** farenoughtrips.com (registered 2026-11-26); farenough.ca held as the likely launch domain. The site stays hidden from search engines until the launch domain is final.
- **Several departure cities at launch, not just Toronto.** Toronto is the development city; Montreal and Vancouver are the first test cities. Everything built from now on is departure-city aware (1.8).
- **Hosting (recommended, owner's call):** Cloudflare Pages for the site and small server functions, GitHub for code and the daily refresh. **Email:** forwarding for hello@, MailerLite (suggested) for sign-ups, CASL double opt-in. See TODO.md.
- **Destination list in the repo** (data/seed/destinations.csv), per departure city from 1.8. Photos are real Wikimedia photos, never AI-generated.

**Ruled out:**
- Hotellook (shut down).
- Amadeus (decommissioned).
- Duffel for Phase 1 (its terms ban metasearch use; Stays needs sales).
- Live Aviasales and Kiwi search (need 50,000+ monthly users).
- Booking.com and other big hotel programs inside Travelpayouts (need traffic, for now).

## Defaults the plan uses

| Decision | Default | Why |
|---|---|---|
| Wedge | **Decided:** Canadian departures | Fixes currency, market and visa scope |
| Origin | Toronto (YYZ, YTZ, Billy Bishop). Montreal and Vancouver after Gate A | Keeps Gate A tractable |
| Destinations | 25, chosen by flight coverage; countries at advisory level 2+ skipped | Can't price what has no fares |
| Flights | Aviasales cached fares; estimate = trip's own fare x 1.10 | Validated 2026-11-25 |
| Hotels | LiteAPI samples into bands, plus the city price index for seasonality | Live data without per-search calls |
| Daily spend | Canadian baseline x World Bank price level | Weakest number; Gate A checks it |
| Hotel link | Klook now, Expedia once approved, Booking.com later | Booking.com needs traffic |
| Activities | Viator (direct), Klook and KKday for Asia | Viator has no traffic minimum |
| Hosting | GitHub Pages static site + GitHub Actions refresh | Free; fine until a real backend is needed |
| LLM | After Gate A | Not needed to pass any gate |

## Stages

```
Stage 1 Tester-ready ──► Stage 2 Gate A ──► (owner: employer + TICO, Gate B) ──► Stage 4 Real product ──► Launch ──► Gate D
        └──► Stage 3 Landing page and demand test (Gate C), in parallel once there is a name
```

### Stage 1: Tester-ready site (about a week)

Goal: testers see fresh, accurate-looking trips, and every click can earn.

- [x] **1.1 Daily automatic refresh** (built 2026-11-26; runs once the two key secrets are added).
  - `.github/workflows/pages.yml` runs daily at 04:17 Toronto time and on every push.
  - It restores the database from the Actions cache and runs `refresh auto` (flights when older than 20 h, hotels 6 days, reference data 25 days, destination list 30 days; an empty database rebuilds itself).
  - It then exports the snapshot, runs both test suites, deploys, and writes a refresh and data-cost summary on each run.
  - Without the secrets it deploys the committed snapshot.
- [x] **1.2 Affiliate links** (done 2026-11-26, except Expedia).
  - `backend/src/tripfinder/links.py` builds Travelpayouts partner links (project 605382) at export time, tagged per destination (`sub_id` such as `site-CUN-flight`). The export checks the format against the partner links API once per run.
  - Flight links are tracked (verified: the redirect lands on Aviasales with marker and click ID).
  - "Check hotels" goes to Klook (tracked) for Asian destinations and an untracked Booking.com search elsewhere, until Expedia's link format is known (TODO.md).
  - Airline names and stops come from the Travelpayouts airlines file.
- [x] **1.3 Accuracy fixes found in validation** (done 2026-11-26):
  - (a) hotel fees LiteAPI marks as paid at the property are now added (same currency only)
  - (b) seasonality: weekly job stores LiteAPI's city price index for all 25 destinations. Each fare gets a factor (trip nights vs sample nights, half-weighted, clamped 0.6-2.0). Calibration in docs/validation-2026-11-24.md
  - (c) ~~`grouped_prices` for richer flight coverage~~ tested: it reads the same cache and adds almost nothing (Chicago in January: 1 fare either way). Thin destinations stay thin. The real fix is the live price check in Stage 4
  - (d) without a requested length, fares shorter than 3 nights are ignored. The default search now returns 3-5 night trips
- [ ] **1.4 Tester feedback.** A "Was this price right?" link on each result, opening a short form with the trip pre-filled (owner provides the form). This doubles as Gate A data.
- [x] **1.5 Small fixes** (all three on the site by 2026-11-26).
  - Airline names instead of codes.
  - A visible "prices updated" date.
  - Clear wording that prices are estimates and booking happens on the partner's site.
- [x] **1.6 Quick wins from research** (2026-11-26; docs/research/feature-ideas.md #5, #8, #9, #10):
  - "Best for" theme chips on the finder and a best-for / what-to-do line on each card (hand-written, data/seed/themes.csv).
  - Mexico City added through data/seed/always_include.csv; when that list changes the daily run adds the new place to the current list (no re-ranking). Hamilton checked and parked (too few cached fares).
- [x] **1.7 Keep the destination list stable** (2026-11-26). A test re-selection had swapped 7 of 25 places on noisy bulk fare counts (1-18 per place). Now:
  - **The list lives in the repo** (data/seed/destinations.csv, 25 places, plus Mexico City from always_include.csv). The live site had drifted: the CI run at 03:37 on 2026-11-26 re-picked by ranking and showed Delhi, Nha Trang, Ottawa, Miami, San José, Warsaw and Yerevan instead of Tokyo, Chicago and others. Now every machine shows the same list; the daily run re-selects only when the file changes, and prints busy routes that aren't on it as suggestions.
  - Without the file, selection is sticky: a place stays while our own daily per-place refresh still finds at least 5 fares (lowest today: 7); only gaps are filled from the bulk ranking. On today's counts nothing changes.
  - New places get a page address from their name, and `tripfinder assets --fill-photos` finds a real, credited Wikimedia Commons photo (reusable licences only, wide and large, marked for review). The daily workflow runs it, so a new place deploys with a photo, and lists missing theme rows with a ready-made request in the run summary.
  - Photos are never AI-generated: a made-up picture of a real place would undercut the honest-numbers promise. AI image skills are for marketing graphics later.
  - Theme rows are short text (no prices), written by a person or an AI session and checked by test_themes.py. Writing them inside the workflow would need an Anthropic API key secret (owner's call).
  - "Doesn't fit, but close": places within max($300, 15%) over the budget, with a link that re-runs the search at that amount.
  - The Gate A result (median whole-trip error 11% on 50 trips) is in "How it works".
  - Hotel bands are rebuilt on every refresh (no API cost), so band rule changes reach the site the next day.

Done when the live site refreshes itself daily, links are tracked, and the 3-trip spot check still holds.

- [x] **1.8 Several departure cities** (built 2026-11-26). Toronto (26 destinations), Montreal (13) and Vancouver (17); 37 destinations in all, 14 of them new (themes written, photos reviewed). Pairs with under 5 cached fares were dropped (Montreal to London, Madrid and Vancouver; Vancouver to Los Angeles and Los Cabos). The March break page stays Toronto-only (Ontario dates). Fare depth checked: Calgary is thin, and Ottawa, Halifax, Winnipeg and Edmonton are too thin for now. Moved up from Stage 4 (decision 2026-11-26). A list of departure cities in the repo; flights stored per city; a destination list per city; one data file per city; a "From" picker on the finder; pages under /from-<city>/; wording driven by the city. Then a new city is one row in a file plus a check that the flight cache has enough fares for it.
- [x] **1.9 Save fare history daily** (started 2026-11-26: tables fare_history and band_history; 826 fare rows on day one). Showing it waits for 30-60 days of data (research #14). Cheapest fare per departure city x destination x month x trip length, plus the hotel band, one row per day. Each refresh overwrites the cache, and history can't be bought back later. After 30-60 days: "about $110 below what we've seen for these dates", worded exactly (Competition Act; no "sale" or "save").
- [ ] **1.11 Things to do (Viator)**, once the API key works. Per destination: the 3-5 best-rated activities with a "from" price in CAD and Viator's own tracked link (each product comes with a productUrl carrying our partner ID; bookings happen on viator.com, which keeps us referral-only). Refreshed weekly into the database like hotels, so a page view costs no API call. Shown on destination pages and as one line on cards ("Top thing to do: ..., from $X"). Not added to the trip total: activities stay optional. Basic affiliate access covers what we need (/destinations, /products/search, /products/{code}, /attractions). Rate limits are per endpoint over 10-second windows.
- [x] **1.10 Card additions** (research #12, #11 part; done 2026-11-26): "Leaves about $X for extras" on trips that fit (rounded down to $10); a route line ("Montreal → Cancun, direct"; stops shown only for exact cached fares).

**Feature backlog:** docs/research/feature-ideas.md (15 ideas, each checked against the Phase 1 rules). Next candidates after 1.8-1.10: ground trips by train or car (#7), results map (#11), when to visit (#15), chat-style search prototype (#2).

### Stage 2: Gate A, the 50-trip accuracy test (about 2 weeks, mostly elapsed time)

Needs the LiteAPI **production** key, so hotel prices are real rather than sandbox.

- [x] **2.1 Test set** (2026-11-26: `tripfinder gate-a generate` → `docs/gate-a/sheet.csv`). A script picks 50 trips: a mix of destinations, 1-4 travellers, 3-10 nights, dates 1-4 months out, including a few holiday dates.
- [x] **2.2 Real prices** (all 50 checked 2026-11-26 in the browser; `python -m tripfinder.gate_a_fill` records them; `tripfinder gate-a report` → `docs/gate-a/report.md`). For each trip, record the real flight price (Google Flights) and hotel price (Booking.com or Expedia, same tier):
  - I do this through the browser where sites allow it.
  - Tester feedback fills in the rest.
- [ ] **2.3 Daily spend check.** Compare our daily figures with published per-city daily budgets, then adjust the baseline.
- [x] **2.4 Report** (2026-11-26, sandbox hotel prices): **PASS**. Median absolute total error 11% (90th pct 32%), real total inside our range on 44 of 50 trips; holiday trips 9%.
  - Flights: median error +1%, so the 1.10 uplift stays (the +12% on the first 10 trips was a small sample).
  - Hotels are the weak part: median -8%, upscale tier -14%. Two Orlando trips (5-star, 2 rooms) and two Caribbean resort trips came out far too high (+68% to +479%); the sandbox price for big resort rooms looks unreliable. Re-run with the LiteAPI production key before quoting the number.
  - Big flight misses: New York Dec 4-6 (cache fare too low, -66%) and Bali over New Year (-36%).
  - Method notes: Booking.com searched as Guanacaste for Liberia and as Bali for Denpasar; Frankfurt 5-star resolved to the airport area; Edmonton has a single 5-star hotel.
- [x] **2.4a Hotel band filters** (2026-11-26). Hotel bands now drop a hotel's quote when it is over 2.5x that hotel's own median across sample dates (sandbox spikes; Orlando 5-star February went to $2,094/night), and leave out all-inclusive resorts (their price includes meals, which daily spending already counts). Re-scored on the 50 checked trips: median total error 10% (was 11%), 90th percentile 27% (was 32%); Orlando A13 +192% → +39%, Punta Cana A08 +54% → +9%. Cancun got slightly lower (A26 -22% → -27%).
- [x] **2.4c Trip dates match the nights priced** (2026-11-26, found by the brand session's review). With a fixed length and no cached fare within 2 nights of it, a trip showed one fare's dates (e.g. Bali "6 Feb-25 Feb (7 nights)") while hotel and daily costs covered 7 nights. Now the return date is departure + nights in both engines, and those estimated trips get an Aviasales search for their own dates instead of the cached link (819 of 2,376 fixed-length packages; 0 mismatches left).
- [ ] **2.4b** Re-run the 50 trips once the production key is in, and look at the trips still over 25% total error (Orlando 5-star in January, Kingston, New York flights, Bali over New Year).
  - Pass: median total error within about 20-25%.
  - Fail: fix the weakest component and re-run.

Done when the Gate A report exists. **This is the evidence for the employer and TICO conversations.**

### Stage 3: Landing page and demand test (Gate C, in parallel)

- [x] Brand name chosen: **Far Enough** (2026-11-26); plans in docs/brand/ and docs/content/. Domain and handles to register (owner, TODO.md).
- [ ] **Hosting move** (domain registered 2026-11-26; waiting on the owner's Cloudflare account and the two secrets, TODO.md): Cloudflare Pages with the custom domain, rename the site to Far Enough, hello@ forwarding. The daily GitHub workflow only changes its deploy step (`wrangler pages deploy site`, project name farenough; GitHub Pages stays up until the new address works, then redirects).
- [ ] Landing page: the pitch, a few live example trips, email sign-up, affiliate disclosure. It also gives the Booking.com (CJ) and Skyscanner applications a real site to review.
- [ ] Simple, privacy-friendly analytics: visits, sign-ups, clicks.
- [ ] Run 4-6 weeks against the **agreed Gate C thresholds** (2026-11-26), judged after at least 1,000 unique visitors:
  - **Pass:** email sign-ups at least 5% of visitors, partner clicks at least 15% of searchers, and 10+ unprompted replies.
  - **Fail:** sign-ups under 2% and clicks under 8%.
  - **In between:** change one thing, run 2 more weeks.
- [ ] Programmatic destination and month pages, per docs/content/programmatic-pages.md (March break page live by 2027-01-04).
- **Gate B timing (decision 2026-11-26):** left open. Building continues as if TICO's answer is fine. Ask TICO before public promotion or paid traffic.

### Stage 4: Real product (after Gate A passes)

- [ ] Hosted backend: Postgres, search API, two-stage pipeline (cached discovery, then a live check of the top results via LiteAPI flights once production flights are activated).
- [ ] Destination page: Viator activities (live, on open), know-before-you-go notes for all 25 destinations, entry requirements (replace the scraped visa data before scaling).
- [ ] Flexible dates, price alerts (more origins moved up to 1.8).
- [ ] Click logging and the Travelpayouts statistics API for Gate D.
- [ ] LLM layer: free-text trip requests, "why this fits" blurbs. It never produces prices.
- [ ] Hardening: monitoring, rate limits, legal copy, privacy policy.

### Launch, then Gate D

- Gate B (TICO's answer in writing) before going public.
- Gate D after 2-3 months: revenue per 1,000 visitors decides paid traffic and Phase 2.

### Phase 2 hooks (do not build now)

Selling trips through LiteAPI (hotels, flights, experiences), with an agent on top of its MCP server. Needs TICO registration and a trust account. Gated on Phase 1 traction.

## Running cost target

| Item | Now | Stage 2 | Stage 4 |
|---|---|---|---|
| Flights, reference data | $0 | $0 | $0 |
| LiteAPI hotel searches | $0 | $0 (within ratio) | $0-2 |
| LiteAPI city price index | n/a | about $2-5/month | about $2-5/month |
| LiteAPI flight live check | n/a | n/a | EUR 0.005 per search beyond 1,500 per booking |
| Hosting, CI | $0 (GitHub) | $0 | Free tier or about $5-10/month for a small server + Postgres |
| Domain | n/a | about $15/year | about $15/year |
