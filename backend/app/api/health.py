from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from ..models.database import get_db
from ..simulator.vehicle_simulator import vehicle_simulator
from ..services.health_engine import health_engine
from ..services.range_estimator import range_estimator
from ..schemas.health import HealthAssessmentResponse, RangeEstimationRequest, RangeEstimationResponse

router = APIRouter(prefix="/health", tags=["EV Health Monitoring"])

@router.get("/status", response_model=HealthAssessmentResponse)
def get_health_status(vehicle_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    v_state = vehicle_simulator.get_state(vehicle_id)
    curr = v_state.latest_telemetry
    if not curr:
        curr = vehicle_simulator.step(vehicle_id)

    assessment = health_engine.assess_telemetry(curr.model_dump(), db_session=db)
    return assessment

@router.post("/assess", response_model=HealthAssessmentResponse)
def assess_telemetry_point(point: Dict[str, Any] = None, db: Session = Depends(get_db)):
    if not point:
        curr = vehicle_simulator.latest_telemetry or vehicle_simulator.step()
        point = curr.model_dump()
    assessment = health_engine.assess_telemetry(point, db_session=db)
    return assessment

@router.post("/estimate-range", response_model=RangeEstimationResponse)
def calculate_range(req: RangeEstimationRequest):
    vid = req.vehicle_id or vehicle_simulator.active_vehicle_id
    v_state = vehicle_simulator.get_state(vid)
    curr = v_state.latest_telemetry
    curr_dict = curr.model_dump() if curr else None
    return range_estimator.estimate_range(req, curr_dict)
