from datetime import UTC, datetime, timedelta

from tripfinder.db import connect
from tripfinder.jobs import due_steps

ALL = {"reference", "select", "flights", "hotels", "seasonality"}
NOW = datetime(2026, 11, 26, 12, tzinfo=UTC)


def _db(tmp_path):
    return connect(tmp_path / "t.db")


def _log(conn, job, at):
    conn.execute("INSERT INTO api_calls (job, run, provider, endpoint, status, ms, bytes, at) VALUES (?,?,?,?,?,?,?,?)",
                 (job, job, "x", "/", 200, 1, 1, at.isoformat()))


def _fill(conn):
    conn.execute("INSERT INTO advisories VALUES ('MX',1,'t','u','p','f')")
    conn.execute("INSERT INTO price_levels VALUES ('MX',0.6,'2025','f')")
    conn.execute("INSERT INTO airlines VALUES ('AC','Air Canada')")
    conn.execute("INSERT INTO destinations VALUES ('CUN','Cancun','MX',21.1,-86.8,10,1)")
    conn.execute("INSERT INTO fares VALUES ('CUN','2027-01-10','2027-01-17',300,'CAD','AC',0,'','2026-11-20','f')")
    conn.execute("INSERT INTO lodging_bands VALUES ('CUN','2027-01','mid',100,150,200,'CAD',30,'liteapi','2026-11-20')")
    conn.execute("INSERT INTO price_index VALUES ('CUN','2027-01-10',200,'f')")


def test_empty_database_runs_everything(tmp_path):
    assert set(due_steps(_db(tmp_path))) == ALL


def test_fresh_data_skips_everything(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    for job in ALL:
        _log(conn, job, NOW - timedelta(hours=2))
    assert due_steps(conn, NOW) == {}


def test_flights_daily_hotels_and_seasonality_weekly(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    for job in ("reference", "select", "hotels", "seasonality"):
        _log(conn, job, NOW - timedelta(days=3))
    _log(conn, "flights", NOW - timedelta(hours=23))
    assert set(due_steps(conn, NOW)) == {"flights"}
    _log(conn, "hotels", NOW - timedelta(days=7))  # an older run doesn't matter; the latest counts
    assert set(due_steps(conn, NOW)) == {"flights"}
    for job in ("hotels", "seasonality"):
        conn.execute("DELETE FROM api_calls WHERE job = ?", (job,))
        _log(conn, job, NOW - timedelta(days=7))
    assert set(due_steps(conn, NOW)) == {"flights", "hotels", "seasonality"}


def test_new_destination_list_refreshes_everything_that_depends_on_it(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    for job in ("reference", "flights", "hotels", "seasonality"):
        _log(conn, job, NOW - timedelta(hours=2))
    _log(conn, "select", NOW - timedelta(days=40))
    assert set(due_steps(conn, NOW)) == {"select", "flights", "hotels", "seasonality"}
