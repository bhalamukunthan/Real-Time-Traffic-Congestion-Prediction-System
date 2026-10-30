from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RoadInfoSchema(BaseModel):
    road_id: str
    road_name: str
    location: str
    latitude: float
    longitude: float
    speed_limit: int
    lane_count: int
    length_km: float

    class Config:
        from_attributes = True


class TrafficEventCreate(BaseModel):
    event_id: str
    timestamp: datetime
    road_id: str
    road_name: str
    location: str
    vehicle_count: int = Field(ge=0)
    average_speed: float = Field(ge=0.0)
    traffic_density: float = Field(ge=0.0, le=100.0)
    weather_condition: str
    congestion_level: str
    is_simulated: bool = True


class TrafficEventResponse(TrafficEventCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TrafficMetricResponse(BaseModel):
    id: int
    timestamp: datetime
    road_id: str
    window_size_seconds: int
    total_vehicles: int
    rolling_avg_speed: float
    current_density: float
    avg_density: float
    max_density: float
    congestion_level: str

    class Config:
        from_attributes = True


class TrafficPredictionResponse(BaseModel):
    id: Optional[int] = None
    prediction_time: datetime
    target_time: datetime
    road_id: str
    road_name: Optional[str] = None
    horizon_minutes: int
    predicted_density: float
    predicted_speed: float
    predicted_congestion: str
    confidence_score: float
    model_version: str

    class Config:
        from_attributes = True


class TrafficAnomalyResponse(BaseModel):
    id: int
    event_id: str
    timestamp: datetime
    road_id: str
    road_name: str
    vehicle_count: int
    average_speed: float
    traffic_density: float
    anomaly_score: float
    anomaly_reason: str
    status: str

    class Config:
        from_attributes = True


class RoadLiveStatus(BaseModel):
    road_id: str
    road_name: str
    location: str
    latitude: float
    longitude: float
    vehicle_count: int
    average_speed: float
    traffic_density: float
    congestion_level: str
    last_updated: datetime
    predicted_congestion: Optional[str] = None


class DashboardSummaryResponse(BaseModel):
    total_vehicles_monitored: int
    average_speed_network: float
    active_roads_count: int
    congested_roads_count: int
    average_density_network: float
    active_alerts_count: int
    roads_status: List[RoadLiveStatus]
    recent_events: List[TrafficEventResponse]
    recent_anomalies: List[TrafficAnomalyResponse]
    congestion_distribution: Dict[str, int]
    last_event_time: Optional[datetime] = None


class ModelMetricEvaluation(BaseModel):
    model_name: str
    mae: float
    rmse: float
    r2_score: float
    trained_at: str
    samples_count: int


class SystemStatusResponse(BaseModel):
    kafka_producer_status: str
    kafka_consumer_status: str
    backend_status: str
    database_status: str
    database_type: str
    ml_model_status: str
    last_received_event_time: Optional[datetime] = None
    uptime_seconds: float
    events_processed_count: int
    anomalies_detected_count: int

