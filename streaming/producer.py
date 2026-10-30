"""
Apache Kafka Traffic Event Producer
Reads or generates continuous traffic telemetry events, converts them to JSON,
and streams them to the Kafka topic 'traffic-events' (with automatic emulator fallback).
"""

import os
import sys
import time
import json
import random
import logging
import argparse
from datetime import datetime

# Adjust Python path so running from root or streaming/ works
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.config import settings
from streaming.stream_emulator import stream_queue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Producer] %(message)s"
)
logger = logging.getLogger("kafka_producer")

ROADS_DATA = [
    {"road_id": "ROAD-001", "road_name": "Grand Trunk Expressway", "location": "Downtown North", "cap": 160, "limit": 80},
    {"road_id": "ROAD-002", "road_name": "Central Metro Corridor", "location": "Commercial District", "cap": 110, "limit": 50},
    {"road_id": "ROAD-003", "road_name": "Coastal Ring Highway", "location": "Harbor Zone", "cap": 140, "limit": 70},
    {"road_id": "ROAD-004", "road_name": "Tech Park Boulevard", "location": "Silicon Suburb", "cap": 120, "limit": 60},
    {"road_id": "ROAD-005", "road_name": "Airport Expressway", "location": "Aerocity Sector", "cap": 180, "limit": 90},
    {"road_id": "ROAD-006", "road_name": "Riverfront Arterial Way", "location": "Riverside Promenade", "cap": 80, "limit": 45}
]

WEATHER_OPTIONS = ["Clear", "Overcast", "Rain", "Fog"]

def is_kafka_broker_reachable(bootstrap_servers: str, timeout: float = 0.8) -> bool:
    """Quick socket probe to check if Kafka broker port is actively accepting connections."""
    import socket
    try:
        host, port = bootstrap_servers.split(",")[0].split(":")
        with socket.create_connection((host.strip(), int(port.strip())), timeout=timeout):
            return True
    except Exception:
        return False

def create_kafka_producer(bootstrap_servers: str):
    """Attempts to connect to an active Apache Kafka cluster."""
    if not is_kafka_broker_reachable(bootstrap_servers):
        logger.info("Kafka broker at %s is not actively listening. Enabling emulator fallback.", bootstrap_servers)
        return None

    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            api_version=(2, 5, 0),
            request_timeout_ms=2000,
            max_block_ms=2000
        )
        logger.info("Connected to Apache Kafka broker at %s", bootstrap_servers)
        return producer
    except Exception as e:
        logger.warning("Could not establish direct connection to Kafka at %s: %s", bootstrap_servers, e)
        return None

def generate_live_event(road: dict) -> dict:
    """Generates a realistic live traffic event for the given road."""
    now = datetime.now()
    hour = now.hour
    is_rush_hour = (7 <= hour <= 10) or (16 <= hour <= 19)
    
    cap = road["cap"]
    limit = road["limit"]
    
    factor = random.uniform(0.70, 0.95) if is_rush_hour else random.uniform(0.20, 0.60)
    
    # 5% chance of simulated incident / anomaly
    inject_anomaly = (random.random() < 0.05)
    
    vehicle_count = max(5, int(cap * factor + random.randint(-8, 8)))
    density = min(100.0, max(5.0, (vehicle_count / cap) * 100.0 + random.uniform(-4, 4)))
    
    speed_factor = max(0.15, 1.0 - (density / 105.0))
    avg_speed = max(8.0, min(float(limit), limit * speed_factor + random.uniform(-3, 3)))
    
    if inject_anomaly:
        anomaly_choice = random.choice(["jam", "surge"])
        if anomaly_choice == "jam":
            avg_speed = max(6.0, avg_speed * 0.25)
            density = min(98.0, density * 1.5)
            vehicle_count = int(vehicle_count * 1.3)
        else:
            avg_speed = min(limit * 1.25, avg_speed * 1.4)
            vehicle_count = max(2, int(vehicle_count * 0.3))
            
    if density < 35.0:
        congestion = "LOW"
    elif density < 65.0:
        congestion = "MEDIUM"
    elif density < 85.0:
        congestion = "HIGH"
    else:
        congestion = "SEVERE"

    return {
        "event_id": f"LIVE-{now.strftime('%Y%m%d%H%M%S')}-{road['road_id']}-{random.randint(100, 999)}",
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "road_id": road["road_id"],
        "road_name": road["road_name"],
        "location": road["location"],
        "vehicle_count": vehicle_count,
        "average_speed": round(avg_speed, 2),
        "traffic_density": round(density, 2),
        "weather_condition": random.choice(WEATHER_OPTIONS),
        "congestion_level": congestion,
        "is_simulated": True
    }

def run_producer(
    interval: float = 2.0,
    topic: str = "traffic-events",
    mode: str = "auto",
    count: int = 0
):
    """Continuous stream producer main loop."""
    logger.info("Starting Traffic Event Producer [Topic: %s, Interval: %.1fs, Mode: %s]", topic, interval, mode)
    
    kafka_prod = None
    if mode in ["kafka", "auto"]:
        kafka_prod = create_kafka_producer(settings.KAFKA_BOOTSTRAP_SERVERS)
        if kafka_prod is None and mode == "kafka":
            logger.error("Kafka mode was explicitly requested but broker was unreachable. Exiting.")
            sys.exit(1)

    if kafka_prod is None:
        logger.info("Operating in Streaming Emulation Mode (queue enabled for consumer & dashboard).")

    events_sent = 0
    road_idx = 0
    
    try:
        while True:
            # Cycle through roads to provide rich multi-road streams
            road = ROADS_DATA[road_idx % len(ROADS_DATA)]
            road_idx += 1
            
            event = generate_live_event(road)
            
            # Send to Kafka if available
            if kafka_prod:
                try:
                    kafka_prod.send(topic, value=event)
                    kafka_prod.flush()
                except Exception as ex:
                    logger.warning("Failed sending to Kafka, falling back to local queue: %s", ex)
                    stream_queue.publish(topic, event)
            else:
                # Send to decoupled emulator queue
                stream_queue.publish(topic, event)
                
            events_sent += 1
            logger.info(
                "[%d] Sent: %s | Vehicles: %d | Speed: %.1f km/h | Density: %.1f%% | Level: %s",
                events_sent, event["road_id"], event["vehicle_count"],
                event["average_speed"], event["traffic_density"], event["congestion_level"]
            )
            
            if count > 0 and events_sent >= count:
                logger.info("Reached target count of %d events. Stopping producer.", count)
                break
                
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Producer interrupted by user. Stopping gracefully.")
    finally:
        if kafka_prod:
            kafka_prod.close()
        logger.info("Traffic Producer stopped. Total events produced: %d", events_sent)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traffic Telemetry Stream Producer")
    parser.add_argument("--interval", type=float, default=settings.EVENT_INTERVAL_SECONDS, help="Seconds between events")
    parser.add_argument("--topic", type=str, default=settings.KAFKA_TOPIC, help="Kafka topic name")
    parser.add_argument("--mode", type=str, default=settings.KAFKA_MODE, choices=["kafka", "simulator", "auto"])
    parser.add_argument("--count", type=int, default=0, help="Number of events to generate (0 for infinite)")
    args = parser.parse_args()
    
    run_producer(interval=args.interval, topic=args.topic, mode=args.mode, count=args.count)
