"""
Data preprocessing service for threat detection and attack classification.
Handles feature extraction, validation, and transformation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from app.models.ml_models import EnsembleModel, DecisionTreeModel


class DataPreprocessor:
    """Handles preprocessing for both threat detection and attack classification models."""

    # Features required by ensemble model (10 features)
    THREAT_DETECTION_FEATURES = [
        'service', 'flag', 'src_bytes', 'dst_bytes', 'count',
        'same_srv_rate', 'diff_srv_rate', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_same_src_port_rate'
    ]

    # Features required by decision tree model (42 features)
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

    def __init__(self):
        self.ensemble_model = EnsembleModel()
        self.decision_tree_model = DecisionTreeModel()

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
                # Try to find feature with slight variations (spaces, case)
                found = False
                for key in raw_data.keys():
                    if key.strip().lower() == feature_name.strip().lower():
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
                raise ValueError(f"Missing required feature: {feature_name}")

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
                # Try to find feature with slight variations (spaces, case)
                found = False
                for key in raw_data.keys():
                    if key.strip().lower() == feature_name.strip().lower():
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
            'same_srv_rate', 'diff_srv_rate',
            'dst_host_same_srv_rate', 'dst_host_same_src_port_rate'
        ]

        for feature in rate_features:
            if not (0 <= features[feature] <= 1):
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
