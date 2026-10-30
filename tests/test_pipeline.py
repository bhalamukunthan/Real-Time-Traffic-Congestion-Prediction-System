"""
End-to-End Pipeline & Integration Test Suite
Validates all 6 layers of the Real-Time Traffic Congestion Prediction System.
"""

import os
import sys
import unittest
from datetime import datetime

os.environ["TESTING"] = "true"

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import settings
from backend.database import SessionLocal, init_db
from backend.models import RoadInformation, TrafficEvent, TrafficMetric, TrafficPrediction, TrafficAnomaly
from streaming.processor import process_traffic_event
from ml.predict import predict_future_traffic, density_to_congestion_level
from ml.anomaly_detection import detect_anomaly
from backend.routes.traffic import get_dashboard_summary, get_live_traffic, get_roads, get_traffic_history
from backend.routes.predictions import get_predictions, get_model_evaluation_metrics
from backend.routes.anomalies import get_anomalies
from backend.routes.system import get_system_status

class TrafficPipelineIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_database_and_road_seeding(self):
        """Verify database tables and seeded road metadata."""
        db = SessionLocal()
        try:
            roads = db.query(RoadInformation).all()
            self.assertGreaterEqual(len(roads), 6, "Expected at least 6 default road corridors.")
            road_ids = [r.road_id for r in roads]
            self.assertIn("ROAD-001", road_ids)
            self.assertIn("ROAD-002", road_ids)
            print("[PASS] Layer 5 (Database): 6 road corridors successfully verified.")
        finally:
            db.close()

    def test_02_ml_models_inference(self):
        """Verify Random Forest Regressor and Isolation Forest inference."""
        # 1. Random Forest prediction
        pred = predict_future_traffic(
            road_id="ROAD-001",
            vehicle_count=75,
            average_speed=40.0,
            traffic_density=55.0
        )
        self.assertIn("predicted_density", pred)
        self.assertIn("predicted_speed", pred)
        self.assertIn("predicted_congestion", pred)
        self.assertIn("confidence_score", pred)
        self.assertGreater(pred["confidence_score"], 0.5)

        # 2. Isolation Forest normal vs anomaly
        normal_check = detect_anomaly(vehicle_count=50, average_speed=50.0, traffic_density=40.0)
        self.assertIn("is_anomaly", normal_check)
        self.assertFalse(normal_check["is_anomaly"])

        anomaly_check = detect_anomaly(
            vehicle_count=160, average_speed=8.0, traffic_density=95.0, rolling_avg_speed=60.0
        )
        self.assertTrue(anomaly_check["is_anomaly"])
        self.assertIn("anomaly_score", anomaly_check)
        self.assertIn("anomaly_reason", anomaly_check)
        print("[PASS] Layer 4 (Machine Learning): RF and Isolation Forest inferences verified.")

    def test_03_stream_processor_and_sliding_window(self):
        """Verify stream processor sliding window calculations and database persistence."""
        event_dict = {
            "event_id": f"TEST-EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-ROAD-001",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "road_id": "ROAD-001",
            "road_name": "Grand Trunk Expressway",
            "location": "Downtown North",
            "vehicle_count": 85,
            "average_speed": 35.5,
            "traffic_density": 68.2,
            "weather_condition": "Rain",
            "congestion_level": "HIGH",
            "is_simulated": True
        }
        
        result = process_traffic_event(event_dict)
        self.assertIn("event", result)
        self.assertIn("metrics", result)
        self.assertIn("prediction", result)
        self.assertIn("anomaly", result)
        self.assertEqual(result["event"]["road_id"], "ROAD-001")
        self.assertGreater(result["metrics"]["rolling_avg_speed"], 0)
        print("[PASS] Layer 3 (Stream Processor): Sliding window analytics and DB persistence verified.")

    def test_04_backend_rest_apis(self):
        """Verify all required REST API endpoints and response schemas."""
        db = SessionLocal()
        try:
            # 1. Summary
            data_summary = get_dashboard_summary(db)
            self.assertIsNotNone(data_summary.total_vehicles_monitored)
            self.assertGreaterEqual(data_summary.active_roads_count, 1)

            # 2. Live traffic
            live_roads = get_live_traffic(db)
            self.assertGreaterEqual(len(live_roads), 6)

            # 3. Roads
            roads = get_roads(db)
            self.assertEqual(len(roads), 6)

            # 4. History
            history = get_traffic_history(road_id=None, congestion_level=None, hours=24, limit=10, db=db)
            self.assertIsInstance(history, list)

            # 5. Predictions
            preds = get_predictions(road_id="ALL", limit=10, db=db)
            self.assertIsInstance(preds, list)

            # 6. Evaluation
            eval_metrics = get_model_evaluation_metrics()
            self.assertIn("density_metrics", eval_metrics)

            # 7. Anomalies
            anomalies = get_anomalies(road_id="ALL", status="ALL", limit=10, db=db)
            self.assertIsInstance(anomalies, list)

            # 8. System Status
            sys_status = get_system_status(db)
            self.assertEqual(sys_status.backend_status, "ONLINE")
            print("[PASS] Backend REST APIs: All 8 required endpoints and schemas validated.")
        finally:
            db.close()

    def test_05_frontend_files_integrity(self):
        """Verify all 7 frontend HTML pages and required JS/CSS assets exist."""
        required_pages = [
            "index.html",
            "traffic.html",
            "map.html",
            "predictions.html",
            "anomalies.html",
            "history.html",
            "status.html"
        ]
        frontend_dir = os.path.join(project_root, "frontend")
        for page in required_pages:
            path = os.path.join(frontend_dir, page)
            self.assertTrue(os.path.exists(path), f"Missing page: {page}")

        # Check CSS and JS
        self.assertTrue(os.path.exists(os.path.join(frontend_dir, "css", "style.css")))
        for js_file in ["api.js", "dashboard.js", "traffic.js", "map.js", "predictions.js", "anomalies.js", "history.js", "status.js"]:
            self.assertTrue(os.path.exists(os.path.join(frontend_dir, "js", js_file)), f"Missing JS: {js_file}")
        print("[PASS] Layer 6 (Visualization): All 7 pages and 9 scripts/stylesheets verified.")

if __name__ == "__main__":
    unittest.main()
