"""Gemini writes JSON drafts. It never sends a message or places a call."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_URL


class GeminiError(RuntimeError):
    pass


def generate_json(prompt: str, schema: dict) -> dict:
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY is not set")

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise GeminiError(f"Gemini HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    parts = (
        body.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        reason = body.get("promptFeedback") or body.get("error") or "empty response"
        raise GeminiError(f"Gemini returned no text: {reason}")
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GeminiError(f"Gemini returned invalid JSON: {text[:300]}") from exc
    if not isinstance(parsed, dict):
        raise GeminiError("Gemini JSON was not an object")
    return parsed
