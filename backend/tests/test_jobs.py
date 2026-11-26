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


def _hotels(conn, rows):
    conn.executemany(
        "INSERT INTO hotel_prices VALUES (?,?,?,?,?,?,?,?,?)",
        [("ORL", checkin, 3, hid, name, stars, nightly * 3, "CAD", "2026-11-26T00:00:00") for checkin, hid, name, stars, nightly in rows],
    )


def test_bands_drop_spiky_quotes_and_all_inclusive(tmp_path):
    from tripfinder.jobs import rebuild_bands

    conn = connect(tmp_path / "t.db")
    rows = []
    for i in range(6):  # six normal 4-star hotels, same price every month
        for month in ("2026-12-15", "2027-01-15", "2027-02-15"):
            rows.append((month, f"h{i}", f"Hotel {i}", 4.0, 200 + 10 * i))
    rows = [r for r in rows if not (r[0] == "2027-02-15" and r[1] == "h0")]
    rows.append(("2027-02-15", "h0", "Hotel 0", 4.0, 2000))  # 10x its own usual price: a bad quote
    for month in ("2026-12-15", "2027-01-15", "2027-02-15"):
        rows.append((month, "ai", "Beach Resort - All Inclusive", 4.0, 900))
    _hotels(conn, rows)
    rebuild_bands(conn)
    feb = conn.execute("SELECT nightly_high, sample_size FROM lodging_bands WHERE month='2027-02' AND tier='mid'").fetchone()
    assert feb["sample_size"] == 5 and feb["nightly_high"] < 300
    dec = conn.execute("SELECT sample_size FROM lodging_bands WHERE month='2026-12' AND tier='mid'").fetchone()
    assert dec["sample_size"] == 6
    rebuild_bands(conn, drop_all_inclusive=False)
    assert conn.execute("SELECT sample_size FROM lodging_bands WHERE month='2026-12' AND tier='mid'").fetchone()["sample_size"] == 7


def test_changed_hand_picked_list_makes_selection_due(tmp_path):
    conn = _db(tmp_path)
    _fill(conn)
    for job in ALL:
        _log(conn, job, NOW - timedelta(hours=2))
    assert due_steps(conn, NOW) == {}
    due = due_steps(conn, NOW, extras=["MEX"])
    assert due["extras"] == "hand-picked destination list changed" and "select" not in due and "hotels" in due
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('always_include', 'MEX')")
    assert due_steps(conn, NOW, extras=["MEX"]) == {}


def test_selection_is_sticky():
    from collections import Counter

    from tripfinder.jobs import choose_destinations

    counts = Counter({"A": 100, "B": 90, "C": 80, "D": 12, "E": 4, "X": 3})
    eligible = set(counts)
    # Fresh start: top 3 by fare count.
    assert choose_destinations(counts, eligible, [], [], 3) == ["A", "B", "C"]
    # D was already chosen and still has >= 10 fares: it stays even though C now ranks higher.
    assert choose_destinations(counts, eligible, ["D", "A", "B"], [], 3) == ["D", "A", "B"]
    # E has dropped under 5 fares, so its slot is refilled from the ranking.
    assert choose_destinations(counts, eligible, ["E", "A", "B"], [], 3) == ["A", "B", "C"]
    # Keeping uses our own stored fares when given: D has 1 bulk fare today but 7 stored, so it stays.
    low = Counter({"A": 100, "B": 90, "C": 80, "D": 1})
    assert choose_destinations(low, set(low), ["D", "A", "B"], [], 3, stored={"D": 7, "A": 50, "B": 40}) == ["D", "A", "B"]
    # A place now under an advisory (not eligible) is dropped; hand-picked places are added on top.
    assert choose_destinations(counts, eligible - {"A"}, ["A", "B", "C"], ["X"], 3) == ["B", "C", "D", "X"]
