import io
import csv
import json
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from ..models.database import get_db, TelemetryRecord, ValidationRun, TestResultItem
from ..simulator.vehicle_simulator import vehicle_simulator

router = APIRouter(prefix="/export", tags=["Export & Reporting"])

@router.get("/telemetry-csv")
def export_telemetry_csv(
    vehicle_id: Optional[str] = Query(None),
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """Exports recent vehicle telemetry log as downloadable CSV file."""
    vid = vehicle_id or vehicle_simulator.active_vehicle_id
    v_state = vehicle_simulator.get_state(vid)
    buffer = v_state.history_buffer

    if not buffer or len(buffer) < 5:
        db_records = db.query(TelemetryRecord).filter(
            TelemetryRecord.vehicle_id == vid
        ).order_by(TelemetryRecord.id.desc()).limit(limit).all()

        data_to_export = [
            {
                "timestamp": r.timestamp.isoformat(),
                "vehicle_id": r.vehicle_id,
                "vehicle_type": r.vehicle_type,
                "battery_voltage": r.battery_voltage,
                "battery_current": r.battery_current,
                "battery_temperature": r.battery_temperature,
                "state_of_charge": r.state_of_charge,
                "state_of_health": r.state_of_health,
                "motor_temperature": r.motor_temperature,
                "secondary_motor_temperature": r.secondary_motor_temperature,
                "coolant_temperature": r.coolant_temperature,
                "cabin_temperature": r.cabin_temperature,
                "vehicle_speed": r.vehicle_speed,
                "energy_consumption": r.energy_consumption,
                "charging_status": r.charging_status,
                "ambient_temperature": r.ambient_temperature,
                "moisture_status": r.moisture_status,
                "power_kw": r.power_kw,
                "temp_delta": r.temp_delta,
                "operating_context": r.operating_context
            }
            for r in db_records
        ]
    else:
        data_to_export = buffer[-limit:]

    if not data_to_export:
        raise HTTPException(status_code=404, detail="No telemetry points available for export.")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(data_to_export[0].keys()))
    writer.writeheader()
    for row in data_to_export:
        writer.writerow(row)
    output.seek(0)

    filename = f"motomind_telemetry_{vid}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/ota-report/{run_id}")
def export_ota_report(run_id: str, db: Session = Depends(get_db)):
    """Exports complete OTA Validation Run Report as downloadable JSON."""
    run = db.query(ValidationRun).filter(ValidationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Validation run not found.")

    items = db.query(TestResultItem).filter(TestResultItem.validation_run_id == run_id).all()

    report = {
        "report_title": "MotoMind OTA Software Update Validation Report",
        "run_id": run.id,
        "generated_at": run.timestamp.isoformat(),
        "target_vehicle_type": run.target_vehicle_type or "two_wheeler",
        "vehicle_profile_id": run.vehicle_profile_id or "E2W-SCOOT-01",
        "test_suite_version": run.test_suite_version,
        "overall_result": run.overall_result,
        "decision_summary": run.block_reason or "All mandatory safety assertions passed. Software is cleared for virtual staging.",
        "metrics": {
            "total_scenarios_executed": run.total_tests,
            "passed": run.passed_tests,
            "failed": run.failed_tests,
            "blocked": run.blocked_tests,
            "coverage_percentage": f"{run.coverage_percentage}%",
            "execution_duration_sec": run.execution_duration_sec,
            "regression_detected": run.regression_detected
        },
        "scenarios_breakdown": [
            {
                "id": it.scenario_id,
                "name": it.scenario_name,
                "category": it.category,
                "severity": it.severity,
                "status": it.status,
                "expected": it.expected_behavior,
                "actual": it.actual_behavior,
                "reference": it.reference_behavior,
                "regression": it.is_regression,
                "evidence": it.evidence_data
            }
            for it in items
        ],
        "disclaimer": run.disclaimer
    }

    report_json = json.dumps(report, indent=2)
    return Response(
        content=report_json,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=OTA_Validation_Report_{run.id}.json"}
    )
