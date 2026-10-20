from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from ..simulator.vehicle_simulator import vehicle_simulator
from ..vehicle_profiles import profile_registry
from ..schemas.telemetry import SimulatorStatus, FaultInjectionRequest, SimulationProfileRequest, VehicleSwitchRequest

router = APIRouter(prefix="/simulator", tags=["Simulator"])

@router.get("/status", response_model=SimulatorStatus)
def get_simulator_status(vehicle_id: Optional[str] = Query(None)):
    return vehicle_simulator.get_status(vehicle_id)

@router.get("/vehicles")
def list_vehicle_profiles():
    return profile_registry.list_profiles()

@router.post("/switch-vehicle")
def switch_active_vehicle(req: VehicleSwitchRequest):
    try:
        profile = vehicle_simulator.set_active_vehicle(req.vehicle_id)
        return {
            "status": "SUCCESS",
            "active_vehicle_id": req.vehicle_id,
            "vehicle_type": profile.vehicle_type,
            "display_name": profile.display_name,
            "message": f"Active vehicle switched to {profile.display_name}."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/start")
def start_simulation(vehicle_id: Optional[str] = Query(None)):
    vehicle_simulator.start(vehicle_id)
    return {"status": "SUCCESS", "message": "Simulation started."}

@router.post("/pause")
def pause_simulation(vehicle_id: Optional[str] = Query(None)):
    vehicle_simulator.pause(vehicle_id)
    return {"status": "SUCCESS", "message": "Simulation paused."}

@router.post("/reset")
def reset_simulation(vehicle_id: Optional[str] = Query(None)):
    vehicle_simulator.reset(vehicle_id)
    return {"status": "SUCCESS", "message": "Simulation reset to default initial state."}

@router.post("/inject-fault")
def inject_fault(req: FaultInjectionRequest):
    valid_faults = [
        "over_temp_battery", "motor_overheat", "sudden_voltage_sag",
        "high_discharge_current", "moisture_detected", "sensor_drift",
        "sensor_disconnect", "cell_imbalance", "coolant_pump_failure",
        "secondary_motor_overheat", "insulation_loss"
    ]
    if req.fault_type not in valid_faults:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid fault type '{req.fault_type}'. Allowed types: {', '.join(valid_faults)}"
        )
    vehicle_simulator.inject_fault(req.fault_type, req.duration_seconds, req.vehicle_id)
    return {
        "status": "SUCCESS",
        "message": f"Injected synthetic fault '{req.fault_type}' for {req.duration_seconds} seconds.",
        "active_fault": req.fault_type
    }

@router.post("/clear-fault")
def clear_fault(vehicle_id: Optional[str] = Query(None)):
    vehicle_simulator.clear_fault(vehicle_id)
    return {"status": "SUCCESS", "message": "Cleared all active injected faults."}

@router.post("/profile")
def set_profile(req: SimulationProfileRequest):
    valid_profiles = ["city_commute", "aggressive_sport", "eco_cruising", "idle_charging", "dc_fast_charging"]
    if req.profile_name not in valid_profiles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid profile name. Allowed: {', '.join(valid_profiles)}"
        )
    vehicle_simulator.set_profile(req.profile_name, req.vehicle_id)
    return {
        "status": "SUCCESS",
        "message": f"Operating profile updated to '{req.profile_name}'."
    }

@router.post("/step")
def step_simulation(vehicle_id: Optional[str] = Query(None)):
    point = vehicle_simulator.step(vehicle_id)
    return point.model_dump()
