# Proof of Concept Report

Date: 2026-11-23. Code: `backend/` (package `tripfinder`). How to run it: [backend/README.md](../backend/README.md).

**Question:** can we gather and keep fresh the data for whole-trip packages from Toronto (flights + hotel + daily spend) at near-zero cost?

**Answer: yes, at this scale.** The data for 25 destinations, 3 months ahead, costs nothing to keep fresh. The only metered source, LiteAPI hotel search, runs about 333 searches a month, 7% of its free allowance. User searches never call an outside API: they read a 2 MB database and answer in under half a second.

## What was built

| Part | What it does |
|---|---|
| Pricing engine (`engine.py`, `money.py`) | Package = flights + lodging + daily spend, each as low / expected / high in CAD, with a confidence label: `cached (Nd)`, `sampled (Nd)` or `estimated`. Rooms allocated at 2 adults per room. Without a trip length, it finds the longest trip that fits the budget, using only lengths a real fare offers. Ranks by fit (within budget, then stretch) and price or nights. Money arithmetic refuses mixed currencies. 29 unit tests. |
| Data jobs (`jobs.py`, `providers.py`) | `select`: picks the 25 destinations with the most cached fares and skips countries where Canada advises avoiding travel (Russia and Israel were dropped). `refresh flights`, `refresh hotels`, `refresh reference`. |
| Cost meter (`meter.py`, `costs.py`) | Logs every outbound call (provider, endpoint, status, time, bytes; never keys), retries rate limits, and projects the monthly volume. |
| Search (`search.py`, `cli.py`, `web.py`) | `python -m tripfinder search ...` and a local web page with results, cost breakdown bars, travel advisories, "know before you go" notes and outbound links. |

## Data sources and measured cost (one full refresh)

| Job | Source | Calls per run | Time | Schedule | Calls per month | Cost |
|---|---|---|---|---|---|---|
| Flights | Aviasales Data API (Travelpayouts) | 75 | 11-16 s | daily | 2,250 | Free |
| Hotels | LiteAPI `hotels/rates` (sandbox) | 75 | 75 s | weekly | 333 | Free within 5,000 searches per booking |
| Price levels | World Bank (PPP ÷ exchange rate) | 2 | 1 s | monthly | 2 | Free, CC BY 4.0 |
| Travel advisories | Global Affairs Canada JSON feed | 1 | <1 s | monthly | 1 | Free (we link, we don't copy) |
| Destination pick | Aviasales + Travelpayouts city list | 8 | 2 s | monthly | 8 | Free |

- Total refresh time is about 1.5 minutes a day, which fits GitHub Actions' free tier with plenty to spare.
- One weekly hotel run gives 7,500-9,300 hotel prices and 194 price ranges (destination × month × comfort tier).
- **Worst case for hotels:** if LiteAPI billed every search at Nuitee's published flight surcharge (EUR 0.005), 333 searches would cost EUR 1.67 a month.
- **Scaling:** 100 destinations × 6 months is 600 searches per weekly run, about 2,600 a month. That's still about half of a 5,000 allowance, or EUR 13 a month at the worst-case rate.

## What the results look like

A CAD 3,000 search for 2 adults, mid comfort, January 2027 returns Calgary (3 nights, CAD 2,515) and Cancún (5 nights, CAD 2,744) within budget. Dallas, Vancouver and Istanbul come back as stretches.

A CAD 6,000 search for 2 adults, 2 children, 7 nights, budget comfort ranks Cancún first (CAD 3,029: flights 1,560, hotel 409, daily 1,061), then Punta Cana. Cancún carries Mexico's cash-declaration note and a "high degree of caution" advisory link.

## What the POC found

1. **Flight coverage is good near-term, thin per destination.** There are about 12 cached fares per destination per month. Some destinations have only 1-3 fares for a month, so the engine sometimes has to price a trip length that no cached fare matches. Those trips are labelled `estimated` and get a wider range.
2. **Resort destinations need a curated hotel area.** Liberia, Punta Cana and Orlando returned few or no hotels around the city point. `data/seed/hotel_areas.csv` sets the right search centre and radius, and fixed all three. Kingston stays thin (37 hotels).
3. **The LiteAPI sandbox rate-limits parallel searches.** Four workers got HTTP 429. Two workers plus retry with backoff gave 0 failures.
4. **The World Bank price-level indicator is archived.** It's derived instead as PPP conversion factor ÷ market exchange rate. For example, Mexico is 0.65× Canada, Colombia 0.45×, the US 1.11×.
5. **Daily spend is the weakest number.** The Canadian base (CAD 80 / 140 / 240 per adult per day by tier) is an assumption scaled by price level. It is often the largest component, so it's the first thing the accuracy test (Gate A) should check.

## Not proven yet

- **Accuracy.** Sandbox hotel prices look plausible but haven't been checked against Booking.com. That's Gate A: 50 packages priced by hand.
- **Production terms.** LiteAPI's Terms of Service haven't been read (search-only use, showing derived ranges). The production key needs a card on file. Whether zero bookings still get a 5,000-search allowance is unconfirmed.
- **Affiliate links.** Flight links carry the Travelpayouts marker. Hotel links are plain Booking.com searches until the program is joined.
- **Hosting.** Everything runs locally on SQLite. Postgres and scheduled jobs come in M1.

## Running cost summary

| Item | Monthly |
|---|---|
| Flight data | $0 |
| Hotel data | $0 (worst case about EUR 2) |
| Reference data (price levels, advisories, cities) | $0 |
| Scheduled jobs (GitHub Actions) | $0 |
| Database | $0 (2 MB) |
| **Total** | **$0, worst case under EUR 2** |
