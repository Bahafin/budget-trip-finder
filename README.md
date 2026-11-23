# Budget Trip Finder (prototype)

Enter a total trip budget and get whole trips from Toronto that fit: flights, hotel and daily spending, as a low / expected / high range in CAD.

**Try it:** https://bahafin.github.io/budget-trip-finder/ (prototype for user testing; prices are estimates, not quotes)

## How it works

- `backend/`: Python data jobs and the pricing engine. The jobs refresh cached fares (Aviasales), sample hotel prices (LiteAPI), and load price levels (World Bank) and Canadian travel advisories. See [backend/README.md](backend/README.md).
- `site/`: the static test site served by GitHub Pages. `python -m tripfinder export` writes `site/data.json`, and `site/engine.js` prices trips in the browser. A parity test (`node --test site/tests/parity.test.mjs`) checks it against the Python engine.
- `docs/`: spec, plan, data coverage report and [proof-of-concept report](docs/poc-report.md).

## Update the test site's data

```bash
cd backend
uv run python -m tripfinder refresh all
uv run python -m tripfinder export
```

Then commit `site/data.json` and `site/tests/golden.json`, and push. The Pages workflow runs the parity test and deploys.
