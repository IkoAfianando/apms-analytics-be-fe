from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_db
from app.schemas import ProductionSummaryResponse

router = APIRouter(prefix="/v1/production", tags=["production"])


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@router.get("/summary", response_model=ProductionSummaryResponse)
def production_summary(
    location_id: Optional[str] = Query(None),
    from_ts: Optional[str] = Query(None, description="ISO datetime"),
    to_ts: Optional[str] = Query(None, description="ISO datetime"),
):
    db = get_db()
    match: dict = {}
    if location_id:
        match["locationId"] = location_id
    # counts memiliki index: startAt_1, startAt_1_timerId_1
    dt_from = _parse_dt(from_ts)
    dt_to = _parse_dt(to_ts)
    if dt_from or dt_to:
        match["startAt"] = {}
        if dt_from:
            match["startAt"]["$gte"] = dt_from
        if dt_to:
            match["startAt"]["$lte"] = dt_to

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$timerId",
                "totalTons": {"$sum": {"$ifNull": ["$tons", 0]}},
                "avgRunRate": {"$avg": "$runRate"},
                "avgTargetRate": {"$avg": "$targetRate"},
                "counts": {"$sum": 1},
            }
        },
        {"$sort": {"totalTons": -1}},
    ]

    agg = list(db["counts"].aggregate(pipeline))
    items = [
        {
            "timerId": str(a.get("_id")) if a.get("_id") else None,
            "totalTons": float(a.get("totalTons", 0) or 0),
            "avgRunRate": a.get("avgRunRate"),
            "avgTargetRate": a.get("avgTargetRate"),
            "counts": int(a.get("counts", 0) or 0),
        }
        for a in agg
    ]
    return {"items": items}

