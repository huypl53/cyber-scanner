"""
Mock ML models for threat detection and attack classification.
These models simulate the behavior of the trained ensemble and decision tree models.
"""
import numpy as np
from typing import Dict, List, Tuple
import hashlib


class EnsembleModel:
    """
    Mock Ensemble Model for binary threat detection (Normal vs Attack).
    Simulates the ensemble of ANN + LSTM models from the research code.
    Uses 10 features for prediction.
    """

    REQUIRED_FEATURES = [
        'service', 'flag', 'src_bytes', 'dst_bytes', 'count',
        'same_srv_rate', 'diff_srv_rate', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_same_src_port_rate'
    ]

    def __init__(self):
        self.threshold = 0.5
        self.model_version = "ensemble_v1"

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
        feature_values = [features.get(f, 0) for f in self.REQUIRED_FEATURES]

        # Generate a deterministic but realistic prediction based on feature patterns
        score = self._calculate_threat_score(feature_values)

        # Add some randomness based on feature hash for realism
        feature_hash = self._hash_features(feature_values)
        noise = (feature_hash % 20) / 100  # 0-0.19 noise
        score = min(1.0, max(0.0, score + noise - 0.1))

        is_attack = score > self.threshold

        return score, is_attack

    def _validate_features(self, features: Dict[str, float]) -> None:
        """Validate that all required features are present."""
        missing = set(self.REQUIRED_FEATURES) - set(features.keys())
        if missing:
            raise ValueError(f"Missing required features: {missing}")

    def _calculate_threat_score(self, feature_values: List[float]) -> float:
        """
        Calculate threat score based on feature patterns.
        Higher values in certain features indicate higher threat probability.
        """
        # Normalize features (simple min-max approach with assumed ranges)
        # In real model, these would be based on training data statistics

        # Extract key indicators
        src_bytes = min(feature_values[2] / 10000, 1.0) if feature_values[2] > 0 else 0
        dst_bytes = min(feature_values[3] / 10000, 1.0) if feature_values[3] > 0 else 0
        count = min(feature_values[4] / 500, 1.0)
        same_srv_rate = feature_values[5]
        diff_srv_rate = feature_values[6]
        dst_host_srv_count = min(feature_values[7] / 255, 1.0)

        # Simple heuristic: high count + high dst_host_srv_count + unusual service rates
        # indicate potential attack
        threat_indicators = []

        # High connection count
        if count > 0.5:
            threat_indicators.append(0.3)

        # Unusual service rate patterns
        if same_srv_rate < 0.3 or same_srv_rate > 0.95:
            threat_indicators.append(0.2)

        if diff_srv_rate > 0.5:
            threat_indicators.append(0.25)

        # High destination host connections
        if dst_host_srv_count > 0.7:
            threat_indicators.append(0.25)

        # Large data transfers
        if src_bytes > 0.8 or dst_bytes > 0.8:
            threat_indicators.append(0.15)

        # Calculate final score
        base_score = sum(threat_indicators) if threat_indicators else 0.1
        return min(base_score, 0.95)

    def _hash_features(self, feature_values: List[float]) -> int:
        """Create a deterministic hash from features for reproducible randomness."""
        feature_str = ''.join([f"{v:.6f}" for v in feature_values])
        return int(hashlib.md5(feature_str.encode()).hexdigest(), 16)


class DecisionTreeModel:
    """
    Mock Decision Tree Model for multi-class attack classification (14 classes).
    Uses 42 features for prediction.
    """

    REQUIRED_FEATURES = [
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

    def __init__(self):
        self.model_version = "decision_tree_v1"

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

        # Extract feature values
        feature_values = [features.get(f, 0) for f in self.REQUIRED_FEATURES]

        # Classify based on feature patterns
        attack_type_encoded = self._classify_attack(feature_values)
        attack_type_name = self.ATTACK_TYPES[attack_type_encoded]

        # Calculate confidence (mock: higher for more distinct patterns)
        confidence = self._calculate_confidence(feature_values, attack_type_encoded)

        return attack_type_encoded, attack_type_name, confidence

    def _validate_features(self, features: Dict[str, float]) -> None:
        """Validate that all required features are present."""
        missing = set(self.REQUIRED_FEATURES) - set(features.keys())
        if missing:
            raise ValueError(f"Missing required features for attack classification: {missing}")

    def _classify_attack(self, feature_values: List[float]) -> int:
        """
        Classify attack type based on feature patterns.
        This is a simplified heuristic-based classification.
        """
        # Extract key features for classification
        dest_port = feature_values[0]
        flow_duration = feature_values[1]
        total_fwd_packets = feature_values[2]
        flow_bytes_s = feature_values[8]
        flow_packets_s = feature_values[9]
        fin_flag = feature_values[23]
        rst_flag = feature_values[24]
        psh_flag = feature_values[25]
        ack_flag = feature_values[26]

        # Create deterministic hash for consistent classification
        feature_hash = self._hash_features(feature_values)

        # Port-based detection
        if dest_port == 21:  # FTP
            return 4  # FTP-Patator

        if dest_port == 22:  # SSH
            return 7  # SSH-Patator

        if dest_port in [80, 443, 8080]:  # Web ports
            if psh_flag > 0 and ack_flag > 10:
                # Determine web attack type based on hash
                web_attacks = [9, 11, 12]  # Brute Force, XSS, SQL Injection
                return web_attacks[feature_hash % 3]

        # High packet rate -> DDoS/DoS
        if flow_packets_s > 1000:
            if total_fwd_packets > 100:
                return 2  # DDoS
            else:
                # Determine DoS type based on patterns
                dos_types = [1, 5, 6, 8]  # Hulk, slowloris, Slowhttptest, GoldenEye
                return dos_types[feature_hash % 4]

        # Port scanning detection
        if fin_flag > 0 and rst_flag > 0 and flow_duration < 1000:
            return 3  # PortScan

        # Bot detection (unusual patterns)
        if flow_bytes_s > 5000 and flow_bytes_s < 50000 and ack_flag > 5:
            return 10  # Bot

        # Infiltration (long duration, moderate traffic)
        if flow_duration > 100000 and flow_bytes_s > 100:
            return 13  # Infiltration

        # Default to BENIGN if no attack pattern matches
        return 0  # BENIGN

    def _calculate_confidence(self, feature_values: List[float], attack_type: int) -> float:
        """Calculate confidence score (0-1) for the prediction."""
        # Mock confidence: more distinct patterns get higher confidence
        feature_hash = self._hash_features(feature_values)
        base_confidence = 0.75 + (feature_hash % 25) / 100  # 0.75-0.99
        return round(base_confidence, 2)

    def _hash_features(self, feature_values: List[float]) -> int:
        """Create a deterministic hash from features."""
        feature_str = ''.join([f"{v:.6f}" for v in feature_values])
        return int(hashlib.md5(feature_str.encode()).hexdigest(), 16)


# Global model instances (singleton pattern)
_ensemble_model = None
_decision_tree_model = None


def get_ensemble_model() -> EnsembleModel:
    """Get or create the ensemble model instance."""
    global _ensemble_model
    if _ensemble_model is None:
        _ensemble_model = EnsembleModel()
    return _ensemble_model


def get_decision_tree_model() -> DecisionTreeModel:
    """Get or create the decision tree model instance."""
    global _decision_tree_model
    if _decision_tree_model is None:
        _decision_tree_model = DecisionTreeModel()
    return _decision_tree_model
