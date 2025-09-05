from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_db
from app.schemas import CycleTimesResponse

router = APIRouter(prefix="/v1", tags=["cycles"])


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@router.get("/cycle-times", response_model=CycleTimesResponse)
def cycle_times(
    timer_id: Optional[str] = Query(None),
    from_ts: Optional[str] = Query(None, description="ISO datetime"),
    to_ts: Optional[str] = Query(None, description="ISO datetime"),
    limit: int = Query(200, le=5000),
):
    db = get_db()
    # Prefer "cycletimers" collection (ada index timerId, clientStartedAt, endAt)
    match: dict = {}
    if timer_id:
        match["timerId"] = timer_id
    dt_from = _parse_dt(from_ts)
    dt_to = _parse_dt(to_ts)
    if dt_from or dt_to:
        match["clientStartedAt"] = {}
        if dt_from:
            match["clientStartedAt"]["$gte"] = dt_from
        if dt_to:
            match["clientStartedAt"]["$lte"] = dt_to

    cursor = (
        db["cycletimers"]
        .find(match, {"clientStartedAt": 1, "endAt": 1})
        .sort("clientStartedAt", 1)
        .limit(limit)
    )

    items = []
    for doc in cursor:
        st = doc.get("clientStartedAt")
        en = doc.get("endAt")
        if st and en:
            cycle = (en - st).total_seconds()
            items.append({"t": st.isoformat(), "cycleSec": float(cycle)})

    # Fallback: jika kosong, coba ambil dari timerlogs.cycle
    if not items:
        match_logs: dict = {}
        if timer_id:
            match_logs["timerId"] = timer_id
        if dt_from or dt_to:
            match_logs["createdAt"] = {}
            if dt_from:
                match_logs["createdAt"]["$gte"] = dt_from
            if dt_to:
                match_logs["createdAt"]["$lte"] = dt_to
        cursor2 = (
            db["timerlogs"]
            .find(match_logs, {"createdAt": 1, "cycle": 1})
            .sort("createdAt", 1)
            .limit(limit)
        )
        for doc in cursor2:
            if doc.get("cycle") is not None and doc.get("createdAt") is not None:
                created_at = doc["createdAt"]
                # Handle both datetime objects and strings
                if isinstance(created_at, str):
                    time_str = created_at
                else:
                    time_str = created_at.isoformat()
                items.append({"t": time_str, "cycleSec": float(doc["cycle"])})

    return {"items": items}

