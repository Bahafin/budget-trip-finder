# tripfinder (proof of concept)

Whole-trip budget packages from Toronto: cached flights (Aviasales), sampled hotel prices (LiteAPI), daily spend scaled by World Bank price levels, and Canadian travel advisories. Results: [docs/poc-report.md](../docs/poc-report.md).

## Setup

Needs `uv`. Keys go in the repo-root `.env` (copy `.env.example`): `TRAVELPAYOUTS_TOKEN`, `TRAVELPAYOUTS_MARKER`, `LITEAPI_KEY`.

```bash
cd backend
uv sync
```

## Fill the database (var/tripfinder.db)

```bash
uv run python -m tripfinder refresh reference
```

```bash
uv run python -m tripfinder select
```

```bash
uv run python -m tripfinder refresh flights
```

```bash
uv run python -m tripfinder refresh hotels
```

`refresh all` runs reference, flights and hotels in one go. To re-sample only some destinations: `refresh hotels --only LIR,PUJ`.

## Use it

```bash
uv run python -m tripfinder search --budget 3000 --adults 2 --month 2027-01
```

```bash
uv run python -m tripfinder costs
```

```bash
uv run python -m tripfinder serve
```

`serve` opens a local page at http://127.0.0.1:8000. Leave out `--nights` to get the longest trip that fits the budget.

## Tests

```bash
uv run pytest -q
```

## Curated data

- `data/seed/know_before_you_go.csv`: per-country notes written in our own words, each linking to travel.gc.ca.
- `data/seed/hotel_areas.csv`: hotel search centre and radius for resort destinations.
