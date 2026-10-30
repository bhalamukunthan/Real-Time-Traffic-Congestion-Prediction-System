import asyncio
import json
import logging
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from streaming.processor import register_ws_broadcaster, unregister_ws_broadcaster

logger = logging.getLogger("websocket_manager")
router = APIRouter(tags=["WebSocket Stream"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Total clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected. Total clients: %d", len(self.active_connections))

    async def broadcast_json(self, data: dict):
        if not self.active_connections:
            return
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.debug("Failed sending to client, scheduling disconnect: %s", e)
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

    def synchronous_broadcast(self, payload: dict):
        """Called by background thread stream processor to deliver updates into the asyncio loop."""
        if self.loop and self.active_connections:
            try:
                asyncio.run_coroutine_threadsafe(self.broadcast_json(payload), self.loop)
            except Exception as e:
                logger.debug("Error submitting coroutine for broadcast: %s", e)

manager = ConnectionManager()

# Register synchronous bridge into stream processor
register_ws_broadcaster(manager.synchronous_broadcast)

@router.websocket("/ws/traffic")
async def traffic_websocket_endpoint(websocket: WebSocket):
    """
    Live WebSocket streaming channel.
    Continuously pushes fresh traffic events, metrics, predictions, and anomalies
    to the frontend without requiring browser reloads.
    """
    if manager.loop is None:
        manager.loop = asyncio.get_running_loop()

    await manager.connect(websocket)
    try:
        # Send initial welcome confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to Real-Time Traffic Prediction Telemetry Stream",
            "status": "ONLINE"
        })

        while True:
            # Keep socket alive and handle client pings / incoming filters
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket exception: %s", e)
        manager.disconnect(websocket)

