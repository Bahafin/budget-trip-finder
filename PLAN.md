# Budget Trip Finder: Implementation Plan

Plan date: 2026-11-21. The spec is [docs/PHASE1_SPEC.md](docs/PHASE1_SPEC.md); this file says what gets built, in what order, and what has to be true before each step.

**Approach:** the work is ordered around the spec's go/no-go gates, so nothing expensive gets built before the data is proven. The pricing engine and the accuracy test (Gate A) come before any real UI. A landing page (Gate C) runs alongside them to test demand. Search UI, LLM and hardening come only after Gate A passes.

## Defaults used where the owner hasn't decided yet

Each of these is a default the plan uses until the owner answers; all are listed in spec section 12.

| Decision | Default in this plan | Why |
|---|---|---|
| Wedge | **Decided 2026-11-21:** Canadian departures: CAD prices, CA flight-data market, Canadian-passport entry rules first | Owner is in Ontario; it fixes currency, market and visa scope in one move |
| Origin region | Toronto (YYZ, YTZ), with YUL and YVR added in M2 if coverage holds | One origin region keeps Gate A tractable |
| Launch destinations | 25, picked in M0 by flight-data coverage from YYZ | Destinations with no cached flights can't be priced |
| Lodging | **Curated bands with seasons**, refreshed by a scheduled LiteAPI job if its terms allow (Hotellook is gone; see docs/m0-coverage-report.md) | Bands keep user searches free of live hotel calls; LiteAPI makes them less manual |
| Data refresh | GitHub Actions schedules | Free, zero setup; jobs stay Prefect-ready |
| Affiliate accounts | Travelpayouts (Aviasales + Hotellook), Viator Basic | Self-serve, free |
| LLM | Deferred to M5 | Not needed to pass any gate |

## Owner actions (not code)

These are on the owner, and some take weeks, so they start now.

| Action | Needed by | Blocks |
|---|---|---|
| ~~Open Travelpayouts account, get API token~~ Done 2026-11-22; token in `.env`. Project "Bahafin" under review | — | — |
| Join Aviasales, Booking.com, Expedia, Viator once the Project is approved | M3 | Outbound links |
| Ask Travelpayouts support which hotel programs offer the Data API "on request" | Now | Live hotel prices |
| Contact Duffel sales: (1) enable Stays, (2) confirm in writing that showing prices with no booking through Duffel is allowed under Services Agreement 2.5(d) "metasearch", (3) CAD balance currency, (4) eligibility for a Canadian sole proprietor | Now | Live hotel prices via Duffel; Phase 2 booking backend |
| Read LiteAPI Terms of Service (search-only use, showing derived ranges); request Experiences access only if Phase 2 gets close | Before the M1 adapter | LiteAPI band refresh |
| Write know-before-you-go notes for the 25 launch destinations (drones, medication, cash limits, imports) from travel.gc.ca | With lodging bands | Destination page |
| Open Viator Partner (Basic Access) account | M4 | Activities |
| Pick brand name and register domain | M1 | Landing page (Gate C) |
| Contact TICO in writing about referral-only operation | Before public launch | Gate B |
| Set Gate C thresholds (signups, click-through) | Before landing page goes live | Gate C |
| Check employer outside-business-activity policy | Before public launch | Launch |

## Phases

```
M0 Data check ──► M1 Skeleton + engine ──► Gate A (accuracy) ──► M3 Search API ──► M4 Web app ──► M5 LLM ──► M6 Hardening ──► Gate B ──► Launch ──► Gate D
                         │
                         └──► Landing page (Gate C, runs 4-6 weeks in parallel)
```

### M0: Data verification (spike, throwaway scripts)

Goal: prove the free data sources can price trips from Toronto before writing the real app.

- [x] Aviasales Data API from Toronto, CA market, CAD: 148 destinations over 5 months, cache median 3 days old (see docs/m0-coverage-report.md).
- [x] US market comparison: almost identical.
- [x] Hotellook data API: gone (404). Lodging moves to curated bands.
- [ ] Load the visa dataset and check Canadian-passport rows for the candidates.
- [ ] Pull the World Bank price level index for candidate countries.
- [ ] Write `docs/m0-coverage-report.md`: per destination, which components have data. Pick the 25 launch destinations from it.

Done when: the report exists and names 25 destinations where flights and lodging both have data (or a curated band is planned).

### M1: Skeleton and pricing engine

- [ ] Monorepo layout:
  ```
  backend/    FastAPI app (structure from spec 5), pyproject, Alembic
  web/        Next.js app (empty until M4, landing page lives here first)
  data/seed/  destinations.csv, lodging_bands.csv, daily_costs.csv (curated, versioned)
  scripts/    M0 spike scripts, Gate A harness
  docs/
  ```
- [ ] Toolchain: `uv` with Python 3.12 pinned (the machine has 3.15; libraries lag new Python releases), ruff, pytest, mypy. Node 22 LTS for `web/`.
- [ ] Database: Postgres. No Docker or local Postgres on this machine, so use a free hosted Postgres for dev, or install Postgres locally. Tests use a throwaway schema.
- [ ] Domain layer, pure and fully unit-tested: cost model with low/expected/high ranges, room allocation, currency handling (`Money` type that refuses mixed-currency arithmetic), ranking.
- [ ] Provider interfaces + fakes for flights, lodging, daily costs, visa, FX. Normalized record: `value, currency, fetched_at, source, confidence`.
- [ ] Real adapters for Aviasales and LiteAPI hotel rates (band refresh job), with contract tests on recorded fixtures.
- [ ] `know_before_you_go` seed table (destination, category: drone/medication/cash/imports/laws, summary in our words, source URL, reviewed_at), plus a job that flags rows when the Global Affairs feed's `date-published` changes.
- [ ] Refresh jobs as plain functions + a CLI entry point; GitHub Actions schedule calls them.
- [ ] CI: lint, type check, tests on every push.

Done when: `python -m app.jobs refresh-all` fills the DB for the 25 destinations, and a CLI command prints ranked packages for a budget.

### Gate A: Accuracy test

- [ ] Harness in `scripts/gate_a/`: generate 50 packages (mix of destinations, 1-4 travellers, 3-10 nights, dates 1-4 months out).
- [ ] For each, record the engine's expected total, then the real total found by hand on partner sites (flight + hotel of the same tier). This is manual work, about a day; the owner or a helper does it.
- [ ] Report median and 90th-percentile error per component.

Pass: median total error within ~20-25%. Fail: fix the weakest component (usually lodging or daily costs) and re-run before building further.

### Landing page (parallel with M1 and Gate A)

- [ ] One page in `web/`: the pitch, 3-5 example packages generated by the engine (static, labelled estimates), email signup, affiliate disclosure.
- [ ] Analytics: visits, signups, example-package clicks.
- [ ] Host on a free static tier. Run 4-6 weeks against the Gate C thresholds.

### M3: Search API (after Gate A passes)

- [ ] `POST /v1/search`, `GET /v1/destinations/{id}/package`, `GET /v1/entry-requirements`, `GET /v1/out/...` as in spec 6.
- [ ] Two-stage pipeline: discovery from cache, verification of top 10.
- [ ] Flexible dates (window, month, none) from cached calendars; under 3 s for a one-month window.
- [ ] Graceful degradation on provider outage.
- [ ] Nationality never persisted or logged (test asserts it).

### M4: Web app

- [ ] Input form with conditional fields (group, dates, region, optional nationality).
- [ ] Results list with ranges, confidence labels, cache age, per-person split.
- [ ] Destination detail: breakdown, live Viator activities, outbound links through `/v1/out`.
- [ ] Referral-only copy, affiliate disclosure, visa disclaimer, privacy policy page, World Bank attribution.
- [ ] Mobile-first.

### M5: LLM layer

- [ ] Eval set of 25 free-text queries with expected parsed inputs.
- [ ] `LLMClient` interface; benchmark a hosted model and an open-weight one (e.g. Nemotron) on the eval set; pick by accuracy and cost.
- [ ] Intent parsing + "why this fits" blurbs. Numbers in output are validated against pipeline output or dropped.

### M6: Hardening

- [ ] Rate limiting, cache TTL review, error monitoring, load test, legal copy review.

### Launch and after

- Gate B (TICO answer in writing) before going public.
- Gate D: after 2-3 months, revenue per 1,000 visitors decides paid traffic and Phase 2.
- Apply to hotel-chain, airline and GetYourGuide programs once the site is live.

## Running cost target

Near zero until Gate D: free tiers for hosting, Postgres, CI and data sources. Paid items only when a gate justifies them (licensed visa data, Numbeo, paid LLM usage beyond testing).

## First tasks for the coding agent

1. `git init`, add `.gitignore` and `.env.example` (no real keys).
2. Write the M0 scripts against the Travelpayouts token once the owner provides it in `.env`.
3. In parallel, build the domain cost model and its tests (no external dependency).
