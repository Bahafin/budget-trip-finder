# Owner to-do list

Things only you can do: accounts, terms, payments, legal and decisions. The build plan is in [PLAN.md](PLAN.md). Updated 2026-11-26.

## Now (unblocks Stage 1: tester-ready site)

- [x] **farenoughtrips.com registered** (done 2026-11-26). It's the development domain; the site stays hidden from search engines until the launch domain is final.
- [ ] **Hosting setup, in this order** (about 30 minutes; recommended 2026-11-26). After step 4 I do the rest: the deploy change, the www redirect and the checks.
  1. **Cloudflare account:** sign up free at dash.cloudflare.com. Turn on two-factor sign-in.
  2. **Add the domain:** Add a domain → farenoughtrips.com → Free plan. Cloudflare shows two nameservers (like `xxx.ns.cloudflare.com`). At the registrar where you bought the domain, replace its nameservers with those two. It can take from minutes to a day; Cloudflare emails you when the domain is active. If your registrar is Cloudflare itself, skip this step.
  3. **API token for the daily deploy:** My Profile → API Tokens → Create Token → Custom token, permission **Account → Cloudflare Pages → Edit**, limited to your account. Copy the token and your **Account ID** (on the domain's overview page, right column).
  4. **Two GitHub secrets** at github.com/Bahafin/budget-trip-finder → Settings → Secrets and variables → Actions: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`. Then tell me.
  5. **(after my first deploy) Attach the domain:** Workers & Pages → farenough → Custom domains → Set up a custom domain → farenoughtrips.com (and www.farenoughtrips.com). Cloudflare adds the DNS records and HTTPS itself.
  6. **Email forwarding:** domain → Email → Email Routing → Get started. Add `hello@farenoughtrips.com` forwarding to your Gmail and click the confirmation email Google receives. Cloudflare adds the mail records itself.
- [ ] **farenough.ca:** register it to hold it (about $15 a year), likely the launch domain. It needs a CIRA-certified registrar (Cloudflare's registrar may not sell .ca; check). Later, point its nameservers to Cloudflare too. farenough.com is taken.
- [ ] **Social handles:** claim **@farenoughtrips** on Instagram, TikTok and YouTube (and X if free).
- [ ] optional: a trademark agent's clearance search before spending on the brand.
- [x] **Expedia link format** (done 2026-11-26: you sent unshortened Link Builder links for Expedia and Hotels.com; every "Check hotels" button is now a tracked Expedia.ca search). One check for you in a day or two: in the Creator Toolbox reports, do clicks show up, and do they carry our reference (adref such as `site-CUN-hotel`)? If clicks appear without it, tell me and I'll copy the adref values from your links instead.
- [x] **Viator registration** (done 2026-11-26; sandbox key stored in `.env` as VIATOR_API_KEY, not in the repo).
- [ ] **Viator key says "Invalid API Key"** (checked twice on 2026-11-26, on both the sandbox and production addresses; still failing in the evening). In the Viator Partner Platform, check: (1) the key is active (new keys can take a while), (2) whether it's a sandbox or production key, (3) your partner ID (pid, starts with P00...) and access level (Basic affiliate is enough for us). If it still fails tomorrow, email affiliateapi@tripadvisor.com.
- [x] **Add two GitHub repo secrets** (done 2026-11-26; checked: the daily run uses them) so the daily refresh can run: `TRAVELPAYOUTS_TOKEN` and `LITEAPI_KEY`. Do it at github.com/Bahafin/budget-trip-finder → Settings → Secrets and variables → Actions → New repository secret. Or from a terminal: `gh secret set TRAVELPAYOUTS_TOKEN -R Bahafin/budget-trip-finder` (it asks for the value). If you're about to generate new keys, add the new ones. The partner ID and project ID are public and already in the code.
- [ ] **Generate new API keys.** The Travelpayouts token, Duffel test token and LiteAPI sandbox key were pasted in chat. Put the new ones in `.env` (and later in the GitHub secrets).
- [ ] **Spot-check the ground trip prices** in `data/seed/ground.csv` (added 2026-11-26, from memory of typical "from" fares, so rough): for a few rows, look up a VIA Rail / GO / Amtrak / BC Ferries Connector fare about a month out and tell me what you see. Also: which Whistler bus to link (the row has a fare but no link), and is there a Montreal to Mont-Tremblant bus worth listing (car only now)?
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
- [ ] **Email** (plan discussed 2026-11-26):
  - **Mailbox:** hello@farenoughtrips.com, forwarded to your Gmail by Cloudflare Email Routing (free). To send as that address: the sign-up provider's mail service or a free Zoho mailbox; Google Workspace (about $8-10 a month) only if you want a separate inbox.
  - **Sign-ups and alerts:** pick the provider. My suggestion: **MailerLite** (free tier, double opt-in, sign-up forms; check current limits). Personal "tell me when it fits" alerts come later: saved searches stored with us, sent through a transactional service (Brevo or Resend free tiers).
  - **CASL:** every email needs a mailing address. A PO box works if you'd rather not use your home address.
  - Needed before the landing page (content plan week 4).
- [ ] **Hosting:** Cloudflare Pages chosen; your setup steps are under "Now" above. GitHub keeps the code and the daily refresh.
- [ ] **Launch with several departure cities, not just Toronto** (decided 2026-11-26). Toronto stays the development city; Montreal and Vancouver are the first test cities.

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
- [x] Destination list kept in the repo (data/seed/destinations.csv); AI-generated destination photos ruled out (real Wikimedia photos only); AI image skills kept for marketing graphics later (2026-11-26)
