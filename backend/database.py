import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

logger = logging.getLogger("traffic_db")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

def get_engine():
    """
    Creates SQLAlchemy Engine with Primary MySQL connection attempt.
    If MySQL server is not reachable or unconfigured, it gracefully falls back
    to SQLite to guarantee seamless development and testing.
    """
    engine = None
    # 1. Attempt MySQL first if requested
    if not settings.DATABASE_URL.startswith("sqlite"):
        try:
            temp_engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 3}
            )
            # Test connectivity
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to MySQL database: %s", settings.MYSQL_DATABASE)
            engine = temp_engine
        except Exception as e:
            logger.warning(
                "MySQL connection to %s:%s failed (%s).",
                settings.MYSQL_HOST, settings.MYSQL_PORT, e
            )
            if settings.USE_SQLITE_FALLBACK:
                logger.info(
                    "Activating SQLite fallback at %s for continuous operation.",
                    settings.SQLITE_FALLBACK_URL
                )
            else:
                raise e

    # 2. Fallback to SQLite if MySQL failed or if SQLite is explicitly configured
    if engine is None:
        db_path = settings.SQLITE_FALLBACK_URL
        connect_args = {"check_same_thread": False, "timeout": 20} if db_path.startswith("sqlite") else {}
        engine = create_engine(db_path, connect_args=connect_args)
        
        # Configure SQLite for high concurrency (WAL mode)
        if db_path.startswith("sqlite"):
            from sqlalchemy import event
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                try:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.close()
                except Exception:
                    pass
        logger.info("Database engine initialized with %s", db_path)

    return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes tables and seeds initial road metadata if empty."""
    from backend import models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Seed default roads if needed
    db = SessionLocal()
    try:
        count = db.query(models.RoadInformation).count()
        if count == 0:
            logger.info("Seeding initial road network information...")
            seed_roads = [
                models.RoadInformation(
                    road_id="ROAD-001",
                    road_name="Grand Trunk Expressway",
                    location="Downtown North",
                    latitude=28.6139,
                    longitude=77.2090,
                    speed_limit=80,
                    lane_count=4,
                    length_km=12.5
                ),
                models.RoadInformation(
                    road_id="ROAD-002",
                    road_name="Central Metro Corridor",
                    location="Commercial District",
                    latitude=28.6328,
                    longitude=77.2197,
                    speed_limit=50,
                    lane_count=3,
                    length_km=8.2
                ),
                models.RoadInformation(
                    road_id="ROAD-003",
                    road_name="Coastal Ring Highway",
                    location="Harbor Zone",
                    latitude=28.5921,
                    longitude=77.2270,
                    speed_limit=70,
                    lane_count=4,
                    length_km=15.0
                ),
                models.RoadInformation(
                    road_id="ROAD-004",
                    road_name="Tech Park Boulevard",
                    location="Silicon Suburb",
                    latitude=28.5355,
                    longitude=77.3910,
                    speed_limit=60,
                    lane_count=3,
                    length_km=10.4
                ),
                models.RoadInformation(
                    road_id="ROAD-005",
                    road_name="Airport Expressway",
                    location="Aerocity Sector",
                    latitude=28.5562,
                    longitude=77.1000,
                    speed_limit=90,
                    lane_count=4,
                    length_km=18.0
                ),
                models.RoadInformation(
                    road_id="ROAD-006",
                    road_name="Riverfront Arterial Way",
                    location="Riverside Promenade",
                    latitude=28.6562,
                    longitude=77.2410,
                    speed_limit=45,
                    lane_count=2,
                    length_km=6.8
                )
            ]
            db.bulk_save_objects(seed_roads)
            db.commit()
            logger.info("Seeded 6 primary urban roads.")
    except Exception as e:
        db.rollback()
        logger.error("Error during road seeding: %s", e)
    finally:
        db.close()
