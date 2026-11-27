// node --test site/tests/pages.test.mjs: every number on the generated pages must be what the browser engine
// gives for the same request. `python -m tripfinder pages` writes pages-manifest.json with each priced call.
import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";
import { bestPackage, prepare, pricePackage } from "../engine.js";

const here = new URL(".", import.meta.url);
// One manifest per departure city (pages-manifest-<slug>.json), checked against that city's data file.
const cities = existsSync(new URL("../data/", here))
  ? readdirSync(new URL("../data/", here)).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5))
  : [];

for (const slug of cities) {
const manifestUrl = new URL(`pages-manifest-${slug}.json`, here);
test(`pages manifest matches the browser engine (${slug})`, { skip: !existsSync(manifestUrl) && "run `python -m tripfinder pages` first" }, () => {
  const snapshot = JSON.parse(readFileSync(new URL(`../data/${slug}.json`, here), "utf8"));
  const manifest = JSON.parse(readFileSync(manifestUrl, "utf8"));
  const C = snapshot.constants;
  const today = manifest.today;
  // Destination pages price flight trips only (ground trips are finder-only for now), so ground options are left out.
  const dests = new Map(prepare(snapshot, today).map((d) => [d.code, { ...d, ground: null }]));
  assert.ok(manifest.calls.length > 0, "no priced calls in the manifest");
  for (const call of manifest.calls) {
    let dest = dests.get(call.code);
    if (call.window) {
      const w = call.window;
      dest = { ...dest, fares: dest.fares.filter((f) => w.departFrom <= f.depart && f.depart <= w.departTo && w.retFrom <= f.ret && f.ret <= w.retTo) };
    }
    const req = call.request;
    const got = call.kind === "price" ? pricePackage(dest, req, call.nights, req.month, today, C) : bestPackage(dest, req, today, C);
    const label = `${call.kind} ${call.code} ${JSON.stringify(req)}`;
    if (call.result === null) {
      assert.equal(got, null, label);
      continue;
    }
    assert.ok(got, `${label}: engine.js priced nothing`);
    assert.deepEqual([got.nights, got.month, got.fit, got.fare.depart], [call.result.nights, call.result.month, call.result.fit, call.result.depart], label);
    for (const k of ["low", "expected", "high"]) {
      assert.ok(Math.abs(got.total[k] - call.result[k]) <= 1, `${label} ${k}: ${got.total[k]} vs ${call.result[k]}`);
    }
  }
});
}
