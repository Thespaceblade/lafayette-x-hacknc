"""Route a Jev result. Keyword overrides beat a low-confidence classification."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.config import CONFIDENCE_CUTOFF, FRAUD_CUTOFF

_CO = re.compile(r"carbon monoxide|\bco alarm\b", re.IGNORECASE)
_FIRE = re.compile(r"\bfire\b", re.IGNORECASE)
_GAS = re.compile(r"\bgas\b", re.IGNORECASE)

ROUTES_BY_TYPE = {
    "emergency_maintenance": "emergency",
    "urgent_maintenance": "urgent_maintenance",
    "routine_maintenance": "routine_maintenance",
    "leasing": "leasing",
    "rent_payment": "priya",
    "legal": "priya",
    "esa": "priya",
    "noise": "noise",
}

SAFETY_LINES = {
    "gas": (
        "Leave the unit now and call 911 and Enbridge Gas North Carolina from outside. "
        "Do not flip any switches."
    ),
    "co": (
        "Leave the unit now, including pets, and call 911 from outside. "
        "Do not stay inside with the windows open."
    ),
    "fire": "Leave the unit now and call 911.",
}

_SAFETY_ANCHOR = {
    "gas": "do not flip",
    "co": "including pets",
    "fire": "call 911",
}


def safety_kind(body: str) -> str | None:
    """Gas, carbon monoxide, or fire. A chirping smoke alarm is not a fire."""
    if _CO.search(body):
        return "co"
    if _FIRE.search(body):
        return "fire"
    if _GAS.search(body) and "gas bill" not in body.lower():
        return "gas"
    return None


def decide_route(classification: dict, safety: str | None) -> str:
    if safety:
        return "emergency"
    if (classification.get("is_fraud") or 0) >= FRAUD_CUTOFF:
        return "fraud"
    confidence = classification.get("confidence")
    if confidence is None or confidence < CONFIDENCE_CUTOFF:
        return "human"
    message_type = classification.get("message_type")
    if message_type == "emergency_maintenance" or (classification.get("is_emergency") or 0) >= FRAUD_CUTOFF:
        return "emergency"
    return ROUTES_BY_TYPE.get(message_type, "human")


def deadline_for(route: str, received_at: datetime) -> datetime:
    if route == "emergency" or route == "leasing" or route == "human":
        return received_at + timedelta(hours=1)
    if route == "fraud":
        return received_at
    if route == "urgent_maintenance" or route == "priya":
        return same_or_next_business_day(received_at)
    if route == "noise":
        return add_business_days(received_at, 1)
    if route == "routine_maintenance":
        return add_business_days(received_at, 5)
    return received_at + timedelta(hours=1)


def ensure_safety(reply: str, safety: str | None) -> str:
    if not safety:
        return reply
    anchor = _SAFETY_ANCHOR[safety]
    if anchor in reply.lower():
        return reply
    return f"{SAFETY_LINES[safety]}\n\n{reply}".strip()


def same_or_next_business_day(moment: datetime) -> datetime:
    if moment.weekday() < 5 and moment.hour < 17:
        return _at_1700(moment)
    return add_business_days(moment, 1)


def add_business_days(moment: datetime, days: int) -> datetime:
    cursor = moment
    left = days
    while left:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            left -= 1
    return _at_1700(cursor)


def _at_1700(moment: datetime) -> datetime:
    return moment.replace(hour=17, minute=0, second=0, microsecond=0)
