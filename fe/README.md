Frontend (Next.js + ECharts)

Summary: APMS data visualization dashboard using ECharts.

Setup:
- Node.js 18+
- pnpm 8+
- `cp .env.local.example .env.local` then adjust `NEXT_PUBLIC_API_BASE`
- `pnpm install`
- `pnpm dev`

Home page (`/`) displays examples:
- Production trends (line chart) from endpoint `/v1/production/summary`
- Downtime Pareto (bar) from endpoint `/v1/downtime/reasons`
- Cycle time distribution (scatter) from endpoint `/v1/cycle-times`

