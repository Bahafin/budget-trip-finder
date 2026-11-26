# SEO checklist for the day we turn indexing on (Gate B)

Written 2026-11-26 from a review with the `programmatic-seo` and `seo-audit` skills. Today every page is `noindex` and there's no sitemap, which is correct while we're testing. Before the switch (`TRIPFINDER_INDEXABLE=true`), go down this list.

Who does each item: **O** = owner, **D** = development session.

## Must be true before indexing

| ✓ | Item | Who | Status 2026-11-26 |
|---|---|---|---|
| ☐ | Own domain live (farenough.ca), and `SITE_URL` + `BRAND_NAME` in `pages.py` switched | O, D | Not registered |
| ☐ | Gate B (TICO) decided | O | Open |
| ☐ | GitHub Pages URL redirects to the new domain (or the old site is noindexed) so the two don't compete | D | — |
| ☐ | `robots.txt` at the domain root: allow all, plus a `Sitemap:` line ([ai-visibility.md §2](ai-visibility.md)) | D | Not possible on the sub-path |
| ☐ | Sitemap lists only pages that pass their gate. Already built: `site/from-toronto/sitemap.xml`; for robots.txt it needs to sit at the root, or be listed in a sitemap index there | D | Built, written only when indexable |
| ☐ | Canonical on every page points to the new domain (it's built from `SITE_URL`) | D | Built |
| ☐ | Home page (`index.html`) links to `/from-toronto/`. Today nothing links to the generated pages, which would leave them **orphaned** | D | **Not done** |
| ☐ | Trip finder results link to the matching destination page ("See the full cost breakdown") | D | Not done |
| ☐ | Email sign-up works (provider chosen, CASL consent) | O, D | Placeholder |
| ☐ | About page with a named owner and how to reach us (trust signal for Google and AI tools) | O | Not written |
| ☐ | Privacy page (no cookies today; the email provider changes that) | O | Not written |

## Already handled by the generator (tested)

- Unique titles of 65 characters or fewer, unique meta descriptions, one `<h1>` per page.
- Breadcrumbs in the page and as `BreadcrumbList` JSON-LD. No `Offer` or `Product` markup.
- Thin-page gates: 74 of 109 pages pass today. Pages that fail stay `noindex` even after launch.
- Every amount dated, plus a staleness banner and noindex if fares are older than 14 days.
- Affiliate disclosure before the first partner link; partner links use `rel="sponsored nofollow"`.
- The "How we estimate" page and per-destination check results (E-E-A-T and original data).
- Content in plain HTML: no JavaScript needed to read a page.

## Known risks to watch in Search Console (first 8 weeks)

1. **Hub vs month page overlap.** `/from-toronto/cancun/` leads with the cheapest month, so its main table matches `/from-toronto/cancun/january/`. If Search Console shows "Duplicate, Google chose different canonical", or the two pages swap places for the same query, give the hub a different lead: a month comparison instead of one month's table.
2. **Pages "updated" every day.** `dateModified` is the data date, so every page changes daily. The spec says to change it only when a headline number moves more than 5%. Build that if Google crawls a lot but indexes slowly.
3. **Templated wording.** All 25 destination pages share sentence templates. What makes them differ is the numbers, the questions and answers, and the per-destination checks. The biggest improvement is still the owner's hand-written paragraph for the top 10 destinations. Watch "Crawled, currently not indexed" for destination × month pages: if more than half stay out after 6 weeks, noindex the month pages and keep the hubs.
4. **Mixed brand names.** Pages say "Budget Trip Finder" until the switch. Change it before indexing so Google never learns the old name.

## After launch (weeks 1–8)

- Search Console and Bing Webmaster Tools: submit the sitemap; check indexed vs submitted weekly.
- PageSpeed Insights on the home page, the Cancún hub and one budget page (photos are the heaviest part).
- Monthly AI-answer check ([ai-visibility.md §4](ai-visibility.md)).
- Pages at positions 8–20 for a query: improve their title and first paragraph first. That's the fastest win.
