from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class HealthAssessmentResponse(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    vehicle_id: str = "E2W-SCOOT-01"
    vehicle_type: str = "two_wheeler"
    overall_status: str = Field(..., description="Normal, Warning, High Anomaly, Insufficient Data")
    battery_health_score: float = Field(..., description="Battery sub-system score 0-100")
    motor_health_score: float = Field(..., description="Motor sub-system score 0-100")
    electrical_health_score: float = Field(..., description="Power & wiring sub-system score 0-100")
    thermal_management_score: Optional[float] = Field(None, description="Coolant / thermal loop score for liquid-cooled 4W")
    anomaly_detected: bool = Field(False)
    anomaly_score: float = Field(0.0)
    reasons: List[str] = Field(default_factory=list)
    triggered_values: Dict[str, Any] = Field(default_factory=dict)
    rule_violations: List[str] = Field(default_factory=list)
    disclaimer: str = "Informational estimate only. Not a confirmed mechanical diagnosis."

    model_config = ConfigDict(from_attributes=True)

class RangeEstimationRequest(BaseModel):
    vehicle_id: Optional[str] = Field(None, description="Target vehicle ID; defaults to active vehicle")
    battery_soc: Optional[float] = Field(None, description="Current SOC % (if None, use current simulated value)")
    battery_capacity_kwh: Optional[float] = Field(None, description="Configurable usable capacity in kWh")
    average_consumption_wh_km: Optional[float] = Field(None, description="Observed Wh/km")
    route_distance_km: Optional[float] = Field(None, description="Planned trip distance in km")
    elevation_gain_m: Optional[float] = Field(0.0, description="Estimated total elevation gain in meters")
    traffic_factor: Optional[float] = Field(1.0, description="1.0 = normal, 1.25 = heavy stop-and-go")

class RangeEstimationResponse(BaseModel):
    vehicle_id: str
    vehicle_type: str
    estimated_range_km: float
    confidence_interval_min_km: float
    confidence_interval_max_km: float
    usable_energy_remaining_wh: float
    assumed_consumption_wh_km: float
    capacity_used_kwh: float
    soc_percent: float
    assumptions_explanation: List[str]
    disclaimer: str = "Simulated estimation. No external live map or traffic API is connected."
