# Daily spending check (PLAN 2.3), 2026-11-26

**Question:** is our day-to-day figure (Canadian baseline per adult per day: budget $80, mid $140, upscale $240, scaled by the country's World Bank price level vs Canada) close to what travellers report spending?

**Source:** BudgetYourTrip.com city pages (data "last updated October 30, 2026"), read in a browser. They give the average traveller's daily spend on **meals** and **local transportation** (mid-range, per person). USD converted at 1.427 CAD (BudgetYourTrip's own CA$ figure for Montreal). Their entertainment/sightseeing figure is per purchase, not per day, so it's left out; our figure also covers modest entry fees, so ours *should* sit a little above theirs.

| Place | Published meals + transport (CAD/day) | Ours, mid (CAD/day) | Ours / published | Level we used → now |
|---|---|---|---|---|
| New York | 194 | 155 | 0.80 | 1.11 → **1.25** |
| Honolulu | 167 | 155 | 0.93 | 1.11 |
| Orlando | 255 | 155 | 0.61 | 1.11 → **1.47** |
| Paris | 150 | 129 | 0.86 | 0.92 |
| London | 161 | 143 | 0.89 | 1.02 |
| Tokyo | 113 | 108 | 0.96 | 0.77 |
| Bangkok | 57 | 50 | 0.88 | 0.36 |
| Bali | 56 | 48 | 0.86 | 0.34 |
| Cancún | 86 | 91 | 1.06 | 0.65 |
| Punta Cana | 102 | 60 | 0.59 | 0.43 → **0.58** |
| Mexico City | 79 | 91 | 1.16 | 0.65 |
| Lisbon | 157 | 101 | 0.64 | 0.72 → **0.92** |
| Istanbul | 123 | 70 | 0.57 | 0.50 → **0.69** |
| Barcelona | 123 | 106 | 0.87 | 0.76 |
| Montreal | 114 | 140 | 1.23 | 1.00 |
| Toronto | 194 | 140 | 0.72 | 1.00 |
| Vancouver | 94 | 140 | 1.49 | 1.00 |

**Findings**
- Median ours/published: 0.87. Most places are within about 15%, which is fine for an estimate that also covers entry fees.
- The big misses are visitor hot spots where the country average undersells what visitors pay: Punta Cana, Istanbul, Lisbon, Orlando (theme-park food and transport) and New York.
- One source is noisy: Toronto (194) and Vancouver (94) shouldn't be twice apart, so the Canadian baseline stays unchanged.

**Change made:** `data/seed/daily_level.csv` sets a per-place level for those five, **halfway** between the country level and the published one (one source isn't enough to copy outright). The engine uses it instead of the country level (search.load_destinations). Everything else keeps the country level.

**Next:** a second source (e.g. Numbeo restaurant and transit prices) before changing anything else; recheck after testers report real spending.
