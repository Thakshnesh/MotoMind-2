from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..models.database import get_db, SoftwareVersion, ValidationRun, TestResultItem
from ..ota.validation_runner import ota_runner
from ..ota.test_scenarios import get_scenarios_for_vehicle
from ..schemas.ota import (
    SoftwareVersionCreate, SoftwareVersionResponse,
    ValidationRunCreateRequest, ValidationRunResponse,
    TestResultItemResponse
)

router = APIRouter(prefix="/ota", tags=["OTA Software Update Validation"])

@router.get("/versions", response_model=List[SoftwareVersionResponse])
def list_software_versions(
    target_vehicle_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SoftwareVersion)
    if target_vehicle_type:
        query = query.filter(
            (SoftwareVersion.target_vehicle_type == target_vehicle_type) |
            (SoftwareVersion.target_vehicle_type == "universal")
        )
    return query.order_by(SoftwareVersion.id.asc()).all()

@router.post("/versions", response_model=SoftwareVersionResponse)
def create_software_version(req: SoftwareVersionCreate, db: Session = Depends(get_db)):
    existing = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == req.version_string).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Version '{req.version_string}' already exists.")

    version = SoftwareVersion(
        version_string=req.version_string,
        version_type=req.version_type,
        target_vehicle_type=req.target_vehicle_type,
        release_notes=req.release_notes,
        bms_profile_config=req.bms_profile_config,
        is_active_reference=False
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

@router.get("/scenarios")
def list_test_scenarios(
    target_vehicle_type: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None)
):
    v_type = target_vehicle_type or vehicle_type or "two_wheeler"
    scenarios = get_scenarios_for_vehicle(v_type)
    return [
        {
            "scenario_id": s.scenario_id,
            "name": s.name,
            "category": s.category,
            "severity": s.severity,
            "description": s.description,
            "inputs": s.inputs,
            "expected_behavior": s.expected_behavior,
            "target_vehicle_type": v_type
        }
        for s in scenarios
    ]

@router.get("/runs", response_model=List[ValidationRunResponse])
def list_validation_runs(
    target_vehicle_type: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(ValidationRun)
    if target_vehicle_type:
        query = query.filter(ValidationRun.target_vehicle_type == target_vehicle_type)

    runs = query.order_by(ValidationRun.timestamp.desc()).limit(limit).all()
    out = []
    for r in runs:
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.id == r.reference_version_id).first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.id == r.candidate_version_id).first()
        out.append({
            "id": r.id,
            "timestamp": r.timestamp,
            "reference_version_id": r.reference_version_id,
            "candidate_version_id": r.candidate_version_id,
            "reference_version_string": ref.version_string if ref else "v2.4.1-stable",
            "candidate_version_string": cand.version_string if cand else "v2.5.0-rc1",
            "target_vehicle_type": r.target_vehicle_type or "two_wheeler",
            "vehicle_profile_id": r.vehicle_profile_id or "E2W-SCOOT-01",
            "test_suite_version": r.test_suite_version,
            "total_tests": r.total_tests,
            "passed_tests": r.passed_tests,
            "failed_tests": r.failed_tests,
            "blocked_tests": r.blocked_tests,
            "overall_result": r.overall_result,
            "block_reason": r.block_reason,
            "coverage_percentage": r.coverage_percentage,
            "execution_duration_sec": r.execution_duration_sec,
            "regression_detected": r.regression_detected,
            "disclaimer": r.disclaimer
        })
    return out

@router.get("/runs/{run_id}", response_model=ValidationRunResponse)
def get_validation_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(ValidationRun).filter(ValidationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Validation run not found.")

    items = db.query(TestResultItem).filter(TestResultItem.validation_run_id == run_id).all()
    ref = db.query(SoftwareVersion).filter(SoftwareVersion.id == run.reference_version_id).first()
    cand = db.query(SoftwareVersion).filter(SoftwareVersion.id == run.candidate_version_id).first()

    return {
        "id": run.id,
        "timestamp": run.timestamp,
        "reference_version_id": run.reference_version_id,
        "candidate_version_id": run.candidate_version_id,
        "reference_version_string": ref.version_string if ref else "v2.4.1-stable",
        "candidate_version_string": cand.version_string if cand else "v2.5.0-rc1",
        "target_vehicle_type": run.target_vehicle_type or "two_wheeler",
        "vehicle_profile_id": run.vehicle_profile_id or "E2W-SCOOT-01",
        "test_suite_version": run.test_suite_version,
        "total_tests": run.total_tests,
        "passed_tests": run.passed_tests,
        "failed_tests": run.failed_tests,
        "blocked_tests": run.blocked_tests,
        "overall_result": run.overall_result,
        "block_reason": run.block_reason,
        "coverage_percentage": run.coverage_percentage,
        "execution_duration_sec": run.execution_duration_sec,
        "regression_detected": run.regression_detected,
        "results": [
            {
                "id": it.id,
                "scenario_id": it.scenario_id,
                "scenario_name": it.scenario_name,
                "category": it.category,
                "severity": it.severity,
                "status": it.status,
                "expected_behavior": it.expected_behavior,
                "actual_behavior": it.actual_behavior,
                "reference_behavior": it.reference_behavior,
                "is_regression": it.is_regression,
                "evidence_data": it.evidence_data,
                "execution_time_ms": it.execution_time_ms
            }
            for it in items
        ],
        "disclaimer": run.disclaimer
    }

@router.post("/run", response_model=ValidationRunResponse)
def start_validation_run(req: ValidationRunCreateRequest, db: Session = Depends(get_db)):
    v_type = req.target_vehicle_type or "two_wheeler"
    vid = req.vehicle_profile_id or ("E4W-SEDAN-01" if v_type == "four_wheeler" else "E2W-SCOOT-01")

    # Lookup reference version
    if req.reference_version_id:
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.id == req.reference_version_id).first()
    else:
        ref = db.query(SoftwareVersion).filter(
            SoftwareVersion.target_vehicle_type == v_type,
            SoftwareVersion.version_type == "REFERENCE"
        ).first()

    if not ref:
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.target_vehicle_type == v_type).first() or db.query(SoftwareVersion).first()

    # Lookup candidate version
    if req.candidate_version_id:
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.id == req.candidate_version_id).first()
    else:
        cand = db.query(SoftwareVersion).filter(
            SoftwareVersion.target_vehicle_type == v_type,
            SoftwareVersion.version_type == "CANDIDATE"
        ).first()

    if not cand:
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.id != ref.id).first()

    if not ref or not cand:
        raise HTTPException(status_code=400, detail="Reference or Candidate software version missing.")

    summary = ota_runner.execute_validation_run(
        reference_profile=ref.bms_profile_config,
        candidate_profile=cand.bms_profile_config,
        reference_version_id=ref.id,
        candidate_version_id=cand.id,
        target_vehicle_type=v_type,
        vehicle_profile_id=vid,
        test_suite_version=req.test_suite_version,
        selected_scenario_ids=req.selected_scenarios,
        db_session=db
    )
    return summary

@router.post("/run-demo-regression", response_model=ValidationRunResponse)
def run_deliberate_regression_demo(
    target_vehicle_type: str = Query("two_wheeler"),
    db: Session = Depends(get_db)
):
    """
    BUILT-IN REGRESSION DEMONSTRATION:
    2W: TC-003 fails high-temp cutoff at 56.5°C -> BLOCK.
    4W: TC-4W-003 fails 52°C cutoff & TC-4W-006 fails HVIL loop trip -> BLOCK.
    """
    v_type = "four_wheeler" if "four" in target_vehicle_type.lower() else "two_wheeler"

    if v_type == "four_wheeler":
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.4.1-4w-stable").first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.5.0-4w-rc1-regressed").first()
        vid = "E4W-SEDAN-01"
    else:
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.4.1-stable").first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.5.0-rc1-regressed").first()
        vid = "E2W-SCOOT-01"

    if not ref or not cand:
        # Fallback to any reference/candidate
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.version_type == "REFERENCE").first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.version_type == "CANDIDATE").first()

    summary = ota_runner.execute_validation_run(
        reference_profile=ref.bms_profile_config,
        candidate_profile=cand.bms_profile_config,
        reference_version_id=ref.id,
        candidate_version_id=cand.id,
        target_vehicle_type=v_type,
        vehicle_profile_id=vid,
        test_suite_version="MOTO-SAFETY-SUITE-v1.0",
        db_session=db
    )
    return summary

@router.post("/run-demo-passing", response_model=ValidationRunResponse)
def run_clean_passing_demo(
    target_vehicle_type: str = Query("two_wheeler"),
    db: Session = Depends(get_db)
):
    """
    CLEAN PASSING DEMONSTRATION:
    Runs reference vs clean candidate with 100% assertions passing -> PASS.
    """
    v_type = "four_wheeler" if "four" in target_vehicle_type.lower() else "two_wheeler"

    if v_type == "four_wheeler":
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.4.1-4w-stable").first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.5.0-4w-clean").first()
        vid = "E4W-SEDAN-01"
    else:
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.4.1-stable").first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.version_string == "v2.5.0-clean").first()
        vid = "E2W-SCOOT-01"

    if not ref or not cand:
        ref = db.query(SoftwareVersion).filter(SoftwareVersion.version_type == "REFERENCE").first()
        cand = db.query(SoftwareVersion).filter(SoftwareVersion.version_type == "CANDIDATE").first()

    summary = ota_runner.execute_validation_run(
        reference_profile=ref.bms_profile_config,
        candidate_profile=cand.bms_profile_config,
        reference_version_id=ref.id,
        candidate_version_id=cand.id,
        target_vehicle_type=v_type,
        vehicle_profile_id=vid,
        test_suite_version="MOTO-SAFETY-SUITE-v1.0",
        db_session=db
    )
    return summary
