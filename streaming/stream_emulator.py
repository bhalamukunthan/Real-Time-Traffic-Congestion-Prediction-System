"""
Streaming Queue & Kafka Fallback Emulator
Provides decoupled publisher/subscriber semantics matching Apache Kafka topic behaviors.
Supports both in-memory threading and cross-process IPC via lightweight streaming buffer,
allowing Producer and Consumer to execute in completely independent terminal windows
even if an Apache Kafka cluster daemon is not running locally.
"""

import os
import sys
import time
import json
import sqlite3
import logging
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger("stream_emulator")

BUFFER_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".stream_buffer.db")

class CrossProcessStreamQueue:
    def __init__(self):
        self.subscribers = []
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(BUFFER_DB_PATH, timeout=10) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS stream_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        status TEXT DEFAULT 'PENDING',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stream_topic_status ON stream_messages(topic, status)")
                conn.commit()
        except Exception as e:
            logger.debug("Failed initializing stream buffer db: %s", e)

    def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to cross-process buffer and in-memory subscribers."""
        payload_json = json.dumps(message)
        try:
            with sqlite3.connect(BUFFER_DB_PATH, timeout=10) as conn:
                conn.execute(
                    "INSERT INTO stream_messages (topic, payload, status) VALUES (?, ?, 'PENDING')",
                    (topic, payload_json)
                )
                conn.commit()
        except Exception as e:
            logger.debug("Stream buffer insert error: %s", e)

        # Notify in-process callbacks
        for sub in list(self.subscribers):
            try:
                sub(topic, message)
            except Exception as e:
                logger.debug("Subscriber dispatch error: %s", e)

    def subscribe(self, callback: Callable[[str, Dict[str, Any]], None]):
        self.subscribers.append(callback)

    def consume(self, topic: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Consumes the oldest pending message for the topic from cross-process buffer."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with sqlite3.connect(BUFFER_DB_PATH, timeout=5) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, payload FROM stream_messages WHERE topic = ? AND status = 'PENDING' ORDER BY id ASC LIMIT 1",
                        (topic,)
                    )
                    row = cursor.fetchone()
                    if row:
                        msg_id, payload_str = row
                        cursor.execute("UPDATE stream_messages SET status = 'PROCESSED' WHERE id = ?", (msg_id,))
                        conn.commit()
                        return json.loads(payload_str)
            except Exception as e:
                logger.debug("Stream buffer read error: %s", e)
            time.sleep(0.1)
        return None

stream_queue = CrossProcessStreamQueue()
