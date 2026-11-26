# Owner to-do list

Things only you can do: accounts, terms, payments, legal and decisions. The build plan is in [PLAN.md](PLAN.md). Updated 2026-11-26.

## Now (unblocks Stage 1: tester-ready site)

- [ ] **Register the Far Enough name** (decided 2026-11-26). In one sitting, so nobody grabs them in between:
  - re-check availability
  - register **farenough.ca** and **farenoughtrips.com** (farenough.com is taken)
  - claim **@farenoughtrips** on Instagram, TikTok and YouTube (and X if free)
  - then tell me, and I'll put the name, tagline ("See how far your budget goes.") and domain on the site
  - optional: a trademark agent's clearance search before spending on the brand
- [ ] **Expedia: find how to make a link to any page.** Your link (`expedia.com/affiliate/fsA8EBn`) is a short code, and Expedia blocks automated requests, so I can't see the format behind it. In the Creator Toolbox Link Builder, build a link for a **hotel search page** (e.g. Cancún, 2 adults, specific dates) and send me both the page URL you pasted and the link it gave you. If the Toolbox mentions a deep-link or URL parameter format (for example an affiliate ID you can add to any Expedia URL), send that instead. It's better.
- [ ] **Apply to Viator directly**: partners.viator.com. No traffic minimum, 8%, 30-day cookie. It's for the activities section, and its Basic API is instant. Send me one example link and the API key once approved.
- [ ] **Add two GitHub repo secrets** so the daily refresh can run: `TRAVELPAYOUTS_TOKEN` and `LITEAPI_KEY`. Do it at github.com/Bahafin/budget-trip-finder → Settings → Secrets and variables → Actions → New repository secret. Or from a terminal: `gh secret set TRAVELPAYOUTS_TOKEN -R Bahafin/budget-trip-finder` (it asks for the value). If you're about to generate new keys, add the new ones. The partner ID and project ID are public and already in the code.
- [ ] **Generate new API keys.** The Travelpayouts token, Duffel test token and LiteAPI sandbox key were pasted in chat. Put the new ones in `.env` (and later in the GitHub secrets).
- [ ] **Create a tester feedback form.** Google Forms or similar, with fields: trip shown, price we showed, price you found, where, comments. Send me the link and I'll add a "Was this price right?" button to each result.
- [ ] **Pick 5-10 testers** and send them the link once Stage 1 is done.

## Soon (unblocks Stage 2: Gate A)

- [ ] **LiteAPI production key**: attach a card in Nuitee Connect (dashboard → API Keys). Hotel prices become real instead of sandbox. Expected cost: about $0-5 a month at our volume.
- [ ] **Search a few of our destinations on Klook and KKday hotels** (e.g. Cancún, Orlando, Lisbon). Klook blocks automated browsers, so only you can check their hotel coverage outside Asia.
- [ ] **Decide whether to hide your email in the public repo history.** Commits currently show your Gmail. I can rewrite the history with GitHub's private noreply address; it needs a force push.

## Applications that may take a while

- [ ] **Kayak affiliate**: affiliates.kayak.com form. Deep links to flight and hotel searches; its API could become the live price check.
- [ ] **Hostelworld**: via Partnerize (partners.hostelworld.com). For the budget comfort tier.
- [ ] **Nuitee (LiteAPI)**: request Experiences access (Request Assistance → Experiences). Activate production flights later (Flights → Introduction), when we build the live price check.

## Decisions and legal (before public launch)

- [ ] **Employer outside-business-activity policy**: check disclosure rules. The Gate A report is your evidence that it works and costs almost nothing.
- [ ] **TICO**: ask in writing whether a referral-only site (affiliate links, no bookings or payments) needs registration in Ontario (Gate B). **Decision 2026-11-26: left open; building continues as if the answer is fine.** Ask before public promotion or paid traffic.
- [ ] **Email provider** for sign-ups and alerts (MailerLite, Buttondown or similar; CASL-compliant double opt-in). Needed before the landing page (content plan week 4).

## Later, once the site has traffic

- [ ] Booking.com via CJ (needs an active website).
- [ ] Skyscanner via Impact (5,000+ unique visitors a month).
- [ ] Re-apply to Booking.com, Expedia, Agoda and Trip.com inside Travelpayouts.
- [ ] GetYourGuide, Tripadvisor.

## Done

- [x] Travelpayouts account and API token (2026-11-22)
- [x] Wedge decided: Canadian departures (2026-11-21)
- [x] Joined Aviasales, Klook, KKday in Travelpayouts (2026-11-25)
- [x] Travelpayouts project ID shared: 605382 ("Bahafin") (2026-11-26)
- [x] Expedia Group Travel Creator Program joined; first link `expedia.com/affiliate/fsA8EBn` (2026-11-26)
- [x] LiteAPI sandbox account; Duffel test account (Duffel parked for Phase 2)
- [x] Public repo and test site approved (2026-11-23)
- [x] Brand name chosen: **Far Enough**, tagline "See how far your budget goes." (2026-11-26; see docs/brand/)
- [x] Gate C thresholds accepted (2026-11-26; see PLAN.md Stage 3)
- [x] Site redesign approved and merged (2026-11-26)
