"""Pure pricing engine: package = flights + lodging + daily spend, each as a low/expected/high range.

Nothing here does I/O. Inputs are plain dataclasses that the data layer fills from the database.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .money import Money, PriceRange

TIERS = ("budget", "mid", "upscale")

# Per-person daily spend in Canada (food, local transport, incidentals), CAD.
# Assumption for the POC, scaled abroad by the World Bank price level. Label: estimated.
DAILY_BASE_CAD = {"budget": 80, "mid": 140, "upscale": 240}
CHILD_DAILY_SHARE = Decimal("0.7")

# Fallback nightly room rate in Canada when no hotel sample exists, scaled the same way. Label: estimated.
NIGHTLY_BASE_CAD = {"budget": 130, "mid": 210, "upscale": 380}

NIGHTS_SEARCH = range(14, 2, -1)  # when the user gives no length: try 14 nights down to 3
NIGHTS_TOLERANCE = 2  # a cached fare counts as "this length" if within +/- 2 nights


@dataclass(frozen=True)
class TripRequest:
    budget: Money
    adults: int
    children: int = 0
    month: str | None = None  # "YYYY-MM"; None = any month with data
    nights: int | None = None  # None = longest trip that fits the budget
    tier: str = "mid"
    sort: str = "cheapest"  # cheapest | most_nights

    def __post_init__(self) -> None:
        if self.adults < 1:
            raise ValueError("at least one adult")
        if self.children < 0:
            raise ValueError("children cannot be negative")
        if self.tier not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}")
        if self.nights is not None and not 1 <= self.nights <= 30:
            raise ValueError("nights must be 1-30")

    @property
    def travellers(self) -> int:
        return self.adults + self.children


@dataclass(frozen=True)
class Fare:
    """One cached round-trip fare, per person."""

    destination: str
    depart: date
    ret: date
    price: Money
    found_on: date  # when a user search last saw this price
    airline: str = ""
    transfers: int = 0
    link: str = ""

    @property
    def nights(self) -> int:
        return (self.ret - self.depart).days

    @property
    def month(self) -> str:
        return self.depart.strftime("%Y-%m")


@dataclass(frozen=True)
class LodgingBand:
    """Nightly price per room for one destination, month and tier."""

    nightly: PriceRange
    sample_size: int
    as_of: date
    source: str = "liteapi"


@dataclass
class DestinationData:
    code: str
    name: str
    country_code: str
    fares: list[Fare]
    bands: dict[tuple[str, str], LodgingBand] = field(default_factory=dict)  # (month, tier) -> band
    price_level: Decimal | None = None  # destination price level / Canada price level


@dataclass(frozen=True)
class Component:
    name: str
    total: PriceRange
    confidence: str
    detail: str


@dataclass
class Package:
    destination: DestinationData
    nights: int
    month: str
    fare: Fare | None
    components: list[Component]
    total: PriceRange
    fit: str  # within | stretch | over

    def per_person(self, travellers: int) -> PriceRange:
        return self.total * (Decimal(1) / Decimal(travellers))


def rooms_needed(adults: int, children: int) -> int:
    """Two adults per room, rounded up; a room takes at most four people including children."""
    return max(math.ceil(adults / 2), math.ceil((adults + children) / 4), 1)


def _ordered(low: Money, expected: Money, high: Money) -> PriceRange:
    lo, ex, hi = sorted([low, expected, high], key=lambda m: m.amount)
    return PriceRange(lo, ex, hi)


def flight_component(fares: list[Fare], req: TripRequest, nights: int, month: str, today: date) -> tuple[Component, Fare] | None:
    in_month = [f for f in fares if f.month == month]
    if not in_month:
        return None
    matching = [f for f in in_month if abs(f.nights - nights) <= NIGHTS_TOLERANCE]
    exact = bool(matching)
    pool = sorted(matching or in_month, key=lambda f: (f.price.amount, f.depart, f.ret))  # deterministic ties
    prices = [f.price for f in pool]
    best = pool[0]
    expected = Money(Decimal(str(statistics.median(p.amount for p in prices[:3]))), best.price.currency)
    # Cached fares can be up to a week old and are the cheapest seen, so the top of the range is padded.
    pad = Decimal("1.15") if exact else Decimal("1.35")
    high = max(prices[:5], key=lambda m: m.amount) * pad
    per_person = _ordered(best.price, expected, high)
    age = (today - best.found_on).days
    confidence = f"cached ({age}d)" if exact else "estimated"
    detail = (
        f"{len(pool)} cached fares, cheapest {best.price} pp on {best.depart:%b %d}, {best.nights} nights"
        + ("" if exact else f" (no fare near {nights} nights; used nearest dates)")
    )
    return Component("flights", per_person * req.travellers, confidence, detail), best


def lodging_component(dest: DestinationData, req: TripRequest, nights: int, month: str, today: date) -> Component:
    rooms = rooms_needed(req.adults, req.children)
    band = dest.bands.get((month, req.tier)) or _nearest_band(dest, month, req.tier)
    if band is not None:
        age = (today - band.as_of).days
        label = f"sampled ({age}d)" if band.source == "liteapi" else "estimated"
        detail = f"{rooms} room(s) x {nights} nights, {req.tier} tier, from {band.sample_size} hotel prices"
        return Component("lodging", band.nightly * (rooms * nights), label, detail)
    level = dest.price_level or Decimal(1)
    base = Money.of(NIGHTLY_BASE_CAD[req.tier]) * level
    nightly = PriceRange(base * Decimal("0.7"), base, base * Decimal("1.5"))
    return Component("lodging", nightly * (rooms * nights), "estimated", f"{rooms} room(s), no hotel sample; scaled Canadian average")


def _nearest_band(dest: DestinationData, month: str, tier: str) -> LodgingBand | None:
    same_tier = sorted(m for (m, t) in dest.bands if t == tier)
    if not same_tier:
        return None
    nearest = min(same_tier, key=lambda m: abs(_month_index(m) - _month_index(month)))
    return dest.bands[(nearest, tier)]


def _month_index(month: str) -> int:
    y, m = month.split("-")
    return int(y) * 12 + int(m)


def daily_component(dest: DestinationData, req: TripRequest, nights: int) -> Component:
    level = dest.price_level if dest.price_level is not None else Decimal(1)
    per_adult_day = Money.of(DAILY_BASE_CAD[req.tier]) * level
    people = Decimal(req.adults) + Decimal(req.children) * CHILD_DAILY_SHARE
    days = nights + 1
    expected = per_adult_day * (people * days)
    rng = PriceRange(expected * Decimal("0.75"), expected, expected * Decimal("1.3"))
    src = f"price level {level:.2f} x Canada" if dest.price_level is not None else "no price level; Canadian average"
    return Component("daily", rng, "estimated", f"{per_adult_day} per adult per day, {days} days ({src})")


def price_package(dest: DestinationData, req: TripRequest, nights: int, month: str, today: date) -> Package | None:
    flight = flight_component(dest.fares, req, nights, month, today)
    if flight is None:
        return None  # no flight data means the trip can't be priced
    flights, fare = flight
    if abs(fare.nights - nights) <= NIGHTS_TOLERANCE:
        nights = fare.nights  # price the stay the fare actually allows
    comps = [flights, lodging_component(dest, req, nights, month, today), daily_component(dest, req, nights)]
    total = PriceRange.zero(req.budget.currency)
    for c in comps:
        total = total + c.total
    if total.expected <= req.budget:
        fit = "within"
    elif total.low <= req.budget:
        fit = "stretch"
    else:
        fit = "over"
    return Package(dest, nights, month, fare, comps, total, fit)


def best_package(dest: DestinationData, req: TripRequest, today: date) -> Package | None:
    """Cheapest month (or the requested one) and, without a fixed length, the longest trip that fits."""
    months = [req.month] if req.month else sorted({f.month for f in dest.fares})
    candidates: list[Package] = []
    for month in months:
        if req.nights is not None:
            pkg = price_package(dest, req, req.nights, month, today)
        else:
            # Only lengths a cached fare actually offers, longest first; stop at the first that fits.
            lengths = sorted({f.nights for f in dest.fares if f.month == month and f.nights in NIGHTS_SEARCH}, reverse=True)
            pkg = None
            for n in lengths:
                p = price_package(dest, req, n, month, today)
                if p is None:
                    break
                pkg = p
                if p.fit == "within":
                    break
        if pkg is not None:
            candidates.append(pkg)
    if not candidates:
        return None
    order = {"within": 0, "stretch": 1, "over": 2}
    return min(candidates, key=lambda p: (order[p.fit], -p.nights if req.nights is None else 0, p.total.expected.amount))


def rank(packages: list[Package], req: TripRequest, include_stretch: bool = True) -> list[Package]:
    keep = [p for p in packages if p.fit == "within" or (include_stretch and p.fit == "stretch")]
    if req.sort == "most_nights":
        key = lambda p: (p.fit != "within", -p.nights, p.total.expected.amount)
    else:
        key = lambda p: (p.fit != "within", p.total.expected.amount)
    return sorted(keep, key=key)
