"""
FastAPI Application Server
Entry point for Real-Time Traffic Congestion Prediction System.
"""

import os
import sys
import threading
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Ensure root workspace directory is on python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.config import settings
from backend.database import init_db
from backend.routes import traffic, predictions, anomalies, system, websocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [API] %(message)s"
)
logger = logging.getLogger("traffic_api")

# Background thread handle for automated simulation if enabled
_sim_thread = None
_sim_running = False

def background_traffic_simulator():
    """Generates continuous live events if standalone producer is not active."""
    global _sim_running
    from streaming.producer import ROADS_DATA, generate_live_event
    from streaming.processor import process_traffic_event
    import random
    
    logger.info("Background telemetry streaming thread started.")
    road_idx = 0
    while _sim_running:
        try:
            road = ROADS_DATA[road_idx % len(ROADS_DATA)]
            road_idx += 1
            event = generate_live_event(road)
            process_traffic_event(event)
            time.sleep(settings.EVENT_INTERVAL_SECONDS)
        except Exception as e:
            logger.error("Simulator background loop error: %s", e)
            time.sleep(2.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Initializing database models and seed data...")
    init_db()

    # If background simulation is auto-enabled, start thread so Live Server sees data immediately
    global _sim_thread, _sim_running
    if os.environ.get("TESTING") != "true":
        _sim_running = True
        _sim_thread = threading.Thread(target=background_traffic_simulator, daemon=True)
        _sim_thread.start()
        logger.info("Background traffic simulation daemon activated.")

    yield

    # Shutdown sequence
    _sim_running = False
    logger.info("Shutting down Traffic Analytics backend...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-Time Traffic Congestion Prediction & Anomaly Detection System using Kafka Streaming, Random Forest, Isolation Forest, and MySQL.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for Live Server (127.0.0.1:5500) & local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(traffic.router)
app.include_router(predictions.router)
app.include_router(anomalies.router)
app.include_router(system.router)
app.include_router(websocket.router)

# Mount static frontend files
frontend_dir = os.path.join(parent_dir, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.get("/dashboard", include_in_schema=False)
def dashboard_redirect():
    return RedirectResponse(url="/frontend/index.html")

@app.get("/")
def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ONLINE",
        "docs_url": "http://127.0.0.1:8000/docs",
        "dashboard_url": "http://127.0.0.1:8000/frontend/index.html",
        "live_server_frontend": settings.LIVE_SERVER_URL,
        "endpoints": {
            "summary": "/api/dashboard/summary",
            "live_traffic": "/api/traffic/live",
            "roads": "/api/traffic/roads",
            "history": "/api/traffic/history",
            "predictions": "/api/predictions",
            "anomalies": "/api/anomalies",
            "system_status": "/api/system/status",
            "websocket": "/ws/traffic"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=False
    )
