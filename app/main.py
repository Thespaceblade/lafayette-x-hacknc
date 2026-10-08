"""Classifier gateway plus the request inbox.

Run: python -m uvicorn app.main:app --port 8000
"""

from __future__ import annotations

import json
import threading
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.config import ROOT
from app.present import to_request
from app.session import Session

CACHE = ROOT / "cache" / "replay.json"
_load_lock = threading.Lock()

app = FastAPI(title="Laurel Hill gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session = Session()


def ensure_loaded() -> None:
    with _load_lock:
        if session.results:
            return
        if CACHE.exists():
            session.load_results(json.loads(CACHE.read_text()))
            return
        session.replay()
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(session.results))


class Incoming(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    body: str
    channel: str = "email"
    sender: str = Field(default="", alias="from")
    unit: str = ""
    received_at: datetime | None = None
    message_id: str | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/replay")
def replay() -> dict:
    session.replay()
    return session.inbox()


@app.post("/messages")
def messages(incoming: Incoming) -> dict:
    return session.paste(
        body=incoming.body,
        channel=incoming.channel,
        sender=incoming.sender,
        unit=incoming.unit,
        received_at=incoming.received_at,
        message_id=incoming.message_id,
    )


@app.get("/inbox")
def inbox() -> dict:
    return session.inbox()


@app.get("/overdue")
def overdue() -> dict:
    return session.overdue()


@app.get("/stats")
def stats() -> dict:
    return session.stats()


@app.get("/api/requests")
def api_requests() -> dict:
    ensure_loaded()
    return {"source": "csv", "requests": [to_request(result) for result in session.results]}


@app.post("/api/requests")
def api_add_request(payload: dict) -> dict:
    body = str(payload.get("body") or "").strip()
    if not body:
        raise HTTPException(status_code=400, detail="body is required")
    ensure_loaded()
    result = session.paste(
        body=body,
        channel=str(payload.get("channel") or "web form"),
        sender=str(payload.get("sender") or ""),
        unit=str(payload.get("unit") or ""),
    )
    return to_request(result)


app.mount("/", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="frontend")
