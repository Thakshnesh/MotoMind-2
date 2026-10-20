import os
import sys
import datetime
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.ml.anomaly_model import SelfLearningAnomalyEngine

def generate_offline_dataset(num_samples: int = 1500, output_path: str = "synthetic_ev_telemetry.csv"):
    print(f"Generating {num_samples} synthetic EV telemetry samples...")
    engine = SelfLearningAnomalyEngine()
    df = engine.generate_synthetic_training_dataset(n_samples=num_samples)

    # Add timestamp index
    base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=num_samples)
    timestamps = [base_time + datetime.timedelta(seconds=i) for i in range(num_samples)]
    df["timestamp"] = [t.isoformat() for t in timestamps]

    # Reorder columns
    cols = ["timestamp", "battery_voltage", "battery_current", "battery_temperature", "motor_temperature", "vehicle_speed", "power_kw", "temp_delta", "is_fault"]
    df = df[cols]

    df.to_csv(output_path, index=False)
    print(f"Dataset saved successfully to: {os.path.abspath(output_path)}")
    print(f"Summary statistics:\n{df.describe()}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "synthetic_ev_telemetry.csv"
    generate_offline_dataset(1500, out_file)
