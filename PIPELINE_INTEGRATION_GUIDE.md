# ML Pipeline Integration Guide

This guide explains how to train, bundle, and deploy both the **Threat Detection** and **Attack Classification** models with their complete preprocessing pipelines.

## Overview

Both models now save their complete preprocessing pipelines along with the trained models in a single `.joblib` file. This ensures consistency between training and inference.

---

## 1. Threat Detection Pipeline (Ensemble ANN + LSTM)

### Training Script
**File:** `research/ensemble_threat_detection_v1.py`

**What it does:**
- Loads training data with a `class` column (Normal vs Attack)
- Label encodes categorical features
- Performs RFE (Recursive Feature Elimination) to select 10 features
- Applies StandardScaler
- Trains ANN and LSTM models
- Saves complete bundle + model profile

### Training Command

```bash
python research/ensemble_threat_detection_v1.py \
  --train_csv /path/to/Train_data.csv \
  --n_features 10
```

### Outputs

1. **`threat_detector_ensemble.joblib`** - Complete pipeline bundle containing:
   - LabelEncoder for categorical features
   - Selected feature names (after RFE)
   - StandardScaler
   - ANN model weights
   - LSTM model weights

2. **`threat_detector_profile.json`** - Model metadata for backend:
   ```json
   {
     "expected_features": ["service", "flag", "src_bytes", ...],
     "class_labels": ["Normal", "Attack"],
     "preprocessing_notes": "...",
     "preprocessing_pipeline": {...}
   }
   ```

### Upload to Backend

```bash
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -F "file=@threat_detector_ensemble.joblib" \
  -F "model_type=threat_detector" \
  -F "profile_config=@threat_detector_profile.json"
```

### Activate Model

```bash
# Get model_id from upload response
curl -X POST "http://localhost:8000/api/v1/models/{model_id}/activate"
```

---

## 2. Attack Classification Pipeline (DecisionTree)

### Training Script
**File:** `research/attack_classification_v1.py`

**What it does:**
- Loads multiple CSV files from CIC-IDS2017 dataset
- Removes duplicates and handles inf/NaN values
- Label encodes categorical features and attack labels
- Removes highly correlated features (threshold=0.85)
- Applies RobustScaler
- Trains DecisionTree classifier
- Saves complete bundle + model profile

### Training Command

```bash
python research/attack_classification_v1.py \
  --train_csvs data/Friday-*.csv data/Monday-*.csv data/Thursday-*.csv \
  --correlation_threshold 0.85 \
  --max_depth 10
```

Or with wildcards:

```bash
python research/attack_classification_v1.py \
  --train_csvs data/*.csv
```

### Outputs

1. **`attack_classifier.joblib`** - Complete pipeline bundle containing:
   - LabelEncoder for attack labels
   - Feature columns (after correlation removal)
   - Removed correlated features list
   - RobustScaler
   - DecisionTree model
   - Class mapping (encoded → original labels)

2. **`attack_classifier_profile.json`** - Model metadata:
   ```json
   {
     "expected_features": ["Destination Port", "Flow Duration", ...],
     "class_labels": ["BENIGN", "DoS Hulk", "DDoS", ...],
     "preprocessing_notes": "...",
     "preprocessing_pipeline": {...}
   }
   ```

### Upload to Backend

```bash
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -F "file=@attack_classifier.joblib" \
  -F "model_type=attack_classifier" \
  -F "profile_config=@attack_classifier_profile.json"
```

### Activate Model

```bash
# Get model_id from upload response
curl -X POST "http://localhost:8000/api/v1/models/{model_id}/activate"
```

---

## 3. Backend Architecture

### New Files Created

1. **`backend/app/models/ensemble_pipeline.py`**
   - `EnsembleThreatDetector` - Wrapper for threat detection pipeline

2. **`backend/app/models/attack_classification_pipeline.py`**
   - `AttackClassifierV2` - Wrapper for attack classification pipeline

3. **Research files:**
   - `research/ensemble_threat_detection_v1.py` - Bundled threat detector
   - `research/attack_classification_v1.py` - Bundled attack classifier

### Modified Files

1. **`backend/app/models/ml_models.py`**
   - Added `get_ensemble_model_v2()` and `reset_ensemble_model_v2()`
   - Added `get_attack_classifier_v2()` and `reset_attack_classifier_v2()`

2. **`backend/app/services/threat_detector.py`**
   - Loads real ensemble model when available
   - Falls back to mock model

3. **`backend/app/services/model_validator.py`**
   - Validates ensemble bundles with `_validate_ensemble_bundle()`
   - Validates attack classifier bundles with `_validate_attack_classifier_bundle()`

4. **`backend/app/services/preprocessor.py`**
   - Added `extract_features_for_ensemble()` for ensemble model support

5. **`backend/app/api/routes/models.py`**
   - Resets model singletons on activation

6. **`backend/app/api/routes/predictions.py`**
   - Updated to pass db session to ThreatDetectorService

7. **`backend/app/api/routes/upload.py`**
   - Updated to pass db session to ThreatDetectorService

---

## 4. How It Works

### Training Phase

```
Raw CSV Data
    ↓
[Label Encoding]
    ↓
[Feature Selection (RFE or Correlation)]
    ↓
[Scaling (StandardScaler or RobustScaler)]
    ↓
[Model Training (ANN+LSTM or DecisionTree)]
    ↓
Single .joblib Bundle
```

### Inference Phase (Backend)

```
CSV Upload
    ↓
[Feature Extraction]
    ↓
Load Active Model Bundle
    ↓
Bundle.predict()
  ├─ Label Encoding (internal)
  ├─ Feature Selection (internal)
  ├─ Scaling (internal)
  └─ Model Prediction
    ↓
Prediction Results
```

---

## 5. Key Features

### ✅ Complete Preprocessing
- All preprocessing steps saved with the model
- No need to replicate preprocessing in backend
- Guaranteed consistency between training and inference

### ✅ Single File Deployment
- One `.joblib` file contains everything
- Easy versioning and rollback
- Atomic uploads

### ✅ Model Profiles
- Automatic metadata generation
- Documents feature requirements
- Describes preprocessing steps

### ✅ Hot Reloading
- Singleton cache resets on activation
- No server restart needed
- Immediate model switching

### ✅ Backward Compatible
- Falls back to mock models if no real model active
- Supports both bundled and traditional models
- Progressive migration

---

## 6. Testing Your Models

### Test Threat Detector

```bash
# Upload CSV for threat detection
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -F "file=@test_traffic.csv"
```

### Test Attack Classifier

```bash
# Upload CSV for attack classification
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -F "file=@test_attacks.csv"
```

### Check Prediction Statistics

```bash
curl http://localhost:8000/api/v1/predictions/stats
```

---

## 7. Model Management

### List All Models

```bash
curl http://localhost:8000/api/v1/models/
```

### List Threat Detectors Only

```bash
curl http://localhost:8000/api/v1/models/?model_type=threat_detector
```

### Get Model Details

```bash
curl http://localhost:8000/api/v1/models/{model_id}
```

### Deactivate Model

```bash
curl -X POST http://localhost:8000/api/v1/models/{model_id}/deactivate
```

### Delete Model

```bash
curl -X DELETE http://localhost:8000/api/v1/models/{model_id}
```

---

## 8. Troubleshooting

### Issue: KeyError during training

**Problem:** Pandas requires lists for column selection, not tuples

**Solution:** Already fixed in the code - uses `list(selected_features)`

### Issue: Model not loading in backend

**Check:**
1. Model is uploaded and activated
2. Check backend logs for "Loaded real ensemble model v2" or "Loaded real attack classifier v2"
3. Ensure `.joblib` format is used
4. Verify model_type matches (threat_detector or attack_classifier)

### Issue: Prediction fails with missing features

**Cause:** Input data missing required features

**Solution:** Check model profile to see required features:
```bash
curl http://localhost:8000/api/v1/models/profile/threat_detector
```

### Issue: CUDA/TensorFlow warnings

**Solution:** These are harmless warnings from TensorFlow. To suppress:
- Set environment variable: `TF_CPP_MIN_LOG_LEVEL=2`
- Or ignore - they don't affect functionality

---

## 9. Next Steps

1. **Train your models** with actual training data
2. **Upload bundles** to the backend
3. **Activate models** to replace mocks
4. **Test predictions** with real traffic data
5. **Monitor performance** through API endpoints

The backend will automatically use your trained models for all threat detection and attack classification predictions!
