"""Tiny dev server for the Laurel Hill request inbox.

    python server.py            # http://localhost:8000

Serves frontend/ and a small JSON API:
    GET  /api/requests   -> {"source": "csv"|"sample", "requests": [...]}
    POST /api/requests   -> add a request submitted from the form

Hook point: set `category` on each request (e.g. from the classifier) and the
front-end will use it instead of its keyword fallback.
"""
import csv
import json
import os
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
MESSAGES_CSV = ROOT / "data" / "messages.csv"

# messages.csv column names aren't fixed yet, so accept common variants.
ALIASES = {
    "id": ["id", "message_id", "msg_id"],
    "received_at": ["received_at", "timestamp", "received", "time"],
    "channel": ["channel", "source", "type"],
    "sender": ["sender", "from", "name", "sender_name"],
    "contact": ["contact", "phone", "email", "from_address", "sender_contact"],
    "property": ["property", "building"],
    "unit": ["unit", "unit_id", "apt"],
    "body": ["body", "message", "text", "content"],
    "category": ["category", "label"],
    "language": ["language", "lang"],
}


def _normalize(row, i):
    lower = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
    out = {}
    for field, names in ALIASES.items():
        out[field] = next((lower[n] for n in names if lower.get(n)), "")
    out["id"] = out["id"] or f"M{i:03d}"
    if not out["category"]:
        out.pop("category")  # let the front-end classify
    if not out["language"]:
        out.pop("language")
    return out


def load_requests():
    if not MESSAGES_CSV.exists():
        return None
    with MESSAGES_CSV.open(newline="", encoding="utf-8-sig") as f:
        return [_normalize(r, i) for i, r in enumerate(csv.DictReader(f), 1)]


REQUESTS = load_requests()  # None -> front-end uses its sample data
SUBMITTED = []


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/requests":
            # source "sample": no CSV yet, so the front-end adds its built-in sample requests.
            source = "sample" if REQUESTS is None else "csv"
            return self._json(200, {"source": source, "requests": SUBMITTED[::-1] + (REQUESTS or [])})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/requests":
            return self._json(404, {"error": "not found"})
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid JSON"})
        if not str(data.get("body", "")).strip():
            return self._json(400, {"error": "body is required"})
        req = {k: str(data.get(k, "")).strip() for k in ("sender", "contact", "property", "unit", "body", "channel", "category")}
        if not req["category"]:
            req.pop("category")
        req["id"] = f"N{len(SUBMITTED) + 1:03d}"
        req["received_at"] = datetime.now().isoformat(timespec="minutes")
        SUBMITTED.append(req)
        return self._json(201, req)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    src = MESSAGES_CSV if REQUESTS is not None else "built-in sample data"
    print(f"Serving on http://localhost:{port}  (requests from {src})")
    ThreadingHTTPServer(("", port), Handler).serve_forever()
