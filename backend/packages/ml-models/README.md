# ML Models - Training & Deployment Guide

## Overview

Two ML pipelines for the AI Threat Detection system:

| Model | Features | Task | Algorithm | TensorFlow Required |
|-------|----------|------|-----------|-------------------|
| **Threat Detector** | 10 (from RFE selection) | Binary classification (Normal/Attack) | ANN + LSTM ensemble | Yes |
| **Attack Classifier** | 41 (after correlation removal) | Multi-class classification (14 attack types) | DecisionTree | No |

## Training

### Attack Classifier

```bash
cd backend/packages/ml-models

python -m ml_models.attack_classification \
  --train_csvs data/attack_classifcation.csv \
  --max_depth 10 \
  --correlation_threshold 0.85
```

Options:
- `--train_csvs` — one or more CSV files with a `Label` column
- `--max_depth` — decision tree max depth (default: 10)
- `--correlation_threshold` — remove features with correlation above this (default: 0.85)
- `--random_state` — random seed (default: 42)
- `--predict_csv` — optional CSV for inference after training
- `--output_preds` — where to save predictions

Outputs:
- `attack_classifier.joblib` — model bundle
- `attack_classifier_profile.json` — feature profile for backend integration

### Threat Detector

Requires TensorFlow (`pip install tensorflow-cpu` on Linux x86, or `pip install tensorflow` on macOS with Apple Silicon).

```bash
python -m ml_models.threat_classification \
  --train_csv data/threat_classification.csv \
  --n_features 10
```

Options:
- `--train_csv` — CSV file with a `class` column (normal/attack labels)
- `--n_features` — number of features to select via RFE (default: 10)
- `--random_state` — random seed (default: 42)
- `--predict_csv` — optional CSV for inference after training
- `--output_preds` — where to save predictions

Outputs:
- `threat_detector_ensemble.joblib` — ANN+LSTM ensemble bundle
- `threat_detector_profile.json` — feature profile
- `trained_pipeline/` — individual files (artifacts.pkl, model_ann.h5, model_lstm.h5)

## Training Data Format

### Threat Detection CSV

Must include a `class` column with labels (e.g., `normal`, `attack`). All other columns are treated as features. The pipeline performs:

1. Label encoding of categorical columns (protocol_type, service, flag)
2. RFE feature selection (selects top N features)
3. StandardScaler normalization

Example columns: `duration, protocol_type, service, flag, src_bytes, dst_bytes, land, wrong_fragment, ..., class`

### Attack Classification CSV

Must include a `Label` column with attack type names. Uses CICFlowMeter-style features (78 columns). The pipeline performs:

1. Column name stripping (whitespace)
2. Deduplication and NaN/inf removal
3. Label encoding of the target
4. Correlation-based feature removal (threshold=0.85)
5. RobustScaler normalization

Example labels: `BENIGN, DDoS, PortScan, DoS Hulk, FTP-Patator, SSH-Patator, Bot, Web Attack – Brute Force, Web Attack – XSS, Web Attack – Sql Injection, Infiltration, DoS slowloris, DoS Slowhttptest, DoS GoldenEye`

## Deployment

### Option 1: Copy to models directory

```bash
# After training, from packages/ml-models/:
cp attack_classifier.joblib ../../models/attack_classifier/attack_classifier_$(date +%Y%m%d).joblib
cp threat_detector_ensemble.joblib ../../models/threat_detector/threat_detector_$(date +%Y%m%d).joblib
```

The backend auto-detects the latest model file by modification time.

### Option 2: Upload through the UI

Navigate to `/en/models` and use the upload form. The backend validates the model before accepting it.

### Option 3: Upload via API

```bash
curl -X POST http://localhost:8000/api/v1/models/upload \
  -F "file=@attack_classifier.joblib" \
  -F "model_type=attack_classifier" \
  -F "description=My trained model"
```

After uploading, activate the model via the UI or API:
```bash
curl -X PUT http://localhost:8000/api/v1/models/{model_id}/activate
```

## Mock Fallback

When models or TensorFlow are not available, the backend falls back to mock predictions automatically. This keeps the system functional for development and testing. Check `model_version` in API responses — `mock_v1` indicates mock mode.

## Programmatic Usage

```python
from ml_models import AttackClassificationPipeline

# Train
pipeline = AttackClassificationPipeline(max_depth=10, correlation_threshold=0.85)
metrics = pipeline.train(train_df)

# Save
pipeline.save_as_bundle("attack_classifier.joblib")

# Load and predict
loaded = AttackClassificationPipeline.load_from_bundle("attack_classifier.joblib")
predicted_encoded, confidence, predicted_labels = loaded.predict(raw_df)
```

```python
from ml_models import ThreatDetectionPipeline  # requires tensorflow

# Train
pipeline = ThreatDetectionPipeline(n_features=10)
metrics = pipeline.train(train_df)

# Save
pipeline.save_as_bundle("threat_detector_ensemble.joblib")

# Load and predict
loaded = ThreatDetectionPipeline.load_from_bundle("threat_detector_ensemble.joblib")
preds, prob_ensemble, prob_ann = loaded.predict(raw_df)
```
