# Google vs Far Enough

**The core question:** "I have $X in total for N people from Toronto. Where can we go, all costs in?"

**Draft 1, 2026-11-25.** Built from [competitors.md](../brand/competitors.md) §5-6, the spec's risk table ([PHASE1_SPEC.md](../PHASE1_SPEC.md) §15) and a source check run today. **The owner hasn't run any hands-on tests yet.** Rows marked *to test* get filled in from the owner's results (§6).

Status marks: ✅ confirmed from a primary source, ⚠️ third-party or not yet tested from Canada, *to test* means nobody has checked it yet.

## 1. What Google offers for this question (as of 2026-11-25)

| Google tool | What it does for our question | Canada? | Status |
|---|---|---|---|
| **Google Flights Explore** | Map of destinations from YYZ. The price filter keeps only places you can **fly** to under a limit. Flights only. | Yes | ✅ [Google blog](https://blog.google/products/travel/theres-still-time-to-plan-your-perfect-spring-break-trip) (desktop filter) |
| **Flight Deals** (AI, in Google Flights) | You type a sentence ("a week somewhere warm in February") and get cheap-fare destinations. Flights only. | Beta in Canada, the U.S. and India from 2025-08-14. Expanded to 200+ countries in Nov 2025 | ✅ [Google blog](https://blog.google/products/search/google-flights-ai-flight-deals/), [support page](https://support.google.com/travel/answer/16497283?hl=en) |
| **Exclude basic economy** filter | Removes basic fares on U.S. and Canada trips, so the cheapest fare you see is closer to what you'd pay with a bag | U.S. and Canada | ✅ same Google blog |
| **Price insights** (low / typical / high vs history) | Says whether a **flight** price is good. Not a range of what the trip will cost | Shown "for eligible routes" | ⚠️ third-party guides; *to test* on YYZ routes |
| **Google Hotels** | Hotel prices per destination, with a total-price display option | Yes | *to test*: does it show the total with taxes and fees in CAD? |
| **AI Mode Canvas trip planning** | Builds a plan in a side panel with live flight and hotel data, Maps and web info. You can mention a budget in your prompt | **U.S. only, Labs opt-in, desktop** when announced (Nov 2025) | ✅ [Google blog](https://blog.google/products-and-platforms/products/search/agentic-plans-booking-travel-canvas-ai-mode/); *to test* whether it works from Canada now |
| **AI Mode hotel booking / price tracking** | Hotel booking hand-off inside Google is U.S. only. Flight price tracking in 180+ countries | Tracking yes, booking no | ⚠️ [TechCrunch, Aug 2026](https://techcrunch.com/2026/08/27/googles-ai-mode-can-now-track-flight-prices-help-book-hotels-and-more/) (not checked against Google's own page) |
| **AI Overviews** in normal search | A summary answer to "where can I travel for $2,000 from Toronto" | Yes | *to test*: which numbers it gives and where they come from |

**What we haven't found:** any Google tool that **models a total trip budget** (flights + hotel + daily spend for N people) and filters destinations by it. A "total trip under $X" option would be a small step from Explore plus Hotels. **That's the threat to watch** (§5).

## 2. Side by side on the core question

| What the user needs | Google (best tool for it) | Far Enough today | Who wins |
|---|---|---|---|
| Start from a budget, not a destination | Explore price filter, Flight Deals prompt | Budget is the first field | Tie |
| **Budget covers the whole trip** (flights + hotel + spending for the group) | No. Flights only, or a plan where you add things up yourself | Yes: flights + hotel + daily spend, totalled for N travellers | **Us** |
| Group maths (rooms, kids, per-person split) | Passenger count for flights; hotel guests separately | Rooms and travellers in one total, per-person split | **Us** |
| Honest uncertainty | Price insights for flights (good / typical / high) | Low / expected / high range on the total, confidence label per part | **Us** (if Gate A holds) |
| Price freshness and accuracy | **Live** fares and hotel prices | Cached fares (up to about 7 days), sampled hotel bands, estimated daily spend. Spot check within -8% to +4% on 3 trips; Gate A not done | **Google** |
| Destination coverage | Every route from YYZ | 25 destinations | **Google** |
| Dates | Flexible dates, calendar, "any week in the next 6 months", months ahead | Month optional; fares only about 3 months ahead | **Google** |
| Natural-language input | Flight Deals and AI Mode take a sentence | Form only (LLM parsing planned after Gate A) | **Google** |
| CAD and Canadian context | CAD prices; no advisories | CAD, Government of Canada advisory level on each result, level 2+ dropped | **Us** |
| Know before you go (drones, cash, medication) | Not in the flight or hotel tools; AI Mode might mention some | Notes per destination linking to travel.gc.ca (planned for all 25) | **Us** (once written) |
| Daily spending estimate | None in the flight and hotel tools; AI answers may guess | Canadian baseline × World Bank price level (unvalidated, about 40% of the total) | **Us**, but our weakest number |
| Price tracking / alerts | Flight price tracking, email alerts | None yet ("tell me when it fits" planned as a waitlist) | **Google** |
| Speed to an answer | One page, instant | One page, instant (static) | Tie |
| Trust and brand | Huge | Unknown new site | **Google** |
| Booking path | Many partners; booking in AI Mode for U.S. hotels | Referral links (Aviasales, Klook; Expedia pending) | **Google** |

## 3. Where we win, and how to show it

1. **The total.** Google answers "where can I fly for $400". We answer "where does $2,500 get the two of you, hotel and food included". Show the gap with one real example per page: Google's flight price next to our all-in range (feature-ideas #1; marketing hook 2: "Google says $389 to Lisbon...").
2. **Honest ranges plus confidence labels.** Nobody shows a low / expected / high total. That only counts if Gate A passes, so Gate A is also our marketing proof.
3. **Canadian specifics.** Advisories, know-before-you-go, CAD, Toronto first. Google is global and won't do this per country.
4. **The "doesn't fit" list.** Google's price filter hides places just over the limit. We can say "Lisbon fits if you add $300 or go in February" (feature-ideas #5).

## 4. Where Google wins, and what would close the gap

| Gap | Closes it | Cost / when |
|---|---|---|
| Live prices vs our cache and estimates | Live price check of the top results (LiteAPI flights); show the age of every price; Gate A numbers on the site | Stage 4; EUR 0.005 per search beyond the free ratio |
| 25 destinations | Grow to 40-60 once Gate A passes; say "we cover 25 popular places from Toronto" rather than pretend to be complete | After Gate A |
| Flexible dates / cheapest month | Month comparison over the fare horizon (feature-ideas #4) | After Gate A |
| Typing a sentence | LLM parsing into the form, never producing prices (feature-ideas #2) | Stage 4 |
| Alerts | "Tell me when it fits" waitlist now, real alerts later (feature-ideas #3) | Waitlist now |
| Brand trust | Show the method and sources, publish the accuracy test, date every number | Landing page + Gate A report |
| **Not closable:** coverage, live inventory, distribution | Don't compete. Send users to Google Flights to confirm a fare if that builds trust | n/a |

## 5. Threat watch

What would hurt us most, roughly most likely first. Check each again when the owner tests:

1. **Canvas trip planning reaches Canada** and answers our question with a believable total. Our edge would shrink to ranges, advisories and focus. → *Test from Canada (Q5 below).*
2. **Explore adds hotels** ("flight + hotel under $X"). Google's older Destinations feature once showed flight + hotel estimates ([Techlicious](https://techlicious.com/blog/google-destinations-a-better-way-to-plan-your-next-vacation), old), so this is a known idea for them.
3. **AI Overviews answer "where can I go for $2,000 from Toronto"** with a list. That takes the search clicks our content plan targets ([seo-strategy.md](../content/seo-strategy.md)). → *Test Q6.*
4. **Flight Deals adds an "all-in" or hotel option.**

Signals: Google's travel blog (blog.google/products/travel), Search Engine Land and Skift travel coverage. Re-check this section monthly or when the owner sees something new.

## 6. Test script for the owner

So results are comparable, run the same six questions in each Google tool and on our site. Record the date, device, signed in or not, and take one screenshot per answer (save as `screenshots/<date>-<tool>-q<n>.png`). Paste notes or screenshots here in chat, and I write them up.

| # | Question | Run it in |
|---|---|---|
| Q1 | $2,000 CAD total, 2 adults, 5 nights, January, from Toronto | Explore (set the price limit to what's left after a rough hotel guess), Flight Deals, our site |
| Q2 | $5,000 total, 2 adults + 2 kids, March break 2027 | Flight Deals, AI Mode, our site |
| Q3 | $1,500 total, 1 adult, 4 nights, February | Explore, Flight Deals, our site |
| Q4 | $6,000 total, 2 adults, 10 nights, open to Asia | Flight Deals, AI Mode, our site |
| Q5 | Free text in AI Mode (try Canvas if it appears): "We have $2,500 total for two people from Toronto for a week in February. Where can we go with flights, hotel and food all included?" | AI Mode, Gemini app |
| Q6 | Plain Google search: "where can I travel for $2000 from Toronto" | Google Search (note whether an AI Overview appears) |

For each answer, note:
- Did it suggest destinations without being told one?
- Did its number cover **flights only, flights + hotel, or everything**?
- Was it in CAD and for the whole group?
- Did it show a range or say how sure it was?
- Did it mention advisories or entry rules?
- How many clicks or follow-ups did it take to get a total?
- Would you trust the number?

## 7. Test log

| Date | Tool | Question | Result in one line | Note |
|---|---|---|---|---|
| — | — | — | No tests yet | — |
