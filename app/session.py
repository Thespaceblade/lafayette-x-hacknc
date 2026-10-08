"""In-memory weekend. Replay and a pasted message share one ticket list."""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from app.config import MONDAY_CUTOFF, SCENARIO_NOW, iso
from app.data import Data, Message, leasing_stats, load_data
from app.handlers import run_handler
from app.jev import JevError, classify
from app.route import deadline_for, decide_route, safety_kind


class Session:
    def __init__(self) -> None:
        self.results: list[dict] = []
        self.tickets: dict[str, dict] = {}
        self.data: Data | None = None
        self._paste_n = 0

    def load(self) -> Data:
        if self.data is None:
            self.data = load_data()
        return self.data

    def reset(self) -> None:
        self.results = []
        self.tickets = {}
        self._paste_n = 0

    def load_results(self, results: list[dict]) -> None:
        """Restore a saved replay so a new message can still link to those tickets."""
        self.reset()
        self.load()
        self.results = list(results)
        for result in self.results:
            root_id = result.get("linked_to") or result["message_id"]
            self.tickets[result["message_id"]] = {
                "message_id": result["message_id"],
                "root_id": root_id,
                "deadline": datetime.fromisoformat(result["deadline"]),
                "received_at": result["received_at"],
                "unit": result.get("unit") or "",
                "summary": " ".join(result["body"].split())[:160],
                "route": result["route"],
                "is_noise": result["route"] == "noise",
            }

    def replay(self) -> list[dict]:
        self.reset()
        data = self.load()
        for message in data.messages:
            self.handle(message)
        return self.results

    def paste(
        self,
        body: str,
        channel: str = "email",
        sender: str = "",
        unit: str = "",
        received_at: datetime | None = None,
        message_id: str | None = None,
    ) -> dict:
        self.load()
        self._paste_n += 1
        message = Message(
            message_id=message_id or f"P{self._paste_n}",
            received_at=received_at or SCENARIO_NOW,
            channel=channel,
            sender=sender,
            unit=unit.strip(),
            body=body,
        )
        return self.handle(message)

    def handle(self, message: Message) -> dict:
        data = self.load()
        safety = safety_kind(message.body)
        try:
            classification = classify(message, self._open_tickets())
        except JevError as exc:
            classification = _failed_classification(str(exc))

        route = decide_route(classification, safety)
        linked_to = self._resolve_link(classification.get("follow_up_of"))
        root = self.tickets.get(linked_to) if linked_to else None
        deadline = root["deadline"] if root else deadline_for(route, message.received_at)
        output = run_handler(
            route,
            message,
            classification,
            safety,
            deadline,
            data,
            self.tickets,
        )
        result = {
            "message_id": message.message_id,
            "received_at": iso(message.received_at),
            "channel": message.channel,
            "from": message.sender,
            "unit": message.unit or None,
            "body": message.body,
            "route": route,
            "linked_to": linked_to,
            "deadline": iso(deadline),
            "safety_override": safety,
            "classification": classification,
            **output,
        }
        self.results.append(result)
        root_id = root["root_id"] if root else message.message_id
        self.tickets[message.message_id] = {
            "message_id": message.message_id,
            "root_id": root_id,
            "deadline": deadline,
            "received_at": iso(message.received_at),
            "unit": message.unit or (root["unit"] if root else ""),
            "summary": " ".join(message.body.split())[:160],
            "route": route,
            "is_noise": route == "noise",
        }
        if root:
            root.setdefault("followups", []).append(message.message_id)
        return result

    def inbox(self) -> dict:
        gemini_calls = sum(1 for result in self.results if result["gemini_called"])
        return {
            "scenario_now": iso(SCENARIO_NOW),
            "count": len(self.results),
            "gemini_calls": gemini_calls,
            "no_llm_calls": len(self.results) - gemini_calls,
            "by_route": dict(Counter(result["route"] for result in self.results)),
            "messages": self.results,
        }

    def overdue(self) -> dict:
        late = [
            result
            for result in self.results
            if datetime.fromisoformat(result["deadline"]) <= MONDAY_CUTOFF
        ]
        return {
            "as_of": iso(MONDAY_CUTOFF),
            "count": len(late),
            "messages": late,
        }

    def stats(self) -> dict:
        return leasing_stats(self.load().history)

    def _open_tickets(self) -> list[dict]:
        return [
            {
                "message_id": ticket["message_id"],
                "unit": ticket["unit"],
                "summary": ticket["summary"],
            }
            for ticket in self.tickets.values()
        ]

    def _resolve_link(self, follow_up_of: object) -> str | None:
        if not follow_up_of or follow_up_of == "none":
            return None
        ticket = self.tickets.get(str(follow_up_of))
        if not ticket:
            return None
        return ticket["root_id"]


def _failed_classification(error: str) -> dict:
    return {
        "message_type": None,
        "confidence": None,
        "probabilities": {},
        "is_emergency": 0.0,
        "is_fraud": 0.0,
        "language": "en",
        "language_confidence": None,
        "follow_up_of": "none",
        "answers": {},
        "model": None,
        "usage": {},
        "error": error,
    }
