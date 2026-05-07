# Nava — AI Triage System

AI-powered inbox for residential property managers. Replaces Excel triaging with a priority queue driven by Claude.

## Quick Start

```bash
# 1. Copy env and add your Anthropic key
cp .env.example .env
# edit .env — set ANTHROPIC_API_KEY

# 2. Start everything
docker-compose up --build

# 3. Load demo data (in a new terminal)
docker-compose exec backend python /app/../scripts/seed_demo.py
# or locally: DATABASE_URL=postgresql+asyncpg://nava:nava_dev@localhost:5432/nava python scripts/seed_demo.py

# 4. Open the app
open http://localhost:3000
```

## Test the ingest endpoint

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"manual","sender_name":"Test","subject":"Awaria windy","body_raw":"Winda nie działa od rana w budynku A."}'
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ingest` | Ingest a message → AI triage → create ticket |
| GET | `/api/tickets` | List tickets (filters: status, priority, category) |
| GET | `/api/tickets/{id}` | Get single ticket |
| PATCH | `/api/tickets/{id}` | Update status / notes / override priority |
| POST | `/api/tickets/{id}/resolve` | Mark resolved |
| POST | `/api/tickets/{id}/dismiss` | Dismiss |
| GET | `/health` | Backend health check |

## Phase 1 Checklist

- [x] `docker-compose up` starts everything
- [x] `POST /api/ingest` triages via Claude and stores ticket
- [x] `GET /api/tickets` returns sorted, filtered list
- [x] Frontend shows tickets with priority color coding
- [x] Admin can open ticket, edit AI draft, mark as resolved
- [x] Demo seed data: `python scripts/seed_demo.py`
