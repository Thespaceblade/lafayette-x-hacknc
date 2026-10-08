"""Load the Experienced-track files. Tenant names and vendor rates stay out of prompts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import DATA_DIR


@dataclass
class Message:
    message_id: str
    received_at: datetime
    channel: str
    sender: str
    unit: str
    body: str


@dataclass
class Data:
    messages: list[Message]
    units: list[dict]
    vendors: list[dict]
    slots: list[dict]
    history: list[dict]
    leasing_rules: str
    maintenance_rules: str
    reply_style: str


def _section(markdown: str, heading: str) -> str:
    marker = f"## {heading}"
    start = markdown.find(marker)
    if start < 0:
        return ""
    rest = markdown[start:]
    nxt = rest.find("\n## ", len(marker))
    return (rest if nxt < 0 else rest[:nxt]).strip() + "\n"


def load_data(directory: Path | None = None) -> Data:
    folder = directory or DATA_DIR
    handbook = (folder / "company.md").read_text()
    return Data(
        messages=_messages(folder / "messages.csv"),
        units=_rows(folder / "units.csv"),
        vendors=_rows(folder / "vendors.csv"),
        slots=_slots(folder / "showing_slots.csv"),
        history=_rows(folder / "response_history.csv"),
        leasing_rules=_section(handbook, "Leasing rules"),
        maintenance_rules=_section(handbook, "Maintenance priorities"),
        reply_style=_section(handbook, "What a good reply looks like"),
    )


def _rows(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _messages(path: Path) -> list[Message]:
    found = []
    for row in _rows(path):
        found.append(
            Message(
                message_id=row["message_id"],
                received_at=datetime.strptime(row["received_at"], "%Y-%m-%d %H:%M"),
                channel=row["channel"],
                sender=row["from"],
                unit=(row.get("unit") or "").strip(),
                body=row["body"],
            )
        )
    found.sort(key=lambda item: (item.received_at, item.message_id))
    return found


def _slots(path: Path) -> list[dict]:
    parsed = []
    for row in _rows(path):
        when = datetime.strptime(f"{row['date']} {row['start_time']}", "%Y-%m-%d %H:%M")
        parsed.append({**row, "at": when})
    return parsed


def available_units(data: Data) -> list[dict]:
    """Units a prospect could be told about. Occupied units and tenant names are omitted."""
    open_units = []
    for unit in data.units:
        if unit["status"] == "occupied":
            continue
        open_units.append(
            {
                "unit_id": unit["unit_id"],
                "property": unit["property"],
                "bedrooms": unit["bedrooms"],
                "bathrooms": unit["bathrooms"],
                "monthly_rent": unit["monthly_rent"],
                "status": unit["status"],
                "available_date": unit["available_date"],
                "pet_policy": unit["pet_policy"],
            }
        )
    return open_units


def open_slots(data: Data, received_at: datetime, limit: int = 16) -> list[dict]:
    upcoming = [
        slot
        for slot in data.slots
        if slot["status"] == "open" and slot["at"] >= received_at
    ]
    upcoming.sort(key=lambda slot: slot["at"])
    return [
        {
            "date": slot["date"],
            "day": slot["day"],
            "start_time": slot["start_time"],
        }
        for slot in upcoming[:limit]
    ]


def public_vendor(vendor: dict | None) -> dict | None:
    if not vendor:
        return None
    return {
        "vendor_id": vendor["vendor_id"],
        "name": vendor["name"],
        "trade": vendor["trade"],
        "phone": vendor["phone"],
        "after_hours": vendor["after_hours"],
    }


def leasing_stats(history: list[dict]) -> dict:
    """Tour rate from response_history.csv. Under 1 hour is 11 of 21; over a day is 8 of 92."""
    leasing = [row for row in history if row["type"] == "leasing"]

    def bucket(rows: list[dict]) -> dict:
        tours = sum(1 for row in rows if row["outcome"] == "tour booked")
        total = len(rows)
        return {
            "tours": tours,
            "total": total,
            "rate": (tours / total) if total else None,
        }

    under = [row for row in leasing if float(row["hours_to_first_response"]) < 1]
    over = [row for row in leasing if float(row["hours_to_first_response"]) > 24]
    return {
        "source": "response_history.csv",
        "metric": "leasing leads that booked a tour",
        "under_1_hour": bucket(under),
        "over_24_hours": bucket(over),
    }
