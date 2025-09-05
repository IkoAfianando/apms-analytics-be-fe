from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body

from app.db import get_db

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _time_key(format: str, field: str) -> Dict[str, Any]:
    return {"$dateToString": {"format": format, "date": f"${field}"}}


@router.post("/query")
def analytics_query(
    payload: Dict[str, Any] = Body(
        ..., example={
            "collection": "timerlogs",
            "filters": {"locationId": None, "from": None, "to": None, "timeField": "createdAt"},
            "group": {"timeBucket": "day", "timeField": "createdAt", "by": ["stopReason"]},
            "metrics": [{"op": "sum", "field": "durationSec", "as": "duration"}],
            "limit": 200,
            "sort": {"by": "duration", "order": -1},
        }
    ),
):
    db = get_db()
    collection = payload.get("collection")
    filters = payload.get("filters", {}) or {}
    group = payload.get("group", {}) or {}
    metrics = payload.get("metrics", []) or []
    limit = int(payload.get("limit", 200) or 200)
    sort = payload.get("sort") or {}

    coll = db[collection]

    match: Dict[str, Any] = {}
    # generic equality filters (non-empty)
    for k, v in filters.items():
        if k in ("from", "to", "timeField"):
            continue
        if v is not None and v != "":
            match[k] = v

    # time window
    time_field = filters.get("timeField") or group.get("timeField") or "createdAt"
    dt_from = _parse_dt(filters.get("from"))
    dt_to = _parse_dt(filters.get("to"))
    if dt_from or dt_to:
        match[time_field] = {}
        if dt_from:
            match[time_field]["$gte"] = dt_from
        if dt_to:
            match[time_field]["$lte"] = dt_to

    pipeline: List[Dict[str, Any]] = []

    # Precompute durationSec if fields exist
    if collection in ("timerlogs", "timerloghistories", "controllertimers"):
        pipeline.append(
            {
                "$addFields": {
                    "__durationSec": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$endedAt", None]},
                                    {"$ne": [f"${time_field}", None]},
                                ]
                            },
                            {"$divide": [{"$subtract": ["$endedAt", f"${time_field}"]}, 1000]},
                            None,
                        ]
                    }
                }
            }
        )

    if match:
        pipeline.append({"$match": match})

    # Build group key
    group_id: Dict[str, Any] = {}
    cats: List[str] = []
    time_bucket = (group.get("timeBucket") or "").lower()
    time_field = group.get("timeField") or time_field
    if time_bucket:
        if time_bucket == "day":
            group_id["t"] = _time_key("%Y-%m-%d", time_field)
        elif time_bucket == "month":
            group_id["t"] = _time_key("%Y-%m", time_field)
        elif time_bucket == "hour":
            group_id["t"] = _time_key("%Y-%m-%d %H:00", time_field)
    for b in group.get("by", []) or []:
        group_id[b] = f"${b}"
        cats.append(b)

    # Build accumulators
    accum: Dict[str, Any] = {}
    for m in metrics:
        op = (m.get("op") or "").lower()
        field = m.get("field")
        out = m.get("as") or f"{op}_{field}"
        src = f"${field}"
        if field == "durationSec":
            src = "$__durationSec"
        if op == "sum":
            accum[out] = {"$sum": {"$ifNull": [src, 0]}}
        elif op == "avg":
            accum[out] = {"$avg": src}
        elif op == "min":
            accum[out] = {"$min": src}
        elif op == "max":
            accum[out] = {"$max": src}
        elif op == "count":
            accum[out] = {"$sum": 1}

    if group_id:
        pipeline.append({"$group": {"_id": group_id, **accum}})
    elif accum:
        pipeline.append({"$group": {"_id": None, **accum}})

    if sort and sort.get("by"):
        pipeline.append({"$sort": {sort["by"]: int(sort.get("order", -1))}})
    elif time_bucket:
        pipeline.append({"$sort": {"_id.t": 1}})

    if limit:
        pipeline.append({"$limit": limit})

    rows = list(coll.aggregate(pipeline))

    # normalize result: return dataset-like and series inference
    columns = ["t", *cats, *[m.get("as") or f"{m.get('op')}_{m.get('field')}" for m in metrics]]
    data_rows: List[List[Any]] = []
    for r in rows:
        rid = r.get("_id") or {}
        row = [rid.get("t")] if "t" in columns else []
        for c in cats:
            row.append(rid.get(c))
        for m in metrics:
            key = m.get("as") or f"{m.get('op')}_{m.get('field')}"
            val = r.get(key)
            if isinstance(val, (int, float)):
                row.append(float(val))
            else:
                row.append(val)
        data_rows.append(row)

    return {"columns": columns, "rows": data_rows, "raw": rows}


@router.get("/timerlogs/heatmap/daily-counts")
def timerlogs_daily_counts():
    db = get_db()
    pipeline = [
        {"$addFields": {"day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}}}},
        {"$group": {"_id": "$day", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    rows = list(db["timerlogs"].aggregate(pipeline))
    return {"items": [{"day": r["_id"], "count": int(r["count"]) } for r in rows]}


@router.get("/timerlogs/histogram")
def timerlogs_histogram(field: str = "cycle", buckets: int = 20):
    db = get_db()
    pipeline = [
        {"$match": {field: {"$ne": None}}},
        {"$bucketAuto": {"groupBy": f"${field}", "buckets": buckets}},
        {"$project": {"_id": 0, "min": "$min", "max": "$max", "count": "$count"}},
    ]
    rows = list(db["timerlogs"].aggregate(pipeline))
    return {"items": rows}


@router.get("/timerlogs/pareto/stop-reasons")
def timerlogs_pareto_stop_reason(limit: int = 20):
    db = get_db()
    pipeline = [
        {"$match": {"stopReason": {"$ne": None}}},
        {"$group": {"_id": "$stopReason", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
        {"$limit": limit},
    ]
    rows = list(db["timerlogs"].aggregate(pipeline))
    return {"items": [{"stopReason": r["_id"], "count": int(r["n"]) } for r in rows]}

