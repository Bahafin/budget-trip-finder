# Budget Trip Finder (prototype)

Enter a total trip budget and get whole trips from a Canadian city (Toronto, Montreal or Vancouver for now) that fit: flights, hotel and daily spending, as a low / expected / high range in CAD.

**Try it:** https://bahafin.github.io/budget-trip-finder/ (prototype for user testing; prices are estimates, not quotes)

## How it works

- `backend/`: Python data jobs and the pricing engine. The jobs refresh cached fares (Aviasales), sample hotel prices (LiteAPI), and load price levels (World Bank) and Canadian travel advisories. See [backend/README.md](backend/README.md).
- `site/`: the static test site served by GitHub Pages. `python -m tripfinder export` writes `site/data.json`, and `site/engine.js` prices trips in the browser. A parity test (`node --test site/tests/parity.test.mjs`) checks it against the Python engine.
- `docs/`: spec, plan, data coverage report and [proof-of-concept report](docs/poc-report.md).

## Lists kept in the repo (data/seed/)

- `origins.csv`: departure cities. `destinations.csv`: the destinations each departure city shows. Changing either makes the next daily run re-select and refresh.
- `ground.csv`: places in reach without flying, per departure city: a public option (train, bus or ferry, with a typical advance one-way fare per adult and hours) and/or a car option (km one way, drive hours, parking per night, ferry fares). Hand-entered and rough; the engine prices the trip both ways (and by plane when there are fares) and shows the cheapest, always labelled "estimated". A ground place also needs its row in `destinations.csv` so it gets hotel prices.
- `themes.csv`: "best for" tags and a "what to do" line per destination (hand-written, no prices). `site/photos.js`: one real, credited Wikimedia Commons photo per destination.
- **To add a departure city:** add a row to `origins.csv` and its destinations to `destinations.csv` (check first that the Aviasales cache has at least 5 fares for each pair), then run `refresh auto`, `assets --fill-photos` (review any photo it marks `"review": true`), add theme rows for new places, `export` and `pages`. The daily workflow does everything except the theme rows and the photo review.
- `fare_history` and `band_history` (database tables) keep one summary row a day, so we can later say how today's prices compare with what we've seen.

## How the test site stays fresh

`.github/workflows/pages.yml` runs every day and on every push to `main`:
1. Restores the database from the GitHub Actions cache.
2. Runs `refresh auto`: flights daily, hotels weekly, reference data monthly, and a full rebuild if the cache is gone.
3. Exports `site/data.json` (the default city) and `site/data/<city>.json`, fills photos for new places, builds the pages under `site/from-<city>/`, and runs both test suites.
4. Deploys.

It needs two repository secrets, `TRAVELPAYOUTS_TOKEN` and `LITEAPI_KEY`. Without them it deploys the committed snapshot. To force a step, run the workflow manually with, for example, `force: hotels`.

The committed `site/data.json` is only a fallback. To update it by hand:

```bash
cd backend
uv run python -m tripfinder refresh auto
uv run python -m tripfinder export
```
