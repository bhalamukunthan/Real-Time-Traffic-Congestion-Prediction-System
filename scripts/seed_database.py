"""
Database Historical Seeder
Seeds historical events from dataset/traffic_data.csv into the database tables
(traffic_events, traffic_metrics, traffic_predictions, traffic_anomalies)
so that historical analytics and charts are populated immediately upon first launch.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal, init_db
from backend.models import RoadInformation, TrafficEvent, TrafficMetric, TrafficPrediction, TrafficAnomaly
from ml.predict import predict_future_traffic, density_to_congestion_level
from ml.anomaly_detection import detect_anomaly

def seed_database_from_csv(csv_path: str = None, max_records: int = 500):
    if csv_path is None:
        csv_path = os.path.join(project_root, "dataset", "traffic_data.csv")

    if not os.path.exists(csv_path):
        print(f"Dataset not found at {csv_path}. Run dataset/generate_dataset.py first.")
        return

    print("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        existing_count = db.query(TrafficEvent).count()
        if existing_count >= max_records:
            print(f"Database already contains {existing_count} events. Skipping historical seed.")
            return

        print(f"Loading records from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Take the most recent records
        sample_df = df.tail(max_records)
        print(f"Seeding {len(sample_df)} historical records into database...")

        events_to_add = []
        metrics_to_add = []
        preds_to_add = []
        anomalies_to_add = []

        for _, row in sample_df.iterrows():
            try:
                event_time = datetime.strptime(str(row["timestamp"]), "%Y-%m-%d %H:%M:%S")
            except Exception:
                event_time = datetime.now()

            road_id = str(row["road_id"])
            road_name = str(row["road_name"])
            location = str(row["location"])
            vehicle_count = int(row["vehicle_count"])
            average_speed = float(row["average_speed"])
            traffic_density = float(row["traffic_density"])
            weather = str(row.get("weather_condition", "Clear"))
            congestion = str(row["congestion_level"])

            # 1. Event
            evt = TrafficEvent(
                event_id=str(row["event_id"]),
                timestamp=event_time,
                road_id=road_id,
                road_name=road_name,
                location=location,
                vehicle_count=vehicle_count,
                average_speed=average_speed,
                traffic_density=traffic_density,
                weather_condition=weather,
                congestion_level=congestion,
                is_simulated=True
            )
            events_to_add.append(evt)

            # 2. Metric
            met = TrafficMetric(
                timestamp=event_time,
                road_id=road_id,
                window_size_seconds=60,
                total_vehicles=vehicle_count,
                rolling_avg_speed=average_speed,
                current_density=traffic_density,
                avg_density=traffic_density,
                max_density=traffic_density,
                congestion_level=congestion
            )
            metrics_to_add.append(met)

            # 3. Prediction (15-min horizon)
            target_time = event_time + timedelta(minutes=15)
            pred_density = min(100.0, max(5.0, traffic_density * 1.05))
            pred_speed = max(10.0, average_speed * 0.95)
            pred_congestion = density_to_congestion_level(pred_density)
            pred = TrafficPrediction(
                prediction_time=event_time,
                target_time=target_time,
                road_id=road_id,
                horizon_minutes=15,
                predicted_density=round(pred_density, 2),
                predicted_speed=round(pred_speed, 2),
                predicted_congestion=pred_congestion,
                confidence_score=0.85,
                model_version="RandomForest_v1.0"
            )
            preds_to_add.append(pred)

            # 4. Anomaly check
            ano_check = detect_anomaly(vehicle_count, average_speed, traffic_density)
            if ano_check["is_anomaly"]:
                ano = TrafficAnomaly(
                    event_id=evt.event_id,
                    timestamp=event_time,
                    road_id=road_id,
                    road_name=road_name,
                    vehicle_count=vehicle_count,
                    average_speed=average_speed,
                    traffic_density=traffic_density,
                    anomaly_score=ano_check["anomaly_score"],
                    anomaly_reason=ano_check["anomaly_reason"],
                    status="ACTIVE"
                )
                anomalies_to_add.append(ano)

        # Batch insert
        db.bulk_save_objects(events_to_add)
        db.bulk_save_objects(metrics_to_add)
        db.bulk_save_objects(preds_to_add)
        db.bulk_save_objects(anomalies_to_add)
        db.commit()

        print(f"[OK] Seeded {len(events_to_add)} events, {len(metrics_to_add)} metrics, {len(preds_to_add)} predictions, and {len(anomalies_to_add)} anomalies into database.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database_from_csv()

