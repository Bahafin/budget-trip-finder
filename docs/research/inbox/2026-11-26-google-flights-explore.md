# Google Flights Explore, Toronto to anywhere (owner test, 2026-11-26)

**Steps:**
1. Google Travel Explore from Toronto, defaults: round trip, 1 adult, economy, "1-week trip in the next 6 months". [Link](https://www.google.com/travel/explore?tfs=CBwQAxoOagwIAhIIL20vMGg3aDYaDnIMCAISCC9tLzBoN2g2QAFIAXACggELCP___________wGYAQGyAQQYASAB&tfu=GgIgAw).
2. Clicked Miami.

**Setup:** owner's browser, 2026-11-26. Prices in CAD. When I opened the same link in the built-in browser (signed out), the page showed the search bar and filters but the results kept "Loading results", so everything below is from the owner's test and screenshot.

## What it showed

**Explore map (step 1):**
- **Flights only.** Destinations on a map with the cheapest round-trip fare each. No hotel, no daily spend, no total.
- **CAD.**
- **Default window: a 1-week trip any time in the next 6 months.** It finds the cheapest week for each place.
- **Filters:** Stops, Price, Airlines, Duration and **Bags**. The bag filter means Google can price a checked bag into the fare, which is something we don't do yet (feature-ideas #6).
- The map gives a feel for distance and travel time. The owner doesn't need that at this stage.

**Destination view (Miami, step 2):**
- Flights plus **stays** (hotel prices). **Still no trip total.**
- **Price insight:** "Prices are currently low: $112 cheaper than usual for your search".
- **"When to visit"** ([screenshot](screenshots/2026-11-26-google-explore-miami-when-to-visit.png)):
  - peak season (Dec-Mar, "most popular and higher prices") and off-season (Apr-Jul, "less popular and lower prices")
  - per month: high and low temperature (°C) and a popularity icon.

## Useful

- **Six months ahead.** It's the main thing Explore does better than us. → feature-ideas #4 (updated with what it would take).
- **"Cheaper than usual."** A reason to act now, with a number. → feature-ideas #14.
- **"When to visit."** Weather plus peak and off-season answers "is this a good month to go?", which a budget alone doesn't. → feature-ideas #15.
- **Bags filter.** → feature-ideas #6 (evidence added).
- **Confirms our gap.** Even Google's own travel tool, two clicks deep, never adds flights + hotel + spending into one number for a group.

## Wrong or unverified

| Claim | Status | Check |
|---|---|---|
| "$112 cheaper than usual" | ⚠️ Google's own history; we can't check it | Google doesn't say what "usual" means (likely its price history for the route and dates) |
| Miami temperatures (Nov 26/22 °C, Dec 24/21, Jan 23/19) | ⚠️ not checked | Plausible for Miami; not needed for a decision |
| Peak Dec-Mar, off-season Apr-Jul | ⚠️ not checked | Google's labels, probably from its own search and price data |

## What our data can and can't do here

- **Fare horizon: about 3 months, thinning fast.** Today's snapshot (2026-11-26) has 555 fares in December, 157 in January and 90 in February, and nothing after.
  - **Moving to production keys won't change that.** The LiteAPI production key affects hotels. Our flights come from the Aviasales cache, which only holds what other users recently searched.
  - The live Aviasales and Kiwi search needs 50,000+ monthly users.
- **Ways to see 6 months ahead:**
  - (a) **LiteAPI flights** (production): live prices for any date. EUR 0.005 per search beyond 1,500 searches per booking ([api-coverage-check.md](../api-coverage-check.md)). With no bookings that may mean paying for every search. A weekly 6-month scan of 26 places, one search per place per week, is about 2,800 searches a month, roughly EUR 15. Daily is about EUR 100. Rough sums; check how the "per booking" allowance works before relying on them.
  - (b) **Kayak's API**, if the affiliate application is approved.
  - (c) **Estimated fares** for months beyond the cache: the nearest cached month × a seasonal factor, clearly labelled `estimated`.
- **Hotels already go a year ahead.** The weekly job stores LiteAPI's city price index: daily average hotel prices about 365 days ahead for every destination. So **we can already say which months are expensive or cheap for hotels**, at no extra cost. That's half of Google's "when to visit".
- **Weather data** (checked 2026-11-26):
  - **Open-Meteo:** its free API is for **non-commercial use only**. Commercial use needs a paid plan, even though the data itself is CC BY 4.0 ([terms](https://open-meteo.com/en/terms)). Ruled out on the free tier.
  - **Hand-written table:** for about 26 places × 12 months, from public climate normals, written in our own words and refreshed yearly, costs $0. A public-domain source such as NOAA's global station data is likely usable (⚠️ terms not checked).
- **"Cheaper than usual" needs history we don't keep yet.** Each daily refresh overwrites the fare cache. **Start saving a daily summary now** (cheapest fare per destination × month × trip length). In 30-60 days we'd have our own "usual". History can't be bought back later.
- **Wording risk:** Canada's Competition Act targets misleading savings claims, and the Competition Bureau warns against made-up "regular prices" and vague savings claims ([Bureau: ordinary selling price](https://competition-bureau.canada.ca/deceptive-marketing-practices/types-deceptive-marketing-practices/ordinary-selling-price); [Nov 2025 notice](https://www.canada.ca/en/competition-bureau/news/2025/11/businesses-make-sure-your-black-friday-deals-are-real.html)). We aren't the seller, but say exactly what we measured: "$112 below the average we've seen for these dates over the last 60 days", not "on sale" or "save $112". This isn't legal advice. Add it to the questions for a lawyer.

## What it means for us

- Google comparison updated: first hands-on Google test in the log; rows for date range, price insight and when to visit.
- Feature ideas: #4 updated (how to reach 6 months), #6 evidence (Bags filter). New: #14 price vs our own history (**start collecting now**), #15 when to visit.
