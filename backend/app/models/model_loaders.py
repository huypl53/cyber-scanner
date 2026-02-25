"""
Lightweight model loaders that use ml_models package directly.

This module provides simple functions to load and use the ML models from
the ml-models workspace package, with singleton caching and dict→DataFrame conversion.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional

# Import from ml-models workspace package
from ml_models import AttackClassificationPipeline

try:
    from ml_models import ThreatDetectionPipeline
except ImportError:
    ThreatDetectionPipeline = None

logger = logging.getLogger(__name__)

# Model storage directory
MODELS_DIR = Path(__file__).parent.parent.parent / "models"

# Expected features (must match what the model expects)
# Based on threat_detector_profile.json - the 11 features the model was trained on
THREAT_DETECTION_FEATURES = [
    'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'count', 'same_srv_rate', 'diff_srv_rate', 'dst_host_srv_count',
    'dst_host_same_srv_rate'
]

ATTACK_CLASSIFICATION_FEATURES = [
    'Destination Port', 'Flow Duration', 'Total Fwd Packets',
    'Total Length of Fwd Packets', 'Fwd Packet Length Max',
    'Fwd Packet Length Min', 'Bwd Packet Length Max',
    'Bwd Packet Length Min', 'Flow Bytes/s', 'Flow Packets/s',
    'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Min', 'Bwd IAT Total',
    'Bwd IAT Std', 'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags',
    'Bwd URG Flags', 'Fwd Header Length', 'Bwd Header Length',
    'Bwd Packets/s', 'Min Packet Length', 'FIN Flag Count',
    'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count',
    'URG Flag Count', 'Down/Up Ratio', 'Fwd Avg Bytes/Bulk',
    'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
    'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Init_Win_bytes_forward',
    'Init_Win_bytes_backward', 'min_seg_size_forward', 'Active Mean',
    'Active Std', 'Active Max', 'Idle Std'
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

# Singleton cache
_threat_pipeline: Optional[ThreatDetectionPipeline] = None
_attack_pipeline: Optional[AttackClassificationPipeline] = None


def _find_latest_model(model_type: str) -> Optional[str]:
    """Find the latest model file in models directory."""
    if not MODELS_DIR.exists():
        return None

    model_files = list(MODELS_DIR.glob(f"{model_type}_*.joblib"))
    if not model_files:
        return None

    # Sort by modification time, newest first
    latest = max(model_files, key=lambda p: p.stat().st_mtime)
    return str(latest)


def get_threat_pipeline():
    """Get or load the ThreatDetectionPipeline (singleton)."""
    global _threat_pipeline
    if _threat_pipeline is None:
        if ThreatDetectionPipeline is None:
            raise ImportError(
                "ThreatDetectionPipeline requires TensorFlow. "
                "Install with: pip install tensorflow"
            )
        model_path = _find_latest_model("threat_detector")
        if model_path:
            logger.info(f"Loading threat detection pipeline from: {model_path}")
            _threat_pipeline = ThreatDetectionPipeline.load_from_bundle(model_path)
        else:
            raise FileNotFoundError(
                "No threat detection model found. Expected a file matching "
                "'threat_detector_*.joblib' in the models directory."
            )
    return _threat_pipeline


def get_attack_pipeline() -> AttackClassificationPipeline:
    """Get or load the AttackClassificationPipeline (singleton)."""
    global _attack_pipeline
    if _attack_pipeline is None:
        model_path = _find_latest_model("attack_classifier")
        if model_path:
            logger.info(f"Loading attack classification pipeline from: {model_path}")
            _attack_pipeline = AttackClassificationPipeline.load_from_bundle(model_path)
        else:
            raise FileNotFoundError(
                "No attack classification model found. Expected a file matching "
                "'attack_classifier_*.joblib' in the models directory."
            )
    return _attack_pipeline


def _mock_threat_prediction(features: Dict[str, float]) -> Tuple[float, bool]:
    """Mock threat prediction based on heuristic feature analysis."""
    import hashlib
    # Deterministic score from features for consistency
    feature_str = str(sorted(features.items()))
    hash_val = int(hashlib.md5(feature_str.encode()).hexdigest(), 16)
    score = (hash_val % 1000) / 1000.0  # 0.0 - 1.0
    # Weight by suspicious indicators
    if features.get('src_bytes', 0) > 10000:
        score = min(score + 0.2, 1.0)
    if features.get('diff_srv_rate', 0) > 0.5:
        score = min(score + 0.15, 1.0)
    is_attack = score > 0.5
    return score, is_attack


def _mock_attack_prediction(features: Dict[str, float]) -> Tuple[int, str, float]:
    """Mock attack classification based on heuristic feature analysis."""
    import hashlib
    feature_str = str(sorted(features.items()))
    hash_val = int(hashlib.md5(feature_str.encode()).hexdigest(), 16)
    attack_type_idx = hash_val % len(ATTACK_TYPES)
    confidence = 0.5 + (hash_val % 500) / 1000.0
    return attack_type_idx, ATTACK_TYPES[attack_type_idx], confidence


# Track mock fallback state with retry support
_using_mock_threat = False
_using_mock_attack = False
_mock_threat_since: Optional[float] = None
_mock_attack_since: Optional[float] = None
_MOCK_RETRY_INTERVAL = 60.0  # seconds before retrying real model load


def _should_retry_real_model(mock_since: Optional[float]) -> bool:
    """Check if enough time has passed to retry loading a real model."""
    if mock_since is None:
        return True
    import time
    return (time.time() - mock_since) >= _MOCK_RETRY_INTERVAL


def predict_threat(features: Dict[str, float]) -> Tuple[float, bool]:
    """
    Predict threat probability and binary classification.
    Falls back to mock predictions if model/TensorFlow not available.
    Periodically retries loading the real model.
    """
    global _using_mock_threat, _mock_threat_since

    if _using_mock_threat:
        if not _should_retry_real_model(_mock_threat_since):
            return _mock_threat_prediction(features)
        # Retry: reset flag and clear cached pipeline for fresh attempt
        global _threat_pipeline
        _using_mock_threat = False
        _mock_threat_since = None
        _threat_pipeline = None

    try:
        pipeline = get_threat_pipeline()
    except (ImportError, FileNotFoundError) as e:
        import time
        logger.warning(f"Using mock threat predictions: {e}")
        _using_mock_threat = True
        _mock_threat_since = time.time()
        return _mock_threat_prediction(features)

    # Validate features
    missing = set(THREAT_DETECTION_FEATURES) - set(features.keys())
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    # Convert dict to DataFrame (single row)
    df = pd.DataFrame([features])

    # Predict
    preds, prob_ensemble, _ = pipeline.predict(df)

    score = float(prob_ensemble[0])
    is_attack = bool(preds[0])

    return score, is_attack


def predict_attack_type(features: Dict[str, float]) -> Tuple[int, str, float]:
    """
    Predict attack type from 42 features.
    Falls back to mock predictions if model not available.
    """
    global _using_mock_attack, _mock_attack_since

    if _using_mock_attack:
        if not _should_retry_real_model(_mock_attack_since):
            return _mock_attack_prediction(features)
        # Retry: reset flag and clear cached pipeline for fresh attempt
        global _attack_pipeline
        _using_mock_attack = False
        _mock_attack_since = None
        _attack_pipeline = None

    try:
        pipeline = get_attack_pipeline()
    except (ImportError, FileNotFoundError) as e:
        import time
        logger.warning(f"Using mock attack predictions: {e}")
        _using_mock_attack = True
        _mock_attack_since = time.time()
        return _mock_attack_prediction(features)

    # Validate features
    missing = set(ATTACK_CLASSIFICATION_FEATURES) - set(features.keys())
    if missing:
        raise ValueError(f"Missing required features for attack classification: {missing}")

    # Convert dict to DataFrame (single row)
    df = pd.DataFrame([features])

    # Predict
    predicted_encoded, confidence, predicted_labels = pipeline.predict(df)

    attack_type_encoded = int(predicted_encoded[0])
    attack_type_name = str(predicted_labels[0])
    confidence_score = float(confidence[0])

    return attack_type_encoded, attack_type_name, confidence_score


def get_model_version(pipeline_type: str) -> str:
    """Get the version info for a pipeline."""
    if pipeline_type == "threat":
        if _using_mock_threat:
            return "mock_v1"
        try:
            pipeline = get_threat_pipeline()
            return f"threat_detector_{pipeline.random_state}"
        except (ImportError, FileNotFoundError):
            return "mock_v1"
    elif pipeline_type == "attack":
        if _using_mock_attack:
            return "mock_v1"
        try:
            pipeline = get_attack_pipeline()
            return f"attack_classifier_{pipeline.random_state}"
        except (ImportError, FileNotFoundError):
            return "mock_v1"
    else:
        return "unknown"


def get_threshold() -> float:
    """Get the threat detection threshold (hardcoded at 0.5)."""
    return 0.5


def reload_models():
    """Reload model instances (clear cache) and reset mock fallback state."""
    global _threat_pipeline, _attack_pipeline
    global _using_mock_threat, _using_mock_attack
    global _mock_threat_since, _mock_attack_since
    _threat_pipeline = None
    _attack_pipeline = None
    _using_mock_threat = False
    _using_mock_attack = False
    _mock_threat_since = None
    _mock_attack_since = None
    logger.info("Model pipelines cleared. Will reload on next access.")
