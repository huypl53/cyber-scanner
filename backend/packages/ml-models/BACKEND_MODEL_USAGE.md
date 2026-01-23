# Backend Model Usage Quick Reference

## Threat Detection (Binary Classification)

### Model: RealEnsembleModel
**File**: `backend/models/threat_detector_ensemble.joblib`
**Type**: Keras Ensemble (ANN + LSTM)

### Usage
```python
from app.models.ml_models import get_ensemble_model

# Load model (singleton)
model = get_ensemble_model()

# Prepare features (must match exactly)
features = {
    'protocol_type': 1,  # Encoded categorical (tcp=1, udp=2, etc.)
    'service': 20,       # Encoded categorical
    'flag': 2,           # Encoded categorical
    'src_bytes': 100.0,
    'dst_bytes': 50.0,
    'count': 5.0,
    'same_srv_rate': 0.8,
    'diff_srv_rate': 0.2,
    'dst_host_srv_count': 10.0,
    'dst_host_same_srv_rate': 0.9
}

# Predict
threat_score, is_attack = model.predict(features)

# Results
print(f"Threat Score: {threat_score:.4f}")  # 0.0 to 1.0
print(f"Is Attack: {is_attack}")            # True/False
```

### Expected Output
- `threat_score`: Float between 0.0 (normal) and 1.0 (attack)
- `is_attack`: Boolean (True if score > 0.5)

---

## Attack Classification (Multi-class)

### Model: RealDecisionTreeModel
**File**: `backend/models/attack_classifier.joblib`
**Type**: Decision Tree Classifier

### Usage
```python
from app.models.ml_models import get_decision_tree_model

# Load model (singleton)
model = get_decision_tree_model()

# Prepare features (41 features, no leading spaces)
features = {
    'Destination Port': 80,
    'Flow Duration': 1000,
    'Total Fwd Packets': 5,
    'Fwd Packet Length Max': 150,
    'Fwd Packet Length Min': 40,
    'Fwd Packet Length Mean': 100,
    'Bwd Packet Length Max': 100,
    'Bwd Packet Length Min': 30,
    'Flow Bytes/s': 500.0,
    'Flow Packets/s': 5.0,
    'Flow IAT Mean': 100,
    'Flow IAT Std': 20,
    'Flow IAT Min': 50,
    'Fwd IAT Std': 15,
    'Bwd IAT Std': 15,
    'Fwd PSH Flags': 0,
    'Bwd PSH Flags': 0,
    'Fwd URG Flags': 0,
    'Bwd URG Flags': 0,
    'Bwd Packets/s': 2.0,
    'Min Packet Length': 30,
    'FIN Flag Count': 0,
    'RST Flag Count': 0,
    'PSH Flag Count': 1,
    'ACK Flag Count': 1,
    'URG Flag Count': 0,
    'CWE Flag Count': 0,
    'Down/Up Ratio': 1.0,
    'Fwd Avg Bytes/Bulk': 0,
    'Fwd Avg Packets/Bulk': 0,
    'Fwd Avg Bulk Rate': 0,
    'Bwd Avg Bytes/Bulk': 0,
    'Bwd Avg Packets/Bulk': 0,
    'Bwd Avg Bulk Rate': 0,
    'Init_Win_bytes_forward': 8192,
    'Init_Win_bytes_backward': 8192,
    'min_seg_size_forward': 48,
    'Active Mean': 100,
    'Active Std': 20,
    'Active Max': 200,
    'Idle Std': 0
}

# Predict
attack_type_encoded, attack_type_name, confidence = model.predict(features)

# Results
print(f"Attack Type (encoded): {attack_type_encoded}")  # 0-3
print(f"Attack Type (name): {attack_type_name}")        # e.g., "BENIGN"
print(f"Confidence: {confidence:.4f}")                  # 0.0 to 1.0
```

### Expected Output
- `attack_type_encoded`: Integer (0-3)
- `attack_type_name`: String ("BENIGN", "Web Attack - Brute Force", etc.)
- `confidence`: Float between 0.0 and 1.0

---

## Feature Names Reference

### Threat Detection (10 features)
```python
THREAT_DETECTION_FEATURES = [
    'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'count', 'same_srv_rate', 'diff_srv_rate', 'dst_host_srv_count',
    'dst_host_same_srv_rate'
]
```

### Attack Classification (41 features)
```python
ATTACK_CLASSIFICATION_FEATURES = [
    'Destination Port', 'Flow Duration', 'Total Fwd Packets',
    'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
    'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Flow Bytes/s', 'Flow Packets/s',
    'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Min', 'Fwd IAT Std',
    'Bwd IAT Std', 'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags',
    'Bwd URG Flags', 'Bwd Packets/s', 'Min Packet Length', 'FIN Flag Count',
    'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count',
    'URG Flag Count', 'CWE Flag Count', 'Down/Up Ratio', 'Fwd Avg Bytes/Bulk',
    'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
    'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate', 'Init_Win_bytes_forward',
    'Init_Win_bytes_backward', 'min_seg_size_forward', 'Active Mean',
    'Active Std', 'Active Max', 'Idle Std'
]
```

---

## Common Pitfalls

1. **Feature Name Mismatch**: Feature names must match exactly (case-sensitive, no extra spaces)
2. **Missing Features**: All required features must be present in the input dictionary
3. **Categorical Encoding**: For threat detector, categorical features must be pre-encoded (protocol_type, service, flag)
4. **Data Types**: Features should be numeric (int or float)

---

## Testing Models

Run the integration test:
```bash
cd /mnt/Code/code/freelance/2511-AI-heal-network-sec/ui/research
uv run python test_backend_integration.py
```

Expected output:
```
✓ All tests passed! Models are ready for backend activation.
```
