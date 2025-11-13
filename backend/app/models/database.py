from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TrafficData(Base):
    """
    Stores raw network traffic data uploaded or streamed in real-time.
    Supports both 10-feature (threat detection) and 42-feature (attack classification) datasets.
    """
    __tablename__ = "traffic_data"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Store features as JSON for flexibility (handles both 10 and 42 feature sets)
    features = Column(JSON, nullable=False)

    # Source of data
    source = Column(String, nullable=False)  # 'upload' or 'realtime'
    batch_id = Column(String, nullable=True, index=True)  # For grouping uploaded CSV rows

    # Relationships
    threat_prediction = relationship("ThreatPrediction", back_populates="traffic_data", uselist=False)
    attack_prediction = relationship("AttackPrediction", back_populates="traffic_data", uselist=False)


class ThreatPrediction(Base):
    """
    Stores binary threat detection predictions (Normal vs Attack).
    Uses ensemble model with 10 features.
    """
    __tablename__ = "threat_predictions"

    id = Column(Integer, primary_key=True, index=True)
    traffic_data_id = Column(Integer, ForeignKey("traffic_data.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Prediction results
    prediction_score = Column(Float, nullable=False)  # Probability score (0-1)
    is_attack = Column(Boolean, nullable=False)  # True if attack detected (score > 0.5)
    threshold = Column(Float, default=0.5)

    # Model info
    model_version = Column(String, default="ensemble_v1")

    # Relationships
    traffic_data = relationship("TrafficData", back_populates="threat_prediction")


class AttackPrediction(Base):
    """
    Stores multi-class attack type predictions (14 classes).
    Uses decision tree model with 42 features.
    Only created when threat is detected.
    """
    __tablename__ = "attack_predictions"

    id = Column(Integer, primary_key=True, index=True)
    traffic_data_id = Column(Integer, ForeignKey("traffic_data.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Prediction results
    attack_type_encoded = Column(Integer, nullable=False)  # 0-13
    attack_type_name = Column(String, nullable=False)  # e.g., "DDoS", "PortScan"
    confidence = Column(Float, nullable=True)  # Model confidence if available

    # Model info
    model_version = Column(String, default="decision_tree_v1")

    # Relationships
    traffic_data = relationship("TrafficData", back_populates="attack_prediction")
    self_healing_action = relationship("SelfHealingAction", back_populates="attack_prediction", uselist=False)


class SelfHealingAction(Base):
    """
    Logs self-healing actions taken in response to detected attacks.
    """
    __tablename__ = "self_healing_actions"

    id = Column(Integer, primary_key=True, index=True)
    attack_prediction_id = Column(Integer, ForeignKey("attack_predictions.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Action details
    action_type = Column(String, nullable=False)  # 'restart_service', 'block_ip', 'alert_admin', 'log_only'
    action_description = Column(Text, nullable=False)  # Human-readable description
    action_params = Column(JSON, nullable=True)  # Parameters like {"service": "apache2"} or {"ip": "192.168.1.1"}

    # Execution status
    status = Column(String, default="logged")  # 'logged', 'simulated', 'executed', 'failed'
    execution_time = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    attack_prediction = relationship("AttackPrediction", back_populates="self_healing_action")
