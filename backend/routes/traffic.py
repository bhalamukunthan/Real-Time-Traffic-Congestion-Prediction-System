from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.schemas import (
    DashboardSummaryResponse,
    RoadLiveStatus,
    RoadInfoSchema,
    TrafficEventResponse
)
from backend.services import traffic_service

router = APIRouter(prefix="/api", tags=["Traffic Analytics"])

@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Fetch aggregated KPIs, charts data, and road statuses for the Overview Dashboard."""
    return traffic_service.get_dashboard_summary(db)

@router.get("/traffic/live", response_model=List[RoadLiveStatus])
def get_live_traffic(db: Session = Depends(get_db)):
    """Fetch live traffic metrics across all urban road corridors."""
    return traffic_service.get_live_road_statuses(db)

@router.get("/traffic/roads", response_model=List[RoadInfoSchema])
def get_roads(db: Session = Depends(get_db)):
    """Fetch static metadata, geographic coordinates, and limits of monitored roads."""
    return traffic_service.get_all_roads(db)

@router.get("/traffic/history", response_model=List[TrafficEventResponse])
def get_traffic_history(
    road_id: Optional[str] = Query(None, description="Filter by Road ID (e.g. ROAD-001)"),
    congestion_level: Optional[str] = Query(None, description="Filter by Congestion Level (LOW, MEDIUM, HIGH, SEVERE)"),
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    limit: int = Query(200, ge=1, le=1000, description="Max number of records"),
    db: Session = Depends(get_db)
):
    """Fetch historical traffic time-series events with filtering support."""
    return traffic_service.get_traffic_history(
        db, road_id=road_id, congestion_level=congestion_level, hours=hours, limit=limit
    )

