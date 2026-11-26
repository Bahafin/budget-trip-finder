"""Command line: python -m tripfinder <command>.

  select              pick launch destinations from flight coverage
  refresh [what]      refresh reference | flights | hotels | all
  search ...          ranked packages for a budget
  costs               what keeping the data fresh costs (from the api_calls log)
  serve               local web page on http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from . import jobs
from .config import ROOT, load_settings
from .db import connect
from .engine import TripRequest
from .money import Money
from .search import load_notes, search, to_dict


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tripfinder")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("select")
    r = sub.add_parser("refresh")
    r.add_argument("what", choices=["reference", "flights", "hotels", "all", "auto"], default="all", nargs="?")
    r.add_argument("--only", help="comma-separated destination codes (hotels only)")
    r.add_argument("--force", default="", help="auto: comma-separated steps to run even if fresh (reference,select,flights,hotels)")
    s = sub.add_parser("search")
    s.add_argument("--budget", type=float, required=True, help="total trip budget in CAD")
    s.add_argument("--adults", type=int, default=2)
    s.add_argument("--children", type=int, default=0)
    s.add_argument("--month", help="YYYY-MM")
    s.add_argument("--nights", type=int)
    s.add_argument("--tier", default="mid", choices=["budget", "mid", "upscale"])
    s.add_argument("--sort", default="cheapest", choices=["cheapest", "most_nights"])
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--json", action="store_true")
    sub.add_parser("costs")
    sv = sub.add_parser("serve")
    sv.add_argument("--port", type=int, default=8000)
    ga = sub.add_parser("gate-a", help="50-trip accuracy test: generate a check sheet, or report on a filled one")
    ga.add_argument("action", choices=["generate", "report"])
    ga.add_argument("--n", type=int, default=50)
    ga.add_argument("--seed", type=int, default=2026)
    ga.add_argument("--sheet", default=str(ROOT / "docs" / "gate-a" / "sheet.csv"))
    ga.add_argument("--out", default=str(ROOT / "docs" / "gate-a" / "report.md"))
    ex = sub.add_parser("export", help="write the static site data snapshot (and parity cases for the JS engine)")
    ex.add_argument("--out", default=str(ROOT / "site" / "data.json"))
    ex.add_argument("--golden", default=str(ROOT / "site" / "tests" / "golden.json"))
    args = ap.parse_args(argv)

    settings = load_settings()
    conn = connect(settings.db_path)

    if args.cmd == "select":
        chosen = jobs.select_destinations(conn, settings)
        print(f"{len(chosen)} destinations: {' '.join(chosen)}")
    elif args.cmd == "refresh" and args.what == "auto":
        t = time.monotonic()
        outcome = jobs.refresh_auto(conn, settings, force=tuple(x for x in args.force.split(",") if x))
        for step, result in outcome.items():
            print(f"{step:<10} {result}")
        print(f"auto refresh finished in {time.monotonic() - t:.0f}s")
    elif args.cmd == "refresh":
        steps = ["reference", "flights", "hotels"] if args.what == "all" else [args.what]
        for step in steps:
            t = time.monotonic()
            if step == "hotels" and args.only:
                result = jobs.refresh_hotels(conn, settings, only=args.only.split(","))
            else:
                result = getattr(jobs, f"refresh_{step}")(conn, settings)
            print(f"{step}: {result} in {time.monotonic() - t:.0f}s")
    elif args.cmd == "search":
        req = TripRequest(Money.of(args.budget), args.adults, args.children, args.month, args.nights, args.tier, args.sort)
        results = search(conn, req)[: args.limit]
        notes = load_notes(settings.seed_dir)
        rows = [to_dict(p, req, conn, settings, notes) for p in results]
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print_results(rows, req)
    elif args.cmd == "costs":
        from .costs import report

        print(report(conn, settings))
    elif args.cmd == "serve":
        import uvicorn

        from .web import create_app

        uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port)
    elif args.cmd == "gate-a":
        from pathlib import Path

        from . import gate_a

        sheet = Path(args.sheet)
        if args.action == "generate":
            if sheet.exists():
                raise SystemExit(f"{sheet} exists; pass --sheet with a new name so filled-in prices are never overwritten")
            rows = gate_a.generate(conn, args.n, args.seed)
            gate_a.write_sheet(rows, sheet)
            print(f"{len(rows)} trips written to {sheet} ({sum(1 for r in rows if r['holiday'])} on holiday dates, "
                  f"{len({r['destination'] for r in rows})} destinations)")
        else:
            text = gate_a.report(sheet)
            Path(args.out).write_text(text + "\n", encoding="utf8")
            print(text.split("\n\n")[0:3][-1] if text else "")
            print(f"report written to {args.out}")
    elif args.cmd == "export":
        from pathlib import Path

        from .export import write_golden, write_snapshot
        from .links import check_template
        from .meter import Meter

        if settings.travelpayouts_token and not check_template(Meter(conn, "links"), settings):
            raise SystemExit("Travelpayouts partner link format changed: update PROGRAMS in links.py before exporting")
        print("snapshot:", write_snapshot(conn, settings, Path(args.out)))
        print("golden cases:", write_golden(conn, settings, Path(args.golden)))
    return 0


def print_results(rows: list[dict], req: TripRequest) -> None:
    if not rows:
        print("No destinations fit this budget.")
        return
    print(f"Budget {req.budget} for {req.adults} adult(s), {req.children} child(ren), {req.tier} tier\n")
    for i, r in enumerate(rows, 1):
        t = r["total"]
        flag = "" if r["fit"] == "within" else "  [stretch: only fits at the low end]"
        print(f"{i:>2}. {r['name']} ({r['code']}, {r['country']})  {r['nights']} nights, {r['dates']['depart']} to {r['dates']['return']}{flag}")
        print(f"    total {r['currency']} {t['expected']:,.0f}  (range {t['low']:,.0f} - {t['high']:,.0f}), per person {r['per_person']['expected']:,.0f}")
        for c in r["components"]:
            print(f"      {c['name']:<8} {c['expected']:>8,.0f}  [{c['confidence']}]  {c['detail']}")
        if r["advisory"] and r["advisory"]["level"]:
            print(f"      advisory: {r['advisory']['text']}")
        for n in r["know_before"]:
            print(f"      know before you go ({n['category']}): {n['summary']}")
        print()


if __name__ == "__main__":
    sys.exit(main())
