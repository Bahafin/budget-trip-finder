from datetime import UTC, datetime, timedelta

from tripfinder.db import connect
from tripfinder.jobs import due_steps


def _db(tmp_path):
    return connect(tmp_path / "t.db")


def _log(conn, job, at):
    conn.execute("INSERT INTO api_calls (job, run, provider, endpoint, status, ms, bytes, at) VALUES (?,?,?,?,?,?,?,?)",
                 (job, job, "x", "/", 200, 1, 1, at.isoformat()))


def _fill(conn):
    conn.execute("INSERT INTO advisories VALUES ('MX',1,'t','u','p','f')")
    conn.execute("INSERT INTO price_levels VALUES ('MX',0.6,'2025','f')")
    conn.execute("INSERT INTO destinations VALUES ('CUN','Cancun','MX',21.1,-86.8,10,1)")
    conn.execute("INSERT INTO fares VALUES ('CUN','2027-01-10','2027-01-17',300,'CAD','AC',0,'','2026-11-20','f')")
    conn.execute("INSERT INTO lodging_bands VALUES ('CUN','2027-01','mid',100,150,200,'CAD',30,'liteapi','2026-11-20')")


def test_empty_database_runs_everything(tmp_path):
    assert set(due_steps(_db(tmp_path))) == {"reference", "select", "flights", "hotels"}


def test_fresh_data_skips_everything(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    now = datetime(2026, 11, 26, 12, tzinfo=UTC)
    for job in ("reference", "select", "flights", "hotels"):
        _log(conn, job, now - timedelta(hours=2))
    assert due_steps(conn, now) == {}


def test_flights_daily_hotels_weekly(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    now = datetime(2026, 11, 26, 12, tzinfo=UTC)
    _log(conn, "reference", now - timedelta(days=3))
    _log(conn, "select", now - timedelta(days=3))
    _log(conn, "flights", now - timedelta(hours=23))
    _log(conn, "hotels", now - timedelta(days=3))
    assert set(due_steps(conn, now)) == {"flights"}
    _log(conn, "hotels", now - timedelta(days=7))  # older run doesn't matter; the latest counts
    assert set(due_steps(conn, now)) == {"flights"}


def test_new_destination_list_refreshes_flights_and_hotels(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    now = datetime(2026, 11, 26, 12, tzinfo=UTC)
    for job in ("reference", "flights", "hotels"):
        _log(conn, job, now - timedelta(hours=2))
    _log(conn, "select", now - timedelta(days=40))
    assert set(due_steps(conn, now)) == {"select", "flights", "hotels"}
