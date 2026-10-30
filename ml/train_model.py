"""
Machine Learning Training Pipeline
Trains:
1. Random Forest Regressor for 15-minute ahead Traffic Density & Speed Prediction.
2. Isolation Forest for Real-Time Traffic Anomaly & Pattern Detection.
Evaluates both models with rigorous metrics and saves artifacts via Joblib.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "traffic_data.csv")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")

ROAD_ID_MAP = {
    "ROAD-001": 1,
    "ROAD-002": 2,
    "ROAD-003": 3,
    "ROAD-004": 4,
    "ROAD-005": 5,
    "ROAD-006": 6
}

def train_and_evaluate_models():
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
    print("==================================================")
    print("TRAFFIC ML TRAINING & EVALUATION PIPELINE")
    print("==================================================")
    
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}. Run dataset/generate_dataset.py first.")

    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded dataset: {len(df)} records from {DATASET_PATH}")
    
    # 1. Feature Engineering
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["road_id", "timestamp"]).reset_index(drop=True)
    
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_of_week
    df["is_weekend"] = df["day_of_week"].apply(lambda x: 1 if x >= 5 else 0)
    df["road_code"] = df["road_id"].map(ROAD_ID_MAP).fillna(0)
    
    # Target Construction: 15-minute future traffic density & speed
    # Group by road to prevent lookahead leakage across roads
    df["target_future_density"] = df.groupby("road_id")["traffic_density"].shift(-1)
    df["target_future_speed"] = df.groupby("road_id")["average_speed"].shift(-1)
    
    # Drop records where target is NaN (end of each road series)
    clean_df = df.dropna(subset=["target_future_density", "target_future_speed"]).copy()
    
    feature_cols = [
        "road_code",
        "hour",
        "day_of_week",
        "is_weekend",
        "vehicle_count",
        "average_speed",
        "traffic_density"
    ]
    
    X = clean_df[feature_cols].values
    y_density = clean_df["target_future_density"].values
    y_speed = clean_df["target_future_speed"].values
    
    # Train / Test Split (80% train, 20% holdout test)
    X_train, X_test, y_dens_train, y_dens_test, y_spd_train, y_spd_test = train_test_split(
        X, y_density, y_speed, test_size=0.20, random_state=42, shuffle=True
    )
    
    # Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # -----------------------------------------------------------------
    # MODEL 1: Random Forest Regressor (Multi-output: Density and Speed)
    # -----------------------------------------------------------------
    print("\nTraining Random Forest Regressors for Congestion & Speed...")
    rf_density = RandomForestRegressor(
        n_estimators=120,
        max_depth=14,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rf_density.fit(X_train_scaled, y_dens_train)
    
    rf_speed = RandomForestRegressor(
        n_estimators=120,
        max_depth=14,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rf_speed.fit(X_train_scaled, y_spd_train)
    
    # Evaluation on Holdout Test Set
    pred_dens_test = rf_density.predict(X_test_scaled)
    pred_spd_test = rf_speed.predict(X_test_scaled)
    
    dens_mae = float(mean_absolute_error(y_dens_test, pred_dens_test))
    dens_rmse = float(root_mean_squared_error(y_dens_test, pred_dens_test))
    dens_r2 = float(r2_score(y_dens_test, pred_dens_test))
    
    spd_mae = float(mean_absolute_error(y_spd_test, pred_spd_test))
    spd_rmse = float(root_mean_squared_error(y_spd_test, pred_spd_test))
    spd_r2 = float(r2_score(y_spd_test, pred_spd_test))
    
    print("\n[Random Forest Density Evaluation on Test Data]")
    print(f"  MAE:  {dens_mae:.3f}%")
    print(f"  RMSE: {dens_rmse:.3f}%")
    print(f"  R2:   {dens_r2:.4f}")

    print("\n[Random Forest Speed Evaluation on Test Data]")
    print(f"  MAE:  {spd_mae:.3f} km/h")
    print(f"  RMSE: {spd_rmse:.3f} km/h")
    print(f"  R2:   {spd_r2:.4f}")

    # -----------------------------------------------------------------
    # MODEL 2: Isolation Forest (Traffic Anomaly Detection)
    # -----------------------------------------------------------------
    print("\nTraining Isolation Forest for Traffic Anomaly Detection...")
    anomaly_features = clean_df[["vehicle_count", "average_speed", "traffic_density"]].values
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.035, # ~3.5% expected synthetic anomalies
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(anomaly_features)
    
    # Evaluation summary
    test_anomaly_preds = iso_forest.predict(anomaly_features)
    detected_anomalies_count = int(np.sum(test_anomaly_preds == -1))
    print(f"Isolation Forest identified {detected_anomalies_count} anomalies out of {len(clean_df)} events ({detected_anomalies_count/len(clean_df)*100:.2f}%)")

    # -----------------------------------------------------------------
    # Save Model Artifacts
    # -----------------------------------------------------------------
    rf_bundle = {
        "density_model": rf_density,
        "speed_model": rf_speed,
        "features": feature_cols,
        "road_map": ROAD_ID_MAP,
        "version": "RandomForest_v1.0"
    }
    
    rf_path = os.path.join(SAVED_MODELS_DIR, "random_forest_regressor.joblib")
    iso_path = os.path.join(SAVED_MODELS_DIR, "isolation_forest.joblib")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "feature_scaler.joblib")
    metrics_path = os.path.join(SAVED_MODELS_DIR, "model_metrics.json")
    
    joblib.dump(rf_bundle, rf_path)
    joblib.dump(iso_forest, iso_path)
    joblib.dump(scaler, scaler_path)
    
    metrics = {
        "model_version": "RandomForest_v1.0 + IsolationForest_v1.0",
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_dataset_rows": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "density_metrics": {
            "mae": round(dens_mae, 3),
            "rmse": round(dens_rmse, 3),
            "r2_score": round(dens_r2, 4)
        },
        "speed_metrics": {
            "mae": round(spd_mae, 3),
            "rmse": round(spd_rmse, 3),
            "r2_score": round(spd_r2, 4)
        },
        "anomaly_metrics": {
            "contamination_rate": 0.035,
            "detected_in_training": detected_anomalies_count
        }
    }
    
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
        
    print(f"\nAll models saved successfully to: {SAVED_MODELS_DIR}")
    return metrics

if __name__ == "__main__":
    train_and_evaluate_models()
