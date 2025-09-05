from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db

router = APIRouter(prefix="/machines", tags=["Machines Analytics"])

@router.get("/utilization-chart")
def get_machine_utilization_chart(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    machine_class_id: Optional[str] = Query(None),
    chart_type: str = Query("bar", description="bar, line, heatmap")
):
    """Get machine utilization data"""
    db = get_db()
    
    # Join machines with timer logs to get utilization data
    pipeline = []
    
    # Match criteria
    match_stage = {}
    if location_id:
        match_stage["locationId"] = location_id
    if machine_class_id:
        match_stage["machineClassId"] = machine_class_id
    
    if match_stage:
        pipeline.append({"$match": match_stage})
    
    # Lookup timer logs
    lookup_match = {}
    if start_date and end_date:
        lookup_match["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline.extend([
        {"$lookup": {
            "from": "timerlogs",
            "let": {"machineId": "$_id"},
            "pipeline": [
                {"$match": {
                    "$expr": {"$eq": ["$machineId", "$$machineId"]},
                    **lookup_match
                }},
                {"$group": {
                    "_id": None,
                    "totalRuntime": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}},
                    "logCount": {"$sum": 1},
                    "productiveTime": {"$sum": {
                        "$cond": [
                            {"$eq": ["$stopReason", "Unit Created"]},
                            {"$subtract": ["$endedAt", "$createdAt"]},
                            0
                        ]
                    }}
                }}
            ],
            "as": "utilization"
        }},
        {"$addFields": {
            "utilizationData": {"$arrayElemAt": ["$utilization", 0]}
        }},
        {"$project": {
            "machineName": "$name",
            "machineClass": "$machineClassId",
            "location": "$locationId",
            "totalRuntime": {"$ifNull": ["$utilizationData.totalRuntime", 0]},
            "logCount": {"$ifNull": ["$utilizationData.logCount", 0]},
            "productiveTime": {"$ifNull": ["$utilizationData.productiveTime", 0]},
            "utilizationRate": {
                "$cond": [
                    {"$gt": ["$utilizationData.totalRuntime", 0]},
                    {"$multiply": [
                        {"$divide": ["$utilizationData.productiveTime", "$utilizationData.totalRuntime"]},
                        100
                    ]},
                    0
                ]
            }
        }},
        {"$sort": {"utilizationRate": -1}}
    ])
    
    results = list(db.machines.aggregate(pipeline))
    
    if chart_type == "heatmap":
        # Create heatmap data
        locations = sorted(list(set([r["location"] for r in results if r["location"]])))
        machines = [r["machineName"] or f"Machine {i}" for i, r in enumerate(results)]
        
        data = []
        for i, machine in enumerate(machines):
            for j, location in enumerate(locations):
                machine_data = next((r for r in results if r["machineName"] == machine and r["location"] == location), None)
                utilization = machine_data["utilizationRate"] if machine_data else 0
                data.append([i, j, round(utilization, 2)])
        
        return {
            "data": data,
            "xAxis": machines,
            "yAxis": locations
        }
    
    return {
        "xAxis": [r["machineName"] or f"Machine {i}" for i, r in enumerate(results)],
        "series": [
            {
                "name": "Utilization Rate %",
                "type": chart_type,
                "data": [round(r["utilizationRate"], 2) for r in results]
            },
            {
                "name": "Log Count",
                "type": chart_type,
                "yAxisIndex": 1,
                "data": [r["logCount"] for r in results]
            }
        ]
    }

@router.get("/status-distribution")
def get_machine_status_distribution(
    location_id: Optional[str] = Query(None),
    chart_type: str = Query("pie", description="pie, doughnut, bar")
):
    """Get machine status distribution"""
    db = get_db()
    
    pipeline = []
    
    if location_id:
        pipeline.append({"$match": {"locationId": location_id}})
    
    pipeline.extend([
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "machines": {"$push": "$name"}
        }},
        {"$sort": {"count": -1}}
    ])
    
    results = list(db.machines.aggregate(pipeline))
    
    if chart_type in ["pie", "doughnut"]:
        return {
            "data": [
                {
                    "name": r["_id"] or "Unknown",
                    "value": r["count"]
                }
                for r in results
            ]
        }
    
    return {
        "xAxis": [r["_id"] or "Unknown" for r in results],
        "series": [
            {
                "name": "Machine Count",
                "type": "bar",
                "data": [r["count"] for r in results]
            }
        ]
    }

@router.get("/performance-matrix")
def get_machine_performance_matrix(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    top_n: int = Query(20)
):
    """Get machine performance matrix (efficiency vs utilization)"""
    db = get_db()
    
    match_stage = {}
    if location_id:
        match_stage["locationId"] = location_id
    
    lookup_match = {}
    if start_date and end_date:
        lookup_match["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": match_stage},
        {"$lookup": {
            "from": "timerlogs",
            "let": {"machineId": "$_id"},
            "pipeline": [
                {"$match": {
                    "$expr": {"$eq": ["$machineId", "$$machineId"]},
                    **lookup_match
                }},
                {"$group": {
                    "_id": None,
                    "totalLogs": {"$sum": 1},
                    "productiveLogs": {"$sum": {
                        "$cond": [{"$eq": ["$stopReason", "Unit Created"]}, 1, 0]
                    }},
                    "totalRuntime": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}},
                    "avgCycleTime": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}}
                }}
            ],
            "as": "performance"
        }},
        {"$addFields": {
            "perfData": {"$arrayElemAt": ["$performance", 0]}
        }},
        {"$project": {
            "machineName": "$name",
            "machineClass": "$machineClassId",
            "location": "$locationId",
            "efficiency": {
                "$cond": [
                    {"$gt": ["$perfData.totalLogs", 0]},
                    {"$multiply": [
                        {"$divide": ["$perfData.productiveLogs", "$perfData.totalLogs"]},
                        100
                    ]},
                    0
                ]
            },
            "utilization": {
                "$cond": [
                    {"$gt": ["$perfData.totalRuntime", 0]},
                    {"$divide": ["$perfData.totalRuntime", 28800000]}, # 8 hours in ms
                    0
                ]
            },
            "totalLogs": {"$ifNull": ["$perfData.totalLogs", 0]},
            "avgCycleTime": {"$ifNull": ["$perfData.avgCycleTime", 0]}
        }},
        {"$match": {"totalLogs": {"$gt": 0}}},
        {"$limit": top_n}
    ]
    
    results = list(db.machines.aggregate(pipeline))
    
    # Format for scatter plot
    scatter_data = []
    for r in results:
        scatter_data.append([
            round(r["utilization"], 2),  # x-axis: utilization
            round(r["efficiency"], 2),   # y-axis: efficiency
            r["totalLogs"],              # size
            r["machineName"] or "Unknown" # name
        ])
    
    return {
        "data": scatter_data,
        "xAxis": "Utilization",
        "yAxis": "Efficiency %",
        "size": "Total Logs"
    }

@router.get("/downtime-ranking")
def get_machine_downtime_ranking(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    top_n: int = Query(15)
):
    """Get machine downtime ranking"""
    db = get_db()
    
    match_stage = {}
    if location_id:
        match_stage["locationId"] = location_id
    
    lookup_match = {"stopReason": {"$ne": "Unit Created"}}
    if start_date and end_date:
        lookup_match["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    pipeline = [
        {"$match": match_stage},
        {"$lookup": {
            "from": "timerlogs",
            "let": {"machineId": "$_id"},
            "pipeline": [
                {"$match": {
                    "$expr": {"$eq": ["$machineId", "$$machineId"]},
                    **lookup_match
                }},
                {"$group": {
                    "_id": None,
                    "downtimeEvents": {"$sum": 1},
                    "totalDowntime": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}},
                    "avgDowntime": {"$avg": {"$subtract": ["$endedAt", "$createdAt"]}},
                    "maxDowntime": {"$max": {"$subtract": ["$endedAt", "$createdAt"]}}
                }}
            ],
            "as": "downtime"
        }},
        {"$addFields": {
            "downtimeData": {"$arrayElemAt": ["$downtime", 0]}
        }},
        {"$project": {
            "machineName": "$name",
            "location": "$locationId",
            "downtimeEvents": {"$ifNull": ["$downtimeData.downtimeEvents", 0]},
            "totalDowntime": {"$ifNull": ["$downtimeData.totalDowntime", 0]},
            "avgDowntime": {"$ifNull": ["$downtimeData.avgDowntime", 0]},
            "maxDowntime": {"$ifNull": ["$downtimeData.maxDowntime", 0]}
        }},
        {"$match": {"downtimeEvents": {"$gt": 0}}},
        {"$sort": {"totalDowntime": -1}},
        {"$limit": top_n}
    ]
    
    results = list(db.machines.aggregate(pipeline))
    
    return {
        "xAxis": [r["machineName"] or f"Machine {i}" for i, r in enumerate(results)],
        "series": [
            {
                "name": "Total Downtime (hours)",
                "type": "bar",
                "data": [round(r["totalDowntime"] / (60 * 60 * 1000), 2) for r in results]
            },
            {
                "name": "Downtime Events",
                "type": "line",
                "yAxisIndex": 1,
                "data": [r["downtimeEvents"] for r in results]
            },
            {
                "name": "Avg Downtime (min)",
                "type": "line",
                "yAxisIndex": 2,
                "data": [round(r["avgDowntime"] / (60 * 1000), 2) for r in results]
            }
        ]
    }

@router.get("/machine-classes")
def get_machine_class_analytics(
    chart_type: str = Query("bar", description="bar, pie, treemap"),
    metric: str = Query("count", description="count, efficiency, utilization")
):
    """Get machine class analytics"""
    db = get_db()
    
    pipeline = [
        {"$group": {
            "_id": "$machineClassId",
            "machineCount": {"$sum": 1},
            "machines": {"$push": "$name"},
            "locations": {"$addToSet": "$locationId"}
        }},
        {"$lookup": {
            "from": "machineclasses",
            "localField": "_id",
            "foreignField": "_id",
            "as": "classInfo"
        }},
        {"$addFields": {
            "className": {"$arrayElemAt": ["$classInfo.name", 0]}
        }},
        {"$sort": {"machineCount": -1}}
    ]
    
    results = list(db.machines.aggregate(pipeline))
    
    if chart_type == "treemap":
        return {
            "data": [
                {
                    "name": r["className"] or r["_id"] or "Unknown",
                    "value": r["machineCount"],
                    "children": [
                        {"name": machine, "value": 1}
                        for machine in (r["machines"] or [])
                    ]
                }
                for r in results
            ]
        }
    
    if chart_type == "pie":
        return {
            "data": [
                {
                    "name": r["className"] or r["_id"] or "Unknown",
                    "value": r["machineCount"]
                }
                for r in results
            ]
        }
    
    return {
        "xAxis": [r["className"] or r["_id"] or "Unknown" for r in results],
        "series": [
            {
                "name": "Machine Count",
                "type": "bar",
                "data": [r["machineCount"] for r in results]
            },
            {
                "name": "Location Count",
                "type": "bar",
                "data": [len(r["locations"]) for r in results]
            }
        ]
    }

@router.get("/availability-timeline")
def get_machine_availability_timeline(
    machine_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    granularity: str = Query("hour", description="hour, day")
):
    """Get machine availability timeline"""
    db = get_db()
    
    query = {}
    if machine_id:
        query["machineId"] = machine_id
    if start_date and end_date:
        query["createdAt"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    time_format = {
        "hour": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$createdAt"}},
        "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}}
    }
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "time": time_format[granularity],
                "machine": "$machineId",
                "status": {"$cond": [{"$eq": ["$stopReason", "Unit Created"]}, "running", "stopped"]}
            },
            "count": {"$sum": 1},
            "duration": {"$sum": {"$subtract": ["$endedAt", "$createdAt"]}}
        }},
        {"$group": {
            "_id": {
                "time": "$_id.time",
                "machine": "$_id.machine"
            },
            "totalDuration": {"$sum": "$duration"},
            "runningDuration": {"$sum": {
                "$cond": [{"$eq": ["$_id.status", "running"]}, "$duration", 0]
            }},
            "stoppedDuration": {"$sum": {
                "$cond": [{"$eq": ["$_id.status", "stopped"]}, "$duration", 0]
            }}
        }},
        {"$addFields": {
            "availability": {
                "$cond": [
                    {"$gt": ["$totalDuration", 0]},
                    {"$multiply": [
                        {"$divide": ["$runningDuration", "$totalDuration"]},
                        100
                    ]},
                    0
                ]
            }
        }},
        {"$sort": {"_id.time": 1}}
    ]
    
    results = list(db.timerlogs.aggregate(pipeline))
    
    # Group by machine
    machines = sorted(list(set([r["_id"]["machine"] for r in results if r["_id"]["machine"]])))
    times = sorted(list(set([r["_id"]["time"] for r in results])))
    
    series_data = {}
    for machine in machines:
        series_data[machine] = []
        for time in times:
            availability = next((r["availability"] for r in results 
                               if r["_id"]["time"] == time and r["_id"]["machine"] == machine), 0)
            series_data[machine].append(round(availability, 2))
    
    return {
        "xAxis": times,
        "series": [
            {
                "name": f"Machine {machine}",
                "type": "line",
                "data": series_data[machine]
            }
            for machine in machines
        ]
    }

@router.get("/machine-summary")
def get_machine_summary():
    """Get overall machine summary statistics"""
    db = get_db()
    
    pipeline = [
        {"$group": {
            "_id": None,
            "totalMachines": {"$sum": 1},
            "activeMachines": {"$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}},
            "inactiveMachines": {"$sum": {"$cond": [{"$eq": ["$status", "inactive"]}, 1, 0]}},
            "uniqueLocations": {"$addToSet": "$locationId"},
            "uniqueClasses": {"$addToSet": "$machineClassId"}
        }}
    ]
    
    result = list(db.machines.aggregate(pipeline))
    
    if not result:
        return {
            "totalMachines": 0,
            "activeMachines": 0,
            "inactiveMachines": 0,
            "locationCount": 0,
            "classCount": 0,
            "utilizationRate": 0
        }
    
    data = result[0]
    utilization_rate = (data["activeMachines"] / data["totalMachines"] * 100) if data["totalMachines"] > 0 else 0
    
    return {
        "totalMachines": data["totalMachines"],
        "activeMachines": data["activeMachines"],
        "inactiveMachines": data["inactiveMachines"],
        "locationCount": len(data["uniqueLocations"]),
        "classCount": len(data["uniqueClasses"]),
        "utilizationRate": round(utilization_rate, 2)
    }
