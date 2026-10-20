import pytest
from backend.app.services.health_engine import HealthEngine
from backend.app.config import settings

def test_health_engine_normal_point():
    engine = HealthEngine()
    normal_point = {
        "battery_voltage": 52.0,
        "battery_current": 15.0,
        "battery_temperature": 32.0,
        "motor_temperature": 45.0,
        "vehicle_speed": 40.0,
        "state_of_charge": 75.0,
        "ambient_temperature": 28.0,
        "moisture_status": "dry",
        "sensor_fault_status": False,
        "fault_codes": [],
        "power_kw": 0.78,
        "temp_delta": 4.0,
        "data_source_type": "simulated"
    }
    assessment = engine.assess_telemetry(normal_point)
    assert assessment["overall_status"] in ["Normal", "Warning"]
    assert assessment["battery_health_score"] >= 80.0
    assert assessment["motor_health_score"] >= 80.0

def test_health_engine_critical_battery_overtemp():
    engine = HealthEngine()
    critical_point = {
        "battery_voltage": 50.0,
        "battery_current": 45.0,
        "battery_temperature": 57.5, # Exceeds 55°C critical limit
        "motor_temperature": 60.0,
        "vehicle_speed": 55.0,
        "state_of_charge": 50.0,
        "ambient_temperature": 30.0,
        "moisture_status": "dry",
        "sensor_fault_status": False,
        "fault_codes": ["BMS_CRITICAL_OVERHEAT"],
        "power_kw": 2.25,
        "temp_delta": 27.5,
        "data_source_type": "simulated"
    }
    assessment = engine.assess_telemetry(critical_point)
    assert assessment["overall_status"] == "High Anomaly"
    assert "CRITICAL_BATTERY_OVERTEMP" in assessment["rule_violations"]
    assert assessment["battery_health_score"] < 60.0

def test_health_engine_sensor_disconnect():
    engine = HealthEngine()
    disconnect_point = {
        "battery_voltage": 0.0,
        "sensor_fault_status": True,
        "data_source_type": "unavailable"
    }
    assessment = engine.assess_telemetry(disconnect_point)
    assert assessment["overall_status"] == "Insufficient Data"
    assert "SENSOR_BUS_DISCONNECT" in assessment["rule_violations"]
