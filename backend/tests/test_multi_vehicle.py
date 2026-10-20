import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.vehicle_profiles import profile_registry
from backend.app.simulator.vehicle_simulator import vehicle_simulator
from backend.app.services.health_engine import HealthEngine
from backend.app.ml.anomaly_model import anomaly_engine
from backend.app.ota.virtual_bms import VirtualBMS
from backend.app.ota.validation_runner import OTAValidationRunner
from backend.app.ota.test_scenarios import get_scenarios_for_vehicle

client = TestClient(app)

def test_vehicle_profile_registry():
    profiles = profile_registry.list_profiles()
    assert len(profiles) >= 2
    types = [p["vehicle_type"] for p in profiles]
    assert "two_wheeler" in types
    assert "four_wheeler" in types

    p_2w = profile_registry.get_profile("E2W-SCOOT-01")
    assert p_2w.battery.nominal_voltage == 52.0
    assert p_2w.motor.cooling_type == "air_cooled"

    p_4w = profile_registry.get_profile("E4W-SEDAN-01")
    assert p_4w.battery.nominal_voltage == 400.0
    assert p_4w.motor.cooling_type == "liquid_glycol_loop"
    assert p_4w.motor.motor_count == 2

def test_simulator_vehicle_switching_and_telemetry():
    # Switch to 4W
    vehicle_simulator.set_active_vehicle("E4W-SEDAN-01")
    assert vehicle_simulator.active_vehicle_id == "E4W-SEDAN-01"

    point_4w = vehicle_simulator.step("E4W-SEDAN-01")
    assert point_4w.vehicle_type == "four_wheeler"
    assert point_4w.vehicle_id == "E4W-SEDAN-01"
    # 4W voltage should be around 340-440V
    assert 340.0 <= point_4w.battery_voltage <= 440.0
    assert point_4w.coolant_temperature is not None
    assert point_4w.secondary_motor_temperature is not None
    assert point_4w.sensor_availability["coolant_temperature"] in ["measured", "simulated"]
    assert point_4w.sensor_availability["moisture_status"] == "unavailable"

    # Switch back to 2W
    vehicle_simulator.set_active_vehicle("E2W-SCOOT-01")
    point_2w = vehicle_simulator.step("E2W-SCOOT-01")
    assert point_2w.vehicle_type == "two_wheeler"
    assert 40.0 <= point_2w.battery_voltage <= 62.0
    assert point_2w.coolant_temperature is None
    assert point_2w.sensor_availability["coolant_temperature"] == "unavailable"
    assert point_2w.sensor_availability["moisture_status"] in ["measured", "simulated"]

def test_adaptive_health_engine_2w_vs_4w():
    engine = HealthEngine()

    # 2W telemetry without coolant loop should NOT produce false errors
    telemetry_2w = {
        "vehicle_id": "E2W-SCOOT-01",
        "vehicle_type": "two_wheeler",
        "battery_voltage": 52.0,
        "battery_current": 15.0,
        "battery_temperature": 32.0,
        "motor_temperature": 45.0,
        "coolant_temperature": None,
        "secondary_motor_temperature": None,
        "insulation_resistance_kohm": None,
        "vehicle_speed": 40.0,
        "state_of_charge": 75.0,
        "ambient_temperature": 28.0,
        "moisture_status": "dry",
        "sensor_fault_status": False,
        "fault_codes": [],
        "power_kw": 0.78,
        "temp_delta": 4.0,
        "data_source_type": "simulated",
        "sensor_availability": {
            "battery_voltage": "simulated",
            "coolant_temperature": "unavailable",
            "secondary_motor_temperature": "unavailable"
        }
    }
    assessment_2w = engine.assess_telemetry(telemetry_2w)
    assert assessment_2w["overall_status"] in ["Normal", "Warning"]
    assert "WARN_COOLANT_HIGH_TEMP" not in assessment_2w["rule_violations"]

    # 4W telemetry with coolant overtemp (e.g. 68°C vs 60°C limit) should be flagged
    telemetry_4w_fault = {
        "vehicle_id": "E4W-SEDAN-01",
        "vehicle_type": "four_wheeler",
        "battery_voltage": 395.0,
        "battery_current": 45.0,
        "battery_temperature": 38.0,
        "motor_temperature": 55.0,
        "secondary_motor_temperature": 52.0,
        "coolant_temperature": 68.0, # Coolant overtemp violation
        "insulation_resistance_kohm": 450.0,
        "vehicle_speed": 80.0,
        "state_of_charge": 65.0,
        "ambient_temperature": 28.0,
        "sensor_fault_status": False,
        "fault_codes": [],
        "power_kw": 17.7,
        "temp_delta": 10.0,
        "data_source_type": "simulated",
        "sensor_availability": {
            "battery_voltage": "simulated",
            "coolant_temperature": "simulated",
            "secondary_motor_temperature": "simulated"
        }
    }
    assessment_4w = engine.assess_telemetry(telemetry_4w_fault)
    assert "WARN_COOLANT_HIGH_TEMP" in assessment_4w["rule_violations"]
    assert assessment_4w["overall_status"] in ["Warning", "High Anomaly"]

def test_ml_anomaly_multi_vehicle_isolation():
    # 2W model uses 7 features
    m_2w = anomaly_engine.get_model("two_wheeler")
    assert len(m_2w.feature_names) == 7
    assert "coolant_temperature" not in m_2w.feature_names

    # 4W model uses 8 features
    m_4w = anomaly_engine.get_model("four_wheeler")
    assert len(m_4w.feature_names) == 8
    assert "coolant_temperature" in m_4w.feature_names

    # Train 4W model independently
    res = anomaly_engine.train_baseline(vehicle_type="four_wheeler", sample_count=300)
    assert res["status"] == "SUCCESS"
    assert m_4w.is_trained is True
    assert m_4w.training_sample_count >= 300

def test_ota_virtual_bms_4w_hvil_and_overtemp():
    bms_4w = VirtualBMS({
        "version_string": "v4.1.0-sedan-stable",
        "vehicle_type": "four_wheeler",
        "nominal_pack_voltage": 400.0,
        "max_cell_temp_cutoff": 58.0,
        "over_voltage_cutoff": 425.0,
        "hvil_trip_enabled": True
    })

    # Test HVIL open circuit
    state_hvil = {
        "battery_voltage": 395.0,
        "battery_current": 20.0,
        "battery_temperature": 32.0,
        "hvil_closed": False
    }
    res_hvil = bms_4w.evaluate_state(state_hvil)
    assert res_hvil["contactor_open"] is True
    assert "FAULT_HVIL_CIRCUIT_OPEN" in res_hvil["active_faults"]

    # Test 4W over-voltage cutoff (e.g. 430V > 425V limit)
    state_ov = {
        "battery_voltage": 432.0,
        "battery_current": -50.0,
        "battery_temperature": 30.0
    }
    res_ov = bms_4w.evaluate_state(state_ov)
    assert res_ov["contactor_open"] is True
    assert "FAULT_OVER_VOLTAGE_PROTECT" in res_ov["active_faults"]

def test_api_vehicle_switching_and_ota():
    # Test GET vehicles
    res_veh = client.get("/api/simulator/vehicles")
    assert res_veh.status_code == 200
    veh_list = res_veh.json()
    assert len(veh_list) >= 2

    # Test switch to 4W
    res_sw = client.post("/api/simulator/switch-vehicle", json={"vehicle_id": "E4W-SEDAN-01"})
    assert res_sw.status_code == 200
    assert res_sw.json()["active_vehicle_id"] == "E4W-SEDAN-01"

    # Test 4W OTA scenarios retrieval
    res_scen = client.get("/api/ota/scenarios?vehicle_type=four_wheeler")
    assert res_scen.status_code == 200
    scenarios_4w = res_scen.json()
    assert len(scenarios_4w) >= 12
    scen_ids = [s["scenario_id"] for s in scenarios_4w]
    assert "TC-4W-003-BATTERY-OVERTEMP" in scen_ids
    assert "TC-4W-006-HVIL-LOOP-SAFETY" in scen_ids

    # Run 4W deliberate regression demo
    res_demo = client.post("/api/ota/run-demo-regression?vehicle_type=four_wheeler")
    assert res_demo.status_code == 200
    demo_run = res_demo.json()
    assert demo_run["overall_result"] == "BLOCK"
    assert demo_run["regression_detected"] is True

    # Restore default 2W vehicle
    client.post("/api/simulator/switch-vehicle", json={"vehicle_id": "E2W-SCOOT-01"})
