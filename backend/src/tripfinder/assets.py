"""What each destination needs besides prices: a photo, a theme row and a page address.

`check` lists the selected destinations that are missing a photo (site/photos.js) or a theme row
(data/seed/themes.csv). `fill_photos` finds a real, reusable photo on Wikimedia Commons for each missing one
and writes it into photos.js with its credit, marked `"review": true` until a person has looked at it.
Photos of real places are never AI-generated: a made-up picture of a real city would undercut the site's
promise of honest information.

Theme rows are short, hand-checked text (no prices). New ones are written by a person or an AI session and
checked by the tests in test_themes.py; `check` prints a ready-made request for them.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .config import ROOT
from .export import THEMES, load_themes
from .meter import Meter

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
UA = "tripfinder-assets/0.1 (destination photo lookup)"
OK_LICENSES = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain)$", re.I)  # reusable with credit; no NC or ND
PHOTOS = ROOT / "site" / "photos.js"


def slugify(name: str) -> str:
    """'Mexico City' -> 'mexico-city'; 'Denpasar (Bali)' -> 'denpasar-bali'."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load_photos(path: Path = PHOTOS) -> dict[str, dict[str, Any]]:
    text = path.read_text(encoding="utf8")
    return json.loads(text[text.index("{") : text.rindex("}") + 1])


def write_photos(photos: dict[str, dict[str, Any]], path: Path = PHOTOS) -> None:
    text = path.read_text(encoding="utf8")
    head = text[: text.index("{")]
    path.write_text(head + json.dumps(photos, indent=1, ensure_ascii=False) + ";\n", encoding="utf8")


def check(dests: list[dict[str, Any]], seed_dir: Path, photos: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    themes = load_themes(seed_dir)
    return {
        "photo": [{"code": d["code"], "name": d["name"]} for d in dests if d["code"] not in photos],
        "photo_review": [{"code": c, "name": p.get("alt", c)} for c, p in photos.items() if p.get("review")],
        "theme": [{"code": d["code"], "name": d["name"], "country": d.get("country", "")} for d in dests if d["code"] not in themes],
    }


def theme_request(missing: list[dict[str, str]]) -> str:
    """A ready-made request for whoever writes the theme rows (a person or an AI session)."""
    rows = "\n".join(f"- {m['code']}: {m['name']} ({m['country']})" for m in missing)
    return (
        "Add one row per place to data/seed/themes.csv (code,themes,best_for,todo):\n"
        f"- themes: 1-3 of {', '.join(THEMES)}, separated by ';'\n"
        "- best_for: 3-6 words a traveller would recognise\n"
        "- todo: one line of 3-4 things to do, no prices or numbers of any kind\n"
        f"Places:\n{rows}\n"
        "Then run the tests (test_themes.py checks the tags)."
    )


def _strip(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html or "").strip()


def pick_photo(pages: list[dict[str, Any]]) -> dict[str, str] | None:
    """The first wide, large, reusable image among Commons search results."""
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = _strip(meta.get("LicenseShortName", {}).get("value", ""))
        w, h = info.get("width", 0), info.get("height", 1)
        if not (OK_LICENSES.match(lic) and w >= 2000 and w / h >= 1.3 and info.get("thumburl")):
            continue
        title = p["title"].removeprefix("File:")
        return {
            "src": info["thumburl"].split("?")[0],
            "alt": _strip(meta.get("ImageDescription", {}).get("value", ""))[:140] or title.rsplit(".", 1)[0],
            "tagline": "",
            "author": _strip(meta.get("Artist", {}).get("value", ""))[:80] or "Wikimedia Commons contributor",
            "license": lic,
            "page": info.get("descriptionurl", ""),
            "review": True,
        }
    return None


def find_photo(meter: Meter, name: str) -> dict[str, str] | None:
    for q in (f"{name} skyline", f"{name} landmark", f"{name} city"):
        data = meter.request(
            "wikimedia",
            COMMONS_API,
            params={
                "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} filetype:bitmap",
                "gsrnamespace": "6", "gsrlimit": "15", "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                "iiurlwidth": "960",
            },
            headers={"User-Agent": UA},
        )
        pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
        found = pick_photo(pages)
        if found:
            return found
    return None


def fill_photos(meter: Meter, missing: list[dict[str, str]], path: Path = PHOTOS) -> list[str]:
    photos = load_photos(path)
    added = []
    for m in missing:
        found = find_photo(meter, m["name"])
        if found:
            photos[m["code"]] = found
            added.append(m["code"])
    if added:
        write_photos(photos, path)
    return added
