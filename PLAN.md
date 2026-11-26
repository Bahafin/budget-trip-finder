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
- [ ] **1.5 Small fixes.**
  - Airline names instead of codes.
  - A visible "prices updated" date.
  - Clear wording that prices are estimates and booking happens on the partner's site.

Done when the live site refreshes itself daily, links are tracked, and the 3-trip spot check still holds.

### Stage 2: Gate A, the 50-trip accuracy test (about 2 weeks, mostly elapsed time)

Needs the LiteAPI **production** key, so hotel prices are real rather than sandbox.

- [ ] **2.1 Test set.** A script picks 50 trips: a mix of destinations, 1-4 travellers, 3-10 nights, dates 1-4 months out, including a few holiday dates.
- [ ] **2.2 Real prices.** For each trip, record the real flight price (Google Flights) and hotel price (Booking.com or Expedia, same tier):
  - I do this through the browser where sites allow it.
  - Tester feedback fills in the rest.
- [ ] **2.3 Daily spend check.** Compare our daily figures with published per-city daily budgets, then adjust the baseline.
- [ ] **2.4 Report.** Median and 90th-percentile error per component and in total.
  - Pass: median total error within about 20-25%.
  - Fail: fix the weakest component and re-run.

Done when the Gate A report exists. **This is the evidence for the employer and TICO conversations.**

### Stage 3: Landing page and demand test (Gate C, in parallel)

- [x] Brand name chosen: **Far Enough** (2026-11-26); plans in docs/brand/ and docs/content/. Domain and handles to register (owner, TODO.md).
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
- [ ] More origins (Montreal, Vancouver), flexible dates, price alerts.
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
