# $2,500 for two from Toronto or Hamilton (ChatGPT, 2026-11-26)

**Asked:** "Find me 5 places I can go in the next two months flying out of Toronto or Hamilton, for a budget of 2500 CAD (including flights, accommodation and money spent)". Follow-up: "Budget is for 2 adults".
**Tool and setup:** ChatGPT with web search (it cites sources), logged in, so it used saved memory about the owner. Shared link: https://chatgpt.com/share/6b07ac68-3764-83e8-98df-3405536dbd94 (read 2026-11-26).

## What it answered

**First answer.** It assumed $2,500 was for **one** adult and 4 nights, even though it knew from memory that the owner travels with family. It gave five places, each with a "best for" label, a cost table (flight, 4 nights' lodging, food, activities, misc.) as ranges, and a "what to do" line:

| Place | "Best for" | Total for 1 person |
|---|---|---|
| Cancún | Escaping winter, beach | $1,500-2,100 |
| Mexico City | Culture, food, value | $1,150-1,650 |
| New York | Short city break | $1,650-2,100 |
| Montreal | Quick winter getaway | $1,200-1,550 |
| Orlando | Theme parks, warm weather | $1,500-2,100 |

It ended with a ranking, a personal pick (Mexico City), caveats (estimates; checked bags and insurance not included) and a **clarifying question** about group size.

**After "2 adults".** Same five places, a single number each (no range) for 4-5 nights:

| Place | Flights for 2 | Lodging | Spending | Total |
|---|---|---|---|---|
| Mexico City | $700 | $450 | $600 | $1,750 |
| Cancún | $850 | $550 | $650 | $2,050 |
| Montreal | $400 | $600 | $700 | $1,700 |
| New York | $600 | $900 | $800 | $2,300 |
| Orlando | $800 | $600 | $700 | $2,100 |

Advice: go in January rather than over the holidays. It asked another clarifying question (beach or city?) and offered next steps ("plan a detailed 5-night trip").

## Same question on our engine (snapshot 2026-11-26, 2 adults, $2,500, "most nights")

| | December, budget tier | January, budget tier |
|---|---|---|
| Fits (expected ≤ $2,500) | Punta Cana 8n $2,192 · Cancún 7n $2,302 · Montreal 4n $1,771 · Calgary 4n $1,850 · Kingston (Jamaica) 4n $2,052 · Dallas 4n $2,423 | Punta Cana 8n $2,132 · Cancún 7n $2,235 · Vancouver 5n $2,461 · Dallas 4n $2,397 · Calgary 3n $1,750 |
| Stretch (low end fits) | Edmonton, Vancouver, Orlando 4n $2,538, Chicago, Amsterdam, New York 3n $2,976 | Montreal 6n $2,575, Frankfurt, Istanbul, Paris |

At the **mid** tier only 1-2 places fit in each month. **Mexico City isn't one of our 25 destinations**, so we can't show ChatGPT's top pick.

Component comparison, same place:

| | ChatGPT (2 adults, 4-5 nights) | Us (budget tier) |
|---|---|---|
| Montreal | flights $400, lodging $600, spending $700 = $1,700 | 4n: flights $392, lodging $579, daily $800 = $1,771 (range $1,354-2,826) |
| Cancún | $850 / $550 / $650 = $2,050 | 7n in Dec: $959 / $511 / $832 = $2,302 |
| New York | $600 / $900 / $800 = $2,300 | 3n in Dec: $372 / **$1,894** / $710 = $2,976 |
| Orlando | $800 / $600 / $700 = $2,100 | 4n in Dec: $1,045 / $605 / $888 = $2,538 |

## Useful

- **Grouping by what a place offers** ("best for beach", "culture and food", "theme parks") makes five numbers easy to choose between. We show numbers only. → feature-ideas #8.
- **Clarifying questions** at the right moment: group size, then beach or city. Our form asks for everything up front. → merged into feature-ideas #2.
- **Places you don't have to fly to.** The owner's point: Montreal works by train, bus or car. ChatGPT priced it as a flight, but it's the kind of trip we can't show at all today. → feature-ideas #7.
- **Mexico City** is a strong value pick for Toronto and isn't in our 25. → feature-ideas #9.
- **Hamilton (YHM)** was asked for and ChatGPT ignored it. → feature-ideas #10.
- It warns about the holiday price jump and leaves out bags and insurance. We already handle holidays (city price index). Bags → feature-ideas #6.

## Wrong or unverified

| Claim | Status | Check |
|---|---|---|
| $2,500 is for one person (first answer) | ❌ | Wrong guess. A whole-trip tool needs the group size before it shows a number. Our form makes it required |
| Mexico City flights for 2 = $700 | ❌ (internally) | It cites "around $590 per person" for Jan 18-23, which is $1,180 for two. The table uses a lower fare without saying which dates |
| New York lodging $900 for 4-5 nights for two | ⚠️ likely low for December | Our LiteAPI band gives $1,894 for 3 nights at the budget tier in December. The Dec 2026 spot check put our hotel medians within -12% to +8% of Booking.com. ChatGPT itself said January, not Christmas |
| Spending money $600-800 for two for 4-5 nights (about $65-90 per person per day) | ⚠️ unverified | That's far below our baseline (budget $80, mid $140 per adult per day). **Neither figure is validated.** This is Gate A 2.3's question; add it to the daily-spend check |
| Fare figures ("from $310", "$400-430 per person to Cancún in January") | ⚠️ unverified | Sourced from deal blogs (RedTag, escapenightly, Axel) and Kayak snippets, not live searches. Our Cancún January fare for two is $856 (≈ $428 per person), so it agrees |
| Totals as single numbers after the follow-up | — | Not wrong, but less honest: the first answer had ranges and the second dropped them |
| Advisories, entry rules, know-before-you-go | Missing | Not mentioned at all. Our Canadian specifics still differ |

## What it means for us

- **ChatGPT is a real substitute for our core question.** It gives a whole-trip answer in CAD, grouped by what each place offers, in about a minute. Its weak points:
  - it guessed the group size
  - its numbers aren't consistent
  - its sources are stale
  - it has no confidence labels, advisories or links to check prices.
- **Our edge against chatbots:** live-ish data that is dated and consistent, ranges, advisories, and partner links. **Its edge against us:** places by theme, more destinations (Mexico City), conversation, and ground-travel trips.
- The gap in daily spending (theirs roughly half of ours) is the most important number to check in Gate A.
- Feature ideas added or updated: #2 (chat input, with an NVIDIA note), #7, #8, #9, #10.
- Google comparison updated: new §1b on chatbots and a test log row.

Sources checked:
- NVIDIA NIM FAQ: https://forums.developer.nvidia.com/t/nvidia-nim-faq/300317
- Busbud affiliate program: https://www.busbud.com/en-ca/affiliate
- Travelpayouts Busbud offer: https://travelpayouts.com/en/offers/busbud-affiliate-program
- Travelpayouts Omio data: https://support.travelpayouts.com/hc/en-us/articles/360024389872-Data-from-Omio
- Omio VIA Rail page: https://www.omio.com/companies/trains/via-rail
