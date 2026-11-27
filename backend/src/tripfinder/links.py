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

# Expedia Group Travel Creator Program (direct, joined 2026-11-26). Format from the owner's Link Builder
# (unshortened option, 2026-11-26): <base>?landingPage=<page>&camref=<campaign>&creativeref=<creative>&adref=<ref>.
# camref and creativeref came with the owner's links; adref is the publisher's own reference (like sub_id),
# so we put ours in it. Expedia: hotels 3.6%; Hotels.com: 1.35-3.6% (PHASE1_SPEC section 14).
@dataclass(frozen=True)
class ExpediaBrand:
    name: str
    base: str  # affiliate redirect
    search: str  # hotel search page on the Canadian site
    camref: str
    creativeref: str
    extra: tuple[tuple[str, str], ...] = ()


EXPEDIA_GROUP = {
    "expedia": ExpediaBrand("Expedia", "https://expedia.com/affiliate", "https://www.expedia.ca/Hotel-Search",
                            "1100l6zQri", "1011l87781", (("siteid", "1"),)),
    "hotels.com": ExpediaBrand("Hotels.com", "https://www.hotels.com/affiliate", "https://ca.hotels.com/Hotel-Search",
                               "1100l6zQrn", "1101l67721"),
}
HOTEL_BRAND = "expedia"  # the "Check hotels" button; switch to "hotels.com" here if it earns better

# Country names for the search box, so "Kingston" means the right Kingston. Unknown codes search the city alone.
COUNTRY_NAMES = {
    "AE": "United Arab Emirates", "CA": "Canada", "CR": "Costa Rica", "DE": "Germany", "DO": "Dominican Republic",
    "ES": "Spain", "FR": "France", "GB": "United Kingdom", "GR": "Greece", "HK": "Hong Kong", "ID": "Indonesia",
    "JM": "Jamaica", "JP": "Japan", "KR": "South Korea", "MA": "Morocco", "MX": "Mexico", "NL": "Netherlands",
    "NZ": "New Zealand", "PA": "Panama", "PF": "French Polynesia", "PT": "Portugal", "TH": "Thailand", "TR": "Turkey",
    "US": "United States", "VN": "Vietnam", "IT": "Italy", "IE": "Ireland", "IS": "Iceland", "CU": "Cuba",
}


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


def flight_search_link(s: Settings, destination: str, origin: str | None = None) -> str:
    """Aviasales search from Toronto for any dates; the browser fills {dep} {ret} (DDMM) and {pax}
    (adults digit, then children digit if any). Used when no cached fare matches the trip's length."""
    page = f"https://www.aviasales.com/search/{origin or s.origin}{{dep}}{destination}{{ret}}{{pax}}"
    return tracked(s, "aviasales", page, f"site-{destination}-flight")


def expedia_group(brand: str, page: str, ref: str) -> str:
    b = EXPEDIA_GROUP[brand]
    q = [*b.extra, ("landingPage", page), ("camref", b.camref), ("creativeref", b.creativeref), ("adref", ref)]
    return b.base + "?" + urllib.parse.urlencode(q)


def room_adults(adults: int, rooms: int) -> str:
    """Expedia takes adults per room, comma-separated: 4 adults in 2 rooms is "2,2" (checked on expedia.ca 2026-11-26)."""
    rooms = max(1, min(rooms, adults))
    return ",".join(str(adults // rooms + (1 if i < adults % rooms else 0)) for i in range(rooms))


def hotel_link(s: Settings, city: str, country: str, destination: str, checkin: str, checkout: str, adults: int, children: int, rooms: int,
               brand: str = HOTEL_BRAND) -> dict[str, str]:
    """Where "Check hotels" goes: a tracked Expedia hotel search for the trip's dates, adults and rooms.
    Placeholders ({checkin} ...) stay as braces in the search page, so after one round of encoding in
    landingPage they read %7Bcheckin%7D, which the browser fills. Children aren't passed: Expedia wants each
    child's age, which we don't ask for. In the exported template (adults "{adults}") the adults-per-room
    value is the "{roomAdults}" placeholder, which the browser fills with roomAdults(). Returns the url and the partner name for the button label."""
    b = EXPEDIA_GROUP[brand]
    where = f"{city}, {COUNTRY_NAMES[country]}" if country in COUNTRY_NAMES and COUNTRY_NAMES[country] != city else city
    q = {"destination": where, "d1": checkin, "startDate": checkin, "d2": checkout, "endDate": checkout, "adults": room_adults(adults, rooms) if isinstance(adults, int) else "{roomAdults}", "rooms": rooms}
    page = b.search + "?" + urllib.parse.urlencode(q, safe="{}", quote_via=urllib.parse.quote)
    return {"url": expedia_group(brand, page, f"site-{destination}-hotel"), "partner": b.name}


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
