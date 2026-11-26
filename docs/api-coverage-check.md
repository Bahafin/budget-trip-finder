# API coverage check: Travelpayouts and LiteAPI

Checked 2026-11-25. Sources: all 38 articles in the Travelpayouts help centre's "API and data" category (support.travelpayouts.com/hc/en-us/categories/200358578), and the LiteAPI (Nuitee Connect) overview, access, pricing and rate-limit pages (docs.nuitee.com).

**Short answer:** we use the right Travelpayouts API (the flight Data API), but our docs miss four things that matter:
1. Affiliate links must go through the **partner links API**. We currently append `marker=` by hand, which isn't the documented method and isn't verified to track.
2. A better Data API endpoint for our case (`grouped_prices`, with trip-length filters).
3. The **statistics API**, which we need to measure revenue for Gate D.
4. LiteAPI's **city price index**, which fixes holiday and seasonal hotel pricing for a few dollars a month.

## Travelpayouts: what exists and what it means for us

| API / data | Access | Use for us | In our docs before? |
|---|---|---|---|
| **Aviasales Data API** (cached prices, 2-7 days old) | Token only, no approval | Our flight source. Recommended: cache 24 h, request gzip | Partly: only `prices_for_dates` |
| `v3/prices_for_dates` | 600 req/min | What we use now. Cheapest fares "found in the last 48 hours" | Yes |
| `v3/grouped_prices` with `min_trip_duration` / `max_trip_duration` | 600 req/min | **Cheapest fare per departure day for a trip-length window.** Fixes thin coverage (some destinations have 1-3 fares a month). Could replace or extend our per-destination calls | No |
| `v2/prices/week-matrix` | 60 req/min | Prices +/- 3 days around given dates: a cheap freshness check for top results | No |
| `v3/search_by_price_range` | 600 req/min | Fares between a min and max price from an origin: budget-first discovery ("where can I fly for under $400") | No |
| `v3/get_latest_prices`, `v2/prices/month-matrix`, `v3/get_special_offers`, `v3/get_popular_directions` | 60-600 req/min | Price trends, deal badges, "popular from Toronto" lists. Nice to have | No |
| GraphQL (`/graphql/v1/`) | 60 req/min | Same data, fewer requests | No |
| **Aviasales Flight Search API (live)** | **Only for projects with 50,000+ monthly active users.** Strict rules: user-initiated searches, 9% search-to-click and 5% click-to-purchase conversion, no scraping | Not available to us. Revisit after launch if traffic gets there | No |
| **Kiwi.com API** | Also 50,000+ monthly users | Not available | No |
| **Partner links API** (`POST /links/v1/create`) | Token + project ID (`trs`) + joined brand programs. 100 req/min, 10 links per request | **Converts Aviasales, Booking.com and other brand URLs into tracked affiliate links.** Needed for every outbound link | No |
| **Statistics API** (`/statistics/v1/execute_query`) | Token, 30 req/min | Bookings, clicks and earnings per program: automates Gate D (revenue per 1,000 visitors) | No |
| Balance and payments API | Token | Earnings and payout history | No |
| Data files (`/data/en/countries.json`, `cities.json`, `airports.json`, `airlines.json`) | Free | Cities already used. Airlines would let us show "Air Canada" instead of "AC" | Partly |
| Autocomplete (`autocomplete.travelpayouts.com/places2`) | Free | City/airport search box when we add origins beyond Toronto | No |
| `whereami` (IP to nearest city) | Free | Pre-fill the origin later; check `accuracy` before trusting it | No |
| Airline logos (`img.wway.io`) | Free | Result cards | No |
| Viator deals feed | Ask support | Discounted tours for the activities section; links still need converting | No |
| Omio feed (trains, buses), Airalo (eSIM), Tiqets, WeGoTrip | No approval | Later add-ons (eSIM is a natural upsell) | No |
| intui.travel, GetTransfer (airport transfers) | intui: no approval; GetTransfer: approval | A possible "airport transfer" cost line later | No |
| Hotel API | **None.** "Aviasales doesn't provide Hotels API" (FAQ) | Confirms hotels come from LiteAPI or curated ranges | Yes (Hotellook gone) |

Rate limits are per minute. Going over returns HTTP 429 and blocks for the rest of the minute; `X-Rate-Limit-Remaining` shows what's left.

## LiteAPI: what going live involves

| Product | Sandbox | Production |
|---|---|---|
| Hotels | On; "production-like" data | **Attach a credit card to get a `prod_` key.** That's all |
| Flights | On, but data "does not mirror production" and is of limited accuracy; docs say not to use it to validate prices | Self-serve activation in the dashboard (**Flights → Introduction**) once the account is in production mode. May ask for use case and expected traffic |
| Experiences | **Off until requested**, even in sandbox. Overview still says "coming soon" | Request and approval |
| City price index (`GET /v3.0/prices/city`) | Works | Beta. Average nightly price per day for up to 1,000 hotels in a city, a year ahead, in USD. $0.02 per request on its own page ($0.05 on the pricing page). 10 requests a minute |

- Rate limits: sandbox 5 requests/second, production 250/second, per key.
- Hotel search is free within 5,000 searches per booking; excess "may be billed" (no rate published).
- Flight search: EUR 0.005 per search beyond 1,500 per booking.
- Ticketing: 1% fee (EUR 2-10) per booking.

**Price index test (sandbox, Cancún):** 364 daily values. December averages US$294 a night, but it climbs from US$245 on Dec 15 to US$549 on Dec 30. That's the holiday spike our mid-month hotel samples miss (Edmonton at Christmas came in low in the spot check). Plan: keep our per-tier ranges from hotel samples, and scale them by the index for the trip's actual dates. 25 cities refreshed weekly is about 108 calls a month, US$2-5 a month.

## Changes this implies

1. **Links:** generate flight and hotel links through the partner links API at export time (about 55 requests for 530 fares; under the 100/min limit). Needs the Bahafin project ID and approved Aviasales and Booking.com programs.
2. **Flight coverage:** test `grouped_prices` with trip-length windows (e.g. 2-4, 5-8, 9-14 nights) against `prices_for_dates` for coverage per destination.
3. **Hotel seasonality:** add the LiteAPI city price index to the weekly job and scale ranges by the trip's dates.
4. **Gate D:** pull clicks and bookings from the statistics API instead of reading the dashboard by hand.
5. **LiteAPI production key:** needed before Gate A and before wider testing, so hotel prices are real rather than sandbox. Production flights stay off until we want the live price check.
