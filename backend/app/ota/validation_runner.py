import time
import uuid
import datetime
from typing import Dict, Any, List, Optional
from .virtual_bms import VirtualBMS
from .test_scenarios import get_scenarios_for_vehicle, ALL_TEST_SCENARIOS, TestScenario
from ..models.database import SoftwareVersion, ValidationRun, TestResultItem

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class OTAValidationRunner:
    """
    Automated Virtual OTA Software Update Validation Runner.
    Executes identical synthetic test suites against Reference and Candidate BMS firmware profiles
    for both Electric Two-Wheelers and Electric Four-Wheelers.
    """

    @staticmethod
    def execute_validation_run(
        reference_profile: Dict[str, Any],
        candidate_profile: Dict[str, Any],
        reference_version_id: int,
        candidate_version_id: int,
        target_vehicle_type: str = "two_wheeler",
        vehicle_profile_id: str = "E2W-SCOOT-01",
        test_suite_version: str = "MOTO-SAFETY-SUITE-v1.0",
        selected_scenario_ids: Optional[List[str]] = None,
        db_session = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        run_id = f"RUN-{utc_now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        ref_profile_copy = dict(reference_profile)
        cand_profile_copy = dict(candidate_profile)
        ref_profile_copy["vehicle_type"] = target_vehicle_type
        cand_profile_copy["vehicle_type"] = target_vehicle_type

        ref_bms = VirtualBMS(ref_profile_copy)
        cand_bms = VirtualBMS(cand_profile_copy)

        suite_scenarios = get_scenarios_for_vehicle(target_vehicle_type)
        scenarios_to_run = suite_scenarios
        if selected_scenario_ids:
            scenarios_to_run = [s for s in suite_scenarios if s.scenario_id in selected_scenario_ids]

        passed_count = 0
        failed_count = 0
        blocked_count = 0
        regression_detected = False
        block_reasons = []
        test_results = []

        for scenario in scenarios_to_run:
            t0 = time.time()

            ref_output = ref_bms.evaluate_state(scenario.inputs)
            cand_output = cand_bms.evaluate_state(scenario.inputs)

            passed, explanation, evidence = scenario.assertion_func(cand_output, ref_output)
            exec_ms = round((time.time() - t0) * 1000.0, 2)

            is_regression = evidence.get("is_regression", False)
            if is_regression:
                regression_detected = True

            status = "PASS" if passed else "FAIL"
            if not passed:
                failed_count += 1
                if scenario.severity in ["CRITICAL", "MAJOR"]:
                    blocked_count += 1
                    block_reasons.append(f"[{scenario.scenario_id}] {explanation}")
            else:
                passed_count += 1

            result_item = {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.name,
                "category": scenario.category,
                "severity": scenario.severity,
                "status": status,
                "expected_behavior": scenario.expected_behavior,
                "actual_behavior": explanation,
                "reference_behavior": f"derate_state={ref_output['derate_state']}, contactor_open={ref_output['contactor_open']}",
                "is_regression": is_regression,
                "evidence_data": {
                    **evidence,
                    "inputs": scenario.inputs,
                    "candidate_output": cand_output,
                    "reference_output": ref_output
                },
                "execution_time_ms": exec_ms
            }
            test_results.append(result_item)

        total_tests = len(scenarios_to_run)
        duration_sec = round(time.time() - start_time, 3)

        if failed_count == 0:
            overall_result = "PASS"
            final_block_reason = None
        else:
            overall_result = "BLOCK"
            final_block_reason = " ; ".join(block_reasons[:3])
            if len(block_reasons) > 3:
                final_block_reason += f" and {len(block_reasons)-3} more safety violations."

        coverage_pct = round((total_tests / len(suite_scenarios)) * 100.0, 1) if suite_scenarios else 100.0

        run_summary = {
            "id": run_id,
            "timestamp": utc_now(),
            "reference_version_id": reference_version_id,
            "candidate_version_id": candidate_version_id,
            "reference_version_string": reference_profile.get("version_string", "v2.4.1-stable"),
            "candidate_version_string": candidate_profile.get("version_string", "v2.5.0-rc1"),
            "target_vehicle_type": target_vehicle_type,
            "vehicle_profile_id": vehicle_profile_id,
            "test_suite_version": test_suite_version,
            "total_tests": total_tests,
            "passed_tests": passed_count,
            "failed_tests": failed_count,
            "blocked_tests": blocked_count,
            "overall_result": overall_result,
            "block_reason": final_block_reason,
            "coverage_percentage": coverage_pct,
            "execution_duration_sec": duration_sec,
            "regression_detected": regression_detected,
            "results": test_results,
            "disclaimer": "Simulation validation is a pre-deployment virtual check and does not guarantee real-vehicle physical safety."
        }

        if db_session:
            try:
                db_run = ValidationRun(
                    id=run_id,
                    timestamp=run_summary["timestamp"],
                    reference_version_id=reference_version_id,
                    candidate_version_id=candidate_version_id,
                    target_vehicle_type=target_vehicle_type,
                    vehicle_profile_id=vehicle_profile_id,
                    test_suite_version=test_suite_version,
                    total_tests=total_tests,
                    passed_tests=passed_count,
                    failed_tests=failed_count,
                    blocked_tests=blocked_count,
                    overall_result=overall_result,
                    block_reason=final_block_reason,
                    coverage_percentage=coverage_pct,
                    execution_duration_sec=duration_sec,
                    regression_detected=regression_detected,
                    disclaimer=run_summary["disclaimer"]
                )
                db_session.add(db_run)
                db_session.flush()

                for item in test_results:
                    db_item = TestResultItem(
                        validation_run_id=run_id,
                        scenario_id=item["scenario_id"],
                        scenario_name=item["scenario_name"],
                        category=item["category"],
                        severity=item["severity"],
                        status=item["status"],
                        expected_behavior=item["expected_behavior"],
                        actual_behavior=item["actual_behavior"],
                        reference_behavior=item["reference_behavior"],
                        is_regression=item["is_regression"],
                        evidence_data=item["evidence_data"],
                        execution_time_ms=item["execution_time_ms"]
                    )
                    db_session.add(db_item)

                db_session.commit()
            except Exception:
                db_session.rollback()

        return run_summary

ota_runner = OTAValidationRunner()
