from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import datetime
from ..models.database import (
    get_db, ServiceRecord, WaterExposureRecord, ComponentRecord, HealthAssessmentRecord
)
from ..schemas.service import (
    ServiceRecordCreate, ServiceRecordResponse,
    WaterExposureCreate, WaterExposureResponse,
    ComponentRecordCreate, ComponentRecordResponse,
    ServiceModeToggleRequest
)
from ..simulator.vehicle_simulator import vehicle_simulator
from ..vehicle_profiles import profile_registry
from ..ml.anomaly_model import anomaly_engine

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

router = APIRouter(prefix="/service", tags=["Vehicle Service & Component History"])

@router.get("/records", response_model=List[ServiceRecordResponse])
def get_service_records(
    vehicle_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ServiceRecord)
    if vehicle_id:
        query = query.filter(ServiceRecord.vehicle_id == vehicle_id)
    return query.order_by(ServiceRecord.timestamp.desc()).all()

@router.post("/records", response_model=ServiceRecordResponse)
def create_service_record(req: ServiceRecordCreate, db: Session = Depends(get_db)):
    vid = req.vehicle_id or vehicle_simulator.active_vehicle_id
    profile = profile_registry.get_profile(vid)

    latest_assessment = db.query(HealthAssessmentRecord).filter(
        HealthAssessmentRecord.vehicle_id == vid
    ).order_by(HealthAssessmentRecord.id.desc()).first()
    pre_score = latest_assessment.battery_health_score if latest_assessment else 92.0
    post_score = min(100.0, pre_score + 6.5)

    record = ServiceRecord(
        timestamp=utc_now(),
        vehicle_id=vid,
        vehicle_type=req.vehicle_type or profile.vehicle_type,
        service_type=req.service_type,
        description=req.description,
        technician_notes=req.technician_notes,
        odometer_km=req.odometer_km,
        pre_service_health_score=pre_score,
        post_service_health_score=post_score,
        component_replaced_id=req.component_replaced_id,
        is_service_mode_session=vehicle_simulator.get_state(vid).service_mode_active
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/water-exposure", response_model=List[WaterExposureResponse])
def get_water_exposure_records(
    vehicle_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(WaterExposureRecord)
    if vehicle_id:
        query = query.filter(WaterExposureRecord.vehicle_id == vehicle_id)
    return query.order_by(WaterExposureRecord.timestamp.desc()).all()

@router.post("/water-exposure", response_model=WaterExposureResponse)
def create_water_exposure_record(req: WaterExposureCreate, db: Session = Depends(get_db)):
    vid = req.vehicle_id or vehicle_simulator.active_vehicle_id
    profile = profile_registry.get_profile(vid)

    record = WaterExposureRecord(
        timestamp=utc_now(),
        vehicle_id=vid,
        vehicle_type=req.vehicle_type or profile.vehicle_type,
        exposure_type=req.exposure_type,
        severity_level=req.severity_level,
        duration_minutes=req.duration_minutes,
        moisture_sensor_reading=req.moisture_sensor_reading,
        post_exposure_inspected=False,
        notes=req.notes,
        disclaimer="Exposure recording does not confirm physical water ingress or damage."
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/components", response_model=List[ComponentRecordResponse])
def get_components(
    vehicle_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ComponentRecord)
    if vehicle_id:
        query = query.filter(ComponentRecord.vehicle_id == vehicle_id)
    return query.order_by(ComponentRecord.installed_at.desc()).all()

@router.post("/components", response_model=ComponentRecordResponse)
def add_component_replacement(req: ComponentRecordCreate, db: Session = Depends(get_db)):
    vid = req.vehicle_id or vehicle_simulator.active_vehicle_id
    profile = profile_registry.get_profile(vid)
    v_type = req.vehicle_type or profile.vehicle_type

    # Retire existing active component of same type on this vehicle
    existing = db.query(ComponentRecord).filter(
        ComponentRecord.vehicle_id == vid,
        ComponentRecord.component_type == req.component_type,
        ComponentRecord.is_active == True
    ).all()
    for comp in existing:
        comp.is_active = False
        comp.retired_at = utc_now()

    new_comp = ComponentRecord(
        vehicle_id=vid,
        vehicle_type=v_type,
        component_type=req.component_type,
        serial_number=req.serial_number,
        installed_at=utc_now(),
        is_active=True,
        baseline_established_at=utc_now() if req.reset_baseline else None,
        nominal_specs=req.nominal_specs,
        notes=req.notes
    )
    db.add(new_comp)

    # If baseline reset requested, retrain this vehicle's model baseline
    if req.reset_baseline:
        anomaly_engine.train_baseline(vehicle_type=v_type, sample_count=600, contamination=0.03)

    db.commit()
    db.refresh(new_comp)
    return new_comp

@router.post("/components/{comp_id}/reset-baseline")
def reset_component_baseline(comp_id: int, db: Session = Depends(get_db)):
    comp = db.query(ComponentRecord).filter(ComponentRecord.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found.")
    comp.baseline_established_at = utc_now()
    anomaly_engine.train_baseline(vehicle_type=comp.vehicle_type, sample_count=600, contamination=0.03)
    db.commit()
    return {
        "status": "SUCCESS",
        "message": f"Fresh telemetry baseline established for {comp.component_type} on {comp.vehicle_id}."
    }

@router.post("/service-mode")
def toggle_service_mode(req: ServiceModeToggleRequest):
    vehicle_simulator.set_service_mode(req.active, req.vehicle_id)
    v_state = vehicle_simulator.get_state(req.vehicle_id)
    return {
        "status": "SUCCESS",
        "vehicle_id": v_state.vehicle_id,
        "service_mode_active": v_state.service_mode_active,
        "message": f"Service Mode {'activated' if req.active else 'deactivated'} for {v_state.vehicle_id}."
    }

@router.get("/before-after-comparison")
def get_service_comparison(
    vehicle_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ServiceRecord)
    if vehicle_id:
        query = query.filter(ServiceRecord.vehicle_id == vehicle_id)
    records = query.order_by(ServiceRecord.timestamp.desc()).limit(5).all()

    comparisons = []
    for r in records:
        pre = r.pre_service_health_score or 90.0
        post = r.post_service_health_score or 98.0
        delta = round(post - pre, 1)
        comparisons.append({
            "service_id": r.id,
            "vehicle_id": r.vehicle_id,
            "vehicle_type": r.vehicle_type,
            "service_type": r.service_type,
            "timestamp": r.timestamp,
            "pre_health_score": pre,
            "post_health_score": post,
            "delta": delta,
            "improvement_pct": f"+{delta}%" if delta > 0 else f"{delta}%",
            "notes": r.description
        })
    return {
        "comparisons": comparisons,
        "summary": "Service interventions have yielded positive restorative gains across powertrain and battery subsystems.",
        "disclaimer": "Informational comparison based on algorithmic health indexes."
    }
