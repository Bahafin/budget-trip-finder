# Content calendar: 8 weeks (30 Nov 2026 – 24 Jan 2027)

Written 2026-11-25. Sized for a solo owner with a day job: **about 4-5 hours a week**. Anything that doesn't fit slides a week; the March break piece is the one fixed deadline (live by **4 January 2027**, because families search for March break in January).

## Ground rules for every piece

- Numbers come from `site/data.json` / the engine, with the date they were estimated. Re-check them on the day you publish.
- Headline number = whole-trip expected total for a stated group (usually 2 adults), never the cheapest fare alone.
- Affiliate disclosure at the top of any article with partner links. In videos: say it and put it in the caption ("Links may earn us a commission").
- Referral wording ("compare", "see on Expedia"), never "book with us".
- Site is `noindex` while testing. Articles can be drafted and published on the site anyway; search traffic starts after launch. Community posts in weeks 1-4 **don't link to the site at all**; they build reputation and collect questions.

## Community rules (check the sidebar again before every post)

| Community | Self-promotion position (as far as I could verify) | How we take part |
|---|---|---|
| r/PersonalFinanceCanada | Rules include no surveys and no self-promotion (quoted in a removed-post discussion; check the live sidebar). | Answer budgeting questions about trips with numbers and method. **Never link the site.** Profile can mention it. |
| r/TravelHacks, r/travel | Typical rules: no blog spam, no self-promotional links; some allow links in weekly threads. Unverified for the current version. | Helpful answers; link only if a mod-approved thread allows it and it directly answers the question. |
| r/toronto, r/askTO | Strict on advertising. | Answer "where can we go for $X" threads with numbers. No links. |
| r/churningcanada, r/PersonalFinanceCanada daily threads | Points/finance focused; promotion not allowed. | Read for questions; rarely post. |
| Facebook groups (YYZ Deals group, Toronto parents' groups, "Cheap travel from Canada"-type groups) | Varies by group; most ban links without admin approval. | Ask the admin first. Offer a monthly "where $2,000 goes this month" post written for the group, link only if they agree. |

General Reddit norm: keep at least 90% of activity non-promotional (the widely cited 90/10 guideline; Reddit's own wording may have changed). Use one honest account; say "I'm building a trip cost tool" if relevant. Never use multiple accounts or ask friends to upvote.

## Week by week

Formats: **A** = article on the site, **V** = short video (30-60 s, phone screen recording + voice-over; YouTube Shorts / TikTok / Instagram Reels), **C** = community post or answer, **E** = email (once a provider exists).

### Week 1 (30 Nov – 6 Dec): listen and publish the first sample
- **C (research, 1.5 h):** Read 20 recent threads on r/PersonalFinanceCanada, r/TravelHacks, r/askTO about trip budgets. Copy the exact questions people ask (no usernames) into `docs/content/questions-log.md`. This replaces our keyword estimates with real wording.
- **A:** Publish sample 1, *Cancún from Toronto: what a week really costs* (draft in `samples/`, refresh the numbers first).
  Hook: "The $389 flight is real. The week is $2,260 for two." (7 nights, 22-29 Jan, basic hotel, estimated 25 Nov)
- **V:** Screen recording of the cost breakdown. Hook: "Everyone quotes the flight. Here's the rest of the bill for Cancún."

### Week 2 (7 – 13 Dec): the budget-first angle
- **A:** Publish sample 2, *Where $2,000 gets two people from Toronto in January*.
  Hook: "Three trips fit. Tokyo is $6,900. Here's the honest list."
- **V:** "We typed $2,000 into a trip calculator for January. Only 3 of 25 places fit." Show the list scrolling.
- **C:** 3-5 genuine answers to budget questions on Reddit using our method ("flights are about X per person in January, hotels Y a night, plan Z a day"), no links.

### Week 3 (14 – 20 Dec): spending money
- **A:** *How much spending money do you need in Mexico and the Dominican Republic?* (daily estimates per tier, what's included, how we estimate, the honest "this part is unverified, tell us what you spent").
  Hook: "Your all-inclusive covers the food. It doesn't cover these 6 things."
- **V:** "What $91 a day gets you in Cancún vs $140 in Toronto" (price level explained in 30 s).
- **C:** Ask in r/PersonalFinanceCanada (as a discussion, no link, if rules allow): "For those back from Mexico/DR: what did you actually spend per day beyond the hotel?" Collect answers to check our daily estimates (the validation doc's open item 5).

### Week 4 (21 – 27 Dec): holiday week, light
- **A (short):** *Why holiday flights from Toronto cost double* using our own December data (Cancún fares on 6 Dec vs 19-28 Dec: about $436 vs $800-1,060 per person).
  Hook: "Same seat, same plane, 2.4x the price. We tracked every Toronto–Cancún fare in December."
- **V:** chart of December fares by date. Hook: "Fly on the 6th, not the 19th."
- **C:** none (holidays). Update `questions-log.md`.

### Week 5 (28 Dec – 3 Jan): March break, the big one
- **A:** *March break 2027 from Toronto: what fits $3,000 and $5,000 for a family of four* (2 adults + 2 children, engine supports children). Needs March fares in the cache; if they're thin, publish with clear "early estimate" labels and update weekly.
  Hook: "March break prices go up every week in January. Here's what fits today."
- **V:** "A family of 4, $5,000, March break. Here's where it goes."
- **E:** first email if a provider is set up: "March break: what fits your budget this week".
- Deadline: **live by 4 Jan**.

### Week 6 (4 – 10 Jan): all-inclusive vs do-it-yourself
- **A:** *All-inclusive vs booking flights and hotel separately: a real comparison for Cancún and Punta Cana* — our DIY totals next to publicly listed package "from" prices, both dated, plus what each leaves out (tips, resort fees, excursions, food quality). Not a deal list; no "best deal" claims.
  Hook: "We priced Punta Cana both ways. The answer depends on one thing: how much you drink."
- **V:** split-screen comparison.
- **C:** Facebook: message 2-3 group admins (Toronto travel/parent groups) offering a monthly no-link "where $2,000 goes this month" post. Only post where approved.

### Week 7 (11 – 17 Jan): February and reading week
- **A:** *Where $1,500 gets two people in February* (students and couples; budget tier). Plus *Reading week from Toronto under $1,500*.
  Hook: "Reading week on $750 each: the real options."
- **V:** "Student budget: $750 each, one week, from Pearson."
- **C:** r/UofT, r/yorku, r/TMU: check rules; most allow genuinely useful posts. Ask first if unsure.

### Week 8 (18 – 24 Jan): review and repeat
- **A:** Refresh samples 1-2 with new numbers ("updated <date>") and publish *Where $2,000 gets two people in February* from the same template.
- **Review (1 h):** Search Console (if launched), video views, email sign-ups, which community answers got traction. Decide the next 8 weeks: double down on whatever produced sign-ups.
- **V:** best-performing format again with a new destination.

## Video production notes

- Phone screen recording of the trip finder + voice-over. No faces needed, no music licensing (use platform library audio).
- First 2 seconds = the number and the twist ("$327 flight, $2,260 trip").
- Caption: "Estimates in CAD, checked <date>. Prices change. Links may earn us a commission. We don't sell trips; you book on the partner's site."
- Same video to YouTube Shorts, TikTok and Reels. Account creation is an owner task (not done).

## Hook bank (spare hooks for later weeks)

- "Bali is cheap. Getting there isn't: $2,900 in flights for two." (January 2027 data: about $1,335 per person cheapest)
- "Montreal for a weekend costs more than Cancún for five nights." (check numbers before using)
- "The cheapest trip from Toronto this month isn't somewhere warm."
- "Your hotel's 'from $80' doesn't include the resort fee."
- "Why the trip calculator says 'stretch' and not 'yes'."
