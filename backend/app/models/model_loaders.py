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
from ml_models import ThreatDetectionPipeline, AttackClassificationPipeline

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


def get_threat_pipeline() -> ThreatDetectionPipeline:
    """Get or load the ThreatDetectionPipeline (singleton)."""
    global _threat_pipeline
    if _threat_pipeline is None:
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


def predict_threat(features: Dict[str, float]) -> Tuple[float, bool]:
    """
    Predict threat probability and binary classification.

    Args:
        features: Dictionary with 10 required features

    Returns:
        Tuple of (probability_score, is_attack)
    """
    pipeline = get_threat_pipeline()

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

    Args:
        features: Dictionary with 42 required features

    Returns:
        Tuple of (attack_type_encoded, attack_type_name, confidence)
    """
    pipeline = get_attack_pipeline()

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
        pipeline = get_threat_pipeline()
        return f"threat_detector_{pipeline.random_state}"
    elif pipeline_type == "attack":
        pipeline = get_attack_pipeline()
        return f"attack_classifier_{pipeline.random_state}"
    else:
        return "unknown"


def get_threshold() -> float:
    """Get the threat detection threshold (hardcoded at 0.5)."""
    return 0.5


def reload_models():
    """Reload model instances (clear cache)."""
    global _threat_pipeline, _attack_pipeline
    _threat_pipeline = None
    _attack_pipeline = None
    logger.info("Model pipelines cleared. Will reload on next access.")
