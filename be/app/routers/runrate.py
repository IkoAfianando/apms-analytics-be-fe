from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_db

router = APIRouter(prefix="/v1/production", tags=["production"])


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@router.get("/runrate-timeseries")
def runrate_timeseries(
    timer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    from_ts: Optional[str] = Query(None),
    to_ts: Optional[str] = Query(None),
):
    db = get_db()
    match: dict = {}
    if timer_id:
        match["timerId"] = timer_id
    if location_id:
        match["locationId"] = location_id
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
            "$addFields": {
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$startAt"}},
            }
        },
        {
            "$group": {
                "_id": "$day",
                "avgRunRate": {"$avg": "$runRate"},
                "avgTargetRate": {"$avg": "$targetRate"},
                "n": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    agg = list(db["counts"].aggregate(pipeline))
    items = [
        {
            "day": a.get("_id"),
            "runRate": float(a.get("avgRunRate") or 0),
            "targetRate": float(a.get("avgTargetRate") or 0),
            "n": int(a.get("n") or 0),
        }
        for a in agg
    ]
    return {"items": items}

