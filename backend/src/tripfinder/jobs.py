"""Refresh jobs. Plain functions so a cron, GitHub Actions or Prefect can call them unchanged."""

from __future__ import annotations

import csv
import sqlite3
import statistics
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from . import providers as p
from .config import Settings
from .meter import ApiError, Meter


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def upcoming_months(n: int, today: date | None = None) -> list[str]:
    """The next n calendar months, starting with next month."""
    d = (today or date.today()).replace(day=1)
    months = []
    for _ in range(n):
        d = (d + timedelta(days=32)).replace(day=1)
        months.append(d.strftime("%Y-%m"))
    return months


def refresh_reference(conn: sqlite3.Connection, s: Settings) -> dict[str, int]:
    """Price levels (World Bank) and travel advisories (Global Affairs Canada). Monthly is plenty."""
    meter = Meter(conn, "reference")
    levels = p.fetch_price_levels(meter)
    conn.executemany(
        "INSERT OR REPLACE INTO price_levels VALUES (?,?,?,?)",
        [(c, ratio, year, _now()) for c, (ratio, year) in levels.items()],
    )
    advisories = p.fetch_advisories(meter)
    conn.executemany(
        "INSERT OR REPLACE INTO advisories VALUES (?,?,?,?,?,?)",
        [(a.country_code, a.level, a.text, a.url, a.published, _now()) for a in advisories],
    )
    airlines = p.fetch_airlines(meter)
    conn.executemany("INSERT OR REPLACE INTO airlines VALUES (?,?)", list(airlines.items()))
    conn.commit()
    return {"price_levels": len(levels), "advisories": len(advisories), "airlines": len(airlines)}


def origins(s: Settings) -> list[dict[str, str]]:
    """Departure cities (data/seed/origins.csv): code, name, slug. Without the file, just the settings origin."""
    path = s.seed_dir / "origins.csv"
    if not path.exists():
        return [{"code": s.origin, "name": "Toronto", "slug": "toronto"}]
    return [{"code": r["code"].strip(), "name": r["name"].strip(), "slug": r["slug"].strip()}
            for r in csv.DictReader(path.open(encoding="utf8")) if r["code"].strip()]


def pinned_pairs(s: Settings) -> dict[str, list[str]]:
    """The destination list per departure city, kept in the repo (data/seed/destinations.csv), so every machine
    shows the same places and a change to a list is a reviewed commit. Without the file, selection ranks."""
    path = s.seed_dir / "destinations.csv"
    if not path.exists():
        return {}
    out: dict[str, list[str]] = {}
    for r in csv.DictReader(path.open(encoding="utf8")):
        if r["code"].strip():
            out.setdefault((r.get("origin") or s.origin).strip(), []).append(r["code"].strip())
    return out


def pinned_list(s: Settings) -> list[str]:
    """Every pinned destination, across departure cities."""
    return sorted({c for codes in pinned_pairs(s).values() for c in codes})


def list_key(s: Settings) -> str:
    """What the current selection was made from; a change makes selection due."""
    pairs = pinned_pairs(s)
    pinned = ";".join(f"{o}={','.join(sorted(pairs[o]))}" for o in sorted(pairs))
    return "pinned:" + pinned + "|extra:" + ",".join(sorted(always_include(s)))


def always_include(s: Settings) -> list[str]:
    """Destinations picked by hand on top of the top-N by fare count (data/seed/always_include.csv)."""
    path = s.seed_dir / "always_include.csv"
    if not path.exists():
        return []
    return [r["code"].strip() for r in csv.DictReader(path.open(encoding="utf8")) if r["code"].strip()]


def add_extras(conn: sqlite3.Connection, s: Settings) -> list[str]:
    """Add the hand-picked destinations to the current selection without re-ranking the rest, so adding one
    place doesn't reshuffle the list (and the pages, themes and photos built around it)."""
    meter = Meter(conn, "extras")
    cities = {c["code"]: c for c in p.fetch_cities(meter)}
    blocked = {r["country_code"] for r in conn.execute("SELECT country_code FROM advisories WHERE level >= 2")}
    added = []
    for code in always_include(s):
        c = cities.get(code)
        if not c or not c.get("coordinates") or c["country_code"] in blocked:
            continue
        row = conn.execute("SELECT fares_seen FROM destinations WHERE code = ?", (code,)).fetchone()
        conn.execute(
            "INSERT OR REPLACE INTO destinations VALUES (?,?,?,?,?,?,1)",
            (code, c["name"], c["country_code"], c["coordinates"]["lat"], c["coordinates"]["lon"], row[0] if row else 0),
        )
        added.append(code)
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('always_include', ?)", (",".join(sorted(always_include(s))),))
    conn.commit()
    return added


KEEP_MIN_FARES = 5  # a selected place stays while our own per-place fare refresh still finds this many fares


def choose_destinations(counts: Counter[str], eligible: set[str], current: list[str], extras: list[str], n: int,
                        stored: dict[str, int] | None = None, keep_min: int = KEEP_MIN_FARES) -> list[str]:
    """Sticky selection. Places already on the list stay while they still have enough fares in our own table
    (`stored`, from the daily per-place refresh; the bulk counts in `counts` are small and noisy day to day,
    and each place carries pages, themes, a photo and Gate A trips). Only the gaps are filled from the bulk
    fare-count ranking. Hand-picked places are added on top."""
    have = stored if stored is not None else counts
    keep = [c for c in current if c not in extras and c in eligible and have.get(c, 0) >= keep_min][:n]
    for code, _ in counts.most_common():
        if len(keep) >= n:
            break
        if code in eligible and code not in keep and code not in extras:
            keep.append(code)
    return keep + [c for c in extras if c in eligible and counts[c] > 0 and c not in keep]


def select_destinations(conn: sqlite3.Connection, s: Settings) -> list[str]:
    """Pick the destinations: keep the current ones that still have fares, fill gaps with the places that have
    the most cached fares from the origin, and add the hand-picked ones in always_include.csv (all only if they
    aren't under an advisory)."""
    meter = Meter(conn, "select")
    counts: Counter[str] = Counter()
    for month in upcoming_months(s.months_ahead):
        counts.update(f.destination for f in p.fetch_fares(meter, s, month))
    cities = {c["code"]: c for c in p.fetch_cities(meter)}
    # Never recommend countries where Canada advises avoiding non-essential (2) or all (3) travel.
    blocked = {r["country_code"] for r in conn.execute("SELECT country_code FROM advisories WHERE level >= 2")}
    if not blocked:
        raise RuntimeError("no advisories loaded: run `refresh reference` before `select`")
    eligible = {
        code for code in counts
        if (c := cities.get(code)) and c.get("coordinates") and code != s.origin and c["country_code"] not in blocked
    }
    pairs = pinned_pairs(s)
    if pairs:
        pinned = pinned_list(s)
        eligible |= {c for c in pinned if (x := cities.get(c)) and x.get("coordinates") and x["country_code"] not in blocked}
        extras = [c for c in always_include(s) if c in eligible and c not in pinned]
        per_origin = {o: [c for c in codes if c in eligible and c != o] for o, codes in pairs.items()}
        per_origin.setdefault(s.origin, [])
        per_origin[s.origin] += [c for c in extras if c not in per_origin[s.origin]]
        chosen = sorted({c for codes in per_origin.values() for c in codes})
        _store_selection(conn, s, cities, eligible, counts, chosen)
        conn.execute("DELETE FROM selection")
        conn.executemany("INSERT OR IGNORE INTO selection VALUES (?, ?)",
                         [(o, c) for o, codes in per_origin.items() for c in codes])
        conn.commit()
        for o in per_origin:  # suggestions: busy routes from each departure city that aren't on its list
            oc: Counter[str] = Counter()
            for month in upcoming_months(s.months_ahead):
                oc.update(f.destination for f in p.fetch_fares(meter, replace(s, origin=o), month))
            suggest = [c for c, _ in oc.most_common(40) if (x := cities.get(c)) and x.get("coordinates")
                       and x["country_code"] not in blocked and c not in per_origin[o] and c != o][:5]
            if suggest:
                print(f"busy routes from {o} not on its list (add to data/seed/destinations.csv):", ", ".join(suggest))
        return chosen
    current = [r[0] for r in conn.execute("SELECT code FROM destinations WHERE selected = 1 ORDER BY fares_seen DESC")]
    stored = dict(conn.execute("SELECT destination, COUNT(*) FROM fares WHERE depart >= ? GROUP BY destination", (date.today().isoformat(),)).fetchall())
    eligible |= {c for c in current if (x := cities.get(c)) and x.get("coordinates") and x["country_code"] not in blocked}
    chosen = choose_destinations(counts, eligible, current, always_include(s), s.destinations, stored)
    _store_selection(conn, s, cities, eligible, counts, chosen)
    return chosen


def _store_selection(conn, s: Settings, cities, eligible: set[str], counts: Counter[str], chosen: list[str]) -> None:
    conn.execute("UPDATE destinations SET selected = 0")
    for code in eligible:
        c = cities[code]
        conn.execute(
            "INSERT OR REPLACE INTO destinations VALUES (?,?,?,?,?,?,?)",
            (code, c["name"], c["country_code"], c["coordinates"]["lat"], c["coordinates"]["lon"], counts[code], int(code in chosen)),
        )
    # Remember which lists this selection used, so a changed list triggers a new selection.
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('lists', ?)", (list_key(s),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('always_include', ?)", (",".join(sorted(always_include(s))),))
    conn.commit()


def _selected(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM destinations WHERE selected = 1 ORDER BY fares_seen DESC").fetchall()


def refresh_flights(conn: sqlite3.Connection, s: Settings) -> dict[str, int]:
    """Per destination and month: cached round-trip fares. Free; run daily."""
    meter = Meter(conn, "flights")
    today = date.today()
    conn.execute("DELETE FROM fares WHERE depart < ?", (today.isoformat(),))
    rows = 0
    for origin, code in conn.execute("SELECT origin, code FROM selection ORDER BY origin, code").fetchall():
        so = replace(s, origin=origin)
        for month in upcoming_months(s.months_ahead):
            fares = p.fetch_fares(meter, so, month, destination=code)
            conn.executemany(
                "INSERT OR REPLACE INTO fares VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (origin, f.destination, f.depart.isoformat(), f.ret.isoformat(), f.price, s.currency, f.airline,
                     f.transfers, f.link, f.found_on.isoformat(), _now())
                    for f in fares
                ],
            )
            rows += len(fares)
    conn.commit()
    return {"fares": rows, "history_rows": save_fare_history(conn, today)}


def save_fare_history(conn: sqlite3.Connection, today: date) -> int:
    """Keep what today's cache shows: cheapest fare per departure city, destination, month and trip length.
    The fares table only holds the current cache, and this history can't be rebuilt later (PLAN 1.9)."""
    nights = "CAST(julianday(ret) - julianday(depart) AS INTEGER)"
    conn.execute(
        f"INSERT OR REPLACE INTO fare_history SELECT ?, origin, destination, substr(depart, 1, 7), {nights}, "
        f"MIN(price), COUNT(*), currency FROM fares WHERE depart >= ? "
        f"GROUP BY origin, destination, substr(depart, 1, 7), {nights}, currency",
        (today.isoformat(), today.isoformat()),
    )
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM fare_history WHERE day = ?", (today.isoformat(),)).fetchone()[0]


def tier_for(stars: float | None) -> str | None:
    if stars is None:
        return None
    if stars < 3.5:
        return "budget"
    if stars < 4.5:
        return "mid"
    return "upscale"


def hotel_areas(s: Settings) -> dict[str, tuple[float, float, int]]:
    """Curated search centres for destinations whose hotels sit away from the city point (beach resorts)."""
    path = s.seed_dir / "hotel_areas.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf8") as f:
        return {r["code"]: (float(r["lat"]), float(r["lon"]), int(r["radius_m"])) for r in csv.DictReader(f)}


def refresh_hotels(conn: sqlite3.Connection, s: Settings, workers: int = 2, only: list[str] | None = None) -> dict[str, int]:
    """One sample search per destination and month (mid-month check-in), then rebuild the bands. Run weekly."""
    meter = Meter(conn, "hotels-partial" if only else "hotels")
    today = date.today()
    areas = hotel_areas(s)
    tasks = []
    for d in _selected(conn):
        if only and d["code"] not in only:
            continue
        for month in upcoming_months(s.months_ahead):
            checkin = max(date.fromisoformat(f"{month}-15"), today + timedelta(days=7))
            tasks.append((d, checkin))

    def run(task):
        d, checkin = task
        lat, lon, radius = areas.get(d["code"], (d["lat"], d["lon"], s.hotel_radius_m))
        try:
            prices = p.fetch_hotel_prices(meter, s, lat, lon, checkin, checkin + timedelta(days=s.hotel_sample_nights), radius)
            return d, checkin, prices
        except ApiError as e:
            return d, checkin, e

    errors = 0
    stored = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for d, checkin, result in pool.map(run, tasks):
            if isinstance(result, Exception):
                errors += 1
                continue
            conn.executemany(
                "INSERT OR REPLACE INTO hotel_prices VALUES (?,?,?,?,?,?,?,?,?)",
                [(d["code"], checkin.isoformat(), s.hotel_sample_nights, h.hotel_id, h.name, h.stars, h.total, h.currency, _now()) for h in result],
            )
            stored += len(result)
    conn.commit()
    bands = rebuild_bands(conn)
    return {"searches": len(tasks), "errors": errors, "hotel_prices": stored, "bands": bands}


SPIKE = 2.5  # a hotel priced over 2.5x its own median across sample dates is treated as a bad quote
ALL_INCLUSIVE = ("all inclusive", "all-inclusive", "allinclusive")


def is_all_inclusive(name: str | None) -> bool:
    n = (name or "").lower()
    return any(k in n for k in ALL_INCLUSIVE)


def rebuild_bands(conn: sqlite3.Connection, min_sample: int = 5, drop_all_inclusive: bool = True) -> int:
    """Nightly price per room by destination, month and tier: 25th percentile / median / 75th percentile.

    Two filters keep a small sample honest:
    - a hotel's price for one date more than SPIKE times its own median over all sampled dates is dropped
      (the sandbox sometimes quotes a hotel at 3-4x its usual rate);
    - all-inclusive resorts are left out, because their price includes meals and we count food in daily spending.
    """
    rows = conn.execute("SELECT destination, checkin, nights, hotel_id, hotel_name, stars, total, currency, fetched_at FROM hotel_prices").fetchall()
    per_hotel: dict[tuple[str, str], list[float]] = {}
    for r in rows:
        per_hotel.setdefault((r["destination"], r["hotel_id"]), []).append(r["total"] / r["nights"])
    hotel_median = {k: statistics.median(v) for k, v in per_hotel.items()}
    groups: dict[tuple[str, str, str, str], list[float]] = {}
    as_of: dict[tuple[str, str], str] = {}
    for r in rows:
        tier = tier_for(r["stars"])
        if tier is None or (drop_all_inclusive and is_all_inclusive(r["hotel_name"])):
            continue
        nightly = r["total"] / r["nights"]
        if nightly > SPIKE * hotel_median[(r["destination"], r["hotel_id"])]:
            continue
        month = r["checkin"][:7]
        groups.setdefault((r["destination"], month, tier, r["currency"]), []).append(nightly)
        as_of[(r["destination"], month)] = max(as_of.get((r["destination"], month), ""), r["fetched_at"][:10])
    conn.execute("DELETE FROM lodging_bands WHERE source = 'liteapi'")
    n = 0
    for (dest, month, tier, cur), prices in groups.items():
        if len(prices) < min_sample:
            continue
        q1, med, q3 = statistics.quantiles(prices, n=4)
        conn.execute(
            "INSERT OR REPLACE INTO lodging_bands VALUES (?,?,?,?,?,?,?,?,?,?)",
            (dest, month, tier, round(q1, 2), round(med, 2), round(q3, 2), cur, len(prices), "liteapi", as_of[(dest, month)]),
        )
        conn.execute(  # history of the bands, one row per day (PLAN 1.9)
            "INSERT OR REPLACE INTO band_history VALUES (?,?,?,?,?,?,?,?)",
            (date.today().isoformat(), dest, month, tier, round(q1, 2), round(med, 2), round(q3, 2), len(prices)),
        )
        n += 1
    conn.commit()
    return n


def index_city_names(s: Settings) -> dict[str, list[str]]:
    """City names to try with LiteAPI's price index when ours don't match (e.g. 'Denpasar (Bali)')."""
    path = s.seed_dir / "price_index_cities.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf8") as f:
        return {r["code"]: [c.strip() for c in r["cities"].split("|") if c.strip()] for r in csv.DictReader(f)}


def refresh_seasonality(conn: sqlite3.Connection, s: Settings, pause_s: float = 6.5) -> dict[str, int]:
    """Daily hotel price index per destination, a year ahead. The endpoint allows 10 calls a minute. Run weekly."""
    meter = Meter(conn, "seasonality")
    overrides = index_city_names(s)
    covered = days = 0
    first = True
    for d in _selected(conn):
        for city in [*overrides.get(d["code"], []), d["name"]]:
            if not first:
                time.sleep(pause_s)  # stay under 10 calls a minute
            first = False
            try:
                rows = p.fetch_price_index(meter, s, d["country_code"], city)
            except ApiError:
                rows = []
            if rows:
                conn.execute("DELETE FROM price_index WHERE destination = ?", (d["code"],))
                conn.executemany("INSERT INTO price_index VALUES (?,?,?,?)", [(d["code"], day, usd, _now()) for day, usd in rows])
                conn.commit()
                covered += 1
                days += len(rows)
                break
    return {"destinations": covered, "days": days}


# --- Scheduled entry point -------------------------------------------------------------------

# How old each dataset may get before `refresh auto` refreshes it.
MAX_AGE = {
    "reference": timedelta(days=25),  # World Bank, travel advisories
    "select": timedelta(days=30),  # destination list
    "flights": timedelta(hours=20),  # daily
    "hotels": timedelta(days=6),  # weekly
    "seasonality": timedelta(days=6),  # weekly (paid beta endpoint: about 25 calls a week)
}


def last_success(conn: sqlite3.Connection, job: str) -> datetime | None:
    row = conn.execute("SELECT MAX(at) FROM api_calls WHERE job = ? AND status BETWEEN 200 AND 399", (job,)).fetchone()
    return datetime.fromisoformat(row[0]) if row and row[0] else None


def due_steps(conn: sqlite3.Connection, now: datetime | None = None, extras: list[str] | tuple[str, ...] = (),
              pinned: list[str] | tuple[str, ...] = ()) -> dict[str, str]:
    """Which refresh steps are due and why. Empty tables always count as due, so a fresh database rebuilds itself."""
    now = now or datetime.now(UTC)
    count = lambda sql: conn.execute(sql).fetchone()[0]
    empty = {
        "reference": any(count(f"SELECT COUNT(*) FROM {t}") == 0 for t in ("advisories", "price_levels", "airlines")),
        "select": count("SELECT COUNT(*) FROM destinations WHERE selected = 1") == 0,
        "flights": count("SELECT COUNT(*) FROM fares") == 0,
        "hotels": count("SELECT COUNT(*) FROM lodging_bands") == 0,
        "seasonality": count("SELECT COUNT(*) FROM price_index") == 0,
    }
    due: dict[str, str] = {}
    for step, max_age in MAX_AGE.items():
        last = last_success(conn, step)
        if empty[step]:
            due[step] = "no data yet"
        elif last is None or now - last > max_age:
            due[step] = f"last refreshed {last:%Y-%m-%d %H:%M} UTC" if last else "never refreshed"
    if pinned:
        key = conn.execute("SELECT value FROM meta WHERE key = 'lists'").fetchone()
        want = pinned if isinstance(pinned, str) else "pinned:" + ",".join(sorted(pinned)) + "|extra:" + ",".join(sorted(extras))
        if key is None or key[0] != want:
            due.setdefault("select", "destination list in the repo changed")
    row = conn.execute("SELECT value FROM meta WHERE key = 'always_include'").fetchone()
    if extras and (row is None or row[0] != ",".join(sorted(extras))):
        due.setdefault("extras", "hand-picked destination list changed")
    if "select" in due or "extras" in due:
        # New destinations need fresh flights and hotels too.
        due.setdefault("flights", "destination list changed")
        due.setdefault("hotels", "destination list changed")
        due.setdefault("seasonality", "destination list changed")
    return due


def refresh_auto(conn: sqlite3.Connection, s: Settings, force: tuple[str, ...] = ()) -> dict[str, str]:
    """Run whatever is due, in dependency order. One failing step does not stop the others."""
    due = due_steps(conn, extras=always_include(s), pinned=list_key(s) if pinned_pairs(s) else ())
    for step in force:
        due.setdefault(step, "forced")
    steps = {
        "reference": refresh_reference,
        "select": select_destinations,
        "extras": add_extras,
        "flights": refresh_flights,
        "hotels": refresh_hotels,
        "seasonality": refresh_seasonality,
    }
    outcome: dict[str, str] = {}
    for step, fn in steps.items():
        if step not in due:
            outcome[step] = "skipped (fresh)"
            continue
        try:
            result = fn(conn, s)
            outcome[step] = f"ran ({due[step]}): {result if not isinstance(result, list) else f'{len(result)} destinations'}"
        except Exception as e:  # noqa: BLE001 - report and carry on; the export uses whatever data exists
            outcome[step] = f"FAILED ({due[step]}): {type(e).__name__}: {str(e)[:200]}"
    # Bands are derived from stored hotel prices, so rebuilding is free; doing it every run means a change to
    # the band rules reaches the site on the next run instead of waiting for the weekly hotel refresh.
    outcome["bands"] = f"rebuilt: {rebuild_bands(conn)}"
    return outcome
