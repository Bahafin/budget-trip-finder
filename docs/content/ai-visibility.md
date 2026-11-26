# AI answers: which prompts to track, and how pages get cited

Written 2026-11-26 after a review with the `ai-seo` skill. **Why this matters:** for our core question, ChatGPT is a closer substitute than any Google tool ([google-comparison.md §1b](../research/google-comparison.md)). Getting **cited** in those answers, with our dated whole-trip numbers, is a channel in its own right.

## 1. Before anything else: be in the indexes AI tools search

An AI tool can't cite a page its search index doesn't have. Once the site is indexable (after Gate B) and on its own domain:

| Index | Feeds | What to do (owner, free) |
|---|---|---|
| Google | AI Overviews, AI Mode, Gemini | Search Console: add the domain and submit the sitemap |
| Bing | ChatGPT search, Copilot | Bing Webmaster Tools: import from Search Console |
| Brave | Claude's web search | Submit the main URLs at search.brave.com/submit-url |
| Perplexity | its own index plus Google's | Nothing to submit; allow `PerplexityBot` |

## 2. robots.txt policy (decide at launch)

These rules only work at the root of our own domain. GitHub Pages under a sub-path can't serve them.

- One `User-agent: *` rule that allows everything, plus `Sitemap:`. **Don't** write an allowlist of named bots: a named group silently shuts out the agents it doesn't name.
- **Keep the search and answer crawlers allowed:** `OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot`, Googlebot, Bingbot. Blocking them removes us from AI answers.
- **Training crawlers are a separate choice:** `GPTBot`, `ClaudeBot`, `Google-Extended`. Blocking them doesn't stop citations. Owner decision: we lean towards allowing them, because being "known" helps a new brand.

## 3. What makes our pages citable (built 2026-11-26)

- **Answer first:** every page opens with one dated sentence that is the whole answer.
- **Questions with direct answers:** each destination page has a "Common questions" section built from the data (cost of a week, cheapest month, flight price, spending money). No AI-written numbers.
- **Original data:** the "How we estimate" page publishes our 50-trip hand check (median 11% off on the whole trip) and every trip checked. Each destination page also shows its own check results. No one else has this, so it gives AI tools a primary source to cite.
- **Dates everywhere:** each amount carries `data-asof`, and pages say "estimated on <date>".
- **Plain HTML:** content is in the initial HTML, with no JavaScript needed to read it.

Not done yet, and worth doing at launch:
- An `/llms.txt` at the domain root listing the hubs, the method page and the monthly budget pages.
- An About page with a named owner. AI tools and Google both weigh who is behind the numbers.

## 4. Prompts to track (monthly, by hand)

Run each prompt **3 times** in ChatGPT (search on), Perplexity and Google (AI Overview / AI Mode), from Canada, logged out where you can. Record whether we're **cited** (linked as a source), **mentioned** (named) or absent, and who is cited instead. Write it as a rate, e.g. "cited 1/3".

| # | Prompt (the way people type it) | Our page that should answer it |
|---|---|---|
| 1 | where can 2 people go for $2000 from toronto in january | `/from-toronto/january/under-2000/` |
| 2 | vacation for two under $3000 from toronto | `/from-toronto/<month>/under-3000/` |
| 3 | how much does a week in cancun cost from toronto for 2 | `/from-toronto/cancun/` |
| 4 | punta cana trip cost from toronto | `/from-toronto/punta-cana/` |
| 5 | how much spending money for cancun per day | Cancún FAQ + spending-money guide |
| 6 | cheapest month to fly toronto to cancun | Cancún FAQ |
| 7 | march break 2027 trip ideas from toronto under $5000 family of 4 | `/from-toronto/march-break/` |
| 8 | is a trip to japan from canada affordable for 2 | `/from-toronto/tokyo/` |
| 9 | nyc trip cost from toronto for a weekend | `/from-toronto/new-york/` |
| 10 | orlando trip cost from toronto for a family | `/from-toronto/orlando/` |
| 11 | all inclusive vs booking separately cancun | guide (not written yet) |
| 12 | cheapest warm places to travel from toronto this winter | `/from-toronto/` + month hubs |
| 13 | tool to find trips that fit my budget from canada | home page (the trip finder) |
| 14 | how accurate are trip cost estimates / how much does a trip really cost | method page |

## 5. Log

Copy this table each month (first run: the week the site goes indexable).

| Date | Prompt # | Tool | Runs | Cited | Mentioned | Who was cited instead |
|---|---|---|---|---|---|---|
| | | | | | | |

**How to read it:** if an AI answer gets a fact about us wrong or vague, the page that should state that fact isn't saying it plainly, so fix that page first. If we're absent, the sources it does cite are the places to be seen (Reddit threads, Canadian publishers, YouTube).
