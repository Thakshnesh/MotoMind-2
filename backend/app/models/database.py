import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from ..config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True) # two_wheeler, four_wheeler
    battery_voltage = Column(Float, nullable=False)        # Volts
    battery_current = Column(Float, nullable=False)        # Amps (positive discharge, negative charge)
    battery_temperature = Column(Float, nullable=False)    # °C
    state_of_charge = Column(Float, nullable=False)        # % (0-100)
    state_of_health = Column(Float, nullable=True)         # % (0-100), optional
    motor_temperature = Column(Float, nullable=False)      # °C (Primary/Front)
    secondary_motor_temperature = Column(Float, nullable=True) # °C (Rear/Secondary - 4W)
    coolant_temperature = Column(Float, nullable=True)     # °C (Liquid Cooling Loop - 4W)
    cabin_temperature = Column(Float, nullable=True)       # °C (HVAC - 4W)
    hvac_power_kw = Column(Float, nullable=True)           # kW (4W)
    insulation_resistance_kohm = Column(Float, nullable=True) # kOhm (4W HV Isolation)
    vehicle_speed = Column(Float, nullable=False)          # km/h
    energy_consumption = Column(Float, nullable=False)     # Wh/km
    charging_status = Column(String(32), default="idle")   # idle, discharging, charging, fast_charging
    ambient_temperature = Column(Float, default=28.0)      # °C
    moisture_status = Column(String(32), default="dry")    # dry, damp, wet (2W chassis/flood)
    sensor_fault_status = Column(Boolean, default=False)
    fault_codes = Column(JSON, default=list)               # e.g. ["BMS_OVERHEAT"]
    power_kw = Column(Float, default=0.0)                  # V * A / 1000
    temp_delta = Column(Float, default=0.0)                # battery_temp - ambient_temp
    data_source_type = Column(String(32), default="simulated") # simulated, estimated, measured, unavailable
    sensor_availability = Column(JSON, default=dict)       # Individual sensor mapping
    operating_context = Column(String(64), default="normal_cruising")
    service_mode_active = Column(Boolean, default=False)

class HealthAssessmentRecord(Base):
    __tablename__ = "health_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True)
    overall_status = Column(String(32), nullable=False)    # Normal, Warning, High Anomaly, Insufficient Data
    battery_health_score = Column(Float, default=100.0)    # 0 - 100
    motor_health_score = Column(Float, default=100.0)      # 0 - 100
    electrical_health_score = Column(Float, default=100.0) # 0 - 100
    thermal_management_score = Column(Float, nullable=True) # 0 - 100 (for liquid cooled 4W)
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)             # Model anomaly score
    reasons = Column(JSON, default=list)                   # list of strings explaining issues
    triggered_values = Column(JSON, default=dict)          # {battery_temperature: 52.3}
    rule_violations = Column(JSON, default=list)           # Deterministic violations
    disclaimer = Column(String(256), default="Informational estimate only. Not a confirmed mechanical diagnosis.")

class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True)
    severity = Column(String(32), default="WARNING")       # INFO, WARNING, CRITICAL
    category = Column(String(64), nullable=False)          # BATTERY_THERMAL, MOTOR_OVERHEAT, VOLTAGE_SAG, CURRENT_SPIKE, SENSOR_FAULT, ML_OUTLIER
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    anomaly_score = Column(Float, default=0.0)
    features_involved = Column(JSON, default=dict)
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)

class ComponentRecord(Base):
    __tablename__ = "component_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True)
    component_type = Column(String(64), nullable=False)    # BATTERY_PACK, TRACTION_MOTOR, BMS_MODULE, MOTOR_CONTROLLER, COOLANT_PUMP
    serial_number = Column(String(64), unique=True, nullable=False)
    installed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    retired_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    baseline_established_at = Column(DateTime, nullable=True)
    nominal_specs = Column(JSON, default=dict)
    notes = Column(Text, nullable=True)

class ServiceRecord(Base):
    __tablename__ = "service_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True)
    service_type = Column(String(64), nullable=False)      # ROUTINE_MAINTENANCE, WATER_WASH, REPAIR, INSPECTION, COMPONENT_REPLACEMENT, COOLANT_FLUSH
    description = Column(Text, nullable=False)
    technician_notes = Column(Text, nullable=True)
    odometer_km = Column(Float, default=0.0)
    pre_service_health_score = Column(Float, nullable=True)
    post_service_health_score = Column(Float, nullable=True)
    component_replaced_id = Column(Integer, ForeignKey("component_records.id"), nullable=True)
    is_service_mode_session = Column(Boolean, default=False)

class WaterExposureRecord(Base):
    __tablename__ = "water_exposure_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True)
    exposure_type = Column(String(64), nullable=False)     # PRESSURE_WASH, RAIN_RIDE, FLOOD_WATER, WASHING, UNDERBODY_SPRAY
    severity_level = Column(String(32), default="MODERATE")# LOW, MODERATE, HIGH
    duration_minutes = Column(Integer, default=15)
    moisture_sensor_reading = Column(String(32), default="damp")
    post_exposure_inspected = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    disclaimer = Column(String(256), default="Exposure recording does not confirm physical water ingress or damage.")

class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    vehicle_id = Column(String(64), default="E2W-SCOOT-01", index=True)
    vehicle_type = Column(String(32), default="two_wheeler", index=True)
    start_time = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    end_time = Column(DateTime, nullable=True)
    start_soc = Column(Float, nullable=False)
    end_soc = Column(Float, nullable=True)
    energy_added_kwh = Column(Float, default=0.0)
    charger_type = Column(String(32), default="STANDARD_AC") # STANDARD_AC, FAST_DC, CCS2
    max_charge_temp = Column(Float, default=0.0)
    abnormal_session = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

# OTA Software Update Validation Models
class SoftwareVersion(Base):
    __tablename__ = "software_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version_string = Column(String(32), unique=True, nullable=False) # e.g. "v2.4.1-stable", "v2.5.0-rc1"
    version_type = Column(String(32), default="CANDIDATE")           # REFERENCE, CANDIDATE
    target_vehicle_type = Column(String(32), default="two_wheeler")  # two_wheeler, four_wheeler, universal
    release_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    bms_profile_config = Column(JSON, nullable=False)
    is_active_reference = Column(Boolean, default=False)

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String(64), primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    reference_version_id = Column(Integer, ForeignKey("software_versions.id"), nullable=False)
    candidate_version_id = Column(Integer, ForeignKey("software_versions.id"), nullable=False)
    target_vehicle_type = Column(String(32), default="two_wheeler")
    vehicle_profile_id = Column(String(64), default="E2W-SCOOT-01")
    test_suite_version = Column(String(32), default="MOTO-SAFETY-SUITE-v1.0")
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    blocked_tests = Column(Integer, default=0)
    overall_result = Column(String(16), nullable=False)              # PASS, BLOCK
    block_reason = Column(Text, nullable=True)
    coverage_percentage = Column(Float, default=100.0)
    execution_duration_sec = Column(Float, default=0.0)
    regression_detected = Column(Boolean, default=False)
    disclaimer = Column(String(256), default="Simulation validation is a pre-deployment virtual check and does not guarantee real-vehicle physical safety.")

class TestResultItem(Base):
    __tablename__ = "test_result_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    validation_run_id = Column(String(64), ForeignKey("validation_runs.id"), nullable=False)
    scenario_id = Column(String(64), nullable=False)
    scenario_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    severity = Column(String(32), default="CRITICAL")                # CRITICAL, MAJOR, MINOR
    status = Column(String(16), nullable=False)                      # PASS, FAIL
    expected_behavior = Column(Text, nullable=False)
    actual_behavior = Column(Text, nullable=False)
    reference_behavior = Column(Text, nullable=True)
    is_regression = Column(Boolean, default=False)
    evidence_data = Column(JSON, default=dict)
    execution_time_ms = Column(Float, default=0.0)

def init_db():
    Base.metadata.create_all(bind=engine)
