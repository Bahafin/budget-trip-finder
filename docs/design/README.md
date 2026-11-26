# Site redesign screenshots

Taken 2026-11-25 from `site/` on branch `site-redesign` (rebased on main's tracked-link and airline changes), served locally.

- `desktop-light.png`, `desktop-dark.png`: 1366 px wide, top 3000 px of the page (headless Edge).
- `mobile-*.jpg`: 375 x 812 phone viewport (in-app browser): hero and search (dark), a result card, the partner links, and a card in dark mode.

## What changed
- Hero photo with the headline "See how far $3,000 goes.", where the amount is the budget field (after the 2026-11-26 design review; it was "Where can $3,000 take you?").
- Search form as one panel; on phones the fields sit in a 3 + 2 grid.
- Result cards lead with a destination photo, the place, a "Fits your budget" / "Stretch" badge, nights, dates and travellers, then the estimated total, the likely range and the per-person price.
- A small meter shows the low-to-high range against the budget line; the same numbers are written as text.
- "What's included" lists flights, hotel and daily spending with each one's range and confidence label in plain words ("Cached fare, 2 days old"); the engine's detail strings sit under "How we estimated this".
- Travel advice and "Know before you go" notes stay on every card, with their official sources.
- Partner buttons say where they go ("See flights on Aviasales", "See hotels on Klook" or "on Booking.com", from `hotelLinkFor()`), never "Book now". Both are `rel="noopener sponsored"`.
- The Flights row names the airline and says direct or how many stops. A line under them says prices are estimates and links may be affiliate links.

## Brand
Colours and type follow `docs/brand/name-and-brand.md` section 5: lake `#0E5E6F`, sun `#F2A541` for the one call to action (ink text on it), paper background, mist fields and track, ink dark mode; Bricolage Grotesque for display and Inter for text (Google Fonts). All are CSS custom properties at the top of `site/index.html`. The brand is decided (Far Enough), but the site shows "Budget Trip Finder" until farenough.ca is registered; change the name in `site/index.html` (see the comment above `<title>`) and `BRAND_NAME` in `backend/src/tripfinder/pages.py` together.

## Photos
`site/photos.js` maps each airport code to a Wikimedia Commons photo (hotlinked 960 px thumbnail) with author, licence and file page; the card shows the credit. To swap a photo, change all four fields together.
