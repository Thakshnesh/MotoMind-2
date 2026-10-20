import os
import pytest
from backend.app.models.database import init_db, SessionLocal, TelemetryRecord
from backend.scripts.seed_db import seed_database
from backend.app.simulator.vehicle_simulator import vehicle_simulator

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Session-level test fixture that automatically provisions the test database schema,
    seeds reference/candidate software versions and components, and initializes simulator states.
    """
    # 1. Initialize SQLite schema
    init_db()

    # 2. Seed database with reference and candidate software versions & vehicle profiles
    seed_database()

    # 3. Step simulator to populate telemetry buffer
    p_2w = vehicle_simulator.step("E2W-SCOOT-01")
    p_4w = vehicle_simulator.step("E4W-SEDAN-01")

    # 4. Insert at least one persistent DB record for history queries
    db = SessionLocal()
    try:
        rec_2w = TelemetryRecord(
            vehicle_id="E2W-SCOOT-01",
            vehicle_type="two_wheeler",
            battery_voltage=p_2w.battery_voltage,
            battery_current=p_2w.battery_current,
            battery_temperature=p_2w.battery_temperature,
            state_of_charge=p_2w.state_of_charge,
            state_of_health=p_2w.state_of_health,
            motor_temperature=p_2w.motor_temperature,
            vehicle_speed=p_2w.vehicle_speed,
            energy_consumption=p_2w.energy_consumption,
            charging_status=p_2w.charging_status,
            ambient_temperature=p_2w.ambient_temperature,
            moisture_status=p_2w.moisture_status,
            sensor_fault_status=p_2w.sensor_fault_status,
            fault_codes=p_2w.fault_codes,
            power_kw=p_2w.power_kw,
            temp_delta=p_2w.temp_delta,
            data_source_type=p_2w.data_source_type,
            sensor_availability=p_2w.sensor_availability,
            operating_context=p_2w.operating_context,
            service_mode_active=p_2w.service_mode_active
        )
        db.add(rec_2w)
        db.commit()
    finally:
        db.close()

    yield

    # Teardown: ensure simulator is reset to default 2W vehicle
    vehicle_simulator.set_active_vehicle("E2W-SCOOT-01")
