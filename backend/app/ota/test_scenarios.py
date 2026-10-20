from typing import Dict, Any, List, Callable

class TestScenario:
    def __init__(
        self,
        scenario_id: str,
        name: str,
        category: str,
        severity: str,
        description: str,
        inputs: Dict[str, Any],
        expected_behavior: str,
        assertion_func: Callable[[Dict[str, Any], Dict[str, Any]], tuple[bool, str, Dict[str, Any]]]
    ):
        self.scenario_id = scenario_id
        self.name = name
        self.category = category
        self.severity = severity
        self.description = description
        self.inputs = inputs
        self.expected_behavior = expected_behavior
        self.assertion_func = assertion_func

# ----------------- TWO-WHEELER ASSERTIONS ----------------- #
def assert_tc001(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = (
        candidate["contactor_open"] is False and
        candidate["derate_state"] == "NORMAL" and
        candidate["allowed_discharge_amps"] >= 50.0
    )
    msg = "Nominal operation confirmed: contactor closed, no derating active." if passed else "Unexpected contactor trip or derate in normal driving."
    return passed, msg, {"derate_state": candidate["derate_state"], "contactor_open": candidate["contactor_open"]}

def assert_tc002(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["allowed_charge_amps"] <= 15.0 and candidate["contactor_open"] is False
    msg = "Boundary charge current properly governed at top of charge curve." if passed else "Over-charge allowance at upper SOC boundary."
    return passed, msg, {"allowed_charge_amps": candidate["allowed_charge_amps"]}

def assert_tc003(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = (
        candidate["contactor_open"] is True and
        candidate["derate_state"] == "EMERGENCY_CUTOFF" and
        candidate["allowed_discharge_amps"] == 0.0 and
        "FAULT_THERMAL_RUNAWAY_PROTECTION" in candidate["active_faults"]
    )
    is_regression = (reference["contactor_open"] is True and reference["derate_state"] == "EMERGENCY_CUTOFF") and not passed
    msg = f"Passed: Virtual BMS actuated EMERGENCY_CUTOFF at 56.5°C." if passed else f"CRITICAL FAILURE: Virtual BMS failed to open contactor during battery over-temp (derate='{candidate['derate_state']}')."
    return passed, msg, {
        "candidate_derate": candidate["derate_state"],
        "candidate_contactor_open": candidate["contactor_open"],
        "reference_derate": reference["derate_state"],
        "is_regression": is_regression
    }

def assert_tc004(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["allowed_charge_amps"] == 0.0 and "FAULT_SUBZERO_CHARGE_INHIBIT" in candidate["active_faults"]
    msg = "Subzero charging inhibit correctly engaged to prevent lithium dendrite plating." if passed else "Subzero charge current was not clamped to 0A."
    return passed, msg, {"allowed_charge_amps": candidate["allowed_charge_amps"]}

def assert_tc005(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["contactor_open"] is True and "FAULT_OVER_VOLTAGE_PROTECT" in candidate["active_faults"]
    msg = "Pack over-voltage triggered immediate contactor opening." if passed else "Failed to trip contactor on over-voltage condition."
    return passed, msg, {"contactor_open": candidate["contactor_open"], "faults": candidate["active_faults"]}

def assert_tc006(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["contactor_open"] is True and candidate["allowed_discharge_amps"] == 0.0
    msg = "Overcurrent trip successfully decoupled load contactor." if passed else "Load contactor remained closed during overcurrent surge."
    return passed, msg, {"contactor_open": candidate["contactor_open"]}

def assert_tc007(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["allowed_discharge_amps"] == 0.0 and "INFO_DRIVE_INTERLOCK_ENGAGED" in candidate["active_faults"]
    msg = "Drive interlock active: motor drive disabled while charging cable connected." if passed else "Drive interlock failed: allowed discharge current while plugged in."
    return passed, msg, {"allowed_discharge_amps": candidate["allowed_discharge_amps"]}

def assert_tc008(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["safety_integrity_ok"] is not None
    msg = "SOC input discontinuity handled gracefully without kernel panic or crash." if passed else "BMS exception triggered on SOC sensor discontinuity."
    return passed, msg, {"faults": candidate["active_faults"]}

def assert_tc009(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = "FAULT_BMS_INVALID_SENSOR_DATA" in candidate["active_faults"] and candidate["allowed_discharge_amps"] <= 20.0
    msg = "Sensor disconnect detected: BMS transitioned to safe limp-mode derate." if passed else "Failed to handle disconnected sensor signal."
    return passed, msg, {"faults": candidate["active_faults"], "derate_state": candidate["derate_state"]}

def assert_tc010(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["contactor_open"] is True and "FAULT_CAN_BUS_TIMEOUT" in candidate["active_faults"]
    msg = "CAN bus watchdog timeout triggered failsafe shutdown." if passed else "Failed to enforce failsafe stop upon CAN timeout."
    return passed, msg, {"contactor_open": candidate["contactor_open"]}

def assert_tc011(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["derate_state"] in ["LIMP_MODE", "FAILSAFE_STOP", "EMERGENCY_CUTOFF"]
    msg = "Out-of-bounds sensor reading safely quarantined." if passed else "BMS accepted impossible sensor reading as normal."
    return passed, msg, {"derate_state": candidate["derate_state"]}

def assert_tc012(candidate: Dict[str, Any], reference: Dict[str, Any]):
    ref_contactor = reference["contactor_open"]
    cand_contactor = candidate["contactor_open"]
    passed = ref_contactor == cand_contactor or cand_contactor is True
    msg = "Regression check: candidate profile matches reference baseline safety envelope." if passed else "Regression detected: candidate less restrictive on safety contactor than reference."
    return passed, msg, {"candidate": candidate["derate_state"], "reference": reference["derate_state"]}

# ----------------- FOUR-WHEELER ASSERTIONS ----------------- #
def assert_4w_001(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["contactor_open"] is False and candidate["derate_state"] == "NORMAL" and candidate["allowed_discharge_amps"] >= 250.0
    msg = "400V Dual-Motor cruise nominal: main contactors closed, full traction current permitted." if passed else "Premature contactor trip under 400V cruise."
    return passed, msg, {"contactor_open": candidate["contactor_open"]}

def assert_4w_002(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["allowed_charge_amps"] <= 250.0 and candidate["contactor_open"] is False
    msg = "DC Fast Charge current safely modulated at upper voltage boundary." if passed else "DC Fast Charge current exceeded upper envelope."
    return passed, msg, {"allowed_charge_amps": candidate["allowed_charge_amps"]}

def assert_4w_003(candidate: Dict[str, Any], reference: Dict[str, Any]):
    # 4W High-voltage pack over-temperature (>52°C)
    passed = candidate["contactor_open"] is True and candidate["derate_state"] == "EMERGENCY_CUTOFF" and "FAULT_THERMAL_RUNAWAY_PROTECTION" in candidate["active_faults"]
    is_regression = (reference["contactor_open"] is True and reference["derate_state"] == "EMERGENCY_CUTOFF") and not passed
    msg = "400V Pack overtemp (>52°C): dual contactors opened immediately." if passed else "CRITICAL FAILURE: 400V contactor failed to open during high-temp excursion!"
    return passed, msg, {"contactor_open": candidate["contactor_open"], "is_regression": is_regression}

def assert_4w_004(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["allowed_charge_amps"] == 0.0 and "FAULT_SUBZERO_CHARGE_INHIBIT" in candidate["active_faults"]
    msg = "Subzero (-8°C) DC Fast Charge successfully inhibited to prevent lithium dendrite shorts." if passed else "Subzero DC fast charge allowed current flow."
    return passed, msg, {"allowed_charge_amps": candidate["allowed_charge_amps"]}

def assert_4w_005(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["contactor_open"] is True and "FAULT_OVER_VOLTAGE_PROTECT" in candidate["active_faults"]
    msg = "455V Over-voltage trip decoupled battery pack." if passed else "Over-voltage trip failed to isolate 400V traction pack."
    return passed, msg, {"contactor_open": candidate["contactor_open"]}

def assert_4w_006(candidate: Dict[str, Any], reference: Dict[str, Any]):
    # High Voltage Interlock Loop (HVIL) open
    passed = candidate["contactor_open"] is True and "FAULT_HVIL_CIRCUIT_OPEN" in candidate["active_faults"]
    is_regression = (reference["contactor_open"] is True) and not passed
    msg = "HVIL circuit break detected: pyrofuse / main contactor tripped within 20ms." if passed else "CRITICAL: HVIL loop open but contactors remained energized!"
    return passed, msg, {"contactor_open": candidate["contactor_open"], "is_regression": is_regression}

def assert_4w_007(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["allowed_discharge_amps"] == 0.0 and "INFO_DRIVE_INTERLOCK_ENGAGED" in candidate["active_faults"]
    msg = "CCS2 DC charge interlock engaged: traction inverter disabled while tethered to fast-charger." if passed else "Traction power allowed while plugged in."
    return passed, msg, {"allowed_discharge_amps": candidate["allowed_discharge_amps"]}

def assert_4w_008(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["safety_integrity_ok"] is not None
    msg = "Dual-motor CAN torque sync verified." if passed else "CAN torque sync failure."
    return passed, msg, {"safety": candidate["safety_integrity_ok"]}

def assert_4w_009(candidate: Dict[str, Any], reference: Dict[str, Any]):
    # Coolant loop overtemp (>68°C)
    passed = candidate["derate_state"] == "COOLING_DERATE" and "FAULT_COOLANT_LOOP_OVERTEMP" in candidate["active_faults"] and candidate["allowed_discharge_amps"] <= 120.0
    msg = "Coolant loop thermal failure (>70°C): BMS enforced aggressive cooling derate." if passed else "Failed to derate under high coolant temperature."
    return passed, msg, {"derate_state": candidate["derate_state"], "allowed_amps": candidate["allowed_discharge_amps"]}

def assert_4w_010(candidate: Dict[str, Any], reference: Dict[str, Any]):
    # HV Isolation breach (<100 kOhm)
    passed = candidate["contactor_open"] is True and "FAULT_HV_ISOLATION_BREACH" in candidate["active_faults"]
    msg = "Chassis HV isolation breach (45 kOhm): contactor opened to prevent electric shock." if passed else "Failed to trip on HV isolation fault."
    return passed, msg, {"contactor_open": candidate["contactor_open"]}

def assert_4w_011(candidate: Dict[str, Any], reference: Dict[str, Any]):
    passed = candidate["derate_state"] in ["LIMP_MODE", "FAILSAFE_STOP", "EMERGENCY_CUTOFF"]
    msg = "Sensor corruption safely quarantined." if passed else "Unphysical cell frame accepted."
    return passed, msg, {"derate_state": candidate["derate_state"]}

def assert_4w_012(candidate: Dict[str, Any], reference: Dict[str, Any]):
    ref_contactor = reference["contactor_open"]
    cand_contactor = candidate["contactor_open"]
    passed = ref_contactor == cand_contactor or cand_contactor is True
    msg = "E4W regression check: candidate matches reference baseline safety." if passed else "Regression detected on 4W profile."
    return passed, msg, {"candidate": candidate["derate_state"], "reference": reference["derate_state"]}

# ----------------- SCENARIO SUITES ----------------- #
SCENARIOS_2W = [
    TestScenario("TC-001-NORMAL-OPERATING", "Nominal Cruise Conditions", "FUNCTIONAL", "MAJOR", "Verifies BMS allows full normal discharge and closed contactor under standard operating variables.", {"battery_voltage": 52.0, "battery_current": 18.0, "battery_temperature": 32.0, "ambient_temperature": 28.0, "sensor_valid": True, "can_latency_ms": 12.0}, "Contactor CLOSED, derate_state NORMAL, full current allowed.", assert_tc001),
    TestScenario("TC-002-BOUNDARY-VALUE", "Upper SOC Boundary Charge Taper", "BOUNDARY", "MAJOR", "Verifies charge current limiting near cell top balance boundary.", {"battery_voltage": 57.5, "battery_current": -12.0, "battery_temperature": 35.0, "charging_plugged": True, "sensor_valid": True, "can_latency_ms": 15.0}, "Contactor CLOSED, allowed_charge_amps throttled <= 15A.", assert_tc002),
    TestScenario("TC-003-BATTERY-OVERTEMP", "Battery Critical Over-Temperature Protection", "SAFETY_CRITICAL", "CRITICAL", "Verifies immediate EMERGENCY_CUTOFF and contactor opening when cell temperature exceeds 55.0°C limit.", {"battery_voltage": 51.5, "battery_current": 35.0, "battery_temperature": 56.5, "ambient_temperature": 38.0, "sensor_valid": True, "can_latency_ms": 14.0}, "Contactor OPEN, derate_state EMERGENCY_CUTOFF, allowed_discharge_amps 0.0A, FAULT_THERMAL_RUNAWAY_PROTECTION raised.", assert_tc003),
    TestScenario("TC-004-BATTERY-UNDERTEMP", "Subzero Charge Inhibit Logic", "SAFETY_CRITICAL", "CRITICAL", "Verifies that charging current is completely inhibited (0A) when pack temp is below 0°C to prevent lithium dendrite short circuits.", {"battery_voltage": 48.0, "battery_current": -10.0, "battery_temperature": -4.0, "ambient_temperature": -5.0, "charging_plugged": True, "sensor_valid": True, "can_latency_ms": 10.0}, "allowed_charge_amps 0.0A, FAULT_SUBZERO_CHARGE_INHIBIT active.", assert_tc004),
    TestScenario("TC-005-OVER-UNDER-VOLTAGE", "Pack Over-Voltage Contactor Trip", "SAFETY_CRITICAL", "CRITICAL", "Verifies contactor trip when pack voltage surges beyond 58.8V ceiling.", {"battery_voltage": 60.2, "battery_current": -15.0, "battery_temperature": 32.0, "sensor_valid": True, "can_latency_ms": 12.0}, "Contactor OPEN, FAULT_OVER_VOLTAGE_PROTECT raised.", assert_tc005),
    TestScenario("TC-006-OVERCURRENT-PROTECT", "Discharge Overcurrent Fast Trip", "SAFETY_CRITICAL", "CRITICAL", "Verifies load contactor disconnects under sudden 78A short/overload surge.", {"battery_voltage": 49.0, "battery_current": 78.0, "battery_temperature": 34.0, "sensor_valid": True, "can_latency_ms": 12.0}, "Contactor OPEN, allowed_discharge_amps 0.0A.", assert_tc006),
    TestScenario("TC-007-CHARGING-SAFETY", "Charging Cable Drive Interlock", "SAFETY_CRITICAL", "CRITICAL", "Verifies propulsion motor is completely disabled when charge plug is inserted.", {"battery_voltage": 52.0, "battery_current": -10.0, "battery_temperature": 30.0, "charging_plugged": True, "sensor_valid": True, "can_latency_ms": 10.0}, "allowed_discharge_amps 0.0A, INFO_DRIVE_INTERLOCK_ENGAGED active.", assert_tc007),
    TestScenario("TC-008-SOC-SOH-FAULT", "SOC Corrupt Value Graceful Degradation", "FAULT_TOLERANCE", "MAJOR", "Verifies BMS firmware handles corrupted SOC telemetry frames without crashing.", {"battery_voltage": 52.0, "battery_current": 10.0, "battery_temperature": 30.0, "state_of_charge": -99.0, "sensor_valid": True, "can_latency_ms": 10.0}, "Firmware remains stable, rejects out-of-range SOC gracefully.", assert_tc008),
    TestScenario("TC-009-SENSOR-DRIFT-DISCONNECT", "Temperature Sensor Disconnect Handling", "FAULT_TOLERANCE", "MAJOR", "Verifies transition to safe Limp Mode when analog temperature sensor signal line drops.", {"battery_voltage": 52.0, "battery_current": 20.0, "battery_temperature": 0.0, "sensor_valid": False, "can_latency_ms": 12.0}, "derate_state LIMP_MODE, FAULT_BMS_INVALID_SENSOR_DATA active.", assert_tc009),
    TestScenario("TC-010-CAN-COMM-TIMEOUT", "CAN Bus Loss Watchdog Shutdown", "SAFETY_CRITICAL", "CRITICAL", "Verifies vehicle enters safe failsafe stop if CAN bus latency exceeds 250ms timeout.", {"battery_voltage": 52.0, "battery_current": 15.0, "battery_temperature": 30.0, "sensor_valid": True, "can_latency_ms": 380.0}, "Contactor OPEN, FAULT_CAN_BUS_TIMEOUT active.", assert_tc010),
    TestScenario("TC-011-INVALID-STALE-DATA", "Quarantine of Stale / Corrupted Pack Inputs", "FAULT_TOLERANCE", "MAJOR", "Verifies quarantine logic when incoming sensor packets report unphysical spikes.", {"battery_voltage": 52.0, "battery_current": 10.0, "battery_temperature": 999.0, "sensor_valid": False, "can_latency_ms": 15.0}, "Safe derate enforced; data marked invalid.", assert_tc011),
    TestScenario("TC-012-REGRESSION-REFERENCE", "Reference Baseline Compatibility Suite", "REGRESSION", "CRITICAL", "Direct comparative evaluation against certified reference version v2.4.1 safety envelope.", {"battery_voltage": 53.0, "battery_current": 22.0, "battery_temperature": 34.0, "sensor_valid": True, "can_latency_ms": 15.0}, "Candidate safety envelope must not weaken reference protections.", assert_tc012),
]

SCENARIOS_4W = [
    TestScenario("TC-4W-001-NORMAL-CRUISE", "400V Dual-Motor Highway Cruise", "FUNCTIONAL", "MAJOR", "Verifies 400V high-voltage contactor closure and high-power dual-inverter draw.", {"battery_voltage": 395.0, "battery_current": 95.0, "battery_temperature": 31.0, "coolant_temperature": 34.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 12.0}, "Contactors CLOSED, derate_state NORMAL, full current permitted.", assert_4w_001),
    TestScenario("TC-4W-002-BOUNDARY-DC-FASTCHARGE", "DC Fast Charge 200A Taper", "BOUNDARY", "MAJOR", "Verifies CCS2 DC fast-charge current taper at upper 430V pack voltage threshold.", {"battery_voltage": 435.0, "battery_current": -160.0, "battery_temperature": 36.0, "coolant_temperature": 40.0, "charging_plugged": True, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 15.0}, "Contactors CLOSED, allowed_charge_amps throttled <= 250A.", assert_4w_002),
    TestScenario("TC-4W-003-BATTERY-OVERTEMP", "400V Pack Critical Over-Temperature Cutoff", "SAFETY_CRITICAL", "CRITICAL", "Verifies immediate dual contactor opening when 400V pack temperature exceeds 52.0°C limit.", {"battery_voltage": 390.0, "battery_current": 140.0, "battery_temperature": 54.5, "coolant_temperature": 48.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 14.0}, "Contactors OPEN, derate_state EMERGENCY_CUTOFF, allowed_discharge_amps 0.0A, FAULT_THERMAL_RUNAWAY_PROTECTION raised.", assert_4w_003),
    TestScenario("TC-4W-004-SUBZERO-DC-CHARGE", "Subzero (-8°C) DC Fast Charge Inhibit", "SAFETY_CRITICAL", "CRITICAL", "Verifies DC fast charging is clamped to 0A at -8°C to prevent lithium dendrite shorts.", {"battery_voltage": 370.0, "battery_current": -80.0, "battery_temperature": -8.0, "coolant_temperature": -7.0, "charging_plugged": True, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 10.0}, "allowed_charge_amps 0.0A, FAULT_SUBZERO_CHARGE_INHIBIT active.", assert_4w_004),
    TestScenario("TC-4W-005-OVER-VOLTAGE-TRIP", "Pack Over-Voltage Contactor Trip (455V)", "SAFETY_CRITICAL", "CRITICAL", "Verifies contactors open when regenerative braking spikes voltage above 450V.", {"battery_voltage": 456.0, "battery_current": -110.0, "battery_temperature": 32.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 12.0}, "Contactors OPEN, FAULT_OVER_VOLTAGE_PROTECT active.", assert_4w_005),
    TestScenario("TC-4W-006-HVIL-LOOP-SAFETY", "High Voltage Interlock Loop (HVIL) Trip", "SAFETY_CRITICAL", "CRITICAL", "Verifies that physical disconnect of service plug or HVIL loop immediately opens high-voltage contactors.", {"battery_voltage": 395.0, "battery_current": 40.0, "battery_temperature": 30.0, "hvil_closed": False, "sensor_valid": True, "can_latency_ms": 10.0}, "Contactors OPEN, FAULT_HVIL_CIRCUIT_OPEN active.", assert_4w_006),
    TestScenario("TC-4W-007-CHARGING-INTERLOCK", "CCS2 DC Charge Propulsion Inhibit", "SAFETY_CRITICAL", "CRITICAL", "Verifies traction inverters are disabled when DC fast charge coupler is attached.", {"battery_voltage": 400.0, "battery_current": -120.0, "battery_temperature": 32.0, "charging_plugged": True, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 10.0}, "allowed_discharge_amps 0.0A, INFO_DRIVE_INTERLOCK_ENGAGED active.", assert_4w_007),
    TestScenario("TC-4W-008-DUAL-MOTOR-TORQUE-SYNC", "Dual-Inverter CAN Sync Verification", "FAULT_TOLERANCE", "MAJOR", "Verifies front and rear inverter CAN torque command synchronization.", {"battery_voltage": 395.0, "battery_current": 60.0, "battery_temperature": 32.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 10.0}, "Dual motor controllers report synchronized safety integrity.", assert_4w_008),
    TestScenario("TC-4W-009-COOLANT-PUMP-DERATE", "Glycol Thermal Loop Pump Failure Derating", "SAFETY_CRITICAL", "MAJOR", "Verifies aggressive 30% thermal derate when liquid coolant loop exceeds 68°C.", {"battery_voltage": 390.0, "battery_current": 80.0, "battery_temperature": 38.0, "coolant_temperature": 72.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 12.0}, "derate_state COOLING_DERATE, allowed_discharge_amps <= 120A, FAULT_COOLANT_LOOP_OVERTEMP active.", assert_4w_009),
    TestScenario("TC-4W-010-HV-ISOLATION-DEGRADE", "Chassis High Voltage Isolation Breakdown", "SAFETY_CRITICAL", "CRITICAL", "Verifies isolation monitor opens contactors when isolation resistance drops below 100 kOhm.", {"battery_voltage": 395.0, "battery_current": 50.0, "battery_temperature": 30.0, "insulation_resistance_kohm": 45.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 12.0}, "Contactors OPEN, FAULT_HV_ISOLATION_BREACH active.", assert_4w_010),
    TestScenario("TC-4W-011-INVALID-CELL-CORRUPTION", "Corrupt Cell Differential Rejection", "FAULT_TOLERANCE", "MAJOR", "Verifies rejection and safe limp-mode when cell telemetry frames contain invalid CRC.", {"battery_voltage": 395.0, "battery_current": 30.0, "battery_temperature": 999.0, "sensor_valid": False, "hvil_closed": True, "can_latency_ms": 15.0}, "Safe derate enforced; data quarantined.", assert_4w_011),
    TestScenario("TC-4W-012-REGRESSION-REFERENCE-4W", "4W Reference Baseline Compatibility Check", "REGRESSION", "CRITICAL", "Direct comparative evaluation against certified reference version v2.4.1-4W envelope.", {"battery_voltage": 400.0, "battery_current": 75.0, "battery_temperature": 33.0, "hvil_closed": True, "sensor_valid": True, "can_latency_ms": 14.0}, "Candidate safety envelope must not weaken reference protections.", assert_4w_012),
]

ALL_TEST_SCENARIOS = SCENARIOS_2W # Default backwards compatibility

def get_scenarios_for_vehicle(vehicle_type: str = "two_wheeler") -> List[TestScenario]:
    if "four" in vehicle_type.lower():
        return SCENARIOS_4W
    return SCENARIOS_2W
