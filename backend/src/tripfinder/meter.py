"""HTTP client that records every outbound call (provider, endpoint, status, time, bytes).

The api_calls table is how the POC proves what keeping the data fresh costs. Query strings and
headers are never logged, so keys stay out of the database.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any


class ApiError(RuntimeError):
    def __init__(self, provider: str, status: int, body: str):
        super().__init__(f"{provider} HTTP {status}: {body[:300]}")
        self.status = status


class Meter:
    def __init__(self, conn: sqlite3.Connection, job: str = ""):
        self.conn = conn
        self.job = job
        self.run = f"{job}@{datetime.now(UTC).isoformat(timespec='seconds')}"
        self._lock = threading.Lock()

    def request(
        self,
        provider: str,
        url: str,
        *,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
        timeout: float = 60,
        retries: int = 3,
    ) -> Any:
        full = url + ("?" + urllib.parse.urlencode(params) if params else "")
        data = json.dumps(body).encode() if body is not None else None
        hdrs = {"Accept": "application/json", "Accept-Encoding": "identity", **(headers or {})}
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        endpoint = urllib.parse.urlparse(url).path
        for attempt in range(retries + 1):
            req = urllib.request.Request(full, data=data, method=method, headers=hdrs)
            start = time.monotonic()
            status, raw, retry_after = 0, b"", None
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status, raw = resp.status, resp.read()
            except urllib.error.HTTPError as e:
                status, raw = e.code, e.read()
                retry_after = e.headers.get("Retry-After")
            except (urllib.error.URLError, TimeoutError) as e:
                raw = str(e).encode()
            finally:
                self._log(provider, endpoint, status, start, len(raw))  # every attempt is logged and counted
            if status in (0, 429, 502, 503, 504) and attempt < retries:
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 2 * 2**attempt
                time.sleep(min(wait, 30))
                continue
            break
        if status >= 400 or status == 0:
            raise ApiError(provider, status, raw.decode("utf8", "replace"))
        return json.loads(raw)

    def _log(self, provider: str, endpoint: str, status: int, start: float, size: int) -> None:
        ms = int((time.monotonic() - start) * 1000)
        with self._lock:
            self.conn.execute(
                "INSERT INTO api_calls (job, run, provider, endpoint, status, ms, bytes, at) VALUES (?,?,?,?,?,?,?,?)",
                (self.job, self.run, provider, endpoint, status, ms, size, datetime.now(UTC).isoformat(timespec="seconds")),
            )
            self.conn.commit()
