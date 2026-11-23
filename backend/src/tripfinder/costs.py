"""What gathering and keeping the data costs, from the api_calls log plus the providers' published terms."""

from __future__ import annotations

import sqlite3

from .config import Settings

# Refresh cadence the POC assumes, in runs per month.
SCHEDULE = {"flights": 30, "hotels": 4.33, "reference": 1, "select": 1}

# Published terms as read on 2026-11-23 (see docs/m0-coverage-report.md).
TERMS = {
    "aviasales": "free (Travelpayouts Data API, no per-call fee)",
    "travelpayouts-data": "free",
    "worldbank": "free, CC BY 4.0 (attribute)",
    "gac": "free (link to travel.gc.ca; don't copy text commercially)",
    "liteapi": "free within 5,000 searches per booking; excess 'may be billed', rate unpublished",
}


def report(conn: sqlite3.Connection, s: Settings) -> str:
    rows = conn.execute(
        """
        WITH runs AS (
            SELECT job, COALESCE(run, job || substr(at, 1, 13)) AS run_id, COUNT(*) AS n, MAX(at) AS last
            FROM api_calls GROUP BY job, run_id
        ),
        full_run AS (  -- per job, its latest full run (partial re-runs are logged as job 'hotels-partial')
            SELECT job, run_id FROM (
                SELECT job, run_id, ROW_NUMBER() OVER (PARTITION BY job ORDER BY last DESC) AS rk FROM runs
            ) WHERE rk = 1 AND job NOT LIKE '%-partial'
        )
        SELECT c.job, c.provider, COUNT(*) AS calls, SUM(c.status >= 400) AS failed,
               AVG(c.ms) AS avg_ms, SUM(c.ms) AS total_ms, SUM(c.bytes) AS bytes
        FROM api_calls c JOIN full_run f ON f.job = c.job AND COALESCE(c.run, c.job || substr(c.at, 1, 13)) = f.run_id
        GROUP BY c.job, c.provider ORDER BY c.job
        """
    ).fetchall()
    dest_count = conn.execute("SELECT COUNT(*) FROM destinations WHERE selected = 1").fetchone()[0]
    lines = [f"Data cost for {dest_count} destinations, {s.months_ahead} months ahead (last run of each job)\n"]
    lines.append(f"{'job':<10} {'provider':<19} {'calls':>5} {'fail':>4} {'avg s':>6} {'MB':>6} {'runs/mo':>7} {'calls/mo':>8}")
    monthly: dict[str, float] = {}
    for r in rows:
        per_month = r["calls"] * SCHEDULE.get(r["job"], 1)
        monthly[r["provider"]] = monthly.get(r["provider"], 0) + per_month
        lines.append(
            f"{r['job']:<10} {r['provider']:<19} {r['calls']:>5} {r['failed']:>4} {r['avg_ms'] / 1000:>6.1f} "
            f"{(r['bytes'] or 0) / 1e6:>6.1f} {SCHEDULE.get(r['job'], 1):>7} {per_month:>8.0f}"
        )
    lines.append("\nMonthly calls by provider and what they cost:")
    for prov, n in sorted(monthly.items()):
        lines.append(f"  {prov:<19} {n:>7.0f}  {TERMS.get(prov, '?')}")
    hotels = monthly.get("liteapi", 0)
    if hotels:
        lines.append(
            f"\nLiteAPI: {hotels:.0f} searches/month is {hotels / 5000:.0%} of a 5,000-search allowance. "
            f"Worst case at Nuitee's published flight surcharge (EUR 0.005/search): EUR {hotels * 0.005:.2f}/month."
        )
    size = s.db_path.stat().st_size / 1e6 if s.db_path.exists() else 0
    lines.append(f"Database size: {size:.1f} MB. User searches make no external calls (they read the database).")
    return "\n".join(lines)
