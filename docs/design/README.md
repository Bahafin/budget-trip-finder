# Site redesign screenshots

Taken 2026-11-25 from `site/` on branch `site-redesign`, served locally, with the 2026-11-26 data snapshot.

- `desktop-light.png`, `desktop-dark.png`: 1366 px wide, top 3000 px of the page (headless Edge).
- `mobile-*.jpg`: 375 x 812 phone viewport (in-app browser): hero and search, a result card, the partner links, and a card in dark mode.

## What changed
- Hero photo with the budget question ("Where can $3,000 take you?"), updated live as the budget changes.
- Search form as one panel; on phones the fields sit in a 3 + 2 grid.
- Result cards lead with a destination photo, the place, a "Fits your budget" / "Stretch" badge, nights, dates and travellers, then the estimated total, the likely range and the per-person price.
- A small meter shows the low-to-high range against the budget line; the same numbers are written as text.
- "What's included" lists flights, hotel and daily spending with each one's range and confidence label in plain words ("Cached fare, 2 days old"); the engine's detail strings sit under "How we estimated this".
- Travel advice and "Know before you go" notes stay on every card, with their official sources.
- Partner buttons say where they go ("See flights on Aviasales", "See hotels on Booking.com"), never "Book now". A line under them says prices are estimates and links may be affiliate links.

## Brand swap
Colours and fonts are CSS custom properties at the top of `site/index.html` (`--brand`, `--sun`, `--font-display`, ...). The name appears in `<title>`, the logo text and the logo `aria-label`.

## Photos
`site/photos.js` maps each airport code to a Wikimedia Commons photo (hotlinked 960 px thumbnail) with author, licence and file page; the card shows the credit. To swap a photo, change all four fields together.
