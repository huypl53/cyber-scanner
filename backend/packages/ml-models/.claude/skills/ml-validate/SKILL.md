---
name: ml-validate
description: Validate trained ML models, generate CSV examples, and verify backend compatibility. Use when validating models or exporting test data.
allowed-tools: Bash, Read, Write, Edit
---

# ML Model Validation

## Validation Workflow

1. Load model bundle
2. Verify bundle structure
3. Run test predictions
4. Validate feature sets
5. Export CSV examples

## Commands

### Validate Model
```bash
# Using validation script
uv run .claude/scripts/validate_model.py --model-path models/threat_detector.joblib --model-type threat_detector

# Or using python directly
uv run python -c "
import joblib
bundle = joblib.load('models/threat_detector.joblib')
print('Bundle keys:', list(bundle.keys()))
print('Expected features:', bundle.get('artifacts', {}).get('selected_features', []))
"
```

### Export CSV Examples
```bash
# Using export script
uv run .claude/scripts/export_csv_examples.py --model-path models/threat_detector.joblib --output examples/validation.csv --n-samples 10

# Or manually from trained pipeline
uv run python -c "
import joblib
import pandas as pd
bundle = joblib.load('models/threat_detector.joblib')
features = bundle['artifacts']['selected_features']
sample_data = pd.DataFrame({f: [0] for f in features})
sample_data.to_csv('examples/sample.csv', index=False)
"
```

## Backend Compatibility

### Verify Model Works with Backend

**Threat Detection (RealEnsembleModel):**
```python
# Test loading with backend model class
cd ../backend
uv run python -c "
from app.models.ml_models import RealEnsembleModel
m = RealEnsembleModel(model_path='models/threat_detector_xxx.joblib')
print('Loaded:', m.is_real_model)
print('Expected features:', m.get_expected_features())
"
```

**Attack Classification (RealDecisionTreeModel):**
```python
# Test loading with backend model class
cd ../backend
uv run python -c "
from app.models.ml_models import RealDecisionTreeModel
m = RealDecisionTreeModel(model_path='models/attack_classifier.joblib')
print('Loaded:', m.is_real_model)
print('Attack types:', m.get_class_labels())
"
```

## Validation Checklist

- [ ] Bundle loads without errors using `joblib.load()`
- [ ] All expected features are documented in profile JSON
- [ ] Class labels match backend expectations
- [ ] Preprocessing steps are documented
- [ ] Test predictions work correctly
- [ ] CSV examples can be generated and used for predictions

## Model Profile Format

Expected profile JSON structure:
```json
{
  "expected_features": ["feature1", "feature2", ...],
  "class_labels": ["Normal", "Attack", ...],
  "preprocessing_notes": "Description of preprocessing steps",
  "preprocessing_pipeline": {
    "steps": ["step1", "step2", ...],
    "n_features_selected": 10,
    "selected_features": ["feature1", ...],
    "scaler_type": "RobustScaler"
  }
}
```

## Feature Validation

### Check Features Match
```python
import joblib

bundle = joblib.load('models/threat_detector.joblib')
expected = bundle['artifacts']['selected_features']
print("Expected features:", expected)

# Validate CSV has all features
import pandas as pd
df = pd.read_csv('data/test.csv')
missing = set(expected) - set(df.columns)
if missing:
    print(f"Missing features: {missing}")
else:
    print("All features present")
```

## Test Prediction Example

```bash
# Run prediction on test data
uv run threat_classification.py \
  --train_csv data/train/threat.csv \
  --predict_csv data/test.csv \
  --output_preds predictions.csv
```
