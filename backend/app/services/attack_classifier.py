"""
Attack Classification Service using Decision Tree Model.
Performs multi-class classification: 14 attack types.
"""
from typing import Dict
from sqlalchemy.orm import Session
from app.models.ml_models import get_decision_tree_model
from app.models.database import TrafficData, AttackPrediction


class AttackClassifierService:
    """Service for classifying attack types using decision tree model."""

    def __init__(self):
        self.model = get_decision_tree_model()

    def predict(
        self,
        features: Dict[str, float],
        db: Session,
        traffic_data_id: int
    ) -> AttackPrediction:
        """
        Classify the type of attack from network traffic.

        Args:
            features: Dictionary with 42 attack classification features
            db: Database session
            traffic_data_id: ID of the associated traffic data record

        Returns:
            AttackPrediction database object
        """
        # Get prediction from decision tree model
        attack_type_encoded, attack_type_name, confidence = self.model.predict(features)

        # Create prediction record
        prediction = AttackPrediction(
            traffic_data_id=traffic_data_id,
            attack_type_encoded=attack_type_encoded,
            attack_type_name=attack_type_name,
            confidence=confidence,
            model_version=self.model.model_version
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
    ) -> list[AttackPrediction]:
        """
        Classify attack types for multiple traffic data records.

        Args:
            features_list: List of feature dictionaries
            db: Database session
            traffic_data_ids: List of traffic data IDs

        Returns:
            List of AttackPrediction objects
        """
        predictions = []

        for features, traffic_id in zip(features_list, traffic_data_ids):
            attack_type_encoded, attack_type_name, confidence = self.model.predict(features)

            prediction = AttackPrediction(
                traffic_data_id=traffic_id,
                attack_type_encoded=attack_type_encoded,
                attack_type_name=attack_type_name,
                confidence=confidence,
                model_version=self.model.model_version
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
    ) -> AttackPrediction:
        """Get attack classification for specific traffic data."""
        return db.query(AttackPrediction).filter(
            AttackPrediction.traffic_data_id == traffic_data_id
        ).first()

    def get_recent_predictions(
        self,
        db: Session,
        limit: int = 100
    ) -> list[AttackPrediction]:
        """Get recent attack classifications."""
        return db.query(AttackPrediction).order_by(
            AttackPrediction.created_at.desc()
        ).limit(limit).all()

    def get_attack_type_distribution(self, db: Session) -> Dict:
        """Get distribution of attack types."""
        from sqlalchemy import func

        # Query attack type counts
        distribution = db.query(
            AttackPrediction.attack_type_name,
            func.count(AttackPrediction.id).label('count')
        ).group_by(
            AttackPrediction.attack_type_name
        ).all()

        return {
            attack_type: count
            for attack_type, count in distribution
        }
