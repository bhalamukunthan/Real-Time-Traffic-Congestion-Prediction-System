-- =======================================================
-- Real-Time Traffic Congestion Prediction System
-- Database Schema: traffic_analytics
-- =======================================================

CREATE DATABASE IF NOT EXISTS traffic_analytics;
USE traffic_analytics;

-- Table 1: Road Information
CREATE TABLE IF NOT EXISTS road_information (
    road_id VARCHAR(50) PRIMARY KEY,
    road_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    speed_limit INT NOT NULL DEFAULT 60,
    lane_count INT NOT NULL DEFAULT 3,
    length_km DECIMAL(5, 2) NOT NULL DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Raw Traffic Events (from Kafka stream)
CREATE TABLE IF NOT EXISTS traffic_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL UNIQUE,
    timestamp DATETIME NOT NULL,
    road_id VARCHAR(50) NOT NULL,
    road_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    vehicle_count INT NOT NULL,
    average_speed DECIMAL(6, 2) NOT NULL,
    traffic_density DECIMAL(6, 2) NOT NULL,
    weather_condition VARCHAR(50) NOT NULL,
    congestion_level VARCHAR(20) NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_road_time (road_id, timestamp),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (road_id) REFERENCES road_information(road_id) ON DELETE CASCADE
);

-- Table 3: Real-Time Stream Processed Metrics
CREATE TABLE IF NOT EXISTS traffic_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    road_id VARCHAR(50) NOT NULL,
    window_size_seconds INT NOT NULL DEFAULT 60,
    total_vehicles INT NOT NULL,
    rolling_avg_speed DECIMAL(6, 2) NOT NULL,
    current_density DECIMAL(6, 2) NOT NULL,
    avg_density DECIMAL(6, 2) NOT NULL,
    max_density DECIMAL(6, 2) NOT NULL,
    congestion_level VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metrics_road_time (road_id, timestamp),
    FOREIGN KEY (road_id) REFERENCES road_information(road_id) ON DELETE CASCADE
);

-- Table 4: Machine Learning Predictions
CREATE TABLE IF NOT EXISTS traffic_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_time DATETIME NOT NULL,
    target_time DATETIME NOT NULL,
    road_id VARCHAR(50) NOT NULL,
    horizon_minutes INT NOT NULL DEFAULT 15,
    predicted_density DECIMAL(6, 2) NOT NULL,
    predicted_speed DECIMAL(6, 2) NOT NULL,
    predicted_congestion VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(4, 3) DEFAULT 0.850,
    model_version VARCHAR(50) NOT NULL DEFAULT 'RandomForest_v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pred_road_time (road_id, target_time),
    FOREIGN KEY (road_id) REFERENCES road_information(road_id) ON DELETE CASCADE
);

-- Table 5: Traffic Anomalies (Isolation Forest detections)
CREATE TABLE IF NOT EXISTS traffic_anomalies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL,
    timestamp DATETIME NOT NULL,
    road_id VARCHAR(50) NOT NULL,
    road_name VARCHAR(100) NOT NULL,
    vehicle_count INT NOT NULL,
    average_speed DECIMAL(6, 2) NOT NULL,
    traffic_density DECIMAL(6, 2) NOT NULL,
    anomaly_score DECIMAL(6, 4) NOT NULL,
    anomaly_reason VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_anomaly_time (timestamp),
    FOREIGN KEY (road_id) REFERENCES road_information(road_id) ON DELETE CASCADE
);

-- Initial Seed Data for Roads
INSERT INTO road_information (road_id, road_name, location, latitude, longitude, speed_limit, lane_count, length_km)
VALUES
    ('ROAD-001', 'Grand Trunk Expressway', 'Downtown North', 28.6139, 77.2090, 80, 4, 12.5),
    ('ROAD-002', 'Central Metro Corridor', 'Commercial District', 28.6328, 77.2197, 50, 3, 8.2),
    ('ROAD-003', 'Coastal Ring Highway', 'Harbor Zone', 28.5921, 77.2270, 70, 4, 15.0),
    ('ROAD-004', 'Tech Park Boulevard', 'Silicon Suburb', 28.5355, 77.3910, 60, 3, 10.4),
    ('ROAD-005', 'Airport Expressway', 'Aerocity Sector', 28.5562, 77.1000, 90, 4, 18.0),
    ('ROAD-006', 'Riverfront Arterial Way', 'Riverside Promenade', 28.6562, 77.2410, 45, 2, 6.8)
ON DUPLICATE KEY UPDATE road_name=VALUES(road_name);

