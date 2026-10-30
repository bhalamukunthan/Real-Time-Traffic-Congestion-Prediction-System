"""
Traffic Service Layer
Encapsulates all database query logic, KPI rollups, and time-series aggregation.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.config import settings
from backend.models import RoadInformation, TrafficEvent, TrafficMetric, TrafficPrediction, TrafficAnomaly
from backend.schemas import (
    RoadLiveStatus,
    DashboardSummaryResponse,
    TrafficEventResponse,
    TrafficAnomalyResponse,
    TrafficPredictionResponse,
    SystemStatusResponse
)
from streaming.processor import metrics_tracker

def get_all_roads(db: Session) -> List[Dict[str, Any]]:
    """Retrieve all road corridor records."""
    roads = db.query(RoadInformation).all()
    return [
        {
            "road_id": r.road_id,
            "road_name": r.road_name,
            "location": r.location,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "speed_limit": r.speed_limit,
            "lane_count": r.lane_count,
            "length_km": r.length_km
        }
        for r in roads
    ]

def get_live_road_statuses(db: Session) -> List[RoadLiveStatus]:
    """
    Computes current status for every road by querying the latest event,
    metric, and future prediction.
    """
    roads = db.query(RoadInformation).all()
    statuses = []

    for road in roads:
        # Get latest event for this road
        latest_event = (
            db.query(TrafficEvent)
            .filter(TrafficEvent.road_id == road.road_id)
            .order_by(desc(TrafficEvent.timestamp))
            .first()
        )
        
        # Get latest prediction
        latest_pred = (
            db.query(TrafficPrediction)
            .filter(TrafficPrediction.road_id == road.road_id)
            .order_by(desc(TrafficPrediction.prediction_time))
            .first()
        )

        if latest_event:
            statuses.append(RoadLiveStatus(
                road_id=road.road_id,
                road_name=road.road_name,
                location=road.location,
                latitude=road.latitude,
                longitude=road.longitude,
                vehicle_count=latest_event.vehicle_count,
                average_speed=latest_event.average_speed,
                traffic_density=latest_event.traffic_density,
                congestion_level=latest_event.congestion_level,
                last_updated=latest_event.timestamp,
                predicted_congestion=latest_pred.predicted_congestion if latest_pred else "LOW"
            ))
        else:
            # Fallback default when no event has streamed yet
            statuses.append(RoadLiveStatus(
                road_id=road.road_id,
                road_name=road.road_name,
                location=road.location,
                latitude=road.latitude,
                longitude=road.longitude,
                vehicle_count=0,
                average_speed=float(road.speed_limit),
                traffic_density=0.0,
                congestion_level="LOW",
                last_updated=datetime.now(),
                predicted_congestion="LOW"
            ))

    return statuses

def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    """Computes full high-level KPIs and summary for the main overview dashboard."""
    statuses = get_live_road_statuses(db)
    
    total_vehicles = sum(s.vehicle_count for s in statuses)
    active_roads = len([s for s in statuses if s.vehicle_count > 0]) or len(statuses)
    
    avg_speed = round(
        sum(s.average_speed for s in statuses) / len(statuses), 1
    ) if statuses else 55.0
    
    avg_density = round(
        sum(s.traffic_density for s in statuses) / len(statuses), 1
    ) if statuses else 20.0
    
    congested_count = len([s for s in statuses if s.congestion_level in ["HIGH", "SEVERE"]])
    
    # Congestion breakdown
    congestion_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "SEVERE": 0}
    for s in statuses:
        congestion_dist[s.congestion_level] = congestion_dist.get(s.congestion_level, 0) + 1

    # Recent events (last 10)
    recent_events_db = (
        db.query(TrafficEvent)
        .order_by(desc(TrafficEvent.timestamp))
        .limit(10)
        .all()
    )
    recent_events = [TrafficEventResponse.model_validate(e) for e in recent_events_db]

    # Recent active anomalies (last 10)
    recent_anomalies_db = (
        db.query(TrafficAnomaly)
        .order_by(desc(TrafficAnomaly.timestamp))
        .limit(10)
        .all()
    )
    recent_anomalies = [TrafficAnomalyResponse.model_validate(a) for a in recent_anomalies_db]

    active_alerts_count = db.query(TrafficAnomaly).filter(TrafficAnomaly.status == "ACTIVE").count()

    last_event = db.query(TrafficEvent).order_by(desc(TrafficEvent.timestamp)).first()
    last_event_time = last_event.timestamp if last_event else None

    return DashboardSummaryResponse(
        total_vehicles_monitored=total_vehicles,
        average_speed_network=avg_speed,
        active_roads_count=active_roads,
        congested_roads_count=congested_count,
        average_density_network=avg_density,
        active_alerts_count=active_alerts_count,
        roads_status=statuses,
        recent_events=recent_events,
        recent_anomalies=recent_anomalies,
        congestion_distribution=congestion_dist,
        last_event_time=last_event_time
    )

def get_traffic_history(
    db: Session,
    road_id: Optional[str] = None,
    congestion_level: Optional[str] = None,
    hours: int = 24,
    limit: int = 200
) -> List[TrafficEventResponse]:
    """Retrieve filtered historical events."""
    query = db.query(TrafficEvent)
    
    if road_id and road_id.upper() != "ALL":
        query = query.filter(TrafficEvent.road_id == road_id)
        
    if congestion_level and congestion_level.upper() != "ALL":
        query = query.filter(TrafficEvent.congestion_level == congestion_level.upper())
        
    if hours > 0:
        since = datetime.now() - timedelta(hours=hours)
        query = query.filter(TrafficEvent.timestamp >= since)
        
    events = query.order_by(desc(TrafficEvent.timestamp)).limit(limit).all()
    return [TrafficEventResponse.model_validate(e) for e in events]

def get_predictions_list(
    db: Session,
    road_id: Optional[str] = None,
    limit: int = 50
) -> List[TrafficPredictionResponse]:
    """Retrieve recent traffic predictions."""
    query = db.query(TrafficPrediction)
    if road_id and road_id.upper() != "ALL":
        query = query.filter(TrafficPrediction.road_id == road_id)
        
    preds = query.order_by(desc(TrafficPrediction.prediction_time)).limit(limit).all()
    results = []
    # Join with road name
    roads_map = {r.road_id: r.road_name for r in db.query(RoadInformation).all()}
    for p in preds:
        res = TrafficPredictionResponse.model_validate(p)
        res.road_name = roads_map.get(p.road_id, p.road_id)
        results.append(res)
    return results

def get_anomalies_list(
    db: Session,
    road_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[TrafficAnomalyResponse]:
    """Retrieve detected unusual traffic events."""
    query = db.query(TrafficAnomaly)
    if road_id and road_id.upper() != "ALL":
        query = query.filter(TrafficAnomaly.road_id == road_id)
    if status and status.upper() != "ALL":
        query = query.filter(TrafficAnomaly.status == status.upper())
        
    anomalies = query.order_by(desc(TrafficAnomaly.timestamp)).limit(limit).all()
    return [TrafficAnomalyResponse.model_validate(a) for a in anomalies]

def get_system_status(db: Session) -> SystemStatusResponse:
    """Retrieve runtime statuses of Kafka, DB, Backend, and ML models."""
    uptime = (datetime.now() - metrics_tracker.start_time).total_seconds()
    
    # DB test
    db_status = "ONLINE"
    db_type = "MySQL" if "mysql" in settings.DATABASE_URL.lower() else "SQLite"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "OFFLINE"

    # ML model check
    ml_status = "ONLINE (Ready)"
    metrics_file = settings.METRICS_PATH
    if not os.path.exists(settings.RF_MODEL_PATH) or not os.path.exists(settings.ISO_MODEL_PATH):
        ml_status = "DEGRADED (Model files missing)"

    # Producer & Consumer Status
    kafka_prod_status = "ACTIVE" if metrics_tracker.events_processed > 0 else "READY / IDLE"
    kafka_cons_status = "ACTIVE" if metrics_tracker.events_processed > 0 else "READY / IDLE"

    return SystemStatusResponse(
        kafka_producer_status=kafka_prod_status,
        kafka_consumer_status=kafka_cons_status,
        backend_status="ONLINE",
        database_status=db_status,
        database_type=db_type,
        ml_model_status=ml_status,
        last_received_event_time=metrics_tracker.last_event_time,
        uptime_seconds=round(uptime, 1),
        events_processed_count=metrics_tracker.events_processed,
        anomalies_detected_count=metrics_tracker.anomalies_detected
    )

