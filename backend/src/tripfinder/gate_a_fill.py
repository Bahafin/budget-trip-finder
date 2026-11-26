"""Record checked real prices into a Gate A sheet: python -m tripfinder.gate_a_fill <sheet> <id> <flight_pp> <hotel_stay_total> <source> [notes]

hotel_stay_total is the whole-stay hotel price as shown (all requested rooms, all nights, taxes included);
it is converted to per room per night here, matching the sheet's columns.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path


def fill(sheet: Path, trip_id: str, flight_pp: float, hotel_stay_total: float, source: str, notes: str = "") -> dict:
    rows = list(csv.DictReader(sheet.open(encoding="utf8")))
    fields = list(rows[0].keys())
    for r in rows:
        if r["id"] == trip_id:
            r["real_flight_pp"] = f"{flight_pp:.2f}"
            r["real_hotel_night"] = f"{hotel_stay_total / (int(r['nights']) * int(r['rooms'])):.2f}"
            r["real_checked_on"] = date.today().isoformat()
            r["real_source"] = source
            r["notes"] = notes
            break
    else:
        raise SystemExit(f"no trip {trip_id}")
    with sheet.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return r


if __name__ == "__main__":
    a = sys.argv[1:]
    r = fill(Path(a[0]), a[1], float(a[2]), float(a[3]), a[4], a[5] if len(a) > 5 else "")
    print(r["id"], r["name"], "flight", r["real_flight_pp"], "hotel/night/room", r["real_hotel_night"])
