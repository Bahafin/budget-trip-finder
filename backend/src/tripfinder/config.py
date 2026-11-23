"""Settings from the repo-root .env file (never committed) and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # backend/src/tripfinder -> repo root


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    return values


@dataclass(frozen=True)
class Settings:
    travelpayouts_token: str
    travelpayouts_marker: str
    liteapi_key: str
    db_path: Path
    seed_dir: Path
    origin: str = "YTO"  # all Toronto airports
    currency: str = "CAD"
    market: str = "ca"
    months_ahead: int = 3
    destinations: int = 25
    hotel_sample_nights: int = 3
    hotel_radius_m: int = 10000


def load_settings() -> Settings:
    env = {**_load_env_file(ROOT / ".env"), **os.environ}
    return Settings(
        travelpayouts_token=env.get("TRAVELPAYOUTS_TOKEN", ""),
        travelpayouts_marker=env.get("TRAVELPAYOUTS_MARKER", ""),
        liteapi_key=env.get("LITEAPI_KEY", ""),
        db_path=Path(env.get("TRIPFINDER_DB", ROOT / "var" / "tripfinder.db")),
        seed_dir=ROOT / "data" / "seed",
    )
