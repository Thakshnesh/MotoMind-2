import sys
import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000/api"

def api_get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def api_post(endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    payload = json.dumps(data).encode('utf-8') if data else b""
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    print("=" * 60)
    print("MINT-CONDITION E2E LIVE SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. List vehicles
    vehicles = api_get("/simulator/vehicles")
    print(f"[1] Vehicle catalog ({len(vehicles)} vehicles):")
    for v in vehicles:
        volt = v.get('battery_voltage') or v.get('battery', {}).get('nominal_voltage', 52.0)
        cap = v.get('capacity_kwh') or v.get('battery', {}).get('usable_capacity_kwh', 3.2)
        print(f"    - {v['vehicle_id']} ({v['vehicle_type']}): {v['display_name']} [Nominal: {volt}V, {cap}kWh]")
    assert len(vehicles) >= 2, "Expected at least 2 vehicles"

    # 2. Switch to 2W
    sw_2w = api_post("/simulator/switch-vehicle", {"vehicle_id": "E2W-SCOOT-01"})
    print(f"[2] Switched active vehicle to: {sw_2w['active_vehicle_id']}")
    assert sw_2w['active_vehicle_id'] == "E2W-SCOOT-01"

    # 3. Step & read 2W telemetry
    t_2w = api_post("/simulator/step", {"vehicle_id": "E2W-SCOOT-01"})
    print(f"[3] 2W Telemetry: Voltage={t_2w['battery_voltage']}V, BatteryTemp={t_2w['battery_temperature']}C, Coolant={t_2w.get('coolant_temperature')}")
    assert 40.0 <= t_2w['battery_voltage'] <= 62.0, "2W voltage outside 40-62V"
    assert t_2w.get('coolant_temperature') is None, "2W should have no coolant temperature"
    assert t_2w['sensor_availability']['coolant_temperature'] == 'unavailable'

    # 4. Inject 2W fault & check health
    api_post("/simulator/inject-fault", {"fault_type": "over_temp_battery", "duration_seconds": 15, "vehicle_id": "E2W-SCOOT-01"})
    print("[4] Injected 2W fault: over_temp_battery")
    for _ in range(5):
        api_post("/simulator/step", {"vehicle_id": "E2W-SCOOT-01"})
    h_2w = api_get("/health/status?vehicle_id=E2W-SCOOT-01")
    print(f"    Health Status: {h_2w['overall_status']}, Score={h_2w['battery_health_score']}%, Violations={h_2w['rule_violations']}")
    assert h_2w['overall_status'] in ['Warning', 'High Anomaly']
    api_post("/simulator/clear-fault", {"vehicle_id": "E2W-SCOOT-01"})

    # 5. Switch to 4W
    sw_4w = api_post("/simulator/switch-vehicle", {"vehicle_id": "E4W-SEDAN-01"})
    print(f"[5] Switched active vehicle to: {sw_4w['active_vehicle_id']}")
    assert sw_4w['active_vehicle_id'] == "E4W-SEDAN-01"

    # 6. Step & read 4W telemetry
    t_4w = api_post("/simulator/step", {"vehicle_id": "E4W-SEDAN-01"})
    print(f"[6] 4W Telemetry: Voltage={t_4w['battery_voltage']}V, Coolant={t_4w.get('coolant_temperature')}C, SecMotor={t_4w.get('secondary_motor_temperature')}C")
    assert 340.0 <= t_4w['battery_voltage'] <= 440.0, "4W voltage outside 340-440V"
    assert t_4w.get('coolant_temperature') is not None, "4W should have coolant temperature"
    assert t_4w['sensor_availability']['coolant_temperature'] in ['simulated', 'measured']

    # 7. Inject 4W fault & check health
    api_post("/simulator/inject-fault", {"fault_type": "coolant_pump_failure", "duration_seconds": 20, "vehicle_id": "E4W-SEDAN-01"})
    print("[7] Injected 4W fault: coolant_pump_failure")
    for _ in range(6):
        api_post("/simulator/step", {"vehicle_id": "E4W-SEDAN-01"})
    h_4w = api_get("/health/status?vehicle_id=E4W-SEDAN-01")
    print(f"    Health Status: {h_4w['overall_status']}, Violations={h_4w['rule_violations']}")
    assert any("COOLANT" in v for v in h_4w['rule_violations'])
    api_post("/simulator/clear-fault", {"vehicle_id": "E4W-SEDAN-01"})

    # 8. Train 2W & 4W ML baselines independently
    train_2w = api_post("/anomaly/train", {"vehicle_type": "two_wheeler", "sample_count": 350, "contamination": 0.03, "exclude_known_faults": True})
    print(f"[8] Trained 2W Isolation Forest: {train_2w['status']}, samples={train_2w['training_sample_count']}, features={train_2w['features_used']}")
    assert len(train_2w['features_used']) == 7

    train_4w = api_post("/anomaly/train", {"vehicle_type": "four_wheeler", "sample_count": 350, "contamination": 0.03, "exclude_known_faults": True})
    print(f"[9] Trained 4W Isolation Forest: {train_4w['status']}, samples={train_4w['training_sample_count']}, features={train_4w['features_used']}")
    assert len(train_4w['features_used']) == 8
    assert "coolant_temperature" in train_4w['features_used']

    # 9. Range Estimations
    range_2w = api_post("/health/estimate-range", {"vehicle_id": "E2W-SCOOT-01", "battery_soc": 80.0, "battery_capacity_kwh": 3.2, "average_consumption_wh_km": 32.0})
    print(f"[10] 2W Range Estimate: {range_2w['estimated_range_km']} km (Band: {range_2w['confidence_interval_min_km']}-{range_2w['confidence_interval_max_km']} km)")
    assert 60 <= range_2w['estimated_range_km'] <= 95

    range_4w = api_post("/health/estimate-range", {"vehicle_id": "E4W-SEDAN-01", "battery_soc": 80.0, "battery_capacity_kwh": 64.0, "average_consumption_wh_km": 165.0})
    print(f"[11] 4W Range Estimate: {range_4w['estimated_range_km']} km (Band: {range_4w['confidence_interval_min_km']}-{range_4w['confidence_interval_max_km']} km)")
    assert 250 <= range_4w['estimated_range_km'] <= 360

    # 10. Service & Component Lifecycle
    svc_mode = api_post("/service/service-mode", {"active": True, "vehicle_id": "E4W-SEDAN-01"})
    print(f"[12] Service Mode Toggled: active={svc_mode['service_mode_active']}")
    comp = api_post("/service/components", {
        "vehicle_id": "E4W-SEDAN-01",
        "component_type": "COOLANT_PUMP",
        "serial_number": "SN-PUMP-4W-009",
        "nominal_specs": {"flow_rate_lpm": 18.0},
        "reset_baseline": True,
        "notes": "Replaced thermal loop circulation pump."
    })
    print(f"[13] Component Registered: id={comp['id']}, type={comp['component_type']}, vehicle={comp['vehicle_id']}")
    api_post("/service/service-mode", {"active": False, "vehicle_id": "E4W-SEDAN-01"})

    # 11. OTA Validation 2W Demos
    ota_2w_reg = api_post("/ota/run-demo-regression?vehicle_type=two_wheeler")
    print(f"[14] 2W OTA Regression Demo: verdict={ota_2w_reg['overall_result']}, failed={ota_2w_reg['failed_tests']}, regression={ota_2w_reg['regression_detected']}")
    assert ota_2w_reg['overall_result'] == "BLOCK"
    assert ota_2w_reg['regression_detected'] is True

    ota_2w_pass = api_post("/ota/run-demo-passing?vehicle_type=two_wheeler")
    print(f"[15] 2W OTA Clean Demo: verdict={ota_2w_pass['overall_result']}, passed={ota_2w_pass['passed_tests']}/{ota_2w_pass['total_tests']}")
    assert ota_2w_pass['overall_result'] == "PASS"

    # 12. OTA Validation 4W Demos
    ota_4w_reg = api_post("/ota/run-demo-regression?vehicle_type=four_wheeler")
    print(f"[16] 4W OTA Regression Demo: verdict={ota_4w_reg['overall_result']}, failed={ota_4w_reg['failed_tests']}, regression={ota_4w_reg['regression_detected']}")
    assert ota_4w_reg['overall_result'] == "BLOCK"
    assert ota_4w_reg['regression_detected'] is True

    ota_4w_pass = api_post("/ota/run-demo-passing?vehicle_type=four_wheeler")
    print(f"[17] 4W OTA Clean Demo: verdict={ota_4w_pass['overall_result']}, passed={ota_4w_pass['passed_tests']}/{ota_4w_pass['total_tests']}")
    assert ota_4w_pass['overall_result'] == "PASS"

    print("=" * 60)
    print("ALL 17 LIVE WORKFLOW VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
