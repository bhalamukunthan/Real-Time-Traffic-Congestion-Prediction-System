"""
Traffic Dataset Generator
Generates realistic historical traffic events across multiple urban corridors,
incorporating diurnal patterns (morning and evening rush hours), weather conditions,
and synthetic anomalies for training Machine Learning models.
"""

import os
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ROADS = [
    {
        "road_id": "ROAD-001",
        "road_name": "Grand Trunk Expressway",
        "location": "Downtown North",
        "speed_limit": 80,
        "lane_count": 4,
        "base_capacity": 160
    },
    {
        "road_id": "ROAD-002",
        "road_name": "Central Metro Corridor",
        "location": "Commercial District",
        "speed_limit": 50,
        "lane_count": 3,
        "base_capacity": 110
    },
    {
        "road_id": "ROAD-003",
        "road_name": "Coastal Ring Highway",
        "location": "Harbor Zone",
        "speed_limit": 70,
        "lane_count": 4,
        "base_capacity": 140
    },
    {
        "road_id": "ROAD-004",
        "road_name": "Tech Park Boulevard",
        "location": "Silicon Suburb",
        "speed_limit": 60,
        "lane_count": 3,
        "base_capacity": 120
    },
    {
        "road_id": "ROAD-005",
        "road_name": "Airport Expressway",
        "location": "Aerocity Sector",
        "speed_limit": 90,
        "lane_count": 4,
        "base_capacity": 180
    },
    {
        "road_id": "ROAD-006",
        "road_name": "Riverfront Arterial Way",
        "location": "Riverside Promenade",
        "speed_limit": 45,
        "lane_count": 2,
        "base_capacity": 80
    }
]

WEATHER_CONDITIONS = [
    ("Clear", 0.65, 1.0, 1.0),       # name, probability, speed_factor, density_factor
    ("Overcast", 0.15, 0.95, 1.05),
    ("Rain", 0.12, 0.75, 1.25),
    ("Heavy Rain", 0.05, 0.55, 1.45),
    ("Fog", 0.03, 0.60, 1.35)
]

def determine_congestion_level(density_pct: float) -> str:
    """Classify traffic congestion level according to standard transportation thresholds."""
    if density_pct < 35.0:
        return "LOW"
    elif density_pct < 65.0:
        return "MEDIUM"
    elif density_pct < 85.0:
        return "HIGH"
    else:
        return "SEVERE"

def generate_traffic_dataset(
    num_days: int = 7,
    interval_minutes: int = 15,
    anomaly_rate: float = 0.03,
    output_path: str = "dataset/traffic_data.csv"
):
    """Generates synthetic historical dataset with realistic time-of-day traffic patterns."""
    print(f"Generating realistic traffic dataset for {num_days} days across {len(ROADS)} roads...")
    start_time = datetime.now() - timedelta(days=num_days)
    total_steps = int((num_days * 24 * 60) / interval_minutes)
    
    events = []
    weather_choices = [w[0] for w in WEATHER_CONDITIONS]
    weather_probs = [w[1] for w in WEATHER_CONDITIONS]

    for step in range(total_steps):
        curr_time = start_time + timedelta(minutes=step * interval_minutes)
        hour = curr_time.hour
        is_weekend = curr_time.weekday() >= 5
        
        # Diurnal pattern multiplier (0.15 at night up to 1.0 at rush hours)
        if 7 <= hour <= 10:
            diurnal_factor = 0.90 + random.uniform(0.0, 0.15) if not is_weekend else 0.45
        elif 16 <= hour <= 19:
            diurnal_factor = 0.95 + random.uniform(0.0, 0.20) if not is_weekend else 0.65
        elif 11 <= hour <= 15:
            diurnal_factor = 0.55 + random.uniform(-0.05, 0.10)
        elif 20 <= hour <= 23:
            diurnal_factor = 0.40 + random.uniform(-0.05, 0.05)
        else: # late night 0-6
            diurnal_factor = 0.15 + random.uniform(-0.05, 0.05)
            
        weather_idx = np.random.choice(len(weather_choices), p=weather_probs)
        w_name, _, w_speed_fac, w_dens_fac = WEATHER_CONDITIONS[weather_idx]
        
        for road in ROADS:
            cap = road["base_capacity"]
            limit = road["speed_limit"]
            
            # Base vehicles
            expected_vehicles = cap * diurnal_factor * (1.1 if "Metro" in road["road_name"] else 1.0)
            vehicle_count = max(5, int(np.random.normal(expected_vehicles, cap * 0.08)))
            
            # Density percentage (0 - 100%)
            density = min(100.0, max(2.0, (vehicle_count / cap) * 100.0 * w_dens_fac + random.uniform(-3, 3)))
            
            # Speed is inversely related to density (Greenshields Traffic Flow Model concept)
            speed_ratio = max(0.15, 1.0 - (density / 110.0))
            avg_speed = max(8.0, min(float(limit), limit * speed_ratio * w_speed_fac + random.uniform(-2, 2)))
            
            # Inject realistic anomalies
            is_anomaly = random.random() < anomaly_rate
            if is_anomaly:
                anomaly_type = random.choice(["gridlock_accident", "phantom_jam", "speeding_surge"])
                if anomaly_type == "gridlock_accident":
                    avg_speed = max(4.0, avg_speed * 0.25)
                    density = min(99.0, density * 1.6)
                    vehicle_count = int(vehicle_count * 1.4)
                elif anomaly_type == "speeding_surge":
                    avg_speed = min(limit * 1.3, avg_speed * 1.5)
                    vehicle_count = max(2, int(vehicle_count * 0.3))
                    density = max(5.0, density * 0.3)
                    
            congestion = determine_congestion_level(density)
            
            event_id = f"EVT-{curr_time.strftime('%Y%m%d%H%M')}-{road['road_id']}-{random.randint(100, 999)}"
            events.append({
                "event_id": event_id,
                "timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "road_id": road["road_id"],
                "road_name": road["road_name"],
                "location": road["location"],
                "vehicle_count": int(vehicle_count),
                "average_speed": round(float(avg_speed), 2),
                "traffic_density": round(float(density), 2),
                "weather_condition": w_name,
                "congestion_level": congestion,
                "is_simulated": True
            })

    df = pd.DataFrame(events)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset generated successfully with {len(df)} records at: {output_path}")
    return df

if __name__ == "__main__":
    generate_traffic_dataset(num_days=7, interval_minutes=15)

