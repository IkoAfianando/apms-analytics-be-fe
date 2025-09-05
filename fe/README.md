Frontend (Next.js + ECharts)

Ringkas: Dashboard visualisasi data APMS menggunakan ECharts.

Persiapan:
- Node.js 18+
- pnpm 8+
- `cp .env.local.example .env.local` lalu sesuaikan `NEXT_PUBLIC_API_BASE`
- `pnpm install`
- `pnpm dev`

Halaman awal (`/`) menampilkan contoh:
- Trend produksi (line chart) dari endpoint `/v1/production/summary`
- Pareto downtime (bar) dari endpoint `/v1/downtime/reasons`
- Distribusi cycle time (scatter) dari endpoint `/v1/cycle-times`

