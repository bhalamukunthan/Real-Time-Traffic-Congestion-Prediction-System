# Real-Time Traffic Congestion Prediction System Using Streaming Analytics and Machine Learning

A production-grade, enterprise-ready Smart City Traffic Monitoring and Telemetry Prediction platform demonstrating all six college-required layers of Data Stream Analytics:
1. **Data Source**: Multi-corridor realistic urban traffic event generator & historical dataset replay.
2. **Streaming Tool**: Apache Kafka Producer & Consumer with seamless decoupling and queue resilience.
3. **Stream Processor**: Python sliding-window streaming engine for real-time speed, density, and congestion categorization.
4. **Machine Learning Algorithms**: Random Forest Regressor (15-min future congestion forecasting) & Isolation Forest (unsupervised traffic anomaly detection).
5. **Database**: MySQL relational analytics warehouse (`traffic_analytics`) with automated SQLAlchemy failover.
6. **Visualization**: Responsive, dark-navy smart-city operations dashboard with Chart.js and Leaflet.js, configured for Live Server (`:5500`) and FastAPI (`:8000`).

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------+
|                       1. DATA SOURCE LAYER                            |
|       Synthetic Urban Road Telemetry / Historical Dataset (CSV)       |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                      2. STREAMING TOOL LAYER                          |
|    Kafka Producer  --->  Apache Kafka Topic  --->  Kafka Consumer     |
|   (JSON Serialization)     ['traffic-events']     (Payload Validation)|
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    3. STREAM PROCESSOR LAYER                          |
|         Sliding Window Analytics (Rolling Speed, Density, Volumes)    |
|             Congestion Categorization (LOW, MEDIUM, HIGH, SEVERE)     |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                  4. MACHINE LEARNING ENGINE LAYER                     |
|  * Random Forest Regressor: 15-Minute Future Density & Speed Forecast |
|  * Isolation Forest: Hazard, Bottleneck & Volume Surge Detection      |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                       5. DATABASE STORAGE LAYER                       |
|           MySQL Database (`traffic_analytics`) via SQLAlchemy         |
|   Tables: road_information, traffic_events, traffic_metrics,         |
|           traffic_predictions, traffic_anomalies                      |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    6. FASTAPI BACKEND & WEBSOCKET                     |
|     REST API Endpoints (:8000) & Real-Time WebSocket Channel (/ws)    |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                     7. VISUALIZATION DASHBOARD                        |
|       VS Code Live Server (:5500) | Chart.js | Leaflet.js Dark Maps   |
|         7 Pages: Overview, Live, Map, Forecasts, Anomalies, etc.      |
+-----------------------------------------------------------------------+
```

---

## 📁 Project Directory Structure

```
traffic-congestion-prediction/
│
├── frontend/                   # Smart-City Visual Dashboard (Port 5500)
│   ├── index.html              # Page 1: Overview Dashboard
│   ├── traffic.html            # Page 2: Live Traffic Monitoring
│   ├── map.html                # Page 3: Leaflet.js Interactive Map
│   ├── predictions.html        # Page 4: ML Forecasts & Evaluation Metrics
│   ├── anomalies.html          # Page 5: Isolation Forest Anomaly Detection
│   ├── history.html            # Page 6: Diurnal Trends & Historical Analytics
│   ├── status.html             # Page 7: 6-Layer System Status Verification
│   ├── css/
│   │   └── style.css           # Dark Navy & Cyan Theme Design System
│   └── js/
│       ├── api.js              # Resilient REST & WebSocket API Client
│       ├── dashboard.js        # Overview KPI & Chart Controllers
│       ├── traffic.js          # Live Telemetry & Road Filter Handlers
│       ├── map.js              # Leaflet GIS Markers & Popup Logic
│       ├── predictions.js      # Multi-Step Forecast Comparison Views
│       ├── anomalies.js        # Outlier & Alert Table Handlers
│       ├── history.js          # 24-Hour Diurnal Rush-Hour Analytics
│       └── status.js           # Live Architecture Heartbeat Monitor
│
├── backend/                    # FastAPI High-Throughput REST & WebSocket Core
│   ├── main.py                 # Application server & CORS configuration
│   ├── config.py               # Pydantic environment settings
│   ├── database.py             # MySQL Engine with seamless SQLite failover
│   ├── models.py               # SQLAlchemy 2.0 ORM Database Schemas
│   ├── schemas.py              # Pydantic Request & Response Data Models
│   ├── routes/
│   │   ├── traffic.py          # /api/dashboard/summary, /api/traffic/*
│   │   ├── predictions.py      # /api/predictions, /evaluation
│   │   ├── anomalies.py        # /api/anomalies
│   │   ├── system.py           # /api/system/status
│   │   └── websocket.py        # /ws/traffic live streaming push socket
│   └── services/
│       └── traffic_service.py  # Analytical queries & KPI aggregations
│
├── streaming/                  # Apache Kafka Streaming & Processing Pipeline
│   ├── producer.py             # Kafka Producer (JSON serialization)
│   ├── consumer.py             # Kafka Consumer (Validation & forwarding)
│   ├── processor.py            # Stream analytics & sliding-window metrics
│   └── stream_emulator.py      # IPC Queue emulator (active when Kafka is offline)
│
├── ml/                         # Machine Learning Modules
│   ├── train_model.py          # RF & Isolation Forest training pipeline
│   ├── predict.py              # 15-min future density & speed inference
│   ├── anomaly_detection.py    # Statistical outlier classification & diagnostics
│   └── saved_models/
│       ├── random_forest_regressor.joblib
│       ├── isolation_forest.joblib
│       ├── feature_scaler.joblib
│       └── model_metrics.json  # Holdout test metrics (MAE, RMSE, R²)
│
├── dataset/                    # Data Source Layer
│   ├── generate_dataset.py     # Realistic diurnal data generator
│   └── traffic_data.csv        # 4,032 historical time-series events
│
├── database/
│   └── schema.sql              # Pure MySQL DDL schema and initial seeds
│
├── scripts/
│   ├── setup.py                # Automated 1-step DB, dataset, and ML setup
│   └── run_all.py              # Convenience launcher for FastAPI backend
│
├── tests/
│   └── test_pipeline.py        # Complete 5-phase integration test suite
│
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── .env                        # Local configuration
├── .gitignore
└── README.md
```

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend** | HTML5, CSS3, Modern JavaScript (ES6+), Leaflet.js, Chart.js |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, WebSockets, Pydantic v2 |
| **Streaming** | Apache Kafka, kafka-python-ng, Cross-Process Buffer |
| **Processing** | Python Sliding Windows, Pandas, NumPy |
| **Machine Learning** | Scikit-Learn (Random Forest Regressor, Isolation Forest), Joblib |
| **Database** | MySQL 8.0+, SQLAlchemy 2.0 (with SQLite failover resilience) |

---

## 🚀 Step-by-Step Setup and Execution Guide

### 1. Prerequisites & Required Software
- **Python**: Version 3.10 to 3.13 installed (`python --version`)
- **VS Code**: With the **Live Server** extension installed
- **MySQL Server** (Optional for local testing; system auto-activates SQLite fallback if offline)
- **Apache Kafka & Zookeeper** (Optional; system includes transparent IPC streaming fallback)

---

### 2. Python Environment Setup
Open Windows Command Prompt (`cmd.exe`) or PowerShell:

```cmd
cd C:\Users\Asus\.gemini\antigravity\scratch\traffic-congestion-prediction
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Python Dependencies

```cmd
pip install -r requirements.txt
```

---

### 4. Database Setup (MySQL)
If running a local MySQL server:
1. Open MySQL Command Line Client:
```sql
CREATE DATABASE IF NOT EXISTS traffic_analytics;
```
2. Run the provided schema script:
```cmd
mysql -u root -p traffic_analytics < database/schema.sql
```
3. Update `.env` with your MySQL credentials:
```ini
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/traffic_analytics
```
*(Note: If MySQL is offline, the system automatically uses SQLite `traffic_analytics.db` without failing).*

---

### 5. Automated System Initialization (1-Step Setup)
Run the automated setup script to build tables, generate the 4,032-event dataset, train both Machine Learning models, and seed historical data:

```cmd
python scripts\setup.py
```
*(or simply double-click `setup.bat` on Windows)*

Expected output:
```
[Step 1/4] Initializing Database Schema & Road Information...
[OK] Database tables initialized and 6 urban corridors seeded.
[Step 2/4] Generating Historical Traffic Dataset...
[OK] Historical dataset generated at dataset/traffic_data.csv
[Step 3/4] Training Random Forest Regressor & Isolation Forest...
[OK] Machine Learning models trained, evaluated, and saved to ml/saved_models/
[Step 4/4] Seeding Database with Historical Records...
[OK] Database populated with historical telemetry for instant dashboard charts.
```

---

### 6. Quick Launch Using Windows Batch Files
For convenience on Windows CMD, one-click launcher scripts are provided:

| Action | Command / Batch File | Description |
|---|---|---|
| **1-Click Setup** | `setup.bat` | Initializes DB, generates data, trains ML, and seeds records. |
| **Start Backend** | `start_backend.bat` | Starts Uvicorn server on port 8000 with auto-reload. |
| **Start Producer** | `start_producer.bat` | Starts live Kafka traffic event generator. |
| **Start Consumer** | `start_consumer.bat` | Starts Kafka consumer and sliding-window stream processor. |
| **Run Tests** | `run_tests.bat` | Runs automated 5-phase integration test suite. |

---

### 6. Apache Kafka Setup (Optional)
If running a full Apache Kafka distribution:

**Terminal 1: Start Zookeeper**
```cmd
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
```

**Terminal 2: Start Kafka Broker**
```cmd
bin\windows\kafka-server-start.bat config\server.properties
```

**Terminal 3: Create Kafka Topic**
```cmd
bin\windows\kafka-topics.bat --create --topic traffic-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

---

### 7. Run the System Components

#### Terminal 1: Start FastAPI Backend
```cmd
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative Redoc API Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Terminal 2: Run Kafka Consumer (Ingestion & Stream Processor)
```cmd
python streaming/consumer.py
```

#### Terminal 3: Run Kafka Producer (Live Telemetry Stream)
```cmd
python streaming/producer.py --interval 2.0
```

#### Step 4: Open Frontend with VS Code Live Server
1. In VS Code or Antigravity IDE, open `frontend/index.html`.
2. Right click inside the editor and choose **"Open with Live Server"**.
3. Your browser will open the dashboard at:
   **[http://127.0.0.1:5500](http://127.0.0.1:5500)** (or `http://127.0.0.1:5500/frontend/index.html`)

---

## 🖥️ Frontend Dashboard Pages

| Page | File | Description |
|---|---|---|
| **Overview Dashboard** | `frontend/index.html` | 6 KPI cards, live speed/density charts, congestion donut, vehicle volume comparisons, 15-min projection, and real-time event logs. |
| **Live Traffic Monitoring** | `frontend/traffic.html` | Live corridor status cards, multi-parameter filters (by road, time horizon, congestion level), and full telemetry table. |
| **Interactive Traffic Map** | `frontend/map.html` | Leaflet.js interactive map with color-coded congestion markers (Green, Yellow, Orange, Red) and detailed sensor popup telemetry. |
| **Prediction Analytics** | `frontend/predictions.html` | Random Forest multi-step forecast timelines, model evaluation cards (MAE, RMSE, R²), and prediction confidence intervals. |
| **Anomaly Detection** | `frontend/anomalies.html` | Isolation Forest statistical outlier detection log, critical bottleneck flags, volume surges, and diagnostic reasoning. |
| **Historical Analytics** | `frontend/history.html` | 24-hour diurnal rush-hour volume profiles, corridor performance comparisons, and multi-day history aggregates. |
| **System Status** | `frontend/status.html` | Real-time health monitoring of all 6 Data Stream Analytics layers, Kafka status, backend uptime, and total processed event counts. |

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/summary` | Aggregated high-level KPIs, charts data, and active road statuses. |
| `GET` | `/api/traffic/live` | Current live telemetry and congestion classification per road. |
| `GET` | `/api/traffic/roads` | Metadata, geographic coordinates, and limits for all 6 corridors. |
| `GET` | `/api/traffic/history` | Historical telemetry records with filtering by road, level, and hours. |
| `GET` | `/api/predictions` | Recent 15-minute future traffic predictions. |
| `GET` | `/api/predictions/evaluation` | Model validation metrics (MAE, RMSE, R²) on holdout test data. |
| `GET` | `/api/anomalies` | Detected unusual traffic patterns and diagnostic explanations. |
| `GET` | `/api/system/status` | Operational statuses of Kafka, MySQL, ML models, and backend. |
| `WS` | `/ws/traffic` | Real-time WebSocket streaming channel for live push telemetry. |

---

## 🧪 Verification & Testing

To execute the automated integration test suite covering all 6 layers:

```cmd
python tests/test_pipeline.py
```

Expected output:
```
[PASS] Layer 5 (Database): 6 road corridors successfully verified.
[PASS] Layer 4 (Machine Learning): RF and Isolation Forest inferences verified.
[PASS] Layer 3 (Stream Processor): Sliding window analytics and DB persistence verified.
[PASS] Backend REST APIs: All 8 required endpoints and schemas validated.
[PASS] Layer 6 (Visualization): All 7 pages and 9 scripts/stylesheets verified.
Ran 5 tests in 4.831s
OK
```

---

## 🛡️ Error Handling & Resilience
- **Database Resilience**: Automatically detects whether MySQL server is accessible on startup. If unavailable, seamlessly activates local SQLite fallback with logging, preventing crashes.
- **Kafka Failover**: If Apache Kafka broker is offline, the stream producer and consumer automatically route messages through a persistent cross-process queue buffer with zero configuration.
- **WebSocket Auto-Reconnect**: Frontend WebSocket client automatically reconnects with exponential backoff on network hiccups and maintains an HTTP polling fallback if the socket closes.
- **Input Validation**: All incoming telemetry events are validated via Pydantic models with bounds checking on speeds, densities, and vehicle counts.

