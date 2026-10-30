"""
Apache Kafka Traffic Event Consumer
Subscribes to the 'traffic-events' topic, continuously receives messages,
validates payload structure, and forwards them to the Stream Processor.
"""

import os
import sys
import time
import json
import logging
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.config import settings
from backend.database import init_db
from streaming.stream_emulator import stream_queue
from streaming.processor import process_traffic_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Consumer] %(message)s"
)
logger = logging.getLogger("kafka_consumer")

REQUIRED_FIELDS = ["road_id", "vehicle_count", "average_speed", "traffic_density"]

def validate_event(event: dict) -> bool:
    """Validates incoming message against expected schema."""
    if not isinstance(event, dict):
        return False
    return all(field in event for field in REQUIRED_FIELDS)

def is_kafka_broker_reachable(bootstrap_servers: str, timeout: float = 0.8) -> bool:
    """Quick socket probe to check if Kafka broker port is actively accepting connections."""
    import socket
    try:
        host, port = bootstrap_servers.split(",")[0].split(":")
        with socket.create_connection((host.strip(), int(port.strip())), timeout=timeout):
            return True
    except Exception:
        return False

def create_kafka_consumer(bootstrap_servers: str, topic: str, group_id: str):
    """Attempts to connect to Kafka topic as a consumer."""
    if not is_kafka_broker_reachable(bootstrap_servers):
        logger.info("Kafka broker at %s is not actively listening. Enabling emulator consumer fallback.", bootstrap_servers)
        return None

    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers.split(","),
            group_id=group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            api_version=(2, 5, 0),
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=1000
        )
        logger.info("Connected to Kafka topic '%s' at %s", topic, bootstrap_servers)
        return consumer
    except Exception as e:
        logger.warning("Could not establish direct Kafka consumer connection: %s", e)
        return None

def run_consumer(
    topic: str = "traffic-events",
    mode: str = "auto",
    count: int = 0
):
    """Continuously consumes events and dispatches to processor."""
    logger.info("Initializing database before consumer start...")
    init_db()
    
    logger.info("Starting Traffic Event Consumer [Topic: %s, Mode: %s]", topic, mode)
    
    kafka_cons = None
    if mode in ["kafka", "auto"]:
        kafka_cons = create_kafka_consumer(
            settings.KAFKA_BOOTSTRAP_SERVERS,
            topic,
            settings.KAFKA_CONSUMER_GROUP
        )
        if kafka_cons is None and mode == "kafka":
            logger.error("Kafka mode was explicitly requested but broker was unreachable. Exiting.")
            sys.exit(1)

    if kafka_cons is None:
        logger.info("Operating in Streaming Emulation Consumer Mode.")

    events_consumed = 0
    try:
        while True:
            raw_event = None
            if kafka_cons:
                try:
                    msg_batch = kafka_cons.poll(timeout_ms=1000)
                    for _, messages in msg_batch.items():
                        for message in messages:
                            raw_event = message.value
                            break
                        if raw_event:
                            break
                except Exception as ex:
                    logger.warning("Kafka poll error: %s", ex)
            
            # If no kafka event retrieved, check queue emulator
            if raw_event is None:
                raw_event = stream_queue.consume(topic, timeout=1.0)

            if raw_event is not None:
                if not validate_event(raw_event):
                    logger.error("Invalid event rejected: %s", raw_event)
                    continue

                events_consumed += 1
                result = process_traffic_event(raw_event)
                
                # Check for anomaly notice
                is_ano = result.get("anomaly", {}).get("is_anomaly", False)
                ano_tag = " [*** ANOMALY FLAGGED ***]" if is_ano else ""
                
                logger.info(
                    "[%d] Processed: %s | Speed: %.1f km/h | Density: %.1f%% | Congestion: %s%s",
                    events_consumed,
                    raw_event.get("road_id"),
                    raw_event.get("average_speed"),
                    raw_event.get("traffic_density"),
                    result.get("event", {}).get("congestion_level"),
                    ano_tag
                )
                
                if count > 0 and events_consumed >= count:
                    logger.info("Reached target count of %d events. Stopping consumer.", count)
                    break
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user. Stopping gracefully.")
    finally:
        if kafka_cons:
            kafka_cons.close()
        logger.info("Traffic Consumer stopped. Total events consumed: %d", events_consumed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traffic Telemetry Stream Consumer")
    parser.add_argument("--topic", type=str, default=settings.KAFKA_TOPIC, help="Kafka topic name")
    parser.add_argument("--mode", type=str, default=settings.KAFKA_MODE, choices=["kafka", "simulator", "auto"])
    parser.add_argument("--count", type=int, default=0, help="Number of events to consume (0 for infinite)")
    args = parser.parse_args()
    
    run_consumer(topic=args.topic, mode=args.mode, count=args.count)
