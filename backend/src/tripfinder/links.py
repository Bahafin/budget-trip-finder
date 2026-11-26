"""Affiliate links: one place that turns a partner page into a tracked link.

Travelpayouts brands use the same redirect as the partner links API returns
(`POST /links/v1/create`, checked 2026-11-26):
    https://tp.media/r?campaign_id=<program>&marker=<partner id>&p=<promo>&sub_id=<tag>&trs=<project>&u=<page>
Building it locally saves an API call per link; `check_template` asks the API for one link per export and
fails loudly if the format ever changes.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

from .config import Settings
from .meter import Meter

PARTNER_LINKS_URL = "https://api.travelpayouts.com/links/v1/create"


@dataclass(frozen=True)
class Program:
    campaign_id: int
    promo_id: int


# campaign_id / p values returned by the partner links API for the "Bahafin" project (605382).
PROGRAMS = {
    "aviasales": Program(100, 4114),
    "klook": Program(137, 4110),
    "kkday": Program(633, 9074),
}

# Countries where Klook's hotel inventory is the better bet than a plain Booking.com search.
ASIA = {"JP", "TH", "HK", "ID", "SG", "MY", "VN", "KR", "TW", "PH", "CN", "MO", "KH", "IN", "AE", "QA"}


def tracked(s: Settings, program: str, page_url: str, sub_id: str) -> str:
    prog = PROGRAMS[program]
    query = {
        "campaign_id": prog.campaign_id,
        "marker": s.travelpayouts_marker,
        "p": prog.promo_id,
        "sub_id": sub_id,
        "trs": s.travelpayouts_project_id,
        "u": page_url,
    }
    return "https://tp.media/r?" + urllib.parse.urlencode(query)


def aviasales_page(cache_link: str) -> str:
    """Cached fares carry a relative search path; drop any marker we added before."""
    path = cache_link if cache_link.startswith("/") else "/" + cache_link
    parts = urllib.parse.urlsplit(path)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True) if k != "marker"]
    return urllib.parse.urlunsplit(("https", "www.aviasales.com", parts.path, urllib.parse.urlencode(q), ""))


def flight_link(s: Settings, cache_link: str, destination: str) -> str:
    return tracked(s, "aviasales", aviasales_page(cache_link), f"site-{destination}-flight")


def hotel_link(s: Settings, city: str, country: str, destination: str, checkin: str, checkout: str, adults: int, children: int, rooms: int) -> dict[str, str]:
    """Where "Check hotels" goes. Klook (tracked) for Asia; elsewhere a Booking.com search until Expedia's
    link format is known (TODO.md). Returns the url and the partner name for the button label."""
    if country in ASIA:
        page = "https://www.klook.com/en-CA/search/result/?" + urllib.parse.urlencode({"query": f"{city} hotels"})
        return {"url": tracked(s, "klook", page, f"site-{destination}-hotel"), "partner": "Klook"}
    q = {"ss": city, "checkin": checkin, "checkout": checkout, "group_adults": adults, "group_children": children, "no_rooms": rooms}
    return {"url": "https://www.booking.com/searchresults.html?" + urllib.parse.urlencode(q), "partner": "Booking.com"}


def check_template(meter: Meter, s: Settings) -> bool:
    """Ask the partner links API for one Aviasales link and compare it with what `tracked` builds."""
    page = "https://www.aviasales.com/search/YTO1501CUN22011"
    body = {"trs": int(s.travelpayouts_project_id), "marker": int(s.travelpayouts_marker), "shorten": False,
            "links": [{"url": page, "sub_id": "template-check"}]}
    data = meter.request("travelpayouts-links", PARTNER_LINKS_URL, method="POST", body=body,
                         headers={"X-Access-Token": s.travelpayouts_token})
    got = urllib.parse.urlsplit(data["result"]["links"][0]["partner_url"])
    want = urllib.parse.urlsplit(tracked(s, "aviasales", page, "template-check"))
    keys = ("campaign_id", "marker", "p", "trs", "sub_id")
    gq, wq = dict(urllib.parse.parse_qsl(got.query)), dict(urllib.parse.parse_qsl(want.query))
    return got.netloc == want.netloc and got.path == want.path and all(gq.get(k) == wq.get(k) for k in keys)
