"""SQLite storage for the proof of concept. The schema maps 1:1 to the Postgres tables planned for M1."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS destinations (
    code TEXT PRIMARY KEY,          -- IATA city code
    name TEXT NOT NULL,
    country_code TEXT NOT NULL,     -- ISO 3166-1 alpha-2
    lat REAL, lon REAL,
    fares_seen INTEGER NOT NULL DEFAULT 0,
    selected INTEGER NOT NULL DEFAULT 0  -- selected for at least one departure city (hotels, seasonality)
);
CREATE TABLE IF NOT EXISTS selection (  -- which destinations each departure city shows
    origin TEXT NOT NULL, code TEXT NOT NULL,
    PRIMARY KEY (origin, code)
);
CREATE TABLE IF NOT EXISTS fares (
    origin TEXT NOT NULL,           -- IATA city code of the departure city
    destination TEXT NOT NULL,
    depart TEXT NOT NULL, ret TEXT NOT NULL,
    price REAL NOT NULL, currency TEXT NOT NULL,
    airline TEXT, transfers INTEGER, link TEXT,
    found_on TEXT NOT NULL,         -- date a user search last saw this price
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (origin, destination, depart, ret, airline)
);
CREATE TABLE IF NOT EXISTS fare_history (  -- one row per day: what the cache showed, kept for "below usual"
    day TEXT NOT NULL, origin TEXT NOT NULL, destination TEXT NOT NULL, month TEXT NOT NULL, nights INTEGER NOT NULL,
    min_price REAL NOT NULL, fares INTEGER NOT NULL, currency TEXT NOT NULL,
    PRIMARY KEY (day, origin, destination, month, nights)
);
CREATE TABLE IF NOT EXISTS band_history (
    day TEXT NOT NULL, destination TEXT NOT NULL, month TEXT NOT NULL, tier TEXT NOT NULL,
    nightly_low REAL, nightly_mid REAL, nightly_high REAL, sample_size INTEGER,
    PRIMARY KEY (day, destination, month, tier)
);
CREATE TABLE IF NOT EXISTS hotel_prices (
    destination TEXT NOT NULL, checkin TEXT NOT NULL, nights INTEGER NOT NULL,
    hotel_id TEXT NOT NULL, hotel_name TEXT, stars REAL,
    total REAL NOT NULL, currency TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (destination, checkin, hotel_id)
);
CREATE TABLE IF NOT EXISTS lodging_bands (
    destination TEXT NOT NULL, month TEXT NOT NULL, tier TEXT NOT NULL,
    nightly_low REAL NOT NULL, nightly_mid REAL NOT NULL, nightly_high REAL NOT NULL,
    currency TEXT NOT NULL, sample_size INTEGER NOT NULL, source TEXT NOT NULL, as_of TEXT NOT NULL,
    PRIMARY KEY (destination, month, tier)
);
CREATE TABLE IF NOT EXISTS price_levels (
    country_code TEXT PRIMARY KEY, ratio_to_usd REAL NOT NULL, year TEXT NOT NULL, fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS advisories (
    country_code TEXT PRIMARY KEY, level INTEGER, text TEXT, url TEXT, published TEXT, fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS price_index (
    destination TEXT NOT NULL, day TEXT NOT NULL, usd REAL NOT NULL, fetched_at TEXT NOT NULL,
    PRIMARY KEY (destination, day)
);
CREATE TABLE IF NOT EXISTS airlines (
    code TEXT PRIMARY KEY, name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job TEXT, provider TEXT NOT NULL, endpoint TEXT NOT NULL,
    status INTEGER, ms INTEGER, bytes INTEGER, at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY, value TEXT NOT NULL
);
"""


def _migrate_fares_origin(conn: sqlite3.Connection) -> None:
    """Databases from before departure cities: fares had no origin column (all Toronto)."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(fares)")}
    if cols and "origin" not in cols:
        conn.executescript("""
            ALTER TABLE fares RENAME TO fares_old;
            CREATE TABLE fares (
                origin TEXT NOT NULL, destination TEXT NOT NULL,
                depart TEXT NOT NULL, ret TEXT NOT NULL,
                price REAL NOT NULL, currency TEXT NOT NULL,
                airline TEXT, transfers INTEGER, link TEXT,
                found_on TEXT NOT NULL, fetched_at TEXT NOT NULL,
                PRIMARY KEY (origin, destination, depart, ret, airline)
            );
            INSERT INTO fares SELECT 'YTO', destination, depart, ret, price, currency, airline, transfers, link, found_on, fetched_at FROM fares_old;
            DROP TABLE fares_old;
            INSERT OR IGNORE INTO selection SELECT 'YTO', code FROM destinations WHERE selected = 1;
        """)
        conn.commit()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS selection (origin TEXT NOT NULL, code TEXT NOT NULL, PRIMARY KEY (origin, code))")
    _migrate_fares_origin(conn)
    conn.executescript(SCHEMA)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(api_calls)")}
    if "run" not in cols:
        conn.execute("ALTER TABLE api_calls ADD COLUMN run TEXT")
    return conn
