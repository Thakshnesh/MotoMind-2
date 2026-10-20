import pytest
from backend.app.ml.anomaly_model import SelfLearningAnomalyEngine

def test_ml_anomaly_engine_training():
    engine = SelfLearningAnomalyEngine()
    train_res = engine.train_baseline(sample_count=300, contamination=0.03, exclude_known_faults=True)
    
    assert train_res["status"] == "SUCCESS"
    assert engine.is_trained is True
    assert engine.training_sample_count > 0

def test_ml_anomaly_detection_normal_vs_outlier():
    engine = SelfLearningAnomalyEngine()
    engine.train_baseline(sample_count=400, contamination=0.03)

    # Standard normal cruising point
    normal_point = {
        "battery_voltage": 52.0,
        "battery_current": 14.0,
        "battery_temperature": 32.0,
        "motor_temperature": 40.0,
        "vehicle_speed": 42.0,
        "power_kw": 0.72,
        "temp_delta": 4.0
    }
    is_anomaly, score, dev = engine.predict_point(normal_point)
    assert score < 0.65

    # Extreme outlier (impossible current and extreme temp spike)
    outlier_point = {
        "battery_voltage": 41.0,
        "battery_current": 85.0, # far above normal
        "battery_temperature": 58.0,
        "motor_temperature": 110.0,
        "vehicle_speed": 75.0,
        "power_kw": 3.48,
        "temp_delta": 30.0
    }
    is_anomaly_outlier, score_outlier, dev_outlier = engine.predict_point(outlier_point)
    assert score_outlier > 0.65
    assert len(dev_outlier) > 0
