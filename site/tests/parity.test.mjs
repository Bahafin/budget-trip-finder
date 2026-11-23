// node --test site/tests/parity.test.mjs: the browser engine must rank and price like the Python engine.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { prepare, roomsNeeded, search } from "../engine.js";

const here = new URL(".", import.meta.url);
const snapshot = JSON.parse(readFileSync(new URL("../data.json", here), "utf8"));
const golden = JSON.parse(readFileSync(new URL("golden.json", here), "utf8"));
const dests = prepare(snapshot, golden.today);

for (const c of golden.cases) {
  test(`parity: ${JSON.stringify(c.request)}`, () => {
    const req = { children: 0, month: null, nights: null, tier: "mid", sort: "cheapest", ...c.request };
    const got = search(dests, req, golden.today, snapshot.constants);
    assert.deepEqual(
      got.map((p) => [p.dest.code, p.nights, p.month, p.fit]),
      c.results.map((r) => [r.code, r.nights, r.month, r.fit]),
    );
    got.forEach((p, i) => {
      for (const k of ["low", "expected", "high"]) {
        assert.ok(Math.abs(p.total[k] - c.results[i][k]) <= 1, `${p.dest.code} ${k}: ${p.total[k]} vs ${c.results[i][k]}`);
      }
    });
  });
}

test("rooms match the Python rule", () => {
  const cases = [[1, 0, 1], [2, 0, 1], [3, 0, 2], [4, 0, 2], [2, 2, 1], [2, 3, 2], [1, 4, 2], [5, 1, 3]];
  for (const [a, c, r] of cases) assert.equal(roomsNeeded(a, c), r);
});
