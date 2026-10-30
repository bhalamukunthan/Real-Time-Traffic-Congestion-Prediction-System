"""
End-to-End System Setup & Initialization Script
Initializes Database, Generates Training Dataset, and Trains Machine Learning Models.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    print("================================================================")
    print("TRAFFIC CONGESTION PREDICTION SYSTEM: INITIAL SETUP")
    print("================================================================")
    
    # Step 1: Database Initialization
    print("\n[Step 1/3] Initializing Database Schema & Road Information...")
    from backend.database import init_db
    init_db()
    print("[OK] Database tables initialized and 6 urban corridors seeded.")

    # Step 2: Historical Dataset Generation
    print("\n[Step 2/3] Generating Historical Traffic Dataset...")
    from dataset.generate_dataset import generate_traffic_dataset
    csv_path = os.path.join(project_root, "dataset", "traffic_data.csv")
    generate_traffic_dataset(num_days=7, interval_minutes=15, output_path=csv_path)
    print(f"[OK] Historical dataset generated at {csv_path}")

    # Step 3: Train Machine Learning Models
    print("\n[Step 3/4] Training Random Forest Regressor & Isolation Forest...")
    from ml.train_model import train_and_evaluate_models
    metrics = train_and_evaluate_models()
    print("[OK] Machine Learning models trained, evaluated, and saved to ml/saved_models/")

    # Step 4: Seed Historical Records
    print("\n[Step 4/4] Seeding Database with Historical Records...")
    from scripts.seed_database import seed_database_from_csv
    seed_database_from_csv(csv_path=csv_path, max_records=500)
    print("[OK] Database populated with historical telemetry for instant dashboard charts.")

    print("\n================================================================")
    print("SETUP COMPLETE!")
    print("All 6 layers are prepared and ready for execution.")
    print("To start the system:")
    print("  1. Start FastAPI backend:  uvicorn backend.main:app --port 8000 --reload")
    print("  2. Open Frontend:          Right click frontend/index.html -> 'Open with Live Server'")
    print("  3. Run Kafka Producer:     python streaming/producer.py")
    print("  4. Run Kafka Consumer:     python streaming/consumer.py")
    print("================================================================")

if __name__ == "__main__":
    main()
