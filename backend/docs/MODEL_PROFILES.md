# Model Profiles Feature

## Overview

The Model Profiles feature allows you to upload ML models with custom feature requirements and class labels, moving away from hardcoded 42-feature/14-class assumptions. Each model can now define its own expected features and output classes.

## Features

- **Per-Model Configuration**: Each uploaded model can specify its own feature list and class labels
- **Backward Compatibility**: Models uploaded without profiles automatically use default profiles (10/2 for threat_detector, 42/14 for attack_classifier)
- **Dynamic Validation**: Model validation adapts to each model's profile instead of using hardcoded shapes
- **Feature Name Mapping**: Data preprocessor matches incoming data features by name, allowing flexible column ordering
- **Profile API**: Retrieve active model profiles via REST API

## Database Schema

Three new fields added to the `ml_models` table:

- `expected_features` (JSON): Ordered list of feature names required by the model
- `class_labels` (JSON): Ordered list of class label names (for classifiers)
- `preprocessing_notes` (Text): Optional preprocessing instructions/notes

### Migration

```bash
cd backend
# Activate virtual environment
source .venv/bin/activate

# Run migration
python -m alembic upgrade head
```

## API Usage

### Upload Model with Custom Profile

**Endpoint**: `POST /api/v1/models/upload`

**Parameters**:
- `file`: Model file (.pkl, .joblib, or .h5)
- `model_type`: 'threat_detector' or 'attack_classifier'
- `description`: Optional description
- `profile_config`: Optional JSON string with profile configuration

**Example** (using curl):

```bash
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -F "file=@my_custom_model.pkl" \
  -F "model_type=attack_classifier" \
  -F "description=Custom 20-feature model" \
  -F 'profile_config={
    "expected_features": [
      "src_ip_entropy",
      "dst_port",
      "packet_count",
      "byte_rate",
      "connection_duration",
      "tcp_flags",
      "protocol_type",
      "service_type",
      "flag_count",
      "error_rate",
      "syn_count",
      "rst_count",
      "ack_count",
      "fin_count",
      "window_size",
      "urgent_pointer",
      "data_offset",
      "checksum_error",
      "retransmission_rate",
      "inter_packet_delay"
    ],
    "class_labels": [
      "BENIGN",
      "DDoS",
      "PortScan",
      "BruteForce",
      "SQLInjection"
    ],
    "preprocessing_notes": "Features extracted from PCAP using custom tool v2.1"
  }'
```

**Example** (using Python):

```python
import requests

url = "http://localhost:8000/api/v1/models/upload"

profile_config = {
    "expected_features": [
        "feature1", "feature2", "feature3", "feature4", "feature5"
    ],
    "class_labels": ["Normal", "Attack"],
    "preprocessing_notes": "Custom preprocessing applied"
}

files = {'file': open('model.pkl', 'rb')}
data = {
    'model_type': 'threat_detector',
    'description': 'My custom model',
    'profile_config': json.dumps(profile_config)
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Get Active Model Profile

**Endpoint**: `GET /api/v1/models/profile/{model_type}`

**Example**:

```bash
curl "http://localhost:8000/api/v1/models/profile/attack_classifier"
```

**Response**:

```json
{
  "model_type": "attack_classifier",
  "profile": {
    "expected_features": ["feature1", "feature2", ...],
    "class_labels": ["class1", "class2", ...],
    "preprocessing_notes": "Optional notes"
  }
}
```

## Profile Configuration Format

### Minimal Example

```json
{
  "expected_features": ["feature1", "feature2", "feature3"],
  "class_labels": ["class1", "class2"]
}
```

### Full Example

```json
{
  "expected_features": [
    " Destination Port",
    " Flow Duration",
    " Total Fwd Packets",
    "Total Length of Fwd Packets",
    " Fwd Packet Length Max"
  ],
  "class_labels": [
    "BENIGN",
    "DoS Hulk",
    "DDoS",
    "PortScan",
    "FTP-Patator"
  ],
  "preprocessing_notes": "Model trained on CIC-IDS2017 dataset with custom feature selection"
}
```

### Validation Rules

1. **expected_features**:
   - Must be a list of strings
   - Cannot be empty
   - All feature names must be unique
   - Each feature name must be a non-empty string

2. **class_labels**:
   - Must be a list of strings
   - Cannot be empty
   - All class labels must be unique
   - Each label must be a non-empty string

3. **preprocessing_notes**:
   - Optional text field
   - Can be any string

## Default Profiles

If no profile is provided during upload, these defaults are used:

### Threat Detector (10 features, 2 classes)

```python
{
    "expected_features": [
        "service", "flag", "src_bytes", "dst_bytes", "count",
        "same_srv_rate", "diff_srv_rate", "dst_host_srv_count",
        "dst_host_same_srv_rate", "dst_host_same_src_port_rate"
    ],
    "class_labels": ["Normal", "Attack"],
    "preprocessing_notes": "Default 10-feature threat detection profile"
}
```

### Attack Classifier (42 features, 14 classes)

```python
{
    "expected_features": [
        " Destination Port", " Flow Duration", " Total Fwd Packets",
        "Total Length of Fwd Packets", " Fwd Packet Length Max",
        # ... 37 more features
    ],
    "class_labels": [
        "BENIGN", "DoS Hulk", "DDoS", "PortScan", "FTP-Patator",
        "DoS slowloris", "DoS Slowhttptest", "SSH-Patator",
        "DoS GoldenEye", "Web Attack – Brute Force", "Bot",
        "Web Attack – XSS", "Web Attack – Sql Injection", "Infiltration"
    ],
    "preprocessing_notes": "Default 42-feature attack classification profile with 14 attack types"
}
```

## Using Profiles in Code

### DataPreprocessor

```python
from app.services.preprocessor import DataPreprocessor
from app.services.model_manager import ModelManager

preprocessor = DataPreprocessor()
model_manager = ModelManager()

# Get active model profile
profile = model_manager.get_active_model_profile(db, 'attack_classifier')

# Validate and extract features using profile
features = preprocessor.validate_and_extract_features_with_profile(
    raw_data=incoming_data,
    expected_features=profile['expected_features'],
    allow_extra_columns=True  # Ignore extra columns with warning
)
```

### ModelValidator

The validator automatically uses profile information during model upload:

```python
from app.services.model_validator import ModelValidator

validator = ModelValidator()

profile_config = {
    'expected_features': ['feature1', 'feature2', 'feature3'],
    'class_labels': ['class1', 'class2']
}

result = validator.validate_model(
    file_path='model.pkl',
    model_type='threat_detector',
    file_format='.pkl',
    profile_config=profile_config
)
```

## Frontend Usage

The Models UI (http://localhost:3000/models) provides:

1. **Active Model Profiles Display**: Shows current active model's features and classes
2. **Custom Profile Upload**: Optional JSON textarea when uploading new models
3. **Profile Preview**: See feature count and class count for each model in the list

### Steps to Upload Model with Custom Profile:

1. Navigate to Models page
2. Click "Upload New Model"
3. Select model file and type
4. Click "Show" next to "Custom Model Profile (Optional)"
5. Paste JSON profile configuration
6. Click "Upload Model"

## Migration Guide

### Existing Models

Models uploaded before this feature will:
- Show `null` for `expected_features`, `class_labels`, and `preprocessing_notes`
- Automatically use default profiles when loaded
- Continue to work without any changes

### Updating Existing Models

To add profiles to existing models:

```python
from app.models.database import MLModel
from app.services.model_profiles import get_default_profile

# Get model
model = db.query(MLModel).filter(MLModel.id == model_id).first()

# Apply default profile
profile = get_default_profile(model.model_type)
model.expected_features = profile['expected_features']
model.class_labels = profile['class_labels']
model.preprocessing_notes = profile['preprocessing_notes']

db.commit()
```

## Troubleshooting

### Profile Validation Errors

**Error**: "Missing required features: feature1, feature2"
- **Cause**: Incoming data doesn't have all required features
- **Solution**: Ensure your data includes all features defined in the profile, or update the profile

**Error**: "expected_features must contain unique values"
- **Cause**: Duplicate feature names in profile
- **Solution**: Remove duplicates from the feature list

**Error**: "class_labels cannot be empty"
- **Cause**: Empty class labels list
- **Solution**: Provide at least one class label

### Model Upload Failures

**Error**: "Feature count mismatch"
- **Cause**: Model's `n_features_in_` doesn't match profile feature count
- **Solution**: Ensure profile has same number of features as model expects

**Error**: "Invalid JSON in profile_config"
- **Cause**: Malformed JSON
- **Solution**: Validate JSON syntax before uploading

## Best Practices

1. **Feature Names**: Use descriptive, consistent feature names
2. **Class Labels**: Keep class labels concise and meaningful
3. **Preprocessing Notes**: Document feature engineering and data sources
4. **Testing**: Always test with sample data after upload
5. **Versioning**: Include version info in description or preprocessing notes
6. **Documentation**: Maintain external docs describing feature meanings

## Examples

See `/backend/examples/model_profiles/` for:
- Sample profile configurations
- Example upload scripts
- Test data generators
- Profile validation examples

## API Reference

Full API documentation available at: http://localhost:8000/docs

Key endpoints:
- `POST /api/v1/models/upload` - Upload model with profile
- `GET /api/v1/models/profile/{model_type}` - Get active profile
- `GET /api/v1/models/` - List all models (includes profiles)
- `GET /api/v1/models/{model_id}` - Get specific model with profile
