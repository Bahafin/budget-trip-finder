from datetime import date, timedelta
from decimal import Decimal

import pytest

from tripfinder.engine import (
    DestinationData,
    Fare,
    LodgingBand,
    TripRequest,
    best_package,
    price_package,
    rank,
    rooms_needed,
)
from tripfinder.money import CurrencyMismatch, Money, PriceRange

TODAY = date(2026, 11, 23)


def fare(price, depart=date(2027, 1, 10), nights=7, found=date(2026, 11, 20), dest="CUN"):
    return Fare(dest, depart, depart + timedelta(days=nights), Money.of(price), found)


def band(low, mid, high, n=40):
    return LodgingBand(PriceRange(Money.of(low), Money.of(mid), Money.of(high)), n, date(2026, 11, 22))


def dest(fares, bands=None, level=Decimal("0.6"), code="CUN"):
    return DestinationData(code, code, "MX", fares, bands or {}, level)


# --- money -----------------------------------------------------------------

def test_money_refuses_mixed_currency():
    with pytest.raises(CurrencyMismatch):
        Money.of(1, "CAD") + Money.of(1, "USD")


def test_range_must_be_ordered():
    with pytest.raises(ValueError):
        PriceRange(Money.of(5), Money.of(3), Money.of(10))


def test_range_addition_and_scaling():
    r = PriceRange(Money.of(1), Money.of(2), Money.of(3)) * 2 + PriceRange(Money.of(1), Money.of(1), Money.of(1))
    assert r.as_dict() == {"low": 3, "expected": 5, "high": 7}


# --- rooms -----------------------------------------------------------------

@pytest.mark.parametrize(
    "adults,children,rooms",
    [(1, 0, 1), (2, 0, 1), (3, 0, 2), (4, 0, 2), (2, 2, 1), (2, 3, 2), (1, 4, 2), (5, 1, 3)],
)
def test_rooms_needed(adults, children, rooms):
    assert rooms_needed(adults, children) == rooms


# --- request validation ----------------------------------------------------

def test_request_needs_an_adult():
    with pytest.raises(ValueError):
        TripRequest(Money.of(1000), adults=0)


# --- pricing ---------------------------------------------------------------

def test_package_totals_add_up_and_scale_with_travellers():
    d = dest([fare(300), fare(320), fare(360)], {("2027-01", "mid"): band(100, 150, 220)})
    req = TripRequest(Money.of(5000), adults=2, nights=7, month="2027-01")
    p = price_package(d, req, 7, "2027-01", TODAY)
    flights, lodging, daily = p.components
    assert flights.total.low == Money.of(600)  # cheapest fare x 2 people
    assert flights.total.expected == Money.of(640)  # median of cheapest 3 x 2
    assert lodging.total.expected == Money.of(150 * 7)  # 1 room x 7 nights
    assert p.total.expected == flights.total.expected + lodging.total.expected + daily.total.expected
    assert flights.confidence == "cached (3d)"
    assert lodging.confidence == "sampled (1d)"
    assert daily.confidence == "estimated"


def test_fare_of_wrong_length_is_marked_estimated():
    d = dest([fare(300, nights=14)])
    req = TripRequest(Money.of(5000), adults=1, nights=5, month="2027-01")
    p = price_package(d, req, 5, "2027-01", TODAY)
    assert p.components[0].confidence == "estimated"


def test_no_flight_data_means_no_package():
    d = dest([fare(300)])
    req = TripRequest(Money.of(5000), adults=1, nights=7, month="2027-03")
    assert price_package(d, req, 7, "2027-03", TODAY) is None


def test_missing_band_falls_back_to_estimate():
    d = dest([fare(300)])
    req = TripRequest(Money.of(5000), adults=2, nights=7, month="2027-01")
    p = price_package(d, req, 7, "2027-01", TODAY)
    assert p.components[1].confidence == "estimated"


def test_nearest_month_band_is_used():
    d = dest([fare(300)], {("2027-02", "mid"): band(100, 150, 220)})
    req = TripRequest(Money.of(5000), adults=2, nights=7, month="2027-01")
    p = price_package(d, req, 7, "2027-01", TODAY)
    assert p.components[1].total.expected == Money.of(1050)


def test_fit_labels():
    d = dest([fare(300)], {("2027-01", "mid"): band(100, 150, 220)})
    req = {"adults": 1, "nights": 7, "month": "2027-01"}
    total = price_package(d, TripRequest(Money.of(99999), **req), 7, "2027-01", TODAY).total
    assert price_package(d, TripRequest(total.expected, **req), 7, "2027-01", TODAY).fit == "within"
    assert price_package(d, TripRequest(total.low, **req), 7, "2027-01", TODAY).fit == "stretch"
    assert price_package(d, TripRequest(total.low - Money.of(1), **req), 7, "2027-01", TODAY).fit == "over"


def test_without_nights_picks_longest_trip_that_fits():
    fares = [fare(300, nights=n) for n in (4, 7, 10, 14)]
    d = dest(fares, {("2027-01", "mid"): band(100, 150, 220)})
    req = TripRequest(Money.of(2500), adults=1, month="2027-01")
    p = best_package(d, req, TODAY)
    assert p.fit == "within"
    assert p.nights in (4, 7, 10, 14)  # a length some fare really offers
    for n in (4, 7, 10, 14):
        if n > p.nights:
            assert price_package(d, req, n, "2027-01", TODAY).fit != "within"


def test_package_uses_the_fares_real_length():
    d = dest([fare(300, nights=6)])
    req = TripRequest(Money.of(9999), adults=1, nights=7, month="2027-01")
    p = price_package(d, req, 7, "2027-01", TODAY)
    assert p.nights == 6
    assert p.fare.nights == 6


def test_best_package_picks_cheapest_month():
    fares = [fare(900, depart=date(2027, 1, 10)), fare(300, depart=date(2027, 2, 10))]
    d = dest(fares)
    p = best_package(d, TripRequest(Money.of(9999), adults=1, nights=7), TODAY)
    assert p.month == "2027-02"


def test_rank_orders_within_before_stretch_and_drops_over():
    cheap = dest([fare(200)], code="AAA")
    mid = dest([fare(600)], code="BBB")
    pricey = dest([fare(5000)], code="CCC")
    req = TripRequest(Money.of(2600), adults=1, nights=7, month="2027-01")
    pkgs = [best_package(x, req, TODAY) for x in (pricey, mid, cheap)]
    ranked = rank(pkgs, req)
    assert next(p.destination.code for p in ranked) == "AAA"
    assert all(p.fit != "over" for p in ranked)
