Backend (FastAPI + MongoDB)

Summary: API for aggregating APMS data from MongoDB (dump in `dump/apms` folder).

Run locally:
- Python 3.10+
- `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and adjust if needed
- `uvicorn app.main:app --reload --port 8000`

Env vars:
- `MONGODB_URI` default `mongodb://localhost:27018` (follows docker-compose in this repo)
- `MONGODB_DB` default `apms`

Initial endpoints:
- `GET /health` health check
- `GET /v1/production/summary` production aggregates (based on `counts`)
- `GET /v1/downtime/reasons` downtime duration per `stopReason` (based on `timerlogs`)
- `GET /v1/cycle-times` list of cycle times (based on `cycletimers` or `timerlogs.cycle` if available)

Note: Queries use available indexes in dump metadata for efficiency (e.g., `timerId`, `locationId`, `createdAt/endedAt`, `stopReason`).

