# Budget Trip Finder (prototype)

Enter a total trip budget and get whole trips from Toronto that fit: flights, hotel and daily spending, as a low / expected / high range in CAD.

**Try it:** https://bahafin.github.io/budget-trip-finder/ (prototype for user testing; prices are estimates, not quotes)

## How it works

- `backend/`: Python data jobs and the pricing engine. The jobs refresh cached fares (Aviasales), sample hotel prices (LiteAPI), and load price levels (World Bank) and Canadian travel advisories. See [backend/README.md](backend/README.md).
- `site/`: the static test site served by GitHub Pages. `python -m tripfinder export` writes `site/data.json`, and `site/engine.js` prices trips in the browser. A parity test (`node --test site/tests/parity.test.mjs`) checks it against the Python engine.
- `docs/`: spec, plan, data coverage report and [proof-of-concept report](docs/poc-report.md).

## How the test site stays fresh

`.github/workflows/pages.yml` runs every day and on every push to `main`:
1. Restores the database from the GitHub Actions cache.
2. Runs `refresh auto`: flights daily, hotels weekly, reference data monthly, and a full rebuild if the cache is gone.
3. Exports `site/data.json` and runs both test suites.
4. Deploys.

It needs two repository secrets, `TRAVELPAYOUTS_TOKEN` and `LITEAPI_KEY`. Without them it deploys the committed snapshot. To force a step, run the workflow manually with, for example, `force: hotels`.

The committed `site/data.json` is only a fallback. To update it by hand:

```bash
cd backend
uv run python -m tripfinder refresh auto
uv run python -m tripfinder export
```
