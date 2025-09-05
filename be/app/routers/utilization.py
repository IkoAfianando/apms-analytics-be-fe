from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_db

router = APIRouter(prefix="/v1/utilization", tags=["utilization"])


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@router.get("/daily")
def utilization_daily(
    location_id: Optional[str] = Query(None),
    from_ts: Optional[str] = Query(None),
    to_ts: Optional[str] = Query(None),
):
    db = get_db()
    match: dict = {}
    if location_id:
        match["locationId"] = location_id
    dt_from = _parse_dt(from_ts)
    dt_to = _parse_dt(to_ts)
    time_or = []
    if dt_from:
        time_or.append({"createdAt": {"$gte": dt_from}})
        time_or.append({"endedAt": {"$gte": dt_from}})
    if dt_to:
        time_or.append({"createdAt": {"$lte": dt_to}})
        time_or.append({"endedAt": {"$lte": dt_to}})
    if time_or:
        match["$or"] = time_or

    # Simplified pipeline to avoid type mismatch issues
    pipeline = [
        {"$match": match},
        {"$match": {"endedAt": {"$ne": None}, "createdAt": {"$ne": None}}},
        {"$match": {"endedAt": {"$type": "date"}, "createdAt": {"$type": "date"}}},  # Only process datetime objects
        {
            "$addFields": {
                "durationSec": {
                    "$divide": [
                        {"$subtract": ["$endedAt", "$createdAt"]},
                        1000,
                    ]
                },
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "isDown": {
                    "$cond": [
                        {"$and": [
                            {"$ne": ["$stopReason", None]},
                            {"$ne": ["$stopReason", "Unit Created"]}
                        ]},
                        True,
                        False,
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$day",
                "runSec": {"$sum": {"$cond": [{"$eq": ["$isDown", False]}, "$durationSec", 0]}},
                "stopSec": {"$sum": {"$cond": [{"$eq": ["$isDown", True]}, "$durationSec", 0]}},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    try:
        agg = list(db["timerlogs"].aggregate(pipeline))
    except Exception as e:
        # Return empty result if aggregation fails
        agg = []
    items = []
    for a in agg:
        run = float(a.get("runSec", 0) or 0)
        stop = float(a.get("stopSec", 0) or 0)
        total = run + stop if (run + stop) > 0 else 1
        items.append({
            "day": a.get("_id"),
            "runSec": run,
            "stopSec": stop,
            "runPct": round(run / total * 100, 2),
            "stopPct": round(stop / total * 100, 2),
        })
    return {"items": items}

