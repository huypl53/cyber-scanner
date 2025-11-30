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
    threat_prediction: Optional[ThreatPredictionResponse] = None
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


# IP Whitelist Schemas
class IPWhitelistCreate(BaseModel):
    ip_address: str = Field(..., description="IPv4 or IPv6 address")
    description: Optional[str] = None
    is_active: bool = True


class IPWhitelistUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None


class IPWhitelistResponse(BaseModel):
    id: int
    ip_address: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    created_by: Optional[str]

    class Config:
        from_attributes = True


# Data Source Configuration Schemas
class DataSourceConfigUpdate(BaseModel):
    is_enabled: bool
    config_params: Optional[Dict[str, Any]] = None


class DataSourceConfigResponse(BaseModel):
    id: int
    source_name: str
    is_enabled: bool
    description: Optional[str]
    config_params: Optional[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True


# ML Model Management Schemas
class ModelProfileConfig(BaseModel):
    """Configuration for model feature and class requirements"""
    expected_features: Optional[List[str]] = Field(None, description="Ordered list of feature names required by model")
    class_labels: Optional[List[str]] = Field(None, description="Ordered list of class label names (for classifiers)")
    preprocessing_notes: Optional[str] = Field(None, description="Optional preprocessing instructions/notes")


class MLModelUploadRequest(BaseModel):
    model_type: str = Field(..., description="Type of model: 'threat_detector' or 'attack_classifier'")
    description: Optional[str] = Field(None, description="Optional description of the model")


class MLModelResponse(BaseModel):
    id: int
    model_type: str
    version: str
    file_path: str
    file_format: str
    original_filename: str
    is_active: bool
    model_metadata: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    file_size_bytes: Optional[int]
    expected_features: Optional[List[str]]
    class_labels: Optional[List[str]]
    preprocessing_notes: Optional[str]
    created_at: datetime
    uploaded_by: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class MLModelListResponse(BaseModel):
    models: List[MLModelResponse]
    total_count: int


class MLModelActivateRequest(BaseModel):
    model_id: int = Field(..., description="ID of the model to activate")


class MLModelStorageStatsResponse(BaseModel):
    total_models: int
    total_size_bytes: int
    total_size_mb: float
    by_type: Dict[str, Any]
    active_models: List[Dict[str, Any]]
