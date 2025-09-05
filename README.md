# APMS Lite Demo

A lightweight demonstration of an Advanced Production Monitoring System (APMS) with a FastAPI backend and Next.js frontend for data visualization.

## Overview

This project provides a simple yet comprehensive dashboard for monitoring production metrics, downtime analysis, cycle times, and utilization rates. It aggregates data from MongoDB and visualizes it using ECharts.

## Architecture

- **Backend (be/)**: FastAPI application serving REST APIs for data aggregation from MongoDB.
- **Frontend (fe/)**: Next.js application with ECharts for interactive dashboards.

## Features

- Production summary and trends
- Downtime analysis by reason
- Cycle time distribution
- Daily utilization percentages
- Run rate time series
- Location-based filtering

## Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or remote)
- pnpm (for frontend package management)

## Setup

### Backend

1. Navigate to the `be/` directory:
   ```bash
   cd be
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env` and configure as needed.
   - Default MongoDB URI: `mongodb://localhost:27018`
   - Default database: `apms`

4. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend

1. Navigate to the `fe/` directory:
   ```bash
   cd fe
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Set up environment variables:
   - Copy `.env.local.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE` to the backend URL (default: `http://localhost:8000`).

4. Run the development server:
   ```bash
   pnpm dev
   ```

## API Endpoints

- `GET /health` - Health check
- `GET /v1/production/summary` - Production aggregates
- `GET /v1/downtime/reasons` - Downtime by reason
- `GET /v1/cycle-times` - Cycle time data
- `GET /v1/utilization/daily` - Daily utilization
- `GET /v1/production/runrate-timeseries` - Run rate time series
- `GET /v1/refs/basic` - Reference data (locations, machine classes)

## Docker

Dockerfiles are provided for both backend and frontend. You can build and run using Docker Compose (if configured).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
