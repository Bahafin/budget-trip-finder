# Price validation, spot check 1 (2026-11-24)

**Method:** refreshed all data, then ran the site's default search (CAD 3,000, 2 adults, mid comfort, any month, longest trip that fits). For the top 3 results I checked the same dates by hand:
- **Flights:** Google Flights, cheapest round trip from Toronto, per person, CAD.
- **Hotels:** Booking.com, 4-star filter, 2 adults, 1 room, first page of results (20 hotels). Price plus Booking's separate "taxes and charges" line, divided by nights.

Daily spend can't be checked on a booking site, so it is left as our estimate in both columns.

## Results

| Trip | Flights for 2: ours (range) | Real | Error | Hotel for stay: ours (range) | Real (Booking median) | Error | Total: ours | Total with real prices | Error |
|---|---|---|---|---|---|---|---|---|---|
| Edmonton, Dec 25-27 | 906 (886-1,118) | 1,138 | **-20%**, outside range | 344 (207-442) | 350 | -2% | 2,090 | 2,328 | -10% |
| Orlando, Dec 15-17 | 950 (708-1,228) | 688 | **+38%**, outside range | 347 (261-583) | 320 | +8% | 2,230 | 1,940 | +15% |
| Chicago, Dec 16-18 | 912 (736-1,083) | 850 | +7% | 392 (304-553) | 448 | -12% | 2,236 | 2,230 | 0% |

All three real totals fall inside our total range, and all three trips really do fit the CAD 3,000 budget.

## What it tells us

1. **Hotels are good.** Medians land within -12% to +8% of Booking.com, and every real figure is inside our range. Per-night medians: Edmonton 172 vs 175, Orlando 174 vs 160, Chicago 196 vs 224.
2. **Flights are the weak part, and for a fixable reason.** Our cheapest cached fare is usually right: Orlando's 354 vs Google's 344, Chicago's 368 vs 425. But "expected" is the median of the 3 cheapest fares within +/- 2 nights *anywhere in the month*, so it pulls in other dates.
   - Orlando: other dates pushed expected to 475 per person, when the trip's own dates cost 344.
   - Edmonton: the 443 cached fare (Porter via Ottawa, Christmas Day) wasn't available at that price on Google; the cheapest was 569. Holiday fares move fast.
3. **Proposed fix:** anchor the flight estimate on the fare for the trip's own dates (expected = that fare +10%, high +35%) and use other dates only to widen the range. Applied by hand to these 3, the error goes from -20% / +38% / +7% to about -14% / +13% / -5%.
4. **Hotel fees paid at the property are missing.** LiteAPI lists some fees as "not included" (resort and environment fees). In the Cancún sample, 125 of 310 fee lines were like this. Add them to the total; it matters most for resorts.
5. **Daily spend is unverified and is about 40% of these totals.** It needs a different check, such as published per-city daily budgets or tester feedback.
6. **Results lean towards very short trips.** "Longest trip that fits" with "cheapest" sorting returned three 2-night trips for a CAD 3,000 budget. Testers may expect 5-7 nights by default.

## Caveats

- 3 trips is a spot check, not Gate A. Gate A is 50 trips across destinations, group sizes and dates.
- Booking.com's first page is its "top picks" order, not a random sample. Prices on both sites were taken on 2026-11-24.
- The hotel data came from LiteAPI's sandbox. Production prices could differ.

## Re-check after the flight fix (2026-11-25)

**Change:** flight "expected" is now the cheapest cached fare for the trip's own dates x 1.10. Low is x 0.95 and high is x 1.35 (or the priciest of the 5 cheapest fares in the month, if higher). The old rule used the median of the 3 cheapest fares anywhere in the month. The factors live in `engine.py` (`FLIGHT_LOW_FACTOR`, `FLIGHT_LIFT`) and are exported to the browser engine.

Flights refreshed this morning, then Google Flights checked again for the same dates (per person, round trip, CAD):

| Trip | Google today | Old rule: expected (error) | New rule: expected (error) | New range | Real inside? |
|---|---|---|---|---|---|
| Orlando, Dec 15-17 | 364 | 475 (+30%) | 390 (+7%) | 336-534 | yes |
| Chicago, Dec 16-18 | 467 | 456 (-2%) | 405 (-13%) | 350-497 | yes |
| Edmonton, Dec 25-27 | 547 | 453 (-17%) | 488 (-11%) | 421-598 | yes |
| **Average absolute error** | | **16%** | **10%** | | 3 of 3 |

Whole trip, 2 adults (hotels from the 2026-11-24 Booking.com check; daily spend is our estimate in both columns):

| Trip | Ours, old rule | Ours, new rule | With real flight and hotel prices | New error |
|---|---|---|---|---|
| Orlando | 2,230 | 2,059 | 1,980 | +4% |
| Chicago | 2,236 | 2,134 | 2,314 | -8% |
| Edmonton | 2,090 | 2,159 | 2,284 | -5% |

**Takeaways**
- The new rule removed the big overshoot (Orlando +30% to +7%). Whole-trip estimates are now within -8% to +4% on these three.
- Chicago shows the remaining risk. Its cached fare was 7 days old, and the real price rose from 425 to 467 overnight. Ideas to test: lift older fares more than fresh ones, and in Gate A, compare how far cached fares drift by age.
- Holiday dates (Edmonton, Christmas) still run low. Peak-date handling is another Gate A question.
- Still unverified: daily spend, and hotel fees paid at the property.
