from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.production import router as production_router
from app.routers.runrate import router as runrate_router
from app.routers.downtime import router as downtime_router
from app.routers.cycles import router as cycles_router
from app.routers.utilization import router as utilization_router
from app.routers.refs import router as refs_router
from app.routers.analytics import router as analytics_router
from app.routers.simple_timerlogs import router as simple_timerlogs_router
from app.routers.simple_dashboard import router as simple_dashboard_router
from app.routers.advanced_charts import router as advanced_charts_router
app = FastAPI(title="APMS Analytics API", version="1.0.1")

# Allow local FE dev by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


# Original routers
app.include_router(production_router)
app.include_router(runrate_router)
app.include_router(downtime_router)
app.include_router(cycles_router)
app.include_router(utilization_router)
app.include_router(refs_router)
app.include_router(analytics_router)

# New comprehensive dashboard routers
app.include_router(simple_timerlogs_router)
app.include_router(simple_dashboard_router)
app.include_router(advanced_charts_router)
