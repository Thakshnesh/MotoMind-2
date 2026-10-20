from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..models.database import get_db, TelemetryRecord
from ..simulator.vehicle_simulator import vehicle_simulator
from ..schemas.telemetry import TelemetryResponse

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.get("/current", response_model=TelemetryResponse)
def get_current_telemetry(vehicle_id: Optional[str] = Query(None)):
    v_state = vehicle_simulator.get_state(vehicle_id)
    if v_state.latest_telemetry:
        return v_state.latest_telemetry
    point = vehicle_simulator.step(vehicle_id)
    return point

@router.get("/history", response_model=List[TelemetryResponse])
def get_telemetry_history(
    vehicle_id: Optional[str] = Query(None),
    limit: int = Query(60, ge=5, le=300),
    db: Session = Depends(get_db)
):
    v_state = vehicle_simulator.get_state(vehicle_id)
    buffer = v_state.history_buffer
    if len(buffer) >= limit:
        return buffer[-limit:]

    # Fallback to DB
    vid = vehicle_id or vehicle_simulator.active_vehicle_id
    records = db.query(TelemetryRecord).filter(TelemetryRecord.vehicle_id == vid).order_by(TelemetryRecord.id.desc()).limit(limit).all()
    if records:
        return list(reversed(records))

    return buffer

@router.get("/summary")
def get_telemetry_summary(vehicle_id: Optional[str] = Query(None)):
    v_state = vehicle_simulator.get_state(vehicle_id)
    buffer = v_state.history_buffer
    if not buffer:
        if v_state.latest_telemetry:
            buffer = [v_state.latest_telemetry.model_dump()]
        else:
            buffer = [vehicle_simulator.step(vehicle_id).model_dump()]

    voltages = [p["battery_voltage"] for p in buffer]
    currents = [p["battery_current"] for p in buffer]
    batt_temps = [p["battery_temperature"] for p in buffer]
    motor_temps = [p["motor_temperature"] for p in buffer]
    speeds = [p["vehicle_speed"] for p in buffer]
    consumptions = [p["energy_consumption"] for p in buffer]

    latest = buffer[-1]

    return {
        "vehicle_id": v_state.vehicle_id,
        "vehicle_type": v_state.vehicle_type,
        "sample_count": len(buffer),
        "latest_soc": latest.get("state_of_charge"),
        "latest_soh": latest.get("state_of_health"),
        "avg_speed_kmh": round(sum(speeds) / len(speeds), 1),
        "max_speed_kmh": round(max(speeds), 1),
        "avg_consumption_wh_km": round(sum(consumptions) / len(consumptions), 1),
        "battery_temp_min": round(min(batt_temps), 1),
        "battery_temp_max": round(max(batt_temps), 1),
        "motor_temp_max": round(max(motor_temps), 1),
        "voltage_range": {"min": min(voltages), "max": max(voltages)},
        "peak_discharge_current_a": round(max(currents), 1),
        "charging_status": latest.get("charging_status"),
        "operating_context": latest.get("operating_context"),
        "data_source_type": latest.get("data_source_type", "simulated"),
        "sensor_availability": latest.get("sensor_availability", {})
    }
