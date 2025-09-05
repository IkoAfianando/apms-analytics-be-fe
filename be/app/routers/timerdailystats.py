from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db

router = APIRouter(prefix="/timerdailystats", tags=["Timer Daily Stats"])

@router.get("/line-chart")
def get_daily_stats_line_chart(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    machine_class_id: Optional[str] = Query(None),
    group_by: str = Query("day", description="Group by: day, week, month"),
    limit: int = Query(365)
):
    """Get daily stats data for line chart visualization"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    if machine_class_id:
        query["machineClassId"] = machine_class_id
    
    group_format = {
        "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
        "week": {"$dateToString": {"format": "%Y-W%U", "date": "$date"}},
        "month": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": group_format[group_by],
            "totalProduced": {"$sum": "$totalProduced"},
            "totalDowntime": {"$sum": "$totalDowntime"},
            "totalRuntime": {"$sum": "$totalRuntime"},
            "efficiency": {"$avg": "$efficiency"},
            "oee": {"$avg": "$oee"},
            "availability": {"$avg": "$availability"},
            "performance": {"$avg": "$performance"},
            "quality": {"$avg": "$quality"}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": limit}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    return {
        "xAxis": [r["_id"] for r in results],
        "series": [
            {
                "name": "Total Produced",
                "type": "line",
                "data": [r["totalProduced"] or 0 for r in results]
            },
            {
                "name": "Efficiency %",
                "type": "line",
                "yAxisIndex": 1,
                "data": [round(r["efficiency"] or 0, 2) for r in results]
            },
            {
                "name": "OEE %",
                "type": "line",
                "yAxisIndex": 1,
                "data": [round(r["oee"] or 0, 2) for r in results]
            },
            {
                "name": "Availability %",
                "type": "line",
                "yAxisIndex": 1,
                "data": [round(r["availability"] or 0, 2) for r in results]
            }
        ]
    }

@router.get("/multi-metric-area")
def get_daily_stats_multi_metric_area(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    metrics: str = Query("efficiency,oee,availability,performance,quality", description="Comma-separated metrics")
):
    """Get daily stats for multi-metric area chart"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    metric_list = [m.strip() for m in metrics.split(",")]
    
    pipeline = [
        {"$match": query},
        {"$sort": {"date": 1}},
        {"$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            **{metric: f"${metric}" for metric in metric_list}
        }}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    return {
        "xAxis": [r["date"] for r in results],
        "series": [
            {
                "name": metric.title(),
                "type": "area",
                "data": [round(r.get(metric, 0) or 0, 2) for r in results]
            }
            for metric in metric_list
        ]
    }

@router.get("/production-trend")
def get_production_trend(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_ids: Optional[str] = Query(None, description="Comma-separated location IDs"),
    comparison_type: str = Query("daily", description="daily, weekly, monthly")
):
    """Get production trend analysis"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    if location_ids:
        location_list = [loc.strip() for loc in location_ids.split(",")]
        query["locationId"] = {"$in": location_list}
    
    group_format = {
        "daily": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
        "weekly": {"$dateToString": {"format": "%Y-W%U", "date": "$date"}},
        "monthly": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "period": group_format[comparison_type],
                "location": "$locationId"
            },
            "totalProduced": {"$sum": "$totalProduced"},
            "avgEfficiency": {"$avg": "$efficiency"},
            "totalRuntime": {"$sum": "$totalRuntime"},
            "totalDowntime": {"$sum": "$totalDowntime"}
        }},
        {"$sort": {"_id.period": 1, "_id.location": 1}}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    # Organize by location
    locations = sorted(list(set([r["_id"]["location"] for r in results if r["_id"]["location"]])))
    periods = sorted(list(set([r["_id"]["period"] for r in results])))
    
    series_data = {}
    for location in locations:
        series_data[location] = {
            "production": [],
            "efficiency": [],
            "runtime": [],
            "downtime": []
        }
        for period in periods:
            result = next((r for r in results if r["_id"]["period"] == period and r["_id"]["location"] == location), None)
            if result:
                series_data[location]["production"].append(result["totalProduced"])
                series_data[location]["efficiency"].append(round(result["avgEfficiency"] or 0, 2))
                series_data[location]["runtime"].append(result["totalRuntime"])
                series_data[location]["downtime"].append(result["totalDowntime"])
            else:
                series_data[location]["production"].append(0)
                series_data[location]["efficiency"].append(0)
                series_data[location]["runtime"].append(0)
                series_data[location]["downtime"].append(0)
    
    return {
        "xAxis": periods,
        "locations": locations,
        "series": [
            {
                "name": f"{location} - Production",
                "type": "line",
                "data": series_data[location]["production"]
            }
            for location in locations
        ] + [
            {
                "name": f"{location} - Efficiency",
                "type": "line",
                "yAxisIndex": 1,
                "data": series_data[location]["efficiency"]
            }
            for location in locations
        ]
    }

@router.get("/oee-breakdown")
def get_oee_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    chart_type: str = Query("stacked", description="stacked, radar, waterfall")
):
    """Get OEE breakdown (Availability, Performance, Quality)"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "availability": {"$avg": "$availability"},
            "performance": {"$avg": "$performance"},
            "quality": {"$avg": "$quality"},
            "oee": {"$avg": "$oee"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    if chart_type == "radar":
        # Average values for radar chart
        avg_data = {
            "availability": sum(r["availability"] or 0 for r in results) / len(results) if results else 0,
            "performance": sum(r["performance"] or 0 for r in results) / len(results) if results else 0,
            "quality": sum(r["quality"] or 0 for r in results) / len(results) if results else 0,
            "oee": sum(r["oee"] or 0 for r in results) / len(results) if results else 0
        }
        return {
            "type": "radar",
            "data": [
                {"name": "Availability", "value": round(avg_data["availability"], 2), "max": 100},
                {"name": "Performance", "value": round(avg_data["performance"], 2), "max": 100},
                {"name": "Quality", "value": round(avg_data["quality"], 2), "max": 100},
                {"name": "OEE", "value": round(avg_data["oee"], 2), "max": 100}
            ]
        }
    
    return {
        "xAxis": [r["_id"] for r in results],
        "series": [
            {
                "name": "Availability",
                "type": "line" if chart_type == "line" else "bar",
                "stack": "oee" if chart_type == "stacked" else None,
                "data": [round(r["availability"] or 0, 2) for r in results]
            },
            {
                "name": "Performance",
                "type": "line" if chart_type == "line" else "bar",
                "stack": "oee" if chart_type == "stacked" else None,
                "data": [round(r["performance"] or 0, 2) for r in results]
            },
            {
                "name": "Quality",
                "type": "line" if chart_type == "line" else "bar",
                "stack": "oee" if chart_type == "stacked" else None,
                "data": [round(r["quality"] or 0, 2) for r in results]
            }
        ]
    }

@router.get("/efficiency-heatmap")
def get_efficiency_heatmap(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    granularity: str = Query("daily", description="daily, weekly, monthly")
):
    """Get efficiency heatmap by location and time"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    time_formats = {
        "daily": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
        "weekly": {"$dateToString": {"format": "%Y-W%U", "date": "$date"}},
        "monthly": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "time": time_formats[granularity],
                "location": "$locationId"
            },
            "avgEfficiency": {"$avg": "$efficiency"}
        }}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    # Format for heatmap
    data = []
    times = sorted(list(set([r["_id"]["time"] for r in results])))
    locations = sorted(list(set([r["_id"]["location"] for r in results if r["_id"]["location"]])))
    
    for i, time in enumerate(times):
        for j, location in enumerate(locations):
            efficiency = next((r["avgEfficiency"] for r in results 
                             if r["_id"]["time"] == time and r["_id"]["location"] == location), 0)
            data.append([i, j, round(efficiency or 0, 2)])
    
    return {
        "data": data,
        "xAxis": times,
        "yAxis": locations,
        "visualMap": {
            "min": 0,
            "max": 100,
            "calculable": True,
            "orient": "horizontal",
            "left": "center"
        }
    }

@router.get("/downtime-analysis")
def get_downtime_analysis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    chart_type: str = Query("pie", description="pie, bar, treemap")
):
    """Get downtime analysis by reason/category"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$locationId",
            "totalDowntime": {"$sum": "$totalDowntime"},
            "avgDowntime": {"$avg": "$totalDowntime"},
            "totalRuntime": {"$sum": "$totalRuntime"},
            "downtimeRatio": {"$avg": {"$divide": ["$totalDowntime", {"$add": ["$totalDowntime", "$totalRuntime"]}]}}
        }},
        {"$sort": {"totalDowntime": -1}}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    if chart_type == "pie":
        return {
            "data": [
                {
                    "name": r["_id"] or "Unknown",
                    "value": r["totalDowntime"]
                }
                for r in results
            ]
        }
    
    return {
        "xAxis": [r["_id"] or "Unknown" for r in results],
        "series": [
            {
                "name": "Total Downtime",
                "type": "bar",
                "data": [r["totalDowntime"] for r in results]
            },
            {
                "name": "Downtime Ratio %",
                "type": "line",
                "yAxisIndex": 1,
                "data": [round((r["downtimeRatio"] or 0) * 100, 2) for r in results]
            }
        ]
    }

@router.get("/performance-kpis")
def get_performance_kpis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None)
):
    """Get key performance indicators"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "avgOEE": {"$avg": "$oee"},
            "avgEfficiency": {"$avg": "$efficiency"},
            "avgAvailability": {"$avg": "$availability"},
            "avgPerformance": {"$avg": "$performance"},
            "avgQuality": {"$avg": "$quality"},
            "totalProduced": {"$sum": "$totalProduced"},
            "totalRuntime": {"$sum": "$totalRuntime"},
            "totalDowntime": {"$sum": "$totalDowntime"},
            "recordCount": {"$sum": 1}
        }}
    ]
    
    result = list(db.timerdailystats.aggregate(pipeline))
    
    if not result:
        return {
            "oee": 0,
            "efficiency": 0,
            "availability": 0,
            "performance": 0,
            "quality": 0,
            "totalProduced": 0,
            "totalRuntime": 0,
            "totalDowntime": 0,
            "uptimeRatio": 0,
            "recordCount": 0
        }
    
    data = result[0]
    total_time = (data["totalRuntime"] or 0) + (data["totalDowntime"] or 0)
    uptime_ratio = (data["totalRuntime"] / total_time * 100) if total_time > 0 else 0
    
    return {
        "oee": round(data["avgOEE"] or 0, 2),
        "efficiency": round(data["avgEfficiency"] or 0, 2),
        "availability": round(data["avgAvailability"] or 0, 2),
        "performance": round(data["avgPerformance"] or 0, 2),
        "quality": round(data["avgQuality"] or 0, 2),
        "totalProduced": data["totalProduced"] or 0,
        "totalRuntime": data["totalRuntime"] or 0,
        "totalDowntime": data["totalDowntime"] or 0,
        "uptimeRatio": round(uptime_ratio, 2),
        "recordCount": data["recordCount"]
    }
