# Affiliate programs: what we can join now

Checked 2026-11-25, from official partner pages where they could be read. Third-party summaries were used only where noted. Context: Booking.com, Expedia and similar programs inside Travelpayouts currently need more traffic than we have.

## Open now (no traffic minimum found)

| Program | Route | What pays | Cookie | Notes |
|---|---|---|---|---|
| **Aviasales** | Travelpayouts (joined) | Flights, 1.1-1.3% | 30 days | Our flight data and links |
| **Expedia Group Travel Creator Program** (Expedia, Hotels.com, Vrbo) | **Direct**: creator.expediagroup.com (**joined 2026-11-26**) | Hotels, packages, cars. Official page: "up to 4%" (Travel Shops). Travelpayouts listed hotels 3.6%, packages 1.8% | Not stated (7 days via Travelpayouts) | "Anyone can apply! We review all applications within minutes." Link Builder in the Creator Toolbox. Pays via Partnerize. **Best hotel option available now** |
| **Viator** | **Direct**: partners.viator.com | Tours and activities, 8% | 30 days | "No traffic or follower minimums". Affiliate API Basic access is instant (no approval). This is the activities source the spec already planned |
| **Klook** | Travelpayouts (**joined 2026-11-25**) | 5% on all categories including **hotels**; 2% "special activities" | 30 days | Hotels, attractions, tours, transfers, trains. Strongest in Asia: Bangkok, Tokyo, Hong Kong and Bali are in our 25. Americas hotel coverage not checked (Klook blocks automated browsing) |
| **KKday** | Travelpayouts (**joined 2026-11-25**) | 5% tours, transport, eSIM; **3% accommodation**, flights, tickets; 1% special | 30 days | Asia focus. The program page lists accommodation, cruises and flights; packages not listed |
| **Hostelworld** | Direct via Partnerize | Hostels (rate not published) | 30 days (first click) | Free to join, application reviewed. Fits the "budget" comfort tier |
| **Kayak** | Direct form: affiliates.kayak.com | Clicks, bookings and ad revenue for flights, hotels, cars, packages (rates not published) | Not stated | Deep links to pre-filled results and specific hotel pages. Live pricing API: free sandbox; production needs an approved "full affiliate integration". A metasearch partner, so it fits our "compare and click out" model |

## Gated for now

| Program | Route | Barrier | Terms |
|---|---|---|---|
| **Booking.com** | Direct program closed to new partners; new sign-ups go through **CJ** by region | CJ: "an active website, blog or social media profile" (social-only not accepted). No published traffic minimum, but a prototype with no traffic may be refused | 4% on completed stays, 6% cars, 4% attractions, £2/€2 per flight. **Session cookie only** (same browser session) |
| **Skyscanner** | Impact | **More than 5,000 unique visitors a month**, HTTPS, travel content | Share of Skyscanner's commission; 30-day referral |
| **Tripadvisor** | Reportedly CJ (official page blocks automated reading) | Unconfirmed | Third-party sources: share of Tripadvisor's hotel click revenue, 14-day cookie. Unverified |
| **Agoda, Trip.com** | Direct portals (pages render only partly) | Not stated officially. Third-party: Agoda "website owners only" | Trip.com "up to 7%". Agoda 4-7% tiers (third-party) |
| **GetYourGuide** | Direct portal or Travelpayouts | Official page didn't render | 8% (Travelpayouts listing), 31 days |

## Recommended line-up

1. **Flights:** Aviasales (done).
2. **Hotels:**
   - Apply to the **Expedia Group Travel Creator Program** now. It's direct and accepts "anyone"; "Check hotels" links go to Expedia or Hotels.com.
   - Join **Klook** in Travelpayouts as the second hotel link, especially for the Asian destinations.
   - Add **Hostelworld** for the budget tier.
3. **Activities:** **Viator direct** (8%, no minimum, Basic API instant), plus Klook and KKday for Asia.
4. **Metasearch:** apply to **Kayak**. Its deep links cover flights, hotels and packages, and its API could become the live-price check later.
5. **Later, with traffic:** Booking.com via CJ (try once the landing page has real content), Skyscanner (5,000 visitors a month), Tripadvisor, Agoda, Trip.com.

**How links will work:**
- Programs joined through Travelpayouts (Aviasales, Klook, KKday) can use the partner-links API.
- Direct programs (Expedia, Viator, Kayak, Hostelworld) each have their own link builder or deep-link format. One example link from each, created in its dashboard, is enough to build trip-specific links automatically.

Sources: booking.com/affiliate-program/v2, cj.com/en-gb/publisher/partners/booking.com, creator.expediagroup.com, partnerresources.viator.com (affiliate and levels-of-access pages), partners.skyscanner.net/product/affiliates, affiliates.kayak.com (deeplinks and apis pages), partners.hostelworld.com, affiliate.klook.com, travelpayouts.com/en/offers/klook-affiliate-program, travelpayouts.com/en/offers/kkday-affiliate-program, trip.com/partners.

## Link formats seen (2026-11-25)

The owner's dashboard short links redirect as follows. `<click>` is a click ID Travelpayouts adds on each redirect.

| Program | Redirect target |
|---|---|
| Aviasales | `https://www.aviasales.com/?marker=809658.<click>-809658` |
| Klook | `https://affiliate.klook.com/redirect?aid=api|13694|<click>-809658|pid|809658&k_site=<encoded target URL>` |
| KKday | `https://invl.me/clndj1c?aff_sub=<click>-809658&url=<encoded target URL>` |

809658 is the partner ID ("marker"). The partner-links API also needs the **project ID (`trs`): 605382** ("Bahafin"). With both, the export step can create tracked links for any Aviasales, Klook or KKday page.

**Expedia:** the owner's first link is `https://expedia.com/affiliate/fsA8EBn`. It redirects to `www.expedia.com/affiliate/fsA8EBn`, and Expedia then answers automated requests with HTTP 429, so the target and parameter format are unknown. Each Creator Toolbox link is a short code for one page. Trip-specific hotel links need either a parameter format that can be added to any Expedia URL, or one short code per destination made in the Link Builder (25 destinations is manageable). Open question for the owner (TODO.md).
