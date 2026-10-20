import pytest
from backend.app.ota.virtual_bms import VirtualBMS
from backend.app.ota.validation_runner import OTAValidationRunner
from backend.app.ota.test_scenarios import ALL_TEST_SCENARIOS

def test_ota_virtual_bms_reference_overtemp_cutoff():
    ref_profile = {
        "version_string": "v2.4.1-stable",
        "max_cell_temp_cutoff": 55.0,
        "deliberate_regression_bypass_overtemp": False
    }
    bms = VirtualBMS(ref_profile)
    res = bms.evaluate_state({"battery_temperature": 56.5, "battery_voltage": 51.0, "battery_current": 30.0})
    
    assert res["contactor_open"] is True
    assert res["derate_state"] == "EMERGENCY_CUTOFF"
    assert res["allowed_discharge_amps"] == 0.0
    assert "FAULT_THERMAL_RUNAWAY_PROTECTION" in res["active_faults"]

def test_ota_virtual_bms_regressed_fails_cutoff():
    regressed_profile = {
        "version_string": "v2.5.0-rc1-regressed",
        "max_cell_temp_cutoff": 55.0,
        "deliberate_regression_bypass_overtemp": True # REGRESSION
    }
    bms = VirtualBMS(regressed_profile)
    res = bms.evaluate_state({"battery_temperature": 56.5, "battery_voltage": 51.0, "battery_current": 30.0})
    
    # Regression causes it to fail to trigger EMERGENCY_CUTOFF
    assert res["derate_state"] != "EMERGENCY_CUTOFF"
    assert res["contactor_open"] is False

def test_ota_deliberate_regression_runner_returns_block():
    ref_profile = {
        "version_string": "v2.4.1-stable",
        "max_cell_temp_cutoff": 55.0,
        "deliberate_regression_bypass_overtemp": False
    }
    cand_regressed_profile = {
        "version_string": "v2.5.0-rc1-regressed",
        "max_cell_temp_cutoff": 55.0,
        "deliberate_regression_bypass_overtemp": True
    }
    
    summary = OTAValidationRunner.execute_validation_run(
        reference_profile=ref_profile,
        candidate_profile=cand_regressed_profile,
        reference_version_id=1,
        candidate_version_id=2
    )
    
    assert summary["overall_result"] == "BLOCK"
    assert summary["failed_tests"] > 0
    assert summary["regression_detected"] is True
    assert "TC-003-BATTERY-OVERTEMP" in str(summary["block_reason"])

def test_ota_clean_candidate_runner_returns_pass():
    ref_profile = {
        "version_string": "v2.4.1-stable",
        "max_cell_temp_cutoff": 55.0,
        "deliberate_regression_bypass_overtemp": False
    }
    cand_clean_profile = {
        "version_string": "v2.5.0-clean",
        "max_cell_temp_cutoff": 55.0,
        "deliberate_regression_bypass_overtemp": False
    }
    
    summary = OTAValidationRunner.execute_validation_run(
        reference_profile=ref_profile,
        candidate_profile=cand_clean_profile,
        reference_version_id=1,
        candidate_version_id=3
    )
    
    assert summary["overall_result"] == "PASS"
    assert summary["failed_tests"] == 0
    assert summary["blocked_tests"] == 0
    assert summary["regression_detected"] is False
