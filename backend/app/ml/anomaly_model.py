import os
import datetime
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_NAMES_2W = [
    "battery_voltage",
    "battery_current",
    "battery_temperature",
    "motor_temperature",
    "vehicle_speed",
    "power_kw",
    "temp_delta"
]

FEATURE_NAMES_4W = [
    "battery_voltage",
    "battery_current",
    "battery_temperature",
    "motor_temperature",
    "vehicle_speed",
    "power_kw",
    "temp_delta",
    "coolant_temperature"
]

class VehicleIsolationForestModel:
    def __init__(self, vehicle_type: str = "two_wheeler"):
        self.vehicle_type = vehicle_type
        self.feature_names = FEATURE_NAMES_4W if vehicle_type == "four_wheeler" else FEATURE_NAMES_2W
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained: bool = False
        self.training_sample_count: int = 0
        self.last_trained_at: Optional[datetime.datetime] = None
        self.contaminated_samples_filtered: int = 0
        self.contamination_rate: float = 0.03
        self.feature_means: Dict[str, float] = {}
        self.feature_stds: Dict[str, float] = {}

        self.model_path = os.path.join(MODEL_DIR, f"isolation_forest_{vehicle_type}.joblib")
        self.scaler_path = os.path.join(MODEL_DIR, f"scaler_{vehicle_type}.joblib")

        self._load_or_initialize()

    def _load_or_initialize(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data["model"]
                self.training_sample_count = data["sample_count"]
                self.last_trained_at = data["last_trained_at"]
                self.contaminated_samples_filtered = data.get("filtered_count", 0)
                self.contamination_rate = data.get("contamination", 0.03)
                self.feature_means = data.get("means", {})
                self.feature_stds = data.get("stds", {})
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                return
            except Exception:
                pass

        # Immediate baseline train
        self.train_baseline(sample_count=600, contamination=0.03)

    def generate_synthetic_training_dataset(self, n_samples: int = 600) -> pd.DataFrame:
        np.random.seed(42 if self.vehicle_type == "two_wheeler" else 101)
        records = []

        if self.vehicle_type == "four_wheeler":
            # E4W: 400V Pack, 64 kWh, High Power, Coolant Loop
            for _ in range(n_samples):
                soc = float(np.random.uniform(20.0, 95.0))
                voc = 340.0 + (soc / 100.0) * 85.0
                speed = float(np.random.uniform(0.0, 130.0))
                ambient = float(np.random.uniform(20.0, 35.0))
                current = float(np.random.normal(35.0 if speed > 10 else 4.0, 18.0))
                current = float(np.clip(current, -40.0, 220.0))
                voltage = float(voc - current * 0.015 + np.random.normal(0, 0.4))
                batt_temp = float(ambient + (abs(current) ** 1.3) * 0.008 + np.random.normal(3.0, 1.0))
                batt_temp = float(np.clip(batt_temp, 22.0, 42.0))
                motor_temp = float(ambient + speed * 0.35 + np.random.normal(8.0, 3.0))
                motor_temp = float(np.clip(motor_temp, 25.0, 78.0))
                coolant_temp = float((batt_temp + motor_temp) * 0.5 + np.random.normal(0, 1.5))
                coolant_temp = float(np.clip(coolant_temp, 24.0, 52.0))
                power_kw = (voltage * current) / 1000.0
                temp_delta = batt_temp - ambient

                records.append({
                    "battery_voltage": voltage,
                    "battery_current": current,
                    "battery_temperature": batt_temp,
                    "motor_temperature": motor_temp,
                    "vehicle_speed": speed,
                    "power_kw": power_kw,
                    "temp_delta": temp_delta,
                    "coolant_temperature": coolant_temp,
                    "is_fault": False
                })
        else:
            # E2W: 52V Pack, 3.2 kWh, Air Cooled
            for _ in range(n_samples):
                soc = float(np.random.uniform(25.0, 95.0))
                voc = 45.0 + (soc / 100.0) * 13.0
                speed = float(np.random.uniform(0.0, 55.0))
                ambient = float(np.random.uniform(22.0, 36.0))
                current = float(np.random.normal(14.0 if speed > 5 else 1.0, 5.0))
                current = float(np.clip(current, -12.0, 40.0))
                voltage = float(voc - current * 0.045 + np.random.normal(0, 0.2))
                batt_temp = float(ambient + (current ** 2) * 0.005 + np.random.normal(2.5, 1.0))
                batt_temp = float(np.clip(batt_temp, 22.0, 44.0))
                motor_temp = float(ambient + speed * 0.45 + np.random.normal(5.0, 2.0))
                motor_temp = float(np.clip(motor_temp, 25.0, 70.0))
                power_kw = (voltage * current) / 1000.0
                temp_delta = batt_temp - ambient

                records.append({
                    "battery_voltage": voltage,
                    "battery_current": current,
                    "battery_temperature": batt_temp,
                    "motor_temperature": motor_temp,
                    "vehicle_speed": speed,
                    "power_kw": power_kw,
                    "temp_delta": temp_delta,
                    "is_fault": False
                })

        return pd.DataFrame(records)

    def train_baseline(self, sample_count: int = 600, contamination: float = 0.03, exclude_known_faults: bool = True) -> Dict[str, Any]:
        df = self.generate_synthetic_training_dataset(sample_count)
        initial_count = len(df)

        if exclude_known_faults:
            if self.vehicle_type == "four_wheeler":
                df_clean = df[
                    (df["battery_temperature"] < 45.0) &
                    (df["motor_temperature"] < 85.0) &
                    (df["coolant_temperature"] < 58.0) &
                    (df["battery_current"] < 250.0) &
                    (df["battery_voltage"] > 320.0) &
                    (df["battery_voltage"] < 445.0) &
                    (df["is_fault"] == False)
                ].copy()
            else:
                df_clean = df[
                    (df["battery_temperature"] < 48.0) &
                    (df["battery_temperature"] > 10.0) &
                    (df["motor_temperature"] < 80.0) &
                    (df["battery_current"] < 55.0) &
                    (df["battery_voltage"] > 41.0) &
                    (df["battery_voltage"] < 60.0) &
                    (df["is_fault"] == False)
                ].copy()
            filtered_count = initial_count - len(df_clean)
        else:
            df_clean = df
            filtered_count = 0

        X = df_clean[self.feature_names].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled)

        means = {feat: float(np.mean(df_clean[feat])) for feat in self.feature_names}
        stds = {feat: float(np.std(df_clean[feat]) + 1e-6) for feat in self.feature_names}

        self.model = model
        self.scaler = scaler
        self.is_trained = True
        self.training_sample_count = len(df_clean)
        self.last_trained_at = datetime.datetime.now(datetime.timezone.utc)
        self.contaminated_samples_filtered = filtered_count
        self.contamination_rate = contamination
        self.feature_means = means
        self.feature_stds = stds

        try:
            joblib.dump({
                "model": model,
                "sample_count": len(df_clean),
                "last_trained_at": self.last_trained_at,
                "filtered_count": filtered_count,
                "contamination": contamination,
                "means": means,
                "stds": stds
            }, self.model_path)
            joblib.dump(scaler, self.scaler_path)
        except Exception:
            pass

        return {
            "vehicle_type": self.vehicle_type,
            "status": "SUCCESS",
            "training_sample_count": len(df_clean),
            "contaminated_samples_filtered": filtered_count,
            "last_trained_at": self.last_trained_at.isoformat(),
            "contamination_rate": contamination,
            "features_used": self.feature_names
        }

    def predict_point(self, point: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:
        if not self.is_trained or self.model is None or self.scaler is None:
            return False, 0.0, {}

        try:
            raw_features = []
            for feat in self.feature_names:
                val = point.get(feat)
                if val is None or str(val).lower() == "unavailable":
                    val = self.feature_means.get(feat, 0.0)
                raw_features.append(float(val))

            X = np.array([raw_features])
            X_scaled = self.scaler.transform(X)

            decision = float(self.model.decision_function(X_scaled)[0])
            anomaly_score = round(1.0 / (1.0 + np.exp(7.0 * (decision - 0.01))), 3)
            is_anomaly = anomaly_score >= 0.65

            deviations = {}
            for i, feat in enumerate(self.feature_names):
                mean = self.feature_means.get(feat, 0.0)
                std = self.feature_stds.get(feat, 1.0)
                val = raw_features[i]
                z_score = abs(val - mean) / std
                if z_score > 2.2:
                    deviations[feat] = {
                        "value": round(val, 2),
                        "baseline_mean": round(mean, 2),
                        "z_score": round(z_score, 2),
                        "direction": "HIGH" if val > mean else "LOW"
                    }

            return is_anomaly, anomaly_score, deviations
        except Exception as e:
            return False, 0.0, {"error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        return {
            "vehicle_type": self.vehicle_type,
            "is_trained": self.is_trained,
            "training_sample_count": self.training_sample_count,
            "last_trained_at": self.last_trained_at,
            "contaminated_samples_filtered": self.contaminated_samples_filtered,
            "contamination_rate": self.contamination_rate,
            "features_used": self.feature_names,
            "model_type": f"IsolationForest (scikit-learn - {self.vehicle_type})",
            "operational_state": "ACTIVE" if self.is_trained else "UNTRAINED",
            "disclaimer": "Trained on vehicle-specific synthetic distributions. Field validation is required."
        }

class SelfLearningAnomalyEngine:
    """
    Multi-Vehicle Anomaly Engine Manager.
    Maintains independent learned baselines for Two-Wheelers and Four-Wheelers.
    """
    def __init__(self):
        self.models: Dict[str, VehicleIsolationForestModel] = {
            "two_wheeler": VehicleIsolationForestModel("two_wheeler"),
            "four_wheeler": VehicleIsolationForestModel("four_wheeler")
        }

    @property
    def is_trained(self) -> bool:
        return self.models["two_wheeler"].is_trained

    @property
    def training_sample_count(self) -> int:
        return self.models["two_wheeler"].training_sample_count

    def get_model(self, vehicle_type: str = "two_wheeler") -> VehicleIsolationForestModel:
        vt = "four_wheeler" if "four" in str(vehicle_type).lower() else "two_wheeler"
        return self.models[vt]

    def train_baseline(self, vehicle_type: str = "two_wheeler", sample_count: int = 600, contamination: float = 0.03, exclude_known_faults: bool = True) -> Dict[str, Any]:
        if isinstance(vehicle_type, int):
            sample_count = vehicle_type
            vehicle_type = "two_wheeler"
        model = self.get_model(vehicle_type)
        return model.train_baseline(sample_count, contamination, exclude_known_faults)

    def predict_point(self, point: Dict[str, Any], vehicle_type: Optional[str] = None) -> Tuple[bool, float, Dict[str, Any]]:
        v_type = vehicle_type or point.get("vehicle_type", "two_wheeler")
        model = self.get_model(v_type)
        return model.predict_point(point)

    def get_status(self, vehicle_type: str = "two_wheeler", vehicle_id: str = "E2W-SCOOT-01") -> Dict[str, Any]:
        model = self.get_model(vehicle_type)
        st = model.get_status()
        st["vehicle_id"] = vehicle_id
        return st

# Global singleton
anomaly_engine = SelfLearningAnomalyEngine()
