---
name: ml-integrate
description: Integrate trained ML models with FastAPI backend. Use when copying models to backend, testing backend loading, or activating models.
allowed-tools: Bash, Read, Write, Edit
---

# ML Backend Integration

## Integration Steps

1. Copy model bundle to `backend/models/`
2. Test loading with backend model classes
3. Verify feature compatibility
4. Activate model in database (optional)

## Commands

### Copy to Backend
```bash
# Copy threat detection model
cp models/threat_detector_ensemble.joblib ../backend/models/

# Copy attack classification model
cp models/attack_classifier.joblib ../backend/models/

# Copy profile JSON for reference
cp models/threat_detector_profile.json ../backend/models/
cp models/attack_classifier_profile.json ../backend/models/
```

### Test Backend Loading

**Threat Detection:**
```bash
cd ../backend
uv run python -c "
from app.models.ml_models import RealEnsembleModel
m = RealEnsembleModel(model_path='models/threat_detector_ensemble.joblib')
print('Model loaded:', m.is_real_model)
print('Features:', m.get_expected_features())
print('Classes:', m.get_class_labels())
"
```

**Attack Classification:**
```bash
cd ../backend
uv run python -c "
from app.models.ml_models import RealDecisionTreeModel
m = RealDecisionTreeModel(model_path='models/attack_classifier.joblib')
print('Model loaded:', m.is_real_model)
print('Features:', m.get_expected_features())
print('Classes:', m.get_class_labels())
"
```

### Activate Model (via Database)

```bash
# Using backend API or database directly
cd ../backend
uv run python -c "
from app.services.model_manager import ModelManager
manager = ModelManager()

# Activate threat detection model
manager.activate_model(
    model_id='threat_detector_ensemble',
    model_path='models/threat_detector_ensemble.joblib',
    model_type='threat_detector'
)

# Activate attack classification model
manager.activate_model(
    model_id='attack_classifier',
    model_path='models/attack_classifier.joblib',
    model_type='attack_classifier'
)
"
```

## Backend Paths

| Component | Path |
|-----------|------|
| Model loader | `backend/app/models/ml_models.py` |
| Model manager | `backend/app/services/model_manager.py` |
| Preprocessor | `backend/app/services/preprocessor.py` |
| Model storage | `backend/models/` |

## Backend Model Classes

### RealEnsembleModel (Threat Detection)
```python
# Expected bundle structure:
bundle = {
    'artifacts': PreprocessArtifacts(
        encoders: dict,
        selected_features: tuple,
        scaler: StandardScaler
    ),
    'ann_weights': bytes,  # Keras model weights
    'lstm_weights': bytes,  # Keras model weights
    'ann_config': dict,  # Model architecture
    'lstm_config': dict,  # Model architecture
    'n_features': int,
    'random_state': int
}
```

### RealDecisionTreeModel (Attack Classification)
```python
# Expected bundle structure:
bundle = {
    'artifacts': {
        'label_encoder': LabelEncoder,
        'scaler': RobustScaler,
        'feature_columns': tuple,
        'removed_columns': tuple,
        'class_mapping': dict
    },
    'model': DecisionTreeClassifier,
    'correlation_threshold': float,
    'max_depth': int,
    'random_state': int
}
```

## Integration Checklist

- [ ] Model bundle copied to `backend/models/`
- [ ] Profile JSON copied for reference
- [ ] Model loads with backend class without errors
- [ ] Features match backend expectations
- [ ] Class labels are correct
- [ ] Test prediction works via backend
- [ ] Model activated in database (if needed)

## Testing Integration

```bash
# Start backend server
cd ../backend
uv run uvicorn app.main:app --reload

# Test prediction endpoint (in another terminal)
curl -X POST "http://localhost:8000/api/v1/predict/threat" \
  -H "Content-Type: application/json" \
  -d '{"features": {...}}'

curl -X POST "http://localhost:8000/api/v1/predict/attack" \
  -H "Content-Type: application/json" \
  -d '{"features": {...}}'
```

## Troubleshooting

### Model fails to load
- Check bundle format matches backend expectations
- Verify all artifacts present (scaler, encoders, selected_features)
- Ensure feature names match exactly (case-sensitive)

### Feature mismatch errors
- Compare `selected_features` in bundle with backend expectations
- Check feature name spelling, case sensitivity, and whitespace
- Verify preprocessing steps match training

### Prediction errors
- Validate input data distribution matches training data
- Check for NaN/inf values in input
- Ensure all required features are present
