"""Static destination and month pages, generated from the site snapshot (site/data.json).

Spec: docs/content/programmatic-pages.md. Run with `python -m tripfinder pages` after `export`.

Numbers come only from the snapshot and the pricing engine: the snapshot is what the browser engine
(site/engine.js) prices from, and the Python engine is kept in step with it by site/tests/parity.test.mjs.
Every priced call is also written to site/tests/pages-manifest.json, and site/tests/pages.test.mjs re-prices
each one with engine.js, so a page can never show a number the trip finder wouldn't.

Output: site/from-toronto/**/index.html (generated, not committed). Everything stays `noindex` unless
TRIPFINDER_INDEXABLE=true (flip after Gate B); pages that fail their data gate stay `noindex` even then.
"""

from __future__ import annotations

import html
import json
import math
import os
import shutil
import statistics
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from string import Template
from typing import Any
from urllib.parse import urlencode

from .config import ROOT
from .engine import (
    CHILD_DAILY_SHARE,
    DAILY_BASE_CAD,
    DestinationData,
    Fare,
    LodgingBand,
    Package,
    TripRequest,
    best_package,
    price_package,
    rank,
    rooms_needed,
)
from .gate_a import summary as gate_a_summary
from .money import Money, PriceRange

# ---- Brand and site settings ------------------------------------------------------------------------------
# One place to rebrand: switch to "Far Enough" once farenough.ca is registered (TODO.md).
BRAND_NAME = "Budget Trip Finder"
BRAND_TAGLINE = "See how far your budget goes."
BRAND_DESCRIPTOR = "Whole-trip budgets from Toronto"
SITE_URL = "https://bahafin.github.io/budget-trip-finder/"  # canonical base; change with the domain

ORIGIN_SLUG = "from-toronto"
ORIGIN_NAME = "Toronto"
BUDGETS = (1500, 2000, 3000, 5000)  # month x budget pages, CAD, whole trip
HUB_NIGHTS = 7  # destination tables price "a week"
ADULTS = 2  # default group on every page
TIER_LABEL = {"budget": "Budget hotel (up to 3★)", "mid": "Mid-range hotel (4★)", "upscale": "Upscale hotel (5★)"}
TIER_SHORT = {"budget": "budget", "mid": "mid-range", "upscale": "upscale"}

# Indexing gates (programmatic-pages.md, "Indexing gates").
GATE_MONTH_FARES = 5  # destination x month: at least this many fares in the month
GATE_MONTH_WEEK = (HUB_NIGHTS - 2, HUB_NIGHTS + 2)  # ... one of them about a week long
GATE_MONTH_BAND_N = 10  # ... and a mid-tier hotel band from at least this many hotels
GATE_HUB_MONTHS = 2  # destination hub: fares in at least this many months
GATE_BUDGET_RESULTS = 3  # month x budget: at least this many trips that fit or stretch
STALE_DAYS = 14  # newest fare used older than this: warning banner and noindex

# Ontario public-school March break (one fixed week; boards can differ). Add each year once announced.
MARCH_BREAK = {2027: date(2027, 3, 15)}  # Monday of the break week
MARCH_BREAK_GROUP = (2, 2)  # adults, children
MARCH_BREAK_BUDGETS = (3000, 5000)

# URL slugs are fixed here so a renamed destination never breaks a URL.
SLUGS = {
    "MEX": "mexico-city", "CUN": "cancun", "IST": "istanbul", "YVR": "vancouver", "LON": "london", "YYC": "calgary",
    "NYC": "new-york", "KIN": "kingston-jamaica", "PUJ": "punta-cana", "TYO": "tokyo", "BKK": "bangkok",
    "LIR": "liberia-costa-rica", "AMS": "amsterdam", "ORL": "orlando", "YEA": "edmonton", "DXB": "dubai",
    "FLL": "fort-lauderdale", "YMQ": "montreal", "DFW": "dallas", "PTY": "panama-city", "DPS": "bali",
    "CHI": "chicago", "FRA": "frankfurt", "PAR": "paris", "HKG": "hong-kong", "HNL": "honolulu",
}
DISPLAY = {"CUN": "Cancún", "DPS": "Bali", "KIN": "Kingston, Jamaica", "LIR": "Liberia, Costa Rica"}
COUNTRIES = {
    "MX": "Mexico", "TR": "Türkiye", "CA": "Canada", "GB": "United Kingdom", "US": "United States", "JM": "Jamaica",
    "DO": "Dominican Republic", "JP": "Japan", "TH": "Thailand", "CR": "Costa Rica", "NL": "Netherlands",
    "AE": "United Arab Emirates", "PA": "Panama", "ID": "Indonesia", "DE": "Germany", "FR": "France", "HK": "Hong Kong",
}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

# Seller wording we never use in our own copy (TICO / referral-only; PHASE1_SPEC section 8). Tests check pages.
BANNED_PHRASES = ("book now", "book with us", "our price", "buy now", "deal", "deals", "lowest price guaranteed", "reserve now")

TEMPLATES = Path(__file__).parent / "templates"
CHECKS_PATH = ROOT / "docs" / "gate-a" / "sheet.csv"  # Gate A hand checks, shown on the method page
METHOD_PATH = f"{ORIGIN_SLUG}/how-we-estimate/"


# ---- Snapshot loading ---------------------------------------------------------------------------------------

@dataclass
class Snapshot:
    today: date
    generated_at: str
    constants: dict[str, Any]
    dests: list[DestinationData]
    hotel: dict[str, dict[str, str] | None]  # code -> {url template, partner}
    flight_search: dict[str, str]  # code -> Aviasales search template, for estimated fares
    advisories: dict[str, dict[str, Any]]
    notes: dict[str, list[dict[str, str]]]


def load_snapshot(path: Path) -> Snapshot:
    raw = json.loads(path.read_text(encoding="utf8"))
    today = date.fromisoformat(raw["today"])
    dests, hotel, flight_search = [], {}, {}
    for d in raw["destinations"]:
        fares = [
            Fare(
                d["code"], date.fromisoformat(f["depart"]), date.fromisoformat(f["ret"]), Money.of(f["price"]),
                date.fromisoformat(f["foundOn"]), f.get("airline") or "", f.get("transfers") or 0, f.get("link") or "",
                Decimal(str(f.get("season", 1))),
            )
            for f in d["fares"]
            if f["depart"] >= raw["today"]  # same rule as prepare() in engine.js
        ]
        bands = {
            (b["month"], b["tier"]): LodgingBand(
                PriceRange(Money.of(b["low"]), Money.of(b["mid"]), Money.of(b["high"])), b["n"], date.fromisoformat(b["asOf"]), b["source"]
            )
            for b in d["bands"]
        }
        level = Decimal(str(d["priceLevel"])) if d.get("priceLevel") is not None else None
        dests.append(DestinationData(d["code"], d["name"], d["country"], fares, bands, level))
        hotel[d["code"]] = d.get("hotel")
        flight_search[d["code"]] = d.get("flightSearch") or ""
    return Snapshot(today, raw["generatedAt"], raw["constants"], dests, hotel, flight_search, raw.get("advisories", {}), raw.get("notes", {}))


def load_photos(path: Path) -> dict[str, dict[str, str]]:
    """site/photos.js is `export const PHOTOS = {json};`."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf8")
    start, end = text.index("{"), text.rindex("}")
    return json.loads(text[start : end + 1])


# ---- Pricing (every call is recorded for the JS parity check) ---------------------------------------------

@dataclass
class Pricer:
    snap: Snapshot
    calls: list[dict[str, Any]] = field(default_factory=list)

    def req(self, budget: float, tier: str, month: str | None, nights: int | None, adults: int = ADULTS, children: int = 0) -> TripRequest:
        return TripRequest(Money.of(budget), adults, children, month, nights, tier)

    def price(self, dest: DestinationData, req: TripRequest, nights: int, month: str, window: dict | None = None) -> Package | None:
        pkg = price_package(dest, req, nights, month, self.snap.today)
        self._log("price", dest, req, pkg, nights=nights, window=window)
        return pkg

    def best(self, dest: DestinationData, req: TripRequest, window: dict | None = None) -> Package | None:
        pkg = best_package(dest, req, self.snap.today)
        self._log("best", dest, req, pkg, window=window)
        return pkg

    def _log(self, kind: str, dest: DestinationData, req: TripRequest, pkg: Package | None, nights: int | None = None, window: dict | None = None) -> None:
        self.calls.append({
            "kind": kind, "code": dest.code, "nights": nights, "window": window,
            "request": {"budget": float(req.budget.amount), "adults": req.adults, "children": req.children,
                        "month": req.month, "nights": req.nights, "tier": req.tier, "sort": req.sort},
            "result": None if pkg is None else {"nights": pkg.nights, "month": pkg.month, "fit": pkg.fit,
                                                "depart": pkg.fare.depart.isoformat() if pkg.fare else None, **pkg.total.as_dict()},
        })


def window_dest(dest: DestinationData, w: dict[str, str]) -> DestinationData:
    """Destination restricted to fares inside a date window (seasonal pages)."""
    keep = [f for f in dest.fares
            if w["departFrom"] <= f.depart.isoformat() <= w["departTo"] and w["retFrom"] <= f.ret.isoformat() <= w["retTo"]]
    return replace(dest, fares=keep)


# ---- HTML helpers -----------------------------------------------------------------------------------------

def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def name_of(d: DestinationData) -> str:
    return DISPLAY.get(d.code, d.name)


def month_label(m: str) -> str:
    y, mm = m.split("-")
    return f"{MONTHS[int(mm) - 1].capitalize()} {y}"


def month_slug(m: str) -> str:
    return MONTHS[int(m.split("-")[1]) - 1]


def day(d: date) -> str:
    return f"{d.day} {d:%b}"


def day_long(d: date) -> str:
    return f"{d.day} {d:%B %Y}"


@dataclass
class Fmt:
    """Formats amounts. Every price carries the date it was estimated (guardrail 1, tested)."""

    asof: str

    def amt(self, m: Money | float) -> str:
        v = float(m.amount) if isinstance(m, Money) else float(m)
        return f'<span class="amt" data-asof="{self.asof}">${round(v):,}</span>'

    def rng(self, r: PriceRange) -> str:
        return f"{self.amt(r.low)}–{self.amt(r.high)}"

    def cell(self, r: PriceRange) -> str:
        return f'<span class="lo">{self.amt(r.low)}</span> <b>{self.amt(r.expected)}</b> <span class="lo">{self.amt(r.high)}</span>'


def pct(x: float) -> str:
    return f"{round(abs(x) * 100)}%"


def pct_signed(x: float) -> str:
    v = round(x * 100)
    return f"{'+' if v > 0 else '−' if v < 0 else ''}{abs(v)}%"


def budget_for(p: Package) -> int:
    """A round budget the trip fits: its expected total rounded up to the next $500."""
    return math.ceil(p.total.expected.amount / 500) * 500


def budget_amt(n: float) -> str:
    """A budget the reader chose (not a price), marked so the dated-amount test can tell it apart."""
    return f'<span class="bud" data-budget>${round(n):,}</span>'


def sponsored(url: str, text: str, cls: str = "btn secondary") -> str:
    return f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="sponsored nofollow noopener">{esc(text)} ↗</a>'


def flight_link(snap: Snapshot, code: str, fare: Fare, adults: int, children: int) -> str:
    """Python port of flightLinkFor() in site/engine.js."""
    if fare.link:
        return fare.link
    url = snap.flight_search.get(code) or ""
    values = {"dep": fare.depart.strftime("%d%m"), "ret": fare.ret.strftime("%d%m"), "pax": f"{adults}{children or ''}"}
    for k, v in values.items():
        url = url.replace("{" + k + "}", v).replace("%7B" + k + "%7D", v)
    return url


def hotel_link(snap: Snapshot, code: str, fare: Fare, adults: int, children: int) -> dict[str, str] | None:
    """Python port of hotelLinkFor() in site/engine.js."""
    h = snap.hotel.get(code)
    if not h:
        return None
    values = {"checkin": fare.depart.isoformat(), "checkout": fare.ret.isoformat(), "adults": adults, "children": children,
              "rooms": rooms_needed(adults, children)}
    url = h["url"]
    for k, v in values.items():
        url = url.replace("{" + k + "}", str(v)).replace("%7B" + k + "%7D", str(v))
    return {"url": url, "partner": h["partner"]}


def stops(f: Fare) -> str:
    if not f.airline:
        return ""
    return f"{f.airline}, " + ("direct" if not f.transfers else f"{f.transfers} stop{'s' if f.transfers > 1 else ''}")


def conf_text(c: str) -> str:
    if c.startswith("cached ("):
        n = c[8:-2]
        return f"cached fare, {n} day{'' if n == '1' else 's'} old"
    if c.startswith("sampled ("):
        n = c[9:-2]
        return f"sampled hotel prices, {n} day{'' if n == '1' else 's'} old"
    return "estimate"


def group_text(adults: int, children: int) -> str:
    a = f"{adults} adult{'s' if adults > 1 else ''}"
    return a + (f" and {children} child{'ren' if children > 1 else ''}" if children else "")


# ---- Page model and layout --------------------------------------------------------------------------------

@dataclass
class Page:
    path: str  # under site/, ends with "/", e.g. "from-toronto/cancun/"
    title: str  # <title>
    description: str
    h1: str
    eyebrow: str
    body: str
    crumbs: list[tuple[str, str]]  # (label, path) from the origin hub down; last one is this page
    gate: bool  # passes its data gate (indexable once the site is)
    gate_reason: str = ""
    photo: dict[str, str] | None = None
    about: dict[str, Any] | None = None  # schema.org TouristDestination
    article: bool = False
    has_partner_links: bool = False
    hub_of: str = ""  # destination code when this is that destination's hub page (for the finder's card links)


def rel(from_path: str, to_path: str) -> str:
    """Relative link between two site paths (the site lives under a sub-path on GitHub Pages)."""
    depth = from_path.count("/")
    return "../" * depth + to_path


def render(page: Page, snap: Snapshot, site_indexable: bool) -> str:
    asof = snap.today.isoformat()
    indexable = site_indexable and page.gate
    root = rel(page.path, "")
    canonical = SITE_URL + page.path
    crumbs_html = " › ".join(
        f'<a href="{esc(rel(page.path, p))}">{esc(label)}</a>' if p != page.path else f'<span aria-current="page">{esc(label)}</span>'
        for label, p in page.crumbs
    )
    ld: list[dict[str, Any]] = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label, "item": SITE_URL + p} for i, (label, p) in enumerate(page.crumbs)
        ]},
        {"@context": "https://schema.org", "@type": "Article" if page.article else "WebPage", "name": page.h1, "headline": page.h1,
         "description": page.description, "url": canonical, "inLanguage": "en-CA", "dateModified": asof,
         "publisher": {"@type": "Organization", "name": BRAND_NAME, "url": SITE_URL},
         **({"about": page.about} if page.about else {})},
    ]
    stale = (snap.today - newest_fare_date(snap)).days > STALE_DAYS
    hero_img = ""
    credit = ""
    if page.photo:
        hero_img = f'<img src="{esc(page.photo["src"])}" alt="" fetchpriority="high">'
        credit = (f'<p class="hero-credit">Photo: {esc(page.photo["author"])}, '
                  f'<a href="{esc(page.photo["page"])}" target="_blank" rel="noopener">{esc(page.photo["license"])}</a></p>')
    tpl = Template((TEMPLATES / "page.html").read_text(encoding="utf8"))
    return tpl.substitute(
        title=esc(page.title),
        description=esc(page.description),
        robots="index, follow" if indexable and not stale else "noindex, follow",
        canonical=esc(canonical),
        css=esc(rel(page.path, "pages.css")),
        jsonld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"),
        root=esc(root),
        brand=esc(BRAND_NAME),
        tagline=esc(BRAND_TAGLINE),
        hero_class="hero has-photo" if page.photo else "hero",
        hero_img=hero_img,
        credit=credit,
        eyebrow=esc(page.eyebrow),
        h1=esc(page.h1),
        crumbs=crumbs_html,
        stale=('<p class="note adv">These numbers haven\'t refreshed for a while. Treat them as out of date.</p>' if stale else ""),
        disclosure=DISCLOSURE,
        body=page.body,
        asof=asof,
        asof_long=esc(day_long(snap.today)),
        finder=esc(root),
        hub=esc(rel(page.path, ORIGIN_SLUG + "/")),
        method=esc(rel(page.path, METHOD_PATH)),
    )


DISCLOSURE = (
    '<aside class="disclosure" aria-label="How we make money"><b>How we make money:</b> some links on this page go to '
    "partner sites. If you book through them, we may earn a commission at no extra cost to you. We don't sell trips or "
    "take payments: you compare here and book on the partner's site. Partners don't pay for placement.</aside>"
)


def newest_fare_date(snap: Snapshot) -> date:
    found = [f.found_on for d in snap.dests for f in d.fares]
    return max(found) if found else snap.today


# ---- Shared sections ----------------------------------------------------------------------------------------

INCLUDED = (
    '<section class="box"><h2>What\'s in these numbers, and what isn\'t</h2><div class="two">'
    "<div><h3>Included</h3><ul><li>Return flights from Toronto for everyone</li><li>A hotel room for every night, "
    "including fees the hotel charges on arrival when the hotel lists them</li><li>Day-to-day spending: food, local transport, "
    "modest entry fees</li></ul></div>"
    "<div><h3>Not included</h3><ul><li>All-inclusive meal plans (these are hotel-room prices)</li><li>Checked bags, if the fare "
    "doesn't include them</li><li>Travel insurance, tours, tips</li><li>Getting to and parking at the airport</li></ul></div>"
    "</div></section>"
)


def advisory_block(snap: Snapshot, d: DestinationData) -> str:
    out = []
    adv = snap.advisories.get(d.country_code)
    if adv:
        out.append(
            f'<p class="note adv">Government of Canada travel advice for {esc(COUNTRIES.get(d.country_code, d.country_code))}: '
            f'<b>{esc(adv["text"])}</b>. <a href="{esc(adv["url"])}" target="_blank" rel="noopener">Read the current advisory</a> before you book.</p>'
        )
    for n in snap.notes.get(d.country_code, []):
        out.append(
            f'<p class="note kbyg"><b>Know before you go ({esc(n["category"])}):</b> {esc(n["summary"])} '
            f'<a href="{esc(n["source_url"])}" target="_blank" rel="noopener">Source</a>'
            f'{", reviewed " + esc(n["reviewed_at"]) if n.get("reviewed_at") else ""}.</p>'
        )
    if d.country_code != "CA":
        out.append('<p class="note kbyg">Entry rules depend on your passport. Check <a href="https://travel.gc.ca/travelling/advisories" '
                   'target="_blank" rel="noopener">travel.gc.ca</a> for current requirements.</p>')
    if not out:
        return ""
    return '<section class="box"><h2>Before you go</h2>' + "".join(out) + "</section>"


def tier_table(fmt: Fmt, pkgs: dict[str, Package]) -> str:
    tiers = [t for t in ("budget", "mid", "upscale") if t in pkgs]
    head = "".join(f"<th scope=\"col\">{esc(TIER_LABEL[t])}</th>" for t in tiers)
    names = {"flights": f"Flights for {ADULTS}", "lodging": "Hotel", "daily": "Day-to-day spending"}
    rows = []
    for i, cname in enumerate(("flights", "lodging", "daily")):
        cells = "".join(f"<td>{fmt.cell(pkgs[t].components[i].total)}</td>" for t in tiers)
        rows.append(f'<tr><th scope="row">{names[cname]}</th>{cells}</tr>')
    rows.append('<tr class="tot"><th scope="row">Total</th>' + "".join(f"<td>{fmt.cell(pkgs[t].total)}</td>" for t in tiers) + "</tr>")
    rows.append('<tr><th scope="row">Per person (expected)</th>'
                + "".join(f"<td>{fmt.amt(pkgs[t].total.expected * (Decimal(1) / Decimal(ADULTS)))}</td>" for t in tiers) + "</tr>")
    return (f'<div class="scroll"><table class="costs"><caption>Each cell: low, <b>expected</b>, high. CAD.</caption>'
            f'<thead><tr><th></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def method_list(fmt: Fmt, pkgs: dict[str, Package]) -> str:
    any_pkg = pkgs.get("mid") or next(iter(pkgs.values()))
    f = any_pkg.fare
    flights = any_pkg.components[0]
    lead = ("cheapest cached return fare for these dates was" if f.link else
            f"no cached fare for {any_pkg.nights} nights, so this is estimated from the cheapest fare that month,")
    items = [(f"<li><b>Flights:</b> {lead} {fmt.amt(f.price)} per person"
             f"{' (' + esc(stops(f)) + ')' if stops(f) else ''}, seen on {esc(day_long(f.found_on))}; {esc(conf_text(flights.confidence))}.</li>")]
    for t, p in pkgs.items():
        lod = p.components[1]
        level = p.destination.price_level if p.destination.price_level is not None else Decimal(1)
        per_day = Money.of(DAILY_BASE_CAD[t]) * level
        n_hotels = lod.detail.split("from ")[1].split(" ")[0] if "from " in lod.detail else ""
        source = f"median of {n_hotels} hotels sampled" if n_hotels else "no hotel sample; scaled Canadian average"
        items.append(f"<li><b>{esc(TIER_LABEL[t])}:</b> {esc(source)}, {esc(conf_text(lod.confidence).split(', ')[-1])}. "
                     f"Day-to-day: {fmt.amt(per_day)} per adult per day.</li>")
    return '<ul class="method">' + "".join(items) + "</ul>"


PARTNER_NOTE = '<p class="fine">Partner buttons open the partner site, where you check live prices and book with them. May be affiliate links.</p>'


def partner_ctas(snap: Snapshot, d: DestinationData, fare: Fare, adults: int = ADULTS, children: int = 0, note: bool = True) -> str:
    out = []
    url = flight_link(snap, d.code, fare, adults, children)
    if url:
        out.append(sponsored(url, "See these flights on Aviasales" if fare.link else "Search these dates on Aviasales", "btn primary"))
    h = hotel_link(snap, d.code, fare, adults, children)
    if h:
        out.append(sponsored(h["url"], f"See hotels on {h['partner']}"))
    if not out:
        return ""
    return '<div class="ctas">' + "".join(out) + "</div>" + (PARTNER_NOTE if note else "")


def finder_link(page_path: str, params: dict[str, Any] | None = None) -> str:
    """Button into the trip finder, pre-filled with this page's trip (index.html reads these query parameters)."""
    href = rel(page_path, "")
    if params:
        href += "?" + urlencode({k: v for k, v in params.items() if v is not None})
    label = "Change the budget, dates or group size" if params else "Try your own budget, dates and group size"
    return f'<p><a class="btn primary wide" href="{esc(href)}">{esc(label)}</a></p>'


def signup_box(topic: str) -> str:
    """`topic` is HTML (escape plain text before passing it)."""
    # Placeholder until the owner picks an email provider (CASL consent + unsubscribe). No form, no data collected.
    return (f'<section class="box signup"><h2>Get a monthly email about {topic}</h2>'
            "<p>Coming soon: one email a month when whole trips from Toronto get cheaper. No spam, unsubscribe any time.</p></section>")


# ---- Page builders ----------------------------------------------------------------------------------------

@dataclass
class Builder:
    snap: Snapshot
    pricer: Pricer
    photos: dict[str, dict[str, str]]
    checks: dict[str, Any] | None = None  # gate_a.summary(), or None
    fmt: Fmt = field(init=False)
    pages: list[Page] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.fmt = Fmt(self.snap.today.isoformat())

    # Helpers

    def months(self) -> list[str]:
        return sorted({f.month for d in self.snap.dests for f in d.fares})

    def dest_months(self, d: DestinationData) -> list[str]:
        return sorted({f.month for f in d.fares})

    def week(self, d: DestinationData, month: str, tier: str) -> Package | None:
        return self.pricer.price(d, self.pricer.req(999_999, tier, month, HUB_NIGHTS), HUB_NIGHTS, month)

    def week_by_tier(self, d: DestinationData, month: str) -> dict[str, Package]:
        out = {}
        for t in ("budget", "mid", "upscale"):
            p = self.week(d, month, t)
            if p is not None:
                out[t] = p
        return out

    def dest_path(self, d: DestinationData) -> str:
        return f"{ORIGIN_SLUG}/{SLUGS.get(d.code, d.code.lower())}/"

    def dest_month_path(self, d: DestinationData, month: str) -> str:
        return f"{self.dest_path(d)}{month_slug(month)}/"

    def month_path(self, month: str) -> str:
        return f"{ORIGIN_SLUG}/{month_slug(month)}/"

    def budget_path(self, month: str, budget: int) -> str:
        return f"{self.month_path(month)}under-{budget}/"

    def about(self, d: DestinationData) -> dict[str, Any]:
        return {"@type": "TouristDestination", "name": name_of(d),
                "containedInPlace": {"@type": "Country", "name": COUNTRIES.get(d.country_code, d.country_code)}}

    def month_gate(self, d: DestinationData, month: str) -> tuple[bool, str]:
        fares = [f for f in d.fares if f.month == month]
        band = d.bands.get((month, "mid"))
        if len(fares) < GATE_MONTH_FARES:
            return False, f"{len(fares)} fares (< {GATE_MONTH_FARES})"
        if not any(GATE_MONTH_WEEK[0] <= f.nights <= GATE_MONTH_WEEK[1] for f in fares):
            return False, "no fare about a week long"
        if band is None or band.sample_size < GATE_MONTH_BAND_N:
            return False, f"mid hotel sample {band.sample_size if band else 0} (< {GATE_MONTH_BAND_N})"
        return True, ""

    # Destination hub

    def destination_hub(self, d: DestinationData) -> None:
        path = self.dest_path(d)
        months = self.dest_months(d)
        f = self.fmt
        by_month = {m: self.week_by_tier(d, m) for m in months}
        priced = {m: p for m, p in by_month.items() if "mid" in p or "budget" in p}
        if not priced:
            return
        # Headline: the month with the cheapest expected mid-range week (budget tier if no mid band).
        key_tier = lambda p: p.get("mid") or p.get("budget")
        head_month = min(priced, key=lambda m: key_tier(priced[m]).total.expected.amount)
        head = priced[head_month]
        mid, bud = head.get("mid"), head.get("budget")
        lead = mid or bud
        nm = name_of(d)
        answer = (f"A {lead.nights}-night trip for {ADULTS} adults from {ORIGIN_NAME} in {month_label(head_month)} is estimated at about "
                  f"<b>{f.amt(lead.total.expected)}</b> with a {TIER_SHORT['mid' if mid else 'budget']} hotel (likely {f.rng(lead.total)})")
        if mid and bud:
            answer += f", or about <b>{f.amt(bud.total.expected)}</b> with a budget hotel"
        share = lead.components[0].total.expected.amount / lead.total.expected.amount
        answer += (f". That covers flights, the hotel and day-to-day spending, estimated on {esc(day_long(self.snap.today))}. "
                   + (f"The flights are about {round(share * 100)}% of it." if share >= Decimal("0.5")
                      else f"The flights are only about {round(share * 100)}% of it; the rest is the stay."))

        month_rows = []
        for m in months:
            p = by_month[m]
            any_p = p.get("mid") or p.get("budget") or p.get("upscale")
            if any_p is None:
                continue
            link_path = self.dest_month_path(d, m)
            month_rows.append(
                f'<tr><th scope="row"><a href="{esc(rel(path, link_path))}">{esc(month_label(m))}</a></th>'
                f"<td>{esc(day(any_p.fare.depart))}–{esc(day(any_p.fare.ret))} ({any_p.nights} nights)</td>"
                f"<td>{f.amt(any_p.fare.price)}</td>"
                f"<td>{f.amt(p['budget'].total.expected) if 'budget' in p else '–'}</td>"
                f"<td>{f.amt(p['mid'].total.expected) if 'mid' in p else '–'}</td></tr>"
            )
        cheapest = sorted((x for x in d.fares if 3 <= x.nights <= 14), key=lambda x: (x.price.amount, x.depart))[:5]
        fare_rows = "".join(
            f"<tr><td>{esc(day(x.depart))}–{esc(day(x.ret))}</td><td>{x.nights}</td><td>{esc(stops(x)) or '–'}</td>"
            f"<td>{f.amt(x.price)}</td><td>{esc(day(x.found_on))}</td>"
            f"<td>{sponsored(x.link, 'See flights', 'lnk') if x.link else ''}</td></tr>"
            for x in cheapest
        )
        body = [
            f'<p class="answer">{answer}</p>',
            f"<h2>The whole bill for {lead.nights} nights in {esc(month_label(head_month))}</h2>",
            f"<p>{esc(day_long(lead.fare.depart))} to {esc(day_long(lead.fare.ret))}, {lead.nights} nights, {ADULTS} adults sharing one room.</p>",
            tier_table(f, head),
            method_list(f, head),
            partner_ctas(self.snap, d, lead.fare),
            f"<h2>When you go changes the price</h2><p>About a week ({GATE_MONTH_WEEK[0]}–{GATE_MONTH_WEEK[1]} nights) for {ADULTS} adults at the cheapest dates we found in each month.</p>",
            '<div class="scroll"><table><thead><tr><th>Month</th><th>Dates</th><th>Cheapest fare per person</th>'
            "<th>Trip total, budget hotel</th><th>Trip total, mid-range hotel</th></tr></thead><tbody>"
            + "".join(month_rows) + "</tbody></table></div>",
            f"<h2>Cheapest {esc(ORIGIN_NAME)}–{esc(nm)} fares we've seen</h2><p>Per person, return, CAD. Cached fares change quickly.</p>",
            ('<div class="scroll"><table><thead><tr><th>Dates</th><th>Nights</th><th>Airline</th><th>Fare</th><th>Seen on</th><th></th></tr></thead>'
            f"<tbody>{fare_rows}</tbody></table></div>"),
            self.faq_hub(d, by_month, head_month, mid, bud),
            INCLUDED,
            self.how_sure(path, d),
            advisory_block(self.snap, d),
            finder_link(path, self.finder_params(lead, head_month, 'mid' if mid else 'budget')),
            signup_box(esc(f"{nm} from {ORIGIN_NAME}")),
            self.related(d, path, head_month),
        ]
        gate = len(months) >= GATE_HUB_MONTHS
        self.pages.append(Page(
            path=path,
            title=f"{nm} trip cost from {ORIGIN_NAME}: a week for two in CAD",
            description=f"What a week in {nm} really costs from {ORIGIN_NAME} for two: flights, hotel and day-to-day spending as dated CAD estimates.",
            h1=f"{nm} from {ORIGIN_NAME}: what a trip really costs",
            eyebrow=f"{COUNTRIES.get(d.country_code, d.country_code)} · estimated {day_long(self.snap.today)}",
            body="".join(body),
            crumbs=[(f"From {ORIGIN_NAME}", f"{ORIGIN_SLUG}/"), (nm, path)],
            gate=gate, gate_reason="" if gate else f"fares in {len(months)} month(s)",
            photo=self.photos.get(d.code), about=self.about(d), has_partner_links=True, hub_of=d.code,
        ))

    def related(self, d: DestinationData, path: str, month: str) -> str:
        mine = self.week(d, month, "mid")
        others = []
        for o in self.snap.dests:
            if o.code == d.code:
                continue
            p = self.week(o, month, "mid")
            if p is not None and mine is not None:
                others.append((abs(p.total.expected.amount - mine.total.expected.amount), o, p))
        others.sort(key=lambda x: x[0])
        items = "".join(
            f'<li><a href="{esc(rel(path, self.dest_path(o)))}">{esc(name_of(o))}</a>: about a week in {esc(month_label(month))} '
            f"about {self.fmt.amt(p.total.expected)} (mid-range)</li>"
            for _, o, p in others[:3]
        )
        budgets = "".join(
            f'<li><a href="{esc(rel(path, self.budget_path(month, b)))}">Where {budget_amt(b)} gets two people in {esc(month_label(month))}</a></li>'
            for b in BUDGETS
        )
        return f'<section class="box"><h2>Similar budgets</h2><ul>{items}</ul><h3>By budget</h3><ul>{budgets}</ul></section>'

    # Destination x month

    def destination_month(self, d: DestinationData, month: str) -> None:
        path = self.dest_month_path(d, month)
        f = self.fmt
        pk = self.week_by_tier(d, month)
        lead = pk.get("mid") or pk.get("budget")
        if lead is None:
            return
        nm = name_of(d)
        gate, why = self.month_gate(d, month)
        answer = (f"A {lead.nights}-night trip for {ADULTS} adults from {ORIGIN_NAME} in {month_label(month)} is estimated at about "
                  f"<b>{f.amt(lead.total.expected)}</b> with a {TIER_SHORT['mid' if 'mid' in pk else 'budget']} hotel (likely {f.rng(lead.total)})"
                  + (f", or about <b>{f.amt(pk['budget'].total.expected)}</b> with a budget hotel" if "mid" in pk and "budget" in pk else "")
                  + f". Estimated on {esc(day_long(self.snap.today))}.")
        # What common budgets buy this month: longest trip that fits, per tier.
        rows = []
        for b in BUDGETS:
            cells = []
            for t in ("budget", "mid"):
                p = self.pricer.best(d, self.pricer.req(b, t, month, None))
                if p is None:
                    cells.append("<td>–</td>")
                elif p.fit == "over":
                    cells.append(f"<td>Doesn't fit (shortest priced: {p.nights} nights, about {f.amt(p.total.expected)})</td>")
                else:
                    label = "fits" if p.fit == "within" else "stretch"
                    cells.append(f"<td><b>{p.nights} nights</b>, {esc(day(p.fare.depart))}–{esc(day(p.fare.ret))}: about "
                                 f"{f.amt(p.total.expected)} <span class=\"tag {p.fit}\">{label}</span></td>")
            rows.append(f'<tr><th scope="row">{budget_amt(b)}</th>{"".join(cells)}</tr>')
        in_month = sorted((x for x in d.fares if x.month == month and x.nights >= 3), key=lambda x: (x.price.amount, x.depart))[:5]
        fare_rows = "".join(
            f"<tr><td>{esc(day(x.depart))}–{esc(day(x.ret))}</td><td>{x.nights}</td><td>{esc(stops(x)) or '–'}</td>"
            f"<td>{f.amt(x.price)}</td><td>{esc(day(x.found_on))}</td>"
            f"<td>{sponsored(x.link, 'See flights', 'lnk') if x.link else ''}</td></tr>"
            for x in in_month
        )
        siblings = " · ".join(
            f'<a href="{esc(rel(path, self.dest_month_path(d, m)))}">{esc(month_label(m))}</a>' for m in self.dest_months(d) if m != month
        )
        body = [
            f'<p class="answer">{answer}</p>',
            f"<h2>{lead.nights} nights in {esc(month_label(month))}, three ways</h2>",
            f"<p>{esc(day_long(lead.fare.depart))} to {esc(day_long(lead.fare.ret))}, {lead.nights} nights, {ADULTS} adults sharing one room.</p>",
            tier_table(f, pk),
            method_list(f, pk),
            partner_ctas(self.snap, d, lead.fare),
            (f"<h2>What common budgets get you in {esc(month_label(month))}</h2>"
            f"<p>The longest trip for {ADULTS} adults that fits each budget at the cheapest dates we found. "
            "“Stretch” means it fits only if prices land near the low end of our range.</p>"),
            ('<div class="scroll"><table><thead><tr><th>Budget</th><th>Budget hotel</th><th>Mid-range hotel</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table></div>"),
            f"<h2>Cheapest fares in {esc(month_label(month))}</h2>",
            ('<div class="scroll"><table><thead><tr><th>Dates</th><th>Nights</th><th>Airline</th><th>Fare per person</th><th>Seen on</th><th></th></tr></thead>'
            f"<tbody>{fare_rows}</tbody></table></div>"),
            (f"<p>Other months: {siblings}</p>" if siblings else ""),
            INCLUDED,
            self.how_sure(path, d),
            advisory_block(self.snap, d),
            finder_link(path, self.finder_params(lead, month, 'mid' if 'mid' in pk else 'budget')),
            signup_box(esc(f"{nm} from {ORIGIN_NAME}")),
        ]
        self.pages.append(Page(
            path=path,
            title=f"{nm} from {ORIGIN_NAME} in {month_label(month)}: cost for two",
            description=f"What a trip to {nm} from {ORIGIN_NAME} costs in {month_label(month)}: flights, hotel and daily spending, dated estimates in CAD.",
            h1=f"{nm} from {ORIGIN_NAME} in {month_label(month)}",
            eyebrow=f"{COUNTRIES.get(d.country_code, d.country_code)} · estimated {day_long(self.snap.today)}",
            body="".join(body),
            crumbs=[(f"From {ORIGIN_NAME}", f"{ORIGIN_SLUG}/"), (nm, self.dest_path(d)), (month_label(month), path)],
            gate=gate, gate_reason=why, photo=self.photos.get(d.code), about=self.about(d), has_partner_links=True,
        ))

    # Month x budget

    def budget_results(self, month: str, budget: int, tier: str, adults: int = ADULTS, children: int = 0,
                       dests: Iterable[DestinationData] | None = None, window: dict | None = None) -> tuple[list[Package], list[Package]]:
        req = self.pricer.req(budget, tier, month, None, adults, children)
        pkgs = [p for d in (dests if dests is not None else self.snap.dests) if (p := self.pricer.best(d, req, window)) is not None]
        fits = rank(pkgs, req)
        over = sorted((p for p in pkgs if p.fit == "over"), key=lambda p: p.total.expected.amount)
        return fits, over

    def result_card(self, page_path: str, p: Package, adults: int = ADULTS, children: int = 0) -> str:
        f = self.fmt
        d = p.destination
        ph = self.photos.get(d.code)
        names = {"flights": f"Flights for {adults + children}", "lodging": f"Hotel, {p.nights} nights", "daily": "Day-to-day"}
        comps = "".join(f"<li><span>{names[c.name]}</span><b>{f.amt(c.total.expected)}</b></li>" for c in p.components)
        warn = ""
        if p.components[0].confidence == "estimated":
            warn = '<p class="fine">Rougher than the others: no cached fare matched this trip length, so the flight cost is estimated from other dates.</p>'
        lodging = p.components[1]
        if "from " in lodging.detail and lodging.confidence.startswith("sampled"):
            n = int(lodging.detail.split("from ")[1].split(" ")[0])
            if n < GATE_MONTH_BAND_N:
                warn += f'<p class="fine">Hotel price from only {n} hotels: expect fewer rooms at this price.</p>'
        img = (f'<figure class="photo"><img src="{esc(ph["src"])}" alt="{esc(ph["alt"])}" loading="lazy" width="960" height="600">'
               f'<figcaption class="credit">Photo: {esc(ph["author"])}, <a href="{esc(ph["page"])}" target="_blank" rel="noopener">{esc(ph["license"])}</a></figcaption></figure>'
               if ph else "")
        tag = "Fits" if p.fit == "within" else "Stretch"
        return (
            f'<article class="card">{img}<div class="body">'
            f'<h3><a href="{esc(rel(page_path, self.dest_month_path(d, p.month)))}">{esc(name_of(d))}</a> <span class="tag {p.fit}">{tag}</span></h3>'
            f'<p class="when">{esc(day(p.fare.depart))}–{esc(day(p.fare.ret))} · {p.nights} nights</p>'
            f'<p class="big">{f.amt(p.total.expected)}</p><p class="fine">likely {f.rng(p.total)}</p>'
            f'<ul class="rows">{comps}</ul>{warn}{partner_ctas(self.snap, d, p.fare, adults, children, note=False)}</div></article>'
        )

    def month_budget(self, month: str, budget: int) -> None:
        path = self.budget_path(month, budget)
        f = self.fmt
        fits_mid, _ = self.budget_results(month, budget, "mid")
        fits_bud, over_bud = self.budget_results(month, budget, "budget")
        within_mid = [p for p in fits_mid if p.fit == "within"]
        within_bud = [p for p in fits_bud if p.fit == "within"]
        n_dest = len(self.snap.dests)
        if within_mid:
            answer = (f"Of the {n_dest} destinations we track from {ORIGIN_NAME}, <b>{len(within_mid)} fit {budget_amt(budget)} for two people "
                      f"in {month_label(month)} with a mid-range hotel</b>")
            answer += f", and {len(within_bud)} with a budget hotel." if within_bud else "."
        elif within_bud:
            answer = (f"Of the {n_dest} destinations we track from {ORIGIN_NAME}, <b>{len(within_bud)} fit {budget_amt(budget)} for two people "
                      f"in {month_label(month)}</b> if you're happy with a budget hotel: "
                      + esc(", ".join(name_of(p.destination) for p in within_bud[:3])) + ". With a mid-range hotel, nothing fits fully.")
        else:
            answer = (f"Nothing we track fits {budget_amt(budget)} for two people in {month_label(month)} at the expected price. "
                      f"{len(fits_bud)} trips are a stretch with a budget hotel.")
        answer += f" Flights, hotel and day-to-day spending, estimated on {esc(day_long(self.snap.today))}."
        per = budget_amt(budget / ADULTS)
        body = [f'<p class="answer">{answer}</p>',
                f"<p>{budget_amt(budget)} for two is {per} each for flights, a room and food. We'd rather show a short honest list than pad it.</p>"]
        for label, fits in (("With a mid-range hotel (4★)", fits_mid), ("With a budget hotel (up to 3★)", fits_bud)):
            body.append(f"<h2>{esc(label)}</h2>")
            if fits:
                body.append('<div class="grid">' + "".join(self.result_card(path, p) for p in fits[:9]) + "</div>" + PARTNER_NOTE)
            else:
                body.append("<p>Nothing fits or comes close at this budget.</p>")
        if over_bud:
            rows = []
            for p in over_bud[:12]:
                big = max(p.components, key=lambda c: c.total.expected.amount)
                reason = {"flights": f"Flights: about {f.amt(big.total.expected)} for two", "lodging": f"Hotel: about {f.amt(big.total.expected)}",
                          "daily": f"Day-to-day spending: about {f.amt(big.total.expected)}"}[big.name]
                rows.append(f'<tr><th scope="row"><a href="{esc(rel(path, self.dest_month_path(p.destination, month)))}">{esc(name_of(p.destination))}</a></th>'
                            f"<td>{p.nights}</td><td>{f.amt(p.total.expected)}</td><td>{reason}</td></tr>")
            body.append(f"<h2>Doesn't fit {budget_amt(budget)} in {esc(month_label(month))}, and what it would take</h2>"
                        "<p>Budget hotel, cheapest dates we found.</p>"
                        '<div class="scroll"><table><thead><tr><th>Destination</th><th>Nights</th><th>Expected total</th><th>The main cost</th></tr></thead>'
                        f"<tbody>{''.join(rows)}</tbody></table></div>")
        priced = {p.destination.code for p in fits_bud + over_bud}
        missing = [name_of(d) for d in self.snap.dests if d.code not in priced]
        if missing:
            body.append(f"<p class=\"fine\">No {esc(month_label(month))} fares cached for: {esc(', '.join(missing))}.</p>")
        others = " · ".join(f'<a href="{esc(rel(path, self.budget_path(month, b)))}">{budget_amt(b)}</a>' for b in BUDGETS if b != budget)
        months = " · ".join(f'<a href="{esc(rel(path, self.budget_path(m, budget)))}">{esc(month_label(m))}</a>' for m in self.months() if m != month)
        body += [
            f"<p>Other budgets: {others}</p>" + (f"<p>Same budget, other months: {months}</p>" if months else ""),
            ('<section class="box"><h2>How we worked this out</h2><ul>'
            f"<li><b>Who:</b> {ADULTS} adults, one room.</li><li><b>Trip length:</b> for each destination, the longest trip (3–14 nights) "
            f"that fits at the cheapest {esc(month_label(month))} dates we had, otherwise the closest.</li>"
            "<li><b>Flights:</b> cheapest cached return fare for those dates, plus a margin.</li>"
            "<li><b>Hotels:</b> a sample of real hotel prices for the month, by comfort level.</li>"
            "<li><b>Day-to-day:</b> our estimate from each country's price level compared with Canada.</li></ul></section>"),
            INCLUDED, self.how_sure(path), finder_link(path, {"budget": budget, "adults": ADULTS, "month": month, "tier": "mid"}), signup_box(f"trips under {budget_amt(budget)} from {esc(ORIGIN_NAME)}"),
        ]
        count = len(fits_mid) + len([p for p in fits_bud if p.destination.code not in {q.destination.code for q in fits_mid}])
        gate = count >= GATE_BUDGET_RESULTS
        self.pages.append(Page(
            path=path,
            title=f"Where ${budget:,} gets two people from {ORIGIN_NAME} in {month_label(month)}",
            description=f"Whole trips from {ORIGIN_NAME} that fit ${budget:,} for two in {month_label(month)}: flights, hotel and daily spending, dated CAD estimates.",
            h1=f"Where ${budget:,} gets two people from {ORIGIN_NAME} in {month_label(month)}",
            eyebrow=f"{BRAND_DESCRIPTOR} · estimated {day_long(self.snap.today)}",
            body="".join(body),
            crumbs=[(f"From {ORIGIN_NAME}", f"{ORIGIN_SLUG}/"), (month_label(month), self.month_path(month)), (f"Under ${budget:,}", path)],
            gate=gate, gate_reason="" if gate else f"{count} trips fit or stretch (< {GATE_BUDGET_RESULTS})",
            article=True, has_partner_links=True,
        ))

    # Month hub

    def month_hub(self, month: str) -> None:
        path = self.month_path(month)
        f = self.fmt
        rows = []
        for d in self.snap.dests:
            pk = self.week_by_tier(d, month)
            if not pk:
                continue
            lead = pk.get("mid") or pk.get("budget")
            rows.append((lead.total.expected.amount, d, pk))
        rows.sort(key=lambda x: x[0])
        table = "".join(
            f'<tr><th scope="row"><a href="{esc(rel(path, self.dest_month_path(d, month)))}">{esc(name_of(d))}</a></th>'
            f"<td>{(pk.get('mid') or pk.get('budget')).nights}</td>"
            f"<td>{f.amt(pk['budget'].total.expected) if 'budget' in pk else '–'}</td>"
            f"<td>{f.amt(pk['mid'].total.expected) if 'mid' in pk else '–'}</td></tr>"
            for _, d, pk in rows
        )
        budgets = "".join(f'<li><a href="{esc(rel(path, self.budget_path(month, b)))}">Where {budget_amt(b)} gets two people</a></li>' for b in BUDGETS)
        body = (f'<p class="answer">About a week for {ADULTS} adults from {ORIGIN_NAME} in {esc(month_label(month))}, for each of the '
                f"{len(rows)} destinations we have fares for, cheapest first. Estimated on {esc(day_long(self.snap.today))}.</p>"
                f"<h2>By budget</h2><ul>{budgets}</ul>"
                f"<h2>About a week in {esc(month_label(month))}, cheapest first</h2>"
                '<div class="scroll"><table><thead><tr><th>Destination</th><th>Nights</th><th>Total, budget hotel</th><th>Total, mid-range hotel</th></tr></thead>'
                f"<tbody>{table}</tbody></table></div>{INCLUDED}{self.how_sure(path)}{finder_link(path, {'adults': ADULTS, 'month': month})}")
        gate = len(rows) >= GATE_BUDGET_RESULTS
        self.pages.append(Page(
            path=path, title=f"Trips from {ORIGIN_NAME} in {month_label(month)}: what a week costs for two",
            description=f"What a week costs from {ORIGIN_NAME} in {month_label(month)} for {len(rows)} destinations, flights, hotel and daily spending in CAD.",
            h1=f"Trips from {ORIGIN_NAME} in {month_label(month)}", eyebrow=f"{BRAND_DESCRIPTOR} · estimated {day_long(self.snap.today)}",
            body=body, crumbs=[(f"From {ORIGIN_NAME}", f"{ORIGIN_SLUG}/"), (month_label(month), path)], gate=gate,
            gate_reason="" if gate else "too few destinations",
        ))

    # March break

    def march_break(self) -> None:
        path = f"{ORIGIN_SLUG}/march-break/"
        upcoming = [(y, s) for y, s in sorted(MARCH_BREAK.items()) if s + timedelta(days=4) >= self.snap.today]
        if not upcoming:
            return
        year, start = upcoming[0]
        adults, children = MARCH_BREAK_GROUP
        w = {"departFrom": (start - timedelta(days=3)).isoformat(), "departTo": (start + timedelta(days=1)).isoformat(),
             "retFrom": (start + timedelta(days=4)).isoformat(), "retTo": (start + timedelta(days=8)).isoformat()}
        month = start.strftime("%Y-%m")
        dests = [window_dest(d, w) for d in self.snap.dests]
        dests = [d for d in dests if d.fares]
        group = group_text(adults, children)
        body = [(f'<p class="answer">Ontario\'s March break {year} is expected to be the week of <b>{esc(day_long(start))}</b> '
                "(check your school board). Prices for that week tend to climb as it gets closer, so this page updates every day.</p>")]
        sections = 0
        if not dests:
            body.append(f"<p>We don't have fares for March break {year} yet. Airlines' cached fares only reach about three months ahead, "
                        "so they should appear here in early December. Until then, use the trip finder with your own dates.</p>")
        else:
            for b in MARCH_BREAK_BUDGETS:
                for t in ("budget", "mid"):
                    fits, _ = self.budget_results(month, b, t, adults, children, dests, w)
                    body.append(f"<h2>What fits {budget_amt(b)} for {esc(group)} ({esc(TIER_SHORT[t])} hotel)</h2>")
                    if fits:
                        sections += 1
                        body.append('<div class="grid">' + "".join(self.result_card(path, p, adults, children) for p in fits[:6]) + "</div>" + PARTNER_NOTE)
                    else:
                        body.append("<p>Nothing fits or comes close yet.</p>")
        body += [(f"<p class=\"fine\">Family of four: two adults and two children sharing one room; children's day-to-day costs counted at 70% of an adult's. "
                 f"Departures {esc(day(date.fromisoformat(w['departFrom'])))}–{esc(day(date.fromisoformat(w['departTo'])))}, "
                 f"returns {esc(day(date.fromisoformat(w['retFrom'])))}–{esc(day(date.fromisoformat(w['retTo'])))}.</p>"),
                 INCLUDED, self.how_sure(path), finder_link(path, {"budget": MARCH_BREAK_BUDGETS[-1], "adults": adults, "children": children, "month": month, "nights": 7}), signup_box(esc(f"March break {year} from {ORIGIN_NAME}"))]
        gate = len(dests) >= GATE_BUDGET_RESULTS and sections > 0
        self.pages.append(Page(
            path=path, title=f"March break {year} from {ORIGIN_NAME}: trips for a family of four",
            description=f"Whole-trip estimates for Ontario's March break {year} from {ORIGIN_NAME} for a family of four: flights, hotel and daily spending in CAD.",
            h1=f"March break {year} from {ORIGIN_NAME}: what fits your budget", eyebrow=f"{BRAND_DESCRIPTOR} · estimated {day_long(self.snap.today)}",
            body="".join(body), crumbs=[(f"From {ORIGIN_NAME}", f"{ORIGIN_SLUG}/"), (f"March break {year}", path)],
            gate=gate, gate_reason="" if gate else "no or too few March break fares yet", article=True, has_partner_links=bool(dests),
        ))

    # Origin hub

    def origin_hub(self) -> None:
        path = f"{ORIGIN_SLUG}/"
        f = self.fmt
        cards = []
        for d in self.snap.dests:
            ms = self.dest_months(d)
            best = None
            for m in ms:
                p = self.week(d, m, "mid") or self.week(d, m, "budget")
                if p and (best is None or p.total.expected.amount < best.total.expected.amount):
                    best = p
            if best is None:
                continue
            ph = self.photos.get(d.code)
            img = f'<img src="{esc(ph["src"])}" alt="{esc(ph["alt"])}" loading="lazy" width="960" height="600">' if ph else ""
            cards.append((best.total.expected.amount,
                          (f'<a class="tile" href="{esc(rel(path, self.dest_path(d)))}">{img}<span><b>{esc(name_of(d))}</b>'
                          f" about a week from {f.amt(best.total.expected)} for two, in {esc(month_label(best.month))}</span></a>")))
        cards.sort(key=lambda x: x[0])
        month_links = "".join(
            f'<li><a href="{esc(rel(path, self.month_path(m)))}">{esc(month_label(m))}</a>: '
            + " · ".join(f'<a href="{esc(rel(path, self.budget_path(m, b)))}">under {budget_amt(b)}</a>' for b in BUDGETS) + "</li>"
            for m in self.months()
        )
        mb = ""
        if any(s + timedelta(days=4) >= self.snap.today for s in MARCH_BREAK.values()):
            mb = f'<li><a href="{esc(rel(path, ORIGIN_SLUG + "/march-break/"))}">March break from {esc(ORIGIN_NAME)}</a></li>'
        body = (f'<p class="answer">Whole-trip estimates from {esc(ORIGIN_NAME)} for {len(cards)} destinations: flights, a hotel and '
                f"day-to-day spending for two, in CAD, estimated on {esc(day_long(self.snap.today))}.</p>"
                f"<h2>By month and budget</h2><ul>{month_links}{mb}</ul>"
                f'<h2>Destinations, cheapest week first</h2><div class="tiles">{"".join(c for _, c in cards)}</div>'
                f"{INCLUDED}<p><a href=\"{esc(rel(path, METHOD_PATH))}\">How we estimate these numbers, and how accurate they've been</a></p>"
                f"{finder_link(path)}")
        self.pages.append(Page(
            path=path, title=f"Trip costs from {ORIGIN_NAME} by destination and budget, in CAD",
            description=f"Whole-trip cost estimates from {ORIGIN_NAME} for {len(cards)} destinations, by month and budget, in CAD.",
            h1=f"Trips from {ORIGIN_NAME}, all in", eyebrow=BRAND_DESCRIPTOR, body=body,
            crumbs=[(f"From {ORIGIN_NAME}", path)], gate=True,
        ))

    # Accuracy, questions and the method page

    def finder_params(self, p: Package, month: str, tier: str) -> dict[str, Any]:
        return {"budget": budget_for(p), "adults": ADULTS, "month": month, "nights": p.nights, "tier": tier}

    def trips_checked(self, code: str) -> list[dict[str, Any]]:
        return [t for t in (self.checks or {}).get("trips", []) if t["code"] == code]

    def how_sure(self, path: str, d: DestinationData | None = None) -> str:
        out = [('<section class="box"><h2>How sure are these numbers?</h2>'
               "<p>Flights come from cached fares: prices other travellers saw in recent searches, so the price you find can differ. "
               "We add a margin above the cached fare for the expected figure and more for the high one. Hotel prices are a sample "
               "of real rates for the same month, adjusted for busy dates. Day-to-day spending is our estimate from each country's "
               "price level compared with Canada (World Bank data), and it's the least checked part.</p>")]
        c = self.checks
        if c:
            worst = max(("flights", "hotel"), key=lambda k: c[k]["median_abs"])
            out.append(
                f"<p>On {esc(day_long(date.fromisoformat(c['checked_on'])))} we checked {c['n']} trips by hand against Google Flights "
                f"and Booking.com. Our expected whole-trip total was a median of {pct(c['total']['median_abs'])} away from the real price, "
                f"and the real total fell inside our range for {c['total']['inside']} of the {c['n']}. The least accurate part was "
                f"{'the hotel' if worst == 'hotel' else 'the flights'} (a median of {pct(c[worst]['median_abs'])} off).</p>")
            mine = self.trips_checked(d.code) if d else []
            if mine:
                parts = "; ".join(
                    f"{esc(day_long(date.fromisoformat(t['depart'])))}, {t['nights']} nights: {pct(t['total_err'])} "
                    f"{'under' if t['total_err'] < 0 else 'over'} the real total" for t in mine)
                out.append(f"<p>For {esc(name_of(d))} we checked {len(mine)} trip{'s' if len(mine) > 1 else ''}: {parts}. "
                           "These checks used the estimates we showed on that day.</p>")
        out.append(f'<p><a href="{esc(rel(path, METHOD_PATH))}">How we estimate, and every trip we checked</a></p></section>')
        return "".join(out)

    def faq_hub(self, d: DestinationData, by_month: dict[str, dict[str, Package]], head_month: str,
                mid: Package | None, bud: Package | None) -> str:
        """Questions people ask about a destination, answered only from the snapshot and the engine."""
        f = self.fmt
        nm = name_of(d)
        lead = mid or bud
        tier = "mid" if mid else "budget"
        qa: list[tuple[str, str]] = []
        a = (f"About {f.amt(lead.total.expected)} for {lead.nights} nights in {esc(month_label(head_month))} with a "
             f"{TIER_SHORT[tier]} hotel, in the cheapest month we have fares for")
        if mid and bud:
            a += f", or about {f.amt(bud.total.expected)} with a budget hotel"
        qa.append((f"How much does a week in {nm} cost for two from {ORIGIN_NAME}?",
                   a + ". That's return flights for two, the hotel and day-to-day spending, as an estimate in CAD."))
        same_tier = {m: p[tier] for m, p in by_month.items() if tier in p}
        if len(same_tier) >= 2:
            cheap = min(same_tier, key=lambda m: same_tier[m].total.expected.amount)
            dear = max(same_tier, key=lambda m: same_tier[m].total.expected.amount)
            ms = sorted(same_tier)
            qa.append((f"What's the cheapest month to go to {nm} from {ORIGIN_NAME}?",
                       (f"Of the months we have fares for ({esc(month_label(ms[0]))} to {esc(month_label(ms[-1]))}), "
                       f"{esc(month_label(cheap))} is the cheapest: about {f.amt(same_tier[cheap].total.expected)} for "
                       f"{same_tier[cheap].nights} nights with a {TIER_SHORT[tier]} hotel. {esc(month_label(dear))} is the most "
                       f"expensive, at about {f.amt(same_tier[dear].total.expected)} for {same_tier[dear].nights} nights. "
                       "Cached fares only reach about three months ahead, so later months aren't here yet.")))
        fares = [x for x in d.fares if 3 <= x.nights <= 14]
        if fares:
            x0 = min(fares, key=lambda x: (x.price.amount, x.depart))
            middle = Money.of(statistics.median(float(x.price.amount) for x in fares))
            qa.append((f"How much is a return flight from {ORIGIN_NAME} to {nm}?",
                       (f"The cheapest return fare we've seen is {f.amt(x0.price)} per person ({esc(day(x0.depart))} to {esc(day(x0.ret))}"
                       f"{', ' + esc(stops(x0)) if stops(x0) else ''}), seen on {esc(day_long(x0.found_on))}. The middle fare of the "
                       f"{len(fares)} we have cached is {f.amt(middle)}. Check the live price: cached fares change quickly.")))
        if d.price_level is not None:
            per = {t: Money.of(DAILY_BASE_CAD[t]) * d.price_level for t in ("budget", "mid", "upscale")}
            qa.append((f"How much spending money do I need in {nm}?",
                       (f"We estimate about {f.amt(per['budget'])} per adult per day on a budget, {f.amt(per['mid'])} mid-range and "
                       f"{f.amt(per['upscale'])} upscale, for food, local transport and modest entry fees. For the {lead.nights}-night "
                       f"trip above, that's about {f.amt(lead.components[2].total.expected)} for two. It's the least checked part of our "
                       "estimate, so leave some room.")))
        items = "".join(f"<h3>{esc(q)}</h3><p>{a}</p>" for q, a in qa)
        return f'<section class="faq"><h2>Common questions about {esc(nm)} from {esc(ORIGIN_NAME)}</h2>{items}</section>'

    def method_page(self) -> None:
        path = METHOD_PATH
        f = self.fmt
        c = self.checks
        daily = " · ".join(f"{esc(TIER_SHORT[t])}: {f.amt(DAILY_BASE_CAD[t])}" for t in ("budget", "mid", "upscale"))
        body = [
            ('<p class="answer">Every total on this site is an estimate of the whole trip: return flights for everyone, a hotel room '
             "for every night and day-to-day spending, added up in Canadian dollars and shown as a range (low, expected, high). "
             f"The numbers are rebuilt every day from the data we hold. The latest refresh was on {esc(day_long(self.snap.today))}.</p>"),
            ("<h2>Flights</h2><p>We use cached return fares from Toronto (Travelpayouts/Aviasales): prices other travellers saw in recent "
            "searches, each with the date it was seen. For a trip, we take the cheapest cached fare for the dates and add a margin for the "
            "expected figure and a bigger one for the high figure, because cached fares are often gone by the time you search. "
            "Fares only reach about three months ahead.</p>"),
            ("<h2>Hotels</h2><p>For each destination and month we sample real hotel rates (LiteAPI) and keep the low, middle and high "
            "price per night for three comfort levels: budget (up to 3★), mid-range (4★) and upscale (5★). We drop spiky quotes and "
            "all-inclusive resorts so the sample stays comparable, and adjust for busy dates. The page shows how many hotels each "
            "figure comes from.</p>"),
            ("<h2>Day-to-day spending</h2><p>Food, local transport and modest entry fees. We start from a Canadian daily amount per "
             f"adult ({daily}) and scale it by each country's price level compared with Canada (World Bank International Comparison "
             f"Program, CC BY 4.0). Children count at {round(CHILD_DAILY_SHARE * 100)}% of an adult. This is the part we can't check against a booking site, so treat "
             "it as the roughest number.</p>"),
            ("<h2>Fits, stretch and doesn't fit</h2><p>A trip <b>fits</b> when the expected total is within your budget. It's a "
            "<b>stretch</b> when the expected total is over your budget but the low end of the range is under it: it works only if "
            "prices land near the low end. Anything else doesn't fit, and we say what it would take.</p>"),
        ]
        if c:
            rows = "".join(
                f"<tr><th scope=\"row\">{label}</th><td>{pct_signed(c[k]['median'])}</td><td>{pct(c[k]['median_abs'])}</td>"
                f"<td>{pct(c[k]['p90_abs'])}</td><td>{c[k]['inside']} of {c['n']}</td></tr>"
                for k, label in (("flights", "Flights (per person)"), ("hotel", "Hotel (per night)"), ("total", "Whole trip")))
            names = {d.code: name_of(d) for d in self.snap.dests}
            trips = "".join(
                f"<tr><td>{esc(names.get(t['code'], t['code']))}</td><td>{esc(day_long(date.fromisoformat(t['depart'])))}</td>"
                f"<td>{t['nights']}</td><td>{'yes' if t['holiday'] else ''}</td><td>{pct_signed(t['total_err'])}</td>"
                f"<td>{'yes' if t['inside'] else 'no'}</td></tr>"
                for t in sorted(c["trips"], key=lambda t: (names.get(t["code"], t["code"]), t["depart"])))
            body += [
                (f"<h2>How accurate is it?</h2><p>On {esc(day_long(date.fromisoformat(c['checked_on'])))} we picked {c['n']} trips the "
                 "site would really show (a mix of destinations, months, group sizes and hotel levels, including holiday dates) and "
                 "looked up the real price of each on Google Flights and Booking.com. Error is our expected figure minus the real price, "
                 "as a share of the real price: negative means we were too low.</p>"),
                ('<div class="scroll"><table><thead><tr><th></th><th>Median error</th><th>Median size of error</th>'
                 "<th>9 in 10 trips within</th><th>Real price inside our range</th></tr></thead>"
                 f"<tbody>{rows}</tbody></table></div>"),
                ("<p>Day-to-day spending is our estimate on both sides of this check, so it isn't tested here. Hotels are the least "
                 "accurate part: a booking site's first page and our sample can be far apart for resort areas.</p>"),
                "<h3>Every trip we checked</h3>",
                ('<div class="scroll"><table><thead><tr><th>Destination</th><th>Departing</th><th>Nights</th><th>Holiday</th>'
                 f"<th>Whole-trip error</th><th>Inside our range</th></tr></thead><tbody>{trips}</tbody></table></div>"),
            ]
        body += [
            ("<h2>What we leave out</h2><ul><li>All-inclusive meal plans: our hotel prices are for the room</li><li>Checked bags, "
             "if the fare doesn't include them</li><li>Travel insurance, tours and tips</li><li>Getting to and parking at the airport</li>"
             "<li>Resort fees the hotel doesn't list in advance</li></ul>"),
            ("<h2>What we don't do</h2><p>We don't sell trips or take payments. Prices are estimates, not quotes: the partner's site "
             "shows the price you'll actually pay, and you book and pay there. Some partner links may earn us a commission; partners "
             "don't pay for placement. No number on this site is written by an AI "
             "model: they all come from the data and the calculation described here.</p>"),
            finder_link(path),
        ]
        self.pages.append(Page(
            path=path, title=f"How we estimate trip costs from {ORIGIN_NAME}",
            description="How the whole-trip estimates are made (flights, hotels, daily spending), what they leave out, and the results of our hand checks against real prices.",
            h1="How we estimate, and how accurate we've been", eyebrow=f"{BRAND_DESCRIPTOR} · updated {day_long(self.snap.today)}",
            body="".join(body), crumbs=[(f"From {ORIGIN_NAME}", f"{ORIGIN_SLUG}/"), ("How we estimate", path)], gate=True, article=True,
        ))

    def build_all(self) -> list[Page]:
        self.origin_hub()
        for d in self.snap.dests:
            self.destination_hub(d)
            for m in self.dest_months(d):
                self.destination_month(d, m)
        for m in self.months():
            self.month_hub(m)
            for b in BUDGETS:
                self.month_budget(m, b)
        self.march_break()
        self.method_page()
        return self.pages


# ---- Writing -----------------------------------------------------------------------------------------------

def generate(snapshot_path: Path | None = None, site_dir: Path | None = None, indexable: bool | None = None,
             manifest_path: Path | None = None, checks_path: Path | None = None) -> dict[str, int]:
    site_dir = site_dir or ROOT / "site"
    snapshot_path = snapshot_path or site_dir / "data.json"
    manifest_path = manifest_path or site_dir / "tests" / "pages-manifest.json"
    if indexable is None:
        indexable = os.environ.get("TRIPFINDER_INDEXABLE", "").lower() == "true"
    snap = load_snapshot(snapshot_path)
    builder = Builder(snap, Pricer(snap), load_photos(site_dir / "photos.js"), gate_a_summary(checks_path or CHECKS_PATH))
    pages = builder.build_all()
    out_root = site_dir / ORIGIN_SLUG
    if out_root.exists():
        shutil.rmtree(out_root)  # generated output only
    for p in pages:
        target = site_dir / p.path / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(p, snap, indexable), encoding="utf8")
    listed = [p for p in pages if indexable and p.gate]
    if listed:
        urls = "".join(f"<url><loc>{esc(SITE_URL + p.path)}</loc><lastmod>{snap.today.isoformat()}</lastmod></url>" for p in listed)
        (out_root / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf8")
    out_root.mkdir(parents=True, exist_ok=True)
    # The trip finder links each result card to its destination hub when one was written (site/index.html card()).
    (out_root / "index.json").write_text(
        json.dumps({p.hub_of: p.path for p in pages if p.hub_of}, indent=0, sort_keys=True), encoding="utf8")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "today": snap.today.isoformat(),
        "pages": [{"path": p.path, "gate": p.gate, "gateReason": p.gate_reason} for p in pages],
        "calls": builder.pricer.calls,
    }, indent=0), encoding="utf8")
    return {"pages": len(pages), "pass_gate": sum(p.gate for p in pages), "indexable": len(listed), "priced": len(builder.pricer.calls)}


def visible_text(page_html: str) -> str:
    """Page text without tags, scripts, styles or attribute values (for wording tests)."""
    import re

    t = re.sub(r"<(script|style)\b.*?</\1>", " ", page_html, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t))


def banned_in(text: str) -> list[str]:
    import re

    low = text.lower()
    return [w for w in BANNED_PHRASES if re.search(r"\b" + re.escape(w) + r"\b", low)]

