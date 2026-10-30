"""
Real-Time Stream Processor
Performs rolling window analytics, congestion classification, ML inference,
and database persistence for high-throughput traffic telemetry streams.
"""

import logging
from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal
from backend.models import TrafficEvent, TrafficMetric, TrafficPrediction, TrafficAnomaly
from ml.predict import predict_future_traffic, density_to_congestion_level
from ml.anomaly_detection import detect_anomaly

logger = logging.getLogger("stream_processor")

class StreamMetricsTracker:
    """Tracks global runtime statistics for the stream processor."""
    def __init__(self):
        self.events_processed = 0
        self.anomalies_detected = 0
        self.last_event_time = None
        self.start_time = datetime.now()

metrics_tracker = StreamMetricsTracker()

# In-memory sliding windows per road
# Holds last N events for each road_id to calculate real-time window metrics
WINDOW_SIZE = settings.TRAFFIC_SLIDING_WINDOW_EVENTS
road_windows: Dict[str, deque] = {}

# Active WebSocket broadcast callbacks
_ws_broadcasters: List[Any] = []

def register_ws_broadcaster(callback):
    """Register WebSocket broadcast handler from FastAPI."""
    if callback not in _ws_broadcasters:
        _ws_broadcasters.append(callback)

def unregister_ws_broadcaster(callback):
    if callback in _ws_broadcasters:
        _ws_broadcasters.remove(callback)

def process_traffic_event(event_dict: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Core Stream Processing Pipeline:
    1. Validates and parses incoming raw traffic event.
    2. Updates sliding window and computes rolling metrics.
    3. Executes Random Forest Regressor for 15-minute future prediction.
    4. Executes Isolation Forest for pattern anomaly detection.
    5. Saves state to MySQL / Database.
    6. Broadcasts real-time payload to connected dashboards.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        road_id = event_dict.get("road_id")
        road_name = event_dict.get("road_name", "Unknown Road")
        location = event_dict.get("location", "Urban Sector")
        vehicle_count = int(event_dict.get("vehicle_count", 0))
        average_speed = float(event_dict.get("average_speed", 50.0))
        traffic_density = float(event_dict.get("traffic_density", 25.0))
        weather_condition = event_dict.get("weather_condition", "Clear")
        
        # Parse timestamp safely
        ts_raw = event_dict.get("timestamp")
        if isinstance(ts_raw, str):
            try:
                event_time = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                event_time = datetime.now()
        elif isinstance(ts_raw, datetime):
            event_time = ts_raw
        else:
            event_time = datetime.now()

        # Update global tracker
        metrics_tracker.events_processed += 1
        metrics_tracker.last_event_time = event_time

        # -----------------------------------------------------------------
        # 1. Sliding Window & Real-time Metrics Calculation
        # -----------------------------------------------------------------
        if road_id not in road_windows:
            road_windows[road_id] = deque(maxlen=WINDOW_SIZE)
            
        road_windows[road_id].append({
            "timestamp": event_time,
            "vehicle_count": vehicle_count,
            "average_speed": average_speed,
            "traffic_density": traffic_density
        })
        
        window = list(road_windows[road_id])
        total_vehicles_in_window = sum(item["vehicle_count"] for item in window)
        rolling_avg_speed = round(sum(item["average_speed"] for item in window) / len(window), 2)
        avg_density = round(sum(item["traffic_density"] for item in window) / len(window), 2)
        max_density = round(max(item["traffic_density"] for item in window), 2)
        
        current_congestion = density_to_congestion_level(traffic_density)

        # -----------------------------------------------------------------
        # 2. Machine Learning Predictions (Random Forest Regressor)
        # -----------------------------------------------------------------
        ml_prediction = predict_future_traffic(
            road_id=road_id,
            vehicle_count=vehicle_count,
            average_speed=average_speed,
            traffic_density=traffic_density,
            timestamp=event_time
        )
        target_time = event_time + timedelta(minutes=ml_prediction["horizon_minutes"])

        # -----------------------------------------------------------------
        # 3. Anomaly Detection (Isolation Forest)
        # -----------------------------------------------------------------
        anomaly_result = detect_anomaly(
            vehicle_count=vehicle_count,
            average_speed=average_speed,
            traffic_density=traffic_density,
            rolling_avg_speed=rolling_avg_speed
        )
        if anomaly_result["is_anomaly"]:
            metrics_tracker.anomalies_detected += 1

        # -----------------------------------------------------------------
        # 4. Database Persistence (MySQL / SQLAlchemy)
        # -----------------------------------------------------------------
        # A. Save Traffic Event
        db_event = TrafficEvent(
            event_id=event_dict.get("event_id", f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{road_id}"),
            timestamp=event_time,
            road_id=road_id,
            road_name=road_name,
            location=location,
            vehicle_count=vehicle_count,
            average_speed=average_speed,
            traffic_density=traffic_density,
            weather_condition=weather_condition,
            congestion_level=current_congestion,
            is_simulated=event_dict.get("is_simulated", True)
        )
        db.add(db_event)

        # B. Save Stream Metric
        db_metric = TrafficMetric(
            timestamp=event_time,
            road_id=road_id,
            window_size_seconds=60,
            total_vehicles=total_vehicles_in_window,
            rolling_avg_speed=rolling_avg_speed,
            current_density=traffic_density,
            avg_density=avg_density,
            max_density=max_density,
            congestion_level=current_congestion
        )
        db.add(db_metric)

        # C. Save Prediction
        db_pred = TrafficPrediction(
            prediction_time=event_time,
            target_time=target_time,
            road_id=road_id,
            horizon_minutes=ml_prediction["horizon_minutes"],
            predicted_density=ml_prediction["predicted_density"],
            predicted_speed=ml_prediction["predicted_speed"],
            predicted_congestion=ml_prediction["predicted_congestion"],
            confidence_score=ml_prediction["confidence_score"],
            model_version=ml_prediction["model_version"]
        )
        db.add(db_pred)

        # D. Save Anomaly if flagged
        db_anomaly = None
        if anomaly_result["is_anomaly"]:
            db_anomaly = TrafficAnomaly(
                event_id=db_event.event_id,
                timestamp=event_time,
                road_id=road_id,
                road_name=road_name,
                vehicle_count=vehicle_count,
                average_speed=average_speed,
                traffic_density=traffic_density,
                anomaly_score=anomaly_result["anomaly_score"],
                anomaly_reason=anomaly_result["anomaly_reason"],
                status="ACTIVE"
            )
            db.add(db_anomaly)

        db.commit()

        # -----------------------------------------------------------------
        # 5. Build Processed Real-Time Payload & Notify Subscribers
        # -----------------------------------------------------------------
        processed_payload = {
            "type": "traffic_update",
            "event": {
                "event_id": db_event.event_id,
                "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "road_id": road_id,
                "road_name": road_name,
                "location": location,
                "vehicle_count": vehicle_count,
                "average_speed": average_speed,
                "traffic_density": traffic_density,
                "weather_condition": weather_condition,
                "congestion_level": current_congestion
            },
            "metrics": {
                "rolling_avg_speed": rolling_avg_speed,
                "avg_density": avg_density,
                "max_density": max_density,
                "total_vehicles_in_window": total_vehicles_in_window
            },
            "prediction": {
                "road_id": road_id,
                "horizon_minutes": ml_prediction["horizon_minutes"],
                "target_time": target_time.strftime("%Y-%m-%d %H:%M:%S"),
                "predicted_density": ml_prediction["predicted_density"],
                "predicted_speed": ml_prediction["predicted_speed"],
                "predicted_congestion": ml_prediction["predicted_congestion"],
                "confidence_score": ml_prediction["confidence_score"]
            },
            "anomaly": {
                "is_anomaly": anomaly_result["is_anomaly"],
                "anomaly_score": anomaly_result["anomaly_score"],
                "anomaly_reason": anomaly_result["anomaly_reason"]
            }
        }

        # Dispatch to any registered WebSocket clients asynchronously
        for broadcaster in list(_ws_broadcasters):
            try:
                broadcaster(processed_payload)
            except Exception as e:
                logger.debug("Broadcaster callback error: %s", e)

        return processed_payload

    except Exception as e:
        if db:
            db.rollback()
        logger.error("Error processing traffic event: %s", e, exc_info=True)
        return {"error": str(e)}
    finally:
        if should_close_db and db:
            db.close()

