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
    source = Column(String, nullable=False)  # 'upload', 'realtime', 'packet_capture', 'external_kafka'
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


class IPWhitelist(Base):
    """
    Stores IP addresses allowed to send data via external Kafka topic.
    Provides IP-based access control for external data providers.
    """
    __tablename__ = "ip_whitelist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)  # Supports IPv4 and IPv6
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(String(100), nullable=True)  # For future authentication


class DataSourceConfig(Base):
    """
    Stores configuration for different data sources (packet capture, external Kafka, etc.).
    Allows enabling/disabling data sources independently.
    """
    __tablename__ = "data_source_config"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(50), unique=True, nullable=False, index=True)  # e.g., 'packet_capture', 'external_kafka'
    is_enabled = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    config_params = Column(JSON, nullable=True)  # Source-specific config (e.g., interface name, topic name)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MLModel(Base):
    """
    Stores ML model versions with file paths, validation results, and activation status.
    Supports multiple model types (threat_detector, attack_classifier) with version history.
    """
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False, index=True)  # 'threat_detector', 'attack_classifier'
    version = Column(String(100), nullable=False, index=True)  # Timestamp-based: '20251128_143022'
    file_path = Column(String(500), nullable=False)  # Absolute path to model file on disk
    file_format = Column(String(20), nullable=False)  # '.pkl', '.joblib', '.h5'
    original_filename = Column(String(255), nullable=False)  # Original uploaded filename

    # Activation status - only one active model per model_type
    is_active = Column(Boolean, default=False, index=True)

    # Metadata and validation
    model_metadata = Column(JSON, nullable=True)  # Architecture info: input_shape, output_shape, etc.
    validation_results = Column(JSON, nullable=True)  # Test prediction results
    file_size_bytes = Column(Integer, nullable=True)  # File size for storage management

    # Model profile - defines expected features and class labels
    expected_features = Column(JSON, nullable=True)  # Ordered list of feature names required by model
    class_labels = Column(JSON, nullable=True)  # Ordered list of class labels (for classifiers)
    preprocessing_notes = Column(Text, nullable=True)  # Optional preprocessing instructions/notes

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String(100), nullable=True)  # For future authentication
    description = Column(Text, nullable=True)  # Optional user description
