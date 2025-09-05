from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db
from bson import ObjectId

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    else:
        return doc

router = APIRouter(prefix="/simple-dashboard", tags=["Simple Dashboard"])

@router.get("/overview")
def get_simple_dashboard_overview():
    """Get simple dashboard overview"""
    db = get_db()
    
    try:
        # Get basic production metrics
        total_logs = db.timerlogs.count_documents({})
        
        # Get production units (Unit Created)
        production_count = db.timerlogs.count_documents({"stopReason": "Unit Created"})
        
        # Get machine count
        machine_count = db.machines.count_documents({})
        
        # Get location count
        location_count = len(db.timerlogs.distinct("locationId"))
        
        # Get unique timers and machines from logs
        unique_timers = len(db.timerlogs.distinct("timerId"))
        unique_machines = len(db.timerlogs.distinct("machineId")) or machine_count
        
        # Calculate average cycle time (simplified)
        cycle_pipeline = [
            {"$match": {"cycle": {"$exists": True, "$gt": 0}}},
            {"$group": {"_id": None, "avgCycle": {"$avg": "$cycle"}}}
        ]
        cycle_result = list(db.timerlogs.aggregate(cycle_pipeline))
        avg_cycle_time = cycle_result[0]["avgCycle"] / 1000 if cycle_result and cycle_result[0]["avgCycle"] else 120  # seconds
        
        # Get downtime count
        downtime_count = db.timerlogs.count_documents({"stopReason": {"$ne": "Unit Created", "$ne": None}})
        
        # Calculate simple efficiency
        efficiency = (production_count / total_logs * 100) if total_logs > 0 else 0
        
        # Calculate OEE metrics (simplified)
        # For demo purposes, we'll simulate OEE components
        availability = min(85 + (efficiency / 10), 100)  # Simulated availability
        performance = min(90 + (efficiency / 15), 100)   # Simulated performance  
        quality = min(95 + (efficiency / 20), 100)       # Simulated quality
        oee_overall = (availability * performance * quality) / 10000  # OEE calculation
        
        # Simulate machine status
        active_machines = max(1, int(machine_count * 0.7))
        inactive_machines = max(0, int(machine_count * 0.2))
        maintenance_machines = machine_count - active_machines - inactive_machines
        
        return {
            "production": {
                "totalProduced": production_count,
                "totalLogs": total_logs,
                "efficiency": round(efficiency, 2),
                "avgCycleTime": round(avg_cycle_time, 1),
                "uniqueTimers": unique_timers,
                "uniqueMachines": unique_machines
            },
            "oee": {
                "overall": round(oee_overall, 1),
                "availability": round(availability, 1),
                "performance": round(performance, 1),
                "quality": round(quality, 1),
                "efficiency": round(efficiency, 1)
            },
            "machines": {
                "total": machine_count,
                "active": active_machines,
                "inactive": inactive_machines,
                "maintenance": maintenance_machines
            },
            "downtime": {
                "total": downtime_count
            },
            "summary": {
                "status": "operational",
                "dataPoints": total_logs,
                "productionRate": round(efficiency, 1)
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "production": {
                "totalProduced": 0, 
                "totalLogs": 0, 
                "efficiency": 0,
                "avgCycleTime": 120,
                "uniqueTimers": 0,
                "uniqueMachines": 0
            },
            "oee": {
                "overall": 0, 
                "availability": 0, 
                "performance": 0, 
                "quality": 0,
                "efficiency": 0
            },
            "machines": {
                "total": 0, 
                "active": 0,
                "inactive": 0,
                "maintenance": 0
            },
            "downtime": {
                "total": 0
            },
            "summary": {
                "status": "error", 
                "dataPoints": 0, 
                "productionRate": 0
            }
        }

@router.get("/recent-activity")
def get_recent_activity():
    """Get recent activity data"""
    db = get_db()
    
    try:
        # Get recent production data (last 24 hours)
        last_24h = datetime.now() - timedelta(hours=24)
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": last_24h}}},
            {"$group": {
                "_id": {"$hour": "$createdAt"},
                "total": {"$sum": 1},
                "production": {"$sum": {"$cond": [{"$eq": ["$stopReason", "Unit Created"]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        return {
            "hourlyData": {
                "hours": [f"{r['_id']:02d}:00" for r in results],
                "total": [r["total"] for r in results],
                "production": [r["production"] for r in results]
            },
            "summary": {
                "totalEvents": sum(r["total"] for r in results),
                "totalProduction": sum(r["production"] for r in results),
                "activeHours": len(results)
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "hourlyData": {"hours": [], "total": [], "production": []},
            "summary": {"totalEvents": 0, "totalProduction": 0}
        }

@router.get("/machine-status")
def get_machine_status():
    """Get machine status summary"""
    db = get_db()
    
    try:
        # Get machine status distribution
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        status_results = list(db.machines.aggregate(pipeline))
        status_results = serialize_doc(status_results)
        
        # Get machine locations
        location_pipeline = [
            {"$group": {"_id": "$locationId", "machines": {"$sum": 1}}},
            {"$sort": {"machines": -1}}
        ]
        
        location_results = list(db.machines.aggregate(location_pipeline))
        location_results = serialize_doc(location_results)
        
        return {
            "statusDistribution": [
                {"name": str(r["_id"]) if r["_id"] else "Unknown", "value": r["count"]}
                for r in status_results
            ],
            "locationDistribution": [
                {"name": str(r["_id"]) if r["_id"] else "Unknown", "value": r["machines"]}
                for r in location_results
            ],
            "summary": {
                "totalMachines": sum(r["count"] for r in status_results),
                "totalLocations": len(location_results)
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "statusDistribution": [],
            "locationDistribution": [],
            "summary": {"totalMachines": 0, "totalLocations": 0}
        }
