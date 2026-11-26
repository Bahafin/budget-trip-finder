// Browser port of backend/src/tripfinder/engine.py. Keep the two in step:
// site/tests/parity.test.mjs checks this file against results exported from the Python engine.

const TIERS = ["budget", "mid", "upscale"];
const NIGHTS_MIN = 3;
const NIGHTS_MAX = 14;

const DAY_MS = 86400000;
const parseDate = (s) => new Date(s + "T00:00:00Z");
const daysBetween = (a, b) => Math.round((parseDate(b) - parseDate(a)) / DAY_MS);
const monthIndex = (m) => Number(m.slice(0, 4)) * 12 + Number(m.slice(5, 7));
const range = (low, expected, high) => {
  const [l, e, h] = [low, expected, high].sort((a, b) => a - b);
  return { low: l, expected: e, high: h };
};
const scale = (r, f) => ({ low: r.low * f, expected: r.expected * f, high: r.high * f });
const add = (a, b) => ({ low: a.low + b.low, expected: a.expected + b.expected, high: a.high + b.high });

// "Check hotels" link for a trip. The export gives each destination a template; placeholders may be URL-encoded.
export function hotelLinkFor(dest, fare, req) {
  if (!dest.hotel) return null;
  const values = {
    checkin: fare.depart, checkout: fare.ret, adults: req.adults, children: req.children,
    rooms: roomsNeeded(req.adults, req.children),
  };
  let url = dest.hotel.url;
  for (const [k, v] of Object.entries(values)) url = url.replaceAll(`{${k}}`, v).replaceAll(`%7B${k}%7D`, v);
  return { url, partner: dest.hotel.partner };
}

export function roomsNeeded(adults, children) {
  return Math.max(Math.ceil(adults / 2), Math.ceil((adults + children) / 4), 1);
}

export function prepare(snapshot, today) {
  // Drop fares that have already departed and add derived fields once.
  return snapshot.destinations.map((d) => ({
    ...d,
    fares: d.fares
      .filter((f) => f.depart >= today)
      .map((f) => ({ ...f, nights: daysBetween(f.depart, f.ret), month: f.depart.slice(0, 7) })),
    bandMap: new Map(d.bands.map((b) => [`${b.month}|${b.tier}`, b])),
  }));
}

function flightComponent(dest, req, nights, month, today, C) {
  const tol = C.nightsTolerance;
  const inMonth = dest.fares.filter((f) => f.month === month);
  if (!inMonth.length) return null;
  const matching = inMonth.filter((f) => Math.abs(f.nights - nights) <= tol);
  const exact = matching.length > 0;
  const pool = [...(exact ? matching : inMonth)].sort(
    (a, b) => a.price - b.price || a.depart.localeCompare(b.depart) || a.ret.localeCompare(b.ret),
  );
  const prices = pool.map((f) => f.price);
  const best = pool[0];
  // Anchored on the fare for the trip's own dates; other dates only widen the top (see engine.py).
  const [liftExpected, liftHigh] = C.flightLift[exact ? "exact" : "nearby"];
  const expected = best.price * liftExpected;
  const high = Math.max(best.price * liftHigh, ...prices.slice(0, 5));
  const perPerson = range(best.price * C.flightLow, expected, high);
  const age = Math.max(0, daysBetween(best.foundOn, today)); // data stamped in UTC can be "tomorrow" locally
  const detail =
    `${pool.length} cached fares, cheapest $${Math.round(best.price)} pp on ${best.depart}, ${best.nights} nights` +
    (best.airline ? `, ${best.airline}${best.transfers ? `, ${best.transfers} stop${best.transfers > 1 ? "s" : ""}` : ", direct"}` : "") +
    (exact ? "" : ` (no fare near ${nights} nights; used nearest dates)`);
  return {
    comp: { name: "flights", ...scale(perPerson, req.adults + req.children), confidence: exact ? `cached (${age}d)` : "estimated", detail },
    fare: best,
  };
}

function nearestBand(dest, month, tier) {
  const months = dest.bands.filter((b) => b.tier === tier).map((b) => b.month).sort();
  if (!months.length) return null;
  let best = months[0];
  for (const m of months) {
    if (Math.abs(monthIndex(m) - monthIndex(month)) < Math.abs(monthIndex(best) - monthIndex(month))) best = m;
  }
  return dest.bandMap.get(`${best}|${tier}`);
}

function lodgingComponent(dest, req, nights, month, today, C) {
  const rooms = roomsNeeded(req.adults, req.children);
  const band = dest.bandMap.get(`${month}|${req.tier}`) || nearestBand(dest, month, req.tier);
  if (band) {
    const age = Math.max(0, daysBetween(band.asOf, today));
    return {
      name: "lodging",
      ...scale({ low: band.low, expected: band.mid, high: band.high }, rooms * nights),
      confidence: band.source === "liteapi" ? `sampled (${age}d)` : "estimated",
      detail: `${rooms} room(s) x ${nights} nights, ${req.tier} tier, from ${band.n} hotel prices`,
    };
  }
  const base = C.nightlyBase[req.tier] * (dest.priceLevel ?? 1);
  return {
    name: "lodging",
    ...scale({ low: base * 0.7, expected: base, high: base * 1.5 }, rooms * nights),
    confidence: "estimated",
    detail: `${rooms} room(s), no hotel sample; scaled Canadian average`,
  };
}

function dailyComponent(dest, req, nights, C) {
  const level = dest.priceLevel ?? 1;
  const perAdultDay = C.dailyBase[req.tier] * level;
  const people = req.adults + req.children * C.childDailyShare;
  const days = nights + 1;
  const expected = perAdultDay * people * days;
  const src = dest.priceLevel != null ? `price level ${level.toFixed(2)} x Canada` : "no price level; Canadian average";
  return {
    name: "daily",
    low: expected * 0.75,
    expected,
    high: expected * 1.3,
    confidence: "estimated",
    detail: `$${Math.round(perAdultDay)} per adult per day, ${days} days (${src})`,
  };
}

export function pricePackage(dest, req, nights, month, today, C) {
  const tol = C.nightsTolerance;
  const flight = flightComponent(dest, req, nights, month, today, C);
  if (!flight) return null;
  if (Math.abs(flight.fare.nights - nights) <= tol) nights = flight.fare.nights;
  const components = [flight.comp, lodgingComponent(dest, req, nights, month, today, C), dailyComponent(dest, req, nights, C)];
  const total = components.reduce((acc, c) => add(acc, c), { low: 0, expected: 0, high: 0 });
  const fit = total.expected <= req.budget ? "within" : total.low <= req.budget ? "stretch" : "over";
  return { dest, nights, month, fare: flight.fare, components, total, fit };
}

const FIT_ORDER = { within: 0, stretch: 1, over: 2 };

export function bestPackage(dest, req, today, C) {
  const months = req.month ? [req.month] : [...new Set(dest.fares.map((f) => f.month))].sort();
  const candidates = [];
  for (const month of months) {
    let pkg = null;
    if (req.nights != null) {
      pkg = pricePackage(dest, req, req.nights, month, today, C);
    } else {
      const lengths = [...new Set(dest.fares.filter((f) => f.month === month && f.nights >= NIGHTS_MIN && f.nights <= NIGHTS_MAX).map((f) => f.nights))].sort((a, b) => b - a);
      for (const n of lengths) {
        const p = pricePackage(dest, req, n, month, today, C);
        if (!p) break;
        pkg = p;
        if (p.fit === "within") break;
      }
    }
    if (pkg) candidates.push(pkg);
  }
  if (!candidates.length) return null;
  const key = (p) => [FIT_ORDER[p.fit], req.nights == null ? -p.nights : 0, p.total.expected];
  return candidates.reduce((best, p) => (compareKeys(key(p), key(best)) < 0 ? p : best));
}

function compareKeys(a, b) {
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i];
  return 0;
}

export function rank(packages, req) {
  const keep = packages.filter((p) => p.fit === "within" || p.fit === "stretch");
  const key =
    req.sort === "most_nights"
      ? (p) => [p.fit !== "within" ? 1 : 0, -p.nights, p.total.expected]
      : (p) => [p.fit !== "within" ? 1 : 0, p.total.expected];
  return keep.map((p, i) => [p, i]).sort((a, b) => compareKeys(key(a[0]), key(b[0])) || a[1] - b[1]).map(([p]) => p);
}

export function search(dests, req, today, C) {
  if (!(req.adults >= 1)) throw new Error("at least one adult");
  if (!TIERS.includes(req.tier)) throw new Error("unknown comfort tier");
  const pkgs = dests.map((d) => bestPackage(d, req, today, C)).filter(Boolean);
  return rank(pkgs, req);
}
