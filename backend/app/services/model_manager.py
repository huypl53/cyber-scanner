"""
Model management service for storing, versioning, and activating ML models.
"""
import os
import shutil
import joblib
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.database import MLModel
from app.services.model_validator import ModelValidator, ModelValidationError


class ModelManagerError(Exception):
    """Raised when model management operations fail."""
    pass


class ModelManager:
    """
    Manages ML model storage, versioning, and activation.

    Features:
    - Store model files with timestamp-based versioning
    - Validate models before storing
    - Activate/deactivate model versions
    - Track model metadata and validation results
    - Support for multiple model types (threat_detector, attack_classifier)
    """

    def __init__(self, models_directory: str = "/mnt/Code/code/freelance/2511-AI-heal-network-sec/ui/backend/models"):
        """
        Initialize the model manager.

        Args:
            models_directory: Base directory for storing model files
        """
        self.models_directory = models_directory
        self.validator = ModelValidator()

        # Ensure models directory exists
        os.makedirs(self.models_directory, exist_ok=True)

        # Create subdirectories for each model type
        for model_type in ['threat_detector', 'attack_classifier']:
            os.makedirs(os.path.join(self.models_directory, model_type), exist_ok=True)

    def save_model(
        self,
        db: Session,
        file_path: str,
        original_filename: str,
        model_type: str,
        file_format: str,
        description: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> MLModel:
        """
        Save and validate a new model, storing it with version management.

        Args:
            db: Database session
            file_path: Path to the uploaded model file (temporary location)
            original_filename: Original name of the uploaded file
            model_type: Type of model ('threat_detector' or 'attack_classifier')
            file_format: File extension ('.pkl', '.joblib', or '.h5')
            description: Optional description of the model
            uploaded_by: Optional user identifier

        Returns:
            MLModel database record

        Raises:
            ModelManagerError: If validation or storage fails
        """
        # Step 1: Validate the model
        validation_result = self.validator.validate_model(file_path, model_type, file_format)

        if not validation_result['is_valid']:
            raise ModelManagerError(f"Model validation failed: {validation_result['error_message']}")

        # Step 2: Generate version (timestamp-based)
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Step 3: Determine storage path
        storage_filename = f"{model_type}_{version}{file_format}"
        storage_path = os.path.join(
            self.models_directory,
            model_type,
            storage_filename
        )

        # Step 4: Copy model file to storage location
        try:
            shutil.copy2(file_path, storage_path)
        except Exception as e:
            raise ModelManagerError(f"Failed to copy model file to storage: {str(e)}")

        # Step 5: Get file size
        file_size = os.path.getsize(storage_path)

        # Step 6: Create database record
        ml_model = MLModel(
            model_type=model_type,
            version=version,
            file_path=storage_path,
            file_format=file_format,
            original_filename=original_filename,
            is_active=False,  # Not active by default - requires manual activation
            model_metadata=validation_result['model_metadata'],
            validation_results=validation_result,
            file_size_bytes=file_size,
            uploaded_by=uploaded_by,
            description=description
        )

        try:
            db.add(ml_model)
            db.commit()
            db.refresh(ml_model)
        except Exception as e:
            # If database insert fails, clean up the file
            if os.path.exists(storage_path):
                os.remove(storage_path)
            db.rollback()
            raise ModelManagerError(f"Failed to save model to database: {str(e)}")

        return ml_model

    def activate_model(self, db: Session, model_id: int) -> MLModel:
        """
        Activate a specific model version, deactivating all others of the same type.

        Args:
            db: Database session
            model_id: ID of the model to activate

        Returns:
            Activated MLModel record

        Raises:
            ModelManagerError: If model not found or activation fails
        """
        # Get the model to activate
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise ModelManagerError(f"Model with ID {model_id} not found")

        # Verify model file exists
        if not os.path.exists(model.file_path):
            raise ModelManagerError(
                f"Model file not found at {model.file_path}. "
                "File may have been moved or deleted."
            )

        try:
            # Deactivate all other models of the same type
            db.query(MLModel).filter(
                MLModel.model_type == model.model_type,
                MLModel.id != model_id
            ).update({MLModel.is_active: False})

            # Activate the selected model
            model.is_active = True
            db.commit()
            db.refresh(model)

            return model

        except Exception as e:
            db.rollback()
            raise ModelManagerError(f"Failed to activate model: {str(e)}")

    def deactivate_model(self, db: Session, model_id: int) -> MLModel:
        """
        Deactivate a specific model version.

        Args:
            db: Database session
            model_id: ID of the model to deactivate

        Returns:
            Deactivated MLModel record

        Raises:
            ModelManagerError: If model not found
        """
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise ModelManagerError(f"Model with ID {model_id} not found")

        try:
            model.is_active = False
            db.commit()
            db.refresh(model)
            return model
        except Exception as e:
            db.rollback()
            raise ModelManagerError(f"Failed to deactivate model: {str(e)}")

    def get_active_model(self, db: Session, model_type: str) -> Optional[MLModel]:
        """
        Get the currently active model for a specific model type.

        Args:
            db: Database session
            model_type: Type of model ('threat_detector' or 'attack_classifier')

        Returns:
            Active MLModel record or None if no active model
        """
        return db.query(MLModel).filter(
            MLModel.model_type == model_type,
            MLModel.is_active == True
        ).first()

    def load_active_model(self, db: Session, model_type: str) -> Any:
        """
        Load the active model instance from disk.

        Args:
            db: Database session
            model_type: Type of model to load

        Returns:
            Loaded model instance (Keras model, sklearn model, etc.)

        Raises:
            ModelManagerError: If no active model or loading fails
        """
        active_model = self.get_active_model(db, model_type)
        if not active_model:
            raise ModelManagerError(f"No active model found for type: {model_type}")

        if not os.path.exists(active_model.file_path):
            raise ModelManagerError(
                f"Model file not found: {active_model.file_path}. "
                "File may have been moved or deleted."
            )

        try:
            if active_model.file_format == '.h5':
                # Load Keras model
                from tensorflow import keras
                model = keras.models.load_model(active_model.file_path)
            else:
                # Load pickle/joblib model
                model = joblib.load(active_model.file_path)

            return model

        except Exception as e:
            raise ModelManagerError(f"Failed to load model: {str(e)}")

    def list_models(
        self,
        db: Session,
        model_type: Optional[str] = None,
        include_inactive: bool = True
    ) -> List[MLModel]:
        """
        List all models, optionally filtered by type and active status.

        Args:
            db: Database session
            model_type: Filter by model type (optional)
            include_inactive: Whether to include inactive models

        Returns:
            List of MLModel records
        """
        query = db.query(MLModel)

        if model_type:
            query = query.filter(MLModel.model_type == model_type)

        if not include_inactive:
            query = query.filter(MLModel.is_active == True)

        return query.order_by(MLModel.created_at.desc()).all()

    def delete_model(self, db: Session, model_id: int, delete_file: bool = True) -> None:
        """
        Delete a model from the database and optionally from disk.

        Args:
            db: Database session
            model_id: ID of the model to delete
            delete_file: Whether to also delete the model file from disk

        Raises:
            ModelManagerError: If model not found or is currently active
        """
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise ModelManagerError(f"Model with ID {model_id} not found")

        if model.is_active:
            raise ModelManagerError(
                "Cannot delete an active model. Deactivate it first or activate another version."
            )

        try:
            # Delete file from disk if requested
            if delete_file and os.path.exists(model.file_path):
                os.remove(model.file_path)

            # Delete database record
            db.delete(model)
            db.commit()

        except Exception as e:
            db.rollback()
            raise ModelManagerError(f"Failed to delete model: {str(e)}")

    def get_model_info(self, db: Session, model_id: int) -> Optional[MLModel]:
        """
        Get detailed information about a specific model.

        Args:
            db: Database session
            model_id: ID of the model

        Returns:
            MLModel record or None
        """
        return db.query(MLModel).filter(MLModel.id == model_id).first()

    def get_storage_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get statistics about model storage usage.

        Args:
            db: Database session

        Returns:
            Dictionary with storage statistics
        """
        all_models = db.query(MLModel).all()

        stats = {
            'total_models': len(all_models),
            'total_size_bytes': sum(m.file_size_bytes or 0 for m in all_models),
            'by_type': {},
            'active_models': []
        }

        for model_type in ['threat_detector', 'attack_classifier']:
            models = [m for m in all_models if m.model_type == model_type]
            active = [m for m in models if m.is_active]

            stats['by_type'][model_type] = {
                'count': len(models),
                'size_bytes': sum(m.file_size_bytes or 0 for m in models),
                'active_count': len(active)
            }

            if active:
                stats['active_models'].append({
                    'model_type': model_type,
                    'version': active[0].version,
                    'id': active[0].id
                })

        return stats
