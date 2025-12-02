#!/usr/bin/env python3
"""
Train production ML models for threat detection and attack classification.
This script converts research code into production-ready models.
"""
import os
import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler, LabelEncoder
from sklearn.feature_selection import RFE
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Directories
RESEARCH_DIR = Path(__file__).parent.parent / "research"
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Ensure models directory exists
print(f"Models will be saved to: {MODELS_DIR}")


def train_threat_detector():
    """
    Train binary threat detection model (10 features).
    Based on backend/research/threat_detect/threat_detector.py
    """
    print("\n" + "="*80)
    print("TRAINING THREAT DETECTION MODEL (Binary Classification)")
    print("="*80)

    # Load demo data
    data_path = RESEARCH_DIR / "threat_detect" / "data_threat_detect_demo.csv"
    print(f"\nLoading data from: {data_path}")

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print("Creating synthetic training data...")
        df = create_synthetic_threat_data()
    else:
        df = pd.read_csv(data_path)

    print(f"Loaded {len(df)} samples")
    print(f"Columns: {list(df.columns)}")

    # Drop rows with NaN in 'class' column
    df = df.dropna(subset=['class'])

    # Encode class column (normal=0, anomaly=1)
    le_class = LabelEncoder()
    df['class'] = le_class.fit_transform(df['class'])
    print(f"\nClass distribution:\n{df['class'].value_counts()}")

    # Encode categorical features
    categorical_cols = df.select_dtypes(include=['object']).columns
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    # Drop num_outbound_cmds if exists
    if 'num_outbound_cmds' in df.columns:
        df = df.drop(['num_outbound_cmds'], axis=1)

    # Separate features and target
    X_full = df.drop('class', axis=1)
    y_full = df['class']

    print(f"\nPerforming feature selection (RFE to select 10 features)...")

    # Feature selection using RFE with RandomForest
    rfc = RandomForestClassifier(random_state=42, n_estimators=50)
    rfe = RFE(estimator=rfc, n_features_to_select=10)
    rfe.fit(X_full, y_full)

    selected_features = X_full.columns[rfe.get_support()].tolist()
    print(f"Selected features: {selected_features}")

    X_selected = X_full[selected_features]

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_selected)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_full, test_size=0.2, random_state=42
    )

    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # Train ensemble model (RandomForest)
    print("\nTraining RandomForest ensemble model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nTest Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))

    # Save model bundle
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = MODELS_DIR / f"threat_detector_{timestamp}.joblib"

    model_bundle = {
        'model': model,
        'scaler': scaler,
        'label_encoders': label_encoders,
        'selected_features': selected_features,
        'threshold': 0.5,
        'metadata': {
            'version': timestamp,
            'accuracy': float(accuracy),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test),
            'n_features': len(selected_features),
            'model_type': 'RandomForestClassifier',
            'created_at': datetime.now().isoformat()
        }
    }

    joblib.dump(model_bundle, model_path)
    print(f"\n✅ Model saved to: {model_path}")
    print(f"   Model size: {model_path.stat().st_size / 1024:.2f} KB")

    return model_path, accuracy


def train_attack_classifier():
    """
    Train multi-class attack classification model (42 features).
    Based on backend/research/attack_classification/classifier.py
    """
    print("\n" + "="*80)
    print("TRAINING ATTACK CLASSIFICATION MODEL (Multi-class)")
    print("="*80)

    # Load demo data
    data_path = RESEARCH_DIR / "attack_classification" / "demo_atk_class.csv"
    print(f"\nLoading data from: {data_path}")

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print("Creating synthetic training data...")
        df = create_synthetic_attack_data()
    else:
        df = pd.read_csv(data_path)

    print(f"Loaded {len(df)} samples")

    # Clean data
    df = df.dropna()
    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    # Encode label
    label_column = ' Label' if ' Label' in df.columns else 'Label'
    print(f"\nAttack types in data:\n{df[label_column].value_counts()}")

    le = LabelEncoder()
    df[label_column] = le.fit_transform(df[label_column])

    attack_types = {i: label for i, label in enumerate(le.classes_)}
    print(f"\nEncoded attack types: {attack_types}")

    # Separate features and target
    X = df.drop([label_column], axis=1)
    y = df[label_column]

    # Remove highly correlated features (correlation > 0.85)
    print(f"\nOriginal features: {X.shape[1]}")
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.85)]
    X = X.drop(to_drop, axis=1)
    print(f"After removing correlated features: {X.shape[1]}")

    selected_features = X.columns.tolist()

    # Scale features
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, shuffle=True
    )

    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # Train DecisionTree model
    print("\nTraining DecisionTree classifier...")
    model = DecisionTreeClassifier(
        criterion='entropy',
        max_depth=12,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nTest Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Save model bundle
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = MODELS_DIR / f"attack_classifier_{timestamp}.joblib"

    model_bundle = {
        'model': model,
        'scaler': scaler,
        'label_encoder': le,
        'selected_features': selected_features,
        'attack_types': attack_types,
        'metadata': {
            'version': timestamp,
            'accuracy': float(accuracy),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test),
            'n_features': len(selected_features),
            'n_classes': len(attack_types),
            'model_type': 'DecisionTreeClassifier',
            'created_at': datetime.now().isoformat()
        }
    }

    joblib.dump(model_bundle, model_path)
    print(f"\n✅ Model saved to: {model_path}")
    print(f"   Model size: {model_path.stat().st_size / 1024:.2f} KB")

    return model_path, accuracy


def create_synthetic_threat_data():
    """Create synthetic data for threat detection if demo file is missing."""
    print("Generating synthetic threat detection data...")
    np.random.seed(42)

    n_normal = 800
    n_attack = 200

    # Normal traffic patterns
    normal_data = {
        'service': np.random.choice(['http', 'ftp', 'smtp'], n_normal),
        'flag': np.random.choice(['SF', 'S0', 'REJ'], n_normal),
        'src_bytes': np.random.exponential(500, n_normal),
        'dst_bytes': np.random.exponential(1000, n_normal),
        'count': np.random.poisson(10, n_normal),
        'same_srv_rate': np.random.uniform(0.7, 1.0, n_normal),
        'diff_srv_rate': np.random.uniform(0, 0.3, n_normal),
        'dst_host_srv_count': np.random.poisson(20, n_normal),
        'dst_host_same_srv_rate': np.random.uniform(0.7, 1.0, n_normal),
        'dst_host_same_src_port_rate': np.random.uniform(0.5, 1.0, n_normal),
        'class': ['normal'] * n_normal
    }

    # Attack traffic patterns (anomalous)
    attack_data = {
        'service': np.random.choice(['private', 'http', 'other'], n_attack),
        'flag': np.random.choice(['S0', 'REJ', 'RSTO'], n_attack),
        'src_bytes': np.random.exponential(50, n_attack),
        'dst_bytes': np.random.exponential(100, n_attack),
        'count': np.random.poisson(100, n_attack),
        'same_srv_rate': np.random.uniform(0, 0.3, n_attack),
        'diff_srv_rate': np.random.uniform(0.5, 1.0, n_attack),
        'dst_host_srv_count': np.random.poisson(200, n_attack),
        'dst_host_same_srv_rate': np.random.uniform(0, 0.3, n_attack),
        'dst_host_same_src_port_rate': np.random.uniform(0, 0.3, n_attack),
        'class': ['anomaly'] * n_attack
    }

    df_normal = pd.DataFrame(normal_data)
    df_attack = pd.DataFrame(attack_data)
    df = pd.concat([df_normal, df_attack], ignore_index=True)

    return df.sample(frac=1, random_state=42).reset_index(drop=True)


def create_synthetic_attack_data():
    """Create synthetic data for attack classification if demo file is missing."""
    print("Generating synthetic attack classification data...")
    np.random.seed(42)

    attack_labels = [
        'BENIGN', 'DoS Hulk', 'DDoS', 'PortScan', 'FTP-Patator',
        'DoS slowloris', 'DoS Slowhttptest', 'SSH-Patator', 'DoS GoldenEye',
        'Web Attack – Brute Force', 'Bot', 'Web Attack – XSS',
        'Web Attack – Sql Injection', 'Infiltration'
    ]

    n_samples = 1000
    data = {}

    # Generate 42 features
    feature_names = [
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

    for feature in feature_names:
        data[feature] = np.random.randn(n_samples) * 1000

    data[' Label'] = np.random.choice(attack_labels, n_samples)

    return pd.DataFrame(data)


def main():
    """Main training function."""
    print("="*80)
    print("PRODUCTION ML MODEL TRAINING")
    print("="*80)
    print(f"Research directory: {RESEARCH_DIR}")
    print(f"Models directory: {MODELS_DIR}")

    results = {}

    try:
        # Train threat detector
        threat_model_path, threat_acc = train_threat_detector()
        results['threat_detector'] = {
            'path': threat_model_path,
            'accuracy': threat_acc
        }
    except Exception as e:
        print(f"\n❌ Error training threat detector: {e}")
        import traceback
        traceback.print_exc()

    try:
        # Train attack classifier
        attack_model_path, attack_acc = train_attack_classifier()
        results['attack_classifier'] = {
            'path': attack_model_path,
            'accuracy': attack_acc
        }
    except Exception as e:
        print(f"\n❌ Error training attack classifier: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)

    for model_name, info in results.items():
        print(f"\n{model_name}:")
        print(f"  Path: {info['path']}")
        print(f"  Accuracy: {info['accuracy']*100:.2f}%")

    print("\n✅ Training complete!")
    print(f"\nModels saved to: {MODELS_DIR}")
    print("\nNext steps:")
    print("1. Models will be auto-loaded by backend/app/models/ml_models.py")
    print("2. Restart the backend to load the new models")
    print("3. Check logs for 'Loaded real ... model' messages")


if __name__ == "__main__":
    main()
