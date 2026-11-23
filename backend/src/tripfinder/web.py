"""Local demo web app: one page plus a JSON search endpoint. Searches read only the database."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import Settings
from .costs import report
from .db import connect
from .engine import TripRequest
from .money import Money
from .search import load_notes, search, to_dict

PAGE = Path(__file__).with_name("static") / "index.html"


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Budget Trip Finder POC")
    conn = connect(settings.db_path)
    notes = load_notes(settings.seed_dir)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return PAGE.read_text(encoding="utf8")

    @app.get("/api/search")
    def api_search(
        budget: float = Query(gt=0),
        adults: int = Query(2, ge=1, le=9),
        children: int = Query(0, ge=0, le=9),
        month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
        nights: int | None = Query(None, ge=1, le=30),
        tier: str = Query("mid", pattern="^(budget|mid|upscale)$"),
        sort: str = Query("cheapest", pattern="^(cheapest|most_nights)$"),
        limit: int = Query(12, ge=1, le=50),
    ) -> dict:
        try:
            req = TripRequest(Money.of(budget), adults, children, month or None, nights, tier, sort)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        results = search(conn, req)[:limit]
        months = [r[0] for r in conn.execute("SELECT DISTINCT substr(depart, 1, 7) FROM fares ORDER BY 1")]
        return {"results": [to_dict(p, req, conn, settings, notes) for p in results], "months": months}

    @app.get("/api/costs", response_class=PlainTextResponse)
    def api_costs() -> str:
        return report(conn, settings)

    return app
