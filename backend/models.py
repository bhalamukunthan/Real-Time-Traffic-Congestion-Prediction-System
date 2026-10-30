from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class RoadInformation(Base):
    __tablename__ = "road_information"

    road_id = Column(String(50), primary_key=True, index=True)
    road_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_limit = Column(Integer, nullable=False, default=60)
    lane_count = Column(Integer, nullable=False, default=3)
    length_km = Column(Float, nullable=False, default=5.0)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    events = relationship("TrafficEvent", back_populates="road", cascade="all, delete-orphan")
    metrics = relationship("TrafficMetric", back_populates="road", cascade="all, delete-orphan")
    predictions = relationship("TrafficPrediction", back_populates="road", cascade="all, delete-orphan")
    anomalies = relationship("TrafficAnomaly", back_populates="road", cascade="all, delete-orphan")


class TrafficEvent(Base):
    __tablename__ = "traffic_events"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    road_id = Column(String(50), ForeignKey("road_information.road_id"), nullable=False, index=True)
    road_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    vehicle_count = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)
    traffic_density = Column(Float, nullable=False)
    weather_condition = Column(String(50), nullable=False)
    congestion_level = Column(String(20), nullable=False)
    is_simulated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    road = relationship("RoadInformation", back_populates="events")

    __table_args__ = (
        Index("idx_road_time", "road_id", "timestamp"),
    )


class TrafficMetric(Base):
    __tablename__ = "traffic_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    road_id = Column(String(50), ForeignKey("road_information.road_id"), nullable=False, index=True)
    window_size_seconds = Column(Integer, nullable=False, default=60)
    total_vehicles = Column(Integer, nullable=False)
    rolling_avg_speed = Column(Float, nullable=False)
    current_density = Column(Float, nullable=False)
    avg_density = Column(Float, nullable=False)
    max_density = Column(Float, nullable=False)
    congestion_level = Column(String(20), nullable=False)
    calculated_at = Column(DateTime, default=datetime.now)

    road = relationship("RoadInformation", back_populates="metrics")

    __table_args__ = (
        Index("idx_metrics_road_time", "road_id", "timestamp"),
    )


class TrafficPrediction(Base):
    __tablename__ = "traffic_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    prediction_time = Column(DateTime, nullable=False, default=datetime.now)
    target_time = Column(DateTime, nullable=False, index=True)
    road_id = Column(String(50), ForeignKey("road_information.road_id"), nullable=False, index=True)
    horizon_minutes = Column(Integer, nullable=False, default=15)
    predicted_density = Column(Float, nullable=False)
    predicted_speed = Column(Float, nullable=False)
    predicted_congestion = Column(String(20), nullable=False)
    confidence_score = Column(Float, default=0.85)
    model_version = Column(String(50), default="RandomForest_v1.0")
    created_at = Column(DateTime, default=datetime.now)

    road = relationship("RoadInformation", back_populates="predictions")

    __table_args__ = (
        Index("idx_pred_road_time", "road_id", "target_time"),
    )


class TrafficAnomaly(Base):
    __tablename__ = "traffic_anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    event_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    road_id = Column(String(50), ForeignKey("road_information.road_id"), nullable=False, index=True)
    road_name = Column(String(100), nullable=False)
    vehicle_count = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)
    traffic_density = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    anomaly_reason = Column(String(255), nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.now)

    road = relationship("RoadInformation", back_populates="anomalies")

    __table_args__ = (
        Index("idx_anomaly_time", "timestamp"),
    )
