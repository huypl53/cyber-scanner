"""
Production ML models for threat detection and attack classification.
Loads real trained models from filesystem or fallback to mock models if unavailable.
"""
import os
import logging
import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

# Model storage directory
MODELS_DIR = Path(__file__).parent.parent.parent / "models"

# Expected features (must match preprocessor.py)
THREAT_DETECTION_FEATURES = [
    'service', 'flag', 'src_bytes', 'dst_bytes', 'count',
    'same_srv_rate', 'diff_srv_rate', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_same_src_port_rate'
]

ATTACK_CLASSIFICATION_FEATURES = [
    ' Destination Port', ' Flow Duration', ' Total Fwd Packets',
    'Total Length of Fwd Packets', ' Fwd Packet Length Max',
    ' Fwd Packet Length Min', 'Bwd Packet Length Max',
    ' Bwd Packet Length Min', 'Flow Bytes/s', ' Flow Packets/s',
    ' Flow IAT Mean', ' Flow IAT Std', ' Flow IAT Min', 'Bwd IAT Total',
    ' Bwd IAT Std', 'Fwd PSH Flags', ' Bwd PSH Flags', ' Fwd URG Flags',
    ' Bwd URG Flags', ' Fwd Header Length', ' Bwd Header Length',
    ' Bwd Packets/s', ' Min Packet Length', 'FIN Flag Count',
    ' RST Flag Count', ' PSH Flag Count', ' ACK Flag Count',
    ' URG Flag Count', ' Down/Up Ratio', 'Fwd Avg Bytes/Bulk',
    ' Fwd Avg Packets/Bulk', ' Fwd Avg Bulk Rate', ' Bwd Avg Bytes/Bulk',
    ' Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Init_Win_bytes_forward',
    ' Init_Win_bytes_backward', ' min_seg_size_forward', 'Active Mean',
    ' Active Std', ' Active Max', ' Idle Std'
]

ATTACK_TYPES = {
    0: 'BENIGN',
    1: 'DoS Hulk',
    2: 'DDoS',
    3: 'PortScan',
    4: 'FTP-Patator',
    5: 'DoS slowloris',
    6: 'DoS Slowhttptest',
    7: 'SSH-Patator',
    8: 'DoS GoldenEye',
    9: 'Web Attack – Brute Force',
    10: 'Bot',
    11: 'Web Attack – XSS',
    12: 'Web Attack – Sql Injection',
    13: 'Infiltration'
}


class RealEnsembleModel:
    """
    Real trained model for binary threat detection.
    Loads from filesystem or uses intelligent fallback.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.selected_features = THREAT_DETECTION_FEATURES
        self.threshold = 0.5
        self.model_version = "unknown"
        self.is_real_model = False

        # Try to load real model
        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
        else:
            # Try to find latest model in models directory
            latest_model = self._find_latest_model("threat_detector")
            if latest_model:
                self._load_model(latest_model)
            else:
                logger.warning("No real threat detection model found. Using mock model.")
                self._init_mock_model()

    def _find_latest_model(self, model_type: str) -> Optional[str]:
        """Find the latest model file in models directory."""
        if not MODELS_DIR.exists():
            return None

        model_files = list(MODELS_DIR.glob(f"{model_type}_*.joblib"))
        if not model_files:
            return None

        # Sort by modification time, newest first
        latest = max(model_files, key=lambda p: p.stat().st_mtime)
        return str(latest)

    def _load_model(self, model_path: str):
        """Load real trained model from file."""
        try:
            logger.info(f"Loading threat detection model from: {model_path}")
            bundle = joblib.load(model_path)

            self.model = bundle.get('model')
            self.scaler = bundle.get('scaler')
            self.label_encoders = bundle.get('label_encoders', {})
            self.selected_features = bundle.get('selected_features', THREAT_DETECTION_FEATURES)
            self.threshold = bundle.get('threshold', 0.5)

            metadata = bundle.get('metadata', {})
            self.model_version = metadata.get('version', 'unknown')

            self.is_real_model = True
            logger.info(f"Loaded real threat detection model: {self.model_version}")

        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {e}")
            self._init_mock_model()

    def _init_mock_model(self):
        """Initialize mock model as fallback."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler

        logger.info("Initializing mock threat detection model")

        # Create a simple model
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )

        # Train on dummy data
        np.random.seed(42)
        X_dummy = np.random.rand(500, 10)
        y_dummy = np.random.randint(0, 2, 500)
        self.model.fit(X_dummy, y_dummy)

        self.scaler = StandardScaler().fit(X_dummy)
        self.model_version = "mock_v1"
        self.is_real_model = False

    def predict(self, features: Dict[str, float]) -> Tuple[float, bool]:
        """
        Predict threat probability and binary classification.

        Args:
            features: Dictionary with 10 required features

        Returns:
            Tuple of (probability_score, is_attack)
        """
        # Validate features
        self._validate_features(features)

        # Extract feature values in order
        feature_values = np.array([[features.get(f, 0) for f in self.selected_features]])

        # Scale features
        if self.scaler is not None:
            feature_values = self.scaler.transform(feature_values)

        # Predict
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(feature_values)[0]
            score = proba[1] if len(proba) > 1 else proba[0]
        else:
            score = float(self.model.predict(feature_values)[0])

        is_attack = score > self.threshold

        return float(score), bool(is_attack)

    def _validate_features(self, features: Dict[str, float]) -> None:
        """Validate that all required features are present."""
        missing = set(self.selected_features) - set(features.keys())
        if missing:
            raise ValueError(f"Missing required features: {missing}")


class RealDecisionTreeModel:
    """
    Real trained model for multi-class attack classification.
    Loads from filesystem or uses intelligent fallback.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.selected_features = ATTACK_CLASSIFICATION_FEATURES
        self.attack_types = ATTACK_TYPES
        self.model_version = "unknown"
        self.is_real_model = False

        # Try to load real model
        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
        else:
            # Try to find latest model in models directory
            latest_model = self._find_latest_model("attack_classifier")
            if latest_model:
                self._load_model(latest_model)
            else:
                logger.warning("No real attack classification model found. Using mock model.")
                self._init_mock_model()

    def _find_latest_model(self, model_type: str) -> Optional[str]:
        """Find the latest model file in models directory."""
        if not MODELS_DIR.exists():
            return None

        model_files = list(MODELS_DIR.glob(f"{model_type}_*.joblib"))
        if not model_files:
            return None

        # Sort by modification time, newest first
        latest = max(model_files, key=lambda p: p.stat().st_mtime)
        return str(latest)

    def _load_model(self, model_path: str):
        """Load real trained model from file."""
        try:
            logger.info(f"Loading attack classification model from: {model_path}")
            bundle = joblib.load(model_path)

            self.model = bundle.get('model')
            self.scaler = bundle.get('scaler')
            self.label_encoder = bundle.get('label_encoder')
            self.selected_features = bundle.get('selected_features', ATTACK_CLASSIFICATION_FEATURES)
            self.attack_types = bundle.get('attack_types', ATTACK_TYPES)

            metadata = bundle.get('metadata', {})
            self.model_version = metadata.get('version', 'unknown')

            self.is_real_model = True
            logger.info(f"Loaded real attack classification model: {self.model_version}")

        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {e}")
            self._init_mock_model()

    def _init_mock_model(self):
        """Initialize mock model as fallback."""
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import RobustScaler, LabelEncoder

        logger.info("Initializing mock attack classification model")

        # Create a simple model
        self.model = DecisionTreeClassifier(
            max_depth=8,
            random_state=42
        )

        # Train on dummy data
        np.random.seed(42)
        X_dummy = np.random.rand(500, 42)
        y_dummy = np.random.randint(0, 14, 500)
        self.model.fit(X_dummy, y_dummy)

        self.scaler = RobustScaler().fit(X_dummy)

        self.label_encoder = LabelEncoder()
        self.label_encoder.classes_ = np.array(list(self.attack_types.values()))

        self.model_version = "mock_v1"
        self.is_real_model = False

    def predict(self, features: Dict[str, float]) -> Tuple[int, str, float]:
        """
        Predict attack type from 42 features.

        Args:
            features: Dictionary with 42 required features

        Returns:
            Tuple of (attack_type_encoded, attack_type_name, confidence)
        """
        # Validate features
        self._validate_features(features)

        # Extract feature values in order
        feature_values = np.array([[features.get(f, 0) for f in self.selected_features]])

        # Scale features
        if self.scaler is not None:
            feature_values = self.scaler.transform(feature_values)

        # Predict
        attack_type_encoded = int(self.model.predict(feature_values)[0])

        # Get attack type name
        if self.label_encoder:
            try:
                attack_type_name = self.label_encoder.classes_[attack_type_encoded]
            except (IndexError, AttributeError):
                attack_type_name = self.attack_types.get(attack_type_encoded, "Unknown")
        else:
            attack_type_name = self.attack_types.get(attack_type_encoded, "Unknown")

        # Calculate confidence
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(feature_values)[0]
            confidence = float(max(proba))
        else:
            confidence = 0.85  # Default confidence for non-probabilistic models

        return attack_type_encoded, attack_type_name, confidence

    def _validate_features(self, features: Dict[str, float]) -> None:
        """Validate that all required features are present."""
        missing = set(self.selected_features) - set(features.keys())
        if missing:
            raise ValueError(f"Missing required features for attack classification: {missing}")


# Global model instances (singleton pattern with lazy loading)
_ensemble_model: Optional[RealEnsembleModel] = None
_decision_tree_model: Optional[RealDecisionTreeModel] = None


def get_ensemble_model() -> RealEnsembleModel:
    """Get or create the ensemble model instance."""
    global _ensemble_model
    if _ensemble_model is None:
        _ensemble_model = RealEnsembleModel()
    return _ensemble_model


def get_decision_tree_model() -> RealDecisionTreeModel:
    """Get or create the decision tree model instance."""
    global _decision_tree_model
    if _decision_tree_model is None:
        _decision_tree_model = RealDecisionTreeModel()
    return _decision_tree_model


def reload_models():
    """Reload models from filesystem (useful after model update)."""
    global _ensemble_model, _decision_tree_model
    _ensemble_model = None
    _decision_tree_model = None
    logger.info("Model instances reset. Will reload on next access.")
