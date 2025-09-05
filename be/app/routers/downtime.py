from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_db
from app.schemas import DowntimeResponse

router = APIRouter(prefix="/v1/downtime", tags=["downtime"])


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@router.get("/reasons", response_model=DowntimeResponse)
def downtime_reasons(
    location_id: Optional[str] = Query(None),
    from_ts: Optional[str] = Query(None, description="ISO datetime"),
    to_ts: Optional[str] = Query(None, description="ISO datetime"),
):
    db = get_db()
    match: dict = {}
    if location_id:
        match["locationId"] = location_id

    dt_from = _parse_dt(from_ts)
    dt_to = _parse_dt(to_ts)
    # timerlogs punya index createdAt_*, endedAt_* dan stopReason
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
        {"$match": {"stopReason": {"$ne": None}}},
        {"$match": {"endedAt": {"$type": "date"}, "createdAt": {"$type": "date"}}},  # Only process datetime objects
        {
            "$addFields": {
                "durationSec": {
                    "$divide": [
                        {"$subtract": ["$endedAt", "$createdAt"]},
                        1000,
                    ]
                }
            }
        },
        {"$group": {"_id": "$stopReason", "totalDurationSec": {"$sum": "$durationSec"}}},
        {"$sort": {"totalDurationSec": -1}},
    ]

    try:
        agg = list(db["timerlogs"].aggregate(pipeline))
    except Exception as e:
        # Return empty result if aggregation fails
        agg = []
    
    items = []
    for a in agg:
        stop_reason = a.get("_id", "Unknown")
        # Handle case where stopReason might be a list
        if isinstance(stop_reason, list):
            stop_reason = stop_reason[0] if stop_reason else "Unknown"
        elif stop_reason is None:
            stop_reason = "Unknown"
        
        items.append({
            "stopReason": str(stop_reason), 
            "totalDurationSec": float(a.get("totalDurationSec", 0) or 0)
        })
    
    return {"items": items}

