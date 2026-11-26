# SEO and content strategy: Canadian budget-trip searches

Written 2026-11-25. Working name "Budget Trip Finder" (the brand is being chosen in `docs/brand/`).

## Read this first: what is measured and what is estimated

- **No paid keyword tool was used.** There are no Ahrefs/Semrush search volumes or difficulty scores here. Every "volume" and "difficulty" label below is **my estimate**, based on (a) what kinds of pages rank today, (b) how many big publishers target the phrase, and (c) how specific the phrase is. Treat them as a ranking of bets, not as numbers.
- **What the searches showed (2026-11-25):** the top results for the head terms are Canadian publishers (Narcity, blogTO, Curiocity, Money.ca, MoneySense), seller pages (Sunwing, Air Transat, Expedia, Kayak, Priceline) and generic budget sites (BudgetYourTrip, Champion Traveler). Several of the publisher pages ranking for money phrases are **years old** (a 2022 blogTO all-inclusive list, a 2017 Global News list, 2020 budget data). That staleness is our opening: we have prices dated today.
- **Reddit:** the web search tool returned no Reddit threads directly (it often doesn't index them). The Reddit section below is therefore about **how we'll use those communities**, and the step "read 20 recent threads by hand" is on the calendar for week 1. I did not invent thread titles or quotes.
- **First job once the site has a domain:** add it to Google Search Console (free). After 4-6 weeks its query report gives real impression counts, which replace every estimate in this file.

## 1. Who we are writing for

Canadians, mostly in the Greater Toronto Area at first (our only origin is YTO), who start from **a total amount of money** rather than a destination:
"we have $2,000", "under $3,000 for March break", "is Cancún doable on $2,500 for two".

Their real question is: *what does the whole trip cost, all in, in Canadian dollars, and what fits?* Most ranking pages answer only part of it:

| What ranks today | What it leaves out |
|---|---|
| Flight-route pages (Kayak, Expedia, Priceline): "from $199" | Hotels, food, local costs; USD vs CAD confusion; "from" prices for one date |
| All-inclusive deal lists (Narcity, Curiocity, Sunwing) | Dated within days; per-person "from" prices; taxes, tips and resort extras often missing |
| Generic budget sites (BudgetYourTrip, Champion Traveler) | No flights from Canada; USD; old data |
| Cheapest-countries listicles (Money.ca, Narcity, Savvy New Canadians) | No whole-trip number for a given budget; often years old |

**Our angle in one sentence:** the whole-trip price, as a dated low / expected / high range in CAD, from Toronto, with the parts shown separately so readers can check them.

## 2. Keyword groups by search intent

Volume and difficulty are estimates (see above). "Realistic for us" means a new, low-authority domain with no backlinks could reach page 1 within 3-9 months with a genuinely better page.

### A. Budget-first ("where can I go for $X")
Our core use case and the best fit for the tool itself.

| Example queries | Volume (est.) | Difficulty (est.) | Realistic for us? | Page type |
|---|---|---|---|---|
| where can I travel for $2000 from Canada / Toronto | Medium | Medium | **Yes**, long-tail variants first | Budget hub + monthly "Where $X gets you in <month>" |
| vacation for 2 under $3000 from Toronto | Low-medium | Low-medium | **Yes** | Same |
| cheap places to travel from Toronto in January / February | Medium | Medium (Money.ca, Kayak) | Partly; win the month + budget combinations | Monthly page |
| trips under $1000 from Canada | Medium | High (dominated by sale/package sellers) | No, for now | Mention in hubs only |

### B. Destination cost ("how much does a trip to X cost from Toronto")
The best SEO opportunity: high intent, many cities, and our data answers it directly.

| Example queries | Volume (est.) | Difficulty (est.) | Realistic for us? | Page type |
|---|---|---|---|---|
| Cancun trip cost from Toronto / for 2 people / for a week | Medium | Medium | **Yes** | Programmatic destination page |
| how much is a trip to Japan from Canada | Medium | Medium-high (many blogs) | Yes, on "from Toronto" + month variants | Destination page + guide |
| Punta Cana / Orlando / NYC / Lisbon trip cost from Canada | Low-medium each | Low-medium | **Yes**, the long tail adds up | Destination pages |
| is Bali / Bangkok expensive for Canadians | Low-medium | Low-medium | Yes | Destination page FAQ |
| how much spending money for Cancun / Punta Cana | Low-medium | Low | **Yes** | Daily-cost section + short guide |

Evidence: today's "Cancún cost from Toronto" results are mostly **flight-only** pages (Kayak CA, Expedia CA, Priceline, FareCompare, Hopper, Air Transat). Kayak's CA route page gives month averages (cheapest month around C$400, December and August around C$610-620). None of them add hotel and daily costs for the same dates. That gap is exactly our product.

### C. Seasonal / event ("March break", "Christmas", "reading week")
Big, predictable demand peaks. Ontario's March break is one fixed week, so prices spike and families search early (January-February).

| Example queries | Volume (est.) | Difficulty (est.) | Realistic for us? | Page type |
|---|---|---|---|---|
| March break trips under $3000 / family | Medium, seasonal (Jan-Mar) | Medium (insauga, NerdWallet CA, Kayak CA, Curiocity) | **Yes**, if published by early January | Seasonal page from our data + family guide |
| cheap Christmas getaway from Toronto | Medium, Nov-Dec | Medium | Too late for 2026; plan for 2027 | Seasonal page |
| reading week trips from Toronto (Feb) | Low | Low | **Yes**, students | Seasonal page |

Note: today's March break results are a mix of 2022-2025 articles with stale prices (one 2024 Curiocity listing priced a Cuba resort at about $778 per adult). A page with this year's dated numbers is a real improvement.

### D. All-inclusive (very large, very competitive, and a product gap)
"cheap all inclusive from Toronto" is probably the biggest Canadian sun-travel phrase. Sunwing, Air Transat, red-tag-style sellers, Narcity and blogTO own it.

**Honest product gap:** our engine prices **flights + hotel + daily spending** (a do-it-yourself trip). It does not price all-inclusive packages, where meals and drinks are in the hotel rate. We should not pretend to rank for "cheapest all inclusive". What we can do honestly and well:

| Query | Realistic for us? | Page type |
|---|---|---|
| all inclusive vs booking separately / is all inclusive worth it Canada | **Yes** (comparison, not deals) | Guide using our DIY numbers next to published package "from" prices, dated |
| how much extra to bring to an all inclusive (tips, excursions) | **Yes** | Short guide |
| cheap all inclusive from Toronto | No | Don't target |

Product note for the build plan, not for content: if all-inclusive intent shows up strongly in Search Console, an "all-inclusive" lodging tier (resort rates with board basis) would be the single biggest content unlock.

### E. Cost-breakdown and planning guides (supporting content)
Lower volume each, easy to rank, good for links from Reddit answers and for email sign-ups.

- how much spending money per day in Mexico / Dominican Republic / Thailand
- hidden costs of a trip (resort fees, tourist taxes, baggage, airport parking)
- USD vs CAD prices: why the "from $199" fare isn't $199
- how far in advance to book flights from Toronto (from our own cached-fare data, once we have a few months of it)

### F. Branded and navigational (later)
"<brand> review", "<brand> trip finder". Only matters after launch. Note: Aviasales and Expedia ban paid-search ads on their brand names (PHASE1_SPEC section 14), and we shouldn't bid on brand terms anyway at near-zero budget.

## 3. What a small new site can realistically win

Ranked bets (most promising first):

1. **Destination cost pages with "from Toronto" in the title** (group B). Many cities, each with modest competition, and our numbers are unique. Programmatic, so near-zero ongoing effort once built. See [programmatic-pages.md](programmatic-pages.md).
2. **"Where $X gets you in <month>" pages** (group A). Budget × month × group size is a combination nobody covers with whole-trip numbers. Programmatic.
3. **Seasonal pages published 6-10 weeks ahead** (group C): March break 2027 is the first target, so it must be live by early January 2027.
4. **Spending-money and hidden-cost guides** (group E). Hand-written, evergreen, good Reddit answer material.
5. **All-inclusive vs DIY comparison** (group D). One strong page, not a deal list.

Skip for now: "cheap flights" head terms, "all inclusive deals", generic "best places to visit". They are owned by sellers and big publishers, and a referral site with no domain history won't move there.

## 4. Two risks that shape the plan

**AI answers eat clicks.** Studies of Google AI Overviews in 2025 report big drops in clicks to the top result when an AI summary appears: Ahrefs measured about 34.5% (early 2025) and about 58% (December 2025 re-run); Pew found users clicked a result about 8% of the time with an AI summary vs 15% without. Google disputes several of these studies. Implications for us:
- Generic questions ("is Japan expensive") will increasingly be answered on Google itself. Pages need something an AI summary can't give: **today's dated numbers for a specific budget, month and group size, and a tool to change them.**
- Every page carries a **price-alert / monthly email** sign-up. Email is the channel AI can't take (PHASE1_SPEC section 15).
- Branded queries reportedly do better under AI Overviews (Amsive: +18% CTR for branded queries), so building a recognisable name through Reddit and short video is worth it.

**Google's scaled-content policy.** Since March 2024 Google treats "many pages generated mainly to manipulate rankings" as spam, whether made by people or automation, and since mid-2025 issues manual actions for it. Programmatic pages are allowed when each page genuinely helps the reader. Our guardrails (in programmatic-pages.md): publish a page only when it has enough real data, no thin "Cancún in October" pages with nothing in them, no AI-spun filler text, `noindex` for low-data pages.

## 5. Compliance constraints on all content

From PHASE1_SPEC sections 7, 8 and 14, plus Canadian advertising law:
- **Referral wording only.** We compare and link; bookings are completed on partner sites. No "book now with us", no "our price", no "deal" language that implies we sell. Ontario TICO registration is still an open question (Gate B), so stay well on the referral side.
- **Prices are always dated estimates** ("estimated on 2026-11-25, CAD, for 2 adults"), shown as ranges. The Competition Bureau treats **drip pricing** (advertising a price that leaves out mandatory fees) as an enforcement priority, especially in travel (FlightHub 2021, Cineplex 2024, Canada's Wonderland 2025). We don't sell, but headlines like "Cancún for $327!" that quote a one-way-ish fare without the rest invite the same criticism. Headline numbers are **whole-trip expected totals**, never the cheapest component.
- **Affiliate disclosure** at the top of every article and page that has partner links.
- **No AI-generated numbers.** An LLM may help draft prose; every number comes from `site/data.json` or the engine, and is checked.
- **No copied text** from partners, travel.gc.ca or competitors. Advisory levels are quoted as a level with a link to the official page.
- **Viator content** is never in indexable page source.

## 6. Measurement (free tools only)

- Google Search Console: impressions, queries, positions per page. Weekly look.
- Click logging per partner (already planned in the spec) to compute earnings per 1,000 visitors (Gate D).
- Email sign-ups per page: the number that matters most while search traffic is small.
- UTM tags on every Reddit/Facebook/video link so we can tell channels apart.

## Sources (read 2026-11-25)

Search results pages and publishers:
- blogTO, all-inclusive from Toronto under $1,000 (2022): https://blogto.com/travel/2022/10/vacations-all-inclusive-from-toronto
- Narcity, last-minute all-inclusives from Toronto: https://www.narcity.com/toronto/last-minute-all-inclusive-vacations-from-toronto
- Curiocity, all-inclusives under $1,000: https://curiocity.com/all-inclusive-vacations-toronto-under-1000/
- Curiocity, March break all-inclusive deals: https://curiocity.com/all-inclusive-vacation-deals-toronto-march-break/amp/
- Sunwing, all-inclusive from Toronto: https://www.sunwing.ca/en/vacation-deals/all-inclusive-vacations-from-toronto
- Money.ca, cheap places to travel from Toronto: https://money.ca/life/travel/cheap-places-to-travel-from-toronto
- Money.ca, cheapest places to travel from Canada: https://money.ca/life/travel/cheapest-places-to-travel-from-canada
- Savvy New Canadians, cheapest places to visit from Canada: https://www.savvynewcanadians.com/cheapest-places-to-visit-from-canada/
- Global News, budget destinations (2017): https://globalnews.ca/news/3200060/budget-friendly-destinations-adventurous-canadians-should-check-out-in-2017
- Kayak CA, Toronto-Cancún route: https://www.ca.kayak.com/flight-routes/Toronto-YTO/Cancun-CUN
- Expedia CA, Toronto-Cancún flights: https://expedia.ca/lp/flights/yto/cun/toronto-to-cancun
- Hopper, cheap flights Toronto-Cancún: https://media.hopper.com/articles/five-tips-on-finding-cheap-flights-from-toronto-to-cancun
- FareCompare, Toronto-Cancún: https://www.farecompare.com/flights/Toronto-YTO/Cancun-CUN/market.html
- insauga, March break budget ideas: https://www.insauga.com/popular-march-break-budget-friendly-travel-ideas-in-canada/
- NerdWallet CA, March break overspending: https://www.nerdwallet.com/ca/personal-finance/march-break-tips-to-avoid-overspending
- Kayak CA, March break destinations: https://www.ca.kayak.com/news/march-break-destinations
- Neo Financial, is all-inclusive the cheapest way for Canadians to travel: https://www.neofinancial.com/the-get/what-does-all-inclusive-mean-is-it-the-cheapest-way-for-Canadians-to-travel
- BudgetYourTrip (example of generic budget site): https://www.budgetyourtrip.com/canada/toronto
- Japan cost examples: https://www.klook.com/blog/japan-travel-cost , https://www.moneywehave.com/how-much-does-it-cost-to-go-to-japan
- YYZ Deals (Toronto deal site with Facebook group and alerts): https://www.yyzdeals.com/tag/canada

AI Overviews and Google policy:
- Ahrefs, AI Overviews reduce clicks (and update): https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/
- Search Engine Land on Pew's study: https://www.searchengineland.com/google-ai-overviews-hurting-clicks-study-459434/
- Press Gazette on Authoritas: https://pressgazette.co.uk/media-audience-and-business-data/google-ai-overviews-publishers-report-clickthroughs-authoritas-report/
- Google, March 2024 core update and spam policies: https://developers.google.com/search/blog/2024/03/core-update-spam-policies

Advertising law:
- Competition Bureau, drip pricing: https://competition-bureau.canada.ca/en/node/662
- Competition Bureau, "The ambush of hidden fees" (2024): https://www.canada.ca/en/competition-bureau/news/2024/05/the-ambush-of-hidden-fees.html
- McMillan on the FlightHub case: https://mcmillan.ca/insights/competition-bureau-grounds-flighthubs-misleading-advertising/

Community rules (secondary sources; check each sidebar before posting):
- r/PersonalFinanceCanada rules quoted in a removed-post discussion (self-promotion and surveys not allowed): https://libreddit.winscloud.net/r/CanadaFinance/hot
- 90/10 self-promotion guideline explained: https://gleam.io/faq/marketing-and-growth-strategies/promotion/reddit-90-10-rule-explained
