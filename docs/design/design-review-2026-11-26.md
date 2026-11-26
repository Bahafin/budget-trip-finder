# Design review against the frontend-design skill (2026-11-26)

Skill: `anthropics/skills` → `frontend-design` (Apache 2.0), installed in `.agents/skills/` and linked from `.claude/skills/`.
Brief: `docs/brand/name-and-brand.md` §5 (palette and type are fixed by the brief; the skill says the brief's own words win).

## Subject, audience, job
- Subject: whole-trip budgets from Toronto, as an honest range in CAD. Brand **Far Enough**, tagline "See how far your budget goes."
- Audience: Canadians who know what they can spend but not where to go.
- Job of the page: turn one number into a short list of real trips, and send people to partner sites to check and book.

## Audit of the merged redesign

| Skill rule / generic tell | Where it showed up | Change |
|---|---|---|
| One word accented in the headline | "$3,000" in sun colour inside "Where can $3,000 take you?" | The amount becomes the budget field itself, set in the headline type. It is accented because you can edit it, not as decoration. |
| ALL-CAPS labels, eyebrow above the heading | "WHOLE TRIPS FROM TORONTO", "WHAT'S INCLUDED" | Eyebrow removed; the descriptor sits with the logo in sentence case. "What's included" label dropped: the coloured rows say it. |
| Meta strings joined with middle dots | Country · tagline, status line, airline line, footer | Rewritten as short phrases and sentences. |
| "→/↗" appended to button text | Partner buttons | Arrows removed. A hidden "(opens in a new tab)" is read to screen readers; the fine print says it opens the partner site. |
| Numbered markers on content that isn't a sequence | "How it works" 1/2/3 cards | Numbers and card boxes removed; three plain columns of text. |
| SaaS card kit: one radius and one soft shadow on everything | Search panel, result cards, how-it-works cards | Cards lose the drop shadow (hairline border only); radius steps by role: 14px cards, 10px fields and buttons, pills round. The search panel keeps its shadow because it floats over the photo. |
| Big number + small label as the hero default | Hero | The hero is now the question you answer by typing: "See how far **$3,000** goes." |
| Generic logo mark | Orange circle with a figure | A dotted flight arc landing on a horizon line under a small sun, per the logo brief (concept, not the final mark). |

Kept on purpose: the photo scrims (they are for legibility, not decoration), the range meter (the brief's "signature visual": mist track, lake band, ink tick), sun only on the one action per card and the "fits" badge.

## Token plan
- Colour (from the brief): ink `#13293D`, lake `#0E5E6F`, sun `#F2A541`, sun-deep `#B45309`, paper `#FBF8F3`, mist `#E6F0F2`.
- Type: Bricolage Grotesque for the headline, place names and totals; Inter for everything else, tabular figures for money. Scale (px): 13 / 15 / 17 / 22 / 30 / clamp(40-76) headline.
- Layout: left-aligned throughout. Hero is the editable sentence, the rest of the search folds into one quiet row under it.

```
[ Far Enough  Whole-trip budgets from Toronto ]
  See how far
  $ 3,000___  goes.          <- the input is the headline
  [adults][children][nights][month][comfort] [Show trips]
10 trips fit $3,000                         sort: [most nights]
[ photo card ] [ photo card ] [ photo card ]
```

- Principle: spend the boldness on the editable headline; keep cards calm and factual.

## Memory for next pass
Tried: photo-led cards, range meter, sun CTA. Not tried yet: a map or route view; a "compare two trips" layout; destination pages.

## Result
- Screenshots: `review-desktop-hero-light.jpg`, `review-desktop-cards-dark.jpg`, `review-mobile-hero-editing-light.jpg` (budget field focused), `review-mobile-hero-dark.jpg`, `review-mobile-card-dark.jpg`, `review-mobile-how-footer-dark.jpg`. The older `desktop-*.png` / `mobile-*.jpg` files show the first redesign, for comparison.
- Behaviour: the headline budget accepts "3000" or "3,000", reformats with a comma when you leave it, re-runs the search 0.4 s after you stop typing, and asks for at least $100. Enter also submits.
- Parity test: 7/7. No console errors; no sideways scroll at 375 px.
- Seen while testing: headless Edge (used for full-page screenshots) often gets no Wikimedia thumbnails back, while a normal browser gets all 25. Wikimedia throttles some automated traffic; one more reason to copy the photos to our own hosting before launch.
