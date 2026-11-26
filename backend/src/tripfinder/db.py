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
    selected INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS fares (
    destination TEXT NOT NULL,
    depart TEXT NOT NULL, ret TEXT NOT NULL,
    price REAL NOT NULL, currency TEXT NOT NULL,
    airline TEXT, transfers INTEGER, link TEXT,
    found_on TEXT NOT NULL,         -- date a user search last saw this price
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (destination, depart, ret, airline)
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


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(api_calls)")}
    if "run" not in cols:
        conn.execute("ALTER TABLE api_calls ADD COLUMN run TEXT")
    return conn
