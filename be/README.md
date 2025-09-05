Backend (FastAPI + MongoDB)

Ringkas: API untuk aggregasi data APMS dari MongoDB (dump di folder `dump/apms`).

Jalankan lokal:
- Python 3.10+
- `pip install -r requirements.txt`
- Salin `.env.example` ke `.env` lalu sesuaikan bila perlu
- `uvicorn app.main:app --reload --port 8000`

Env vars:
- `MONGODB_URI` default `mongodb://localhost:27018` (mengikuti docker-compose di repo ini)
- `MONGODB_DB` default `apms`

Endpoint awal:
- `GET /health` cek kesehatan
- `GET /v1/production/summary` produksi agregat (berdasar `counts`)
- `GET /v1/downtime/reasons` durasi downtime per `stopReason` (berdasar `timerlogs`)
- `GET /v1/cycle-times` daftar cycle time (berdasar `cycletimers` atau `timerlogs.cycle` bila ada)

Catatan: Query menggunakan index yang tersedia di dump metadata untuk efisiensi (mis. `timerId`, `locationId`, `createdAt/endedAt`, `stopReason`).

