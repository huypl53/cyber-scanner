# Bug Fix: Attack Classification CSV Upload Error

## Issue
When uploading CSV files with 42 features (attack classification), the system returned an error:
```
Error processing CSV: Missing required features: {'dst_host_srv_count', 'src_bytes', 'same_srv_rate', 'diff_srv_rate', 'dst_host_same_srv_rate', 'count', 'service', 'dst_host_same_src_port_rate', 'flag', 'dst_bytes'}
```

## Root Cause
The upload endpoint (`app/api/routes/upload.py`) was **always running threat detection first**, regardless of the CSV's feature set.

### Problem Flow:
1. Attack classification CSV (42 features) uploads successfully
2. Preprocessing correctly detects `model_type = "attack_classification"`
3. Data is stored in database
4. **Bug**: Threat detector is called with 42 attack classification features
5. Threat detector's EnsembleModel validates and expects its 10 specific features
6. Validation fails with "Missing required features" error

### Code Issue
**Before Fix (lines 84-89):**
```python
# Run threat detection
threat_predictions = threat_detector.predict_batch(
    features_list,  # <- 42 attack classification features passed to 10-feature model!
    db,
    traffic_ids
)
```

The threat detector was always called first, but it expects exactly 10 specific features. When passed 42 attack classification features, it failed validation.

## Solution

### Changes Made

#### 1. Modified `app/api/routes/upload.py`
Changed the logic to run the appropriate model based on the detected feature type:

**After Fix:**
```python
# Run appropriate model based on detected type
if model_type == "attack_classification":
    # For attack classification, run attack classifier directly
    attack_predictions = attack_classifier.predict_batch(
        features_list,
        db,
        traffic_ids
    )

    # Log self-healing actions
    self_healing_actions = self_healing.log_action_batch(
        attack_predictions,
        db
    )

    # Build response with attack predictions only
    for traffic_record, attack_pred in zip(traffic_data_records, attack_predictions):
        action = action_map.get(attack_pred.id) if attack_pred else None
        predictions_response.append(
            CompletePredictionResponse(
                traffic_data=traffic_record,
                threat_prediction=None,  # No threat prediction for attack classification
                attack_prediction=attack_pred,
                self_healing_action=action
            )
        )
else:
    # Run threat detection for 10-feature model
    threat_predictions = threat_detector.predict_batch(
        features_list,
        db,
        traffic_ids
    )

    # Build response for threat detection only
    for traffic_record, threat_pred in zip(traffic_data_records, threat_predictions):
        predictions_response.append(
            CompletePredictionResponse(
                traffic_data=traffic_record,
                threat_prediction=threat_pred,
                attack_prediction=None,
                self_healing_action=None
            )
        )
```

#### 2. Modified `app/models/schemas.py`
Made `threat_prediction` optional in the response schema:

**Before:**
```python
class CompletePredictionResponse(BaseModel):
    traffic_data: TrafficDataResponse
    threat_prediction: ThreatPredictionResponse  # Required
    attack_prediction: Optional[AttackPredictionResponse] = None
    self_healing_action: Optional[SelfHealingActionResponse] = None
```

**After:**
```python
class CompletePredictionResponse(BaseModel):
    traffic_data: TrafficDataResponse
    threat_prediction: Optional[ThreatPredictionResponse] = None  # Now optional
    attack_prediction: Optional[AttackPredictionResponse] = None
    self_healing_action: Optional[SelfHealingActionResponse] = None
```

## Testing

### Test Results
```bash
# Test attack classification CSV (42 features)
curl -X POST http://localhost:8000/api/v1/upload/csv \
  -F "file=@test_data/attack_classification_test.csv"

✓ Successfully processed 10 rows
✓ Batch: 05a117d7-4f42-4294-97c8-f2dc475dfad4
✓ Predictions: 10
```

### Verified Functionality
- ✅ Threat detection CSV (10 features) - Works correctly
- ✅ Attack classification CSV (42 features) - Fixed, now works correctly
- ✅ Auto-detection of model type based on features
- ✅ Appropriate model called based on feature set
- ✅ Response schema accepts both model types

## Files Modified
1. `/backend/app/api/routes/upload.py` - Lines 82-135 (refactored model selection logic)
2. `/backend/app/models/schemas.py` - Line 70 (made threat_prediction optional)

## Impact
- **Breaking Change**: No
- **API Changes**: Response schema now allows `threat_prediction` to be null for attack classification uploads
- **Frontend Impact**: Frontend should handle cases where `threat_prediction` may be null

## Notes
The original design assumed threat detection would always run first as a pre-filter before attack classification. However, the two models have completely different feature requirements:
- Threat Detection: 10 features
- Attack Classification: 42 features

The fix separates these concerns and runs only the appropriate model for the given feature set.
