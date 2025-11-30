# Model Profile Examples

This directory contains example model profile configurations for uploading custom ML models.

## Files

- `custom_threat_detector_profile.json` - Example 10-feature threat detection model profile
- `custom_attack_classifier_profile.json` - Example 25-feature attack classification model profile

## Usage

### Using with curl

```bash
# Upload model with custom profile
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -F "file=@your_model.pkl" \
  -F "model_type=attack_classifier" \
  -F "description=My custom model" \
  -F "profile_config=$(cat custom_attack_classifier_profile.json)"
```

### Using with Python

```python
import json
import requests

# Load profile from file
with open('custom_attack_classifier_profile.json', 'r') as f:
    profile_config = json.load(f)

# Upload model
url = "http://localhost:8000/api/v1/models/upload"
files = {'file': open('your_model.pkl', 'rb')}
data = {
    'model_type': 'attack_classifier',
    'description': 'My custom model',
    'profile_config': json.dumps(profile_config)
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Using with Frontend

1. Navigate to http://localhost:3000/models
2. Click "Upload New Model"
3. Select your model file
4. Click "Show" next to "Custom Model Profile"
5. Copy and paste the content of one of the JSON files
6. Click "Upload Model"

## Creating Your Own Profile

1. Copy one of the example files
2. Update `expected_features` to match your model's feature names **in the exact order**
3. Update `class_labels` to match your model's output classes **in the exact order**
4. Add optional `preprocessing_notes` to document your preprocessing steps
5. Validate JSON syntax
6. Upload with your model file

## Important Notes

- **Feature Order Matters**: The order of features in `expected_features` must match the order your model expects
- **Class Order Matters**: The order of `class_labels` must match your model's output class indices
- **Uniqueness**: All feature names and class labels must be unique
- **Non-Empty**: Both lists must contain at least one element
- **Strings Only**: All feature names and class labels must be strings

## Validation

The API will validate your profile configuration and reject it if:
- Features or classes are not unique
- Lists are empty
- Values are not strings
- JSON is malformed

## See Also

- [Full Documentation](../../docs/MODEL_PROFILES.md)
- [API Documentation](http://localhost:8000/docs)
