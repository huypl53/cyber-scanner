"""
API routes for ML model management.
Handles model upload, validation, versioning, and activation.
"""
import os
import json
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.schemas import (
    MLModelResponse,
    MLModelListResponse,
    MLModelStorageStatsResponse
)
from app.services.model_manager import ModelManager, ModelManagerError
from app.services.model_validator import ModelValidator
from app.services.model_profiles import validate_profile_config

router = APIRouter(prefix="/api/v1/models", tags=["models"])

# Initialize model manager
model_manager = ModelManager()
model_validator = ModelValidator()


@router.post("/upload", response_model=MLModelResponse)
async def upload_model(
    file: UploadFile = File(..., description="Model file (.pkl, .joblib, or .h5)"),
    model_type: str = Form(..., description="Type of model: 'threat_detector' or 'attack_classifier'"),
    description: Optional[str] = Form(None, description="Optional description"),
    profile_config: Optional[str] = Form(None, description="Optional JSON config with expected_features, class_labels, preprocessing_notes"),
    db: Session = Depends(get_db)
):
    """
    Upload and validate a new ML model.

    The model will be validated for:
    - Correct file format (.pkl, .joblib, or .h5)
    - Proper architecture (input shape matches expected features)
    - Successful test prediction

    After successful upload, the model is stored with a timestamp-based version
    but is NOT automatically activated. Use the activate endpoint to make it active.

    **Supported Model Types:**
    - `threat_detector`: Binary threat detection (10 features)
    - `attack_classifier`: Multi-class attack classification (42 features)

    **Supported Formats:**
    - `.pkl`: Python pickle
    - `.joblib`: scikit-learn joblib
    - `.h5`: Keras/TensorFlow (requires tensorflow installed)
    """
    # Validate model type
    if model_type not in ['threat_detector', 'attack_classifier']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_type. Must be 'threat_detector' or 'attack_classifier', got: {model_type}"
        )

    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.pkl', '.joblib', '.h5']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_extension}. Supported formats: .pkl, .joblib, .h5"
        )

    # Parse and validate profile_config if provided
    parsed_profile = None
    if profile_config:
        try:
            parsed_profile = json.loads(profile_config)
            # Validate the profile configuration
            validate_profile_config(
                parsed_profile.get('expected_features'),
                parsed_profile.get('class_labels')
            )
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in profile_config: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid profile configuration: {str(e)}"
            )

    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Save and validate model
        ml_model = model_manager.save_model(
            db=db,
            file_path=temp_file_path,
            original_filename=file.filename,
            model_type=model_type,
            file_format=file_extension,
            description=description,
            uploaded_by=None,  # TODO: Add authentication and get user
            profile_config=parsed_profile
        )

        return ml_model

    except ModelManagerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload model: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass  # Best effort cleanup


@router.get("/", response_model=MLModelListResponse)
def list_models(
    model_type: Optional[str] = None,
    include_inactive: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all uploaded models, optionally filtered by type.

    **Query Parameters:**
    - `model_type`: Filter by model type ('threat_detector' or 'attack_classifier')
    - `include_inactive`: Whether to include inactive models (default: True)

    **Response:**
    Returns a list of all models with their metadata, validation results, and activation status.
    """
    try:
        models = model_manager.list_models(db, model_type, include_inactive)
        return MLModelListResponse(
            models=models,
            total_count=len(models)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/{model_id}", response_model=MLModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific model.

    **Path Parameters:**
    - `model_id`: ID of the model to retrieve

    **Response:**
    Returns complete model information including validation results and metadata.
    """
    model = model_manager.get_model_info(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID {model_id} not found")

    return model


@router.post("/{model_id}/activate", response_model=MLModelResponse)
def activate_model(model_id: int, db: Session = Depends(get_db)):
    """
    Activate a specific model version.

    This will deactivate all other models of the same type and make this
    version the active model used for predictions.

    **Path Parameters:**
    - `model_id`: ID of the model to activate

    **Important:**
    Only one model can be active per model type at a time.
    Activating a new version will automatically deactivate the previous one.
    """
    try:
        model = model_manager.activate_model(db, model_id)
        return model
    except ModelManagerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate model: {str(e)}")


@router.post("/{model_id}/deactivate", response_model=MLModelResponse)
def deactivate_model(model_id: int, db: Session = Depends(get_db)):
    """
    Deactivate a specific model version.

    **Path Parameters:**
    - `model_id`: ID of the model to deactivate

    **Warning:**
    Deactivating the active model without activating another will leave
    no active model for that type.
    """
    try:
        model = model_manager.deactivate_model(db, model_id)
        return model
    except ModelManagerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate model: {str(e)}")


@router.delete("/{model_id}")
def delete_model(
    model_id: int,
    delete_file: bool = True,
    db: Session = Depends(get_db)
):
    """
    Delete a model from the system.

    **Path Parameters:**
    - `model_id`: ID of the model to delete

    **Query Parameters:**
    - `delete_file`: Whether to also delete the model file from disk (default: True)

    **Important:**
    - Cannot delete an active model. Deactivate it first or activate another version.
    - File deletion is permanent and cannot be undone.
    """
    try:
        model_manager.delete_model(db, model_id, delete_file)
        return {"message": f"Model {model_id} deleted successfully"}
    except ModelManagerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


@router.get("/stats/storage", response_model=MLModelStorageStatsResponse)
def get_storage_stats(db: Session = Depends(get_db)):
    """
    Get statistics about model storage usage.

    **Response:**
    Returns storage statistics including:
    - Total number of models
    - Total storage size
    - Breakdown by model type
    - Currently active models
    """
    try:
        stats = model_manager.get_storage_stats(db)
        # Add MB conversion
        stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")


@router.get("/info/supported-formats")
def get_supported_formats():
    """
    Get list of supported model file formats.

    **Response:**
    Returns list of supported file extensions and model types.
    """
    return {
        "supported_formats": model_validator.get_supported_formats(),
        "supported_model_types": model_validator.get_supported_model_types(),
        "model_requirements": {
            "threat_detector": {
                "input_features": 10,
                "feature_names": [
                    "service", "flag", "src_bytes", "dst_bytes", "count",
                    "same_srv_rate", "diff_srv_rate", "dst_host_srv_count",
                    "dst_host_same_srv_rate", "dst_host_same_src_port_rate"
                ]
            },
            "attack_classifier": {
                "input_features": 42,
                "note": "Network flow features including port, packet statistics, TCP flags, etc."
            }
        }
    }


@router.get("/profile/{model_type}")
def get_active_model_profile(
    model_type: str,
    db: Session = Depends(get_db)
):
    """
    Get the profile configuration for the active model of a specific type.

    Returns the expected features, class labels, and preprocessing notes for the active model.
    If no active model exists or it has no profile, returns the default profile.

    **Parameters:**
    - `model_type`: Type of model ('threat_detector' or 'attack_classifier')

    **Response:**
    Returns the model profile with:
    - `expected_features`: Ordered list of feature names
    - `class_labels`: Ordered list of class label names
    - `preprocessing_notes`: Optional preprocessing instructions
    """
    if model_type not in ['threat_detector', 'attack_classifier']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_type. Must be 'threat_detector' or 'attack_classifier', got: {model_type}"
        )

    try:
        profile = model_manager.get_active_model_profile(db, model_type)
        return {
            "model_type": model_type,
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model profile: {str(e)}")
