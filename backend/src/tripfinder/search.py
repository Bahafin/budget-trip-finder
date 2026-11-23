"""Glue between storage and the engine: load destination data, run a search, shape results for the CLI and web."""

from __future__ import annotations

import csv
import sqlite3
import urllib.parse
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from .config import Settings
from .engine import (
    DestinationData,
    Fare,
    LodgingBand,
    Package,
    TripRequest,
    best_package,
    rank,
    rooms_needed,
)
from .money import Money, PriceRange


def load_destinations(conn: sqlite3.Connection, today: date | None = None) -> list[DestinationData]:
    today = today or date.today()
    levels = {r["country_code"]: Decimal(str(r["ratio_to_usd"])) for r in conn.execute("SELECT * FROM price_levels")}
    canada = levels.get("CA")
    fares: dict[str, list[Fare]] = defaultdict(list)
    for r in conn.execute("SELECT * FROM fares WHERE depart >= ?", (today.isoformat(),)):
        fares[r["destination"]].append(
            Fare(
                r["destination"], date.fromisoformat(r["depart"]), date.fromisoformat(r["ret"]),
                Money.of(r["price"], r["currency"]), date.fromisoformat(r["found_on"]),
                r["airline"] or "", r["transfers"] or 0, r["link"] or "",
            )
        )
    bands: dict[str, dict[tuple[str, str], LodgingBand]] = defaultdict(dict)
    for r in conn.execute("SELECT * FROM lodging_bands"):
        rng = PriceRange(Money.of(r["nightly_low"], r["currency"]), Money.of(r["nightly_mid"], r["currency"]), Money.of(r["nightly_high"], r["currency"]))
        bands[r["destination"]][(r["month"], r["tier"])] = LodgingBand(rng, r["sample_size"], date.fromisoformat(r["as_of"]), r["source"])
    out = []
    for r in conn.execute("SELECT * FROM destinations WHERE selected = 1"):
        lvl = levels.get(r["country_code"])
        rel = (lvl / canada).quantize(Decimal("0.01")) if lvl and canada else None
        out.append(DestinationData(r["code"], r["name"], r["country_code"], fares[r["code"]], bands[r["code"]], rel))
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
        sep = "&" if "?" in fare.link else "?"
        links["flights"] = f"https://www.aviasales.com{fare.link}{sep}marker={s.travelpayouts_marker}"
    if fare:
        rooms = rooms_needed(req.adults, req.children)
        q = {"ss": d.name, "checkin": fare.depart.isoformat(), "checkout": fare.ret.isoformat(), "group_adults": req.adults, "group_children": req.children, "no_rooms": rooms}
        links["hotels"] = "https://www.booking.com/searchresults.html?" + urllib.parse.urlencode(q)  # affiliate id added once the program is joined
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
