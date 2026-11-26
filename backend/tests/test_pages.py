"""Guardrails for the generated destination and month pages (docs/content/programmatic-pages.md)."""

import json
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

from tripfinder import pages
from tripfinder.config import ROOT
from tripfinder.engine import DestinationData, Fare, LodgingBand
from tripfinder.money import Money, PriceRange

SITE = ROOT / "site"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Generate every page from the committed snapshot into a temporary site folder."""
    site = tmp_path_factory.mktemp("site")
    shutil.copy(SITE / "data.json", site / "data.json")
    shutil.copy(SITE / "photos.js", site / "photos.js")
    stats = pages.generate(site_dir=site, indexable=False, manifest_path=site / "manifest.json")
    files = sorted((site / pages.ORIGIN_SLUG).rglob("index.html"))
    return site, stats, {f: f.read_text(encoding="utf8") for f in files}


def test_generates_the_top_pages(built):
    site, stats, _ = built
    assert stats["pages"] == len(json.loads((site / "manifest.json").read_text())["pages"])
    for p in ["from-toronto/", "from-toronto/cancun/", "from-toronto/march-break/", "from-toronto/punta-cana/", "from-toronto/tokyo/"]:
        assert (site / p / "index.html").exists(), p
    months = sorted({f["depart"][:7] for d in json.loads((SITE / "data.json").read_text())["destinations"] for f in d["fares"]})
    first = pages.month_slug(months[0])
    for b in (2000, 3000):
        assert (site / f"from-toronto/{first}/under-{b}/index.html").exists()


def test_finder_index_lists_written_hubs(built):
    """from-toronto/index.json maps destination code to its hub path, for the finder's card links."""
    site, _, files = built
    index = json.loads((site / pages.ORIGIN_SLUG / "index.json").read_text(encoding="utf8"))
    assert index["CUN"] == "from-toronto/cancun/"
    hubs = {p["path"] for p in json.loads((site / "manifest.json").read_text())["pages"]}
    for code, path in index.items():
        assert path in hubs and (site / path / "index.html") in files, code
        assert re.fullmatch(r"from-toronto/[a-z0-9-]+/", path), path
    priced = {d["code"] for d in json.loads((SITE / "data.json").read_text())["destinations"] if d["fares"]}
    assert set(index) <= priced


def test_every_price_is_dated(built):
    """Guardrail 1: a dollar amount must sit in a data-asof span (an estimate) or a data-budget span (the reader's budget)."""
    _, _, files = built
    for f, text in files.items():
        # The page title, description and heading may name a budget (not a price) in plain text.
        allowed = {f"${b:,}" for b in (*pages.BUDGETS, *pages.MARCH_BREAK_BUDGETS)}
        head, rest = text.split("</head>", 1)
        h1 = re.search(r"<h1>(.*?)</h1>", rest, flags=re.DOTALL).group(1)
        crumbs = re.search(r'<nav class="crumbs".*?</nav>', rest, flags=re.DOTALL).group(0)
        for part in (head, h1, crumbs):
            assert set(re.findall(r"\$[\d,]+", part)) <= allowed, f"{f}: amount in title or heading {part[:80]}"
        body = rest.replace(h1, "").replace(crumbs, "")
        body = re.sub(r"<(script|style)\b.*?</\1>", "", body, flags=re.DOTALL)
        body = re.sub(r'<span class="amt" data-asof="\d{4}-\d{2}-\d{2}">\$[\d,]+</span>', "", body)
        body = re.sub(r'<span class="bud" data-budget>\$[\d,]+</span>', "", body)
        body = re.sub(r'href="[^"]*"', "", body)
        leftover = re.findall(r"\$\s?\d[\d,]*", body)
        assert not leftover, f"{f}: undated amounts {leftover[:5]}"


def test_amounts_carry_the_snapshot_date(built):
    _, _, files = built
    today = json.loads((SITE / "data.json").read_text())["today"]
    for f, text in files.items():
        assert set(re.findall(r'data-asof="([\d-]+)"', text)) <= {today}, f


def test_no_seller_wording(built):
    """Guardrail 4: referral wording only (TICO, PHASE1_SPEC section 8)."""
    _, _, files = built
    for f, text in files.items():
        assert not pages.banned_in(pages.visible_text(text)), f


def test_disclosure_before_any_partner_link(built):
    """Guardrail 3: affiliate disclosure near the top, and partner links are marked sponsored."""
    _, _, files = built
    for f, text in files.items():
        assert "How we make money" in text, f
        first_link = text.find('rel="sponsored')
        if first_link != -1:
            assert text.find("How we make money") < first_link, f
        for a in re.findall(r'<a [^>]*href="https?://(?:tp\.media|www\.booking\.com|www\.klook\.com|www\.aviasales)[^>]*>', text):
            assert "sponsored" in a, f"{f}: {a[:80]}"


def test_noindex_until_launch(built):
    _, _, files = built
    for f, text in files.items():
        assert '<meta name="robots" content="noindex, follow">' in text, f
    assert not (built[0] / pages.ORIGIN_SLUG / "sitemap.xml").exists()


def test_indexable_flag_respects_gates(tmp_path):
    shutil.copy(SITE / "data.json", tmp_path / "data.json")
    shutil.copy(SITE / "photos.js", tmp_path / "photos.js")
    stats = pages.generate(site_dir=tmp_path, indexable=True, manifest_path=tmp_path / "m.json")
    manifest = json.loads((tmp_path / "m.json").read_text())
    for p in manifest["pages"]:
        html = (tmp_path / p["path"] / "index.html").read_text(encoding="utf8")
        fresh = '"index, follow"' in html
        if not p["gate"]:
            assert not fresh, p["path"]
    sitemap = (tmp_path / pages.ORIGIN_SLUG / "sitemap.xml").read_text()
    assert sitemap.count("<loc>") == stats["indexable"] == sum(p["gate"] for p in manifest["pages"])


def test_structured_data_never_claims_offers(built):
    _, _, files = built
    for f, text in files.items():
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.DOTALL)
        assert blocks, f
        for b in blocks:
            data = json.loads(b)
            dumped = json.dumps(data)
            for t in ("Offer", "AggregateOffer", "Product", "Flight", "priceCurrency"):
                assert f'"{t}"' not in dumped, f"{f}: {t}"


def test_no_partner_text_copied(built):
    """Guardrail 5: advisories are linked by level label, never quoted at length; no Viator content anywhere."""
    _, _, files = built
    for f, text in files.items():
        assert "viator" not in text.lower(), f


# ---- Gates on synthetic data ---------------------------------------------------------------------------------

TODAY = date(2026, 11, 25)


def _dest(n_fares, nights=7, band_n=30, months=("2027-01",)):
    fares = []
    for m in months:
        start = date.fromisoformat(m + "-05")
        fares += [Fare("CUN", start + timedelta(days=i), start + timedelta(days=i + nights), Money.of(400 + i), TODAY) for i in range(n_fares)]
    bands = {(m, t): LodgingBand(PriceRange(Money.of(80), Money.of(120), Money.of(200)), band_n, TODAY) for m in months for t in ("budget", "mid")}
    return DestinationData("CUN", "Cancun", "MX", fares, bands, None)


def _builder(dests):
    snap = pages.Snapshot(TODAY, "2026-11-25T00:00:00+00:00", {}, dests, {}, {}, {})
    return pages.Builder(snap, pages.Pricer(snap), {})


@pytest.mark.parametrize(
    "n_fares,nights,band_n,ok",
    [(6, 7, 30, True), (4, 7, 30, False), (6, 3, 30, False), (6, 7, 5, False)],
)
def test_month_gate(n_fares, nights, band_n, ok):
    d = _dest(n_fares, nights, band_n)
    assert _builder([d]).month_gate(d, "2027-01")[0] is ok


def test_hub_needs_two_months():
    one, two = _dest(6), _dest(6, months=("2027-01", "2027-02"))
    for d, ok in ((one, False), (two, True)):
        b = _builder([d])
        b.destination_hub(d)
        assert b.pages[0].gate is ok


def test_march_break_without_fares_says_so():
    b = _builder([_dest(6)])
    b.march_break()
    page = b.pages[0]
    assert page.gate is False
    assert "don't have fares for March break" in page.body


def test_relative_links():
    assert pages.rel("from-toronto/cancun/", "") == "../../"
    assert pages.rel("from-toronto/cancun/january/", "from-toronto/") == "../../../from-toronto/"


def test_finder_link_passes_page_inputs():
    assert 'href="../../"' in pages.finder_link("from-toronto/cancun/")
    link = pages.finder_link("from-toronto/march-2027/under-3000/", budget=3000, adults=2, month="2027-03", nights=None)
    assert 'href="../../../?budget=3000&amp;adults=2&amp;month=2027-03"' in link


def test_hotel_link_matches_engine_js_template():
    snap = pages.Snapshot(TODAY, "", {}, [], {"CUN": {"url": "https://x.test/?in=%7Bcheckin%7D&out={checkout}&r=%7Brooms%7D", "partner": "P"}}, {}, {})
    f = Fare("CUN", date(2027, 1, 5), date(2027, 1, 12), Money.of(400), TODAY)
    assert pages.hotel_link(snap, "CUN", f, 3, 0)["url"] == "https://x.test/?in=2027-01-05&out=2027-01-12&r=2"


def test_brand_is_one_constant(built):
    _, _, files = built
    text = next(iter(files.values()))
    assert pages.BRAND_NAME in text
    assert Path(pages.__file__).read_text(encoding="utf8").count('"Budget Trip Finder"') == 1
