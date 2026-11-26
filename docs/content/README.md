# Content and SEO plan

Written 2026-11-25. Brand: **Far Enough** (pages say "Budget Trip Finder" until farenough.ca is registered). Nothing here is published; the site stays `noindex` until launch.

**Update 2026-11-26:**
- **Status:** the page generator is built and runs daily (109 pages, all noindex), and Gate A passed (median 11% whole-trip error over 50 trips).
- **Skill review:** the plan was reviewed with the `programmatic-seo`, `seo-audit` and `ai-seo` skills. What changed is in [seo-strategy.md §7](seo-strategy.md).
- **Generator additions:** a "How we estimate" page with the Gate A results, per-destination check results, and "Common questions" on destination pages.
- **New docs:** [ai-visibility.md](ai-visibility.md) (prompts to track, getting cited), [launch-seo-checklist.md](launch-seo-checklist.md) (what must be true before indexing) and a drafted spending-money guide.

**The three things that matter most before launch:**
1. Link the home page and the trip finder results to `/from-toronto/`. Today the pages are orphans.
2. The owner's About page.
3. The owner's own paragraph on the top destination pages.

| File | What it is |
|---|---|
| [seo-strategy.md](seo-strategy.md) | Keyword groups for Canadian budget-trip searches, what a new site can realistically win, risks (AI answers, scaled-content policy, drip-pricing optics), sources |
| [programmatic-pages.md](programmatic-pages.md) | Spec for auto-generated destination and month pages from `site/data.json`: URLs, templates, indexing gates, schema.org, guardrails |
| [content-calendar.md](content-calendar.md) | 8 weeks (30 Nov 2026 – 24 Jan 2027) of articles, short videos and community posts with hooks and community rules |
| [samples/cancun-from-toronto-cost.md](samples/cancun-from-toronto-cost.md) | Sample destination cost breakdown (numbers from the engine, estimated 2026-11-25) |
| [samples/where-2000-gets-two-january.md](samples/where-2000-gets-two-january.md) | Sample "where $2,000 gets two people in January" list (same data). **Superseded:** the generated page `/from-toronto/january/under-2000/` now does this daily |
| [samples/spending-money-mexico-dominican-republic.md](samples/spending-money-mexico-dominican-republic.md) | Draft guide #8: spending money for Cancún and Punta Cana (engine numbers, 2026-11-26; 3 facts to check, owner paragraph to add) |
| [ai-visibility.md](ai-visibility.md) | Getting cited in ChatGPT, Perplexity and Google AI answers: indexes, robots.txt policy, 14 prompts to track monthly, log |
| [launch-seo-checklist.md](launch-seo-checklist.md) | What must be true before indexing is switched on (Gate B), what's already tested, risks to watch in Search Console |

**Big caveat:** no paid keyword tool was available, so search volumes and difficulty are my estimates from what ranks today. Search Console data replaces them 4-6 weeks after launch.

## The idea in one paragraph

Most pages that rank for "Cancún trip cost from Toronto" or "where can I travel for $2,000" give a flight-only "from" price, a deal list that's out of date within days, or generic USD budgets with no flights from Canada. Many of the ranking articles are years old. We have whole-trip prices (flights + hotel + daily spend) for 25 destinations from Toronto, in CAD, dated, refreshed daily. So we build **one page per destination and per month × budget from that data**, add a few hand-written guides, and put an email sign-up on every page, because AI answers will take a growing share of search clicks.

## Top 10 target pages

In priority order. "Type" P = programmatic (generated daily), H = hand-written.

| # | Page | URL | Type | Main searches it targets |
|---|---|---|---|---|
| 1 | Cancún from Toronto: what a week really costs | `/from-toronto/cancun/` | P + H paragraph | cancun trip cost from toronto, cancun for 2 people cost, spending money cancun |
| 2 | Where $2,000 gets two people in <month> | `/from-toronto/january/under-2000/` (then February, March) | P | where can I travel for $2000 from Canada/Toronto, vacation for 2 under $2000 |
| 3 | March break 2027 from Toronto: what fits $3,000 and $5,000 for a family | `/from-toronto/march-break/` | P + H | march break trips under $3000, march break family trip cost |
| 4 | Punta Cana from Toronto: trip cost | `/from-toronto/punta-cana/` | P + H paragraph | punta cana trip cost from toronto, punta cana for 2 |
| 5 | Where $3,000 gets two people in <month> | `/from-toronto/january/under-3000/` | P | trips under $3000 from Toronto, vacation under $3000 for 2 |
| 6 | All-inclusive vs booking flights and hotel separately | `/guides/all-inclusive-vs-diy/` | H | is all inclusive worth it Canada, all inclusive vs booking separately |
| 7 | Orlando from Toronto: trip cost | `/from-toronto/orlando/` | P + H paragraph | orlando trip cost from toronto, disney trip cost from canada (families) |
| 8 | How much spending money for Mexico and the Dominican Republic | `/guides/spending-money-mexico-dominican-republic/` | H | how much spending money for cancun / punta cana |
| 9 | Tokyo from Toronto: trip cost | `/from-toronto/tokyo/` | P + H paragraph | how much is a trip to Japan from Canada |
| 10 | New York from Toronto: trip cost | `/from-toronto/new-york/` | P + H paragraph | nyc trip cost from toronto, new york weekend cost |

Why these: Mexico/Caribbean and Orlando are what Toronto searches for in winter and our data is deepest there; budget × month pages are the combination nobody else covers; March break is the biggest predictable peak and must be live by early January; Japan is a high-interest "can we afford it" question where an honest "about $6,900 for two" is useful. Bali and Bangkok follow next ("cheap there, expensive to get to").

Not targeted: "cheap all inclusive from Toronto" and "cheap flights" head terms (owned by sellers and big publishers, and we don't price all-inclusive packages yet).

## First 4 weeks of work

About 4-5 hours a week of the owner's time, plus coding-agent time for the generator.

| Week | Owner | Coding agent |
|---|---|---|
| **1** (30 Nov – 6 Dec) | Read 20 recent Reddit threads on trip budgets and log the exact questions (`questions-log.md`). Review and edit sample 1 (Cancún); add a short personal paragraph. Record the first 30-second screen video. | ~~Page generator and guardrail tests~~ **done 2026-11-26.** Next: link the home page and trip-finder results to the pages. |
| **2** (7 – 13 Dec) | Review sample 2 ($2,000 in January). Video: "Only 3 of 25 places fit $2,000." 3-5 helpful Reddit answers with numbers, **no links**. | ~~Month × budget pages, gates, sitemap~~ **done.** Next: prefill the trip finder from page links (`?dest=&month=&adults=`). |
| **3** (14 – 20 Dec) | Write the spending-money guide (Mexico/DR). Ask Reddit (no link, if rules allow) what people actually spent per day, to check our daily estimates. Pick an email provider (owner decision). | ~~Destination × month pages, breadcrumbs, JSON-LD~~ **done**, plus the method page and per-page questions. Next: the `dateModified` >5% rule. |
| **4** (21 – 27 Dec) | Light week. Short piece and video on holiday fares from our December data (about $436 vs $800-1,060 per person for Cancún). Start the March break draft. | Email sign-up box on every page (once provider chosen); "See full breakdown" links from tool results to destination pages. |

Week 5's fixed deadline: **March break page live by 4 January 2027.**

## Decisions and tasks this plan needs from the owner

- Email provider (CASL-compliant consent and unsubscribe). Needed before week 4.
- Video accounts (YouTube/TikTok/Instagram) under the brand name, once chosen.
- Search Console, once the domain exists.
- When to flip the site from `noindex` to indexable (after Gate B, TICO).
- Whether to add an all-inclusive lodging tier to the engine later (biggest content unlock if demand shows up).

## Things noticed in the data while writing this

- Lisbon is not one of the 25 destinations (it came up in planning).
- Fares only reach 3 months ahead (Dec 2026 – Feb 2027 today). March break pages need March fares in the cache by early January.
- Punta Cana's basic-tier hotel price comes from 5-8 hotels; resort fees aren't in hotel totals yet (validation doc point 4).
- Daily spending is about 40% of totals and still unverified; the content calendar uses community questions to help check it.
