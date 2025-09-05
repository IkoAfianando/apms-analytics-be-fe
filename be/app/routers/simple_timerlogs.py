from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db

router = APIRouter(prefix="/simple-timerlogs", tags=["Simple Timer Logs"])

@router.get("/stats")
def get_simple_timer_logs_stats():
    """Get simple timer logs statistics"""
    db = get_db()
    
    try:
        # Simple count query
        total_count = db.timerlogs.count_documents({})
        
        # Get some recent logs
        recent_logs = list(db.timerlogs.find().sort("_id", -1).limit(10))
        
        # Get unique stop reasons
        pipeline = [
            {"$group": {"_id": "$stopReason", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        stop_reasons = list(db.timerlogs.aggregate(pipeline))
        
        # Convert ObjectIds to strings
        processed_stop_reasons = []
        for reason in stop_reasons:
            processed_stop_reasons.append({
                "_id": str(reason["_id"]) if reason["_id"] is not None else "Unknown",
                "count": reason["count"]
            })
        
        return {
            "totalCount": total_count,
            "recentLogsCount": len(recent_logs),
            "stopReasons": processed_stop_reasons
        }
    except Exception as e:
        return {"error": str(e), "totalCount": 0}

@router.get("/pie-chart")
def get_simple_pie_chart():
    """Get simple pie chart data for stop reasons"""
    db = get_db()
    
    try:
        pipeline = [
            {"$group": {"_id": "$stopReason", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        return {
            "data": [
                {
                    "name": str(r["_id"]) if r["_id"] is not None else "Unknown",
                    "value": r["count"]
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e), "data": []}

@router.get("/bar-chart")
def get_simple_bar_chart():
    """Get simple bar chart data"""
    db = get_db()
    
    try:
        pipeline = [
            {"$group": {"_id": "$locationId", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        return {
            "xAxis": [str(r["_id"]) if r["_id"] is not None else "Unknown" for r in results],
            "series": [
                {
                    "name": "Timer Logs Count",
                    "type": "bar",
                    "data": [r["count"] for r in results]
                }
            ]
        }
    except Exception as e:
        return {"error": str(e), "xAxis": [], "series": []}

@router.get("/line-chart")
def get_simple_line_chart():
    """Get simple line chart data by date"""
    db = get_db()
    
    try:
        # Get data for the last 30 days
        start_date = datetime.now() - timedelta(days=30)
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 30}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        return {
            "xAxis": [str(r["_id"]) if r["_id"] is not None else "Unknown" for r in results],
            "series": [
                {
                    "name": "Daily Timer Logs",
                    "type": "line",
                    "data": [r["count"] for r in results]
                }
            ]
        }
    except Exception as e:
        return {"error": str(e), "xAxis": [], "series": []}
