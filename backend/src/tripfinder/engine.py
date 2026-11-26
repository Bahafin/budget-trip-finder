"""Pure pricing engine: package = flights + lodging + daily spend, each as a low/expected/high range.

Nothing here does I/O. Inputs are plain dataclasses that the data layer fills from the database.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal

from .money import Money, PriceRange

TIERS = ("budget", "mid", "upscale")

# Per-person daily spend in Canada (food, local transport, incidentals), CAD.
# Assumption for the POC, scaled abroad by the World Bank price level. Label: estimated.
DAILY_BASE_CAD = {"budget": 80, "mid": 140, "upscale": 240}
CHILD_DAILY_SHARE = Decimal("0.7")

# Fallback nightly room rate in Canada when no hotel sample exists, scaled the same way. Label: estimated.
NIGHTLY_BASE_CAD = {"budget": 130, "mid": 210, "upscale": 380}

MIN_NIGHTS = 3  # without a requested length, shorter fares are ignored: results should look like holidays
NIGHTS_SEARCH = range(14, MIN_NIGHTS - 1, -1)  # when the user gives no length: try 14 nights down to 3
NIGHTS_TOLERANCE = 2  # a cached fare counts as "this length" if within +/- 2 nights

# Flight range around the cheapest cached fare for the trip's dates: low, and (expected, high) lifts.
# Second key is False when no fare is near the requested length and nearby dates stand in.
FLIGHT_LOW_FACTOR = Decimal("0.95")
FLIGHT_LIFT = {True: (Decimal("1.10"), Decimal("1.35")), False: (Decimal("1.20"), Decimal("1.60"))}


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
    # Hotel price for these dates relative to the dates our hotel sample used (city price index); 1 = no data.
    season: Decimal = Decimal(1)

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


SEASON_MIN, SEASON_MAX = Decimal("0.6"), Decimal("2.0")
# Share of the city index's swing applied to our tier bands. The index averages all hotels, including
# luxury ones that swing harder. Calibrated 2026-11-26 on two Booking.com checks (Cancun New Year,
# Edmonton Christmas): 0.5 gave -5% / +12% against -34% / -2% with none and +24% / +27% with all of it.
# Recheck in Gate A.
SEASON_WEIGHT = 0.5


def season_factor(index: dict[date, float], sample_start: date, sample_nights: int, start: date, nights: int) -> Decimal:
    """How much pricier (or cheaper) hotels are on the trip's nights than on the nights our hotel sample used,
    from a city's daily price index. 1 when either window has less than half its days covered."""
    trip = [index[d] for d in (start + timedelta(days=i) for i in range(nights)) if d in index]
    base = [index[d] for d in (sample_start + timedelta(days=i) for i in range(sample_nights)) if d in index]
    if len(trip) * 2 < nights or len(base) * 2 < sample_nights or not trip or not base:
        return Decimal(1)
    raw = (sum(trip) / len(trip)) / (sum(base) / len(base))
    ratio = Decimal(str(round(1 + (raw - 1) * SEASON_WEIGHT, 2)))
    return min(max(ratio, SEASON_MIN), SEASON_MAX)


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
    shortest = 1 if req.nights is not None else MIN_NIGHTS
    matching = [f for f in in_month if abs(f.nights - nights) <= NIGHTS_TOLERANCE and f.nights >= shortest]
    exact = bool(matching)
    pool = sorted(matching or in_month, key=lambda f: (f.price.amount, f.depart, f.ret))  # deterministic ties
    prices = [f.price for f in pool]
    best = pool[0]
    # The estimate is anchored on the fare for the trip's own dates (validation 2026-11-24: a median across
    # other dates overshot by up to 38%). Cached fares are the cheapest seen and up to a week old, so the
    # expected price sits a little above them; other dates in the month only widen the top of the range.
    lift_expected, lift_high = FLIGHT_LIFT[exact]
    expected = best.price * lift_expected
    high = max([best.price * lift_high, *prices[:5]], key=lambda m: m.amount)
    per_person = _ordered(best.price * FLIGHT_LOW_FACTOR, expected, high)
    age = max(0, (today - best.found_on).days)  # data stamped in UTC can be "tomorrow" locally
    confidence = f"cached ({age}d)" if exact else "estimated"
    detail = (
        f"{len(pool)} cached fares, cheapest {best.price} pp on {best.depart:%b %d}, {best.nights} nights"
        + ("" if exact else f" (no fare near {nights} nights; used nearest dates)")
    )
    if not exact:
        # No fare of this length: the price is an estimate from other dates, so the trip keeps the requested
        # length (return = depart + nights) and drops the cached link, which would open different dates.
        best = replace(best, ret=best.depart + timedelta(days=nights), link="")
    return Component("flights", per_person * req.travellers, confidence, detail), best


def lodging_component(
    dest: DestinationData, req: TripRequest, nights: int, month: str, today: date, season: Decimal = Decimal(1)
) -> Component:
    rooms = rooms_needed(req.adults, req.children)
    band = dest.bands.get((month, req.tier)) or _nearest_band(dest, month, req.tier)
    if band is not None:
        age = max(0, (today - band.as_of).days)
        label = f"sampled ({age}d)" if band.source == "liteapi" else "estimated"
        detail = f"{rooms} room(s) x {nights} nights, {req.tier} tier, from {band.sample_size} hotel prices"
        if season != 1:
            detail += f", dates priced x{season:.2f} vs sample dates"
        return Component("lodging", band.nightly * (rooms * nights) * season, label, detail)
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
    comps = [flights, lodging_component(dest, req, nights, month, today, fare.season), daily_component(dest, req, nights)]
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
