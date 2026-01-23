---
name: ml-train
description: Train ML models for threat detection (binary) and attack classification (multi-class). Use when training, exporting models, or generating CSV examples.
allowed-tools: Bash, Read, Write, Edit, Glob
---

# ML Model Training

## Training Commands

### Threat Detection (Binary: Normal/Attack)
```bash
uv run threat_classification.py --train_csv data/train/threat.csv --n_features 10
```

### Attack Classification (14 attack types)
```bash
uv run attack_classification.py --train_csvs data/train/*.csv --max_depth 10
```

## Model Types

| Model Type | Purpose | Features | Architecture |
|------------|---------|----------|--------------|
| Threat Detection | Binary classification (Normal/Attack) | 10 features (RFE selected) | ANN + LSTM Ensemble |
| Attack Classification | Multi-class (14 attack types) | 42 features (correlation-filtered) | Decision Tree |

## Outputs
- Model bundle: `.joblib` file with model + preprocessing artifacts
- Profile JSON: Expected features, class labels, preprocessing notes
- CSV examples: Sample data matching expected features

## Environment
Always use `uv run` before Python commands to ensure correct environment.

## Training Parameters

### Threat Detection
- `--train_csv`: Path to training CSV with `class` column (0=Normal, 1=Attack)
- `--n_features`: Number of features to select via RFE (default: 10)
- `--random_state`: Random seed for reproducibility (default: 42)

### Attack Classification
- `--train_csvs`: Path(s) to training CSVs with `Label` column
- `--correlation_threshold`: Threshold for removing correlated features (default: 0.85)
- `--max_depth`: Max depth of decision tree (default: 10)
- `--random_state`: Random seed for reproducibility (default: 42)

## Expected Data Format

### Threat Detection CSV
- Must have `class` column with values 0 (Normal) or 1 (Attack)
- Network traffic features include: protocol_type, service, flag, src_bytes, dst_bytes, etc.
- Categorical features (protocol_type, service, flag) are label-encoded automatically

### Attack Classification CSV
- Must have `Label` column with attack type names
- 78+ network flow features
- Handles highly correlated features via correlation removal

## Training Workflow

1. **Load data**: Combine multiple CSVs if needed
2. **Preprocess**: Clean, encode labels, remove duplicates, handle missing values
3. **Feature selection**: RFE for threat detection, correlation removal for attack classification
4. **Scale features**: StandardScaler for threat detection, RobustScaler for attack classification
5. **Train model**: Split data (train/val/test), train model, evaluate
6. **Save bundle**: Export model + artifacts as .joblib
7. **Generate profile**: Create JSON with expected features and metadata

## Generated Files

After training, you'll get:
```
models/
├── threat_detector_ensemble.joblib
├── threat_detector_profile.json
├── attack_classifier.joblib
└── attack_classifier_profile.json
```
