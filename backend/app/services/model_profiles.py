"""
Default model profiles for backward compatibility and easy configuration.
Defines expected features and class labels for standard model types.
"""
from typing import Dict, List, Optional


# Default threat detection profile (10 features, binary classification)
# Updated to match actual trained model features
DEFAULT_THREAT_DETECTION_FEATURES = [
    'flag', 'src_bytes', 'dst_bytes', 'count', 'diff_srv_rate',
    'dst_host_srv_count', 'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
    'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate'
]

DEFAULT_THREAT_DETECTION_CLASSES = [
    'Normal',
    'Attack'
]


# Default attack classification profile (42 features, 14 attack classes)
DEFAULT_ATTACK_CLASSIFICATION_FEATURES = [
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

DEFAULT_ATTACK_CLASSIFICATION_CLASSES = [
    'BENIGN',
    'DoS Hulk',
    'DDoS',
    'PortScan',
    'FTP-Patator',
    'DoS slowloris',
    'DoS Slowhttptest',
    'SSH-Patator',
    'DoS GoldenEye',
    'Web Attack – Brute Force',
    'Bot',
    'Web Attack – XSS',
    'Web Attack – Sql Injection',
    'Infiltration'
]


def get_default_profile(model_type: str) -> Dict[str, any]:
    """
    Get default model profile for a given model type.

    Args:
        model_type: 'threat_detector' or 'attack_classifier'

    Returns:
        Dictionary with expected_features, class_labels, and preprocessing_notes
    """
    if model_type == 'threat_detector':
        return {
            'expected_features': DEFAULT_THREAT_DETECTION_FEATURES,
            'class_labels': DEFAULT_THREAT_DETECTION_CLASSES,
            'preprocessing_notes': 'Default 10-feature threat detection profile'
        }
    elif model_type == 'attack_classifier':
        return {
            'expected_features': DEFAULT_ATTACK_CLASSIFICATION_FEATURES,
            'class_labels': DEFAULT_ATTACK_CLASSIFICATION_CLASSES,
            'preprocessing_notes': 'Default 42-feature attack classification profile with 14 attack types'
        }
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def validate_profile_config(
    expected_features: Optional[List[str]],
    class_labels: Optional[List[str]]
) -> Dict[str, List[str]]:
    """
    Validate model profile configuration.

    Args:
        expected_features: List of feature names
        class_labels: List of class label names

    Returns:
        Dictionary with any validation errors

    Raises:
        ValueError: If validation fails
    """
    errors = []

    # Validate features
    if expected_features is not None:
        if not isinstance(expected_features, list):
            errors.append("expected_features must be a list")
        elif len(expected_features) == 0:
            errors.append("expected_features cannot be empty")
        elif len(expected_features) != len(set(expected_features)):
            errors.append("expected_features must contain unique values")
        elif not all(isinstance(f, str) and f.strip() for f in expected_features):
            errors.append("all feature names must be non-empty strings")

    # Validate class labels
    if class_labels is not None:
        if not isinstance(class_labels, list):
            errors.append("class_labels must be a list")
        elif len(class_labels) == 0:
            errors.append("class_labels cannot be empty")
        elif len(class_labels) != len(set(class_labels)):
            errors.append("class_labels must contain unique values")
        elif not all(isinstance(c, str) and c.strip() for c in class_labels):
            errors.append("all class labels must be non-empty strings")

    if errors:
        raise ValueError("; ".join(errors))

    return {"valid": True}
