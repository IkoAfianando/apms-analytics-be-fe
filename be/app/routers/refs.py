from __future__ import annotations

from fastapi import APIRouter

from app.db import get_db

router = APIRouter(prefix="/v1/refs", tags=["refs"])


@router.get("/basic")
def refs_basic():
    db = get_db()
    locs = [
        {"_id": str(d.get("_id")), "name": d.get("name")}
        for d in db["locations"].find({}, {"name": 1}).sort("name", 1)
    ]
    mcs = [
        {"_id": str(d.get("_id")), "name": d.get("name")}
        for d in db["machineclasses"].find({}, {"name": 1}).sort("name", 1)
    ]
    return {"locations": locs, "machineclasses": mcs}

