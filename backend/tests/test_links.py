import urllib.parse
from pathlib import Path

from tripfinder.config import Settings
from tripfinder.links import aviasales_page, flight_link, flight_search_link, hotel_link

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


def test_hotel_link_is_a_tracked_expedia_search_with_trip_details():
    h = hotel_link(S, "Cancun", "MX", "CUN", "2027-01-10", "2027-01-17", 2, 1, 1)
    assert h["partner"] == "Expedia"
    assert h["url"].startswith("https://expedia.com/affiliate?siteid=1&landingPage=")
    q = _q(h["url"])
    assert (q["camref"], q["creativeref"], q["adref"]) == ("1100l6zQri", "1011l87781", "site-CUN-hotel")
    page = urllib.parse.urlsplit(q["landingPage"])
    assert (page.netloc, page.path) == ("www.expedia.ca", "/Hotel-Search")
    pq = _q(q["landingPage"])
    assert (pq["destination"], pq["d1"], pq["endDate"], pq["adults"], pq["rooms"]) == ("Cancun, Mexico", "2027-01-10", "2027-01-17", "2", "1")


def test_hotel_link_names_the_country_so_kingston_is_the_right_one():
    on = _q(_q(hotel_link(S, "Kingston", "CA", "YGK", "a", "b", 2, 0, 1)["url"])["landingPage"])
    jm = _q(_q(hotel_link(S, "Kingston", "JM", "KIN", "a", "b", 2, 0, 1)["url"])["landingPage"])
    assert (on["destination"], jm["destination"]) == ("Kingston, Canada", "Kingston, Jamaica")
    assert _q(_q(hotel_link(S, "Hong Kong", "HK", "HKG", "a", "b", 2, 0, 1)["url"])["landingPage"])["destination"] == "Hong Kong"


def test_hotel_template_placeholders_are_fillable_once_encoded():
    """export.py passes "{checkin}" etc.; engine.js and pages.py fill "%7Bcheckin%7D" in the final link."""
    url = hotel_link(S, "Cancun", "MX", "CUN", "{checkin}", "{checkout}", "{adults}", "{children}", "{rooms}")["url"]
    for k in ("checkin", "checkout", "roomAdults", "rooms"):
        assert f"%7B{k}%7D" in url and "%257B" not in url, k
    filled = url.replace("%7Bcheckin%7D", "2027-01-10").replace("%7Bcheckout%7D", "2027-01-17").replace("%7BroomAdults%7D", "2").replace("%7Brooms%7D", "1")
    assert _q(_q(filled)["landingPage"])["startDate"] == "2027-01-10"


def test_room_adults_splits_adults_across_rooms():
    from tripfinder.links import room_adults
    assert [room_adults(2, 1), room_adults(4, 2), room_adults(5, 3), room_adults(1, 2)] == ["2", "2,2", "2,2,1", "1"]


def test_hotels_com_brand_uses_its_own_campaign():
    h = hotel_link(S, "Cancun", "MX", "CUN", "2027-01-10", "2027-01-17", 2, 0, 1, brand="hotels.com")
    q = _q(h["url"])
    assert h["partner"] == "Hotels.com" and h["url"].startswith("https://www.hotels.com/affiliate?landingPage=")
    assert (q["camref"], urllib.parse.urlsplit(q["landingPage"]).netloc) == ("1100l6zQrn", "ca.hotels.com")


def test_flight_search_template_is_tracked_with_placeholders():
    url = flight_search_link(S, "CUN")
    q = _q(url)
    assert (q["campaign_id"], q["marker"], q["sub_id"]) == ("100", "809658", "site-CUN-flight")
    assert q["u"] == "https://www.aviasales.com/search/YTO{dep}CUN{ret}{pax}"
    assert "%7Bdep%7D" in url  # the browser fills the encoded placeholders
