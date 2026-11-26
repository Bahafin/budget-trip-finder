"""Gate A: the 50-trip accuracy test.

`generate` picks a varied set of trips the site would really show and writes a check sheet (CSV) with our
estimates and ready-made search links. People (or an agent in a browser) fill in the real prices.
`report` compares them and writes the error summary that decides Gate A (median total error within ~20-25%).
"""

from __future__ import annotations

import csv
import random
import statistics
import urllib.parse
from datetime import date
from pathlib import Path

from .engine import TripRequest, price_package, rooms_needed
from .money import Money
from .search import load_destinations

PARTIES = [(1, 0), (2, 0), (2, 0), (2, 0), (2, 1), (2, 2), (3, 0), (4, 0)]  # couples weighted up
TIERS = ["budget", "mid", "mid", "upscale"]

OUR_FIELDS = [
    "id", "destination", "name", "country", "depart", "return", "nights", "adults", "children", "rooms", "tier",
    "holiday", "flight_pp_low", "flight_pp_expected", "flight_pp_high", "hotel_night_low", "hotel_night_expected",
    "hotel_night_high", "daily_total", "total_low", "total_expected", "total_high", "google_flights_url", "booking_url",
]
REAL_FIELDS = ["real_flight_pp", "real_hotel_night", "real_checked_on", "real_source", "notes"]


def is_holiday(d: date) -> bool:
    """Christmas to New Year (Dec 20 - Jan 3) or Ontario March break (about Mar 7-22)."""
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 3) or (d.month == 3 and 7 <= d.day <= 22)


def google_flights_url(dest_name: str, depart: str, ret: str) -> str:
    q = f"Flights from Toronto to {dest_name} on {depart} through {ret}"
    return "https://www.google.com/travel/flights?" + urllib.parse.urlencode({"q": q, "curr": "CAD", "hl": "en", "gl": "ca"})


def booking_url(dest_name: str, depart: str, ret: str, adults: int, children: int, rooms: int, tier: str) -> str:
    stars = {"budget": "class%3D2%3Bclass%3D3", "mid": "class%3D4", "upscale": "class%3D5"}[tier]
    q = urllib.parse.urlencode({"ss": dest_name, "checkin": depart, "checkout": ret, "group_adults": adults,
                                "group_children": children, "no_rooms": rooms, "selected_currency": "CAD", "lang": "en-gb"})
    return f"https://www.booking.com/searchresults.html?{q}&nflt={stars}"


def generate(conn, n: int = 50, seed: int = 2026, today: date | None = None) -> list[dict]:
    today = today or date.today()
    rng = random.Random(seed)
    dests = [d for d in load_destinations(conn, today) if d.fares]
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    attempts = 0
    while len(rows) < n and attempts < n * 40:
        attempts += 1
        d = dests[len(rows) % len(dests)] if attempts <= n * 2 else rng.choice(dests)  # spread across destinations
        candidates = [f for f in d.fares if 3 <= f.nights <= 10 and (f.depart - today).days >= 7]
        if not candidates:
            continue
        months = sorted({c.month for c in candidates})
        month = rng.choice(months)  # pick the month first so December (most cached fares) does not dominate
        f = rng.choice([c for c in candidates if c.month == month])
        if (d.code, f.depart.isoformat()) in seen:
            continue
        adults, children = rng.choice(PARTIES)
        tier = rng.choice(TIERS)
        req = TripRequest(Money.of(10**6), adults, children, f.month, f.nights, tier)
        pkg = price_package(d, req, f.nights, f.month, today)
        if pkg is None or pkg.fare is None:
            continue
        seen.add((d.code, f.depart.isoformat()))
        fl, lo, da = pkg.components
        travellers = adults + children
        rooms = rooms_needed(adults, children)
        room_nights = pkg.nights * rooms
        dep, ret = pkg.fare.depart.isoformat(), pkg.fare.ret.isoformat()
        rows.append({
            "id": f"A{len(rows) + 1:02d}", "destination": d.code, "name": d.name, "country": d.country_code,
            "depart": dep, "return": ret, "nights": pkg.nights, "adults": adults, "children": children, "rooms": rooms,
            "tier": tier, "holiday": "yes" if is_holiday(pkg.fare.depart) or is_holiday(pkg.fare.ret) else "",
            "flight_pp_low": round(float(fl.total.low.amount) / travellers, 2),
            "flight_pp_expected": round(float(fl.total.expected.amount) / travellers, 2),
            "flight_pp_high": round(float(fl.total.high.amount) / travellers, 2),
            "hotel_night_low": round(float(lo.total.low.amount) / room_nights, 2),
            "hotel_night_expected": round(float(lo.total.expected.amount) / room_nights, 2),
            "hotel_night_high": round(float(lo.total.high.amount) / room_nights, 2),
            "daily_total": round(float(da.total.expected.amount), 2),
            "total_low": round(float(pkg.total.low.amount), 2),
            "total_expected": round(float(pkg.total.expected.amount), 2),
            "total_high": round(float(pkg.total.high.amount), 2),
            "google_flights_url": google_flights_url(d.name, dep, ret),
            "booking_url": booking_url(d.name, dep, ret, adults, children, rooms, tier),
        })
    return rows


def write_sheet(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=OUR_FIELDS + REAL_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**r, **{k: "" for k in REAL_FIELDS}})


def _err(ours: float, real: float) -> float:
    return (ours - real) / real


def _pct(xs: list[float], q: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, round(q * (len(s) - 1)))]


def summary(path: Path) -> dict | None:
    """Gate A results for the public method page: whole-trip and per-component errors, and each checked trip.

    Errors are (ours - real) / real. None when the sheet is missing or has no real prices yet.
    """
    if not path.exists():
        return None
    rows = [r for r in csv.DictReader(path.open(encoding="utf8")) if r["real_flight_pp"] and r["real_hotel_night"]]
    if not rows:
        return None
    comp: dict[str, list[float]] = {"flights": [], "hotel": [], "total": []}
    inside = {"flights": 0, "hotel": 0, "total": 0}
    trips = []
    for r in rows:
        t = int(r["adults"]) + int(r["children"])
        rf, rh = float(r["real_flight_pp"]), float(r["real_hotel_night"])
        real_total = rf * t + rh * int(r["nights"]) * int(r["rooms"]) + float(r["daily_total"])
        for k, ours, real, lo, hi in (
            ("flights", r["flight_pp_expected"], rf, r["flight_pp_low"], r["flight_pp_high"]),
            ("hotel", r["hotel_night_expected"], rh, r["hotel_night_low"], r["hotel_night_high"]),
            ("total", r["total_expected"], real_total, r["total_low"], r["total_high"]),
        ):
            comp[k].append(_err(float(ours), real))
            inside[k] += float(lo) <= real <= float(hi)
        trips.append({"code": r["destination"], "depart": r["depart"], "nights": int(r["nights"]), "holiday": bool(r["holiday"]),
                      "total_err": comp["total"][-1], "inside": float(r["total_low"]) <= real_total <= float(r["total_high"]),
                      "checked_on": r["real_checked_on"]})
    out: dict = {"n": len(rows), "checked_on": max(t["checked_on"] for t in trips), "trips": trips}
    for k, errs in comp.items():
        absx = [abs(e) for e in errs]
        out[k] = {"median": statistics.median(errs), "median_abs": statistics.median(absx), "p90_abs": _pct(absx, 0.9), "inside": inside[k]}
    return out


def report(path: Path) -> str:
    rows = list(csv.DictReader(path.open(encoding="utf8")))
    done = [r for r in rows if r["real_flight_pp"] and r["real_hotel_night"]]
    lines = [f"# Gate A report\n\nSheet: `{path.name}`. Checked {len(done)} of {len(rows)} trips.\n"]
    if not done:
        return "\n".join(lines + ["No real prices recorded yet."])
    comps = {"Flights (per person)": [], "Hotel (per night per room)": [], "Total (our daily spend in both)": []}
    in_range = {"Flights (per person)": 0, "Hotel (per night per room)": 0, "Total (our daily spend in both)": 0}
    detail = []
    for r in done:
        t = int(r["adults"]) + int(r["children"])
        rf, rh = float(r["real_flight_pp"]), float(r["real_hotel_night"])
        real_total = rf * t + rh * int(r["nights"]) * int(r["rooms"]) + float(r["daily_total"])
        pairs = [
            ("Flights (per person)", float(r["flight_pp_expected"]), rf, float(r["flight_pp_low"]), float(r["flight_pp_high"])),
            ("Hotel (per night per room)", float(r["hotel_night_expected"]), rh, float(r["hotel_night_low"]), float(r["hotel_night_high"])),
            ("Total (our daily spend in both)", float(r["total_expected"]), real_total, float(r["total_low"]), float(r["total_high"])),
        ]
        for name, ours, real, lo, hi in pairs:
            comps[name].append(_err(ours, real))
            in_range[name] += lo <= real <= hi
        detail.append((r["id"], r["name"], r["depart"], r["holiday"], _err(pairs[0][1], rf), _err(pairs[1][1], rh), _err(pairs[2][1], real_total)))
    lines.append("| Component | Median error | Median absolute error | 90th pct absolute error | Real price inside our range |")
    lines.append("|---|---|---|---|---|")
    for name, errs in comps.items():
        absx = [abs(e) for e in errs]
        lines.append(f"| {name} | {statistics.median(errs):+.0%} | {statistics.median(absx):.0%} | {_pct(absx, 0.9):.0%} | {in_range[name]} of {len(errs)} |")
    med_total = statistics.median([abs(e) for e in comps["Total (our daily spend in both)"]])
    verdict = "PASS" if med_total <= 0.20 else ("BORDERLINE" if med_total <= 0.25 else "FAIL")
    lines.append(f"\n**Gate A verdict on {len(done)} trips: {verdict}** (median absolute total error {med_total:.0%}; pass within about 20-25%). "
                 "Daily spend is our estimate on both sides, so it is not tested here.\n")
    hol = [abs(x[6]) for x in detail if x[3]]
    if hol:
        lines.append(f"Holiday trips: {len(hol)}, median absolute total error {statistics.median(hol):.0%}.\n")
    lines.append("| Trip | Destination | Depart | Holiday | Flights | Hotel | Total |\n|---|---|---|---|---|---|---|")
    for i, name, dep, hol_, ef, eh, et in detail:
        lines.append(f"| {i} | {name} | {dep} | {hol_} | {ef:+.0%} | {eh:+.0%} | {et:+.0%} |")
    return "\n".join(lines)
