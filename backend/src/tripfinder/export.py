"""Export a static data snapshot for the browser version (GitHub Pages).

Only derived data goes out: per-destination fares, lodging bands (percentiles, never per-hotel prices),
price levels relative to Canada, advisories and our own notes. No keys, no raw hotel rows.
"""

from __future__ import annotations

import csv

import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

from .config import Settings
from .engine import (
    CHILD_DAILY_SHARE,
    DAILY_BASE_CAD,
    FLIGHT_LIFT,
    FLIGHT_LOW_FACTOR,
    MIN_NIGHTS,
    NIGHTLY_BASE_CAD,
    NIGHTS_TOLERANCE,
)
from .links import flight_link, flight_search_link, hotel_link
from .search import load_destinations, load_notes


THEMES = ("beach", "city", "culture", "food", "family", "nature")


def load_themes(seed_dir) -> dict[str, dict]:
    """Hand-written per destination (data/seed/themes.csv): theme tags, a "best for" label and a "what to do" line."""
    path = seed_dir / "themes.csv"
    if not path.exists():
        return {}
    out = {}
    for r in csv.DictReader(path.open(encoding="utf8")):
        tags = [t.strip() for t in r["themes"].split(";") if t.strip()]
        unknown = set(tags) - set(THEMES)
        if unknown:
            raise ValueError(f"themes.csv {r['code']}: unknown theme(s) {sorted(unknown)}")
        out[r["code"]] = {"themes": tags, "bestFor": r["best_for"], "todo": r["todo"]}
    return out


def build_snapshot(conn: sqlite3.Connection, s: Settings, today: date | None = None) -> dict:
    today = today or date.today()
    dests = load_destinations(conn, today)
    countries = {d.country_code for d in dests}
    advisories = {
        r["country_code"]: {"level": r["level"], "text": r["text"], "url": r["url"]}
        for r in conn.execute("SELECT * FROM advisories")
        if r["country_code"] in countries
    }
    notes = {c: v for c, v in load_notes(s.seed_dir).items() if c in countries}
    airlines = {r["code"]: r["name"] for r in conn.execute("SELECT * FROM airlines")}
    themes = load_themes(s.seed_dir)
    out_dests = []
    for d in dests:
        out_dests.append(
            {
                "code": d.code,
                "name": d.name,
                "country": d.country_code,
                "priceLevel": float(d.price_level) if d.price_level is not None else None,
                **themes.get(d.code, {"themes": [], "bestFor": "", "todo": ""}),
                # "Check hotels" link; the browser fills {checkin} {checkout} {adults} {children} {rooms}.
                # Flight search for trips with no cached fare of that length; the browser fills {dep} {ret} {pax}.
                "flightSearch": flight_search_link(s, d.code),
                "hotel": hotel_link(s, d.name, d.country_code, d.code, "{checkin}", "{checkout}", "{adults}", "{children}", "{rooms}"),
                "fares": [
                    {
                        "depart": f.depart.isoformat(),
                        "ret": f.ret.isoformat(),
                        "price": float(f.price.amount),
                        "foundOn": f.found_on.isoformat(),
                        "link": flight_link(s, f.link, d.code) if f.link else "",
                        "airline": airlines.get(f.airline, f.airline),
                        "transfers": f.transfers,
                        "season": float(f.season),
                    }
                    for f in sorted(d.fares, key=lambda f: (f.depart, f.price.amount))
                ],
                "bands": [
                    {
                        "month": m,
                        "tier": t,
                        "low": float(b.nightly.low.amount),
                        "mid": float(b.nightly.expected.amount),
                        "high": float(b.nightly.high.amount),
                        "n": b.sample_size,
                        "asOf": b.as_of.isoformat(),
                        "source": b.source,
                    }
                    for (m, t), b in sorted(d.bands.items())
                ],
            }
        )
    return {
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "currency": s.currency,
        "origin": s.origin,
        "constants": {
            "dailyBase": DAILY_BASE_CAD,
            "nightlyBase": NIGHTLY_BASE_CAD,
            "childDailyShare": float(CHILD_DAILY_SHARE),
            "nightsTolerance": NIGHTS_TOLERANCE,
            "minNights": MIN_NIGHTS,
            "flightLow": float(FLIGHT_LOW_FACTOR),
            "flightLift": {"exact": [float(x) for x in FLIGHT_LIFT[True]], "nearby": [float(x) for x in FLIGHT_LIFT[False]]},
        },
        "destinations": out_dests,
        "advisories": advisories,
        "notes": notes,
        "themes": list(THEMES),
    }


def write_snapshot(conn: sqlite3.Connection, s: Settings, out: Path) -> dict[str, int]:
    snap = build_snapshot(conn, s)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snap, separators=(",", ":"), ensure_ascii=False)
    out.write_text(text, encoding="utf8")
    return {"destinations": len(snap["destinations"]), "bytes": len(text.encode())}


# Requests the browser engine must price exactly like the Python engine (checked by site/tests/parity.test.mjs).
GOLDEN_REQUESTS = [
    {"budget": 3000, "adults": 2},
    {"budget": 3000, "adults": 2, "month": None, "nights": 7},
    {"budget": 6000, "adults": 2, "children": 2, "nights": 7, "tier": "budget"},
    {"budget": 1500, "adults": 1, "tier": "budget", "sort": "most_nights"},
    {"budget": 9000, "adults": 3, "children": 1, "tier": "upscale"},
    {"budget": 2500, "adults": 2, "nights": 5},
]


def write_golden(conn: sqlite3.Connection, s: Settings, out: Path) -> int:
    from .engine import TripRequest
    from .money import Money
    from .search import search

    snap_today = date.today()
    cases = []
    for r in GOLDEN_REQUESTS:
        req = TripRequest(
            Money.of(r["budget"]), r["adults"], r.get("children", 0), r.get("month"), r.get("nights"),
            r.get("tier", "mid"), r.get("sort", "cheapest"),
        )
        results = search(conn, req, snap_today)
        cases.append(
            {
                "request": r,
                "results": [
                    {"code": p.destination.code, "nights": p.nights, "month": p.month, "fit": p.fit, **p.total.as_dict()}
                    for p in results
                ],
            }
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"today": snap_today.isoformat(), "cases": cases}, indent=1), encoding="utf8")
    return len(cases)
