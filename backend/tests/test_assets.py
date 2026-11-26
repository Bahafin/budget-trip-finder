from tripfinder.assets import check, pick_photo, slugify, theme_request


def _page(title, lic, w=4000, h=2500, desc="A view", artist="<a href='x'>Someone</a>"):
    return {"title": f"File:{title}", "imageinfo": [{
        "width": w, "height": h, "thumburl": f"https://thumb.example/{title}?x=1", "descriptionurl": f"https://commons/{title}",
        "extmetadata": {"LicenseShortName": {"value": lic}, "ImageDescription": {"value": desc}, "Artist": {"value": artist}},
    }]}


def test_slugify():
    assert slugify("Mexico City") == "mexico-city"
    assert slugify("Denpasar (Bali)") == "denpasar-bali"
    assert slugify("Montréal") == "montreal"


def test_pick_photo_needs_a_reusable_licence_and_a_wide_large_image():
    pages = [
        _page("nc.jpg", "CC BY-NC 2.0"),           # non-commercial: no
        _page("tall.jpg", "CC BY 2.0", w=2000, h=3000),  # portrait: no
        _page("small.jpg", "CC BY-SA 4.0", w=1200, h=800),  # too small: no
        _page("good.jpg", "CC BY-SA 4.0"),
    ]
    p = pick_photo(pages)
    assert p["src"] == "https://thumb.example/good.jpg" and p["license"] == "CC BY-SA 4.0"
    assert p["author"] == "Someone" and p["review"] is True
    assert pick_photo([_page("pd.jpg", "Public domain")])["license"] == "Public domain"
    assert pick_photo([_page("nd.jpg", "CC BY-ND 4.0")]) is None


def test_check_lists_missing_photos_and_themes(tmp_path):
    (tmp_path / "themes.csv").write_text("code,themes,best_for,todo\nAAA,beach,Sun,Swim\n", encoding="utf8")
    dests = [{"code": "AAA", "name": "A", "country": "MX"}, {"code": "BBB", "name": "B", "country": "VN"}]
    m = check(dests, tmp_path, {"AAA": {"src": "x"}, "CCC": {"src": "y", "review": True}})
    assert [x["code"] for x in m["photo"]] == ["BBB"]
    assert [x["code"] for x in m["theme"]] == ["BBB"]
    assert [x["code"] for x in m["photo_review"]] == ["CCC"]
    assert "BBB: B (VN)" in theme_request(m["theme"])


def test_pick_photo_must_name_the_place():
    woods = _page("Wandering_in_the_Woods.jpg", "CC BY 2.0", desc="A walk in the woods")
    beach = _page("Patong_beach_Phuket.jpg", "CC BY 2.0", desc="Patong beach")
    assert pick_photo([woods, beach], "Phuket")["src"].endswith("Patong_beach_Phuket.jpg")
    assert pick_photo([woods], "Phuket") is None
