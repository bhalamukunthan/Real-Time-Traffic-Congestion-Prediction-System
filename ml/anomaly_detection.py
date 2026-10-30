"""
Traffic Anomaly Detection Module
Uses Isolation Forest to detect anomalous traffic events and patterns
in real time, providing diagnostic reasoning for traffic operators.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")
ISO_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "isolation_forest.joblib")

_iso_model = None

def get_isolation_model():
    """Loads and caches the Isolation Forest model."""
    global _iso_model
    if _iso_model is None:
        if not os.path.exists(ISO_MODEL_PATH):
            raise FileNotFoundError(
                f"Isolation Forest model artifact not found at {ISO_MODEL_PATH}. Run ml/train_model.py first."
            )
        _iso_model = joblib.load(ISO_MODEL_PATH)
    return _iso_model

def detect_anomaly(
    vehicle_count: int,
    average_speed: float,
    traffic_density: float,
    rolling_avg_speed: Optional[float] = None
) -> Dict[str, Any]:
    """
    Detects whether the incoming traffic event is anomalous.
    Returns boolean is_anomaly, anomaly_score, and an interpretable reason.
    """
    model = get_isolation_model()
    
    features = np.array([[vehicle_count, average_speed, traffic_density]], dtype=float)
    
    # predict returns -1 for anomaly, 1 for normal
    raw_pred = model.predict(features)[0]
    is_anomaly = bool(raw_pred == -1)
    
    # decision_function gives anomaly score (lower is more anomalous)
    raw_score = float(model.decision_function(features)[0])
    
    # Check heuristic rule-based anomalies in conjunction with isolation forest
    rule_reasons = []
    if rolling_avg_speed and (rolling_avg_speed - average_speed) > 20:
        rule_reasons.append(f"Sudden sharp speed drop ({average_speed:.1f} vs rolling {rolling_avg_speed:.1f} km/h)")
    if average_speed < 15.0 and traffic_density > 75.0:
        rule_reasons.append("Critical standstill bottleneck detected (potential accident or obstruction)")
    if vehicle_count > 120 and traffic_density > 80.0:
        rule_reasons.append("Unusual sudden vehicle volume spike exceeding 90th percentile")
    if average_speed > 95.0:
        rule_reasons.append("Severe highway overspeeding / hazardous driving pattern")
    if traffic_density > 90.0:
        rule_reasons.append("Near total gridlock density reached on road segment")
        
    if rule_reasons:
        is_anomaly = True

    # Normalized score between 0.0 (normal) and 1.0 (highly anomalous)
    normalized_score = max(0.0, min(1.0, 0.5 - raw_score))
    if is_anomaly:
        normalized_score = max(normalized_score, 0.72)
    
    reason = "Normal traffic flow parameters."
    if is_anomaly:
        if rule_reasons:
            reason = "; ".join(rule_reasons)
        else:
            reason = "Statistically significant divergence from historic traffic flow envelope (Isolation Forest)"
            
    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": round(normalized_score, 4),
        "anomaly_reason": reason
    }

if __name__ == "__main__":
    normal_test = detect_anomaly(50, 48.0, 45.0)
    print("Normal test:", normal_test)
    anomaly_test = detect_anomaly(160, 10.0, 95.0, rolling_avg_speed=55.0)
    print("Anomaly test:", anomaly_test)
