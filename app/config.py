"""Paths, keys, and the routing cutoffs from the scope."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = Path(os.environ.get("DATA_DIR") or (ROOT.parent / "data" / "experienced"))

JEV_MODEL = os.environ.get("JEV_MODEL", "typesafe/jev-1.13")
JEV_URL = "https://openrouter.ai/api/alpha/decisions"
# 2.5-flash is rejected for new API keys. 3.8-flash is the model Google tells those keys to use.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

CONFIDENCE_CUTOFF = 0.6
FRAUD_CUTOFF = 0.5

LUIS_NAME = "Luis Ortega"
LUIS_PHONE = "919-555-0100"
JAKE_NAME = "Jake Ellis"
JAKE_PHONE = "919-555-0102"
PRIYA_NAME = "Priya Raman"
PRIYA_PHONE = "919-555-0101"

# Scenario clock from company.md: Monday, October 5, 2026, 7:00 AM.
SCENARIO_NOW = datetime(2026, 10, 5, 7, 0)
MONDAY_CUTOFF = SCENARIO_NOW


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def friendly(dt: datetime) -> str:
    return dt.strftime("%A, %b %-d, %-I:%M %p")
