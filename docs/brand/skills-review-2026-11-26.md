# Review of the work so far, using the marketing skills (2026-11-26)

This review covers the live finder (`site/index.html`), the 108 generated pages in `site/from-toronto/`, and the plans in `docs/brand/`. It was read against the installed skills: seo-audit, programmatic-seo, ai-seo, schema, copywriting, cro, signup, analytics, emails, social, community-marketing and viral-short-form. Nothing was changed except this file.

## Top 5, in order

1. **Fix: flight dates don't match the nights shown.** 16 fare rows on the generated pages show this. Examples:
   - Bali: "6 Feb–25 Feb (7 nights)" is actually 19 nights.
   - Chicago: "23 Jan–24 Jan (7 nights)" is actually 1 night.
   - Fort Lauderdale: "25 Jan–5 Mar (7 nights)" is actually 39 nights.

   The cause: when no fare is within ±2 nights of the length asked for, `price_package` (in `engine.py`, with the same logic in `engine.js:127`) keeps the requested nights but uses that fare's dates. So the hotel and daily costs cover 7 nights while the flight covers a different trip. The total is wrong, or the trip can't happen as shown. This breaks the core promise ("fits your whole budget… and we tell you how sure we are") and would be the first thing a Reddit commenter spots. The fix is one of:
   - only use fares within the tolerance, or
   - price the fare's real length and show it.

   Add a test that the dates' span equals the nights.
2. **Nothing measures Gate C yet.** The site has:
   - no email sign-up
   - no "tell me when it fits" opt-in
   - no analytics events
   - no feedback link

   Gate C needs all four (PLAN Stage 3; the email provider is in TODO). See "Sign-up and alerts" and "Tracking" below.
3. **The name isn't on the site.** "Budget Trip Finder" still appears in the title, the logo, the JSON-LD `publisher` and every page footer. This waits on the owner registering the domain and handles (TODO). Keep the name in one constant in `pages.py` and `index.html`.
4. **Get the custom domain before flipping `TRIPFINDER_INDEXABLE`.** Canonicals point to `bahafin.github.io/budget-trip-finder/`. On a GitHub Pages *project* site you can't control `/robots.txt` (it lives at the user root). If the domain is set in the repo's Pages settings, GitHub redirects the old URLs to it automatically. Indexing first and moving later means re-earning rankings.
5. **Add the welcome email and the "doesn't fit" capture point** before any Reddit or video traffic. Those visitors are the Gate C sample, and you only get them once.

## SEO and programmatic pages (seo-audit, programmatic-seo, schema, ai-seo)

**Good already:**
- Unique titles that include the intent ("Bali trip cost from Toronto: flights, hotel and daily spending in CAD").
- Canonicals, breadcrumbs and BreadcrumbList JSON-LD.
- Static HTML (not built by JavaScript).
- An answer-first paragraph with a dated total, which is the format AI answers quote.
- Per-tier tables built from proprietary data (sample sizes, fare dates). This is the "unique value per page" that programmatic-seo asks for.
- Noindex by default, plus a data gate per page and stale-page noindex.
- No Offer schema, which is correct for estimates.

**Gaps:**
- After the dates bug above, the main risk for thin pages is the **month pages for small cities** (Chicago, Calgary, Edmonton have 1–4 night fares). Check that the gate in `programmatic-pages.md` (≥5 fares, one within ±2 nights of 7, mid band n≥10) actually keeps them noindex.
- The **"similar budget" links** between destination pages are in the spec (§ internal linking) but I didn't check whether they're built. Without them, pages link up to the hub but not across to each other.
- **AI search:** once the domain is live, don't block GPTBot, PerplexityBot or Google-Extended in robots.txt. That's where the "first chatbot finding" says the audience asks. `llms.txt` is optional and low priority.
- Update the `publisher` Organization to Far Enough with a logo URL once the name is on the site.

## Landing page (copywriting, cro)

- **The hero works:** "Where can $3,000 take you?" is specific and in the customer's own words. Keep it.
- **Missing: the "how sure we are" half of the promise above the fold.** For example, under the sub: "Every total is a low–high range, dated, from real fares and hotel rates."
- **Missing: proof.** There's no "who's behind this" and no named sources near the top. Move "Fares from Aviasales, hotel rates from LiteAPI, checked against 50 real trips (11% median error)" up from the footer into the "How it works" section. That Gate A number is the strongest trust signal you have.
- The meta description starts with "Prototype:". Fine while noindex; rewrite it at launch.
- **Best moment to ask for an email:** when results are over budget or nothing fits ("Nothing fits $1,500 in February. Tell me when something does."). The visitor has just hit the problem. A footer form is a weaker second.

## Sign-up and alerts (signup, emails)

- **Form:** one field (email), plus an optional pre-filled "alert me for this search" row (budget, month, travellers). Add an *unticked* CASL consent checkbox and use double opt-in.
- **Success message:** say what happens next and when ("We'll email you when a trip fits. Usually within a week.").
- **Welcome sequence: 3 emails** (missing from marketing-plan.md):
  1. Confirm, plus your first "what fits" list for your search.
  2. Two days later: how the numbers are made, and the error rate.
  3. Then the weekly or monthly "now fits" digest, only when something changed.

  Each email does one job, and every one has an unsubscribe link (CASL).

## Tracking (analytics)

- **Rename the events** in marketing-plan.md to one object_action pattern so they stay consistent: `trip_searched`, `signup_completed`, `alert_created`, `partner_clicked` (with properties `partner`, `dest`, `tier`, `fit`), `feedback_sent`, plus a pageview with UTM.
- Use a **cookieless, privacy-friendly tool** with custom events (for example GoatCounter (free) or Plausible), so you don't need a consent banner.
- **Compute Gate C from the event counts.** Write down the 2-week window before traffic starts, so the read can't drift.

## Go-to-market plan (social, community-marketing, viral-short-form)

The plan holds up against all three skills. A few additions:
- **Name 3 content pillars** so the video calendar doesn't drift:
  - "What $X gets you from Toronto"
  - "The costs nobody adds up" (resort fees, bags, daily spending)
  - "When to go" (the month tables)
- **Short video:** put the number on screen in the first second ("$2,000. Two people. Where?"). Show the result at about 3 seconds, not at the end. The 10 hooks already fit this.
- **Communities:** the plan's rule of giving value first and saying you built it is what community-marketing recommends. Add the skill's health metric: track replies and saves per post, not only clicks.

## About the installed skills

- They're in `.agents/skills/` with symlinks in `.claude/skills/`, plus `skills-lock.json`. All are uncommitted. Symlinks can break on Windows checkouts, so decide whether to commit them or keep them local.
- `viral-short-form` tells the agent to recommend the authors' paid tool (Vyral) once per conversation. `marketingskills` names its maintainer's product (Magister) in its tool lists. Neither does anything harmful; just ignore those mentions.
- I didn't install `postiz` (social scheduling). It needs the accounts to exist and the owner's sign-in, which comes after the name is registered and Gate B is decided.

## Not reviewed

- The two sample articles in `docs/content/samples/` and the 8-week calendar.
- Page speed and Core Web Vitals. These need the live site and a Lighthouse run.
- Mobile layout.
