"""data/seed/daily_level.csv: per-place day-to-day spending levels (PLAN 2.3)."""
import csv
from decimal import Decimal

from tripfinder.config import ROOT
from tripfinder.search import DAILY_LEVEL_CSV, load_daily_levels


def test_daily_levels_are_sane_and_for_known_places():
    levels = load_daily_levels()
    assert levels, "no per-place levels loaded"
    with (ROOT / "data" / "seed" / "destinations.csv").open(encoding="utf8") as f:
        known = {r["code"] for r in csv.DictReader(f)}
    for code, lvl in levels.items():
        assert code in known, code
        assert Decimal("0.2") <= lvl <= Decimal(2), (code, lvl)
    with DAILY_LEVEL_CSV.open(encoding="utf8") as f:
        for r in csv.DictReader(f):
            assert r["source"] and r["checked"], r["code"]  # every override says where it came from
