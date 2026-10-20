from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SoftwareVersionCreate(BaseModel):
    version_string: str = Field(..., description="e.g. v2.5.0-rc1")
    version_type: str = Field("CANDIDATE", description="REFERENCE, CANDIDATE")
    target_vehicle_type: str = Field("two_wheeler", description="two_wheeler, four_wheeler, universal")
    release_notes: Optional[str] = None
    bms_profile_config: Dict[str, Any] = Field(..., description="BMS protection limits and safety assertion logic")

class SoftwareVersionResponse(BaseModel):
    id: int
    version_string: str
    version_type: str
    target_vehicle_type: str
    release_notes: Optional[str] = None
    created_at: datetime
    bms_profile_config: Dict[str, Any]
    is_active_reference: bool

    model_config = ConfigDict(from_attributes=True)

class TestResultItemResponse(BaseModel):
    id: Optional[int] = None
    scenario_id: str
    scenario_name: str
    category: str
    severity: str
    status: str # PASS, FAIL
    expected_behavior: str
    actual_behavior: str
    reference_behavior: Optional[str] = None
    is_regression: bool
    evidence_data: Dict[str, Any]
    execution_time_ms: float

    model_config = ConfigDict(from_attributes=True)

class ValidationRunCreateRequest(BaseModel):
    reference_version_id: Optional[int] = None
    candidate_version_id: Optional[int] = None
    target_vehicle_type: str = Field("two_wheeler", description="two_wheeler or four_wheeler")
    vehicle_profile_id: Optional[str] = None
    test_suite_version: str = "MOTO-SAFETY-SUITE-v1.0"
    selected_scenarios: Optional[List[str]] = None

class ValidationRunResponse(BaseModel):
    id: str
    timestamp: datetime
    reference_version_id: int
    candidate_version_id: int
    reference_version_string: Optional[str] = None
    candidate_version_string: Optional[str] = None
    target_vehicle_type: str
    vehicle_profile_id: str
    test_suite_version: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    blocked_tests: int
    overall_result: str # PASS, BLOCK
    block_reason: Optional[str] = None
    coverage_percentage: float
    execution_duration_sec: float
    regression_detected: bool
    results: Optional[List[TestResultItemResponse]] = None
    disclaimer: str

    model_config = ConfigDict(from_attributes=True)
