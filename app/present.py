"""Shape a pipeline result the way the request inbox expects it."""

from __future__ import annotations

PREFIX_PROPERTY = {
    "W": "The Weaver",
    "E": "Estes Commons",
    "P": "Pritchard Court",
    "M": "Merritt Mill Flats",
    "C": "Church Street Duplexes",
    "B": "Barclay Townhomes",
}

PRIYA_CATEGORY = {
    "rent_payment": "rent",
    "legal": "legal",
    "esa": "esa",
}

ROUTE_CATEGORY = {
    "emergency": "emergency",
    "urgent_maintenance": "urgent",
    "routine_maintenance": "routine",
    "leasing": "leasing",
    "noise": "noise",
    "fraud": "fraud",
    "human": "review",
}


def to_request(result: dict) -> dict:
    unit = result.get("unit") or ""
    category = _category(result)
    return {
        "id": result["message_id"],
        "received_at": result["received_at"],
        "channel": result.get("channel") or "",
        "sender": result.get("from") or "",
        "contact": result.get("from") or "",
        "property": PREFIX_PROPERTY.get(unit[:1], ""),
        "unit": unit,
        "body": result.get("body") or "",
        "category": category,
        "language": (result.get("classification") or {}).get("language") or "en",
        "deadline": result.get("deadline"),
        "linked_to": result.get("linked_to"),
        "confidence": (result.get("classification") or {}).get("confidence"),
        "gemini_called": bool(result.get("gemini_called")),
        "agent": _agent_text(result),
    }


def _category(result: dict) -> str:
    route = result.get("route")
    if route == "priya":
        message_type = (result.get("classification") or {}).get("message_type")
        return PRIYA_CATEGORY.get(message_type, "review")
    return ROUTE_CATEGORY.get(route, "review")


def _agent_text(result: dict) -> str:
    chunks: list[str] = []
    if result.get("tenant_reply"):
        chunks.append(result["tenant_reply"])
    if result.get("luis_call_script"):
        chunks.append("Draft call to Luis: " + result["luis_call_script"])
    if result.get("vendor_text"):
        name = (result.get("vendor") or {}).get("name") or "vendor"
        chunks.append(f"Draft text to {name}: {result['vendor_text']}")
    work_order = result.get("work_order")
    if work_order:
        chunks.append(f"Work order for {work_order['assign_to']} ({work_order['priority']}).")
    if result.get("priya_summary") and not result.get("tenant_reply"):
        chunks.append(result["priya_summary"].split("\n", 1)[0])
    if result.get("review_reason"):
        chunks.append(result["review_reason"])
    return "\n\n".join(chunks)
