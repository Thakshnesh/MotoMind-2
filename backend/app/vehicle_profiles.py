from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class BatterySpecs(BaseModel):
    nominal_voltage: float
    usable_capacity_kwh: float
    chemistry: str
    voltage_min: float
    voltage_max: float
    max_discharge_current_a: float
    max_charge_current_ac_a: float
    dc_fast_charge_supported: bool = False
    max_charge_current_dc_a: float = 0.0
    normal_max_temp: float
    critical_max_temp: float
    internal_resistance: float = 0.04

class MotorSpecs(BaseModel):
    motor_count: int = 1
    configuration: str
    rated_power_kw: float
    peak_power_kw: float
    normal_max_temp: float
    critical_max_temp: float
    cooling_type: str # "air_cooled" or "liquid_glycol_loop"

class DynamicsSpecs(BaseModel):
    curb_weight_kg: float
    nominal_consumption_wh_km: float
    top_speed_kmh: float

class VehicleProfile(BaseModel):
    vehicle_id: str
    vehicle_type: str # "two_wheeler" or "four_wheeler"
    display_name: str
    category_label: str
    battery: BatterySpecs
    motor: MotorSpecs
    dynamics: DynamicsSpecs
    supported_sensors: Dict[str, str] # e.g. {"battery_voltage": "measured", "coolant_temperature": "unavailable"}
    safety_rule_thresholds: Dict[str, Any]

# Built-in Default Profiles
DEFAULT_PROFILES: Dict[str, VehicleProfile] = {
    "E2W-SCOOT-01": VehicleProfile(
        vehicle_id="E2W-SCOOT-01",
        vehicle_type="two_wheeler",
        display_name="Apex Urban 2W (Scooter)",
        category_label="Electric Two-Wheeler",
        battery=BatterySpecs(
            nominal_voltage=52.0,
            usable_capacity_kwh=3.2,
            chemistry="Li-ion 14S NMC",
            voltage_min=42.0,
            voltage_max=58.8,
            max_discharge_current_a=65.0,
            max_charge_current_ac_a=12.0,
            dc_fast_charge_supported=False,
            max_charge_current_dc_a=0.0,
            normal_max_temp=48.0,
            critical_max_temp=55.0,
            internal_resistance=0.045
        ),
        motor=MotorSpecs(
            motor_count=1,
            configuration="Single Mid-Drive BLDC Motor",
            rated_power_kw=4.0,
            peak_power_kw=6.5,
            normal_max_temp=85.0,
            critical_max_temp=105.0,
            cooling_type="air_cooled"
        ),
        dynamics=DynamicsSpecs(
            curb_weight_kg=115.0,
            nominal_consumption_wh_km=32.0,
            top_speed_kmh=85.0
        ),
        supported_sensors={
            "battery_voltage": "measured",
            "battery_current": "measured",
            "battery_temperature": "measured",
            "motor_temperature": "measured",
            "secondary_motor_temperature": "unavailable",
            "coolant_temperature": "unavailable",
            "cabin_temperature": "unavailable",
            "hvac_power_kw": "unavailable",
            "vehicle_speed": "measured",
            "state_of_charge": "estimated",
            "state_of_health": "estimated",
            "ambient_temperature": "measured",
            "moisture_status": "measured",
            "insulation_resistance_kohm": "unavailable"
        },
        safety_rule_thresholds={
            "overtemp_warn": 48.0,
            "overtemp_cutoff": 55.0,
            "motor_warn": 85.0,
            "motor_cutoff": 105.0,
            "max_current": 65.0,
            "voltage_sag_limit": 41.0
        }
    ),
    "E4W-SEDAN-01": VehicleProfile(
        vehicle_id="E4W-SEDAN-01",
        vehicle_type="four_wheeler",
        display_name="VoltCruiser 4W (Sedan)",
        category_label="Electric Four-Wheeler",
        battery=BatterySpecs(
            nominal_voltage=400.0,
            usable_capacity_kwh=64.0,
            chemistry="Li-ion 96S LFP/NMC Pack",
            voltage_min=320.0,
            voltage_max=450.0,
            max_discharge_current_a=320.0,
            max_charge_current_ac_a=32.0,
            dc_fast_charge_supported=True,
            max_charge_current_dc_a=250.0,
            normal_max_temp=45.0,
            critical_max_temp=52.0,
            internal_resistance=0.015
        ),
        motor=MotorSpecs(
            motor_count=2,
            configuration="Dual Motor (Front PMSM + Rear Induction)",
            rated_power_kw=160.0,
            peak_power_kw=240.0,
            normal_max_temp=90.0,
            critical_max_temp=115.0,
            cooling_type="liquid_glycol_loop"
        ),
        dynamics=DynamicsSpecs(
            curb_weight_kg=1850.0,
            nominal_consumption_wh_km=165.0,
            top_speed_kmh=180.0
        ),
        supported_sensors={
            "battery_voltage": "measured",
            "battery_current": "measured",
            "battery_temperature": "measured",
            "motor_temperature": "measured",
            "secondary_motor_temperature": "measured",
            "coolant_temperature": "measured",
            "cabin_temperature": "measured",
            "hvac_power_kw": "measured",
            "vehicle_speed": "measured",
            "state_of_charge": "estimated",
            "state_of_health": "estimated",
            "ambient_temperature": "measured",
            "moisture_status": "unavailable",
            "insulation_resistance_kohm": "measured"
        },
        safety_rule_thresholds={
            "overtemp_warn": 45.0,
            "overtemp_cutoff": 52.0,
            "motor_warn": 90.0,
            "motor_cutoff": 115.0,
            "coolant_warn": 65.0,
            "max_current": 320.0,
            "voltage_sag_limit": 315.0,
            "insulation_resistance_min_kohm": 100.0
        }
    )
}

class VehicleProfileRegistry:
    """Modular registry allowing dynamic registration of additional EV models."""
    def __init__(self):
        self.profiles: Dict[str, VehicleProfile] = dict(DEFAULT_PROFILES)
        self.active_vehicle_id: str = "E2W-SCOOT-01"

    def get_profile(self, vehicle_id: Optional[str] = None) -> VehicleProfile:
        vid = vehicle_id or self.active_vehicle_id
        if vid not in self.profiles:
            # Fallback to first available or 2W
            return list(self.profiles.values())[0]
        return self.profiles[vid]

    def set_active_vehicle(self, vehicle_id: str) -> VehicleProfile:
        if vehicle_id in self.profiles:
            self.active_vehicle_id = vehicle_id
            return self.profiles[vehicle_id]
        raise ValueError(f"Vehicle profile '{vehicle_id}' not found.")

    def list_profiles(self) -> List[Dict[str, Any]]:
        return [
            {
                "vehicle_id": p.vehicle_id,
                "vehicle_type": p.vehicle_type,
                "display_name": p.display_name,
                "category_label": p.category_label,
                "battery_voltage": p.battery.nominal_voltage,
                "capacity_kwh": p.battery.usable_capacity_kwh,
                "motor_configuration": p.motor.configuration,
                "cooling_type": p.motor.cooling_type,
                "is_active": p.vehicle_id == self.active_vehicle_id
            }
            for p in self.profiles.values()
        ]

    def register_profile(self, profile: VehicleProfile):
        self.profiles[profile.vehicle_id] = profile

profile_registry = VehicleProfileRegistry()
