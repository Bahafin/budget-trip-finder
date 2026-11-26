# Gate A report

Sheet: `sheet.csv`. Checked 10 of 50 trips.

| Component | Median error | Median absolute error | 90th pct absolute error | Real price inside our range |
|---|---|---|---|---|
| Flights (per person) | +12% | 18% | 26% | 3 of 10 |
| Hotel (per night per room) | +2% | 23% | 68% | 6 of 10 |
| Total (our daily spend in both) | +5% | 13% | 32% | 8 of 10 |

**Gate A verdict on 10 trips: PASS** (median absolute total error 13%; pass within about 20-25%). Daily spend is our estimate on both sides, so it is not tested here.

Holiday trips: 2, median absolute total error 8%.

| Trip | Destination | Depart | Holiday | Flights | Hotel | Total |
|---|---|---|---|---|---|---|
| A01 | Cancun | 2026-12-13 |  | +7% | -52% | -15% |
| A02 | Istanbul | 2027-02-08 |  | +16% | -20% | +1% |
| A03 | Vancouver | 2027-02-01 |  | +32% | -3% | +5% |
| A04 | London | 2027-02-12 |  | +9% | +6% | +4% |
| A05 | Calgary | 2026-12-10 |  | +6% | +41% | +18% |
| A06 | New York | 2027-01-02 | yes | -20% | -3% | -4% |
| A07 | Kingston | 2027-02-19 |  | +24% | +68% | +32% |
| A08 | Punta Cana | 2027-02-11 |  | +26% | +106% | +54% |
| A09 | Tokyo | 2027-01-03 | yes | +16% | +14% | +12% |
| A10 | Bangkok | 2026-12-04 |  | -19% | -27% | -16% |
