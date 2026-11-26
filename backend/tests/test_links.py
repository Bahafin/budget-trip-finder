import urllib.parse
from pathlib import Path

from tripfinder.config import Settings
from tripfinder.links import aviasales_page, flight_link, hotel_link

S = Settings("tok", "809658", "key", Path("x.db"), Path("seed"))


def _q(url):
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))


def test_flight_link_matches_partner_api_format():
    url = flight_link(S, "/search/YTO1701CUN22011?t=AB&search_date=23112026&marker=809658", "CUN")
    assert url.startswith("https://tp.media/r?")
    q = _q(url)
    assert (q["campaign_id"], q["marker"], q["p"], q["trs"], q["sub_id"]) == ("100", "809658", "4114", "605382", "site-CUN-flight")
    page = q["u"]
    assert page.startswith("https://www.aviasales.com/search/YTO1701CUN22011?")
    assert "marker" not in _q(page)  # old hand-added marker is dropped


def test_aviasales_page_accepts_path_without_leading_slash():
    assert aviasales_page("search/YTO1701CUN22011").startswith("https://www.aviasales.com/search/")


def test_asian_destinations_get_tracked_klook_hotel_link():
    h = hotel_link(S, "Bangkok", "TH", "BKK", "2027-01-10", "2027-01-17", 2, 0, 1)
    assert h["partner"] == "Klook"
    q = _q(h["url"])
    assert (q["campaign_id"], q["sub_id"]) == ("137", "site-BKK-hotel")


def test_other_destinations_get_booking_search_with_trip_details():
    h = hotel_link(S, "Cancun", "MX", "CUN", "2027-01-10", "2027-01-17", 2, 1, 1)
    assert h["partner"] == "Booking.com"
    q = _q(h["url"])
    assert (q["ss"], q["checkin"], q["group_adults"], q["group_children"]) == ("Cancun", "2027-01-10", "2", "1")
