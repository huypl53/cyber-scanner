"""
Threat Detection Service using Ensemble Model (ANN + LSTM).
Performs binary classification: Normal vs Attack.
"""
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from app.models.model_loaders import predict_threat, get_model_version, get_threshold
from app.models.database import TrafficData, ThreatPrediction
from datetime import datetime


class ThreatDetectorService:
    """Service for detecting threats using the ensemble model."""

    # No init needed - models are loaded lazily with singleton caching

    def predict(
        self,
        features: Dict[str, float],
        db: Session,
        traffic_data_id: int
    ) -> ThreatPrediction:
        """
        Predict whether network traffic is an attack or normal.

        Args:
            features: Dictionary with 10 threat detection features
            db: Database session
            traffic_data_id: ID of the associated traffic data record

        Returns:
            ThreatPrediction database object
        """
        # Get prediction from threat detection pipeline
        score, is_attack = predict_threat(features)

        # Create prediction record
        prediction = ThreatPrediction(
            traffic_data_id=traffic_data_id,
            prediction_score=score,
            is_attack=is_attack,
            threshold=get_threshold(),
            model_version=get_model_version("threat")
        )

        # Save to database
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return prediction

    def predict_batch(
        self,
        features_list: list[Dict[str, float]],
        db: Session,
        traffic_data_ids: list[int]
    ) -> list[ThreatPrediction]:
        """
        Predict threat for multiple traffic data records.

        Args:
            features_list: List of feature dictionaries
            db: Database session
            traffic_data_ids: List of traffic data IDs

        Returns:
            List of ThreatPrediction objects
        """
        predictions = []
        threshold = get_threshold()
        model_version = get_model_version("threat")

        for features, traffic_id in zip(features_list, traffic_data_ids):
            score, is_attack = predict_threat(features)

            prediction = ThreatPrediction(
                traffic_data_id=traffic_id,
                prediction_score=score,
                is_attack=is_attack,
                threshold=threshold,
                model_version=model_version
            )
            predictions.append(prediction)

        # Bulk save
        db.add_all(predictions)
        db.commit()

        # Refresh all predictions
        for prediction in predictions:
            db.refresh(prediction)

        return predictions

    def get_prediction_by_traffic_id(
        self,
        traffic_data_id: int,
        db: Session
    ) -> ThreatPrediction:
        """Get threat prediction for specific traffic data."""
        return db.query(ThreatPrediction).filter(
            ThreatPrediction.traffic_data_id == traffic_data_id
        ).first()

    def get_recent_predictions(
        self,
        db: Session,
        limit: int = 100
    ) -> list[ThreatPrediction]:
        """Get recent threat predictions."""
        return db.query(ThreatPrediction).order_by(
            ThreatPrediction.created_at.desc()
        ).limit(limit).all()

    def get_attack_statistics(self, db: Session) -> Dict:
        """Get statistics about threats detected."""
        total = db.query(ThreatPrediction).count()
        attacks = db.query(ThreatPrediction).filter(
            ThreatPrediction.is_attack == True
        ).count()
        normal = total - attacks

        attack_rate = (attacks / total * 100) if total > 0 else 0

        return {
            "total_predictions": total,
            "total_attacks": attacks,
            "total_normal": normal,
            "attack_rate": round(attack_rate, 2)
        }
