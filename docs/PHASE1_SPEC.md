# Budget Trip Finder: Phase 1 Build Spec

> **Provenance.** Rebuilt on 2026-11-21 from the shared claude.ai chat. The share only exposed the spec's
> first version (sections 1-13). The later edits (v2 research, v3 monetization, risk register) are rebuilt
> here from the chat's summaries and marked **[v2]** or **[v3]**. Exact wording, the ten-item open-decision
> list and some source links from v2/v3 were not available. If you still have the final `PHASE1_SPEC.md`,
> drop it in `docs/` and it replaces this file.

Handover document for a coding agent. Working title only; rename freely.

**Status 2026-11-25:** a working proof of concept exists (`backend/`, live test site at https://bahafin.github.io/budget-trip-finder/). What it proved: [poc-report.md](poc-report.md), [validation-2026-11-24.md](validation-2026-11-24.md). API and partner research: [api-coverage-check.md](api-coverage-check.md), [affiliate-programs-check.md](affiliate-programs-check.md). The build order lives in [../PLAN.md](../PLAN.md). Sections below marked **[2026-11-2x]** reflect those findings.
Spec date: 2026-11-20. Provider terms and APIs change. Check each provider's current docs before coding against it.

## 1. Product summary

The user enters a total trip budget. The system recommends destinations where a complete trip package fits that budget: flights, lodging, daily costs and optional activities. It shows entry requirements when the user gives a nationality, and sends the user to partner sites through affiliate links to book.

**Phase 1 is referral-only.** The product does not take bookings, payments, or traveller documents. All "book" actions are outbound affiliate links.

### Inputs
| Field | Required | Notes |
|---|---|---|
| Total budget + currency | Yes | Whole-trip budget for the whole group |
| Origin airport/city | Yes | Single origin for entire group |
| Travellers | Yes | Adults (and children if supported). Group = same origin and same destination for everyone |
| Nationality | **No [v2]** | Opt-in convenience. Without it, search and pricing work normally. With it, results show entry badges and an optional "hide visa-required" toggle. Session-only by default: not stored, not logged |
| Dates | No | Exact range, flexible window ("any time in March"), month, or none |
| Trip length (nights) | No | Default 5-7 if absent |
| Region filter | No | Country / continent / "anywhere" |

### Outputs
Ranked list of destination packages. Each shows:
- Total estimated package cost (low / expected / high) vs budget, with per-person split
- Cost breakdown: flights, lodging, daily spend (activities appear on the destination detail view, see 4)
- **Confidence label per component:** `live`, `cached (age)`, or `estimated`
- Entry requirement summary (only if nationality given), with "verify with official sources" disclaimer
- **[2026-11-23] Know before you go:** for each destination, short flags for things travellers get caught out by: drones, medication, cash declaration limits, banned or restricted imports, and notable local laws. Example: a drone taken to Colombia was confiscated (travel.gc.ca says drones may only enter Colombia through Bogota's El Dorado airport); Morocco confiscates drones on entry. Shown as an icon on the result card and a section on the destination page, each item linking to the official source. See 4 and 12
- Affiliate deep links to partner sites (flights, lodging, activities)

## 2. Non-goals for Phase 1
- No booking, checkout, payment, or ticketing
- No use of any selling/booking API (e.g., Duffel booking flow). Reserve for Phase 2
- No per-traveller different origins/destinations
- No scraping of sites whose terms prohibit automated access (see section 8). No generic crawler
- No user accounts required (optional: saved searches and price alerts later)
- **[v2]** Do not use Amadeus Self-Service APIs. They were decommissioned on 2026-07-17

## 3. Core concept: package cost model

```
package_total = flights_total + lodging_total + daily_total + activities_total

flights_total    = per_person_roundtrip_fare * travellers
lodging_total    = nightly_rate(room_config) * nights * rooms
daily_total      = per_person_daily_cost * travellers * days   # food, local transport, incidentals
activities_total = optional, user-selectable, default 0 or a small allowance
```

- Always compute and display a **range** (low/expected/high), not a single number. Low and high come from price-band percentiles or provider price spread.
- Rank by fit within budget, then by user-selected preference (cheapest, best value, most days).
- Room allocation: simple rule for Phase 1 (e.g., 2 adults per room, round up). Keep as a pure function with unit tests.
- Currency: store source currency, convert at display using a daily FX table. Never mix currencies in arithmetic.

### Two-stage pipeline (important for cost and speed)
1. **Discovery (cheap, cached):** score every candidate destination using cached flight prices, stored lodging bands and daily-cost data. No live calls.
2. **Verification (limited, live where available):** for the top N (default 10) results only, refresh what can be refreshed (flight link validation, live activity lookups on open) and downgrade confidence labels honestly when something can't be refreshed.

## 4. Data sources

Read each provider's current documentation first. Do not assume field names from this document.

**[2026-11-25]** Full check of the Travelpayouts and LiteAPI docs: [api-coverage-check.md](api-coverage-check.md). Key points: outbound links must be made with the Travelpayouts partner links API; the live Aviasales and Kiwi search APIs need 50,000+ monthly users (not available); LiteAPI's city price index supplies daily hotel seasonality.

| Component | Source | Access | Key constraints |
|---|---|---|---|
| Flights (discovery) | Travelpayouts Aviasales Data API | Free after Travelpayouts signup + Aviasales program | Prices come from users' recent searches, cached up to ~7 days. Not live. Always show cache age and link out to confirm. **[v2]** The cache is per market: a route only has data if users in that market searched it. The default market is Russian, so set the market explicitly and test Canada/US coverage in M0. **[2026-11-25]** CA market confirmed (148 destinations from Toronto). Coverage per destination can be thin (1-3 fares a month), so add `v3/grouped_prices` with trip-length windows. Estimate rule after validation: cheapest cached fare for the trip's own dates x 1.10 (low x 0.95, high x 1.35). The live Aviasales and Kiwi search APIs need 50,000+ monthly users, so they are out. Live price check for top results later: LiteAPI flights (production activation) |
| Lodging **[2026-11-25]** | **LiteAPI (Nuitee) hotel rates**, sampled by a weekly job into bands per destination, month and comfort tier (25th percentile / median / 75th percentile nightly price per room) | Free sandbox now; production key = card on file (owner action) | Hotellook is gone and Travelpayouts has no hotel price API (confirmed in its FAQ). One search per destination per month, mid-month check-in, 3 nights, 2 adults; `data/seed/hotel_areas.csv` fixes resort destinations whose hotels sit away from the city point. Spot check: medians within -12% to +8% of Booking.com. To add: fees LiteAPI marks as paid at the hotel, and seasonality from LiteAPI's **city price index** (`GET /v3.0/prices/city`, daily average a year ahead, US$0.02-0.05 per call, beta) to scale bands for the trip's actual dates. Fallback when no sample exists: Canadian average x price level, labelled `estimated`. Search-only use within LiteAPI's terms still to confirm |
| Activities **[v2; 2026-11-25]** | Viator Partner API, Basic Access (join Viator **directly**: no traffic minimum, 8%, 30-day cookie). Klook and KKday through Travelpayouts for Asian destinations | Instant self-service, no cost | Search endpoints are for real-time, user-initiated searches only, and Basic Access can't use bulk ingestion. **No pre-loading:** activities appear only when a user opens a destination, never in ranking. Basic tier sends users to viator.com to book. Viator "unique content" (e.g. reviews) must not be indexable |
| Daily costs **[v2; 2026-11-25]** | Canadian baseline per comfort tier (CAD 80 / 140 / 240 per adult per day; children 70%) scaled by the World Bank price level. The old price-level indicator is archived, so it is derived as PPP conversion factor (`PA.NUS.PRVT.PP`) / market FX rate (`PA.NUS.FCRF`). CC BY 4.0, attribute it. **Unvalidated and about 40% of a typical total**: Gate A must check it | Free | Numbeo's commercial API is a later upgrade (third-party report: roughly $260-1,250/month, unverified). Free Numbeo use is non-commercial only, so don't use it |
| Visa / entry **[v2]** | MIT-licensed community passport/visa dataset | Free | **Stopgap.** It was scraped from passportindex.org, so rights to the underlying data are unclear for commercial use. Replace with licensed data (e.g. Sherpa) before scaling. Always show disclaimer; never present as authoritative |
| Travel advisories **[2026-11-24]** | Global Affairs Canada JSON feed (advisory level, text, link) | Free | Used to drop countries at level 2+ (avoid non-essential or all travel) from destination selection, and to show the advisory on each result |
| Affiliate links **[2026-11-25]** | Travelpayouts partner links API (`POST /links/v1/create`) for Travelpayouts brands; each direct program's own link builder otherwise | Token + marker 809658 + project ID (`trs`) 605382 | 100 requests/min, 10 links each. Short links seen so far redirect as: Aviasales `aviasales.com/?marker=809658.<click>`, Klook `affiliate.klook.com/redirect?aid=api|13694|<click>-809658|pid|809658&k_site=<url>`, KKday `invl.me/clndj1c?aff_sub=<click>-809658&url=<url>`. Prefer the API so clicks are tracked and tagged with `sub_id` |
| Know before you go **[2026-11-23]** | Hand-written notes per launch destination, in our own words, each linking to the travel.gc.ca country page; advisory level from the Global Affairs Canada JSON feed (`data.international.gc.ca/travel-voyage/index-alpha-eng.json`) | Free | travel.gc.ca text may be reproduced non-commercially only; commercial reproduction needs written permission from Global Affairs. So: write our own short summaries, link to the source, don't copy text. Review a destination's notes when the feed's `date-published` changes for that country. For drones, also link the destination's civil aviation authority where one can be found |
| FX | Any reputable FX API | Free tier ok | Daily refresh |

### Lodging: bands
**[2026-11-25]** Implemented as `lodging_bands(destination, month, tier, nightly_low, nightly_mid, nightly_high, currency, sample_size, source, as_of)`, filled from LiteAPI samples. The original curated design follows and remains the fallback.

A table `lodging_price_band(destination_id, tier, season, nightly_low, nightly_mid, nightly_high, source, as_of)` for the 20-30 launch destinations, seeded by hand from public reference points and refreshed each quarter. Add a `season` column (high/shoulder/low): with no live data, seasonality is the biggest error source. Label as `estimated`. The lodging component sits behind an interface, so a hotel data feed can replace it when one is granted.

## 5. Architecture

Suggested stack (change if there is a good reason):
- **Backend:** Python 3.12, FastAPI
- **DB:** PostgreSQL (SQLAlchemy + Alembic migrations)
- **Data refresh [v2]:** start with plain Python jobs on cron / GitHub Actions schedules (free). Move to Prefect when retries and observability are needed: Prefect Cloud Hobby (2 users, 1 workspace, 5 deployments, 7 days of history, ~500 serverless minutes/month, no custom work pools) fits one deployment per source. Or self-host open-source Prefect on a free VM (Oracle's free Arm tier is now 2 OCPU / 12 GB, idle instances may be reclaimed; Google's e2-micro at 1 GB RAM is too tight for Prefect + Postgres). Write jobs as plain functions so they run under either
- **Cache:** Postgres tables with `fetched_at` + `expires_at`; add Redis only if needed
- **Frontend:** Next.js/React (mobile-first)
- **LLM layer:** provider-agnostic interface (see section 7)
- **Secrets:** environment variables only. Never commit keys
- **[2026-11-24] Proof of concept as built:** SQLite instead of Postgres, a CLI and FastAPI page, and a static GitHub Pages test site that runs a JavaScript port of the engine against an exported data snapshot (a parity test keeps the two engines identical). Postgres and the full API come when Gate A passes

### Modules
```
app/
  api/            # FastAPI routes
  domain/         # pure logic: cost model, ranking, room allocation (heavily unit-tested)
  providers/      # one adapter per data source behind a common interface
    flights/      # AviasalesDataProvider
    lodging/      # LiteApiSampleProvider (bands), PriceIndexProvider (seasonality), CuratedBandProvider (fallback)
    activities/   # ViatorProvider (live, on destination open only)
    daily_costs/  # CuratedDailyCostProvider (World Bank PLI scaling); NumbeoProvider later
    visa/         # VisaDatasetProvider
    fx/
  llm/            # intent parsing + explanation (no price generation)
  jobs/           # scheduled refresh jobs (cron now, Prefect-ready)
  links/          # affiliate deep link builders (single place, config-driven)
```

Provider interface rule: every provider returns normalized records containing `value`, `currency`, `fetched_at`, `source`, `confidence`. The domain layer never knows which vendor produced a number.

### Data model (minimum)
- `destination` (id, name, country, iata_codes[], region, tags[])
- `flight_price_cache` (origin, destination, market, depart_date or month, return_date, price, currency, fetched_at, expires_at, source_link)
- `lodging_price_band` (see above; filled from LiteAPI samples with source = liteapi)
- `daily_cost` (destination_id, tier, per_person_per_day, currency, source, as_of)
- `entry_requirement` (nationality, destination_country, status, notes, source, as_of)
- `search_session` (inputs **without nationality**, results snapshot, created_at) for debugging and analytics
- `click_event` (session_id, component, partner, ts) for affiliate performance analysis
- No `activity_cache` table **[v2]**: Viator Basic forbids bulk ingestion; cache per-request responses only as the terms allow

## 6. API (backend)

- `POST /v1/search`: body = inputs from section 1; returns ranked packages with breakdowns and confidence labels
- `GET /v1/destinations/{id}/package`: detailed breakdown for one destination with the same inputs; triggers live activity lookup
- `GET /v1/entry-requirements?nationality=..&country=..` (do not log the nationality parameter)
- `GET /v1/out/{component}/{token}`: redirect endpoint that logs the click then redirects to the affiliate URL

Flexible dates: when dates are a window or month, search across the window using cached calendar data. Return the cheapest feasible departure and the price spread across the window. Cache aggressively and precompute popular origins nightly.

## 7. Gen AI usage

Allowed:
- Parse free-text trip requests into the structured inputs above
- Rank/explain trade-offs and write short "why this fits" blurbs from structured data
- Suggest destination candidates to feed the deterministic pipeline

Not allowed:
- **The LLM must never produce or adjust prices.** All numbers come from provider data or the curated tables.
- Any LLM output that includes numbers must be validated against pipeline output or discarded.

Implementation notes:
- Provider-agnostic `LLMClient` interface; configure model via env var. Candidates to benchmark on real tasks: a hosted frontier model and an open-weight model such as NVIDIA Nemotron (Nemotron 3 Super's licence permits commercial use but requires keeping safety guardrails; check the specific model's licence). Build a small eval set (20-30 sample queries with expected parsed outputs) before choosing.
- Use structured (JSON-schema) outputs; validate with Pydantic.
- Log prompts/responses without personal data.
- AI is the interface, not the moat. Compete on data quality and focus **[v3]**.

## 8. Compliance and guardrails (agent must follow)

1. **No scraping of sites that prohibit it.** Booking.com's terms prohibit automated access without written permission, and its affiliate agreement bars programmatic extraction. Use APIs or licensed feeds only.
2. **Respect provider caching rules** (Viator real-time only, Aviasales cache age display). Encode TTLs in config.
3. **Referral-only language.** UI copy must say prices are estimates and bookings are completed on the partner's site. No "book now" wording that implies the product is the seller. No payment collection.
4. **Entry requirements:** always show a "verify with official government sources" disclaimer.
5. **Affiliate disclosure** on every results page.
6. **Privacy:** collect minimal data. Nationality is opt-in, session-only by default, never logged with identifiers. Publish a privacy policy. PIPEDA applies as a baseline; confirm with counsel.
7. Do not embed any partner's unique/protected content in indexable page source (see Viator note).
8. **Link choice [v3]:** pick outbound partner by user value (price, availability, region). Commission is a tie-breaker only.
9. **Attribution:** World Bank data is CC BY 4.0; credit it on a sources/about page.

## 9. Milestones

Current build order: see [../PLAN.md](../PLAN.md). Original milestones:

0. **[v2] Data verification:** confirm Aviasales coverage for the launch origins in the CA market, Hotellook data units/currency/coverage for the launch destinations, Viator Basic access. Output: a coverage report. Feeds Gate A
1. **Skeleton:** repo, CI, DB schema, provider interfaces with fakes, domain cost model + unit tests
2. **Data ingestion:** jobs for flights cache, lodging data, daily costs, FX; curated lodging bands and entry-requirement dataset loaded for 20-30 destinations and one origin region
3. **Search API:** two-stage pipeline, flexible dates, confidence labels, ranking
4. **Frontend:** input form (conditional group/dates/region/nationality fields), results list, breakdown view, live activities on open, outbound links with click logging
5. **LLM layer:** intent parsing + explanations behind the interface, with eval set
6. **Hardening:** rate limiting, caching review, monitoring, disclaimers/legal copy, load test

## 10. Acceptance criteria

- Given budget, origin, travellers, and optional filters, `/v1/search` returns >= 5 packages within budget for a typical request, or a clear "nothing fits, closest options" response
- Every price displays a confidence label and age where cached
- Package totals reconcile exactly with component sums (tested)
- When nationality is given and "hide visa-required" is on, entry-blocked destinations are hidden; with no nationality, nothing is filtered
- Nationality never appears in logs, `search_session` or analytics
- Flexible-date search over a one-month window returns in < 3 s from cache
- Provider outage degrades gracefully (stale cache shown with warning; failing component marked `estimated` or hidden)
- All secrets via env; no secrets in repo; provider adapters covered by contract tests using recorded fixtures

## 11. Metrics to log from day one
Searches, result impressions, click-throughs per component and partner, earnings per click **[v3]**, budget distribution, top destinations, empty-result rate, price-confidence mix. These decide whether Phase 2 is worth pursuing.

## 12. Open decisions for the product owner (agent: do not guess, stub and flag)

The v3 spec listed ten; these are the ones recoverable from the chat.

1. **Wedge [v3]: decided 2026-11-21, Canadian departures.** Prices in CAD, flight data queried in the CA market, entry rules for Canadian passports first (other nationalities stay optional). Rejected: a "trips under $X" tier, visa-light destinations ranked by total cost.
2. **Launch scope:** which origin region and which 20-30 destinations (follows from the wedge).
3. **Legal status of referral-only operation in Ontario.** TICO Act s.4 bars acting as a travel agent unless registered; no affiliate/referral exemption was found. Get TICO's answer in writing before public launch (Gate B). Until then, keep copy strictly referral-only.
4. **Lodging source:** settled by M0 on 2026-11-22: curated bands at launch. Open: whether Travelpayouts grants a hotel Data API on request. **2026-11-23:** LiteAPI sandbox works and could refresh the bands automatically (see 4); Duffel Stays needs sales approval and its agreement bans metasearch use.
5. **Visa data source** and licence (replace the stopgap before scaling).
6. **Numbeo** commercial plan: later, if at all.
7. **Brand name, domain**, and **which affiliate accounts to open first**. **[2026-11-25]** Joined: Aviasales, Klook, KKday (Travelpayouts). Booking.com and the other big hotel programs in Travelpayouts need more traffic. Next: Expedia Group Travel Creator Program (direct, open to anyone), Viator (direct), Kayak, Hostelworld. See [affiliate-programs-check.md](affiliate-programs-check.md).
8. **Data-refresh hosting:** cron/GitHub Actions vs Prefect Cloud Hobby vs self-hosted.
9. **Gate C thresholds** for the landing-page test, set before it starts.
10. **Employer outside-business-activity policy:** check disclosure requirements.
11. **Know before you go [2026-11-23]:** ask Global Affairs Canada for written permission to quote travel.gc.ca text, or keep to our own summaries plus links (default).

## 13. Phase 2 hooks (do not build now)
Keep these seams clean: provider interfaces that could later add booking methods; an `Order` concept absent from Phase 1 but easy to add; user approval step design. Phase 2 means selling travel, which needs regulatory registration (TICO: general account plus a separate trust account) and booking-level supplier approvals (Booking.com booking rights, Viator booking tier certification). User approval does not change who the seller is. **[2026-11-23]** Candidate Phase 2 backend: LiteAPI (Nuitee). One account covers hotels, flights and experiences (experiences need enabling by Nuitee support), and its MCP server (`https://mcp.liteapi.travel/api/mcp`, 133 tools) lets an agent search, hold and book. See docs/m0-coverage-report.md.

## 14. Monetization and affiliate programs [v3]

Commission figures come mostly from affiliate-network blogs and directories. Treat them as planning ranges and confirm in each dashboard after approval.

| Category | Programs | Reported rate | Price data? | Notes |
|---|---|---|---|---|
| Flights | Travelpayouts flight programmes | ~1-6% | Yes (Aviasales cache) | Thin revenue; the reason to sell packages |
| Flights | Flight Network (Canadian OTA, Awin) | CAD 13 per sale | No | |
| Flights | Airlines (Qatar, KLM, Emirates) | ~1-2.5% | No | Air Canada, WestJet, Porter, Flair: only third-party listings found; check directly |
| Flights | Skyscanner | Revenue share | Travel API for established high-traffic partners only | Later |
| Hotels | Marriott, Hilton, IHG, Hyatt (mostly Impact); Accor (CJ, Kwanko) | ~3-6% of completed-stay room revenue | No (deep links, catalogs) | Short cookies (~7-30 days). Marriott pays only on completed stays, so cancellations earn nothing and payouts lag. Use as optional "book direct" links; OTA links are the default |
| Hotels | Booking.com Demand API | n/a | Yes, with contract | Managed Affiliate Partner contract required. Phase 1.5 goal |
| Activities | Viator (strongest in North America), GetYourGuide (Europe, LatAm), Klook (Asia) | ~8-10% | Viator live search | Route by destination region |
| Add-ons | Discover Cars, travel insurance | varies | No | Check the regulatory position on insurance before promoting it |

**Travelpayouts catalog, read 2026-11-22 (owner's account):**

| Program | Category | Rate | Cookie |
|---|---|---|---|
| Aviasales | Flights | 1.1–1.3%, paid 30 days after confirmation | 30 days |
| Booking.com | Hotels | 3–5% (€1.5 per flight) | One session |
| Expedia | Hotels, packages | Hotels and activities 3.6%, vacation packages 1.8%, cars 1.35%, flights nothing; paid within 60 days after the stay | 7 days |
| Hotels.com | Hotels | 1.35–3.6% | 7 days |
| Trip.com | Hotels, flights | 1–5.5% | 7–30 days |
| Agoda | Hotels | 1–6% | 1 day |
| Vio.com | Hotels | 40–64% revenue share | 30 days |
| Viator | Activities | 8% | 30 days |
| GetYourGuide | Activities | 8% | 31 days |
| DiscoverCars | Cars | 23–54% (of their revenue) | 365 days |

Package Tours category: Expedia, KKday (Asia), Rakuten Travel (JP). Only Expedia fits Canadian departures, and its package rate (1.8%) is half its hotel rate, so link hotels and flights separately by default. Aviasales and Expedia both ban paid-search ads using their brand name.

Illustrative only: a fully booked 2-person, 5-night trip of about $2,400 earns roughly $75-130, mostly from hotels and activities.

Rules: start with Travelpayouts and Viator; apply to chain and airline programs once the MVP site is live (approvals often need a working site). Disclose affiliate relationships. Log clicks per partner.

**[2026-11-25] Availability as of today** (full table: [affiliate-programs-check.md](affiliate-programs-check.md)):
- Joined: Aviasales, Klook (5% on all categories including hotels), KKday (3% accommodation, 5% tours and transport).
- Open, apply now: Expedia Group Travel Creator Program (direct; covers Expedia, Hotels.com, Vrbo), Viator (direct, 8%), Kayak (direct, deep links to searches and hotel pages), Hostelworld (Partnerize).
- Gated: Booking.com (now via CJ, needs an active website; session cookie), Skyscanner (5,000+ unique visitors a month), Expedia/Booking/Agoda/Trip.com inside Travelpayouts (traffic). Tripadvisor, Agoda, Trip.com and GetYourGuide direct terms are unconfirmed.
- Default hotel link: Expedia (once approved), with Klook second. Booking.com when approved.

## 15. Risks and go/no-go gates [v3]

Verdict: viable only as a narrow, trust-first product. As a generic "find me a trip" tool it likely loses to Google.

| Failure point | Cover |
|---|---|
| Google Flight Deals / AI Mode and AI assistants do "cheap flexible trips" from natural language | Pick one narrow wedge. Build owned channels (email, price alerts) since AI answers eat search traffic |
| Price trust: flight cache is other users' searches; hotel and daily costs are estimates | Ranges, confidence labels, Gate A accuracy test before building UI |
| Thin economics, completed-stay-only commissions, short cookies | Attach activities, cars, insurance; track earnings per click from day one; fixed costs near zero |
| Partner gatekeeping (Booking.com, Skyscanner) | Fallback sources; apply early once a landing page is live. **[2026-11-25]** This hit: Booking.com and the big Travelpayouts hotel programs need traffic. Cover: Expedia's direct program and Klook |
| Legal: TICO open; wrong visa info is a liability | Gate B; nationality opt-in and session-only; replace scraped visa data before scaling |
| Leakage: users compare here, book elsewhere later | Price alerts, saved shortlists, partners with longer cookies |
| Unproven demand | Landing page with 20-30 destinations before the full build (Gate C) |
| Owner's time | Strict Phase 1 scope; Phase 2 gated on traction |

Gates:
- **A:** 50-package accuracy test. Proceed only if median error is within ~20-25%.
- **B:** TICO's answer obtained before public launch.
- **C:** 4-6 week landing-page test against thresholds set in advance.
- **D:** 2-3 month revenue-per-1,000-visitors check before paid traffic or Phase 2.
