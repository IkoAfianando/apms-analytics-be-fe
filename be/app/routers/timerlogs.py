from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db

router = APIRouter(prefix="/timerlogs", tags=["Timer Logs"])

@router.get("/line-chart")
def get_timer_logs_line_chart(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    location_id: Optional[str] = Query(None, description="Location ID filter"),
    machine_class_id: Optional[str] = Query(None, description="Machine Class ID filter"),
    stop_reason: Optional[str] = Query(None, description="Stop reason filter"),
    group_by: str = Query("hour", description="Group by: hour, day, week, month"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Get timer logs data for line chart visualization"""
    db = get_db()
    
    # Build query
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    if machine_class_id:
        query["machineClassId"] = machine_class_id
    if stop_reason:
        query["stopReason"] = stop_reason
    
    # Aggregation pipeline
    group_format = {
        "hour": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$createdAt"}},
        "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
        "week": {"$dateToString": {"format": "%Y-W%U", "date": "$createdAt"}},
        "month": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": group_format[group_by],
            "count": {"$sum": 1},
            "totalDuration": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}},
            "avgDuration": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "uniqueTimers": {"$addToSet": "$timerId"}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": limit}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    # Format for ECharts
    return {
        "xAxis": [r["_id"] for r in results],
        "series": [
            {
                "name": "Count",
                "type": "line",
                "data": [r["count"] for r in results]
            },
            {
                "name": "Avg Duration (ms)",
                "type": "line",
                "data": [r["avgDuration"] or 0 for r in results]
            },
            {
                "name": "Unique Timers",
                "type": "line",
                "data": [len(r["uniqueTimers"]) for r in results]
            }
        ]
    }

@router.get("/stacked-area")
def get_timer_logs_stacked_area(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("day", description="Group by: hour, day, week"),
    stack_by: str = Query("stopReason", description="Stack by: stopReason, locationId, machineClassId")
):
    """Get timer logs data for stacked area chart"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    group_format = {
        "hour": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$createdAt"}},
        "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
        "week": {"$dateToString": {"format": "%Y-W%U", "date": "$createdAt"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "date": group_format[group_by],
                "category": f"${stack_by}"
            },
            "count": {"$sum": 1},
            "totalDuration": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}}
        }},
        {"$sort": {"_id.date": 1, "_id.category": 1}}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    # Organize data for stacked chart
    dates = sorted(list(set([r["_id"]["date"] for r in results])))
    categories = sorted(list(set([r["_id"]["category"] for r in results if r["_id"]["category"]])))
    
    series_data = {}
    for category in categories:
        series_data[category] = []
        for date in dates:
            count = next((r["count"] for r in results if r["_id"]["date"] == date and r["_id"]["category"] == category), 0)
            series_data[category].append(count)
    
    return {
        "xAxis": dates,
        "series": [
            {
                "name": category,
                "type": "area",
                "stack": "total",
                "data": series_data[category]
            }
            for category in categories
        ]
    }

@router.get("/bar-chart")
def get_timer_logs_bar_chart(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("stopReason", description="Group by: stopReason, locationId, machineClassId, operator"),
    top_n: int = Query(20, description="Top N items to show")
):
    """Get timer logs data for bar chart"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": f"${group_by}",
            "count": {"$sum": 1},
            "totalDuration": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}},
            "avgDuration": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "uniqueTimers": {"$addToSet": "$timerId"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": top_n}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    return {
        "xAxis": [r["_id"] or "Unknown" for r in results],
        "series": [
            {
                "name": "Count",
                "type": "bar",
                "data": [r["count"] for r in results]
            },
            {
                "name": "Avg Duration (ms)",
                "type": "bar",
                "data": [r["avgDuration"] or 0 for r in results]
            },
            {
                "name": "Unique Timers",
                "type": "bar",
                "data": [len(r["uniqueTimers"]) for r in results]
            }
        ]
    }

@router.get("/heatmap")
def get_timer_logs_heatmap(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    x_axis: str = Query("hour", description="X-axis: hour, dayOfWeek, day"),
    y_axis: str = Query("locationId", description="Y-axis: locationId, machineClassId, stopReason")
):
    """Get timer logs data for heatmap"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    x_axis_formats = {
        "hour": {"$hour": "$createdAt"},
        "dayOfWeek": {"$dayOfWeek": "$createdAt"},
        "day": {"$dayOfMonth": "$createdAt"}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "x": x_axis_formats[x_axis],
                "y": f"${y_axis}"
            },
            "count": {"$sum": 1}
        }}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    # Format for ECharts heatmap
    data = []
    for r in results:
        if r["_id"]["x"] is not None and r["_id"]["y"] is not None:
            data.append([r["_id"]["x"], r["_id"]["y"], r["count"]])
    
    return {
        "data": data,
        "xAxis": x_axis,
        "yAxis": y_axis
    }

@router.get("/scatter")
def get_timer_logs_scatter(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    x_field: str = Query("createdAt", description="X-axis field"),
    y_field: str = Query("duration", description="Y-axis field"),
    color_by: Optional[str] = Query("stopReason", description="Color by field"),
    limit: int = Query(1000)
):
    """Get timer logs data for scatter plot"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": query},
        {"$addFields": {
            "duration": {"$subtract": ["$endedAt", "$createdAt"]}
        }},
        {"$limit": limit}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    # Format for scatter plot
    data = []
    for r in results:
        x_val = r.get(x_field)
        y_val = r.get(y_field)
        if x_val is not None and y_val is not None:
            point = [x_val, y_val]
            if color_by and r.get(color_by):
                point.append(r[color_by])
            data.append(point)
    
    return {
        "data": data,
        "xField": x_field,
        "yField": y_field,
        "colorBy": color_by
    }

@router.get("/pie-chart")
def get_timer_logs_pie_chart(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("stopReason", description="Group by field"),
    top_n: int = Query(10)
):
    """Get timer logs data for pie chart"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": f"${group_by}",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": top_n}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    return {
        "data": [
            {
                "name": r["_id"] or "Unknown",
                "value": r["count"]
            }
            for r in results
        ]
    }

@router.get("/gauge")
def get_timer_logs_gauge(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    metric: str = Query("efficiency", description="Metric to show: efficiency, utilization, avgDuration")
):
    """Get timer logs data for gauge chart"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "totalCount": {"$sum": 1},
            "productiveCount": {"$sum": {"$cond": [{"$eq": ["$stopReason", "Unit Created"]}, 1, 0]}},
            "avgDuration": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "totalDuration": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}}
        }}
    ]
    
    result = list(db.timerlogs.aggregate(pipeline))
    
    if not result:
        return {"value": 0, "max": 100}
    
    data = result[0]
    
    if metric == "efficiency":
        value = (data["productiveCount"] / data["totalCount"]) * 100 if data["totalCount"] > 0 else 0
        return {"value": round(value, 2), "max": 100, "unit": "%"}
    elif metric == "utilization":
        # Assuming 8 hours as full utilization
        full_day_ms = 8 * 60 * 60 * 1000
        value = min((data["avgDuration"] / full_day_ms) * 100, 100) if data["avgDuration"] else 0
        return {"value": round(value, 2), "max": 100, "unit": "%"}
    else:  # avgDuration
        value = data["avgDuration"] / (60 * 1000) if data["avgDuration"] else 0  # Convert to minutes
        return {"value": round(value, 2), "max": 480, "unit": "min"}  # Max 8 hours

@router.get("/stats")
def get_timer_logs_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get overall timer logs statistics"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "totalLogs": {"$sum": 1},
            "uniqueTimers": {"$addToSet": "$timerId"},
            "uniqueLocations": {"$addToSet": "$locationId"},
            "uniqueMachines": {"$addToSet": "$machineId"},
            "avgDuration": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "maxDuration": {"$max": {"$subtract": ["$endedAt", "$createdAt"]}},
            "minDuration": {"$min": {"$subtract": ["$endedAt", "$createdAt"]}},
            "totalDuration": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}}
        }}
    ]
    
    result = list(db.timerlogs.aggregate(pipeline))
    
    if not result:
        return {
            "totalLogs": 0,
            "uniqueTimers": 0,
            "uniqueLocations": 0,
            "uniqueMachines": 0,
            "avgDuration": 0,
            "maxDuration": 0,
            "minDuration": 0,
            "totalDuration": 0
        }
    
    data = result[0]
    return {
        "totalLogs": data["totalLogs"],
        "uniqueTimers": len(data["uniqueTimers"]),
        "uniqueLocations": len(data["uniqueLocations"]),
        "uniqueMachines": len(data["uniqueMachines"]),
        "avgDuration": data["avgDuration"] or 0,
        "maxDuration": data["maxDuration"] or 0,
        "minDuration": data["minDuration"] or 0,
        "totalDuration": data["totalDuration"] or 0
    }
