"""Provider adapters. Each fetch_* calls the API through the Meter; each parse_* is pure and unit-tested."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .config import Settings
from .meter import Meter

AVIASALES_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
CITIES_URL = "https://api.travelpayouts.com/data/en/cities.json"
LITEAPI_RATES_URL = "https://api.liteapi.travel/v3.0/hotels/rates"
WORLDBANK_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}"
GAC_URL = "https://data.international.gc.ca/travel-voyage/index-alpha-eng.json"


# --- Aviasales (Travelpayouts) -------------------------------------------------

@dataclass(frozen=True)
class RawFare:
    destination: str
    depart: date
    ret: date
    price: float
    airline: str
    transfers: int
    link: str
    found_on: date


def fetch_fares(meter: Meter, s: Settings, month: str, destination: str | None = None) -> list[RawFare]:
    params = {
        "origin": s.origin,
        "departure_at": month,
        "one_way": "false",
        "currency": s.currency.lower(),
        "market": s.market,
        "limit": 1000,
        "sorting": "price",
    }
    if destination:
        params["destination"] = destination
    else:
        params["return_at"] = month  # bulk query: keep it to trips inside the month
    data = meter.request("aviasales", AVIASALES_URL, params=params, headers={"X-Access-Token": s.travelpayouts_token})
    return parse_fares(data, today=date.today())


def parse_fares(payload: dict[str, Any], today: date) -> list[RawFare]:
    out = []
    for x in payload.get("data") or []:
        if not x.get("return_at"):
            continue
        link = x.get("link", "")
        found = today
        if "search_date=" in link:
            try:
                found = datetime.strptime(link.split("search_date=")[1][:8], "%d%m%Y").date()
            except ValueError:
                pass
        out.append(
            RawFare(
                destination=x["destination"],
                depart=date.fromisoformat(x["departure_at"][:10]),
                ret=date.fromisoformat(x["return_at"][:10]),
                price=float(x["price"]),
                airline=x.get("airline", ""),
                transfers=max(int(x.get("transfers") or 0), int(x.get("return_transfers") or 0)),
                link=link,
                found_on=found,
            )
        )
    return out


def fetch_cities(meter: Meter) -> list[dict[str, Any]]:
    return meter.request("travelpayouts-data", CITIES_URL)


# --- LiteAPI (Nuitee) hotel rates ----------------------------------------------

@dataclass(frozen=True)
class HotelPrice:
    hotel_id: str
    name: str
    stars: float | None
    total: float
    currency: str


def fetch_hotel_prices(
    meter: Meter, s: Settings, lat: float, lon: float, checkin: date, checkout: date, radius_m: int | None = None
) -> list[HotelPrice]:
    body = {
        "checkin": checkin.isoformat(),
        "checkout": checkout.isoformat(),
        "currency": s.currency,
        "guestNationality": "CA",
        "occupancies": [{"adults": 2}],
        "latitude": lat,
        "longitude": lon,
        "radius": radius_m or s.hotel_radius_m,
        "maxRatesPerHotel": 1,
        "includeHotelData": True,
        "limit": 200,
        "timeout": 12,
    }
    data = meter.request("liteapi", LITEAPI_RATES_URL, method="POST", body=body, headers={"X-API-Key": s.liteapi_key}, timeout=90)
    return parse_hotel_prices(data)


def parse_hotel_prices(payload: dict[str, Any]) -> list[HotelPrice]:
    info = {h["id"]: h for h in payload.get("hotels") or []}
    out = []
    for h in payload.get("data") or []:
        best: tuple[float, str] | None = None
        for rt in h.get("roomTypes") or []:
            for r in rt.get("rates") or []:
                for t in (r.get("retailRate") or {}).get("total") or []:
                    if best is None or t["amount"] < best[0]:
                        best = (float(t["amount"]), t["currency"])
        if best is None:
            continue
        meta = info.get(h["hotelId"], {})
        stars = meta.get("stars")
        out.append(HotelPrice(h["hotelId"], meta.get("name", ""), float(stars) if stars else None, best[0], best[1]))
    return out


# --- World Bank price levels --------------------------------------------------

def fetch_price_levels(meter: Meter) -> dict[str, tuple[float, str]]:
    """Price level vs USD per ISO-2 country: PPP conversion factor (private consumption) / market FX rate."""
    year = date.today().year
    params = {"format": "json", "per_page": 20000, "date": f"{year - 8}:{year}"}
    ppp = meter.request("worldbank", WORLDBANK_URL.format(indicator="PA.NUS.PRVT.PP"), params=params, timeout=120)
    fx = meter.request("worldbank", WORLDBANK_URL.format(indicator="PA.NUS.FCRF"), params=params, timeout=120)
    return parse_price_levels(ppp, fx)


def _latest(payload: list[Any]) -> dict[str, tuple[str, float]]:
    best: dict[str, tuple[str, float]] = {}
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 and payload[1] else []
    for x in rows:
        iso2 = (x.get("country") or {}).get("id")
        if x.get("value") is None or not iso2:
            continue
        if iso2 not in best or x["date"] > best[iso2][0]:
            best[iso2] = (x["date"], float(x["value"]))
    return best


def parse_price_levels(ppp_payload: list[Any], fx_payload: list[Any]) -> dict[str, tuple[float, str]]:
    ppp, fx = _latest(ppp_payload), _latest(fx_payload)
    return {c: (ppp[c][1] / fx[c][1], ppp[c][0]) for c in ppp if c in fx and fx[c][1]}


# --- Global Affairs Canada travel advisories ----------------------------------

@dataclass(frozen=True)
class Advisory:
    country_code: str
    level: int
    text: str
    url: str
    published: str


def fetch_advisories(meter: Meter) -> list[Advisory]:
    return parse_advisories(meter.request("gac", GAC_URL))


def parse_advisories(payload: dict[str, Any]) -> list[Advisory]:
    out = []
    for iso2, x in (payload.get("data") or {}).items():
        eng = x.get("eng") or {}
        slug = eng.get("url-slug", "")
        out.append(
            Advisory(
                country_code=iso2,
                level=int(x.get("advisory-state") or 0),
                text=eng.get("advisory-text", ""),
                url=f"https://travel.gc.ca/destinations/{slug}" if slug else "https://travel.gc.ca/travelling/advisories",
                published=(x.get("date-published") or {}).get("date", ""),
            )
        )
    return out
