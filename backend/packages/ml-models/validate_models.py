#!/usr/bin/env python3
"""
Validate trained ML models for backend integration.

Tests:
1. Bundle structure (all required components)
2. Profile JSON exists and has correct format
3. Test prediction runs without errors
4. Output is valid (class labels match expected)
"""

import json
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any
from tensorflow.keras.layers import LSTM, BatchNormalization, Dense, Dropout, ReLU
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam


# Define PreprocessArtifacts to match threat_classification.py
@dataclass
class PreprocessArtifacts:
    """Container for preprocessing artifacts."""
    encoders: Dict[str, Any]
    selected_features: list
    scaler: Any


def _build_ann(input_dim: int) -> Sequential:
    """Build ANN model matching threat_classification.py architecture."""
    model = Sequential([
        Dense(128, input_dim=input_dim),
        ReLU(),
        BatchNormalization(),
        Dense(128),
        ReLU(),
        BatchNormalization(),
        Dropout(0.2),
        Dense(64),
        ReLU(),
        BatchNormalization(),
        Dropout(0.2),
        Dense(32),
        ReLU(),
        BatchNormalization(),
        Dropout(0.2),
        Dense(1, activation='sigmoid'),
    ])
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss=BinaryCrossentropy(),
        metrics=['accuracy'],
    )
    return model


def _build_lstm(input_shape: tuple[int, int]) -> Sequential:
    """Build LSTM model matching threat_classification.py architecture."""
    model = Sequential([
        LSTM(256, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(128, return_sequences=True),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(1, activation='sigmoid'),
    ])
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss=BinaryCrossentropy(),
        metrics=['accuracy'],
    )
    return model


def validate_threat_detector(model_path: Path, profile_path: Path) -> dict:
    """Validate threat detection model bundle."""
    print("\n" + "="*70)
    print("VALIDATING THREAT DETECTION MODEL")
    print("="*70)

    results = {
        "model_name": "threat_detector_ensemble",
        "model_path": str(model_path),
        "tests": {}
    }

    # Test 1: Load bundle
    print("\n[Test 1] Loading model bundle...")
    try:
        bundle = joblib.load(model_path)
        results["tests"]["bundle_load"] = {"status": "PASS", "message": "Bundle loaded successfully"}
        print("✓ Bundle loaded successfully")
    except Exception as e:
        results["tests"]["bundle_load"] = {"status": "FAIL", "message": str(e)}
        print(f"✗ Failed to load bundle: {e}")
        return results

    # Test 2: Verify bundle structure
    print("\n[Test 2] Verifying bundle structure...")
    required_keys = ['artifacts', 'ann_weights', 'lstm_weights', 'ann_config',
                     'lstm_config', 'n_features', 'random_state']
    missing_keys = [k for k in required_keys if k not in bundle]

    if missing_keys:
        results["tests"]["bundle_structure"] = {
            "status": "FAIL",
            "message": f"Missing keys: {missing_keys}"
        }
        print(f"✗ Missing keys in bundle: {missing_keys}")
    else:
        results["tests"]["bundle_structure"] = {"status": "PASS", "message": "All required keys present"}
        print("✓ All required keys present")
        print(f"  - n_features: {bundle['n_features']}")
        print(f"  - random_state: {bundle['random_state']}")

    # Test 3: Check artifacts
    print("\n[Test 3] Checking preprocessing artifacts...")
    if 'artifacts' in bundle:
        artifacts = bundle['artifacts']
        # Check if it's a PreprocessArtifacts dataclass
        if hasattr(artifacts, '__dataclass_fields__'):
            artifact_attrs = ['encoders', 'selected_features', 'scaler']
            missing_artifacts = [k for k in artifact_attrs if not hasattr(artifacts, k)]

            if missing_artifacts:
                results["tests"]["artifacts"] = {
                    "status": "FAIL",
                    "message": f"Missing artifacts: {missing_artifacts}"
                }
                print(f"✗ Missing artifacts: {missing_artifacts}")
            else:
                results["tests"]["artifacts"] = {"status": "PASS", "message": "All artifacts present"}
                print("✓ All artifacts present")
                print(f"  - Selected features ({len(artifacts.selected_features)}):")
                for feat in artifacts.selected_features:
                    print(f"    • {feat}")
        else:
            # It's a dict
            artifact_keys = ['encoders', 'selected_features', 'scaler']
            missing_artifacts = [k for k in artifact_keys if k not in artifacts]

            if missing_artifacts:
                results["tests"]["artifacts"] = {
                    "status": "FAIL",
                    "message": f"Missing artifacts: {missing_artifacts}"
                }
                print(f"✗ Missing artifacts: {missing_artifacts}")
            else:
                results["tests"]["artifacts"] = {"status": "PASS", "message": "All artifacts present"}
                print("✓ All artifacts present")
                print(f"  - Selected features ({len(artifacts['selected_features'])}):")
                for feat in artifacts['selected_features']:
                    print(f"    • {feat}")
    else:
        results["tests"]["artifacts"] = {"status": "FAIL", "message": "No artifacts in bundle"}
        print("✗ No artifacts in bundle")

    # Test 4: Check profile JSON
    print("\n[Test 4] Checking profile JSON...")
    if not profile_path.exists():
        results["tests"]["profile_json"] = {
            "status": "FAIL",
            "message": f"Profile not found at {profile_path}"
        }
        print(f"✗ Profile not found at {profile_path}")
    else:
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)

            required_profile_keys = ['expected_features', 'class_labels',
                                    'preprocessing_notes', 'preprocessing_pipeline']
            missing_profile_keys = [k for k in required_profile_keys if k not in profile]

            if missing_profile_keys:
                results["tests"]["profile_json"] = {
                    "status": "FAIL",
                    "message": f"Missing profile keys: {missing_profile_keys}"
                }
                print(f"✗ Missing profile keys: {missing_profile_keys}")
            else:
                results["tests"]["profile_json"] = {
                    "status": "PASS",
                    "message": "Profile valid",
                    "details": profile
                }
                print("✓ Profile JSON valid")
                print(f"  - Expected features: {len(profile['expected_features'])}")
                print(f"  - Class labels: {profile['class_labels']}")
        except Exception as e:
            results["tests"]["profile_json"] = {"status": "FAIL", "message": str(e)}
            print(f"✗ Failed to load profile: {e}")

    # Test 5: Test prediction
    print("\n[Test 5] Running test prediction...")
    try:
        import tempfile
        import os
        from tensorflow.keras.models import load_model

        # Load Keras models from H5 bytes
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write ANN weights to temp file
            ann_path = os.path.join(tmpdir, "ann_weights.h5")
            with open(ann_path, "wb") as f:
                f.write(bundle['ann_weights'])
            ann_model = load_model(ann_path)

            # Write LSTM weights to temp file
            lstm_path = os.path.join(tmpdir, "lstm_weights.h5")
            with open(lstm_path, "wb") as f:
                f.write(bundle['lstm_weights'])
            lstm_model = load_model(lstm_path)

        # Create sample data using selected features
        artifacts = bundle['artifacts']
        # Handle both dataclass and dict
        if hasattr(artifacts, '__dataclass_fields__'):
            selected_features = artifacts.selected_features
            scaler = artifacts.scaler
            encoders = artifacts.encoders
        else:
            selected_features = artifacts['selected_features']
            scaler = artifacts['scaler']
            encoders = artifacts['encoders']

        sample_data = {}

        # Generate realistic sample values
        sample_values = {
            'protocol_type': 'tcp',
            'service': 'http',
            'flag': 'SF',
            'src_bytes': 1000,
            'dst_bytes': 500,
            'count': 5,
            'same_srv_rate': 0.8,
            'diff_srv_rate': 0.2,
            'dst_host_srv_count': 20,
            'dst_host_same_srv_rate': 0.8
        }

        for feat in selected_features:
            sample_data[feat] = [sample_values.get(feat, 0)]

        df = pd.DataFrame(sample_data)

        # Encode categorical features
        for col, encoder in encoders.items():
            if col in df.columns:
                try:
                    df[col] = encoder.transform(df[col])
                except ValueError as e:
                    # Handle unseen labels - use mapping approach
                    label_mapping = {label: idx for idx, label in enumerate(encoder.classes_)}
                    df[col] = df[col].astype(str).map(label_mapping).fillna(0).astype(int)

        # Scale features
        X_scaled = scaler.transform(df)

        # Make predictions
        ann_pred = ann_model.predict(X_scaled, verbose=0)
        # Reshape for LSTM (note: the original uses shape (n, 1, features) but let's check)
        X_lstm = X_scaled.reshape((X_scaled.shape[0], X_scaled.shape[1], 1))
        lstm_pred = lstm_model.predict(X_lstm, verbose=0)

        # Ensemble (average)
        ensemble_pred = (ann_pred + lstm_pred) / 2
        prediction = (ensemble_pred > 0.5).astype(int)[0][0]

        class_labels = ['Normal', 'Attack']
        predicted_class = class_labels[prediction]

        results["tests"]["prediction"] = {
            "status": "PASS",
            "message": "Prediction successful",
            "prediction": predicted_class,
            "confidence": float(ensemble_pred[0][0])
        }
        print(f"✓ Prediction successful")
        print(f"  - Predicted class: {predicted_class}")
        print(f"  - Confidence: {ensemble_pred[0][0]:.4f}")

    except Exception as e:
        results["tests"]["prediction"] = {"status": "FAIL", "message": str(e)}
        print(f"✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()

    return results


def validate_attack_classifier(model_path: Path, profile_path: Path) -> dict:
    """Validate attack classification model bundle."""
    print("\n" + "="*70)
    print("VALIDATING ATTACK CLASSIFICATION MODEL")
    print("="*70)

    results = {
        "model_name": "attack_classifier",
        "model_path": str(model_path),
        "tests": {}
    }

    # Test 1: Load bundle
    print("\n[Test 1] Loading model bundle...")
    try:
        bundle = joblib.load(model_path)
        results["tests"]["bundle_load"] = {"status": "PASS", "message": "Bundle loaded successfully"}
        print("✓ Bundle loaded successfully")
    except Exception as e:
        results["tests"]["bundle_load"] = {"status": "FAIL", "message": str(e)}
        print(f"✗ Failed to load bundle: {e}")
        return results

    # Test 2: Verify bundle structure
    print("\n[Test 2] Verifying bundle structure...")
    required_keys = ['artifacts', 'model', 'correlation_threshold', 'max_depth', 'random_state']
    missing_keys = [k for k in required_keys if k not in bundle]

    if missing_keys:
        results["tests"]["bundle_structure"] = {
            "status": "FAIL",
            "message": f"Missing keys: {missing_keys}"
        }
        print(f"✗ Missing keys in bundle: {missing_keys}")
    else:
        results["tests"]["bundle_structure"] = {"status": "PASS", "message": "All required keys present"}
        print("✓ All required keys present")
        print(f"  - correlation_threshold: {bundle['correlation_threshold']}")
        print(f"  - max_depth: {bundle['max_depth']}")
        print(f"  - random_state: {bundle['random_state']}")

    # Test 3: Check artifacts
    print("\n[Test 3] Checking preprocessing artifacts...")
    if 'artifacts' in bundle:
        artifacts = bundle['artifacts']
        artifact_keys = ['label_encoder', 'scaler', 'feature_columns', 'removed_columns', 'class_mapping']
        missing_artifacts = [k for k in artifact_keys if k not in artifacts]

        if missing_artifacts:
            results["tests"]["artifacts"] = {
                "status": "FAIL",
                "message": f"Missing artifacts: {missing_artifacts}"
            }
            print(f"✗ Missing artifacts: {missing_artifacts}")
        else:
            results["tests"]["artifacts"] = {"status": "PASS", "message": "All artifacts present"}
            print("✓ All artifacts present")
            print(f"  - Feature columns ({len(artifacts['feature_columns'])})")
            print(f"  - Removed columns ({len(artifacts['removed_columns'])}):")
            for col in list(artifacts['removed_columns'])[:5]:
                print(f"    • {col}")
            if len(artifacts['removed_columns']) > 5:
                print(f"    ... and {len(artifacts['removed_columns']) - 5} more")
            print(f"  - Classes ({len(artifacts['class_mapping'])}):")
            for i, cls in enumerate(artifacts['class_mapping'].values()):
                print(f"    {i}. {cls}")
    else:
        results["tests"]["artifacts"] = {"status": "FAIL", "message": "No artifacts in bundle"}
        print("✗ No artifacts in bundle")

    # Test 4: Check profile JSON
    print("\n[Test 4] Checking profile JSON...")
    if not profile_path.exists():
        results["tests"]["profile_json"] = {
            "status": "FAIL",
            "message": f"Profile not found at {profile_path}"
        }
        print(f"✗ Profile not found at {profile_path}")
    else:
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)

            required_profile_keys = ['expected_features', 'class_labels',
                                    'preprocessing_notes', 'preprocessing_pipeline']
            missing_profile_keys = [k for k in required_profile_keys if k not in profile]

            if missing_profile_keys:
                results["tests"]["profile_json"] = {
                    "status": "FAIL",
                    "message": f"Missing profile keys: {missing_profile_keys}"
                }
                print(f"✗ Missing profile keys: {missing_profile_keys}")
            else:
                results["tests"]["profile_json"] = {
                    "status": "PASS",
                    "message": "Profile valid",
                    "details": profile
                }
                print("✓ Profile JSON valid")
                print(f"  - Expected features: {len(profile['expected_features'])}")
                print(f"  - Class labels: {len(profile['class_labels'])} classes")
        except Exception as e:
            results["tests"]["profile_json"] = {"status": "FAIL", "message": str(e)}
            print(f"✗ Failed to load profile: {e}")

    # Test 5: Test prediction
    print("\n[Test 5] Running test prediction...")
    try:
        # Create sample data using feature columns
        feature_columns = bundle['artifacts']['feature_columns']

        # Generate sample values for each feature type
        sample_data = {}
        for feat in feature_columns:
            if 'bytes' in feat.lower():
                sample_data[feat] = [1000]
            elif 'count' in feat.lower() or 'rate' in feat.lower():
                sample_data[feat] = [5]
            elif 'time' in feat.lower():
                sample_data[feat] = [0.5]
            else:
                sample_data[feat] = [1]

        df = pd.DataFrame(sample_data)

        # Preprocess
        scaler = bundle['artifacts']['scaler']
        X_scaled = scaler.transform(df)

        # Make prediction
        model = bundle['model']
        prediction_idx = model.predict(X_scaled)[0]

        # Get class label
        class_mapping = bundle['artifacts']['class_mapping']
        predicted_class = class_mapping.get(str(prediction_idx), f"Class_{prediction_idx}")

        # Get probabilities
        probabilities = model.predict_proba(X_scaled)[0]
        confidence = float(max(probabilities))

        results["tests"]["prediction"] = {
            "status": "PASS",
            "message": "Prediction successful",
            "prediction": predicted_class,
            "confidence": confidence
        }
        print(f"✓ Prediction successful")
        print(f"  - Predicted class: {predicted_class}")
        print(f"  - Confidence: {confidence:.4f}")

    except Exception as e:
        results["tests"]["prediction"] = {"status": "FAIL", "message": str(e)}
        print(f"✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()

    return results


def main():
    """Main validation function."""
    research_dir = Path("/mnt/Code/code/freelance/2511-AI-heal-network-sec/ui/research")

    # Model paths
    threat_model_path = research_dir / "threat_detector_ensemble.joblib"
    threat_profile_path = research_dir / "threat_detector_profile.json"

    attack_model_path = research_dir / "attack_classifier.joblib"
    attack_profile_path = research_dir / "attack_classifier_profile.json"

    print("="*70)
    print("ML MODEL VALIDATION FOR BACKEND INTEGRATION")
    print("="*70)

    # Validate threat detector
    threat_results = validate_threat_detector(threat_model_path, threat_profile_path)

    # Validate attack classifier
    attack_results = validate_attack_classifier(attack_model_path, attack_profile_path)

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    # Calculate pass rates
    threat_passes = sum(1 for t in threat_results["tests"].values() if t["status"] == "PASS")
    threat_total = len(threat_results["tests"])

    attack_passes = sum(1 for t in attack_results["tests"].values() if t["status"] == "PASS")
    attack_total = len(attack_results["tests"])

    print(f"\nThreat Detector: {threat_passes}/{threat_total} tests passed")
    print(f"Attack Classifier: {attack_passes}/{attack_total} tests passed")

    # Determine overall status
    threat_pass = threat_passes == threat_total
    attack_pass = attack_passes == attack_total

    if threat_pass and attack_pass:
        print("\n✓ ALL MODELS PASSED VALIDATION - READY FOR BACKEND INTEGRATION")
        return 0
    else:
        print("\n✗ SOME MODELS FAILED VALIDATION - REVIEW ISSUES ABOVE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
