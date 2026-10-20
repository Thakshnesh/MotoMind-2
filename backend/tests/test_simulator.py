import pytest
from backend.app.simulator.vehicle_simulator import VehicleSimulator

def test_simulator_nominal_step():
    sim = VehicleSimulator()
    sim.set_active_vehicle("E2W-SCOOT-01")
    point = sim.step()
    
    assert point.battery_voltage >= 40.0 and point.battery_voltage <= 62.0
    assert point.state_of_charge >= 0.0 and point.state_of_charge <= 100.0
    assert point.battery_temperature >= 15.0 and point.battery_temperature <= 60.0
    assert point.vehicle_speed >= 0.0
    assert point.data_source_type == "simulated"
    assert point.power_kw is not None

def test_simulator_pause_and_reset():
    sim = VehicleSimulator()
    sim.pause()
    assert sim.is_running is False
    
    sim.start()
    assert sim.is_running is True
    
    sim.step()
    sim.step()
    sim.reset()
    assert sim.tick_count == 0
    assert sim.soc == 85.0
    assert sim.speed == 0.0

def test_fault_injection():
    sim = VehicleSimulator()
    sim.inject_fault("over_temp_battery", duration_seconds=10)
    assert sim.active_injected_fault == "over_temp_battery"
    
    # Run several steps to see temperature elevate
    for _ in range(5):
        sim.step()
    
    assert sim.battery_temp > 33.0
    
    sim.clear_fault()
    assert sim.active_injected_fault is None

def test_profiles():
    sim = VehicleSimulator()
    sim.set_profile("idle_charging")
    assert sim.current_profile == "idle_charging"
    
    point = sim.step()
    assert point.charging_status == "charging"
    assert point.battery_current < 0.0 # Charging current is negative
