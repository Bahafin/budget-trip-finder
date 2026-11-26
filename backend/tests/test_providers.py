from datetime import date

from tripfinder.jobs import tier_for, upcoming_months
from tripfinder.providers import (
    parse_advisories,
    parse_fares,
    parse_hotel_prices,
    parse_price_levels,
)


def test_parse_fares_reads_dates_price_and_cache_date():
    payload = {
        "data": [
            {
                "destination": "CUN", "departure_at": "2027-01-17T09:40:00-05:00", "return_at": "2027-01-22T19:40:00-05:00",
                "price": 360, "airline": "F8", "transfers": 0, "return_transfers": 1,
                "link": "/search/YTO1701CUN22011?t=x&search_date=23112026&expected_price=360",
            },
            {"destination": "CUN", "departure_at": "2027-01-17T09:40:00-05:00", "return_at": None, "price": 100},
        ]
    }
    [f] = parse_fares(payload, today=date(2026, 11, 25))
    assert (f.depart, f.ret, f.price, f.transfers) == (date(2027, 1, 17), date(2027, 1, 22), 360.0, 1)
    assert f.found_on == date(2026, 11, 23)


def test_parse_fares_handles_empty_payload():
    assert parse_fares({"data": None}, today=date(2026, 11, 25)) == []


def test_parse_hotel_prices_takes_cheapest_rate_and_joins_stars():
    payload = {
        "data": [
            {"hotelId": "h1", "roomTypes": [
                {"rates": [{"retailRate": {"total": [{"amount": 500.0, "currency": "CAD"}]}}]},
                {"rates": [{"retailRate": {"total": [{"amount": 420.5, "currency": "CAD"}]}}]},
            ]},
            {"hotelId": "h2", "roomTypes": []},
        ],
        "hotels": [{"id": "h1", "name": "Hotel One", "stars": 4}],
    }
    [h] = parse_hotel_prices(payload)
    assert (h.hotel_id, h.name, h.stars, h.total, h.currency) == ("h1", "Hotel One", 4.0, 420.5, "CAD")


def test_price_level_is_ppp_over_fx_using_latest_year():
    ppp = [{}, [
        {"country": {"id": "MX"}, "date": "2024", "value": 10.0},
        {"country": {"id": "MX"}, "date": "2025", "value": 11.0},
        {"country": {"id": "CA"}, "date": "2025", "value": None},
    ]]
    fx = [{}, [{"country": {"id": "MX"}, "date": "2025", "value": 20.0}]]
    assert parse_price_levels(ppp, fx) == {"MX": (0.55, "2025")}


def test_parse_advisories_builds_travel_gc_ca_link():
    payload = {"data": {"CO": {"advisory-state": 1, "date-published": {"date": "2026-11-01"},
                               "eng": {"advisory-text": "Exercise a high degree of caution", "url-slug": "colombia"}}}}
    [a] = parse_advisories(payload)
    assert (a.country_code, a.level, a.url) == ("CO", 1, "https://travel.gc.ca/destinations/colombia")


def test_tiers_from_stars():
    assert [tier_for(s) for s in (None, 2, 3, 3.5, 4, 4.5, 5)] == [None, "budget", "budget", "mid", "mid", "upscale", "upscale"]


def test_upcoming_months_crosses_year_end():
    assert upcoming_months(3, date(2026, 11, 23)) == ["2026-12", "2027-01", "2027-02"]


def test_hotel_fees_paid_at_the_property_are_added():
    payload = {
        "data": [{"hotelId": "h1", "roomTypes": [{"rates": [{"retailRate": {
            "total": [{"amount": 400.0, "currency": "CAD"}],
            "taxesAndFees": [
                {"included": True, "amount": 50.0, "currency": "CAD"},
                {"included": False, "amount": 31.41, "currency": "CAD", "description": "Environment fee"},
                {"included": False, "amount": 10.0, "currency": "USD"},
            ],
        }}]}]}],
        "hotels": [{"id": "h1", "name": "Resort", "stars": 4}],
    }
    [h] = parse_hotel_prices(payload)
    assert h.total == 431.41  # included tax already in total; USD fee skipped (can't mix currencies)
