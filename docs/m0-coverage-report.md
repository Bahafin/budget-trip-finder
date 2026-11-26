# M0 Coverage Report (in progress)

Checked 2026-11-22 with the owner's Travelpayouts token. Script: `scratch/coverage.py` (not committed).

## Flights: Aviasales Data API, passed

`GET /aviasales/v3/prices_for_dates`, origin `YTO` (all Toronto airports), round trip, `currency=cad`.

| Departure month | Fares (CA market) | Destinations |
|---|---|---|
| Dec 2026 | 221 | 70 |
| Jan 2027 | 164 | 66 |
| Feb 2027 | 114 | 56 |
| Mar 2027 | 67 | 36 |
| Apr 2027 | 62 | 36 |

- 148 distinct destinations over the five months. Cache age: median 3 days, max 6.
- `market=us` returns almost the same data (146 destinations), so the market quirk from the spec does not hurt Toronto.
- Coverage halves past ~3 months out. Flexible-date search should default to the next 3 months and mark later dates as thin.
- Fares are per person, round trip, and include airline code, transfers, duration and a deep-link path (needs the marker appended).
- Cheapest by destination includes NYC 169, FLL 204, MBJ 205, CUN 299, LAX 350, LIR 372, PUJ 435, LIS 595, LON 593, PAR 589, BCN 651 (CAD, lowest seen across the five months).

## Lodging: Hotellook, failed

- `engine.hotellook.com/api/v2/cache.json` and `lookup.json` both return HTTP 404. The hotel data API the v2 spec relied on is gone.
- Hotellook is not in the Travelpayouts programs catalog.
- No hotel program in the catalog (Booking.com, Trip.com, Agoda, Expedia, Hotels.com, Vio.com, Hostelworld, Vrbo, Klook, Traveloka, KKday, Rakuten x2) advertises a price API.
- Travelpayouts' Tools page lists a **Data API "available in some programs on request"**. Ask support which hotel programs offer it.
- Consequence: curated lodging bands become the launch source, not the fallback.

## Duffel (checked 2026-11-23, test token)

Docs read: Stays guides and API reference, offer requests, test mode, pricing, Services Agreement.

**Stays (hotels): blocked for now.**
- The test token gets `This feature is not enabled for your account. Please contact sales` on `POST /stays/search`, even for the test hotels. Stays needs a request to Duffel sales.
- In test mode Stays only returns synthetic "Duffel Test Hotel" properties, so test mode can't measure coverage or accuracy anyway. That needs live access.
- If enabled, the shape fits: search by lat/long + radius (km), dates up to 330 days ahead, guests and rooms. Each result gives `cheapest_rate_total_amount` + currency for the whole stay, star `rating`, review score, location and photos. `fetch_all_rates` gives every room rate. `/stays/accommodation/suggestions` handles place autocomplete.
- Commercial terms are a profit share on completed stays, set by sales.

**Flights: works in test mode, but adds little over Aviasales.**
- `POST /air/offer_requests` YYZ to CUN round trip, Jan 15-22 2027, 1 adult returned 635 offers. Air Canada had 486, Porter 122, Air Transat 24, WestJet 2, and the Duffel sandbox airline 1.
- Every offer came back in **USD**. The request has no currency parameter; the agreement ties currency to the account's balance currency.
- Test-mode prices come from airline sandboxes, and Duffel says it can't guarantee them. The cheapest non-sandbox fare was USD 369.95, but don't treat it as real.
- Each search is a live call taking a few seconds. Aviasales gives cached calendars for free, which suits discovery better.

**Terms that matter for a referral-only site (Services Agreement):**
- **2.5(d): no use of the Services "for metasearch purposes."** Showing Duffel prices and sending users elsewhere to book looks like metasearch. This is the main risk and must be confirmed with Duffel in writing.
- 2.5(k): Supplier data can't be marketed without the supplier's consent. 10.1: rates and click-through volume are confidential.
- 2.3: the search-to-order ratio is counted separately for Flights and Stays, and zero orders counts as one. With no bookings that's 1,500 free searches a month, then USD 0.005 per search. For example, 30k searches costs about USD 142 a month.
- Going live needs KYC verification and a card on file. Eligibility for a Canadian sole proprietor isn't stated.

**Conclusion:** Duffel is built for selling through its API, which is Phase 2 (agent and booking). For Phase 1 it only helps if sales enable Stays **and** confirm in writing that showing prices without booking through Duffel is allowed. Until then, lodging stays on curated bands.

## LiteAPI / Nuitee (checked 2026-11-23, sandbox key)

Docs: docs.nuitee.com (hotel rates, min-rates, static hotel data, flights, experiences access, pricing). Script: `scratch/liteapi_probe.py`.

**Hotels: works in sandbox, with real hotels and CAD prices.** `POST /v3.0/hotels/rates`, 15-20 Jan 2027, 2 adults, `guestNationality=CA`, cheapest rate per hotel:

| City | Hotels priced | 3-star median per night | 4-star | 5-star |
|---|---|---|---|---|
| Cancun | 158 | CAD 95 | CAD 206 | CAD 635 |
| Lisbon | 194 | CAD 107 | CAD 144 | CAD 289 |
| Medellin | 125 | CAD 75 | CAD 118 | CAD 166 |

- Real property names (Melia, InterContinental, Fairfield by Marriott). About 13 s per city search. Responses carry `"sandbox": true`. The docs call it "production-like" but don't say the prices are real, so spot-check before trusting them.
- Search by city, lat/long + radius, place id, IATA code, or hotel ids. Filters include star rating; `maxRatesPerHotel=1` returns only the cheapest rate.
- Free hotel list (`/data/hotels`) with stars, rating, reviews and location, but no prices.
- Commercial model: you sell through LiteAPI and earn a markup or commission. Searches are free within a 5,000:1 search-to-book ratio, and excess "may be billed" (no published rate). A free white-label booking site is offered, but no affiliate or referral link was found. The Terms of Service haven't been read yet.

**Flights: works in sandbox, in CAD.** YYZ to CUN round trip, 15-22 Jan 2027: 345 itineraries, cheapest CAD 394.32, median CAD 720. Each fare includes a base/tax split and checked-bag fees. Docs say the sandbox flight data has "limited accuracy". Fees: 1% ticketing (EUR 2-10), plus EUR 0.005 per search beyond a 1,500:1 search-to-book ratio.

**Experiences: built but not enabled for us.** The docs overview still says "coming soon" (no timeline), but the MCP server already exposes 10 experience tools: search, details, availability, reviews, booking options, prebook, book, status, cancel preview, cancel. Search takes free text or lat/long + radius, dates, currency and price limits. A sandbox search for Cancun returned 403: "Experiences API access is not enabled for this account. Please contact support." It's a booking product (Stripe payment, vouchers).

**MCP server (checked 2026-11-23):** `https://mcp.liteapi.travel/api/mcp`, MCP protocol 2025-06-18 over HTTP with event-stream responses. Auth with the `X-API-Key` header (Bearer and `?apiKey=` also work; the header is preferred because query strings get logged). Our sandbox key returns **133 tools**: 7 for docs and discovery, plus generated wrappers over the whole REST API (hotels and content, hotel booking, flights, experiences, eSIM, loyalty, vouchers, analytics, mapping). Default rate limit is 500 requests/s. A read-only docs server is at `/api/knowledge`.
- Phase 1: not needed. Our backend calls the REST API directly from a scheduled job, which is cheaper, testable, and keeps the LLM away from prices (spec 7).
- Phase 2: a strong fit for the travel-agent idea. An agent can search, hold and book hotels, flights and experiences through one server. Keys stay server-side and the agent never sees them. Nuitee also documents OAuth for Claude, ChatGPT and Cursor.

**Fit for Phase 1 (referral only):**
- Best use: a scheduled job that uses hotel rates to **refresh the curated lodging bands**. That's a few hundred searches a month, inside the free ratio even with zero bookings. Users never trigger a LiteAPI call, and booking links still go to Booking.com/Expedia affiliates.
- Flights and experiences: Aviasales and Viator already cover these on a referral basis. LiteAPI versions belong in Phase 2, when we sell.
- Using the white-label booking site would make us a seller (Nuitee takes payment, we earn commission). That's the TICO question (Gate B), so not in Phase 1.

## Still to check

- [x] ~~Travelpayouts support reply on hotel Data API.~~ Not needed: the help centre FAQ says Aviasales has no hotel API (2026-11-25). Hotels come from LiteAPI.
- [ ] Visa dataset rows for Canadian passports.
- [x] World Bank price levels: the old indicator is archived; derived from PPP / FX instead (built into `refresh reference`, 2026-11-23).
- [ ] Read LiteAPI Terms of Service: search-only use, displaying derived price ranges, any metasearch clause.
- [x] Spot-checked LiteAPI hotel prices against Booking.com (2026-11-24): medians within -12% to +8%. See validation-2026-11-24.md.
- [x] 25 launch destinations picked automatically by flight coverage, skipping countries at advisory level 2+ (`python -m tripfinder select`, 2026-11-23).
