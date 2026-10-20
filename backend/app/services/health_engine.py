import datetime
from typing import Dict, Any, List, Tuple, Optional
from ..vehicle_profiles import profile_registry
from ..ml.anomaly_model import anomaly_engine
from ..models.database import HealthAssessmentRecord, AnomalyEvent

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class HealthEngine:
    """
    Adaptive Multi-Vehicle EV Health Monitoring Engine.
    Adapts deterministic safety assertions and AI scoring to each vehicle's
    specific sensor configuration (2W air-cooled vs 4W liquid-cooled dual motor).
    """
    def __init__(self):
        self.last_assessments: Dict[str, Dict[str, Any]] = {}

    def assess_telemetry(self, point: Dict[str, Any], db_session=None) -> Dict[str, Any]:
        vehicle_id = point.get("vehicle_id", "E2W-SCOOT-01")
        profile = profile_registry.get_profile(vehicle_id)
        v_type = profile.vehicle_type

        reasons = []
        rule_violations = []
        triggered_values = {}

        # 0. Data Availability Check
        if point.get("data_source_type") == "unavailable" or point.get("sensor_fault_status") is True:
            result = {
                "timestamp": utc_now(),
                "vehicle_id": vehicle_id,
                "vehicle_type": v_type,
                "overall_status": "Insufficient Data",
                "battery_health_score": 75.0,
                "motor_health_score": 75.0,
                "electrical_health_score": 50.0,
                "thermal_management_score": 70.0 if v_type == "four_wheeler" else None,
                "anomaly_detected": True,
                "anomaly_score": 0.85,
                "reasons": ["Sensor disconnect or invalid signal data detected on vehicle CAN/sensor bus."],
                "triggered_values": {"sensor_fault_status": True},
                "rule_violations": ["SENSOR_BUS_DISCONNECT"],
                "disclaimer": "Informational estimate only. Not a confirmed mechanical diagnosis."
            }
            self.last_assessments[vehicle_id] = result
            return result

        batt_voltage = float(point.get("battery_voltage", profile.battery.nominal_voltage))
        batt_current = float(point.get("battery_current", 0.0))
        batt_temp = float(point.get("battery_temperature", 30.0))
        motor_temp = float(point.get("motor_temperature", 35.0))
        speed = float(point.get("vehicle_speed", 0.0))
        soc = float(point.get("state_of_charge", 80.0))
        fault_codes = point.get("fault_codes", [])

        # 1. Deterministic Rule Checks (Tailored to vehicle profile)
        p_thresholds = profile.safety_rule_thresholds

        # Battery Temperature
        overtemp_crit = p_thresholds.get("overtemp_cutoff", profile.battery.critical_max_temp)
        overtemp_warn = p_thresholds.get("overtemp_warn", profile.battery.normal_max_temp)
        if batt_temp >= overtemp_crit:
            reasons.append(f"Battery temperature {batt_temp}°C exceeds critical limit ({overtemp_crit}°C).")
            rule_violations.append("CRITICAL_BATTERY_OVERTEMP")
            triggered_values["battery_temperature"] = batt_temp
        elif batt_temp >= overtemp_warn:
            reasons.append(f"Battery temperature {batt_temp}°C approaching thermal warning threshold ({overtemp_warn}°C).")
            rule_violations.append("WARN_BATTERY_HIGH_TEMP")
            triggered_values["battery_temperature"] = batt_temp

        # Motor Temperature (Primary)
        motor_crit = p_thresholds.get("motor_cutoff", profile.motor.critical_max_temp)
        motor_warn = p_thresholds.get("motor_warn", profile.motor.normal_max_temp)
        if motor_temp >= motor_crit:
            reasons.append(f"Primary motor temp {motor_temp}°C exceeds critical limit ({motor_crit}°C).")
            rule_violations.append("CRITICAL_MOTOR_OVERTEMP")
            triggered_values["motor_temperature"] = motor_temp
        elif motor_temp >= motor_warn:
            reasons.append(f"Primary motor temp {motor_temp}°C elevated under operating load.")
            rule_violations.append("WARN_MOTOR_HIGH_TEMP")
            triggered_values["motor_temperature"] = motor_temp

        # Secondary Motor (Only if present in profile)
        sec_motor_temp = point.get("secondary_motor_temperature")
        if sec_motor_temp is not None and str(sec_motor_temp).lower() != "unavailable":
            sec_temp_f = float(sec_motor_temp)
            if sec_temp_f >= motor_crit:
                reasons.append(f"Secondary rear motor temp {sec_temp_f}°C exceeds critical threshold.")
                rule_violations.append("CRITICAL_REAR_MOTOR_OVERTEMP")
                triggered_values["secondary_motor_temperature"] = sec_temp_f

        # Coolant Loop (Only if present in profile - 4W)
        coolant_temp = point.get("coolant_temperature")
        coolant_score = 100.0
        if coolant_temp is not None and str(coolant_temp).lower() != "unavailable":
            c_temp_f = float(coolant_temp)
            if c_temp_f >= 78.0:
                reasons.append(f"Coolant loop temperature {c_temp_f}°C critical! Potential pump failure or fluid blockage.")
                rule_violations.append("CRITICAL_COOLANT_OVERTEMP")
                triggered_values["coolant_temperature"] = c_temp_f
                coolant_score = 35.0
            elif c_temp_f >= 65.0:
                reasons.append(f"Coolant loop temperature {c_temp_f}°C high.")
                rule_violations.append("WARN_COOLANT_HIGH_TEMP")
                triggered_values["coolant_temperature"] = c_temp_f
                coolant_score = 70.0

        # High Voltage Insulation Resistance (4W)
        insulation_kohm = point.get("insulation_resistance_kohm")
        if insulation_kohm is not None and str(insulation_kohm).lower() != "unavailable":
            ins_f = float(insulation_kohm)
            min_ins = p_thresholds.get("insulation_resistance_min_kohm", 100.0)
            if ins_f < min_ins:
                reasons.append(f"HV insulation resistance {ins_f} kOhm below safety threshold ({min_ins} kOhm). Isolation degraded.")
                rule_violations.append("CRITICAL_HV_ISOLATION_FAULT")
                triggered_values["insulation_resistance_kohm"] = ins_f

        # Voltage Sag
        sag_limit = p_thresholds.get("voltage_sag_limit", profile.battery.voltage_min)
        if batt_voltage < sag_limit and soc > 15.0:
            reasons.append(f"Abnormal voltage sag ({batt_voltage}V) observed at {soc}% SOC.")
            rule_violations.append("ABNORMAL_VOLTAGE_SAG")
            triggered_values["battery_voltage"] = batt_voltage

        # Overcurrent
        max_i = p_thresholds.get("max_current", profile.battery.max_discharge_current_a)
        if batt_current > max_i:
            reasons.append(f"Discharge current {batt_current}A exceeds rated pack limit ({max_i}A).")
            rule_violations.append("OVERCURRENT_EXCEEDED")
            triggered_values["battery_current"] = batt_current

        # Moisture (2W chassis/flood)
        moisture = point.get("moisture_status")
        if moisture == "wet":
            reasons.append("Moisture sensor triggered wet status. Potential chassis or connector water exposure.")
            rule_violations.append("CHASSIS_MOISTURE_EXPOSURE")
            triggered_values["moisture_status"] = "wet"

        # Active diagnostic codes
        for code in fault_codes:
            if code not in rule_violations:
                rule_violations.append(code)
                reasons.append(f"Diagnostic Code active: {code}")

        # 2. Vehicle-Specific Self-Learning AI Anomaly Detection
        is_ml_anomaly, ml_score, deviations = anomaly_engine.predict_point(point, v_type)
        if is_ml_anomaly:
            dev_str = ", ".join([f"{k} ({v['direction']}: z={v['z_score']})" for k, v in deviations.items()])
            reasons.append(f"Self-learning Isolation Forest ({v_type}) flagged outlier (Score: {ml_score}). Deviations: {dev_str or 'multivariate interaction'}.")
            triggered_values["ml_deviations"] = deviations
            triggered_values["ml_score"] = ml_score

        # 3. Subsystem Health Calculations
        batt_deductions = 0.0
        if batt_temp >= overtemp_crit:
            batt_deductions += 45.0
        elif batt_temp >= overtemp_warn:
            batt_deductions += 18.0
        if "ABNORMAL_VOLTAGE_SAG" in rule_violations:
            batt_deductions += 25.0
        if "BMS_CELL_DELTA_V_IMBALANCE" in fault_codes:
            batt_deductions += 20.0
        battery_health_score = max(10.0, round(100.0 - batt_deductions, 1))

        motor_deductions = 0.0
        if motor_temp >= motor_crit or "CRITICAL_REAR_MOTOR_OVERTEMP" in rule_violations:
            motor_deductions += 50.0
        elif motor_temp >= motor_warn:
            motor_deductions += 20.0
        motor_health_score = max(10.0, round(100.0 - motor_deductions, 1))

        elec_deductions = 0.0
        if "OVERCURRENT_EXCEEDED" in rule_violations:
            elec_deductions += 35.0
        if "CRITICAL_HV_ISOLATION_FAULT" in rule_violations:
            elec_deductions += 45.0
        if moisture == "wet":
            elec_deductions += 25.0
        if is_ml_anomaly:
            elec_deductions += 15.0
        electrical_health_score = max(10.0, round(100.0 - elec_deductions, 1))

        # 4. Overall Status Determination
        has_critical = any("CRITICAL" in v for v in rule_violations) or ml_score >= 0.85
        has_warning = len(rule_violations) > 0 or is_ml_anomaly or ml_score >= 0.65

        if has_critical:
            overall_status = "High Anomaly"
        elif has_warning:
            overall_status = "Warning"
        else:
            overall_status = "Normal"

        assessment = {
            "timestamp": utc_now(),
            "vehicle_id": vehicle_id,
            "vehicle_type": v_type,
            "overall_status": overall_status,
            "battery_health_score": battery_health_score,
            "motor_health_score": motor_health_score,
            "electrical_health_score": electrical_health_score,
            "thermal_management_score": coolant_score if v_type == "four_wheeler" else None,
            "anomaly_detected": has_critical or has_warning,
            "anomaly_score": ml_score,
            "reasons": reasons,
            "triggered_values": triggered_values,
            "rule_violations": rule_violations,
            "disclaimer": "Informational estimate only. Not a confirmed mechanical diagnosis."
        }

        self.last_assessments[vehicle_id] = assessment

        if db_session and (has_critical or has_warning) and len(reasons) > 0:
            try:
                event = AnomalyEvent(
                    timestamp=assessment["timestamp"],
                    vehicle_id=vehicle_id,
                    vehicle_type=v_type,
                    severity="CRITICAL" if has_critical else "WARNING",
                    category="THERMAL_OVERHEAT" if "OVERTEMP" in str(rule_violations) else ("ELECTRICAL_CURRENT" if "OVERCURRENT" in str(rule_violations) else "ML_OUTLIER"),
                    title=f"{profile.category_label} Alert: {overall_status}",
                    description="; ".join(reasons[:2]),
                    anomaly_score=ml_score,
                    features_involved=triggered_values
                )
                db_session.add(event)
                db_session.commit()
            except Exception:
                db_session.rollback()

        return assessment

health_engine = HealthEngine()
