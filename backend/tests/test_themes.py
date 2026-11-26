import pytest

from tripfinder.config import ROOT
from tripfinder.export import THEMES, load_themes


def test_seed_themes_are_valid_and_complete():
    t = load_themes(ROOT / "data" / "seed")
    assert len(t) >= 26
    for code, v in t.items():
        assert v["themes"] and set(v["themes"]) <= set(THEMES), code
        assert v["bestFor"] and v["todo"], code
        assert not any(ch.isdigit() and "$" in v["todo"] for ch in v["todo"]), code  # no prices in hand-written text


def test_unknown_theme_is_rejected(tmp_path):
    (tmp_path / "themes.csv").write_text("code,themes,best_for,todo\nXXX,beach;skiing,a,b\n", encoding="utf8")
    with pytest.raises(ValueError, match="skiing"):
        load_themes(tmp_path)
