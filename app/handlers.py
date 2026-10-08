"""Emergency and leasing call Gemini. Every other route is a template."""

from __future__ import annotations

import re
from datetime import datetime

from app.config import (
    JAKE_NAME,
    JAKE_PHONE,
    LUIS_NAME,
    LUIS_PHONE,
    PRIYA_NAME,
    friendly,
    iso,
)
from app.data import Data, Message, available_units, open_slots, public_vendor
from app.gemini import GeminiError, generate_json
from app.route import SAFETY_LINES, ensure_safety

EMERGENCY_SCHEMA = {
    "type": "object",
    "properties": {
        "tenant_reply": {"type": "string"},
        "luis_call_script": {"type": "string"},
        "vendor_text": {"type": "string"},
    },
    "required": ["tenant_reply", "luis_call_script", "vendor_text"],
}

LEASING_SCHEMA = {
    "type": "object",
    "properties": {
        "draft_reply": {"type": "string"},
        "suggested_units": {"type": "array", "items": {"type": "string"}},
        "suggested_slot": {"type": "string"},
        "handoff_to_priya": {"type": "boolean"},
        "handoff_reason": {"type": "string"},
    },
    "required": [
        "draft_reply",
        "suggested_units",
        "suggested_slot",
        "handoff_to_priya",
        "handoff_reason",
    ],
}

_BLANK = {
    "gemini_called": False,
    "needs_human": False,
    "fraud_flag": False,
    "tenant_reply": None,
    "luis_call_script": None,
    "vendor_text": None,
    "vendor": None,
    "work_order": None,
    "priya_summary": None,
    "suggested_units": [],
    "suggested_slot": None,
    "handoff_to_priya": False,
    "handoff_reason": None,
    "review_reason": None,
}


def run_handler(
    route: str,
    message: Message,
    classification: dict,
    safety: str | None,
    deadline: datetime,
    data: Data,
    tickets: dict,
) -> dict:
    output = dict(_BLANK)
    output["suggested_units"] = []
    language = classification.get("language") or "en"

    if route == "emergency":
        return _emergency(output, message, safety, deadline, data, language)
    if route == "leasing":
        return _leasing(output, message, deadline, data, language)
    if route in ("urgent_maintenance", "routine_maintenance"):
        return _maintenance(output, message, route, deadline, data, language)
    if route == "noise":
        return _noise(output, message, deadline, language, tickets)
    if route == "priya":
        return _priya(output, message, classification, deadline)
    if route == "fraud":
        return _fraud(output, message)
    output["needs_human"] = True
    output["review_reason"] = classification.get("error") or (
        "Classifier confidence is below 0.6, so this waits for a person."
    )
    return output


def _emergency(output, message, safety, deadline, data, language) -> dict:
    vendor = _select_vendor(data.vendors, message.body, safety, emergency=True)
    output["vendor"] = public_vendor(vendor)
    output["gemini_called"] = True
    when = friendly(deadline)
    vendor_line = (
        f"After-hours vendor: {vendor['name']} ({vendor['trade']}), {vendor['phone']}. "
        "vendor_text is a text message dispatching them. Do not mention their hourly rate."
        if vendor
        else (
            "There is no matching after-hours vendor in the list. "
            "vendor_text should name who else to call (911 or Enbridge Gas North Carolina) "
            "or say that Luis is the only person being dispatched."
        )
    )
    safety_line = SAFETY_LINES.get(safety, "No special safety script. Do not invent one.")
    prompt = f"""You draft messages for Laurel Hill Residential. You cannot send them.

{data.maintenance_rules}

{data.reply_style}

Message ({language}), received {iso(message.received_at)}, unit {message.unit or "unknown"}, via {message.channel}:
From: {message.sender}
{message.body}

Deadline: {when}.
Call {LUIS_NAME} at {LUIS_PHONE}. {vendor_line}
Required safety text for the tenant, when it applies: {safety_line}

Write the tenant reply in {language}. Tell them you are an automated assistant and sign Laurel Hill Residential.
The tenant reply must include the required safety text when one is given.
luis_call_script is what a person reads when calling Luis. It is a draft, not a completed call.
Never quote a vendor's rate. Never blame the tenant.
"""
    try:
        draft = generate_json(prompt, EMERGENCY_SCHEMA)
    except GeminiError as exc:
        output["gemini_called"] = False
        output["needs_human"] = True
        output["review_reason"] = str(exc)
        output["tenant_reply"] = ensure_safety("", safety) or None
        return output

    output["tenant_reply"] = ensure_safety(str(draft.get("tenant_reply") or ""), safety)
    output["luis_call_script"] = str(draft.get("luis_call_script") or "")
    output["vendor_text"] = str(draft.get("vendor_text") or "")
    return output


def _leasing(output, message, deadline, data, language) -> dict:
    units = available_units(data)
    slots = open_slots(data, message.received_at)
    known_units = {unit["unit_id"] for unit in units}
    known_slots = {f"{slot['date']} {slot['start_time']}" for slot in slots}
    output["gemini_called"] = True
    unit_lines = "\n".join(
        f"- {unit['unit_id']} | {unit['property']} | {unit['bedrooms']}br/{unit['bathrooms']}ba | "
        f"${unit['monthly_rent']}/mo | {unit['status']} | available {unit['available_date'] or 'now'} | "
        f"pets: {unit['pet_policy']}"
        for unit in units
    )
    slot_lines = "\n".join(
        f"- {slot['date']} {slot['start_time']} ({slot['day']})" for slot in slots
    ) or "- none"
    prompt = f"""You draft a leasing reply for Laurel Hill Residential. You cannot send it. {JAKE_NAME} ({JAKE_PHONE}) runs every showing. There are no self-guided tours.

{data.leasing_rules}

{data.reply_style}

Available units (do not mention any unit that is not in this list, and do not mention current tenants):
{unit_lines}

Open showing slots at or after this message:
{slot_lines}

Message ({language}), received {iso(message.received_at)}, via {message.channel}:
From: {message.sender}
{message.body}

Reply deadline: {friendly(deadline)}.
Write draft_reply in {language}. Say you are an automated assistant and sign Laurel Hill Residential.
Never promise a unit, a price, or an approval. Only Priya signs leases.
Fair housing: describe the unit and the written policies. Never comment on who lives in a building, whether a neighborhood is safe or quiet, or whether a unit suits families, a religion, a nationality, or a disability. If they ask, refuse that part and answer only the process question.
suggested_units is a list of unit ids copied from the list above.
suggested_slot is one line copied as "YYYY-MM-DD HH:MM", or an empty string.
Set handoff_to_priya true for a sublease, a mid-year takeover in a student building, an assistance animal, or anything Priya must approve. The draft still must not promise an outcome.
"""
    try:
        draft = generate_json(prompt, LEASING_SCHEMA)
    except GeminiError as exc:
        output["gemini_called"] = False
        output["needs_human"] = True
        output["review_reason"] = str(exc)
        return output

    suggested = [unit for unit in draft.get("suggested_units") or [] if unit in known_units]
    slot = str(draft.get("suggested_slot") or "")
    output["tenant_reply"] = str(draft.get("draft_reply") or "")
    output["suggested_units"] = suggested
    output["suggested_slot"] = slot if slot in known_slots else None
    output["handoff_to_priya"] = bool(draft.get("handoff_to_priya"))
    output["handoff_reason"] = str(draft.get("handoff_reason") or "") or None
    if output["handoff_to_priya"]:
        output["priya_summary"] = (
            f"For {PRIYA_NAME}. Leasing handoff. No lease was promised.\n"
            f"Reason: {output['handoff_reason'] or 'needs Priya'}\n"
            f"From: {message.sender} via {message.channel}\n{message.body}"
        )
    return output


def _maintenance(output, message, route, deadline, data, language) -> dict:
    urgent = route == "urgent_maintenance"
    vendor = _select_vendor(data.vendors, message.body, None, emergency=False)
    lockout = _is_lockout(message.body)
    assign = vendor["name"] if vendor and not _luis_handles(message.body) else LUIS_NAME
    if lockout and vendor:
        assign = vendor["name"]
    output["vendor"] = public_vendor(vendor) if assign != LUIS_NAME else None
    output["tenant_reply"] = _maintenance_reply(language, message.unit, deadline, lockout, urgent)
    output["work_order"] = {
        "unit": message.unit or None,
        "priority": "urgent" if urgent else "routine",
        "issue": message.body,
        "assign_to": assign,
        "vendor": output["vendor"],
        "deadline": iso(deadline),
        "tenant_fee": "$75 after-hours lockout fee" if lockout else None,
        "notes": "Do not quote the vendor's rate to the tenant.",
    }
    return output


def _noise(output, message, deadline, language, tickets) -> dict:
    output["tenant_reply"] = _phrase(
        language,
        en=(
            f"This is an automated assistant at Laurel Hill Residential. "
            f"We logged the noise complaint{_unit_clause(message.unit, 'en')} "
            f"and will follow up by {friendly(deadline)}."
        ),
        es=(
            f"Soy un asistente automático de Laurel Hill Residential. "
            f"Registramos la queja de ruido{_unit_clause(message.unit, 'es')} "
            f"y le daremos seguimiento a más tardar el {friendly(deadline)}."
        ),
        it=(
            f"Sono un assistente automatico di Laurel Hill Residential. "
            f"Abbiamo registrato la segnalazione sul rumore{_unit_clause(message.unit, 'it')} "
            f"e la ricontatteremo entro {friendly(deadline)}."
        ),
    )
    if _repeat_noise(tickets, message.unit):
        output["handoff_to_priya"] = True
        output["priya_summary"] = (
            f"For {PRIYA_NAME}. Repeat noise complaint about unit {message.unit}.\n"
            f"From: {message.sender} via {message.channel} at {iso(message.received_at)}\n"
            f"{message.body}"
        )
    return output


def _priya(output, message, classification, deadline) -> dict:
    kind = classification.get("message_type") or "other"
    labels = {
        "rent_payment": "Rent or payment question",
        "legal": "Legal or lease question",
        "esa": "Emotional support or service animal request",
    }
    output["handoff_to_priya"] = True
    output["needs_human"] = True
    output["priya_summary"] = (
        f"For {PRIYA_NAME}. {labels.get(kind, kind)}. No reply was sent to the sender.\n"
        f"Review by {friendly(deadline)}.\n"
        f"From: {message.sender}  Unit: {message.unit or 'unknown'}  "
        f"Channel: {message.channel}  Received: {iso(message.received_at)}\n"
        f"{message.body}"
    )
    return output


def _fraud(output, message) -> dict:
    output["fraud_flag"] = True
    output["needs_human"] = True
    output["handoff_to_priya"] = True
    output["priya_summary"] = (
        f"For {PRIYA_NAME}. Possible fraud. No action taken and no reply sent.\n"
        f"From: {message.sender} via {message.channel} at {iso(message.received_at)}\n"
        f"{message.body}"
    )
    return output


def _mentions(text: str, *words: str) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def _select_vendor(vendors: list[dict], body: str, safety: str | None, emergency: bool) -> dict | None:
    if safety in ("gas", "fire"):
        return None
    text = body.lower()
    trade = None
    if safety == "co" or _mentions(text, "heat", "thermostat", "furnace", "hvac"):
        trade = "hvac"
    elif _mentions(text, "flood", "ceiling") or "coming through" in text:
        trade = "water damage"
    elif _mentions(text, "power", "breaker", "electric"):
        trade = "electrical"
    elif _mentions(text, "lock", "latch") or "locked out" in text:
        trade = "locksmith"
    elif _mentions(text, "ant", "ants", "pest", "roach", "bug"):
        trade = "pest"
    elif _mentions(text, "sewage") or "hot water" in text or "water heater" in text or "no water" in text:
        trade = "plumbing"
    elif _mentions(text, "leak", "plumb", "drain"):
        trade = "plumbing"

    if trade is None:
        return None
    matches = [vendor for vendor in vendors if trade in vendor["trade"].lower()]
    if emergency or _is_after_hours_issue(text):
        after_hours = [vendor for vendor in matches if vendor["after_hours"].strip().lower() == "yes"]
        return after_hours[0] if after_hours else None
    return matches[0] if matches else None


def _luis_handles(body: str) -> bool:
    text = body.lower()
    if _mentions(text, "ant", "ants", "pest", "roach", "lock", "heat", "power", "electric", "flood"):
        return False
    return _mentions(text, "sink", "drip", "disposal", "fridge", "refrigerator", "toilet", "light", "fan", "blind")


def _is_lockout(body: str) -> bool:
    text = body.lower()
    return "locked out" in text or "lockout" in text


def _is_after_hours_issue(text: str) -> bool:
    return any(word in text for word in ("lock", "heat", "power", "flood", "gas", "hot water"))


def _repeat_noise(tickets: dict, unit: str) -> bool:
    if not unit:
        return False
    return any(ticket.get("is_noise") and ticket.get("unit") == unit for ticket in tickets.values())


def _maintenance_reply(language: str, unit: str, deadline: datetime, lockout: bool, urgent: bool) -> str:
    when = friendly(deadline)
    fee = {
        "en": " After-hours lockouts have a $75 fee.",
        "es": " Los cierres fuera de horario tienen un cargo de $75.",
        "it": " Le chiusure fuori orario hanno un costo di $75.",
    }
    extra = fee.get(language, fee["en"]) if lockout else ""
    if urgent:
        return _phrase(
            language,
            en=(
                f"This is an automated assistant at Laurel Hill Residential. "
                f"We logged this{_unit_clause(unit, 'en')} and will have it handled by {when}.{extra}"
            ),
            es=(
                f"Soy un asistente automático de Laurel Hill Residential. "
                f"Registramos el aviso{_unit_clause(unit, 'es')} y lo atenderemos a más tardar el {when}.{extra}"
            ),
            it=(
                f"Sono un assistente automatico di Laurel Hill Residential. "
                f"Abbiamo registrato la segnalazione{_unit_clause(unit, 'it')} "
                f"e la gestiremo entro {when}.{extra}"
            ),
        )
    return _phrase(
        language,
        en=(
            f"This is an automated assistant at Laurel Hill Residential. "
            f"We logged this{_unit_clause(unit, 'en')} and will take care of it by {when}."
        ),
        es=(
            f"Soy un asistente automático de Laurel Hill Residential. "
            f"Registramos el aviso{_unit_clause(unit, 'es')} y lo resolveremos a más tardar el {when}."
        ),
        it=(
            f"Sono un assistente automatico di Laurel Hill Residential. "
            f"Abbiamo registrato la segnalazione{_unit_clause(unit, 'it')} e la risolveremo entro {when}."
        ),
    )


def _unit_clause(unit: str, language: str) -> str:
    if not unit:
        return ""
    if language == "es":
        return f" para la unidad {unit}"
    if language == "it":
        return f" per l'unità {unit}"
    return f" for unit {unit}"


def _phrase(language: str, en: str, es: str, it: str) -> str:
    if language == "es":
        return es
    if language == "it":
        return it
    return en
