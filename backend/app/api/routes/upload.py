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
import pandas as pd
import io
import uuid
from datetime import datetime
from typing import List

router = APIRouter()


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
            raise HTTPException(status_code=400, detail=f"CSV validation error: {str(e)}")

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

        # Run threat detection
        threat_predictions = threat_detector.predict_batch(
            features_list,
            db,
            traffic_ids
        )

        # Build response
        predictions_response: List[CompletePredictionResponse] = []

        # If attack classification features are available, run classification for attacks
        if model_type == "attack_classification":
            # Only classify detected attacks
            attack_indices = [
                i for i, pred in enumerate(threat_predictions)
                if pred.is_attack
            ]

            if attack_indices:
                attack_features = [features_list[i] for i in attack_indices]
                attack_traffic_ids = [traffic_ids[i] for i in attack_indices]

                # Run attack classification
                attack_predictions = attack_classifier.predict_batch(
                    attack_features,
                    db,
                    attack_traffic_ids
                )

                # Log self-healing actions
                self_healing_actions = self_healing.log_action_batch(
                    attack_predictions,
                    db
                )

                # Build response with all predictions
                attack_pred_map = {
                    pred.traffic_data_id: pred
                    for pred in attack_predictions
                }
                action_map = {
                    action.attack_prediction_id: action
                    for action in self_healing_actions
                }

                for i, (traffic_record, threat_pred) in enumerate(
                    zip(traffic_data_records, threat_predictions)
                ):
                    attack_pred = attack_pred_map.get(traffic_record.id)
                    action = action_map.get(attack_pred.id) if attack_pred else None

                    predictions_response.append(
                        CompletePredictionResponse(
                            traffic_data=traffic_record,
                            threat_prediction=threat_pred,
                            attack_prediction=attack_pred,
                            self_healing_action=action
                        )
                    )
            else:
                # No attacks detected
                for traffic_record, threat_pred in zip(
                    traffic_data_records, threat_predictions
                ):
                    predictions_response.append(
                        CompletePredictionResponse(
                            traffic_data=traffic_record,
                            threat_prediction=threat_pred,
                            attack_prediction=None,
                            self_healing_action=None
                        )
                    )
        else:
            # Only threat detection available
            for traffic_record, threat_pred in zip(
                traffic_data_records, threat_predictions
            ):
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
