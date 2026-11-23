"""Refresh jobs. Plain functions so a cron, GitHub Actions or Prefect can call them unchanged."""

from __future__ import annotations

import csv
import sqlite3
import statistics
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
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
    conn.commit()
    return {"price_levels": len(levels), "advisories": len(advisories)}


def select_destinations(conn: sqlite3.Connection, s: Settings) -> list[str]:
    """Pick the launch destinations: the ones with the most cached fares from the origin."""
    meter = Meter(conn, "select")
    counts: Counter[str] = Counter()
    for month in upcoming_months(s.months_ahead):
        counts.update(f.destination for f in p.fetch_fares(meter, s, month))
    cities = {c["code"]: c for c in p.fetch_cities(meter)}
    # Never recommend countries where Canada advises avoiding non-essential (2) or all (3) travel.
    blocked = {r["country_code"] for r in conn.execute("SELECT country_code FROM advisories WHERE level >= 2")}
    if not blocked:
        raise RuntimeError("no advisories loaded: run `refresh reference` before `select`")
    chosen: list[str] = []
    conn.execute("UPDATE destinations SET selected = 0")
    for code, n in counts.most_common():
        c = cities.get(code)
        if not c or not c.get("coordinates") or code == s.origin or c["country_code"] in blocked:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO destinations VALUES (?,?,?,?,?,?,?)",
            (code, c["name"], c["country_code"], c["coordinates"]["lat"], c["coordinates"]["lon"], n, int(len(chosen) < s.destinations)),
        )
        if len(chosen) < s.destinations:
            chosen.append(code)
    conn.commit()
    return chosen


def _selected(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM destinations WHERE selected = 1 ORDER BY fares_seen DESC").fetchall()


def refresh_flights(conn: sqlite3.Connection, s: Settings) -> dict[str, int]:
    """Per destination and month: cached round-trip fares. Free; run daily."""
    meter = Meter(conn, "flights")
    today = date.today()
    conn.execute("DELETE FROM fares WHERE depart < ?", (today.isoformat(),))
    rows = 0
    for d in _selected(conn):
        for month in upcoming_months(s.months_ahead):
            fares = p.fetch_fares(meter, s, month, destination=d["code"])
            conn.executemany(
                "INSERT OR REPLACE INTO fares VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (f.destination, f.depart.isoformat(), f.ret.isoformat(), f.price, s.currency, f.airline, f.transfers, f.link, f.found_on.isoformat(), _now())
                    for f in fares
                ],
            )
            rows += len(fares)
    conn.commit()
    return {"fares": rows}


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


def rebuild_bands(conn: sqlite3.Connection, min_sample: int = 5) -> int:
    """Nightly price per room by destination, month and tier: 25th percentile / median / 75th percentile."""
    groups: dict[tuple[str, str, str, str], list[float]] = {}
    as_of: dict[tuple[str, str], str] = {}
    for r in conn.execute("SELECT destination, checkin, nights, stars, total, currency, fetched_at FROM hotel_prices"):
        tier = tier_for(r["stars"])
        if tier is None:
            continue
        month = r["checkin"][:7]
        groups.setdefault((r["destination"], month, tier, r["currency"]), []).append(r["total"] / r["nights"])
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
        n += 1
    conn.commit()
    return n
