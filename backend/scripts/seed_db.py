import os
import sys
import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.models.database import (
    init_db, SessionLocal, SoftwareVersion, ComponentRecord, ServiceRecord, WaterExposureRecord, AnomalyEvent
)

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

def seed_database():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Software Versions
        if db.query(SoftwareVersion).count() == 0:
            print("Seeding software versions for Two-Wheelers and Four-Wheelers...")
            # 2W Versions
            v2w_ref = SoftwareVersion(
                version_string="v2.4.1-stable",
                version_type="REFERENCE",
                target_vehicle_type="two_wheeler",
                release_notes="Certified factory baseline firmware for Electric Two-Wheeler. 55.0°C thermal cutoff & drive interlock.",
                is_active_reference=True,
                bms_profile_config={
                    "version_string": "v2.4.1-stable",
                    "vehicle_type": "two_wheeler",
                    "max_cell_temp_cutoff": 55.0,
                    "max_cell_temp_warn": 48.0,
                    "min_charge_temp_cutoff": 0.0,
                    "over_voltage_cutoff": 58.8,
                    "under_voltage_cutoff": 42.0,
                    "max_discharge_current": 65.0,
                    "drive_interlock_on_charge": True,
                    "can_timeout_threshold_ms": 250.0,
                    "deliberate_regression_bypass_overtemp": False
                }
            )
            v2w_reg = SoftwareVersion(
                version_string="v2.5.0-rc1-regressed",
                version_type="CANDIDATE",
                target_vehicle_type="two_wheeler",
                release_notes="E2W Candidate with intentionally introduced regression: thermal cutoff bypassed in fast-loop control.",
                is_active_reference=False,
                bms_profile_config={
                    "version_string": "v2.5.0-rc1-regressed",
                    "vehicle_type": "two_wheeler",
                    "max_cell_temp_cutoff": 55.0,
                    "max_cell_temp_warn": 48.0,
                    "min_charge_temp_cutoff": 0.0,
                    "over_voltage_cutoff": 58.8,
                    "under_voltage_cutoff": 42.0,
                    "max_discharge_current": 65.0,
                    "drive_interlock_on_charge": True,
                    "can_timeout_threshold_ms": 250.0,
                    "deliberate_regression_bypass_overtemp": True # REGRESSION
                }
            )
            v2w_clean = SoftwareVersion(
                version_string="v2.5.0-clean",
                version_type="CANDIDATE",
                target_vehicle_type="two_wheeler",
                release_notes="E2W Candidate update with optimized regen efficiency and fully verified safety assertions.",
                is_active_reference=False,
                bms_profile_config={
                    "version_string": "v2.5.0-clean",
                    "vehicle_type": "two_wheeler",
                    "max_cell_temp_cutoff": 55.0,
                    "max_cell_temp_warn": 48.0,
                    "min_charge_temp_cutoff": 0.0,
                    "over_voltage_cutoff": 58.8,
                    "under_voltage_cutoff": 42.0,
                    "max_discharge_current": 65.0,
                    "drive_interlock_on_charge": True,
                    "can_timeout_threshold_ms": 250.0,
                    "deliberate_regression_bypass_overtemp": False
                }
            )

            # 4W Versions
            v4w_ref = SoftwareVersion(
                version_string="v2.4.1-4w-stable",
                version_type="REFERENCE",
                target_vehicle_type="four_wheeler",
                release_notes="Certified factory baseline for 400V Electric Four-Wheeler. 52.0°C cutoff, HVIL loop, liquid loop control.",
                is_active_reference=False,
                bms_profile_config={
                    "version_string": "v2.4.1-4w-stable",
                    "vehicle_type": "four_wheeler",
                    "max_cell_temp_cutoff": 52.0,
                    "max_cell_temp_warn": 45.0,
                    "min_charge_temp_cutoff": 0.0,
                    "over_voltage_cutoff": 450.0,
                    "under_voltage_cutoff": 310.0,
                    "max_discharge_current": 320.0,
                    "max_coolant_temp_derate": 68.0,
                    "hvil_enabled": True,
                    "drive_interlock_on_charge": True,
                    "can_timeout_threshold_ms": 250.0,
                    "deliberate_regression_bypass_overtemp": False,
                    "deliberate_regression_bypass_hvil": False
                }
            )
            v4w_reg = SoftwareVersion(
                version_string="v2.5.0-4w-rc1-regressed",
                version_type="CANDIDATE",
                target_vehicle_type="four_wheeler",
                release_notes="E4W Candidate with regression: HVIL and 400V thermal cutoff bypass regression.",
                is_active_reference=False,
                bms_profile_config={
                    "version_string": "v2.5.0-4w-rc1-regressed",
                    "vehicle_type": "four_wheeler",
                    "max_cell_temp_cutoff": 52.0,
                    "max_cell_temp_warn": 45.0,
                    "min_charge_temp_cutoff": 0.0,
                    "over_voltage_cutoff": 450.0,
                    "under_voltage_cutoff": 310.0,
                    "max_discharge_current": 320.0,
                    "max_coolant_temp_derate": 68.0,
                    "hvil_enabled": True,
                    "drive_interlock_on_charge": True,
                    "can_timeout_threshold_ms": 250.0,
                    "deliberate_regression_bypass_overtemp": True, # REGRESSION
                    "deliberate_regression_bypass_hvil": True      # REGRESSION
                }
            )
            v4w_clean = SoftwareVersion(
                version_string="v2.5.0-4w-clean",
                version_type="CANDIDATE",
                target_vehicle_type="four_wheeler",
                release_notes="E4W Candidate update with enhanced CCS2 thermal throttling and certified HV safety envelope.",
                is_active_reference=False,
                bms_profile_config={
                    "version_string": "v2.5.0-4w-clean",
                    "vehicle_type": "four_wheeler",
                    "max_cell_temp_cutoff": 52.0,
                    "max_cell_temp_warn": 45.0,
                    "min_charge_temp_cutoff": 0.0,
                    "over_voltage_cutoff": 450.0,
                    "under_voltage_cutoff": 310.0,
                    "max_discharge_current": 320.0,
                    "max_coolant_temp_derate": 68.0,
                    "hvil_enabled": True,
                    "drive_interlock_on_charge": True,
                    "can_timeout_threshold_ms": 250.0,
                    "deliberate_regression_bypass_overtemp": False,
                    "deliberate_regression_bypass_hvil": False
                }
            )

            db.add_all([v2w_ref, v2w_reg, v2w_clean, v4w_ref, v4w_reg, v4w_clean])
            db.commit()

        # 2. Seed Component Records
        if db.query(ComponentRecord).count() == 0:
            print("Seeding component records for 2W and 4W...")
            # 2W components
            comp_2w_batt = ComponentRecord(
                vehicle_id="E2W-SCOOT-01",
                vehicle_type="two_wheeler",
                component_type="BATTERY_PACK",
                serial_number="BP-52V-2026-992",
                installed_at=utc_now() - datetime.timedelta(days=120),
                is_active=True,
                baseline_established_at=utc_now() - datetime.timedelta(days=119),
                nominal_specs={"capacity_kwh": 3.2, "voltage": 52.0, "chemistry": "NMC-14S"},
                notes="Primary factory 52V traction battery pack."
            )
            comp_2w_motor = ComponentRecord(
                vehicle_id="E2W-SCOOT-01",
                vehicle_type="two_wheeler",
                component_type="TRACTION_MOTOR",
                serial_number="TM-4KW-881",
                installed_at=utc_now() - datetime.timedelta(days=120),
                is_active=True,
                baseline_established_at=utc_now() - datetime.timedelta(days=119),
                nominal_specs={"rated_power_kw": 4.0, "cooling": "air_cooled"},
                notes="Mid-drive BLDC motor."
            )

            # 4W components
            comp_4w_batt = ComponentRecord(
                vehicle_id="E4W-SEDAN-01",
                vehicle_type="four_wheeler",
                component_type="BATTERY_PACK",
                serial_number="BP-400V-64KWH-014",
                installed_at=utc_now() - datetime.timedelta(days=90),
                is_active=True,
                baseline_established_at=utc_now() - datetime.timedelta(days=89),
                nominal_specs={"capacity_kwh": 64.0, "voltage": 400.0, "chemistry": "LFP/NMC 96S"},
                notes="Primary 400V high-voltage structural pack."
            )
            comp_4w_front_motor = ComponentRecord(
                vehicle_id="E4W-SEDAN-01",
                vehicle_type="four_wheeler",
                component_type="TRACTION_MOTOR",
                serial_number="TM-FRONT-100KW-552",
                installed_at=utc_now() - datetime.timedelta(days=90),
                is_active=True,
                baseline_established_at=utc_now() - datetime.timedelta(days=89),
                nominal_specs={"rated_power_kw": 100.0, "cooling": "liquid_glycol"},
                notes="Front permanent magnet synchronous drive unit."
            )
            comp_4w_pump = ComponentRecord(
                vehicle_id="E4W-SEDAN-01",
                vehicle_type="four_wheeler",
                component_type="COOLANT_PUMP",
                serial_number="PUMP-GLYCOL-V3-102",
                installed_at=utc_now() - datetime.timedelta(days=90),
                is_active=True,
                baseline_established_at=utc_now() - datetime.timedelta(days=89),
                nominal_specs={"flow_rate_lpm": 25.0, "voltage": 12.0},
                notes="Battery & drive unit dual-circuit coolant circulation pump."
            )

            db.add_all([comp_2w_batt, comp_2w_motor, comp_4w_batt, comp_4w_front_motor, comp_4w_pump])
            db.commit()

        # 3. Seed Service Records
        if db.query(ServiceRecord).count() == 0:
            print("Seeding initial service records...")
            s1 = ServiceRecord(
                vehicle_id="E2W-SCOOT-01",
                vehicle_type="two_wheeler",
                timestamp=utc_now() - datetime.timedelta(days=35),
                service_type="ROUTINE_MAINTENANCE",
                description="5,000 km periodic inspection: brake pads, belt tension, and firmware check.",
                technician_notes="All wiring harnesses secure.",
                odometer_km=5120.0,
                pre_service_health_score=94.5,
                post_service_health_score=99.0,
                is_service_mode_session=True
            )
            s2 = ServiceRecord(
                vehicle_id="E4W-SEDAN-01",
                vehicle_type="four_wheeler",
                timestamp=utc_now() - datetime.timedelta(days=20),
                service_type="COOLANT_FLUSH",
                description="10,000 km thermal system check: glycol loop flush, pressure test, and isolation audit.",
                technician_notes="Coolant loop pressure held at 1.5 bar. Isolation resistance tested at 550 kOhm.",
                odometer_km=10450.0,
                pre_service_health_score=92.0,
                post_service_health_score=98.5,
                is_service_mode_session=True
            )
            db.add_all([s1, s2])
            db.commit()

        # 4. Seed Water Exposure Records
        if db.query(WaterExposureRecord).count() == 0:
            print("Seeding water exposure records...")
            w1 = WaterExposureRecord(
                vehicle_id="E2W-SCOOT-01",
                vehicle_type="two_wheeler",
                timestamp=utc_now() - datetime.timedelta(days=14),
                exposure_type="RAIN_RIDE",
                severity_level="MODERATE",
                duration_minutes=25,
                moisture_sensor_reading="damp",
                post_exposure_inspected=True,
                notes="Commute during heavy monsoon rain. Battery enclosure seal verified intact."
            )
            w2 = WaterExposureRecord(
                vehicle_id="E4W-SEDAN-01",
                vehicle_type="four_wheeler",
                timestamp=utc_now() - datetime.timedelta(days=7),
                exposure_type="UNDERBODY_SPRAY",
                severity_level="LOW",
                duration_minutes=10,
                moisture_sensor_reading="unavailable",
                post_exposure_inspected=True,
                notes="Automated car wash undercarriage spray. HV isolation remained above 500 kOhm."
            )
            db.add_all([w1, w2])
            db.commit()

        print("Database seeded successfully with 2W and 4W profiles!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
