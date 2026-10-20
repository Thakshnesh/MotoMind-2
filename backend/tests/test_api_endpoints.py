import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_and_healthz():
    res = client.get("/")
    assert res.status_code == 200
    assert "MotoMind" in res.json()["system"]

    res_h = client.get("/healthz")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "HEALTHY"

def test_simulator_endpoints():
    res = client.get("/api/simulator/status")
    assert res.status_code == 200
    assert "is_running" in res.json()

    res_step = client.post("/api/simulator/step")
    assert res_step.status_code == 200
    assert "battery_voltage" in res_step.json()

    res_fault = client.post("/api/simulator/inject-fault", json={"fault_type": "motor_overheat", "duration_seconds": 15})
    assert res_fault.status_code == 200
    assert res_fault.json()["active_fault"] == "motor_overheat"

    res_clear = client.post("/api/simulator/clear-fault")
    assert res_clear.status_code == 200

def test_telemetry_endpoints():
    res = client.get("/api/telemetry/current")
    assert res.status_code == 200
    assert "battery_voltage" in res.json()

    res_hist = client.get("/api/telemetry/history?limit=10")
    assert res_hist.status_code == 200
    assert isinstance(res_hist.json(), list)

    res_sum = client.get("/api/telemetry/summary")
    assert res_sum.status_code == 200
    assert "latest_soc" in res_sum.json()

def test_health_and_range_endpoints():
    res = client.get("/api/health/status")
    assert res.status_code == 200
    assert "overall_status" in res.json()

    range_payload = {
        "battery_soc": 75.0,
        "battery_capacity_kwh": 3.2,
        "average_consumption_wh_km": 30.0,
        "elevation_gain_m": 50.0,
        "traffic_factor": 1.1
    }
    res_range = client.post("/api/health/estimate-range", json=range_payload)
    assert res_range.status_code == 200
    data = res_range.json()
    assert data["estimated_range_km"] > 0
    assert len(data["assumptions_explanation"]) > 0

def test_ota_demo_endpoints():
    # Deliberate regression demo returns BLOCK
    res_reg = client.post("/api/ota/run-demo-regression")
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert reg_data["overall_result"] == "BLOCK"
    assert reg_data["failed_tests"] > 0

    # Clean passing candidate demo returns PASS
    res_clean = client.post("/api/ota/run-demo-passing")
    assert res_clean.status_code == 200
    clean_data = res_clean.json()
    assert clean_data["overall_result"] == "PASS"
    assert clean_data["failed_tests"] == 0
