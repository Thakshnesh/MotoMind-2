from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..models.database import get_db, AnomalyEvent
from ..ml.anomaly_model import anomaly_engine
from ..vehicle_profiles import profile_registry
from ..schemas.anomaly import ModelStatusResponse, TrainModelRequest, AnomalyEventResponse

router = APIRouter(prefix="/anomaly", tags=["Self-Learning AI Engine"])

@router.get("/model-status", response_model=ModelStatusResponse)
def get_model_status(
    vehicle_id: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None)
):
    vid = vehicle_id or profile_registry.active_vehicle_id
    profile = profile_registry.get_profile(vid)
    v_type = vehicle_type or profile.vehicle_type
    return anomaly_engine.get_status(v_type, vid)

@router.post("/train")
def train_model_baseline(req: TrainModelRequest):
    vid = req.vehicle_id or profile_registry.active_vehicle_id
    profile = profile_registry.get_profile(vid)
    v_type = req.vehicle_type or profile.vehicle_type

    result = anomaly_engine.train_baseline(
        vehicle_type=v_type,
        sample_count=req.sample_count,
        contamination=req.contamination,
        exclude_known_faults=req.exclude_known_faults
    )
    result["vehicle_id"] = vid
    return result

@router.get("/events", response_model=List[AnomalyEventResponse])
def get_anomaly_events(
    vehicle_id: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    severity: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AnomalyEvent)
    if vehicle_id:
        query = query.filter(AnomalyEvent.vehicle_id == vehicle_id)
    elif vehicle_type:
        query = query.filter(AnomalyEvent.vehicle_type == vehicle_type)

    if severity:
        query = query.filter(AnomalyEvent.severity == severity.upper())

    events = query.order_by(AnomalyEvent.id.desc()).limit(limit).all()
    return events

@router.post("/events/{event_id}/acknowledge")
def acknowledge_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(AnomalyEvent).filter(AnomalyEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Anomaly event not found.")
    event.acknowledged = True
    db.commit()
    return {"status": "SUCCESS", "message": f"Event {event_id} acknowledged."}

@router.post("/score-point")
def score_telemetry_point(point: Dict[str, Any], vehicle_type: Optional[str] = None):
    v_type = vehicle_type or point.get("vehicle_type", "two_wheeler")
    is_anomaly, score, deviations = anomaly_engine.predict_point(point, v_type)
    return {
        "vehicle_type": v_type,
        "is_anomaly": is_anomaly,
        "anomaly_score": score,
        "feature_deviations": deviations,
        "evaluation_rule": f"IsolationForest multivariate statistical boundary ({v_type})"
    }
