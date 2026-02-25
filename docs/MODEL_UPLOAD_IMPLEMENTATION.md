# Model Upload Feature Implementation

## Overview

I've successfully implemented a complete ML model upload, validation, and management system for the AI Threat Detection System. This feature allows you to upload trained models (threat detector and attack classifier), validate them, manage multiple versions, and activate/deactivate models as needed.

## Features Implemented

### 1. Backend Components

#### Database Schema (`backend/app/models/database.py`)
- **New `MLModel` table** for tracking model versions:
  - `model_type`: 'threat_detector' or 'attack_classifier'
  - `version`: Timestamp-based versioning (e.g., '20251128_143022')
  - `file_path`: Storage location on disk
  - `file_format`: '.pkl', '.joblib', or '.h5'
  - `is_active`: Boolean flag for active model
  - `model_metadata`: JSON field for architecture info
  - `validation_results`: JSON field for test prediction results
  - `file_size_bytes`: Storage tracking
  - Audit fields: `created_at`, `uploaded_by`, `description`

#### Model Validation Service (`backend/app/services/model_validator.py`)
Comprehensive validation including:
- **File format validation**: Checks file extension and can load the file
- **Architecture validation**: Verifies input shape matches expected features
  - Threat Detector: 10 features
  - Attack Classifier: 42 features
- **Test prediction**: Runs sample prediction to ensure model works
- Supports:
  - `.pkl` (Python pickle)
  - `.joblib` (scikit-learn joblib)
  - `.h5` (Keras/TensorFlow - requires tensorflow installed)

#### Model Management Service (`backend/app/services/model_manager.py`)
Full model lifecycle management:
- **Upload & Store**: Save models with version management
- **Activation**: Activate/deactivate specific model versions
- **List & Filter**: Query models by type and status
- **Delete**: Remove inactive models
- **Load**: Load active models for predictions
- **Storage Stats**: Track storage usage and model counts

#### API Endpoints (`backend/app/api/routes/models.py`)
RESTful API for model management:
- `POST /api/v1/models/upload` - Upload new model
- `GET /api/v1/models/` - List all models (with filters)
- `GET /api/v1/models/{id}` - Get specific model details
- `POST /api/v1/models/{id}/activate` - Activate a model version
- `POST /api/v1/models/{id}/deactivate` - Deactivate a model version
- `DELETE /api/v1/models/{id}` - Delete an inactive model
- `GET /api/v1/models/stats/storage` - Get storage statistics
- `GET /api/v1/models/info/supported-formats` - Get supported formats

### 2. Frontend Components

#### Model Management Page (`frontend/app/models/page.tsx`)
Full-featured UI for model management:
- **Upload Form**:
  - Select model type (threat_detector or attack_classifier)
  - Choose model file (.pkl, .joblib, .h5)
  - Optional description
  - Real-time validation feedback

- **Storage Statistics Dashboard**:
  - Total models count
  - Total storage size
  - Breakdown by model type
  - Currently active models

- **Model List Table**:
  - View all uploaded models
  - Filter by model type
  - See version, status, size, upload date
  - Activate/deactivate models
  - Delete inactive models

#### API Client (`frontend/lib/api.ts`)
TypeScript API functions for:
- `uploadModel()` - Upload new model file
- `getModels()` - Fetch model list with filters
- `getModel()` - Get single model details
- `activateModel()` - Activate a model version
- `deactivateModel()` - Deactivate a model
- `deleteModel()` - Delete a model
- `getModelStorageStats()` - Get storage statistics

#### Navigation (`frontend/app/layout.tsx`)
Added "Models" link to main navigation menu

### 3. Database Migration

**Migration File**: `backend/alembic/versions/b725fdb4d6cd_add_ml_models_table_for_model_versioning.py`
- Creates `ml_models` table with all fields
- Indexes on: `id`, `model_type`, `version`, `is_active`
- Includes downgrade function for rollback

## Setup Instructions

### 1. Run Database Migration

Start your PostgreSQL database, then run:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

This will create the `ml_models` table.

### 2. Create Models Directory

The system stores models at: `/mnt/Code/code/freelance/2511-AI-heal-network-sec/ui/backend/models/`

This directory is created automatically when the `ModelManager` is initialized. Structure:
```
backend/models/
├── threat_detector/
│   └── threat_detector_20251128_143022.pkl
└── attack_classifier/
    └── attack_classifier_20251128_150030.h5
```

### 3. Start Backend Server

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend

```bash
cd frontend
npm run dev
```

Then navigate to: http://localhost:3000/models

## Usage Guide

### Uploading a Model

1. Navigate to **Models** page in the UI
2. Select **Model Type**:
   - **Threat Detector**: Binary classification (10 features)
   - **Attack Classifier**: Multi-class attack detection (42 features)
3. Choose your model file (`.pkl`, `.joblib`, or `.h5`)
4. Optionally add a description
5. Click **Upload Model**

The system will:
- Validate file format
- Load the model
- Check architecture matches expected features
- Run a test prediction
- Store the model with timestamp-based version
- Display validation results

### Model Versioning

- **Automatic Versioning**: Each upload gets a timestamp version (e.g., `20251128_143022`)
- **Keep All Versions**: All uploaded models are preserved
- **Manual Activation**: New uploads are inactive by default

### Activating a Model

1. Find the model version in the list
2. Click **Activate**
3. System will:
   - Deactivate all other models of the same type
   - Activate the selected version
   - Update the active model indicator

### Deleting a Model

1. Ensure model is **not active** (deactivate it first if needed)
2. Click **Delete**
3. Confirm deletion
4. Model record and file are permanently removed

## Model Requirements

### Threat Detector Models
- **Input**: 10 features (NumPy array shape: `(batch_size, 10)`)
- **Features**: service, flag, src_bytes, dst_bytes, count, same_srv_rate, diff_srv_rate, dst_host_srv_count, dst_host_same_srv_rate, dst_host_same_src_port_rate
- **Output**: Binary classification (probability score or class)
- **Supported Formats**: .pkl, .joblib, .h5

### Attack Classifier Models
- **Input**: 42 features (NumPy array shape: `(batch_size, 42)`)
- **Features**: Network flow characteristics (port, packet stats, TCP flags, etc.)
- **Output**: Multi-class classification (14 attack types: BENIGN, DoS Hulk, DDoS, PortScan, etc.)
- **Supported Formats**: .pkl, .joblib, .h5

## Example: Training and Uploading a Model

### 1. Train Your Model (Example)

```python
import joblib
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Train your model
X_train = np.random.rand(1000, 10)  # 10 features for threat detector
y_train = np.random.randint(0, 2, 1000)  # Binary labels

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, 'threat_detector_rf.joblib')
```

### 2. Upload via UI

1. Go to http://localhost:3000/models
2. Select "Threat Detector"
3. Choose `threat_detector_rf.joblib`
4. Add description: "Random Forest trained on NSL-KDD dataset"
5. Upload

### 3. Activate the Model

1. Find your model in the list
2. Click "Activate"
3. Model is now live and will be used for predictions

## API Documentation

### Upload Model

```bash
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -F "file=@threat_detector_rf.joblib" \
  -F "model_type=threat_detector" \
  -F "description=Random Forest model"
```

### List Models

```bash
curl "http://localhost:8000/api/v1/models/?model_type=threat_detector&include_inactive=true"
```

### Activate Model

```bash
curl -X POST "http://localhost:8000/api/v1/models/5/activate"
```

### Get Storage Stats

```bash
curl "http://localhost:8000/api/v1/models/stats/storage"
```

## Architecture Notes

### Validation Process

1. **File Upload** → Temporary storage
2. **Format Check** → Verify extension and loadable
3. **Architecture Validation** → Check input shape
4. **Test Prediction** → Run sample data through model
5. **Storage** → Copy to permanent location
6. **Database Record** → Create MLModel entry
7. **Cleanup** → Remove temporary file

### Storage Strategy

- Models stored in: `backend/models/{model_type}/{model_type}_{version}{format}`
- File system for model files
- PostgreSQL for metadata and tracking
- Separate directories per model type

### Safety Features

- Cannot delete active models
- Only one active model per type at a time
- All validation results stored for audit
- File size limits (500MB max)
- Comprehensive error handling and rollback

## Integration with Existing System

### Using Active Models in Predictions

To integrate the uploaded models with your existing prediction services:

```python
from app.services.model_manager import ModelManager
from app.core.database import get_db

model_manager = ModelManager()

# Load active threat detector
db = next(get_db())
threat_model = model_manager.load_active_model(db, 'threat_detector')

# Use for predictions
prediction = threat_model.predict(features)
```

### Updating Threat Detector Service

Modify `backend/app/services/threat_detector.py` to use uploaded models:

```python
def __init__(self):
    try:
        db = next(get_db())
        model_manager = ModelManager()
        self.model = model_manager.load_active_model(db, 'threat_detector')
    except ModelManagerError:
        # Fallback to mock model if no active model
        self.model = get_ensemble_model()
```

## Files Created/Modified

### Backend
- ✅ `backend/app/models/database.py` - Added MLModel class
- ✅ `backend/app/models/schemas.py` - Added ML model schemas
- ✅ `backend/app/services/model_validator.py` - New file
- ✅ `backend/app/services/model_manager.py` - New file
- ✅ `backend/app/api/routes/models.py` - New file
- ✅ `backend/app/main.py` - Added models router import
- ✅ `backend/alembic/versions/b725fdb4d6cd_add_ml_models_table_for_model_versioning.py` - New migration

### Frontend
- ✅ `frontend/app/models/page.tsx` - New page
- ✅ `frontend/app/layout.tsx` - Added Models nav link
- ✅ `frontend/lib/api.ts` - Added model management API functions

## Testing Checklist

- [ ] Start PostgreSQL database
- [ ] Run database migration: `alembic upgrade head`
- [ ] Start backend server
- [ ] Start frontend
- [ ] Navigate to Models page
- [ ] Upload a test model (.pkl or .joblib)
- [ ] Verify validation results show in upload response
- [ ] Check model appears in list
- [ ] Activate the model
- [ ] Verify only one model is active
- [ ] Upload another version
- [ ] Switch active version
- [ ] Deactivate model
- [ ] Delete inactive model
- [ ] Check storage statistics update correctly

## Future Enhancements

1. **Model Metrics Tracking**: Store accuracy, precision, recall from validation
2. **A/B Testing**: Run predictions with multiple models and compare
3. **Auto-rollback**: Automatically revert if new model performs poorly
4. **Model Export**: Download models from the system
5. **Scheduled Activation**: Set models to activate at specific times
6. **Model Comparison**: Side-by-side comparison of model versions
7. **Authentication**: Integrate with user authentication for uploaded_by field

## Troubleshooting

### "TensorFlow/Keras not installed" Error
For `.h5` models, install TensorFlow:
```bash
pip install tensorflow
```

### "Model validation failed: Input shape mismatch"
Ensure your model was trained with the correct number of features:
- Threat Detector: 10 features
- Attack Classifier: 42 features

### "Cannot delete an active model"
Deactivate the model first, or activate a different version, then delete.

### Migration Already Applied
If you get "Target database is not up to date", the migration may already be applied. Check:
```bash
alembic current
```

## Summary

The model upload feature is fully implemented and ready to use. It provides:
- ✅ Secure model upload with validation
- ✅ Version management with timestamp-based versioning
- ✅ Manual activation control
- ✅ Complete UI for model management
- ✅ RESTful API for all operations
- ✅ Storage tracking and statistics
- ✅ Database persistence with migrations

You can now upload trained models for both threat detection and attack classification, manage multiple versions, and switch between them as needed!
