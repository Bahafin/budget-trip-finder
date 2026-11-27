"""Glue between storage and the engine: load destination data, run a search, shape results for the CLI and web."""

from __future__ import annotations

import csv
import sqlite3
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from .config import ROOT, Settings
from .engine import (
    DestinationData,
    Fare,
    Ground,
    LodgingBand,
    Package,
    TripRequest,
    best_package,
    rank,
    rooms_needed,
    season_factor,
)
from .links import flight_link, hotel_link
from .money import Money, PriceRange


GROUND_CSV = ROOT / "data" / "seed" / "ground.csv"


def load_ground(path: Path = GROUND_CSV) -> dict[str, dict[str, tuple[str, Ground]]]:
    """data/seed/ground.csv: origin -> code -> (display name, how to get there without flying)."""
    out: dict[str, dict[str, tuple[str, Ground]]] = defaultdict(dict)
    if not path.exists():
        return out
    money = lambda v: Money.of(v) if (v or "").strip() else None  # noqa: E731
    with path.open(encoding="utf8") as f:
        for r in csv.DictReader(f):
            out[r["origin"]][r["code"]] = (r["name"], Ground(
                mode=r["mode"].strip(), fare=money(r["fare"]), hours=float(r["hours"] or 0), km=int(r["km"] or 0),
                drive_hours=float(r["drive_hours"] or 0), car_extra=money(r["car_extra"]),
                car_per_person=money(r["car_per_person"]), parking=money(r["parking"]),
                link=r["link"].strip(), partner=r["partner"].strip(),
            ))
    return out


def load_destinations(conn: sqlite3.Connection, today: date | None = None, origin: str = "YTO",
                      ground_csv: Path = GROUND_CSV) -> list[DestinationData]:
    """Destinations shown from one departure city, with that city's fares (hotels and prices are shared) and,
    for places in reach, how to get there by train, bus or car."""
    today = today or date.today()
    ground = load_ground(ground_csv).get(origin, {})
    levels = {r["country_code"]: Decimal(str(r["ratio_to_usd"])) for r in conn.execute("SELECT * FROM price_levels")}
    canada = levels.get("CA")
    # Seasonality: the city's daily hotel price index, and which nights each month's hotel sample used.
    index: dict[str, dict[date, float]] = defaultdict(dict)
    for r in conn.execute("SELECT destination, day, usd FROM price_index"):
        index[r["destination"]][date.fromisoformat(r["day"])] = r["usd"]
    samples: dict[str, dict[str, tuple[date, int]]] = defaultdict(dict)
    for r in conn.execute(
        "SELECT destination, substr(checkin, 1, 7) AS month, MIN(checkin) AS checkin, MAX(nights) AS nights "
        "FROM hotel_prices GROUP BY destination, month"
    ):
        samples[r["destination"]][r["month"]] = (date.fromisoformat(r["checkin"]), r["nights"])

    def season(dest: str, depart: date, ret: date) -> Decimal:
        months = samples.get(dest)
        if not months or not index.get(dest):
            return Decimal(1)
        key = depart.strftime("%Y-%m")
        if key not in months:  # nearest sampled month, as the lodging band lookup does
            key = min(months, key=lambda m: abs((int(m[:4]) * 12 + int(m[5:])) - (depart.year * 12 + depart.month)))
        start, nights = months[key]
        return season_factor(index[dest], start, nights, depart, (ret - depart).days)

    fares: dict[str, list[Fare]] = defaultdict(list)
    for r in conn.execute("SELECT * FROM fares WHERE depart >= ? AND origin = ?", (today.isoformat(), origin)):
        depart, ret = date.fromisoformat(r["depart"]), date.fromisoformat(r["ret"])
        fares[r["destination"]].append(
            Fare(
                r["destination"], depart, ret,
                Money.of(r["price"], r["currency"]), date.fromisoformat(r["found_on"]),
                r["airline"] or "", r["transfers"] or 0, r["link"] or "",
                season(r["destination"], depart, ret),
            )
        )
    bands: dict[str, dict[tuple[str, str], LodgingBand]] = defaultdict(dict)
    for r in conn.execute("SELECT * FROM lodging_bands"):
        rng = PriceRange(Money.of(r["nightly_low"], r["currency"]), Money.of(r["nightly_mid"], r["currency"]), Money.of(r["nightly_high"], r["currency"]))
        bands[r["destination"]][(r["month"], r["tier"])] = LodgingBand(rng, r["sample_size"], date.fromisoformat(r["as_of"]), r["source"])
    out = []
    shown = {r[0] for r in conn.execute("SELECT code FROM selection WHERE origin = ?", (origin,))}
    for r in conn.execute("SELECT * FROM destinations WHERE selected = 1"):
        if shown and r["code"] not in shown:
            continue
        lvl = levels.get(r["country_code"])
        rel = (lvl / canada).quantize(Decimal("0.01")) if lvl and canada else None
        name, g = ground.get(r["code"], (r["name"], None))
        out.append(DestinationData(r["code"], name, r["country_code"], fares[r["code"]], bands[r["code"]], rel, g))
    return out


def search(conn: sqlite3.Connection, req: TripRequest, today: date | None = None) -> list[Package]:
    today = today or date.today()
    pkgs = [best_package(d, req, today) for d in load_destinations(conn, today)]
    return rank([p for p in pkgs if p is not None], req)


def load_notes(seed_dir: Path) -> dict[str, list[dict[str, str]]]:
    notes: dict[str, list[dict[str, str]]] = defaultdict(list)
    path = seed_dir / "know_before_you_go.csv"
    if path.exists():
        with path.open(encoding="utf8") as f:
            for row in csv.DictReader(f):
                notes[row["country_code"]].append(row)
    return notes


def to_dict(pkg: Package, req: TripRequest, conn: sqlite3.Connection, s: Settings, notes: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    d = pkg.destination
    adv = conn.execute("SELECT * FROM advisories WHERE country_code = ?", (d.country_code,)).fetchone()
    fare = pkg.fare
    links: dict[str, str] = {}
    if fare and fare.link:
        links["flights"] = flight_link(s, fare.link, d.code)
    if fare:
        rooms = rooms_needed(req.adults, req.children)
        hotel = hotel_link(s, d.name, d.country_code, d.code, fare.depart.isoformat(), fare.ret.isoformat(), req.adults, req.children, rooms)
        links["hotels"] = hotel["url"]
        links["hotels_partner"] = hotel["partner"]
    return {
        "code": d.code,
        "name": d.name,
        "country": d.country_code,
        "nights": pkg.nights,
        "month": pkg.month,
        "dates": {"depart": fare.depart.isoformat(), "return": fare.ret.isoformat()} if fare else None,
        "fit": pkg.fit,
        "total": pkg.total.as_dict(),
        "per_person": pkg.per_person(req.travellers).as_dict(),
        "currency": pkg.total.currency,
        "components": [{"name": c.name, **c.total.as_dict(), "confidence": c.confidence, "detail": c.detail} for c in pkg.components],
        "advisory": {"level": adv["level"], "text": adv["text"], "url": adv["url"]} if adv else None,
        "know_before": notes.get(d.country_code, []),
        "links": links,
    }
