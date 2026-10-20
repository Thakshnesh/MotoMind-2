from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnomalyEventResponse(BaseModel):
    id: int
    timestamp: datetime
    vehicle_id: str
    vehicle_type: str
    severity: str
    category: str
    title: str
    description: str
    anomaly_score: float
    features_involved: Dict[str, Any]
    acknowledged: bool
    resolved: bool

    model_config = ConfigDict(from_attributes=True)

class ModelStatusResponse(BaseModel):
    vehicle_id: str
    vehicle_type: str
    is_trained: bool
    training_sample_count: int
    last_trained_at: Optional[datetime] = None
    contaminated_samples_filtered: int
    contamination_rate: float
    features_used: List[str]
    model_type: str = "IsolationForest (scikit-learn)"
    operational_state: str
    disclaimer: str = "Model is trained on vehicle-specific synthetic data. Field validation is mandatory before real-world deployment."

class TrainModelRequest(BaseModel):
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID to train; defaults to active vehicle")
    vehicle_type: Optional[str] = Field(None, description="two_wheeler or four_wheeler")
    sample_count: int = Field(600, description="Number of synthetic normal points to generate for training")
    contamination: float = Field(0.02, description="Expected proportion of outliers (0.01 to 0.1)")
    exclude_known_faults: bool = Field(True, description="Enforce safeguard against contaminating baseline with fault data")
