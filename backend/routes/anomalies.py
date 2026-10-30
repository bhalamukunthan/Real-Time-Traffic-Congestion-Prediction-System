from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.schemas import TrafficAnomalyResponse
from backend.services import traffic_service

router = APIRouter(prefix="/api", tags=["Anomalies"])

@router.get("/anomalies", response_model=List[TrafficAnomalyResponse])
def get_anomalies(
    road_id: Optional[str] = Query(None, description="Filter anomalies by Road ID"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. ACTIVE, RESOLVED)"),
    limit: int = Query(100, ge=1, le=500, description="Max anomalies to return"),
    db: Session = Depends(get_db)
):
    """Retrieve unusual traffic patterns flagged by Isolation Forest & real-time rules."""
    return traffic_service.get_anomalies_list(db, road_id=road_id, status=status, limit=limit)

