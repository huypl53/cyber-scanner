"""
Model validation service for uploaded ML models.
Validates file format, architecture, and performs test predictions.

Supports:
- Raw sklearn models (.pkl, .joblib)
- Pipeline bundles from ml_models package (.joblib)
- Keras/TensorFlow models (.h5)
"""
import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
import tempfile

logger = logging.getLogger(__name__)


class ModelValidationError(Exception):
    """Raised when model validation fails."""
    pass


class ModelValidator:
    """
    Validates uploaded ML models for threat detection and attack classification.

    Supports:
    - .pkl (Python pickle)
    - .joblib (scikit-learn joblib) — including pipeline bundles
    - .h5 (Keras/TensorFlow)
    """

    # Expected input shapes for each model type
    EXPECTED_SHAPES = {
        'threat_detector': 10,  # 10 features for threat detection
        'attack_classifier': 42  # 42 features for attack classification
    }

    def __init__(self):
        """Initialize the model validator."""
        self.keras_available = False
        self.tensorflow_available = False

        # Try to import TensorFlow/Keras for .h5 support
        try:
            import tensorflow as tf
            from tensorflow import keras
            self.keras = keras
            self.tf = tf
            self.keras_available = True
            self.tensorflow_available = True
        except ImportError:
            pass

    def validate_model(
        self,
        file_path: str,
        model_type: str,
        file_format: str,
        profile_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate an uploaded model file.

        Args:
            file_path: Path to the uploaded model file
            model_type: Type of model ('threat_detector' or 'attack_classifier')
            file_format: File extension ('.pkl', '.joblib', or '.h5')
            profile_config: Optional model profile with expected_features and class_labels

        Returns:
            Dictionary with validation results including:
            - is_valid: bool
            - error_message: str (if validation failed)
            - model_metadata: dict (architecture info)
            - test_prediction: dict (sample prediction results)
            - profile_config: dict (feature and class configuration)

        Raises:
            ModelValidationError: If validation fails
        """
        # Use default shapes if no profile provided (backward compatibility)
        if profile_config is None:
            expected_features = self.EXPECTED_SHAPES.get(model_type, 42)
            expected_classes = 14 if model_type == 'attack_classifier' else 2
            profile_config = {
                'expected_features': [f'feature_{i}' for i in range(expected_features)],
                'class_labels': [f'class_{i}' for i in range(expected_classes)]
            }

        validation_result = {
            'is_valid': False,
            'error_message': None,
            'model_metadata': {},
            'test_prediction': None,
            'profile_config': profile_config
        }

        try:
            # Step 1: Validate file format
            self._validate_file_format(file_path, file_format)

            # Step 2: Load the model
            model = self._load_model(file_path, file_format)

            # Step 3: Validate model architecture
            metadata = self._validate_architecture(model, model_type, file_format, profile_config)
            validation_result['model_metadata'] = metadata

            # Step 4: Run test prediction
            test_result = self._test_prediction(model, model_type, file_format, profile_config)
            validation_result['test_prediction'] = test_result

            # All validations passed
            validation_result['is_valid'] = True

        except ModelValidationError as e:
            validation_result['error_message'] = str(e)
            validation_result['is_valid'] = False
        except Exception as e:
            validation_result['error_message'] = f"Unexpected error during validation: {str(e)}"
            validation_result['is_valid'] = False

        return validation_result

    def _validate_file_format(self, file_path: str, file_format: str) -> None:
        """Validate that file exists and has correct extension."""
        if not os.path.exists(file_path):
            raise ModelValidationError(f"Model file not found: {file_path}")

        if not file_path.endswith(file_format):
            raise ModelValidationError(
                f"File extension mismatch. Expected {file_format}, got {os.path.splitext(file_path)[1]}"
            )

        # Check file size (limit to 500MB)
        file_size = os.path.getsize(file_path)
        if file_size > 500 * 1024 * 1024:
            raise ModelValidationError(
                f"Model file too large: {file_size / (1024*1024):.2f}MB. Maximum allowed: 500MB"
            )

        # Validate format is supported
        if file_format not in ['.pkl', '.joblib', '.h5']:
            raise ModelValidationError(f"Unsupported file format: {file_format}")

        # Check if .h5 is supported
        if file_format == '.h5' and not self.keras_available:
            raise ModelValidationError(
                "TensorFlow/Keras not installed. Cannot load .h5 models. "
                "Please install tensorflow to support .h5 models."
            )

    def _load_model(self, file_path: str, file_format: str) -> Any:
        """
        Load the model from file based on format.

        For .joblib/.pkl files, detects pipeline bundle format from the ml_models
        package and uses the appropriate pipeline loader. This handles the
        PreprocessArtifacts class deserialization issue.
        """
        try:
            if file_format in ['.pkl', '.joblib']:
                return self._load_pkl_or_joblib(file_path)
            elif file_format == '.h5':
                model = self.keras.models.load_model(file_path)
                return model
            else:
                raise ModelValidationError(f"Unsupported format: {file_format}")

        except ModelValidationError:
            raise
        except Exception as e:
            raise ModelValidationError(f"Failed to load model: {str(e)}")

    def _load_pkl_or_joblib(self, file_path: str) -> Any:
        """
        Load a .pkl or .joblib file, handling pipeline bundle formats.

        Tries in order:
        1. ThreatDetectionPipeline.load_from_bundle (for threat detector bundles)
        2. AttackClassificationPipeline.load_from_bundle (for attack classifier bundles)
        3. Plain joblib.load (for raw sklearn models)
        """
        # Try attack classifier pipeline first (no TensorFlow needed)
        try:
            from ml_models import AttackClassificationPipeline
            pipeline = AttackClassificationPipeline.load_from_bundle(file_path)
            logger.info("Loaded as AttackClassificationPipeline bundle")
            return pipeline
        except Exception:
            pass

        # Try threat detection pipeline (requires TensorFlow)
        try:
            from ml_models import ThreatDetectionPipeline
            pipeline = ThreatDetectionPipeline.load_from_bundle(file_path)
            logger.info("Loaded as ThreatDetectionPipeline bundle")
            return pipeline
        except ImportError:
            # TensorFlow not available — only raise if the file is actually a threat
            # bundle. Otherwise fall through to the plain joblib path below.
            logger.debug("ThreatDetectionPipeline unavailable (no TensorFlow), skipping")
        except Exception as e:
            # Check if the error is related to PreprocessArtifacts (TF model without TF)
            if 'PreprocessArtifacts' in str(e):
                raise ModelValidationError(
                    "This model is a ThreatDetectionPipeline bundle containing "
                    "PreprocessArtifacts which requires TensorFlow. "
                    "Install TensorFlow to support this model format."
                )
            pass

        # Fall back to plain joblib load
        try:
            model = joblib.load(file_path)
            return model
        except Exception as e:
            raise ModelValidationError(f"Failed to load model: {str(e)}")

    def _is_pipeline(self, model: Any) -> bool:
        """Check if the model is a pipeline object from the ml_models package."""
        type_name = type(model).__name__
        return type_name in ('ThreatDetectionPipeline', 'AttackClassificationPipeline')

    def _validate_architecture(
        self,
        model: Any,
        model_type: str,
        file_format: str,
        profile_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that model architecture matches expected input/output shapes."""
        expected_features = len(profile_config.get('expected_features', []))
        expected_classes = len(profile_config.get('class_labels', []))

        if expected_features == 0:
            raise ModelValidationError("Profile configuration must specify expected_features")

        metadata = {
            'model_type': model_type,
            'expected_input_features': int(expected_features),
            'expected_output_classes': int(expected_classes)
        }

        try:
            if self._is_pipeline(model):
                # Pipeline from ml_models package — has internal preprocessing
                metadata['model_format'] = 'pipeline_bundle'
                if hasattr(model, 'artifacts') and model.artifacts is not None:
                    if hasattr(model.artifacts, 'selected_features'):
                        actual = len(model.artifacts.selected_features)
                        metadata['actual_input_features'] = int(actual)
                    elif hasattr(model.artifacts, 'feature_columns'):
                        actual = len(model.artifacts.feature_columns)
                        metadata['actual_input_features'] = int(actual)
                    else:
                        metadata['actual_input_features'] = 'unknown (pipeline with custom artifacts)'
                else:
                    metadata['actual_input_features'] = 'unknown (pipeline without artifacts)'

                # Check for inner model metadata
                if hasattr(model, 'model') and hasattr(model.model, 'classes_'):
                    metadata['num_classes'] = int(len(model.model.classes_))
                elif hasattr(model, 'model_ann'):
                    metadata['model_format'] = 'ensemble_pipeline_bundle'

            elif file_format == '.h5':
                # Keras model - check input shape
                input_shape = model.input_shape
                if isinstance(input_shape, list):
                    input_shape = input_shape[0]  # Handle multiple inputs

                # Extract feature count (last dimension)
                actual_features = input_shape[-1] if len(input_shape) > 1 else input_shape[0]
                metadata['actual_input_features'] = int(actual_features)
                metadata['input_shape'] = list(input_shape)
                metadata['output_shape'] = list(model.output_shape)

                if actual_features != expected_features:
                    raise ModelValidationError(
                        f"Input shape mismatch for {model_type}. "
                        f"Expected {expected_features} features, got {actual_features}"
                    )

            else:
                # sklearn model - try to get feature count from n_features_in_
                if hasattr(model, 'n_features_in_'):
                    actual_features = model.n_features_in_
                    metadata['actual_input_features'] = int(actual_features)

                    if actual_features != expected_features:
                        raise ModelValidationError(
                            f"Feature count mismatch for {model_type}. "
                            f"Expected {expected_features} features, got {actual_features}"
                        )
                else:
                    # Model doesn't expose feature count, will validate during test prediction
                    metadata['actual_input_features'] = 'unknown (will validate during test prediction)'

            # Get additional metadata for raw sklearn models
            if hasattr(model, 'classes_'):
                metadata['num_classes'] = int(len(model.classes_))
                metadata['classes'] = [c.item() if hasattr(c, "item") else c for c in model.classes_]

        except ModelValidationError:
            raise
        except Exception as e:
            raise ModelValidationError(f"Architecture validation failed: {str(e)}")

        return metadata

    def _test_prediction(
        self,
        model: Any,
        model_type: str,
        file_format: str,
        profile_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a test prediction to ensure model works correctly."""
        feature_names = profile_config.get('expected_features', [])
        num_features = len(feature_names)
        if num_features == 0:
            raise ModelValidationError("Cannot generate test data: no expected_features in profile")

        try:
            # Pipeline objects expect DataFrames and handle their own preprocessing
            if self._is_pipeline(model):
                return self._test_pipeline_prediction(model, model_type, feature_names)

            # Generate random test data as numpy array
            test_data = np.random.randn(1, num_features).astype(np.float32)

            if file_format == '.h5':
                # Keras model - use predict()
                prediction = model.predict(test_data, verbose=0)

                # Convert to appropriate format
                if model_type == 'threat_detector':
                    # Binary classification - expect probability score
                    score = float(prediction[0][0]) if len(prediction[0]) == 1 else float(prediction[0][1])
                    result = {
                        'prediction_type': 'binary_classification',
                        'score': score,
                        'is_attack': score > 0.5,
                        'raw_output_shape': list(prediction.shape)
                    }
                else:  # attack_classifier
                    # Multi-class classification
                    predicted_class = int(np.argmax(prediction[0]))
                    confidence = float(np.max(prediction[0]))
                    result = {
                        'prediction_type': 'multi_class_classification',
                        'predicted_class': predicted_class,
                        'confidence': confidence,
                        'raw_output_shape': list(prediction.shape)
                    }

            else:
                # sklearn model - use predict() and predict_proba() if available
                prediction = model.predict(test_data)

                result = {
                    'prediction_type': 'sklearn_model',
                    'predicted_value': int(prediction[0]) if isinstance(prediction[0], (np.integer, int)) else float(prediction[0])
                }

                # Try to get probabilities
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(test_data)
                    result['probabilities'] = probabilities[0].tolist()
                    result['confidence'] = float(np.max(probabilities[0]))

            return result

        except ModelValidationError:
            raise
        except Exception as e:
            raise ModelValidationError(f"Test prediction failed: {str(e)}")

    def _test_pipeline_prediction(
        self,
        pipeline: Any,
        model_type: str,
        feature_names: list
    ) -> Dict[str, Any]:
        """
        Run a test prediction on a pipeline bundle from the ml_models package.
        Pipelines expect DataFrames and handle their own preprocessing internally.
        """
        type_name = type(pipeline).__name__

        if type_name == 'ThreatDetectionPipeline':
            # Use the pipeline's own selected features for test data
            if pipeline.artifacts and hasattr(pipeline.artifacts, 'selected_features'):
                test_features = list(pipeline.artifacts.selected_features)
            else:
                test_features = feature_names
            test_row = {name: np.random.uniform(0, 100) for name in test_features}
            test_df = pd.DataFrame([test_row])

            preds, prob_ensemble, prob_ann = pipeline.predict(test_df)
            return {
                'prediction_type': 'threat_detection_pipeline',
                'predicted_class': int(preds[0]),
                'ensemble_probability': float(prob_ensemble[0]),
                'ann_probability': float(prob_ann[0]),
                'is_attack': bool(preds[0]),
            }

        elif type_name == 'AttackClassificationPipeline':
            # Use the pipeline's own feature columns for test data
            if pipeline.artifacts and hasattr(pipeline.artifacts, 'feature_columns'):
                test_features = list(pipeline.artifacts.feature_columns)
            else:
                test_features = feature_names
            test_row = {name: np.random.uniform(0, 100) for name in test_features}
            test_df = pd.DataFrame([test_row])

            predicted_encoded, confidence, predicted_labels = pipeline.predict(test_df)
            return {
                'prediction_type': 'attack_classification_pipeline',
                'predicted_class': int(predicted_encoded[0]),
                'predicted_label': str(predicted_labels[0]),
                'confidence': float(confidence[0]),
            }

        else:
            raise ModelValidationError(f"Unknown pipeline type: {type_name}")

    @staticmethod
    def get_supported_formats() -> list:
        """Return list of supported model formats."""
        return ['.pkl', '.joblib', '.h5']

    @staticmethod
    def get_supported_model_types() -> list:
        """Return list of supported model types."""
        return ['threat_detector', 'attack_classifier']
