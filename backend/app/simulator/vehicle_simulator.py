import time
import math
import random
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..schemas.telemetry import TelemetryDataPoint
from ..vehicle_profiles import profile_registry, VehicleProfile

def utc_now():
    return datetime.now(timezone.utc)

class VehiclePhysicalState:
    def __init__(self, profile: VehicleProfile):
        self.profile = profile
        self.vehicle_id = profile.vehicle_id
        self.vehicle_type = profile.vehicle_type
        self.is_running = True
        self.tick_count = 0
        self.current_profile = "city_commute"
        self.service_mode_active = False
        self.active_injected_fault: Optional[str] = None
        self.fault_expiry_tick: int = 0

        # Physical states
        self.soc = 85.0 # %
        self.soh = 97.2 # %
        self.ambient_temp = 28.5 # °C
        self.speed = 0.0 # km/h

        if profile.vehicle_type == "four_wheeler":
            self.battery_temp = 29.5
            self.motor_temp = 36.0 # Front
            self.secondary_motor_temp = 35.0 # Rear
            self.coolant_temp = 31.0 # Liquid loop
            self.cabin_temp = 22.5 # HVAC target
            self.hvac_power_kw = 1.8
            self.insulation_resistance_kohm = 550.0
            self.moisture_status = "unavailable"
        else: # two_wheeler
            self.battery_temp = 31.0
            self.motor_temp = 38.0
            self.secondary_motor_temp = None
            self.coolant_temp = None
            self.cabin_temp = None
            self.hvac_power_kw = None
            self.insulation_resistance_kohm = None
            self.moisture_status = "dry"

        self.sensor_fault_active = False
        self.fault_codes: List[str] = []
        self.latest_telemetry: Optional[TelemetryDataPoint] = None
        self.history_buffer: List[Dict[str, Any]] = []

class MultiVehicleSimulator:
    """
    MotoMind Multi-Vehicle Physics Simulator.
    Supports Electric Two-Wheelers (E2W: 52V pack, air-cooled, single motor)
    and Electric Four-Wheelers (E4W: 400V pack, liquid-cooled, dual motor, HVAC).
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.vehicles: Dict[str, VehiclePhysicalState] = {}
        for p in profile_registry.profiles.values():
            self.vehicles[p.vehicle_id] = VehiclePhysicalState(p)

        self.active_vehicle_id = profile_registry.active_vehicle_id
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        v = self.get_active_state()
        return v.is_running if v else True

    @property
    def current_profile(self) -> str:
        v = self.get_active_state()
        return v.current_profile if v else "city_commute"

    @property
    def service_mode_active(self) -> bool:
        v = self.get_active_state()
        return v.service_mode_active if v else False

    @property
    def active_injected_fault(self) -> Optional[str]:
        v = self.get_active_state()
        return v.active_injected_fault if v else None

    @property
    def tick_count(self) -> int:
        v = self.get_active_state()
        return v.tick_count if v else 0

    @property
    def latest_telemetry(self) -> Optional[TelemetryDataPoint]:
        v = self.get_active_state()
        return v.latest_telemetry if v else None

    @property
    def history_buffer(self) -> List[Dict[str, Any]]:
        v = self.get_active_state()
        return v.history_buffer if v else []

    @property
    def soc(self) -> float:
        v = self.get_active_state()
        return v.soc if v else 85.0

    @property
    def soh(self) -> float:
        v = self.get_active_state()
        return v.soh if v else 100.0

    @property
    def speed(self) -> float:
        v = self.get_active_state()
        return v.speed if v else 0.0

    @property
    def battery_temp(self) -> float:
        v = self.get_active_state()
        return v.battery_temp if v else 30.0

    @property
    def motor_temp(self) -> float:
        v = self.get_active_state()
        return v.motor_temp if v else 35.0

    def get_state(self, vehicle_id: Optional[str] = None) -> VehiclePhysicalState:
        vid = vehicle_id or self.active_vehicle_id
        if vid not in self.vehicles:
            p = profile_registry.get_profile(vid)
            self.vehicles[vid] = VehiclePhysicalState(p)
        return self.vehicles[vid]

    def get_active_state(self) -> VehiclePhysicalState:
        return self.get_state(self.active_vehicle_id)

    def set_active_vehicle(self, vehicle_id: str):
        with self._lock:
            profile_registry.set_active_vehicle(vehicle_id)
            self.active_vehicle_id = vehicle_id
            if vehicle_id not in self.vehicles:
                p = profile_registry.get_profile(vehicle_id)
                self.vehicles[vehicle_id] = VehiclePhysicalState(p)
            return profile_registry.get_profile(vehicle_id)

    def start(self, vehicle_id: Optional[str] = None):
        with self._lock:
            v = self.get_state(vehicle_id)
            v.is_running = True

    def pause(self, vehicle_id: Optional[str] = None):
        with self._lock:
            v = self.get_state(vehicle_id)
            v.is_running = False

    def reset(self, vehicle_id: Optional[str] = None):
        with self._lock:
            vid = vehicle_id or self.active_vehicle_id
            p = profile_registry.get_profile(vid)
            self.vehicles[vid] = VehiclePhysicalState(p)
            self.vehicles[vid].is_running = True

    def set_profile(self, profile_name: str, vehicle_id: Optional[str] = None):
        with self._lock:
            v = self.get_state(vehicle_id)
            v.current_profile = profile_name
            if profile_name in ["idle_charging", "dc_fast_charging"]:
                v.speed = 0.0

    def set_service_mode(self, active: bool, vehicle_id: Optional[str] = None):
        with self._lock:
            v = self.get_state(vehicle_id)
            v.service_mode_active = active
            if active:
                v.speed = 0.0

    def inject_fault(self, fault_type: str, duration_seconds: int = 30, vehicle_id: Optional[str] = None):
        with self._lock:
            v = self.get_state(vehicle_id)
            v.active_injected_fault = fault_type
            v.fault_expiry_tick = v.tick_count + duration_seconds

    def clear_fault(self, vehicle_id: Optional[str] = None):
        with self._lock:
            v = self.get_state(vehicle_id)
            v.active_injected_fault = None
            v.sensor_fault_active = False
            v.fault_codes = [c for c in v.fault_codes if not c.startswith("FAULT_") and not c.startswith("WARN_")]

    def step(self, vehicle_id: Optional[str] = None) -> TelemetryDataPoint:
        with self._lock:
            v = self.get_state(vehicle_id)
            v.tick_count += 1
            now = utc_now()
            p = v.profile

            # Check fault expiry
            if v.active_injected_fault and v.tick_count >= v.fault_expiry_tick:
                v.active_injected_fault = None
                v.sensor_fault_active = False
                v.fault_codes = []
                if v.vehicle_type == "two_wheeler":
                    v.moisture_status = "dry"

            # 1. Profile Dynamics
            charging_status = "idle"
            operating_context = "city_commute"
            current_amps = 0.0

            if v.service_mode_active:
                target_speed = 0.0
                current_amps = 0.0
                charging_status = "service_hold"
                operating_context = "maintenance_service"
            elif v.current_profile == "idle_charging":
                target_speed = 0.0
                # AC charging: 2W ~12A (650W), 4W ~32A (7.4 kW / 11 kW)
                current_amps = -p.battery.max_charge_current_ac_a * 0.95
                charging_status = "charging"
                operating_context = "ac_grid_charging"
            elif v.current_profile == "dc_fast_charging" and p.battery.dc_fast_charge_supported:
                target_speed = 0.0
                # DC Fast charging 4W: ~150-200A into 400V pack (~60-80 kW)
                current_amps = -p.battery.max_charge_current_dc_a * 0.75
                charging_status = "fast_charging"
                operating_context = "dc_fast_charging_ccs2"
            elif v.current_profile == "aggressive_sport":
                phase = (v.tick_count % 30) / 30.0
                max_spd = p.dynamics.top_speed_kmh
                target_speed = (max_spd * 0.55) + (max_spd * 0.4) * math.sin(phase * 2 * math.pi)
                target_speed = max(10.0, min(max_spd * 0.95, target_speed + random.uniform(-4, 4)))
                current_amps = (p.battery.max_discharge_current_a * 0.45) + (target_speed / max_spd) * (p.battery.max_discharge_current_a * 0.5)
                charging_status = "discharging"
                operating_context = "high_performance_sport"
            elif v.current_profile == "eco_cruising":
                target_speed = (42.0 if v.vehicle_type == "two_wheeler" else 95.0) + random.uniform(-2, 2)
                current_amps = p.battery.max_discharge_current_a * 0.22 + random.uniform(-1.5, 1.5)
                charging_status = "discharging"
                operating_context = "eco_cruising"
            else: # city_commute
                cycle = v.tick_count % 40
                max_city_spd = 50.0 if v.vehicle_type == "two_wheeler" else 65.0
                if cycle < 10:
                    target_speed = 0.0
                    current_amps = 1.0 if v.vehicle_type == "two_wheeler" else 4.5 # Auxiliary + HVAC
                elif cycle < 22:
                    target_speed = min(max_city_spd, (cycle - 10) * (max_city_spd / 12.0))
                    current_amps = p.battery.max_discharge_current_a * 0.45 + random.uniform(-2, 3)
                elif cycle < 34:
                    target_speed = max_city_spd * 0.8 + random.uniform(-2, 2)
                    current_amps = p.battery.max_discharge_current_a * 0.25 + random.uniform(-1, 2)
                else:
                    target_speed = max(0.0, max_city_spd * 0.8 - (cycle - 34) * 8.0)
                    current_amps = -p.battery.max_discharge_current_a * 0.2 # Regen braking
                charging_status = "discharging" if current_amps > 0 else ("regen" if current_amps < 0 else "idle")
                operating_context = "city_stop_go"

            # Apply smooth speed interpolation
            v.speed = max(0.0, round(v.speed + 0.35 * (target_speed - v.speed), 1))

            # 2. Coulomb counting SOC
            pack_ah = (p.battery.usable_capacity_kwh * 1000.0) / p.battery.nominal_voltage
            dt_hours = 1.0 / 3600.0
            soc_delta = (current_amps * dt_hours / pack_ah) * 100.0
            v.soc = max(1.0, min(100.0, v.soc - soc_delta))

            # 3. Terminal Voltage (Voc - IR sag)
            v_span = p.battery.voltage_max - p.battery.voltage_min
            voc = p.battery.voltage_min + (v.soc / 100.0) * v_span
            voltage_sag = current_amps * p.battery.internal_resistance
            battery_voltage = round(voc - voltage_sag, 2)

            # 4. Thermal Dynamics
            # Heat generation = I^2 * R
            heat_gen_batt = (current_amps ** 2) * p.battery.internal_resistance * 0.0003
            cooling_rate = 0.02 * (v.battery_temp - v.ambient_temp) + (v.speed * 0.0005)
            v.battery_temp += (heat_gen_batt - cooling_rate)
            v.battery_temp = max(v.ambient_temp - 2.0, v.battery_temp)

            # Motor heating
            motor_power_kw = (battery_voltage * max(0.0, current_amps)) / 1000.0
            heat_gen_motor = (motor_power_kw ** 1.25) * (0.07 if v.vehicle_type == "two_wheeler" else 0.02)
            cool_motor = 0.03 * (v.motor_temp - v.ambient_temp) + (v.speed * 0.002)
            v.motor_temp += (heat_gen_motor - cool_motor)
            v.motor_temp = max(v.ambient_temp - 1.0, v.motor_temp)

            # E4W Specific Secondary Motor & Coolant Loop
            if v.vehicle_type == "four_wheeler":
                # Rear motor
                v.secondary_motor_temp = max(v.ambient_temp, round(v.motor_temp * 0.96 + random.uniform(-0.5, 0.5), 1))
                # Glycol coolant loop
                target_coolant = (v.battery_temp + v.motor_temp) * 0.55
                v.coolant_temp = round(v.coolant_temp + 0.1 * (target_coolant - v.coolant_temp), 1)
                # Cabin HVAC
                v.cabin_temp = 22.0 + (0.5 if v.ambient_temp > 30 else 0)
                v.hvac_power_kw = round(1.5 + (0.8 if v.ambient_temp > 32 else 0), 1)
                v.insulation_resistance_kohm = 520.0 + random.uniform(-10, 10)

            # 5. Fault Injection Overrides
            fault_codes = list(v.fault_codes)
            sensor_fault = False
            moisture = v.moisture_status
            data_source = "simulated"

            if v.active_injected_fault == "over_temp_battery":
                v.battery_temp += random.uniform(1.8, 3.2)
                if v.battery_temp >= p.battery.normal_max_temp and "BMS_WARN_HIGH_TEMP" not in fault_codes:
                    fault_codes.append("BMS_WARN_HIGH_TEMP")
                if v.battery_temp >= p.battery.critical_max_temp and "BMS_CRITICAL_OVERHEAT" not in fault_codes:
                    fault_codes.append("BMS_CRITICAL_OVERHEAT")

            elif v.active_injected_fault == "motor_overheat":
                v.motor_temp += random.uniform(2.5, 4.0)
                if v.motor_temp >= p.motor.normal_max_temp and "MOTOR_WARN_OVERTEMP" not in fault_codes:
                    fault_codes.append("MOTOR_WARN_OVERTEMP")
                if v.motor_temp >= p.motor.critical_max_temp and "MOTOR_CRITICAL_SHUTDOWN" not in fault_codes:
                    fault_codes.append("MOTOR_CRITICAL_SHUTDOWN")

            elif v.active_injected_fault == "coolant_pump_failure" and v.vehicle_type == "four_wheeler":
                v.coolant_temp += random.uniform(2.5, 4.5)
                v.battery_temp += 1.5
                if "THERMAL_LOOP_PUMP_COMM_LOSS" not in fault_codes:
                    fault_codes.append("THERMAL_LOOP_PUMP_COMM_LOSS")
                if v.coolant_temp > 65.0 and "COOLANT_OVERTEMP_DERATE" not in fault_codes:
                    fault_codes.append("COOLANT_OVERTEMP_DERATE")

            elif v.active_injected_fault == "secondary_motor_overheat" and v.vehicle_type == "four_wheeler":
                v.secondary_motor_temp = (v.secondary_motor_temp or 40.0) + random.uniform(3.0, 5.0)
                if "REAR_INVERTER_OVERTEMP" not in fault_codes:
                    fault_codes.append("REAR_INVERTER_OVERTEMP")

            elif v.active_injected_fault == "insulation_loss" and v.vehicle_type == "four_wheeler":
                v.insulation_resistance_kohm = round(random.uniform(25.0, 48.0), 1) # Critical < 100 kOhm
                if "HV_ISOLATION_FAULT_CRITICAL" not in fault_codes:
                    fault_codes.append("HV_ISOLATION_FAULT_CRITICAL")

            elif v.active_injected_fault == "sudden_voltage_sag":
                sag_amt = 12.0 if v.vehicle_type == "two_wheeler" else 65.0
                battery_voltage = round(max(p.battery.voltage_min - 5.0, battery_voltage - sag_amt), 1)
                if "BMS_UNDERVOLTAGE_SAG" not in fault_codes:
                    fault_codes.append("BMS_UNDERVOLTAGE_SAG")

            elif v.active_injected_fault == "high_discharge_current":
                current_amps = round(p.battery.max_discharge_current_a * 1.35, 1)
                if "OVERCURRENT_DISCHARGE_FAULT" not in fault_codes:
                    fault_codes.append("OVERCURRENT_DISCHARGE_FAULT")

            elif v.active_injected_fault == "moisture_detected":
                moisture = "wet"
                if "CHASSIS_MOISTURE_INGRESS_WARNING" not in fault_codes:
                    fault_codes.append("CHASSIS_MOISTURE_INGRESS_WARNING")

            elif v.active_injected_fault == "sensor_drift":
                v.battery_temp += 0.9
                sensor_fault = True
                if "TEMP_SENSOR_ANALOG_DRIFT" not in fault_codes:
                    fault_codes.append("TEMP_SENSOR_ANALOG_DRIFT")

            elif v.active_injected_fault == "sensor_disconnect":
                sensor_fault = True
                data_source = "unavailable"
                if "CAN_SENSOR_DISCONNECT" not in fault_codes:
                    fault_codes.append("CAN_SENSOR_DISCONNECT")

            # Calculate Wh/km
            power_kw = round((battery_voltage * current_amps) / 1000.0, 2)
            temp_delta = round(v.battery_temp - v.ambient_temp, 1)

            if v.speed > 5.0 and power_kw > 0:
                wh_km = round((power_kw * 1000.0) / v.speed, 1)
                min_wh = 18.0 if v.vehicle_type == "two_wheeler" else 110.0
                max_wh = 80.0 if v.vehicle_type == "two_wheeler" else 350.0
                wh_km = max(min_wh, min(max_wh, wh_km))
            else:
                wh_km = p.dynamics.nominal_consumption_wh_km

            # Sensor availability dictionary
            sensor_avail = dict(p.supported_sensors)
            if sensor_fault:
                sensor_avail["battery_temperature"] = "unavailable"
                sensor_avail["battery_voltage"] = "unavailable"

            point = TelemetryDataPoint(
                timestamp=now,
                vehicle_id=v.vehicle_id,
                vehicle_type=v.vehicle_type,
                battery_voltage=battery_voltage,
                battery_current=round(current_amps, 1),
                battery_temperature=round(v.battery_temp, 1),
                state_of_charge=round(v.soc, 1),
                state_of_health=round(v.soh, 1),
                motor_temperature=round(v.motor_temp, 1),
                secondary_motor_temperature=v.secondary_motor_temp,
                coolant_temperature=v.coolant_temp,
                cabin_temperature=v.cabin_temp,
                hvac_power_kw=v.hvac_power_kw,
                insulation_resistance_kohm=v.insulation_resistance_kohm,
                vehicle_speed=round(v.speed, 1),
                energy_consumption=wh_km,
                charging_status=charging_status,
                ambient_temperature=round(v.ambient_temp, 1),
                moisture_status=moisture,
                sensor_fault_status=sensor_fault,
                fault_codes=fault_codes,
                power_kw=power_kw,
                temp_delta=temp_delta,
                data_source_type=data_source,
                sensor_availability=sensor_avail,
                operating_context=operating_context,
                service_mode_active=v.service_mode_active
            )

            v.latest_telemetry = point
            v.history_buffer.append(point.model_dump())
            if len(v.history_buffer) > 150:
                v.history_buffer.pop(0)

            return point

    def get_status(self, vehicle_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            v = self.get_state(vehicle_id)
            return {
                "is_running": v.is_running,
                "active_vehicle_id": v.vehicle_id,
                "active_vehicle_type": v.vehicle_type,
                "current_profile": v.current_profile,
                "active_injected_fault": v.active_injected_fault,
                "tick_count": v.tick_count,
                "service_mode_active": v.service_mode_active,
                "latest_telemetry": v.latest_telemetry.model_dump() if v.latest_telemetry else None,
                "available_vehicles": profile_registry.list_profiles(),
                "data_source_indicator": "SYNTHETIC_SIMULATION",
                "disclaimer": "All values generated by MotoMind Multi-Vehicle Synthetic Physics Simulator for prototype evaluation."
            }

    def start_background_loop(self, db_callback=None):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()

        def _run():
            while not self._stop_event.is_set():
                # Step all registered vehicles in parallel/sequence
                with self._lock:
                    v_ids = list(self.vehicles.keys())
                for vid in v_ids:
                    try:
                        v = self.vehicles.get(vid)
                        if v and v.is_running:
                            pt = self.step(vid)
                            if db_callback and vid == self.active_vehicle_id:
                                db_callback(pt)
                    except Exception:
                        pass
                time.sleep(1.0)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_background_loop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

# Global singleton simulator instance
vehicle_simulator = MultiVehicleSimulator()
VehicleSimulator = MultiVehicleSimulator
