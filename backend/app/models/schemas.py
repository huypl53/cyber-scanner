from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime


# Traffic Data Schemas
class TrafficDataBase(BaseModel):
    features: Dict[str, Any]
    source: str = Field(..., description="Source of data: 'upload' or 'realtime'")
    batch_id: Optional[str] = None


class TrafficDataCreate(TrafficDataBase):
    pass


class TrafficDataResponse(TrafficDataBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Threat Prediction Schemas
class ThreatPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    traffic_data_id: int
    prediction_score: float
    is_attack: bool
    threshold: float
    model_version: str
    created_at: datetime


# Attack Prediction Schemas
class AttackPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    traffic_data_id: int
    attack_type_encoded: int
    attack_type_name: str
    confidence: Optional[float]
    model_version: str
    created_at: datetime


# Self-Healing Action Schemas
class SelfHealingActionResponse(BaseModel):
    id: int
    attack_prediction_id: int
    action_type: str
    action_description: str
    action_params: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    execution_time: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# Combined Response for complete prediction pipeline
class CompletePredictionResponse(BaseModel):
    traffic_data: TrafficDataResponse
    threat_prediction: ThreatPredictionResponse
    attack_prediction: Optional[AttackPredictionResponse] = None
    self_healing_action: Optional[SelfHealingActionResponse] = None


# CSV Upload Response
class CSVUploadResponse(BaseModel):
    message: str
    batch_id: str
    total_rows: int
    predictions: List[CompletePredictionResponse]


# Real-time Prediction Message (for WebSocket)
class RealtimePredictionMessage(BaseModel):
    timestamp: datetime
    traffic_data_id: int
    threat_prediction: ThreatPredictionResponse
    attack_prediction: Optional[AttackPredictionResponse] = None
    self_healing_action: Optional[SelfHealingActionResponse] = None


# Statistics Response
class PredictionStats(BaseModel):
    total_predictions: int
    total_attacks: int
    total_normal: int
    attack_rate: float
    attack_type_distribution: Dict[str, int]
    recent_predictions: List[CompletePredictionResponse]
