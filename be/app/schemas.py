from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    from_ts: Optional[str] = Field(None, description="ISO datetime string")
    to_ts: Optional[str] = Field(None, description="ISO datetime string")
    location_id: Optional[str] = None
    timer_id: Optional[str] = None


class ProductionSummaryItem(BaseModel):
    timerId: Optional[str] = None
    totalTons: float = 0
    avgRunRate: Optional[float] = None
    avgTargetRate: Optional[float] = None
    counts: int = 0


class ProductionSummaryResponse(BaseModel):
    items: List[ProductionSummaryItem]


class DowntimeItem(BaseModel):
    stopReason: str
    totalDurationSec: float


class DowntimeResponse(BaseModel):
    items: List[DowntimeItem]


class CycleTimeItem(BaseModel):
    t: str
    cycleSec: float


class CycleTimesResponse(BaseModel):
    items: List[CycleTimeItem]

