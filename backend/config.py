import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "Real-Time Traffic Congestion Prediction System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server Binding
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000
    LIVE_SERVER_URL: str = "http://127.0.0.1:5500"
    CORS_ORIGINS: str = "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,http://localhost:8000,*"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # MySQL Database (College Requirement)
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "traffic_analytics"
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/traffic_analytics"
    
    # SQLite Fallback (Auto-activated when local MySQL service is offline)
    SQLITE_FALLBACK_URL: str = "sqlite:///./traffic_analytics.db"
    USE_SQLITE_FALLBACK: bool = True

    # Apache Kafka Streaming Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "traffic-events"
    KAFKA_CONSUMER_GROUP: str = "traffic-analytics-group"
    KAFKA_MODE: str = "auto" # "kafka", "simulator", or "auto"

    # Streaming & Metrics Configuration
    EVENT_INTERVAL_SECONDS: float = 2.0
    TRAFFIC_SLIDING_WINDOW_EVENTS: int = 20
    
    # ML Models Configuration
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "saved_models")
    RF_MODEL_PATH: str = os.path.join(MODEL_DIR, "random_forest_regressor.joblib")
    ISO_MODEL_PATH: str = os.path.join(MODEL_DIR, "isolation_forest.joblib")
    SCALER_PATH: str = os.path.join(MODEL_DIR, "feature_scaler.joblib")
    METRICS_PATH: str = os.path.join(MODEL_DIR, "model_metrics.json")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
