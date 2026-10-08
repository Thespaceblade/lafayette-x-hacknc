# Lafayette x HackNC

One-hour hackathon project for Lafayette x HackNC.

## Request inbox

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --port 8000
```

Open http://localhost:8000. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` and `OPENROUTER_API_KEY`. Track files load from `../data/experienced`.

Jev classifies every message. Gemini writes a draft only for emergencies and leasing. Paste-ready pitch messages are in `DEMO.md`.
