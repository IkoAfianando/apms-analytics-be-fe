from __future__ import annotations

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.db import get_db
import random
import math
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

router = APIRouter(prefix="/advanced-charts", tags=["Advanced Charts for ECharts"])

@router.get("/line-charts/basic")
def get_basic_line_chart():
    """Basic Line Chart"""
    db = get_db()
    
    try:
        # Get daily production data for the last 14 days
        start_date = datetime.now() - timedelta(days=14)
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, "stopReason": "Unit Created"}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        return {
            "title": "Daily Production Units",
            "xAxis": [r["_id"] for r in results],
            "series": [
                {
                    "name": "Production Units",
                    "type": "line",
                    "data": [r["count"] for r in results],
                    "smooth": True
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/line-charts/smoothed")
def get_smoothed_line_chart():
    """Smoothed Line Chart with multiple series"""
    db = get_db()
    
    try:
        start_date = datetime.now() - timedelta(days=21)
        
        # Get production and downtime data
        production_pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, "stopReason": "Unit Created"}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "production": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        downtime_pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, "stopReason": {"$ne": "Unit Created"}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "downtime": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        production_results = list(db.timerlogs.aggregate(production_pipeline))
        downtime_results = list(db.timerlogs.aggregate(downtime_pipeline))
        
        # Combine data
        all_dates = sorted(list(set([r["_id"] for r in production_results] + [r["_id"] for r in downtime_results])))
        
        production_data = []
        downtime_data = []
        
        for date in all_dates:
            prod = next((r["production"] for r in production_results if r["_id"] == date), 0)
            down = next((r["downtime"] for r in downtime_results if r["_id"] == date), 0)
            production_data.append(prod)
            downtime_data.append(down)
        
        return {
            "title": "Production vs Downtime Trend",
            "xAxis": all_dates,
            "series": [
                {
                    "name": "Production",
                    "type": "line",
                    "data": production_data,
                    "smooth": True,
                    "lineStyle": {"width": 3},
                    "areaStyle": {"opacity": 0.3}
                },
                {
                    "name": "Downtime Events",
                    "type": "line",
                    "data": downtime_data,
                    "smooth": True,
                    "lineStyle": {"width": 3, "type": "dashed"}
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/area-charts/basic")
def get_basic_area_chart():
    """Basic Area Chart"""
    db = get_db()
    
    try:
        start_date = datetime.now() - timedelta(days=30)
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}}},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                    "location": {"$ifNull": ["$locationId", "Unknown"]}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        # Serialize the results to avoid ObjectId issues
        results = serialize_doc(results)
        
        # Organize by location
        dates = sorted(list(set([r["_id"]["date"] for r in results])))
        locations = sorted(list(set([r["_id"]["location"] for r in results if r["_id"]["location"]])))
        
        series_data = []
        for location in locations[:3]:  # Limit to 3 locations
            location_data = []
            for date in dates:
                count = next((r["count"] for r in results 
                            if r["_id"]["date"] == date and r["_id"]["location"] == location), 0)
                location_data.append(count)
            
            series_data.append({
                "name": str(location) if location else "Unknown",
                "type": "area",
                "data": location_data,
                "areaStyle": {"opacity": 0.6}
            })
        
        # If no data, create sample
        if not series_data:
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
            series_data = [
                {"name": "Line A", "type": "area", "data": [random.randint(10, 50) for _ in dates], "areaStyle": {"opacity": 0.6}},
                {"name": "Line B", "type": "area", "data": [random.randint(5, 30) for _ in dates], "areaStyle": {"opacity": 0.6}}
            ]
        
        return {
            "title": "Activity by Location (Area Chart)",
            "xAxis": dates,
            "series": series_data
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/area-charts/stacked")
def get_stacked_area_chart():
    """Stacked Area Chart"""
    db = get_db()
    
    try:
        start_date = datetime.now() - timedelta(days=14)
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}}},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                    "reason": "$stopReason"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        # Serialize the results to avoid ObjectId issues
        results = serialize_doc(results)
        
        # Get top 5 stop reasons - handle array/list values
        reason_counts = {}
        for r in results:
            reason = r["_id"]["reason"]
            
            # Handle different types of stopReason values
            if isinstance(reason, list):
                # If it's a list, convert to string or take first element
                reason_str = str(reason) if len(reason) > 1 else (reason[0] if reason else "Unknown")
            elif isinstance(reason, str):
                reason_str = reason
            else:
                reason_str = str(reason) if reason is not None else "Unknown"
            
            reason_counts[reason_str] = reason_counts.get(reason_str, 0) + r["count"]
        
        top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_reason_names = [r[0] for r in top_reasons]
        
        dates = sorted(list(set([r["_id"]["date"] for r in results])))
        
        series_data = []
        for reason_name in top_reason_names:
            reason_data = []
            for date in dates:
                count = 0
                for r in results:
                    if r["_id"]["date"] == date:
                        r_reason = r["_id"]["reason"]
                        
                        # Handle different types of stopReason values
                        if isinstance(r_reason, list):
                            r_reason_str = str(r_reason) if len(r_reason) > 1 else (r_reason[0] if r_reason else "Unknown")
                        elif isinstance(r_reason, str):
                            r_reason_str = r_reason
                        else:
                            r_reason_str = str(r_reason) if r_reason is not None else "Unknown"
                        
                        if r_reason_str == reason_name:
                            count += r["count"]
                
                reason_data.append(count)
            
            series_data.append({
                "name": reason_name,
                "type": "area",
                "stack": "total",
                "data": reason_data,
                "areaStyle": {}
            })
        
        return {
            "title": "Stacked Activity by Stop Reason",
            "xAxis": dates,
            "series": series_data
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/scatter-charts/basic")
def get_basic_scatter_chart():
    """Basic Scatter Chart"""
    db = get_db()
    
    try:
        # Get cycle time vs production correlation with proper date handling
        pipeline = [
            {"$match": {"stopReason": "Unit Created"}},
            {"$addFields": {
                "createdAtDate": {
                    "$cond": [
                        {"$eq": [{"$type": "$createdAt"}, "date"]},
                        "$createdAt",
                        {"$dateFromString": {"dateString": "$createdAt"}}
                    ]
                },
                "endedAtDate": {
                    "$cond": [
                        {"$eq": [{"$type": "$endedAt"}, "date"]},
                        "$endedAt",
                        {"$dateFromString": {"dateString": "$endedAt"}}
                    ]
                }
            }},
            {"$match": {
                "endedAtDate": {"$ne": None},
                "createdAtDate": {"$ne": None}
            }},
            {"$addFields": {
                "duration": {"$subtract": ["$endedAtDate", "$createdAtDate"]}
            }},
            {"$match": {"duration": {"$gt": 0, "$lt": 3600000}}},  # 1 hour max
            {"$sample": {"size": 200}}  # Sample for performance
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        scatter_data = []
        for r in results:
            if r.get("duration") and r.get("createdAtDate"):
                duration_minutes = r["duration"] / (60 * 1000)  # Convert to minutes
                hour = r["createdAtDate"].hour if hasattr(r["createdAtDate"], "hour") else 0
                scatter_data.append([hour, duration_minutes])
        
        # If no data found, create sample data
        if not scatter_data:
            scatter_data = [[i, random.uniform(1, 30)] for i in range(24)]
        
        return {
            "title": "Cycle Time vs Hour of Day",
            "xAxisName": "Hour of Day",
            "yAxisName": "Cycle Time (minutes)",
            "series": [
                {
                    "name": "Cycle Times",
                    "type": "scatter",
                    "data": scatter_data,
                    "symbolSize": 8
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/heatmap-charts/calendar")
def get_calendar_heatmap():
    """Calendar Heatmap"""
    db = get_db()
    
    try:
        start_date = datetime.now() - timedelta(days=90)
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, "stopReason": "Unit Created"}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "count": {"$sum": 1}
            }}
        ]
        
        results = list(db.timerlogs.aggregate(pipeline))
        
        # Format for calendar heatmap
        heatmap_data = []
        for r in results:
            heatmap_data.append([r["_id"], r["count"]])
        
        return {
            "title": "Production Calendar Heatmap",
            "data": heatmap_data,
            "calendarRange": [start_date.strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/gauge-charts/multi")
def get_multi_gauge_chart():
    """Multiple Gauge Charts for KPIs"""
    db = get_db()
    
    try:
        # Calculate various KPIs
        total_logs = db.timerlogs.count_documents({})
        production_logs = db.timerlogs.count_documents({"stopReason": "Unit Created"})
        
        efficiency = (production_logs / total_logs * 100) if total_logs > 0 else 0
        
        # Machine utilization
        active_machines = db.machines.count_documents({"status": "active"})
        total_machines = db.machines.count_documents({})
        
        utilization = (active_machines / total_machines * 100) if total_machines > 0 else 0
        
        # Quality score (simulated based on production consistency)
        quality_score = min(95 + random.uniform(-5, 5), 100)
        
        return {
            "gauges": [
                {
                    "name": "Efficiency",
                    "value": round(efficiency, 1),
                    "max": 100,
                    "unit": "%",
                    "color": "#28a745" if efficiency > 80 else "#ffc107" if efficiency > 60 else "#dc3545"
                },
                {
                    "name": "Utilization",
                    "value": round(utilization, 1),
                    "max": 100,
                    "unit": "%",
                    "color": "#17a2b8" if utilization > 70 else "#ffc107" if utilization > 50 else "#dc3545"
                },
                {
                    "name": "Quality",
                    "value": round(quality_score, 1),
                    "max": 100,
                    "unit": "%",
                    "color": "#007bff" if quality_score > 90 else "#ffc107" if quality_score > 80 else "#dc3545"
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/radar-charts/performance")
def get_performance_radar():
    """Performance Radar Chart"""
    db = get_db()
    
    try:
        # Calculate metrics for each location
        locations_raw = db.timerlogs.distinct("locationId")[:3]  # Top 3 locations
        # Convert ObjectIds to strings
        locations = [str(loc) if loc is not None else "Unknown" for loc in locations_raw]
        
        radar_data = []
        
        for i, location in enumerate(locations):
            if not location or location == "Unknown":
                continue
                
            # Use the original ObjectId for queries, but display string for output
            original_location = locations_raw[i]
            
            total = db.timerlogs.count_documents({"locationId": original_location})
            production = db.timerlogs.count_documents({"locationId": original_location, "stopReason": "Unit Created"})
            
            efficiency = (production / total * 100) if total > 0 else 0
            
            # Simulated metrics
            availability = min(85 + random.uniform(-10, 10), 100)
            performance = min(90 + random.uniform(-15, 10), 100)
            quality = min(95 + random.uniform(-5, 5), 100)
            throughput = min(efficiency + random.uniform(-5, 5), 100)
            
            radar_data.append({
                "name": location,  # This is now a string
                "value": [efficiency, availability, performance, quality, throughput]
            })
        
        return {
            "title": "Performance Radar by Location",
            "indicators": [
                {"name": "Efficiency", "max": 100},
                {"name": "Availability", "max": 100},
                {"name": "Performance", "max": 100},
                {"name": "Quality", "max": 100},
                {"name": "Throughput", "max": 100}
            ],
            "data": radar_data
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/funnel-charts/conversion")
def get_funnel_chart():
    """Funnel Chart for Process Flow"""
    db = get_db()
    
    try:
        # Production funnel stages
        total_starts = db.timerlogs.count_documents({"stopReason": {"$in": ["Started", "Auto-Start"]}})
        in_progress = db.timerlogs.count_documents({"endedAt": None})
        completed = db.timerlogs.count_documents({"stopReason": "Unit Created"})
        quality_passed = int(completed * 0.95)  # Simulate 95% quality rate
        shipped = int(quality_passed * 0.98)  # Simulate 98% shipping rate
        
        return {
            "title": "Production Process Funnel",
            "data": [
                {"name": "Started", "value": total_starts},
                {"name": "In Progress", "value": in_progress},
                {"name": "Completed", "value": completed},
                {"name": "Quality Passed", "value": quality_passed},
                {"name": "Shipped", "value": shipped}
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/tree-charts/hierarchy")
def get_tree_chart():
    """Tree Chart for Machine Hierarchy"""
    db = get_db()
    
    try:
        # Build machine hierarchy
        locations = list(db.machines.aggregate([
            {"$group": {
                "_id": "$locationId",
                "machines": {"$push": {"id": "$_id", "name": "$name", "class": "$machineClassId"}}
            }}
        ]))
        
        # Serialize the results to avoid ObjectId issues
        locations = serialize_doc(locations)
        
        tree_data = {
            "name": "APMS Factory",
            "children": []
        }
        
        for loc in locations:
            location_node = {
                "name": str(loc["_id"]) if loc["_id"] else "Unknown Location",
                "children": []
            }
            
            for machine in loc["machines"][:5]:  # Limit for display
                machine_node = {
                    "name": machine.get("name", "Unknown Machine"),
                    "value": 1,
                    "itemStyle": {"color": f"#{random.randint(100000, 999999):06x}"}
                }
                location_node["children"].append(machine_node)
            
            if location_node["children"]:  # Only add if has children
                tree_data["children"].append(location_node)
        
        # If no real data, create sample tree
        if not tree_data["children"]:
            tree_data = {
                "name": "APMS Factory",
                "children": [
                    {
                        "name": "Production Line A",
                        "children": [
                            {"name": "Machine 1", "value": 15},
                            {"name": "Machine 2", "value": 12},
                            {"name": "Machine 3", "value": 8}
                        ]
                    },
                    {
                        "name": "Production Line B", 
                        "children": [
                            {"name": "Machine 4", "value": 10},
                            {"name": "Machine 5", "value": 14}
                        ]
                    }
                ]
            }
        
        return {
            "title": "Machine Hierarchy",
            "data": serialize_doc(tree_data)
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/sankey-charts/flow")
def get_sankey_chart():
    """Sankey Chart for Process Flow"""
    db = get_db()
    
    try:
        # Get stop reason transitions (simplified)
        pipeline = [
            {"$group": {"_id": "$stopReason", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 6}
        ]
        
        reasons = list(db.timerlogs.aggregate(pipeline))
        
        # Serialize the results to avoid ObjectId issues
        reasons = serialize_doc(reasons)
        
        nodes = []
        links = []
        
        # Create nodes
        for i, reason in enumerate(reasons):
            nodes.append({"name": reason["_id"] or "Unknown"})
        
        # Create links (simplified flow)
        for i in range(len(reasons) - 1):
            links.append({
                "source": reasons[i]["_id"] or "Unknown",
                "target": reasons[i + 1]["_id"] or "Unknown",
                "value": min(reasons[i]["count"], reasons[i + 1]["count"]) // 10
            })
        
        return {
            "title": "Process Flow (Sankey)",
            "nodes": nodes,
            "links": links
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/dashboard/comprehensive")
def get_comprehensive_chart_data():
    """Get data for all chart types at once"""
    db = get_db()
    
    try:
        # This would be the main endpoint for loading all chart data
        basic_line = get_basic_line_chart()
        smoothed_line = get_smoothed_line_chart()
        basic_area = get_basic_area_chart()
        stacked_area = get_stacked_area_chart()
        scatter = get_basic_scatter_chart()
        calendar_heatmap = get_calendar_heatmap()
        multi_gauge = get_multi_gauge_chart()
        radar = get_performance_radar()
        funnel = get_funnel_chart()
        tree = get_tree_chart()
        sankey = get_sankey_chart()
        
        return {
            "charts": {
                "basicLine": basic_line,
                "smoothedLine": smoothed_line,
                "basicArea": basic_area,
                "stackedArea": stacked_area,
                "scatter": scatter,
                "calendarHeatmap": calendar_heatmap,
                "multiGauge": multi_gauge,
                "radar": radar,
                "funnel": funnel,
                "tree": tree,
                "sankey": sankey
            },
            "status": "success",
            "chartCount": 11
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}
