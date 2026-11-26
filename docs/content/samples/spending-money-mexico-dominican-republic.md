# How much spending money for Cancún and Punta Cana? (draft)

**Status:** draft for the owner, written 2026-11-26. This is calendar week 3 (14–20 Dec), "hand-written guide" #8 in the README.
**URL when published:** `/guides/spending-money-mexico-dominican-republic/`
**Targets:** how much spending money for Cancun, how much spending money for Punta Cana, spending money per day Mexico, all-inclusive extra money.

**Where the numbers come from:** the engine (`daily_component`) and `site/data.json` from 26 November 2026. Rerun them on the day you publish; the commands are at the end. **Before publishing:**
- Check the three facts marked ⚠️ against their official sources.
- Add one paragraph from your own trip or a reader's reply. This is the guide where first-hand experience counts most (E-E-A-T).

---

**How much spending money do you need for Cancún or Punta Cana?** For a week, two adults who aren't on an all-inclusive should plan on about **$1,450 in Cancún** and **$960 in Punta Cana** (Canadian dollars) for mid-range food, local transport and modest entry fees. On a tight budget that falls to about $830 and $550. On an all-inclusive, budget for tips, excursions and transfers instead. *(Our estimates, 26 November 2026.)*

## What we estimate per day

Per adult per day, in CAD, before flights and the hotel:

| | Budget | Mid-range | Upscale |
|---|---|---|---|
| Cancún (Mexico) | $52 | $91 | $156 |
| Punta Cana (Dominican Republic) | $34 | $60 | $103 |
| For comparison: a Canadian city (our baseline) | $80 | $140 | $240 |

For **two adults and 7 nights**, we count 8 days, because you eat on the day you arrive and the day you leave. The ranges run from low to high, with the expected figure in the middle:

| | Budget | Mid-range | Upscale |
|---|---|---|---|
| Cancún | $624 – **$832** – $1,082 | $1,092 – **$1,456** – $1,893 | $1,872 – **$2,496** – $3,245 |
| Punta Cana | $413 – **$550** – $716 | $722 – **$963** – $1,252 | $1,238 – **$1,651** – $2,147 |

## How we get these numbers

We start from what a day costs in Canada at each comfort level: $80, $140 or $240 per adult. Then we scale it by the country's price level compared with Canada, from the World Bank's International Comparison Program (CC BY 4.0). Mexico comes out at 0.65 × Canada and the Dominican Republic at 0.43 ×. Children count at 70% of an adult.

**Be honest about the weak spot:** a price level is for the whole country. Cancún's Hotel Zone and the Punta Cana resort strip cost more than the national average, so a day there can run above our figure, especially if you eat where the tourists eat. Downtown Cancún and local spots run closer to it. This is the least checked part of our estimates. We checked 50 trips against real flight and hotel prices ([how we estimate](/from-toronto/how-we-estimate/)), but nobody can look up "what you'll spend on lunch" on a booking site. **Tell us what you spent and we'll publish the answers** (owner: decide where replies go before publishing).

## What it covers, and what it doesn't

Covered: meals and snacks, local buses or taxis, entry to beaches, parks and sights that charge a modest fee.

Not covered, so add these yourself:
- **Excursions and tours** (cenotes, Isla Mujeres or Saona Island day trips, snorkelling). These are often the biggest extra.
- **Airport transfers**, if your hotel doesn't include them.
- **Tips.** On an all-inclusive, tips at the bar and restaurants add up over a week.
- ⚠️ **Mexico: Quintana Roo's state visitor fee (VISITAX)**, paid online before you leave. Check the current amount on the official state site before quoting it.
- ⚠️ **Dominican Republic: the tourist card.** For most air travellers it's now included in the fare. Check the current rule on the government site or travel.gc.ca.
- ⚠️ **Mexico: cash over USD 10,000 must be declared** on arrival and departure. This is already in our know-before-you-go notes, with its source.

## If you're going all-inclusive

Your meals and drinks are covered, so cut the "food" part of the daily figure. Keep money for tips, excursions, transfers and anything off the resort. Our trip totals use hotel-room prices, not all-inclusive packages: see "What's in these numbers" on the [Cancún](/from-toronto/cancun/) and [Punta Cana](/from-toronto/punta-cana/) pages.

## See the whole trip

- [Cancún from Toronto: what a trip really costs](/from-toronto/cancun/)
- [Punta Cana from Toronto: what a trip really costs](/from-toronto/punta-cana/)
- [Where $2,000 gets two people in January](/from-toronto/january/under-2000/)

---

### For the owner: refreshing the numbers

From `backend/`:

```bash
uv run python -c "from tripfinder import pages; from tripfinder.engine import daily_component, DAILY_BASE_CAD, TripRequest; from tripfinder.money import Money; s=pages.load_snapshot(pages.ROOT/'site'/'data.json'); [print(d.code, t, round(DAILY_BASE_CAD[t]*float(d.price_level)), daily_component(d, TripRequest(Money.of(99999),2,0,None,7,t), 7).total) for d in s.dests if d.code in ('CUN','PUJ','YMQ') for t in DAILY_BASE_CAD]"
```

Links in this draft are site-root paths. Make them relative (or full URLs) when the guide is published under the GitHub Pages sub-path.
