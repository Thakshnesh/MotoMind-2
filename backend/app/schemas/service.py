from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ComponentRecordCreate(BaseModel):
    vehicle_id: str = Field("E2W-SCOOT-01", description="Vehicle ID this component belongs to")
    vehicle_type: str = Field("two_wheeler", description="two_wheeler or four_wheeler")
    component_type: str = Field(..., description="BATTERY_PACK, TRACTION_MOTOR, BMS_MODULE, MOTOR_CONTROLLER, COOLANT_PUMP")
    serial_number: str
    nominal_specs: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    reset_baseline: bool = Field(True, description="Establish a fresh learning baseline for this new component")

class ComponentRecordResponse(BaseModel):
    id: int
    vehicle_id: str
    vehicle_type: str
    component_type: str
    serial_number: str
    installed_at: datetime
    retired_at: Optional[datetime] = None
    is_active: bool
    baseline_established_at: Optional[datetime] = None
    nominal_specs: Dict[str, Any]
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ServiceRecordCreate(BaseModel):
    vehicle_id: str = Field("E2W-SCOOT-01")
    vehicle_type: str = Field("two_wheeler")
    service_type: str = Field(..., description="ROUTINE_MAINTENANCE, WATER_WASH, REPAIR, INSPECTION, COMPONENT_REPLACEMENT, COOLANT_FLUSH")
    description: str
    technician_notes: Optional[str] = None
    odometer_km: float = 0.0
    component_replaced_id: Optional[int] = None

class ServiceRecordResponse(BaseModel):
    id: int
    timestamp: datetime
    vehicle_id: str
    vehicle_type: str
    service_type: str
    description: str
    technician_notes: Optional[str] = None
    odometer_km: float
    pre_service_health_score: Optional[float] = None
    post_service_health_score: Optional[float] = None
    component_replaced_id: Optional[int] = None
    is_service_mode_session: bool

    model_config = ConfigDict(from_attributes=True)

class WaterExposureCreate(BaseModel):
    vehicle_id: str = Field("E2W-SCOOT-01")
    vehicle_type: str = Field("two_wheeler")
    exposure_type: str = Field(..., description="PRESSURE_WASH, RAIN_RIDE, FLOOD_WATER, WASHING, UNDERBODY_SPRAY")
    severity_level: str = Field("MODERATE", description="LOW, MODERATE, HIGH")
    duration_minutes: int = Field(15)
    moisture_sensor_reading: str = Field("damp", description="dry, damp, wet")
    notes: Optional[str] = None

class WaterExposureResponse(BaseModel):
    id: int
    timestamp: datetime
    vehicle_id: str
    vehicle_type: str
    exposure_type: str
    severity_level: str
    duration_minutes: int
    moisture_sensor_reading: str
    post_exposure_inspected: bool
    notes: Optional[str] = None
    disclaimer: str

    model_config = ConfigDict(from_attributes=True)

class ServiceModeToggleRequest(BaseModel):
    vehicle_id: Optional[str] = None
    active: bool
    reason: Optional[str] = "Technician inspection / maintenance session"
