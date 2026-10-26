# LeadForge

AI lead triage for contact forms. A website form posts a lead to this Python service, which scores it with an LLM (rule-based fallback if the LLM is unavailable), stores it in a database, and syncs real leads to HubSpot.

```
WordPress form  -->  POST /leads  -->  score (LLM or rules)  -->  database  -->  HubSpot
```

## What it does

- Receives a lead (name, email, phone, message) and validates it.
- Scores buying intent 0-10, flags spam, extracts intent, writes a one-line summary and a suggested reply.
- Never loses a lead: if the LLM call fails or returns bad JSON, the rule-based scorer takes over (`scored_by` records which one ran).
- Stores everything in PostgreSQL (SQLite for local dev).
- Syncs non-spam leads to HubSpot in a background task. A CRM outage never blocks intake.
- Protects the API with a shared `X-API-Key` header for the WordPress plugin.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # optional: add ANTHROPIC_API_KEY, HUBSPOT_TOKEN
uvicorn app.main:app --reload
```

Interactive docs: http://localhost:8000/docs

```bash
curl -X POST http://localhost:8000/leads -H "Content-Type: application/json" -d '{
  "name": "Asha Verma",
  "email": "asha@example.com",
  "message": "I want to enroll my daughter in the Python course next month. What is the fee?"
}'
```

With Docker and PostgreSQL: `docker compose up --build`.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/leads` | Submit and score a lead |
| GET | `/leads?min_score=6&include_spam=false` | List leads, best first |
| GET | `/leads/{id}` | One lead |
| GET | `/health` | Health check |

## Configuration

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite (default) or PostgreSQL URL |
| `LEADFORGE_API_KEY` | Shared secret for `X-API-Key`; empty disables auth (local only) |
| `ANTHROPIC_API_KEY` | Enables LLM scoring; empty uses the rule-based scorer |
| `LLM_MODEL` | Model name, default `claude-sonnet-5-5` |
| `HUBSPOT_TOKEN` | HubSpot private-app token; empty skips CRM sync |

## Design notes

- **Untrusted input:** the lead message is user text, so the LLM prompt tells the model to ignore instructions inside it, and the model's JSON is validated with Pydantic (score must be an integer 0-10) before it is stored.
- **Graceful degradation:** LLM and CRM failures are logged and recorded on the lead, never raised to the visitor.
- **Tests:** 23 pytest tests cover scoring, the API, auth, and the LLM and HubSpot clients (mocked with `httpx.MockTransport`, so no network is needed). CI runs flake8, pytest and a Docker build.

## Known simplifications

- Tables are created with `create_all`; a production setup would use Alembic migrations.
- CRM sync runs as a FastAPI background task; a queue (Celery/Redis) would add retries.
- One HubSpot contact per lead; no deal or note creation yet.

## Roadmap

- [ ] WordPress plugin that posts form submissions here
- [ ] Slack or email alert for hot leads (score 8+)
- [ ] Small dashboard page for the lead list
- [ ] Deploy to a cloud server with a public URL
