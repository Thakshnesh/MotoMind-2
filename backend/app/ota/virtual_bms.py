from typing import Dict, Any, Tuple

class VirtualBMS:
    """
    Virtual Battery Management System (BMS) & Vehicle Controller Logic Simulator.
    Supports both Electric Two-Wheelers (52V, air-cooled) and Electric Four-Wheelers (400V, liquid-cooled, dual motor, HVIL).
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.version_string = config.get("version_string", "v2.4.1-stable")
        self.vehicle_type = config.get("vehicle_type", "two_wheeler")

        # Thresholds configured by profile
        if self.vehicle_type == "four_wheeler":
            self.max_cell_temp_cutoff = float(config.get("max_cell_temp_cutoff", 52.0))
            self.max_cell_temp_warn = float(config.get("max_cell_temp_warn", 45.0))
            self.min_charge_temp_cutoff = float(config.get("min_charge_temp_cutoff", 0.0))
            self.over_voltage_cutoff = float(config.get("over_voltage_cutoff", 450.0))
            self.under_voltage_cutoff = float(config.get("under_voltage_cutoff", 310.0))
            self.max_discharge_current = float(config.get("max_discharge_current", 320.0))
            self.max_coolant_temp_derate = float(config.get("max_coolant_temp_derate", 68.0))
            self.hvil_enabled = bool(config.get("hvil_enabled", True))
        else: # two_wheeler
            self.max_cell_temp_cutoff = float(config.get("max_cell_temp_cutoff", 55.0))
            self.max_cell_temp_warn = float(config.get("max_cell_temp_warn", 48.0))
            self.min_charge_temp_cutoff = float(config.get("min_charge_temp_cutoff", 0.0))
            self.over_voltage_cutoff = float(config.get("over_voltage_cutoff", 58.8))
            self.under_voltage_cutoff = float(config.get("under_voltage_cutoff", 42.0))
            self.max_discharge_current = float(config.get("max_discharge_current", 65.0))
            self.max_coolant_temp_derate = 999.0
            self.hvil_enabled = False

        self.drive_interlock_on_charge = bool(config.get("drive_interlock_on_charge", True))
        self.can_timeout_threshold_ms = float(config.get("can_timeout_threshold_ms", 250.0))

        # Deliberate regression flags
        self.bypass_overtemp_cutoff = bool(config.get("deliberate_regression_bypass_overtemp", False))
        self.bypass_hvil = bool(config.get("deliberate_regression_bypass_hvil", False))
        self.bypass_drive_interlock = bool(config.get("deliberate_regression_bypass_interlock", False))

    def evaluate_state(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        voltage = float(inputs.get("battery_voltage", 400.0 if self.vehicle_type == "four_wheeler" else 52.0))
        current = float(inputs.get("battery_current", 0.0))
        batt_temp = float(inputs.get("battery_temperature", 30.0))
        coolant_temp = float(inputs.get("coolant_temperature", 32.0))
        charging_plugged = bool(inputs.get("charging_plugged", False))
        hvil_closed = bool(inputs.get("hvil_closed", True))
        can_latency_ms = float(inputs.get("can_latency_ms", 15.0))
        sensor_valid = bool(inputs.get("sensor_valid", True))
        insulation_kohm = float(inputs.get("insulation_resistance_kohm", 500.0))

        active_faults = []
        contactor_open = False
        allowed_discharge_amps = self.max_discharge_current
        allowed_charge_amps = 250.0 if self.vehicle_type == "four_wheeler" else 15.0
        derate_state = "NORMAL"

        # 1. High Voltage Interlock Loop (HVIL - 4W)
        if self.hvil_enabled and not hvil_closed:
            if not self.bypass_hvil:
                active_faults.append("FAULT_HVIL_CIRCUIT_OPEN")
                derate_state = "EMERGENCY_CUTOFF"
                contactor_open = True
                allowed_discharge_amps = 0.0
                allowed_charge_amps = 0.0
            else:
                active_faults.append("WARN_HVIL_IGNORED")

        # 2. Invalid or Stale Sensor Check
        if not sensor_valid:
            active_faults.append("FAULT_BMS_INVALID_SENSOR_DATA")
            derate_state = "LIMP_MODE"
            allowed_discharge_amps = min(allowed_discharge_amps, 20.0)

        # 3. CAN Bus Latency Check
        if can_latency_ms > self.can_timeout_threshold_ms:
            active_faults.append("FAULT_CAN_BUS_TIMEOUT")
            derate_state = "FAILSAFE_STOP"
            contactor_open = True
            allowed_discharge_amps = 0.0

        # 4. Battery Over-Temperature Protection
        if batt_temp >= self.max_cell_temp_cutoff:
            if not self.bypass_overtemp_cutoff:
                active_faults.append("FAULT_THERMAL_RUNAWAY_PROTECTION")
                derate_state = "EMERGENCY_CUTOFF"
                contactor_open = True
                allowed_discharge_amps = 0.0
                allowed_charge_amps = 0.0
            else:
                # REGRESSION DETECTED!
                active_faults.append("WARN_HIGH_TEMP_IGNORED")
                derate_state = "NORMAL"
        elif batt_temp >= self.max_cell_temp_warn:
            active_faults.append("WARN_BATTERY_HIGH_TEMP")
            derate_state = "THERMAL_DERATE"
            allowed_discharge_amps = max(10.0, self.max_discharge_current * 0.5)

        # 5. Coolant Loop Supervision (4W)
        if self.vehicle_type == "four_wheeler" and coolant_temp >= self.max_coolant_temp_derate:
            active_faults.append("FAULT_COOLANT_LOOP_OVERTEMP")
            derate_state = "COOLING_DERATE"
            allowed_discharge_amps = min(allowed_discharge_amps, self.max_discharge_current * 0.3)
            allowed_charge_amps = min(allowed_charge_amps, 25.0)

        # 6. Low-Temperature Charging Inhibit
        if charging_plugged and batt_temp < self.min_charge_temp_cutoff:
            active_faults.append("FAULT_SUBZERO_CHARGE_INHIBIT")
            allowed_charge_amps = 0.0

        # 7. Over-Voltage & Under-Voltage Protection
        if voltage >= self.over_voltage_cutoff:
            active_faults.append("FAULT_OVER_VOLTAGE_PROTECT")
            contactor_open = True
            allowed_charge_amps = 0.0
            allowed_discharge_amps = 0.0
            derate_state = "OVERVOLT_CUTOFF"
        elif voltage <= self.under_voltage_cutoff:
            active_faults.append("FAULT_UNDER_VOLTAGE_CUTOFF")
            derate_state = "UNDERVOLT_CUTOFF"
            contactor_open = True
            allowed_discharge_amps = 0.0

        # 8. Overcurrent Protection
        if current > self.max_discharge_current:
            active_faults.append("FAULT_OVERCURRENT_TRIP")
            contactor_open = True
            allowed_discharge_amps = 0.0
            derate_state = "OVERCURRENT_TRIP"

        # 9. Insulation Resistance (4W)
        if self.vehicle_type == "four_wheeler" and insulation_kohm < 100.0:
            active_faults.append("FAULT_HV_ISOLATION_BREACH")
            contactor_open = True
            allowed_discharge_amps = 0.0
            derate_state = "ISOLATION_CUTOFF"

        # 10. Drive Interlock on Charging
        if charging_plugged and self.drive_interlock_on_charge:
            if not self.bypass_drive_interlock:
                allowed_discharge_amps = 0.0
                active_faults.append("INFO_DRIVE_INTERLOCK_ENGAGED")

        return {
            "version": self.version_string,
            "vehicle_type": self.vehicle_type,
            "contactor_open": contactor_open,
            "derate_state": derate_state,
            "allowed_discharge_amps": allowed_discharge_amps,
            "allowed_charge_amps": allowed_charge_amps,
            "active_faults": active_faults,
            "safety_integrity_ok": not contactor_open and "FAULT_THERMAL_RUNAWAY_PROTECTION" not in active_faults and "FAULT_HVIL_CIRCUIT_OPEN" not in active_faults
        }
