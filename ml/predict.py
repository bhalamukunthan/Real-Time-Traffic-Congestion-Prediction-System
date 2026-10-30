"""
Machine Learning Inference Module
Loads pre-trained Random Forest Regressors to predict 15-minute future
traffic density, speed, and congestion category with confidence scoring.
"""

import os
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")
RF_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "random_forest_regressor.joblib")
SCALER_PATH = os.path.join(SAVED_MODELS_DIR, "feature_scaler.joblib")

_model_cache = None

def get_ml_models():
    """Loads and caches the Random Forest bundle and Scaler."""
    global _model_cache
    if _model_cache is None:
        if not os.path.exists(RF_MODEL_PATH) or not os.path.exists(SCALER_PATH):
            raise FileNotFoundError(
                f"Trained model artifacts not found at {SAVED_MODELS_DIR}. Run ml/train_model.py first."
            )
        rf_bundle = joblib.load(RF_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        _model_cache = (rf_bundle, scaler)
    return _model_cache

def density_to_congestion_level(density: float) -> str:
    """Classifies density into standard traffic congestion tiers."""
    if density < 35.0:
        return "LOW"
    elif density < 65.0:
        return "MEDIUM"
    elif density < 85.0:
        return "HIGH"
    else:
        return "SEVERE"

def predict_future_traffic(
    road_id: str,
    vehicle_count: int,
    average_speed: float,
    traffic_density: float,
    timestamp: datetime = None
) -> Dict[str, Any]:
    """
    Predicts traffic density and speed 15 minutes into the future.
    Computes ensemble variance to estimate a confidence score.
    """
    if timestamp is None:
        timestamp = datetime.now()
        
    rf_bundle, scaler = get_ml_models()
    rf_density = rf_bundle["density_model"]
    rf_speed = rf_bundle["speed_model"]
    road_map = rf_bundle.get("road_map", {})
    
    road_code = road_map.get(road_id, 0)
    hour = timestamp.hour
    day_of_week = timestamp.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    
    raw_features = np.array([[
        road_code,
        hour,
        day_of_week,
        is_weekend,
        vehicle_count,
        average_speed,
        traffic_density
    ]], dtype=float)
    
    scaled_features = scaler.transform(raw_features)
    
    # Prediction from ensemble
    pred_density = float(rf_density.predict(scaled_features)[0])
    pred_speed = float(rf_speed.predict(scaled_features)[0])
    
    # Bound predictions within realistic domain
    pred_density = max(2.0, min(100.0, pred_density))
    pred_speed = max(5.0, min(120.0, pred_speed))
    
    # Calculate confidence from tree standard deviation
    # Lower standard deviation across trees implies higher confidence
    tree_preds = [tree.predict(scaled_features)[0] for tree in rf_density.estimators_]
    tree_std = float(np.std(tree_preds))
    # Normalized confidence score (scale 0.5 to 0.98)
    confidence = max(0.50, min(0.98, 1.0 - (tree_std / 50.0)))
    
    pred_congestion = density_to_congestion_level(pred_density)
    
    return {
        "road_id": road_id,
        "horizon_minutes": 15,
        "predicted_density": round(pred_density, 2),
        "predicted_speed": round(pred_speed, 2),
        "predicted_congestion": pred_congestion,
        "confidence_score": round(confidence, 3),
        "model_version": rf_bundle.get("version", "RandomForest_v1.0")
    }

if __name__ == "__main__":
    test_pred = predict_future_traffic("ROAD-001", 60, 45.0, 52.0)
    print("Inference Test Result:", test_pred)
