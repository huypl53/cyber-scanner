"""
CSV Upload API endpoints.
Handles uploading network traffic data, running predictions, and classification.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.preprocessor import DataPreprocessor
from app.services.threat_detector import ThreatDetectorService
from app.services.attack_classifier import AttackClassifierService
from app.services.self_healing import SelfHealingService
from app.models.database import TrafficData
from app.models.schemas import CSVUploadResponse, CompletePredictionResponse
from app.models.model_loaders import (
    THREAT_DETECTION_FEATURES,
    ATTACK_CLASSIFICATION_FEATURES
)
import pandas as pd
import io
import uuid
from datetime import datetime
from typing import List
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()


def _build_csv_validation_error(
    df_columns: List[str],
    error_message: str
) -> dict:
    """
    Build a detailed CSV validation error response.

    Provides helpful information including:
    - What features were found in the CSV
    - What features are required for each model type
    - Which features are missing
    - Example header lines for reference
    """
    csv_headers = [str(col).strip() for col in df_columns]

    # Check against both feature sets
    threat_matches = sum(
        1 for h in csv_headers
        if h.lower().replace('_', ' ').replace(' ', '') in
        [f.lower().replace('_', ' ').replace(' ', '') for f in THREAT_DETECTION_FEATURES]
    )
    attack_matches = sum(
        1 for h in csv_headers
        if h.lower().replace('_', ' ').replace(' ', '') in
        [f.lower().replace('_', ' ').replace(' ', '') for f in ATTACK_CLASSIFICATION_FEATURES]
    )

    # Determine likely intended model type
    likely_model = None
    if threat_matches >= 8:
        likely_model = "threat_detection"
    elif attack_matches >= 30:
        likely_model = "attack_classification"

    # Build required features list based on likely model
    if likely_model == "threat_detection":
        required_features = list(THREAT_DETECTION_FEATURES)
        model_name = "Threat Detection (10 features)"
    elif likely_model == "attack_classification":
        required_features = list(ATTACK_CLASSIFICATION_FEATURES)
        model_name = "Attack Classification (42 features)"
    else:
        # Ambiguous - show both options
        required_features = []
        model_name = "Unknown - please check format"

    # Calculate missing features
    missing_features = []
    if likely_model and required_features:
        normalized_headers = [h.lower().replace('_', ' ').replace(' ', '') for h in csv_headers]
        for feat in required_features:
            feat_normalized = feat.lower().replace('_', ' ').replace(' ', '')
            if feat_normalized not in normalized_headers:
                missing_features.append(feat)

    # Example headers
    threat_example = ",".join(THREAT_DETECTION_FEATURES)
    attack_example = ",".join([f"'{f}'" if f.startswith(' ') else f for f in ATTACK_CLASSIFICATION_FEATURES[:10]]) + ",..."

    return {
        "error": "CSV validation failed",
        "message": error_message,
        "csv_headers_found": csv_headers,
        "header_count": len(csv_headers),
        "detected_model_type": likely_model,
        "details": {
            "threat_detection_matches": threat_matches,
            "attack_classification_matches": attack_matches,
        },
        "required_features": required_features if likely_model else ["See sample files"],
        "missing_features": missing_features,
        "sample_formats": {
            "threat_detection": {
                "description": "10 features for binary threat detection",
                "example_header": threat_example
            },
            "attack_classification": {
                "description": "42 features for multi-class attack classification",
                "example_header": attack_example,
                "note": "Some headers have leading spaces, e.g., ' Destination Port'"
            }
        },
        "help": {
            "download_samples": "GET /api/v1/samples/ for downloadable sample files",
            "documentation": "See backend/samples/README.md for detailed format information"
        }
    }


@router.post("/upload/csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file with network traffic data.
    Automatically detects model type and runs appropriate predictions.

    Supports two formats:
    - 10 features: Runs threat detection only
    - 42 features: Runs threat detection + attack classification + self-healing

    Returns complete prediction results for all rows.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        # Initialize services
        preprocessor = DataPreprocessor()
        threat_detector = ThreatDetectorService()
        attack_classifier = AttackClassifierService()
        self_healing = SelfHealingService()

        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Process CSV and detect model type
        try:
            features_list, model_type = preprocessor.process_csv_dataframe(df)
        except ValueError as e:
            # Build detailed validation error
            error_detail = _build_csv_validation_error(df.columns, str(e))
            raise HTTPException(status_code=400, detail=error_detail)

        # Store traffic data in database
        traffic_data_records = []
        for features in features_list:
            traffic_record = TrafficData(
                features=features,
                source='upload',
                batch_id=batch_id
            )
            traffic_data_records.append(traffic_record)

        db.add_all(traffic_data_records)
        db.commit()

        # Refresh to get IDs
        for record in traffic_data_records:
            db.refresh(record)

        traffic_ids = [record.id for record in traffic_data_records]

        # Build response
        predictions_response: List[CompletePredictionResponse] = []

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

            # Build response map
            action_map = {
                action.attack_prediction_id: action
                for action in self_healing_actions
            }

            for traffic_record, attack_pred in zip(traffic_data_records, attack_predictions):
                action = action_map.get(attack_pred.id) if attack_pred else None

                predictions_response.append(
                    CompletePredictionResponse(
                        traffic_data=traffic_record,
                        threat_prediction=None,
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

        return CSVUploadResponse(
            message=f"Successfully processed {len(df)} rows",
            batch_id=batch_id,
            total_rows=len(df),
            predictions=predictions_response
        )

    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Invalid CSV format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


@router.get("/upload/batches")
async def list_batches(db: Session = Depends(get_db)):
    """List all uploaded batch IDs with their metadata."""
    from sqlalchemy import func

    batches = db.query(
        TrafficData.batch_id,
        func.count(TrafficData.id).label('row_count'),
        func.min(TrafficData.created_at).label('uploaded_at')
    ).filter(
        TrafficData.source == 'upload',
        TrafficData.batch_id.isnot(None)
    ).group_by(
        TrafficData.batch_id
    ).order_by(
        func.min(TrafficData.created_at).desc()
    ).all()

    return {
        "batches": [
            {
                "batch_id": batch_id,
                "row_count": row_count,
                "uploaded_at": uploaded_at
            }
            for batch_id, row_count, uploaded_at in batches
        ]
    }


@router.get("/upload/batch/{batch_id}")
async def get_batch_predictions(batch_id: str, db: Session = Depends(get_db)):
    """Get all predictions for a specific batch."""
    # Get traffic data for this batch
    traffic_records = db.query(TrafficData).filter(
        TrafficData.batch_id == batch_id
    ).all()

    if not traffic_records:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Build complete response
    predictions_response = []
    for traffic_record in traffic_records:
        threat_pred = traffic_record.threat_prediction
        attack_pred = traffic_record.attack_prediction
        action = attack_pred.self_healing_action if attack_pred else None

        predictions_response.append(
            CompletePredictionResponse(
                traffic_data=traffic_record,
                threat_prediction=threat_pred,
                attack_prediction=attack_pred,
                self_healing_action=action
            )
        )

    return {
        "batch_id": batch_id,
        "total_rows": len(traffic_records),
        "predictions": predictions_response
    }


# Sample file serving
# Path from /app/app/api/routes/upload.py -> /app/samples/
SAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "samples"


@router.get("/samples")
async def list_samples():
    """List available sample CSV files."""
    samples = [
        {
            "name": "threat_detection_sample.csv",
            "description": "10 features for binary threat detection",
            "download_url": "/api/v1/samples/threat_detection_sample.csv"
        },
        {
            "name": "attack_classification_sample.csv",
            "description": "42 features for multi-class attack classification",
            "download_url": "/api/v1/samples/attack_classification_sample.csv"
        }
    ]
    return {"samples": samples}


@router.get("/samples/{filename}")
async def download_sample(filename: str):
    """Download a sample CSV file."""
    # Security: only allow specific filenames
    allowed_files = {
        "threat_detection_sample.csv",
        "attack_classification_sample.csv"
    }

    if filename not in allowed_files:
        raise HTTPException(
            status_code=404,
            detail=f"Sample file not found. Available: {', '.join(allowed_files)}"
        )

    file_path = SAMPLES_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Sample file '{filename}' not found on server"
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
