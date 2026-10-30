from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import SystemStatusResponse
from backend.services import traffic_service

router = APIRouter(prefix="/api", tags=["System Status"])

@router.get("/system/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """Fetch live operational health of Kafka streaming, ML models, MySQL, and backend."""
    return traffic_service.get_system_status(db)

