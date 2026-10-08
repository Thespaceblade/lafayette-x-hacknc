# Lafayette x HackNC

One-hour hackathon project for Lafayette x HackNC.

## Request inbox (front-end)

```
python server.py        # then open http://localhost:8000
```

- Lists every request with a filter by problem type (emergency, urgent/routine repair, leasing, rent, noise, legal, ESA, possible fraud), by property, and by overdue as of Mon Oct 5, 7:00 AM.
- **+ New request** opens a form; it posts to `POST /api/requests` and shows safety instructions right away for gas, CO, and fire.
- Drop the track's `messages.csv` into `data/` and the server loads it instead of the built-in sample requests.
- Each request's category comes from the server's `category` field when present; otherwise `frontend/app.js` falls back to a keyword classifier (`classify()`). Swap in the real classifier server-side.
