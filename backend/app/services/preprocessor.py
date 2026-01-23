"""
Data preprocessing service for threat detection and attack classification.
Handles feature extraction, validation, and transformation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from app.models.model_loaders import (
    THREAT_DETECTION_FEATURES,
    ATTACK_CLASSIFICATION_FEATURES
)


class DataPreprocessor:
    """Handles preprocessing for both threat detection and attack classification models."""

    # Feature constants imported from model_loaders module
    THREAT_DETECTION_FEATURES = THREAT_DETECTION_FEATURES
    ATTACK_CLASSIFICATION_FEATURES = ATTACK_CLASSIFICATION_FEATURES

    # Header mapping for common CSV header variations
    # Maps common header name variations to the expected feature names
    HEADER_MAPPINGS = {
    # Attack classification - variations with common name differences
    'Destination Port': ' Destination Port',
    'destination_port': ' Destination Port',
    'dest_port': ' Destination Port',
    'Dest Port': ' Destination Port',

    'Flow Duration': ' Flow Duration',
    'flow_duration': ' Flow Duration',

    'Total Fwd Packets': ' Total Fwd Packets',
    'total_fwd_packets': ' Total Fwd Packets',
    'total_fwd_packets': 'Total Fwd Packets',

    'Total Length of Fwd Packets': 'Total Length of Fwd Packets',
    'total_length_of_fwd_packets': 'Total Length of Fwd Packets',
    'total_length_fwd_packets': 'Total Length of Fwd Packets',

    'Fwd Packet Length Max': ' Fwd Packet Length Max',
    'fwd_packet_length_max': ' Fwd Packet Length Max',
    'fwd_packet_len_max': ' Fwd Packet Length Max',

    'Fwd Packet Length Min': ' Fwd Packet Length Min',
    'fwd_packet_length_min': 'Fwd Packet Length Min',
    'fwd_packet_len_min': ' Fwd Packet Length Min',

    'Bwd Packet Length Max': 'Bwd Packet Length Max',
    'bwd_packet_length_max': 'Bwd Packet Length Max',
    'bwd_packet_len_max': 'Bwd Packet Length Max',

    'Bwd Packet Length Min': 'Bwd Packet Length Min',
    'bwd_packet_length_min': 'Bwd Packet Length Min',
    'bwd_packet_len_min': 'Bwd Packet Length Min',

    'Flow Bytes/s': 'Flow Bytes/s',
    'flow_bytes_per_sec': 'Flow Bytes/s',
    'flow_rate': 'Flow Bytes/s',

    'Flow Packets/s': ' Flow Packets/s',
    'flow_packets_per_sec': ' Flow Packets/s',
    'packet_rate': ' Flow Packets/s',

    'Flow IAT Mean': ' Flow IAT Mean',
    'flow_iat_mean': ' Flow IAT Mean',
    'iat_mean': ' Flow IAT Mean',

    'Flow IAT Std': ' Flow IAT Std',
    'flow_iat_std': ' Flow IAT Std',
    'iat_std': ' Flow IAT Std',

    'Flow IAT Min': ' Flow IAT Min',
    'flow_iat_min': ' Flow IAT Min',
    'iat_min': ' Flow IAT Min',

    'Bwd IAT Total': 'Bwd IAT Total',
    'bwd_iat_total': 'Bwd IAT Total',
    'bwd_iat_total': 'Bwd IAT Total',

    'Bwd IAT Std': ' Bwd IAT Std',
    'bwd_iat_std': ' Bwd IAT Std',
    'bwd_iat_std': 'Bwd IAT Std',

    'Fwd PSH Flags': 'Fwd PSH Flags',
    'fwd_psh_flags': 'Fwd PSH Flags',
    'fwd_psh': 'Fwd PSH Flags',

    'Bwd PSH Flags': 'Bwd PSH Flags',
    'bwd_psh_flags': 'Bwd PSH Flags',
    'bwd_psh': 'Bwd PSH Flags',

    'Fwd URG Flags': ' Fwd URG Flags',
    'fwd_urg_flags': ' Fwd URG Flags',
    'fwd_urg': ' Fwd URG Flags',

    'Bwd URG Flags': ' Bwd URG Flags',
    'bwd_urg_flags': 'Bwd URG Flags',
    'bwd_urg': 'Bwd URG Flags',

    'Fwd Header Length': ' Fwd Header Length',
    'fwd_header_length': ' Fwd Header Length',
    'fwd_hdr_len': ' Fwd Header Length',

    'Bwd Header Length': ' Bwd Header Length',
    'bwd_header_length': ' Bwd Header Length',
    'bwd_hdr_len': ' Bwd Header Length',

    'Bwd Packets/s': ' Bwd Packets/s',
    'bwd_packets_per_sec': ' Bwd Packets/s',
    'bwd_packet_rate': ' Bwd Packets/s',

    'Min Packet Length': ' Min Packet Length',
    'min_packet_length': ' Min Packet Length',
    'min_pkt_len': ' Min Packet Length',

    'FIN Flag Count': 'FIN Flag Count',
    'fin_flag_cnt': 'FIN Flag Count',
    'fin_flags': 'FIN Flag Count',

    'RST Flag Count': 'RST Flag Count',
    'rst_flag_count': 'RST Flag Count',
    'rst_flags': 'RST Flag Count',

    'PSH Flag Count': ' PSH Flag Count',
    'psh_flag_count': 'PSH Flag Count',
    'psh_flags': 'PSH Flag Count',

    'ACK Flag Count': 'ACK Flag Count',
    'ack_flag_count': 'ACK Flag Count',
    'ack_flags': 'ACK Flag Count',

    'URG Flag Count': 'URG Flag Count',
    'urg_flag_count': 'URG Flag Count',
    'urg_flags': 'URG Flag Count',

    'Down/Up Ratio': 'Down/Up Ratio',
    'down_up_ratio': 'Down/Up Ratio',
    'down_up': 'Down/Up Ratio',

    'Fwd Avg Bytes/Bulk': 'Fwd Avg Bytes/Bulk',
    'fwd_avg_bytes_per_bulk': 'Fwd Avg Bytes/Bulk',
    'fwd_avg_bytes_bulk': 'Fwd Avg Bytes/Bulk',

    'Fwd Avg Packets/Bulk': 'Fwd Avg Packets/Bulk',
    'fwd_avg_packets_per_bulk': 'Fwd Avg Packets/Bulk',
    'fwd_avg_packets_bulk': 'Fwd Avg Packets/Bulk',

    'Fwd Avg Bulk Rate': ' Fwd Avg Bulk Rate',
    'fwd_avg_bulk_rate': ' Fwd Avg Bulk Rate',
    'fwd_avg_bulk_rate': 'Fwd Avg Bulk Rate',

    'Bwd Avg Bytes/Bulk': ' Bwd Avg Bytes/Bulk',
    'bwd_avg_bytes_per_bulk': 'Bwd Avg Bytes/Bulk',
    'bwd_avg_bytes_bulk': 'Bwd Avg Bytes/Bulk',

    'Bwd Avg Packets/Bulk': 'Bwd Avg Packets/Bulk',
    'bwd_avg_packets_per_bulk': 'Bwd Avg Packets/Bulk',
    'bwd_avg_packets_bulk': 'Bwd Avg Packets/Bulk',

    'Bwd Avg Bulk Rate': 'Bwd Avg Bulk Rate',
    'bwd_avg_bulk_rate': 'Bwd Avg Bulk Rate',
    'bwd_avg_bulk_rate': 'Bwd Avg Bulk Rate',

    'Init_Win_bytes_forward': 'Init_Win_bytes_forward',
    'init_win_bytes_fwd': 'Init_Win_bytes_forward',
    'init_win_fwd': 'Init_Win_bytes_forward',

    'Init_Win_bytes_backward': 'Init_Win_bytes_backward',
    'init_win_bytes_bwd': 'Init_Win_bytes_backward',
    'init_win_bwd': 'Init_Win_bytes_backward',

    'min_seg_size_forward': ' min_seg_size_forward',
    'min_seg_size_fwd': 'min_seg_size_forward',
    'min_seg_size_fwd': 'min_seg_size_forward',

    'Active Mean': 'Active Mean',
    'active_mean': 'Active Mean',
    'avg_active': 'Active Mean',

    'Active Std': ' Active Std',
    'active_std': 'Active Std',
    'active_stdev': 'Active Std',

    'Active Max': 'Active Max',
    'active_max': 'Active Max',
    'active_max_value': 'Active Max',

    'Idle Std': ' Idle Std',
    'idle_std': 'Idle Std',
    'idle_stdev': 'Idle Std',

    # Threat detection mappings
    'protocol_type': 'protocol_type',
    'protocol': 'protocol_type',
    'proto': 'protocol_type',

    'service': 'service',
    'service_type': 'service',

    'flag': 'flag',
    'tcp_flags': 'flag',
    'flags': 'flag',

    'src_bytes': 'src_bytes',
    'source_bytes': 'src_bytes',

    'dst_bytes': 'dst_bytes',
    'dest_bytes': 'dst_bytes',
    'destination_bytes': 'dst_bytes',

    'count': 'count',
    'packet_count': 'count',
    'connection_count': 'count',

    'same_srv_rate': 'same_srv_rate',
    'same_service_rate': 'same_srv_rate',

    'diff_srv_rate': 'diff_srv_rate',
    'diff_service_rate': 'diff_srv_rate',
    'srv_rate': 'diff_srv_rate',

    'dst_host_srv_count': 'dst_host_srv_count',
    'destination_host_srv_count': 'dst_host_srv_count',
    'host_srv_count': 'dst_host_srv_count',

    'dst_host_same_srv_rate': 'dst_host_same_srv_rate',
    'destination_host_same_srv_rate': 'dst_host_same_srv_rate',
    'host_same_srv_rate': 'dst_host_same_srv_rate',
}


    def __init__(self):
        pass  # No longer need to instantiate model_models


    @staticmethod
    def _normalize_header_name(header: str) -> str:
        """
        Normalize CSV header name to match expected feature names.

        Args:
            header: Raw header name from CSV

        Returns:
            Normalized header name matching expected feature names
        """
        # Strip whitespace
        normalized = header.strip()

        # Try direct match first (fast path)
        if normalized in THREAT_DETECTION_FEATURES or normalized in ATTACK_CLASSIFICATION_FEATURES:
            return normalized

        # Try header mappings
        return DataPreprocessor.HEADER_MAPPINGS.get(normalized, normalized)


    def validate_and_extract_features_with_profile(
        self,
        raw_data: Dict[str, Any],
        expected_features: List[str],
        allow_extra_columns: bool = True
    ) -> Dict[str, float]:
        """
        Extract and validate features based on a custom feature profile.

        Args:
            raw_data: Raw feature dictionary from CSV or API
            expected_features: Ordered list of required feature names
            allow_extra_columns: If True, extra columns are ignored with a warning; if False, they cause an error

        Returns:
            Dictionary of validated features in the expected order

        Raises:
            ValueError: If required features are missing or validation fails
        """
        features = {}
        missing_features = []
        extra_columns = []

        # Check for required features
        for feature_name in expected_features:
            if feature_name not in raw_data:
                # Try to find feature with slight variations (spaces, case, or mapped names)
                found = False
                for key in raw_data.keys():
                    normalized = _normalize_header_name(key)
                    if normalized == feature_name:
                        features[feature_name] = self._convert_to_float(
                            raw_data[key], feature_name
                        )
                        found = True
                        break

                if not found:
                    missing_features.append(feature_name)
            else:
                features[feature_name] = self._convert_to_float(
                    raw_data[feature_name], feature_name
                )

        # Check for extra columns
        raw_data_keys = set(raw_data.keys())
        expected_keys = set(expected_features)
        extra_columns = list(raw_data_keys - expected_keys)

        # Raise error if required features are missing
        if missing_features:
            raise ValueError(
                f"Missing required features: {', '.join(missing_features)}. "
                f"Expected {len(expected_features)} features but found {len(raw_data)} columns."
            )

        # Handle extra columns
        if extra_columns and not allow_extra_columns:
            raise ValueError(
                f"Unexpected columns found: {', '.join(extra_columns)}. "
                f"Only the {len(expected_features)} expected features are allowed."
            )

        return features

    def validate_and_extract_features(
        self,
        raw_data: Dict[str, Any],
        model_type: str = "auto"
    ) -> Tuple[Dict[str, float], str]:
        """
        Validate and extract features for the specified model.

        Args:
            raw_data: Raw feature dictionary from CSV or API
            model_type: "threat_detection", "attack_classification", or "auto"

        Returns:
            Tuple of (extracted_features, detected_model_type)

        Raises:
            ValueError: If data is invalid or features are missing
        """
        # Auto-detect model type based on available features
        if model_type == "auto":
            model_type = self._detect_model_type(raw_data)

        if model_type == "threat_detection":
            features = self._extract_threat_detection_features(raw_data)
        elif model_type == "attack_classification":
            features = self._extract_attack_classification_features(raw_data)
        else:
            raise ValueError(f"Invalid model type: {model_type}")

        return features, model_type

    def _detect_model_type(self, raw_data: Dict[str, Any]) -> str:
        """Auto-detect which model to use based on available features."""
        threat_detection_match = sum(
            1 for f in self.THREAT_DETECTION_FEATURES if f in raw_data
        )
        attack_classification_match = sum(
            1 for f in self.ATTACK_CLASSIFICATION_FEATURES if f in raw_data
        )

        # Prioritize attack classification if it has more matching features
        if attack_classification_match >= 35:  # At least 80% of features
            return "attack_classification"
        elif threat_detection_match >= 8:  # At least 80% of features
            return "threat_detection"
        else:
            raise ValueError(
                f"Cannot auto-detect model type. "
                f"Threat detection match: {threat_detection_match}/10, "
                f"Attack classification match: {attack_classification_match}/42"
            )

    def _extract_threat_detection_features(
        self,
        raw_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract and validate 10 features for threat detection."""
        features = {}

        for feature_name in self.THREAT_DETECTION_FEATURES:
            if feature_name not in raw_data:
                # Try to find feature with slight variations (spaces, case, or mapped names)
                found = False
                for key in raw_data.keys():
                    normalized = _normalize_header_name(key)
                    if normalized == feature_name:
                        value = raw_data[key]
                        # Convert to float
                        try:
                            features[feature_name] = float(value)
                        except (TypeError, ValueError):
                            raise ValueError(
                                f"Invalid value for feature '{feature_name}': {value}. "
                                f"Expected numeric value."
                            )
                        found = True
                        break

                if not found:
                    raise ValueError(f"Missing required feature: {feature_name}")
            else:
                value = raw_data[feature_name]
                # Convert to float
                try:
                    features[feature_name] = float(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Invalid value for feature '{feature_name}': {value}. "
                        f"Expected numeric value."
                    )

        # Validate ranges
        self._validate_threat_detection_ranges(features)

        return features

    def _extract_attack_classification_features(
        self,
        raw_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract and validate 42 features for attack classification."""
        features = {}

        for feature_name in self.ATTACK_CLASSIFICATION_FEATURES:
            if feature_name not in raw_data:
                # Try to find feature with slight variations (spaces, case, or mapped names)
                found = False
                for key in raw_data.keys():
                    normalized = _normalize_header_name(key)
                    if normalized == feature_name:
                        features[feature_name] = self._convert_to_float(
                            raw_data[key], feature_name
                        )
                        found = True
                        break

                if not found:
                    raise ValueError(f"Missing required feature: {feature_name}")
            else:
                features[feature_name] = self._convert_to_float(
                    raw_data[feature_name], feature_name
                )

        # Validate ranges
        self._validate_attack_classification_ranges(features)

        return features

    def _convert_to_float(self, value: Any, feature_name: str) -> float:
        """Convert value to float with error handling."""
        try:
            # Handle inf and -inf values
            float_value = float(value)
            if np.isinf(float_value):
                return 0.0  # Replace inf with 0
            return float_value
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid value for feature '{feature_name}': {value}. "
                f"Expected numeric value."
            )

    def _validate_threat_detection_ranges(self, features: Dict[str, float]) -> None:
        """Validate that threat detection features are in expected ranges."""
        # Rate features should be between 0 and 1
        rate_features = [
            'diff_srv_rate',
            'dst_host_same_srv_rate', 'dst_host_same_src_port_rate',
            'dst_host_diff_srv_rate', 'dst_host_srv_diff_host_rate'
        ]

        for feature in rate_features:
            if feature in features and not (0 <= features[feature] <= 1):
                raise ValueError(
                    f"Feature '{feature}' must be between 0 and 1, "
                    f"got {features[feature]}"
                )

        # Byte and count features should be non-negative
        non_negative_features = ['src_bytes', 'dst_bytes', 'count', 'dst_host_srv_count']
        for feature in non_negative_features:
            if features[feature] < 0:
                raise ValueError(
                    f"Feature '{feature}' must be non-negative, "
                    f"got {features[feature]}"
                )

    def _validate_attack_classification_ranges(self, features: Dict[str, float]) -> None:
        """Validate that attack classification features are in expected ranges."""
        # Port should be 0-65535
        if not (0 <= features[' Destination Port'] <= 65535):
            raise ValueError(
                f"Destination Port must be between 0 and 65535, "
                f"got {features[' Destination Port']}"
            )

        # Most features should be non-negative (except ratios)
        for feature_name, value in features.items():
            if 'Ratio' not in feature_name and value < 0:
                # Allow some flexibility for network features
                if value < -1000:
                    raise ValueError(
                        f"Feature '{feature_name}' has unrealistic negative value: {value}"
                    )

    def process_csv_row(
        self,
        row: Dict[str, Any],
        model_type: str = "auto"
    ) -> Tuple[Dict[str, float], str]:
        """
        Process a single CSV row and extract features.

        Args:
            row: Dictionary representing a CSV row
            model_type: "threat_detection", "attack_classification", or "auto"

        Returns:
            Tuple of (processed_features, model_type)
        """
        return self.validate_and_extract_features(row, model_type)

    def process_csv_dataframe(
        self,
        df: pd.DataFrame,
        model_type: str = "auto"
    ) -> Tuple[List[Dict[str, float]], str]:
        """
        Process entire CSV dataframe and extract features for all rows.

        Args:
            df: Pandas DataFrame with CSV data
            model_type: "threat_detection", "attack_classification", or "auto"

        Returns:
            Tuple of (list_of_feature_dicts, model_type)
        """
        processed_rows = []

        # Auto-detect from first row
        first_row = df.iloc[0].to_dict()
        _, detected_model_type = self.validate_and_extract_features(
            first_row,
            model_type
        )

        # Process all rows
        for idx, row in df.iterrows():
            try:
                features, _ = self.validate_and_extract_features(
                    row.to_dict(),
                    detected_model_type
                )
                processed_rows.append(features)
            except ValueError as e:
                raise ValueError(f"Error processing row {idx}: {str(e)}")

        return processed_rows, detected_model_type

    def generate_sample_threat_detection_data(self) -> Dict[str, float]:
        """Generate sample data for threat detection model (for testing)."""
        return {
            'service': 5,
            'flag': 2,
            'src_bytes': 1500,
            'dst_bytes': 2000,
            'count': 10,
            'same_srv_rate': 0.8,
            'diff_srv_rate': 0.1,
            'dst_host_srv_count': 50,
            'dst_host_same_srv_rate': 0.75,
            'dst_host_same_src_port_rate': 0.9
        }

    def generate_sample_attack_classification_data(self) -> Dict[str, float]:
        """Generate sample data for attack classification model (for testing)."""
        return {
            ' Destination Port': 80,
            ' Flow Duration': 5000,
            ' Total Fwd Packets': 50,
            'Total Length of Fwd Packets': 5000,
            ' Fwd Packet Length Max': 1500,
            ' Fwd Packet Length Min': 60,
            'Bwd Packet Length Max': 1500,
            ' Bwd Packet Length Min': 60,
            'Flow Bytes/s': 1000,
            ' Flow Packets/s': 10,
            ' Flow IAT Mean': 100,
            ' Flow IAT Std': 50,
            ' Flow IAT Min': 10,
            'Bwd IAT Total': 500,
            ' Bwd IAT Std': 25,
            'Fwd PSH Flags': 1,
            ' Bwd PSH Flags': 1,
            ' Fwd URG Flags': 0,
            ' Bwd URG Flags': 0,
            ' Fwd Header Length': 200,
            ' Bwd Header Length': 200,
            ' Bwd Packets/s': 5,
            ' Min Packet Length': 60,
            'FIN Flag Count': 1,
            ' RST Flag Count': 0,
            ' PSH Flag Count': 2,
            ' ACK Flag Count': 10,
            ' URG Flag Count': 0,
            ' Down/Up Ratio': 0.5,
            'Fwd Avg Bytes/Bulk': 500,
            ' Fwd Avg Packets/Bulk': 5,
            ' Fwd Avg Bulk Rate': 100,
            ' Bwd Avg Bytes/Bulk': 500,
            ' Bwd Avg Packets/Bulk': 5,
            'Bwd Avg Bulk Rate': 100,
            'Init_Win_bytes_forward': 8192,
            ' Init_Win_bytes_backward': 8192,
            ' min_seg_size_forward': 20,
            'Active Mean': 100,
            ' Active Std': 50,
            ' Active Max': 200,
            ' Idle Std': 25
        }
