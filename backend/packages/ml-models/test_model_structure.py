#!/usr/bin/env python3
"""Test script to inspect model bundle structures."""
import joblib
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Tuple
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler

# Define the PreprocessArtifacts classes before loading
@dataclass
class ThreatPreprocessArtifacts:
    """Container for threat detection preprocessing artifacts."""
    encoders: Dict[str, LabelEncoder]
    selected_features: Tuple[str, ...]
    scaler: StandardScaler

@dataclass
class AttackPreprocessArtifacts:
    """Container for attack classification preprocessing artifacts."""
    label_encoder: LabelEncoder
    scaler: RobustScaler
    feature_columns: Tuple[str, ...]
    removed_columns: Tuple[str, ...]
    class_mapping: Dict[int, str]

# Register the classes in the module namespace
import sys
sys.modules['__main__'].PreprocessArtifacts = ThreatPreprocessArtifacts

def main():
    print('=' * 60)
    print('THREAT DETECTOR MODEL STRUCTURE')
    print('=' * 60)

    bundle = joblib.load('threat_detector_ensemble.joblib')
    print(f'\nBundle keys: {list(bundle.keys())}')

    # Check artifacts
    if 'artifacts' in bundle:
        artifacts = bundle['artifacts']
        print(f'\nArtifacts type: {type(artifacts).__name__}')
        print(f'\nSelected features ({len(artifacts.selected_features)}):')
        for i, feat in enumerate(artifacts.selected_features, 1):
            print(f'  {i}. {feat}')

        print(f'\nEncoders keys: {list(artifacts.encoders.keys())}')
        print(f'Scaler type: {type(artifacts.scaler).__name__}')

    # Check models
    if 'ann_weights' in bundle:
        print(f'\nANN weights type: {type(bundle["ann_weights"]).__name__}')
        if isinstance(bundle['ann_weights'], bytes):
            print(f'  Size: {len(bundle["ann_weights"])} bytes')
        elif hasattr(bundle['ann_weights'], 'shape'):
            print(f'  Shape: {bundle["ann_weights"].shape}')

    if 'lstm_weights' in bundle:
        print(f'\nLSTM weights type: {type(bundle["lstm_weights"]).__name__}')
        if isinstance(bundle['lstm_weights'], bytes):
            print(f'  Size: {len(bundle["lstm_weights"])} bytes')
        elif hasattr(bundle['lstm_weights'], 'shape'):
            print(f'  Shape: {bundle["lstm_weights"].shape}')

    print('\n' + '=' * 60)
    print('ATTACK CLASSIFIER MODEL STRUCTURE')
    print('=' * 60)

    bundle2 = joblib.load('attack_classifier.joblib')
    print(f'\nBundle keys: {list(bundle2.keys())}')

    # Check artifacts
    if 'artifacts' in bundle2:
        artifacts2 = bundle2['artifacts']
        print(f'\nArtifacts type: {type(artifacts2).__name__}')

        # Handle both dict and dataclass
        if isinstance(artifacts2, dict):
            feature_cols = artifacts2.get('feature_columns', [])
            removed_cols = artifacts2.get('removed_columns', [])
            class_map = artifacts2.get('class_mapping', {})
            scaler = artifacts2.get('scaler')
            label_enc = artifacts2.get('label_encoder')
        else:
            feature_cols = artifacts2.feature_columns
            removed_cols = artifacts2.removed_columns
            class_map = artifacts2.class_mapping
            scaler = artifacts2.scaler
            label_enc = artifacts2.label_encoder

        print(f'\nFeature columns ({len(feature_cols)}):')
        for i, feat in enumerate(feature_cols[:10], 1):
            print(f'  {i}. {feat}')
        if len(feature_cols) > 10:
            print(f'  ... and {len(feature_cols) - 10} more')

        print(f'\nRemoved columns ({len(removed_cols)}):')
        print(f'  First 5: {list(removed_cols[:5])}')

        print(f'\nClass mapping:')
        for idx, label in class_map.items():
            print(f'  {idx}: {label}')

        print(f'\nScaler type: {type(scaler).__name__}')
        print(f'Label encoder type: {type(label_enc).__name__}')

    # Check model
    if 'model' in bundle2:
        print(f'\nModel type: {type(bundle2["model"]).__name__}')
        print(f'Model classes: {bundle2["model"].classes_ if hasattr(bundle2["model"], "classes_") else "N/A"}')

if __name__ == '__main__':
    main()
