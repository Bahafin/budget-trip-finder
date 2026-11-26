import csv
from datetime import date

from tripfinder.gate_a import OUR_FIELDS, REAL_FIELDS, is_holiday, report


def test_holiday_windows():
    assert is_holiday(date(2026, 12, 24)) and is_holiday(date(2027, 1, 2)) and is_holiday(date(2027, 3, 15))
    assert not is_holiday(date(2026, 12, 10)) and not is_holiday(date(2027, 1, 10)) and not is_holiday(date(2027, 3, 30))


def _row(i, flight, hotel, real_flight, real_hotel, holiday=""):
    r = {k: "" for k in OUR_FIELDS + REAL_FIELDS}
    r.update({
        "id": f"A{i:02d}", "name": "X", "depart": "2027-01-10", "nights": "5", "adults": "2", "children": "0",
        "rooms": "1", "holiday": holiday,
        "flight_pp_low": flight * 0.95, "flight_pp_expected": flight, "flight_pp_high": flight * 1.35,
        "hotel_night_low": hotel * 0.7, "hotel_night_expected": hotel, "hotel_night_high": hotel * 1.5,
        "daily_total": 1000,
        "total_expected": flight * 2 + hotel * 5 + 1000,
        "total_low": flight * 0.95 * 2 + hotel * 0.7 * 5 + 750,
        "total_high": flight * 1.35 * 2 + hotel * 1.5 * 5 + 1300,
        "real_flight_pp": real_flight, "real_hotel_night": real_hotel,
    })
    return r


def test_report_computes_errors_and_verdict(tmp_path):
    sheet = tmp_path / "s.csv"
    rows = [_row(1, 400, 150, 400, 150), _row(2, 400, 150, 500, 150, "yes"), _row(3, 400, 150, 400, 200), _row(4, 400, 150, None, None)]
    rows[3]["real_flight_pp"] = rows[3]["real_hotel_night"] = ""
    with sheet.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=OUR_FIELDS + REAL_FIELDS)
        w.writeheader()
        w.writerows(rows)
    text = report(sheet)
    assert "Checked 3 of 4 trips" in text
    assert "PASS" in text  # totals are within a few percent
    assert "Holiday trips: 1" in text
    assert "| A02 | X | 2027-01-10 | yes | -20% |" in text


def test_report_with_nothing_checked(tmp_path):
    sheet = tmp_path / "s.csv"
    with sheet.open("w", newline="", encoding="utf8") as f:
        csv.DictWriter(f, fieldnames=OUR_FIELDS + REAL_FIELDS).writeheader()
    assert "No real prices recorded yet" in report(sheet)
