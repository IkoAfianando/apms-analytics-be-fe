from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db

router = APIRouter(prefix="/dashboard", tags=["Comprehensive Dashboard"])

@router.get("/overview")
def get_dashboard_overview(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None)
):
    """Get comprehensive dashboard overview with all key metrics"""
    db = get_db()
    
    # Date filter setup
    date_filter = {}
    if start_date and end_date:
        date_filter = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    # Location filter
    location_filter = {}
    if location_id:
        location_filter["locationId"] = location_id
    
    # Get production metrics
    production_pipeline = [
        {"$match": {**location_filter, **({"createdAt": date_filter} if date_filter else {})}},
        {"$group": {
            "_id": None,
            "totalProduced": {"$sum": {"$cond": [{"$eq": ["$stopReason", "Unit Created"]}, 1, 0]}},
            "totalLogs": {"$sum": 1},
            "totalRuntime": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}},
            "avgCycleTime": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "uniqueTimers": {"$addToSet": "$timerId"},
            "uniqueMachines": {"$addToSet": "$machineId"}
        }}
    ]
    
    production_data = list(db.timerlogs.aggregate(production_pipeline))
    prod_metrics = production_data[0] if production_data else {}
    
    # Get daily stats metrics
    daily_stats_filter = dict(location_filter)
    if date_filter:
        daily_stats_filter["date"] = date_filter
    
    daily_stats_pipeline = [
        {"$match": daily_stats_filter},
        {"$group": {
            "_id": None,
            "avgOEE": {"$avg": "$oee"},
            "avgEfficiency": {"$avg": "$efficiency"},
            "avgAvailability": {"$avg": "$availability"},
            "avgPerformance": {"$avg": "$performance"},
            "avgQuality": {"$avg": "$quality"},
            "totalDowntime": {"$sum": "$totalDowntime"}
        }}
    ]
    
    daily_stats_data = list(db.timerdailystats.aggregate(daily_stats_pipeline))
    daily_metrics = daily_stats_data[0] if daily_stats_data else {}
    
    # Get machine status
    machine_pipeline = [
        {"$match": location_filter},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    machine_status = list(db.machines.aggregate(machine_pipeline))
    machine_status_dict = {item["_id"]: item["count"] for item in machine_status}
    
    # Calculate efficiency
    total_logs = prod_metrics.get("totalLogs", 0)
    total_produced = prod_metrics.get("totalProduced", 0)
    efficiency = (total_produced / total_logs * 100) if total_logs > 0 else 0
    
    return {
        "production": {
            "totalProduced": total_produced,
            "totalLogs": total_logs,
            "efficiency": round(efficiency, 2),
            "avgCycleTime": round((prod_metrics.get("avgCycleTime", 0) or 0) / (60 * 1000), 2),  # minutes
            "uniqueTimers": len(prod_metrics.get("uniqueTimers", [])),
            "uniqueMachines": len(prod_metrics.get("uniqueMachines", []))
        },
        "oee": {
            "overall": round(daily_metrics.get("avgOEE", 0) or 0, 2),
            "availability": round(daily_metrics.get("avgAvailability", 0) or 0, 2),
            "performance": round(daily_metrics.get("avgPerformance", 0) or 0, 2),
            "quality": round(daily_metrics.get("avgQuality", 0) or 0, 2),
            "efficiency": round(daily_metrics.get("avgEfficiency", 0) or 0, 2)
        },
        "machines": {
            "total": sum(machine_status_dict.values()),
            "active": machine_status_dict.get("active", 0),
            "inactive": machine_status_dict.get("inactive", 0),
            "maintenance": machine_status_dict.get("maintenance", 0)
        },
        "downtime": {
            "total": round((daily_metrics.get("totalDowntime", 0) or 0) / (60 * 60 * 1000), 2)  # hours
        }
    }

@router.get("/production-charts")
def get_production_charts(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    chart_types: str = Query("line,bar,area", description="Comma-separated chart types")
):
    """Get production data formatted for multiple chart types"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    # Hourly production data
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$createdAt"}},
            "totalLogs": {"$sum": 1},
            "production": {"$sum": {"$cond": [{"$eq": ["$stopReason", "Unit Created"]}, 1, 0]}},
            "downtime": {"$sum": {"$cond": [{"$ne": ["$stopReason", "Unit Created"]}, 1, 0]}},
            "avgCycleTime": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "uniqueTimers": {"$addToSet": "$timerId"}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 168}  # Last week hourly data
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    chart_data = {
        "xAxis": [r["_id"] for r in results],
        "charts": {}
    }
    
    requested_charts = [chart.strip() for chart in chart_types.split(",")]
    
    if "line" in requested_charts:
        chart_data["charts"]["line"] = {
            "series": [
                {
                    "name": "Production Units",
                    "type": "line",
                    "data": [r["production"] for r in results],
                    "smooth": True
                },
                {
                    "name": "Total Logs",
                    "type": "line",
                    "data": [r["totalLogs"] for r in results],
                    "smooth": True
                }
            ]
        }
    
    if "bar" in requested_charts:
        chart_data["charts"]["bar"] = {
            "series": [
                {
                    "name": "Production",
                    "type": "bar",
                    "data": [r["production"] for r in results]
                },
                {
                    "name": "Downtime Events",
                    "type": "bar",
                    "data": [r["downtime"] for r in results]
                }
            ]
        }
    
    if "area" in requested_charts:
        chart_data["charts"]["area"] = {
            "series": [
                {
                    "name": "Production",
                    "type": "area",
                    "stack": "total",
                    "data": [r["production"] for r in results]
                },
                {
                    "name": "Downtime",
                    "type": "area",
                    "stack": "total",
                    "data": [r["downtime"] for r in results]
                }
            ]
        }
    
    return chart_data

@router.get("/real-time-status")
def get_real_time_status(location_id: Optional[str] = Query(None)):
    """Get real-time status of all systems"""
    db = get_db()
    
    # Get latest timer logs (last hour)
    last_hour = datetime.now() - timedelta(hours=1)
    
    query = {"createdAt": {"$gte": last_hour}}
    if location_id:
        query["locationId"] = location_id
    
    # Active timers
    active_timers_pipeline = [
        {"$match": {**query, "endedAt": None}},
        {"$group": {
            "_id": "$timerId",
            "startTime": {"$min": "$createdAt"},
            "machineId": {"$first": "$machineId"},
            "locationId": {"$first": "$locationId"},
            "status": {"$first": "$stopReason"}
        }},
        {"$sort": {"startTime": -1}}
    ]
    
    active_timers = list(db.timerlogs.aggregate(active_timers_pipeline))
    
    # Recent completed production
    recent_production_pipeline = [
        {"$match": {**query, "stopReason": "Unit Created", "endedAt": {"$ne": None}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%H:%M", "date": "$endedAt"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 12}  # Last 12 time slots
    ]
    
    recent_production = list(db.timerlogs.aggregate(recent_production_pipeline))
    
    # Machine alerts (simulated from recent downtime)
    alerts_pipeline = [
        {"$match": {
            **query,
            "stopReason": {"$nin": ["Unit Created", None]},
            "endedAt": None  # Still ongoing
        }},
        {"$group": {
            "_id": "$machineId",
            "alertType": {"$first": "$stopReason"},
            "startTime": {"$min": "$createdAt"},
            "location": {"$first": "$locationId"}
        }},
        {"$sort": {"startTime": 1}}
    ]
    
    alerts = list(db.timerlogs.aggregate(alerts_pipeline))
    
    return {
        "activeTimers": len(active_timers),
        "recentProduction": {
            "times": [r["_id"] for r in reversed(recent_production)],
            "counts": [r["count"] for r in reversed(recent_production)]
        },
        "alerts": [
            {
                "machineId": alert["_id"],
                "type": alert["alertType"],
                "duration": int((datetime.now() - alert["startTime"]).total_seconds() / 60),  # minutes
                "location": alert["location"]
            }
            for alert in alerts
        ],
        "systemStatus": "operational" if len(alerts) < 3 else "warning" if len(alerts) < 6 else "critical"
    }

@router.get("/efficiency-trends")
def get_efficiency_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    granularity: str = Query("daily", description="hourly, daily, weekly")
):
    """Get efficiency trends over time"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    group_formats = {
        "hourly": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$date"}},
        "daily": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
        "weekly": {"$dateToString": {"format": "%Y-W%U", "date": "$date"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": group_formats[granularity],
            "avgOEE": {"$avg": "$oee"},
            "avgEfficiency": {"$avg": "$efficiency"},
            "avgAvailability": {"$avg": "$availability"},
            "avgPerformance": {"$avg": "$performance"},
            "avgQuality": {"$avg": "$quality"},
            "totalProduced": {"$sum": "$totalProduced"},
            "totalDowntime": {"$sum": "$totalDowntime"}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 100}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    return {
        "xAxis": [r["_id"] for r in results],
        "series": [
            {
                "name": "OEE %",
                "type": "line",
                "data": [round(r["avgOEE"] or 0, 2) for r in results],
                "smooth": True
            },
            {
                "name": "Efficiency %",
                "type": "line",
                "data": [round(r["avgEfficiency"] or 0, 2) for r in results],
                "smooth": True
            },
            {
                "name": "Availability %",
                "type": "line",
                "data": [round(r["avgAvailability"] or 0, 2) for r in results],
                "smooth": True
            },
            {
                "name": "Performance %",
                "type": "line",
                "data": [round(r["avgPerformance"] or 0, 2) for r in results],
                "smooth": True
            },
            {
                "name": "Quality %",
                "type": "line",
                "data": [round(r["avgQuality"] or 0, 2) for r in results],
                "smooth": True
            }
        ]
    }

@router.get("/top-performers")
def get_top_performers(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    metric: str = Query("efficiency", description="efficiency, oee, production, availability"),
    top_n: int = Query(10)
):
    """Get top performing machines/locations"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    metric_field = f"avg{metric.title()}" if metric in ["efficiency", "oee", "availability"] else f"total{metric.title()}"
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$locationId",
            "avgOEE": {"$avg": "$oee"},
            "avgEfficiency": {"$avg": "$efficiency"},
            "avgAvailability": {"$avg": "$availability"},
            "avgPerformance": {"$avg": "$performance"},
            "totalProduction": {"$sum": "$totalProduced"},
            "recordCount": {"$sum": 1}
        }},
        {"$sort": {metric_field: -1}},
        {"$limit": top_n}
    ]
    
    results = list(db.timerdailystats.aggregate(pipeline))
    
    return {
        "data": [
            {
                "location": r["_id"] or "Unknown",
                "value": round(r.get(metric_field, 0) or 0, 2),
                "oee": round(r["avgOEE"] or 0, 2),
                "efficiency": round(r["avgEfficiency"] or 0, 2),
                "availability": round(r["avgAvailability"] or 0, 2),
                "production": r["totalProduction"] or 0,
                "records": r["recordCount"]
            }
            for r in results
        ]
    }

@router.get("/anomaly-detection")
def get_anomaly_detection(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    threshold: float = Query(2.0, description="Standard deviation threshold for anomalies")
):
    """Detect anomalies in production data"""
    db = get_db()
    
    query = {}
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    if location_id:
        query["locationId"] = location_id
    
    # Get cycle time anomalies
    pipeline = [
        {"$match": query},
        {"$addFields": {
            "cycleTime": {"$subtract": ["$endedAt", "$createdAt"]}
        }},
        {"$group": {
            "_id": "$timerId",
            "cycles": {"$push": {
                "time": "$createdAt",
                "duration": "$cycleTime",
                "reason": "$stopReason"
            }},
            "avgCycle": {"$avg": "$cycleTime"},
            "stdDev": {"$stdDevPop": "$cycleTime"}
        }},
        {"$unwind": "$cycles"},
        {"$addFields": {
            "zScore": {
                "$cond": [
                    {"$gt": ["$stdDev", 0]},
                    {"$divide": [
                        {"$subtract": ["$cycles.duration", "$avgCycle"]},
                        "$stdDev"
                    ]},
                    0
                ]
            }
        }},
        {"$match": {
            "$or": [
                {"zScore": {"$gt": threshold}},
                {"zScore": {"$lt": {"$multiply": [threshold, -1]}}}
            ]
        }},
        {"$sort": {"cycles.time": -1}},
        {"$limit": 50}
    ]
    
    anomalies = list(db.timerlogs.aggregate(pipeline))
    
    return {
        "anomalies": [
            {
                "timerId": str(anomaly["_id"]) if anomaly.get("_id") else None,
                "timestamp": anomaly["cycles"]["time"].isoformat(),
                "duration": round(anomaly["cycles"]["duration"] / (60 * 1000), 2),  # minutes
                "avgDuration": round(anomaly["avgCycle"] / (60 * 1000), 2),
                "zScore": round(anomaly["zScore"], 2),
                "reason": anomaly["cycles"]["reason"],
                "severity": "high" if abs(anomaly["zScore"]) > threshold * 1.5 else "medium"
            }
            for anomaly in anomalies
        ],
        "summary": {
            "totalAnomalies": len(anomalies),
            "highSeverity": len([a for a in anomalies if abs(a["zScore"]) > threshold * 1.5]),
            "threshold": threshold
        }
    }

@router.get("/predictive-maintenance")
def get_predictive_maintenance(
    location_id: Optional[str] = Query(None),
    days_ahead: int = Query(7, description="Days to predict ahead")
):
    """Get predictive maintenance recommendations"""
    db = get_db()
    
    # Calculate machine health scores based on recent performance
    last_30_days = datetime.now() - timedelta(days=30)
    
    query = {"createdAt": {"$gte": last_30_days}}
    if location_id:
        query["locationId"] = location_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$machineId",
            "totalEvents": {"$sum": 1},
            "downtimeEvents": {"$sum": {"$cond": [{"$ne": ["$stopReason", "Unit Created"]}, 1, 0]}},
            "avgCycleTime": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
            "cycleTimeStdDev": {"$stdDevPop": {"$subtract": ["$endedAt", "$createdAt"]}},
            "lastEvent": {"$max": "$createdAt"},
            "location": {"$first": "$locationId"}
        }},
        {"$addFields": {
            "downtimeRatio": {"$divide": ["$downtimeEvents", "$totalEvents"]},
            "healthScore": {
                "$multiply": [
                    {"$subtract": [1, {"$divide": ["$downtimeEvents", "$totalEvents"]}]},
                    100
                ]
            },
            "variabilityScore": {
                "$cond": [
                    {"$gt": ["$avgCycleTime", 0]},
                    {"$divide": ["$cycleTimeStdDev", "$avgCycleTime"]},
                    0
                ]
            }
        }},
        {"$sort": {"healthScore": 1}}
    ]
    
    machine_health = list(db.timerlogs.aggregate(pipeline))
    
    # Generate maintenance recommendations
    recommendations = []
    for machine in machine_health:
        health_score = machine["healthScore"]
        variability = machine["variabilityScore"]
        downtime_ratio = machine["downtimeRatio"]
        
        priority = "low"
        reason = "Normal operation"
        
        if health_score < 70:
            priority = "high"
            reason = f"Health score below 70% ({health_score:.1f}%)"
        elif downtime_ratio > 0.3:
            priority = "medium"
            reason = f"High downtime ratio ({downtime_ratio*100:.1f}%)"
        elif variability > 0.5:
            priority = "medium"
            reason = f"High cycle time variability"
        
        if priority != "low":
            recommendations.append({
                "machineId": machine["_id"],
                "location": machine["location"],
                "priority": priority,
                "healthScore": round(health_score, 1),
                "reason": reason,
                "recommendedAction": "Schedule inspection" if priority == "medium" else "Immediate maintenance required",
                "estimatedDays": 3 if priority == "high" else 7
            })
    
    return {
        "recommendations": recommendations,
        "summary": {
            "totalMachines": len(machine_health),
            "highPriority": len([r for r in recommendations if r["priority"] == "high"]),
            "mediumPriority": len([r for r in recommendations if r["priority"] == "medium"]),
            "averageHealthScore": round(sum(m["healthScore"] for m in machine_health) / len(machine_health), 1) if machine_health else 0
        }
    }
